"""
ORBIT-INTEL 6G: Confidence-Aware Predictive Reliability Orchestration (CAPRO) Engine
Integrates multi-horizon forecasts, calibrated dual-uncertainty, and SLA-constrained multi-tier selection.
"""

from typing import Optional
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class ExplainableDecision:
    """Audit record explaining why a specific resource allocation/handover occurred."""
    user_id: str
    selected_node_id: Optional[str]
    previous_node_id: Optional[str]
    tier: str
    is_handover: bool
    trigger_code: str
    predicted_sinr_db: float
    q_lower_bound_db: float
    total_uncertainty_db: float
    risk_adjusted_utility_db: float
    explanation: str


class CAPROOrchestrator:
    """
    Confidence-Aware Predictive Reliability Orchestration Engine.
    Coordinates 4-tier SAGIN resources using risk-adjusted utility,
    calibrated prediction intervals, and proactive handover gating.
    """

    def __init__(
        self,
        risk_aversion_kappa: float = 1.5,
        hysteresis_margin_db: float = 2.5,
        handover_margin_s: float = 12.0,
        outage_sinr_threshold_db: float = 3.0,
    ):
        self.kappa = risk_aversion_kappa
        self.hysteresis_db = hysteresis_margin_db
        self.ho_margin_s = handover_margin_s
        self.outage_thresh_db = outage_sinr_threshold_db
        self.name = "M4_CAPRO"

        # Log of explainable decisions
        self.decision_history: list[ExplainableDecision] = []

    def compute_risk_adjusted_utility(
        self,
        predicted_sinr_db: float,
        total_uncertainty_db: float,
        latency_ms: float,
        node_load: float,
        tier: str,
        service_type: str = "URLLC",
    ) -> float:
        """
        R_adj = Q_hat - kappa * U - cost_penalties
        Penalizes prediction uncertainty, queuing latency, and node congestion.
        """
        base_utility = predicted_sinr_db - self.kappa * total_uncertainty_db

        # Latency penalty for URLLC services
        latency_penalty = 0.0
        if service_type == "URLLC":
            if latency_ms > 10.0:
                latency_penalty = (latency_ms - 10.0) * 0.8  # Strong penalty for satellite latency on URLLC
        else:
            if latency_ms > 50.0:
                latency_penalty = (latency_ms - 50.0) * 0.2

        # Congestion penalty
        load_penalty = 5.0 * (node_load ** 2)

        return float(base_utility - latency_penalty - load_penalty)

    def select_network_node(
        self,
        user_id: str,
        current_serving_id: Optional[str],
        available_links: dict[str, dict],
        predictions: dict[str, dict],
        user_service_type: str = "URLLC",
    ) -> ExplainableDecision:
        """
        Evaluates all candidate nodes and determines optimal allocation with proactive handover.
        """
        candidate_evaluations = {}

        for n_id, link in available_links.items():
            if not link["is_visible"]:
                continue

            pred = predictions.get(n_id)
            if not pred:
                continue

            y_pred = pred["y_pred"]
            q_lower = pred["q_lower"]
            u_total = pred["total_uncertainty"]
            tier = link["tier"]
            node_load = link["load"]
            vis_s = link["remaining_visibility_s"]

            # Estimate expected one-way latency
            slant_km = link["slant_distance_m"] / 1000.0
            t_prop_ms = (slant_km / 300.0)
            t_proc_ms = 2.5 if tier == "LEO" else (1.2 if tier == "HAPS" else 0.5)
            t_queue_ms = 0.5 / max(1.0 - node_load, 0.05)
            est_latency_ms = t_prop_ms + t_proc_ms + t_queue_ms

            # Orbital departure check for LEO
            is_satellite_departing = (tier == "LEO" and vis_s < self.ho_margin_s)

            # Risk-adjusted utility
            r_adj = self.compute_risk_adjusted_utility(
                predicted_sinr_db=y_pred,
                total_uncertainty_db=u_total,
                latency_ms=est_latency_ms,
                node_load=node_load,
                tier=tier,
                service_type=user_service_type,
            )

            # Hard penalty if satellite is setting or lower bound is below outage threshold
            if is_satellite_departing:
                r_adj -= 30.0  # Immediate proactive handover trigger
            if q_lower < self.outage_thresh_db:
                r_adj -= 15.0  # High outage probability penalty

            candidate_evaluations[n_id] = {
                "r_adj": r_adj,
                "y_pred": y_pred,
                "q_lower": q_lower,
                "u_total": u_total,
                "est_latency_ms": est_latency_ms,
                "is_satellite_departing": is_satellite_departing,
                "tier": tier,
                "vis_s": vis_s,
            }

        if not candidate_evaluations:
            decision = ExplainableDecision(
                user_id=user_id,
                selected_node_id=None,
                previous_node_id=current_serving_id,
                tier="NONE",
                is_handover=False,
                trigger_code="GLOBAL_OUTAGE_NO_VIABLE_TIER",
                predicted_sinr_db=-25.0,
                q_lower_bound_db=-25.0,
                total_uncertainty_db=0.0,
                risk_adjusted_utility_db=-100.0,
                explanation="No viable SAGIN node visible or meeting basic link bounds.",
            )
            self.decision_history.append(decision)
            return decision

        # Best candidate by risk-adjusted utility
        best_cand_id = max(candidate_evaluations.keys(), key=lambda nid: candidate_evaluations[nid]["r_adj"])
        best_eval = candidate_evaluations[best_cand_id]

        # Case 1: Initial attachment
        if current_serving_id is None or current_serving_id not in candidate_evaluations:
            decision = ExplainableDecision(
                user_id=user_id,
                selected_node_id=best_cand_id,
                previous_node_id=current_serving_id,
                tier=best_eval["tier"],
                is_handover=(current_serving_id is not None),
                trigger_code="INITIAL_OPTIMAL_ATTACH",
                predicted_sinr_db=float(best_eval["y_pred"]),
                q_lower_bound_db=float(best_eval["q_lower"]),
                total_uncertainty_db=float(best_eval["u_total"]),
                risk_adjusted_utility_db=float(best_eval["r_adj"]),
                explanation=f"Selected {best_cand_id} ({best_eval['tier']}) as optimal entry link (R_adj={best_eval['r_adj']:.1f}dB, Latency={best_eval['est_latency_ms']:.1f}ms).",
            )
            self.decision_history.append(decision)
            return decision

        # Case 2: User is currently served
        curr_eval = candidate_evaluations[current_serving_id]

        # Check for urgent trigger reasons
        if curr_eval["is_satellite_departing"]:
            trigger_code = "PROACTIVE_SATELLITE_DESCENT"
            explanation = f"Proactive handover from {current_serving_id} triggered: remaining visibility {curr_eval['vis_s']:.1f}s < threshold {self.ho_margin_s}s."
            is_ho = (best_cand_id != current_serving_id)
            selected = best_cand_id
        elif curr_eval["q_lower"] < self.outage_thresh_db:
            trigger_code = "PREDICTED_OUTAGE_AVOIDANCE"
            explanation = f"Handover triggered: lower confidence bound {curr_eval['q_lower']:.1f}dB breaches outage threshold {self.outage_thresh_db}dB."
            is_ho = (best_cand_id != current_serving_id)
            selected = best_cand_id
        elif curr_eval["u_total"] > 4.5 and best_eval["u_total"] < 2.5:
            trigger_code = "UNCERTAINTY_AVOIDANCE"
            explanation = f"Handover to {best_cand_id} triggered to escape high-flutter channel (Current U={curr_eval['u_total']:.1f}dB vs Target U={best_eval['u_total']:.1f}dB)."
            is_ho = (best_cand_id != current_serving_id)
            selected = best_cand_id
        elif user_service_type == "URLLC" and curr_eval["tier"] == "LEO" and best_eval["tier"] in ["TBS", "UAV", "HAPS"] and best_eval["est_latency_ms"] <= 10.0:
            trigger_code = "URLLC_LATENCY_OPTIMIZATION"
            explanation = f"Offloaded URLLC user from LEO to {best_cand_id} ({best_eval['tier']}) to meet 10ms SLA (Estimated delay {best_eval['est_latency_ms']:.1f}ms)."
            is_ho = (best_cand_id != current_serving_id)
            selected = best_cand_id
        elif (best_cand_id != current_serving_id) and (best_eval["r_adj"] > curr_eval["r_adj"] + self.hysteresis_db):
            trigger_code = "HYSTERESIS_UTILITY_IMPROVEMENT"
            explanation = f"Target {best_cand_id} exceeds current link by {best_eval['r_adj'] - curr_eval['r_adj']:.1f}dB (> {self.hysteresis_db}dB hysteresis margin)."
            is_ho = True
            selected = best_cand_id
        else:
            trigger_code = "STEADY_STATE_OPTIMAL"
            explanation = f"Retaining current connection {current_serving_id} ({curr_eval['tier']}); link adheres to all SLA boundaries (R_adj={curr_eval['r_adj']:.1f}dB)."
            is_ho = False
            selected = current_serving_id

        sel_eval = candidate_evaluations[selected]
        decision = ExplainableDecision(
            user_id=user_id,
            selected_node_id=selected,
            previous_node_id=current_serving_id,
            tier=sel_eval["tier"],
            is_handover=is_ho,
            trigger_code=trigger_code,
            predicted_sinr_db=float(sel_eval["y_pred"]),
            q_lower_bound_db=float(sel_eval["q_lower"]),
            total_uncertainty_db=float(sel_eval["u_total"]),
            risk_adjusted_utility_db=float(sel_eval["r_adj"]),
            explanation=explanation,
        )
        self.decision_history.append(decision)
        return decision

