"""
ORBIT-INTEL 6G: Phase 3 CAPRO Orchestrator Unit Tests
Tests:
1. Dimensionless Normalized Utility Properties
2. Hard Reliability Lower-Bound Gating (q_05 >= 3.0 dB)
3. URLLC Latency SLA Exclusion (LEO delay > 10ms excluded for URLLC)
4. Hysteresis Gating (Delta_J <= 0.08 suppresses handover)
5. Proactive Satellite Descent Trigger (T_vis < 12s)
6. Epistemic Risk Penalty Avoidance
7. Controlled Ablation Variants Execution
8. Deterministic Graceful Fallback on Extreme Degradation
"""

import pytest
import numpy as np
from src.orchestration_engine.capro_engine import CAPROOrchestrator, ExplainableDecision


class TestCAPRORedesign:

    @pytest.fixture
    def standard_links(self):
        return {
            "TBS-01": {"tier": "TBS", "is_visible": True, "slant_distance_m": 800.0, "load": 0.4, "remaining_visibility_s": 9999.0},
            "HAPS-01": {"tier": "HAPS", "is_visible": True, "slant_distance_m": 25000.0, "load": 0.2, "remaining_visibility_s": 1800.0},
            "SAT-01": {"tier": "LEO", "is_visible": True, "slant_distance_m": 1200000.0, "load": 0.1, "remaining_visibility_s": 35.0},
        }

    @pytest.fixture
    def standard_preds(self):
        return {
            "TBS-01": {"y_pred": 16.0, "q_lower": 14.0, "epistemic_std": 0.2, "total_uncertainty": 2.5},
            "HAPS-01": {"y_pred": 18.0, "q_lower": 16.5, "epistemic_std": 0.1, "total_uncertainty": 1.5},
            "SAT-01": {"y_pred": 22.0, "q_lower": 18.0, "epistemic_std": 0.2, "total_uncertainty": 4.0},
        }

    def test_capro_unit_normalization(self, standard_links, standard_preds):
        """Verifies utility function maps to normalized dimensionless scale."""
        capro = CAPROOrchestrator()
        u_info = capro.compute_normalized_utility(
            y_pred_db=20.0,
            q_lower_db=16.0,
            epistemic_std_db=0.3,
            latency_ms=5.0,
            node_load=0.2,
            is_current_serving=True,
            service_type="URLLC",
        )
        assert 0.0 <= u_info["u_link"] <= 1.0
        assert 0.0 <= u_info["u_lat"] <= 1.0
        assert 0.0 <= u_info["u_cap"] <= 1.0
        assert u_info["c_ho"] == 0.0
        assert 0.0 <= u_info["c_risk"] <= 1.0
        assert -0.20 <= u_info["j_score"] <= 1.0

    def test_capro_hard_reliability_constraint(self, standard_links, standard_preds):
        """A link with q_lower < 3.0 dB must be excluded from eligible set."""
        capro = CAPROOrchestrator()
        bad_preds = dict(standard_preds)
        bad_preds["TBS-01"] = {"y_pred": 12.0, "q_lower": 1.5, "epistemic_std": 0.5, "total_uncertainty": 5.0}

        eligible, fallback, _ = capro.filter_eligible_nodes(standard_links, bad_preds, "eMBB")
        assert "TBS-01" not in eligible, "TBS-01 should be filtered out by reliability bound"
        assert "HAPS-01" in eligible
        assert "SAT-01" in eligible

    def test_capro_urllc_latency_exclusion(self, standard_links, standard_preds):
        """LEO satellites (slant delay > 11.6ms) must be ineligible for URLLC (10ms SLA)."""
        capro = CAPROOrchestrator()
        eligible_urllc, _, _ = capro.filter_eligible_nodes(standard_links, standard_preds, "URLLC")
        assert "SAT-01" not in eligible_urllc, "LEO satellite must be ineligible for URLLC 10ms SLA"
        assert "TBS-01" in eligible_urllc
        assert "HAPS-01" in eligible_urllc

        # For eMBB (50ms SLA), LEO satellite must be eligible
        eligible_embb, _, _ = capro.filter_eligible_nodes(standard_links, standard_preds, "eMBB")
        assert "SAT-01" in eligible_embb

    def test_capro_hysteresis_suppression(self, standard_links, standard_preds):
        """Marginal utility improvement (Delta J <= 0.08) must NOT trigger a handover."""
        capro = CAPROOrchestrator()
        # User currently on HAPS-01 (very good link)
        # TBS-01 offers only tiny marginal gain
        dec = capro.select_network_node("UE-01", "HAPS-01", standard_links, standard_preds, "eMBB")
        assert dec.is_handover is False
        assert dec.selected_node_id == "HAPS-01"
        assert dec.trigger_code == "STEADY_STATE_OPTIMAL"

    def test_capro_proactive_departure_trigger(self, standard_links, standard_preds):
        """Setting satellite with remaining visibility < 12s must trigger proactive handover."""
        capro = CAPROOrchestrator(handover_margin_s=12.0)
        setting_links = dict(standard_links)
        setting_links["SAT-01"] = {"tier": "LEO", "is_visible": True, "slant_distance_m": 1200000.0, "load": 0.1, "remaining_visibility_s": 8.0}

        dec = capro.select_network_node("UE-01", "SAT-01", setting_links, standard_preds, "eMBB")
        assert dec.is_handover is True
        assert dec.selected_node_id in ["HAPS-01", "TBS-01"]
        assert dec.trigger_code == "PROACTIVE_SATELLITE_DESCENT"

    def test_capro_epistemic_cost_avoidance(self, standard_links, standard_preds):
        """Link with high epistemic doubt (sigma_epi = 2.8 dB) must be penalized in utility."""
        capro = CAPROOrchestrator()
        volatile_preds = dict(standard_preds)
        # HAPS has lower raw SINR (15 dB) but low epistemic std (0.1 dB)
        # TBS has higher raw SINR (20 dB) but severe epistemic uncertainty (2.8 dB)
        volatile_preds["TBS-01"] = {"y_pred": 20.0, "q_lower": 12.0, "epistemic_std": 2.8, "total_uncertainty": 5.0}
        volatile_preds["HAPS-01"] = {"y_pred": 15.0, "q_lower": 13.0, "epistemic_std": 0.1, "total_uncertainty": 1.5}

        u_tbs = capro.compute_normalized_utility(20.0, 12.0, 2.8, 3.0, 0.2, False, "URLLC")
        u_haps = capro.compute_normalized_utility(15.0, 13.0, 0.1, 4.0, 0.2, True, "URLLC")
        assert u_tbs["c_risk"] > u_haps["c_risk"], "High epistemic uncertainty must yield high risk cost"

    def test_capro_ablation_variants(self, standard_links, standard_preds):
        """All 7 ablation modes must execute and produce valid decisions."""
        ablations = [
            "NoUncertainty",
            "AleatoricOnly",
            "EpistemicOnly",
            "NoHandoverCost",
            "NoReliabilityConstraint",
            "NoLatencyConstraint",
            "FullCAPRO",
        ]
        for mode in ablations:
            capro_abl = CAPROOrchestrator(ablation_mode=mode)
            dec = capro_abl.select_network_node("UE-01", "TBS-01", standard_links, standard_preds, "URLLC")
            assert dec.selected_node_id is not None
            assert isinstance(dec, ExplainableDecision)

    def test_capro_fallback_modes(self):
        """When all nodes violate latency (e.g. offshore URLLC), fallback must relax latency constraint gracefully."""
        capro = CAPROOrchestrator()
        # Only LEO satellite available (slant distance 1500km, delay ~12ms > 10ms URLLC)
        offshore_links = {
            "SAT-01": {"tier": "LEO", "is_visible": True, "slant_distance_m": 1500000.0, "load": 0.1, "remaining_visibility_s": 250.0}
        }
        offshore_preds = {
            "SAT-01": {"y_pred": 18.0, "q_lower": 14.0, "epistemic_std": 0.2, "total_uncertainty": 3.0}
        }
        dec = capro.select_network_node("UE-10", None, offshore_links, offshore_preds, "URLLC")
        assert dec.selected_node_id == "SAT-01"
        assert dec.fallback_used is True
        assert dec.trigger_code == "FALLBACK_RELAXED_LATENCY_SLA"

