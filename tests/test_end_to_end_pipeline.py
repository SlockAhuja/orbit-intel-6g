"""
ORBIT-INTEL 6G: Phase 7 End-to-End Pipeline & Resilience Integration Tests
Validates complete operational chain:
Physical Simulation -> Telemetry -> Features -> Dual Prediction -> CAPRO Orchestration -> Packet Evaluation
and verifies robust failure handling under anomalous network events.
"""

import pytest
import numpy as np
from pathlib import Path

from src.simulation_engine.network_simulator import NetworkSimulator
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import DualUncertaintyPredictor
from src.orchestration_engine.capro_engine import CAPROOrchestrator, ExplainableDecision
from src.experiments.scenarios import ALL_SCENARIOS


@pytest.fixture(scope="module")
def trained_predictor():
    model_path = Path(__file__).resolve().parents[1] / "models" / "capro_predictor.joblib"
    assert model_path.exists(), "Trained model artifact missing"
    return DualUncertaintyPredictor.load(model_path)


@pytest.fixture
def base_simulator():
    return NetworkSimulator(random_seed=42)


def test_full_pipeline_single_user_step(trained_predictor, base_simulator):
    """Verifies complete data flow for a single user through all pipeline stages."""
    sim = base_simulator
    capro = CAPROOrchestrator()
    history = []

    # Run 5 initial warm-up steps
    for _ in range(5):
        history.append(sim.step())

    target_user = sim.users["UE-01"]
    current_telemetry = {n_id: history[-1]["links"][("UE-01", n_id)] for n_id in sim.nodes}

    # Extract features and predict for each candidate node
    preds = {}
    for n_id in sim.nodes:
        feats = FeatureEngineer.extract_features_from_history(history, "UE-01", n_id)
        X = np.array([feats[col] for col in FeatureEngineer.FEATURE_NAMES]).reshape(1, -1)
        pred_res = trained_predictor.predict_with_uncertainty(X)
        preds[n_id] = {
            "y_pred": float(pred_res["y_pred"][0]),
            "q_lower": float(pred_res["q_lower"][0]),
            "total_uncertainty": float(pred_res["total_uncertainty"][0]),
            "epistemic_std": float(pred_res["epistemic_std"][0]),
        }

    # Execute CAPRO decision
    dec = capro.select_network_node(
        user_id="UE-01",
        current_serving_id=None,
        available_links=current_telemetry,
        predictions=preds,
        user_service_type=target_user.service_type,
    )

    assert isinstance(dec, ExplainableDecision)
    assert dec.selected_node_id in sim.nodes
    assert dec.trigger_code in ["INITIAL_OPTIMAL_ATTACH", "INITIAL_FEASIBLE_FALLBACK"]
    assert 0.0 <= dec.risk_adjusted_utility_db <= 1.0


def test_multi_scenario_pipeline_execution(trained_predictor):
    """Executes a 10-second run of each scenario through the full pipeline."""
    capro = CAPROOrchestrator()

    for sc in ALL_SCENARIOS:
        sim = NetworkSimulator(random_seed=123)
        history = []
        user_att = {u: None for u in sim.users}

        for t in range(10):
            sc.apply_step_fn(sim, t)
            telem = sim.step()
            history.append(telem)
            if len(history) > 5:
                history.pop(0)

            for u_id, u in sim.users.items():
                user_links = {n_id: telem["links"][(u_id, n_id)] for n_id in sim.nodes}
                preds = {}
                for n_id in sim.nodes:
                    feats = FeatureEngineer.extract_features_from_history(history, u_id, n_id)
                    X = np.array([feats[col] for col in FeatureEngineer.FEATURE_NAMES]).reshape(1, -1)
                    p = trained_predictor.predict_with_uncertainty(X)
                    preds[n_id] = {
                        "y_pred": float(p["y_pred"][0]),
                        "q_lower": float(p["q_lower"][0]),
                        "total_uncertainty": float(p["total_uncertainty"][0]),
                        "epistemic_std": float(p["epistemic_std"][0]),
                    }

                dec = capro.select_network_node(
                    user_id=u_id,
                    current_serving_id=user_att[u_id],
                    available_links=user_links,
                    predictions=preds,
                    user_service_type=u.service_type,
                )
                assert dec.selected_node_id is not None
                user_att[u_id] = dec.selected_node_id


