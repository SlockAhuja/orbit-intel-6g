"""
Unit tests for Orchestration Engines and Baselines (M1-M4).
"""

import pytest
from src.orchestration_engine.capro_engine import CAPROOrchestrator
from src.baseline_methods.m1_reactive import M1ReactiveBaseline
from src.baseline_methods.m2_threshold_predictive import M2ThresholdPredictiveBaseline
from src.baseline_methods.m3_prediction_only import M3PredictionOnlyBaseline


def test_capro_proactive_satellite_descent():
    """CAPRO must proactively initiate handover when satellite remaining visibility < margin."""
    orchestrator = CAPROOrchestrator(handover_margin_s=12.0)

    links = {
        "SAT-01": {"tier": "LEO", "is_visible": True, "remaining_visibility_s": 8.0, "slant_distance_m": 1200000.0, "load": 0.2},
        "HAPS-01": {"tier": "HAPS", "is_visible": True, "remaining_visibility_s": 1800.0, "slant_distance_m": 25000.0, "load": 0.1},
    }
    preds = {
        "SAT-01": {"y_pred": 22.0, "q_lower": 18.0, "total_uncertainty": 2.0},
        "HAPS-01": {"y_pred": 18.0, "q_lower": 16.0, "total_uncertainty": 1.0},
    }

    decision = orchestrator.select_network_node("UE-01", "SAT-01", links, preds, "URLLC")
    assert decision.is_handover is True
    assert decision.selected_node_id == "HAPS-01"
    assert decision.trigger_code == "PROACTIVE_SATELLITE_DESCENT"


def test_capro_uncertainty_penalty_avoidance():
    """CAPRO must avoid a superficially high SINR link if its uncertainty is excessively high."""
    orchestrator = CAPROOrchestrator(risk_aversion_kappa=2.0)

    links = {
        "SAT-01": {"tier": "LEO", "is_visible": True, "remaining_visibility_s": 300.0, "slant_distance_m": 800000.0, "load": 0.1},
        "HAPS-01": {"tier": "HAPS", "is_visible": True, "remaining_visibility_s": 1800.0, "slant_distance_m": 25000.0, "load": 0.1},
    }
    # SAT-01 has high point prediction 24 dB, but massive uncertainty 9 dB
    # HAPS-01 has stable 18 dB with low uncertainty 1 dB
    preds = {
        "SAT-01": {"y_pred": 24.0, "q_lower": 1.0, "total_uncertainty": 9.0},
        "HAPS-01": {"y_pred": 18.0, "q_lower": 16.0, "total_uncertainty": 1.0},
    }

    decision = orchestrator.select_network_node("UE-01", "HAPS-01", links, preds, "URLLC")
    # Even though SAT-01 has 24 dB, HAPS-01 should be retained due to uncertainty penalty!
    assert decision.selected_node_id == "HAPS-01"
    assert decision.is_handover is False


def test_reactive_baseline_threshold_trigger():
    """M1 Reactive should only trigger handover when current SINR drops below threshold."""
    m1 = M1ReactiveBaseline(sinr_outage_thresh_db=3.0, handover_hysteresis_db=3.0)

    links_good = {
        "TBS-01": {"is_visible": True, "bandwidth_mhz": 50.0, "sinr_db": 12.0},
        "TBS-02": {"is_visible": True, "bandwidth_mhz": 50.0, "sinr_db": 13.0},
    }
    dec_hold = m1.select_network_node("UE-01", "TBS-01", links_good)
    assert dec_hold["selected_node_id"] == "TBS-01"
    assert dec_hold["is_handover"] is False

    # Current drops into outage
    links_bad = {
        "TBS-01": {"is_visible": True, "bandwidth_mhz": 50.0, "sinr_db": 1.5},
        "TBS-02": {"is_visible": True, "bandwidth_mhz": 50.0, "sinr_db": 13.0},
    }
    dec_switch = m1.select_network_node("UE-01", "TBS-01", links_bad)
    assert dec_switch["selected_node_id"] == "TBS-02"
    assert dec_switch["is_handover"] is True

