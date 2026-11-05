"""
Unit and Integration Tests for ORBIT-INTEL 6G STLC Showcase Dashboard.
Validates data ingestion, model inferences, simulation stepping, and plot generators.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.simulation_engine.network_simulator import NetworkSimulator
from src.prediction_engine.models import DualUncertaintyPredictor
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.orchestration_engine.capro_engine import CAPROOrchestrator
from src.baseline_methods.m1_reactive import M1ReactiveBaseline
from src.experiments.scenarios import ALL_SCENARIOS

# Import loaders from app
from dashboard.app import (
    load_predictor,
    load_benchmark_datasets,
    load_robustness_datasets,
    PROJECT_ROOT,
)


class TestDashboardDataLoaders:
    """Verifies that all empirical datasets and models load cleanly."""

    def test_load_predictor_model(self):
        predictor = load_predictor()
        assert predictor is not None, "Predictor model failed to load from models/capro_predictor.joblib"
        assert hasattr(predictor, "predict_with_uncertainty")

    def test_load_benchmark_datasets(self):
        raw_df, method_df, scenario_df, ablation_df, stats_df = load_benchmark_datasets()
        assert raw_df is not None and not raw_df.empty, "RAW_BENCHMARK_RESULTS.csv is missing or empty"
        assert method_df is not None and not method_df.empty, "BENCHMARK_METRICS_BY_METHOD.csv is missing or empty"
        assert scenario_df is not None and not scenario_df.empty, "BENCHMARK_METRICS_BY_SCENARIO.csv is missing or empty"
        assert ablation_df is not None and not ablation_df.empty, "CAPRO_ABLATION_RESULTS.csv is missing or empty"
        assert stats_df is not None and not stats_df.empty, "STATISTICAL_TEST_RESULTS.csv is missing or empty"

        # Verify key columns
        assert "pdr_percent_mean" in method_df.columns
        assert "handover_frequency_per_min_mean" in method_df.columns
        assert "M4_CAPRO" in method_df["method"].values

    def test_load_robustness_datasets(self):
        param_df, metrics_df = load_robustness_datasets()
        assert param_df is not None and not param_df.empty, "PARAMETER_SWEEP_RESULTS.csv missing or empty"
        assert metrics_df is not None and not metrics_df.empty, "ROBUSTNESS_METRICS.csv missing or empty"
        assert "Horizon_Sweep" in metrics_df["experiment_tag"].values


class TestDashboardSimulationAndCAPRO:
    """Verifies live simulator execution and CAPRO decisions."""

    def test_simulation_step_and_telemetry(self):
        sim = NetworkSimulator(random_seed=42)
        snap = sim.step()
        assert "links" in snap
        assert len(sim.nodes) == 6
        assert len(sim.users) == 12

        # Check telemetry keys
        l_data = sim.compute_link_telemetry("UE-01", "SAT-01")
        assert "elevation_deg" in l_data
        assert "slant_distance_m" in l_data
        assert "doppler_shift_hz" in l_data
        assert "remaining_visibility_s" in l_data

    def test_feature_extraction_and_prediction(self):
        sim = NetworkSimulator(random_seed=42)
        predictor = load_predictor()
        history = [sim.step()["links"][("UE-01", "SAT-01")]]
        
        feat_dict = FeatureEngineer.extract_features_from_history(history, "UE-01", "SAT-01")
        feat_vec = FeatureEngineer.to_feature_vector(feat_dict).reshape(1, -1)
        res = predictor.predict_with_uncertainty(feat_vec)

        assert "y_pred" in res
        assert "q_lower" in res
        assert "q_upper" in res
        assert "epistemic_std" in res
        assert res["q_lower"][0] <= res["y_pred"][0] <= res["q_upper"][0]

    def test_capro_orchestration_decision(self):
        sim = NetworkSimulator(random_seed=42)
        capro = CAPROOrchestrator(risk_aversion_kappa=1.5, hysteresis_margin_db=2.5)
        user_links = {nid: sim.compute_link_telemetry("UE-01", nid) for nid in sim.nodes}
        preds = {
            "TBS-01": {"y_pred": 18.0, "q_lower": 15.0, "q_upper": 21.0, "total_uncertainty": 6.0},
            "SAT-01": {"y_pred": 12.0, "q_lower": 9.0, "q_upper": 15.0, "total_uncertainty": 6.0},
        }
        dec = capro.select_network_node("UE-01", None, user_links, preds, "URLLC")
        assert dec.selected_node_id is not None
        assert 0.0 <= dec.risk_adjusted_utility_db <= 1.0
        assert len(dec.explanation) > 10

    def test_m1_reactive_baseline_decision(self):
        sim = NetworkSimulator(random_seed=42)
        m1 = M1ReactiveBaseline()
        user_links = {nid: sim.compute_link_telemetry("UE-01", nid) for nid in sim.nodes}
        dec = m1.select_network_node("UE-01", None, user_links, "URLLC")
        assert dec["selected_node_id"] is not None


class TestScenarioDynamics:
    """Verifies that operational scenarios apply their dynamics without error."""

    def test_scenario_4_orbital_handover_initialization(self):
        sim = NetworkSimulator(random_seed=42)
        sc4 = ALL_SCENARIOS[3]
        sc4.apply_step_fn(sim, 0)
        
        tel1 = sim.compute_link_telemetry("UE-01", "SAT-01")
        tel2 = sim.compute_link_telemetry("UE-01", "SAT-02")
        
        # SAT-01 is setting (~11.6 deg), SAT-02 is rising (~9.4 deg)
        assert 10.0 <= tel1["elevation_deg"] <= 13.0
        assert 8.0 <= tel2["elevation_deg"] <= 10.0

    def test_scenario_stepping_and_environmental_injection(self):
        sim = NetworkSimulator(random_seed=42)
        sim.rain_rate_mm_h = 50.0
        sim.shadowing_flutter_std = 3.0
        snap = sim.step()
        assert snap is not None
        assert sim.rain_rate_mm_h == 50.0
        assert sim.shadowing_flutter_std == 3.0