def test_resilience_to_degraded_network_telemetry(trained_predictor, base_simulator):
    """Verifies CAPRO fallback when telemetry is severely degraded across all nodes."""
    sim = base_simulator
    capro = CAPROOrchestrator()
    user = sim.users["UE-07"]  # Remote user

    degraded_telemetry = {
        n_id: {
            "tier": sim.nodes[n_id].tier,
            "is_visible": True,
            "sinr_db": 1.5,  # Below 3.0 dB outage threshold
            "slant_distance_m": 50000.0,
            "load": 0.9,
            "remaining_visibility_s": 100.0,
        }
        for n_id in sim.nodes
    }
    degraded_preds = {
        n_id: {
            "y_pred": 1.5,
            "q_lower": -1.0,  # Below threshold
            "total_uncertainty": 5.0,
            "epistemic_std": 1.5,
        }
        for n_id in sim.nodes
    }

    # Should safely trigger graceful fallback rather than raising unhandled exceptions
    dec = capro.select_network_node(
        user_id="UE-07",
        current_serving_id=None,
        available_links=degraded_telemetry,
        predictions=degraded_preds,
        user_service_type=user.service_type,
    )
    assert dec.selected_node_id is not None
    assert dec.fallback_used is True
    assert "FALLBACK" in dec.trigger_code


def test_resilience_to_extreme_ood_features(trained_predictor):
    """Verifies DualUncertaintyPredictor and CAPRO when fed extreme out-of-distribution inputs."""
    X_extreme = np.ones((1, len(FeatureEngineer.FEATURE_NAMES))) * 500.0
    pred = trained_predictor.predict_with_uncertainty(X_extreme)

    # Epistemic uncertainty should expand under extreme OOD conditions
    assert pred["epistemic_std"][0] > 0.0
    assert np.isfinite(pred["y_pred"][0])
    assert np.isfinite(pred["total_uncertainty"][0])


def test_orbital_departure_proactive_handover(trained_predictor):
    """Verifies proactive handover execution when LEO satellite approaches orbital horizon."""
    capro = CAPROOrchestrator(handover_margin_s=12.0)
    sim = NetworkSimulator(random_seed=42)

    mock_preds = {
        "SAT-01": {"y_pred": 22.0, "q_lower": 18.0, "total_uncertainty": 2.0, "epistemic_std": 0.5},
        "HAPS-01": {"y_pred": 14.0, "q_lower": 11.0, "total_uncertainty": 1.5, "epistemic_std": 0.4},
    }
    mock_telem = {
        "SAT-01": {"tier": "LEO", "sinr_db": 22.0, "slant_distance_m": 1200000.0, "load": 0.1, "remaining_visibility_s": 5.0, "is_visible": True},
        "HAPS-01": {"tier": "HAPS", "sinr_db": 14.0, "slant_distance_m": 25000.0, "load": 0.2, "remaining_visibility_s": 9999.0, "is_visible": True},
    }

    # User currently on SAT-01
    dec = capro.select_network_node(
        user_id="UE-01",
        current_serving_id="SAT-01",
        available_links=mock_telem,
        predictions=mock_preds,
        user_service_type="eMBB",
    )

    # Must proactively hand off away from SAT-01 because remaining visibility (5s) < margin (12s)
    assert dec.selected_node_id != "SAT-01", "CAPRO failed to proactively evict user before satellite departure"
    assert dec.trigger_code == "PROACTIVE_SATELLITE_DESCENT"
