"""
ORBIT-INTEL 6G: Confidence-Aware Predictive Reliability Orchestration (CAPRO) Engine
Implements mathematically rigorous, unit-normalized multi-attribute utility optimization,
explicit reliability and latency eligibility constraints, and hysteresis-gated handover controls.
"""

from typing import Optional
from dataclasses import dataclass, field
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
    risk_adjusted_utility_db: float  # Normalized utility J in [0, 1]
    explanation: str
    fallback_used: bool = False
    eligible_candidates: list[str] = field(default_factory=list)


class CAPROOrchestrator:
    """
    Confidence-Aware Predictive Reliability Orchestration (CAPRO) Engine.
    Coordinates 4-tier SAGIN resources using:
    1. Hard Feasibility Filter F_u(t) (Reliability, Latency, Visibility, Orbital buffer)
    2. Dimensionless Multi-Objective Utility J in [0, 1] (Link quality, Latency, Capacity, Handover, Epistemic Risk)
    3. Hysteresis Gating (Delta_hyst) to suppress false alarm handover churn
    4. Deterministic Graceful Fallback for extreme stress conditions
    """

    def __init__(
        self,
        risk_aversion_kappa: float = 1.5,
        hysteresis_margin_db: float = 2.5,
        handover_margin_s: float = 12.0,
        outage_sinr_threshold_db: float = 3.0,
        ablation_mode: Optional[str] = None,
    ):
        self.kappa = risk_aversion_kappa
        self.hysteresis_margin = 0.08  # Normalized scale (~2.4 dB on 30 dB span)
        self.hysteresis_db = hysteresis_margin_db
        self.ho_margin_s = handover_margin_s
        self.outage_thresh_db = outage_sinr_threshold_db
        self.ablation_mode = ablation_mode or "FullCAPRO"
        self.name = f"M4_CAPRO_{self.ablation_mode}" if ablation_mode else "M4_CAPRO"

        # Normalized weight vectors (convex simplex sum = 1.0)
        self.weights_urllc = {
            "w_link": 0.35,
            "w_lat": 0.35,
            "w_cap": 0.10,
            "w_ho": 0.15,
            "w_risk": 0.05,
        }
        self.weights_embb = {
            "w_link": 0.40,
            "w_lat": 0.15,
            "w_cap": 0.30,
            "w_ho": 0.10,
            "w_risk": 0.05,
        }

        # Apply ablation adjustments if specified
        if self.ablation_mode == "NoHandoverCost":
            self.weights_urllc["w_ho"] = 0.0
            self.weights_embb["w_ho"] = 0.0
            self.hysteresis_margin = 0.0
        elif self.ablation_mode in ["NoUncertainty", "AleatoricOnly"]:
            self.weights_urllc["w_risk"] = 0.0
            self.weights_embb["w_risk"] = 0.0

        # Log of explainable decisions
        self.decision_history: list[ExplainableDecision] = []

    def compute_estimated_latency(self, link: dict) -> float:
        """Computes physical end-to-end one-way delay decomposition in milliseconds."""
        slant_km = float(link.get("slant_distance_m", 1000.0)) / 1000.0
        tier = link.get("tier", "TBS")
        node_load = float(link.get("load", 0.0))

        # 1. Slant propagation delay (speed of light: 300 km/ms)
        t_prop_ms = slant_km / 300.0

        # 2. Feeder and processing delay
        if tier == "LEO":
            t_feeder_ms = 3.2
            t_proc_ms = 2.5
        elif tier == "HAPS":
            t_feeder_ms = 0.8
            t_proc_ms = 1.2
        elif tier == "UAV":
            t_feeder_ms = 0.2
            t_proc_ms = 0.8
        else:  # TBS
            t_feeder_ms = 0.0
            t_proc_ms = 0.5

        # 3. Queueing delay
        t_queue_ms = 0.5 / max(1.0 - node_load, 0.05)

        # 4. Over-the-air transmission
        t_trans_ms = 0.1

        return float(t_prop_ms + t_feeder_ms + t_proc_ms + t_queue_ms + t_trans_ms)

    def compute_normalized_utility(
        self,
        y_pred_db: float,
        q_lower_db: float,
        epistemic_std_db: float,
        latency_ms: float,
        node_load: float,
        is_current_serving: bool,
        service_type: str = "URLLC",
    ) -> dict[str, float]:
        """
        Computes dimensionless multi-objective utility J in [0, 1] using strictly normalized terms:
        J = w1*U_link + w2*U_latency + w3*U_capacity - w4*C_handover - w5*C_risk
        """
        w = self.weights_urllc if service_type == "URLLC" else self.weights_embb
        l_max = 10.0 if service_type == "URLLC" else 50.0

        # 1. Normalized Link Quality Utility U_link in [0, 1]
        # In NoUncertainty / EpistemicOnly ablations, uses y_pred; otherwise uses median forecast
        u_link = float(np.clip((y_pred_db - 0.0) / 30.0, 0.0, 1.0))

        # 2. Normalized Latency Utility U_latency in [0, 1]
        u_lat = float(1.0 - np.clip((latency_ms - 1.0) / max(l_max - 1.0, 1.0), 0.0, 1.0))

        # 3. Normalized Available Capacity Utility U_capacity in [0, 1]
        u_cap = float(1.0 - np.clip(node_load, 0.0, 1.0))

        # 4. Normalized Handover Cost C_handover in {0, 1}
        c_ho = 0.0 if is_current_serving else 1.0

        # 5. Normalized Epistemic Risk Cost C_risk in [0, 1]
        c_risk = float(np.clip(epistemic_std_db / 3.0, 0.0, 1.0))

        # Synthesize normalized utility J
        j_score = (
            w["w_link"] * u_link
            + w["w_lat"] * u_lat
            + w["w_cap"] * u_cap
            - w["w_ho"] * c_ho
            - w["w_risk"] * c_risk
        )

        return {
            "j_score": float(j_score),
            "u_link": u_link,
            "u_lat": u_lat,
            "u_cap": u_cap,
            "c_ho": c_ho,
            "c_risk": c_risk,
        }

    def filter_eligible_nodes(
        self,
        available_links: dict[str, dict],
        predictions: dict[str, dict],
        service_type: str = "URLLC",
    ) -> tuple[dict[str, dict], bool, str]:
        """
        Enforces hard feasibility constraints F_u(t):
        - Visibility and radio coverage
        - Reliability lower-bound (q_05 >= 3.0 dB)
        - Latency SLA (L <= L_max)
        - Orbital departure buffer (T_vis >= 12.0 s for LEO)
        Returns: (candidate_dict, fallback_used, fallback_tag)
        """
        l_max = 10.0 if service_type == "URLLC" else 50.0
        eligible = {}
        fallback_used = False
        fallback_tag = "FEASIBLE_SET_VALID"

        for n_id, link in available_links.items():
            if not link.get("is_visible", False):
                continue

            pred = predictions.get(n_id)
            if not pred:
                continue

            y_pred = float(pred.get("y_pred", -25.0))
            q_lower = float(pred.get("q_lower", y_pred - 5.0))
            epistemic_std = float(pred.get("epistemic_std", pred.get("total_uncertainty", 1.0) * 0.1))
            total_unc = float(pred.get("total_uncertainty", 1.0))
            tier = link.get("tier", "TBS")
            node_load = float(link.get("load", 0.0))
            vis_s = float(link.get("remaining_visibility_s", 9999.0))
            est_latency = self.compute_estimated_latency(link)

            # Check Hard Feasibility Constraints
            # In NoReliabilityConstraint ablation, ignore q_lower check
            rel_ok = True
            if self.ablation_mode != "NoReliabilityConstraint":
                check_bound = y_pred if self.ablation_mode in ["NoUncertainty", "EpistemicOnly"] else q_lower
                rel_ok = (check_bound >= self.outage_thresh_db)

            # In NoLatencyConstraint ablation, ignore latency check
            lat_ok = True
            if self.ablation_mode != "NoLatencyConstraint":
                lat_ok = (est_latency <= l_max)

            # Orbital departure buffer check for LEO
            orb_ok = (tier != "LEO") or (vis_s >= self.ho_margin_s)

            is_feasible = (rel_ok and lat_ok and orb_ok)

            cand_info = {
                "n_id": n_id,
                "tier": tier,
                "y_pred": y_pred,
                "q_lower": q_lower,
                "epistemic_std": epistemic_std,
                "total_unc": total_unc,
                "est_latency": est_latency,
                "node_load": node_load,
                "vis_s": vis_s,
                "rel_ok": rel_ok,
                "lat_ok": lat_ok,
                "orb_ok": orb_ok,
                "is_feasible": is_feasible,
            }

            if is_feasible:
                eligible[n_id] = cand_info

        # Fallback Protocol if F_u(t) is empty
        if not eligible:
            fallback_used = True
            # Stage 1 Fallback: Relax latency constraint for visible candidates satisfying reliability
            lat_relaxed = {
                nid: c for nid, c in available_links.items()
                if c.get("is_visible") and predictions.get(nid)
                and predictions[nid].get("q_lower", predictions[nid]["y_pred"]) >= self.outage_thresh_db
                and ((c.get("tier") != "LEO") or (c.get("remaining_visibility_s", 0) >= self.ho_margin_s))
            }
            if lat_relaxed:
                fallback_tag = "FALLBACK_RELAXED_LATENCY_SLA"
                for nid in lat_relaxed:
                    p = predictions[nid]
                    l = available_links[nid]
                    eligible[nid] = {
                        "n_id": nid,
                        "tier": l.get("tier"),
                        "y_pred": float(p["y_pred"]),
                        "q_lower": float(p.get("q_lower", p["y_pred"])),
                        "epistemic_std": float(p.get("epistemic_std", 0.2)),
                        "total_unc": float(p.get("total_uncertainty", 1.0)),
                        "est_latency": self.compute_estimated_latency(l),
                        "node_load": float(l.get("load", 0.0)),
                        "vis_s": float(l.get("remaining_visibility_s", 9999.0)),
                        "rel_ok": True,
                        "lat_ok": False,
                        "orb_ok": True,
                        "is_feasible": False,
                    }
            else:
                # Stage 2 Fallback: All links degraded; pick visible candidates maximizing lower bound
                visible_nodes = [
                    nid for nid, c in available_links.items()
                    if c.get("is_visible") and predictions.get(nid)
                ]
                if visible_nodes:
                    fallback_tag = "FALLBACK_MAX_RESIDUAL_SINR"
                    for nid in visible_nodes:
                        p = predictions[nid]
                        l = available_links[nid]
                        eligible[nid] = {
                            "n_id": nid,
                            "tier": l.get("tier"),
                            "y_pred": float(p["y_pred"]),
                            "q_lower": float(p.get("q_lower", p["y_pred"])),
                            "epistemic_std": float(p.get("epistemic_std", 0.5)),
                            "total_unc": float(p.get("total_uncertainty", 2.0)),
                            "est_latency": self.compute_estimated_latency(l),
                            "node_load": float(l.get("load", 0.0)),
                            "vis_s": float(l.get("remaining_visibility_s", 0.0)),
                            "rel_ok": False,
                            "lat_ok": False,
                            "orb_ok": False,
                            "is_feasible": False,
                        }

        return eligible, fallback_used, fallback_tag

    def select_network_node(
        self,
        user_id: str,
        current_serving_id: Optional[str],
        available_links: dict[str, dict],
        predictions: dict[str, dict],
        user_service_type: str = "URLLC",
    ) -> ExplainableDecision:
        """
        Executes reliability-constrained, normalized utility network selection.
        """
        # Step 1: Filter candidate nodes through hard feasibility constraints
        eligible_cands, fallback_used, fallback_tag = self.filter_eligible_nodes(
            available_links, predictions, user_service_type
        )

        # Global Outage: Zero candidates even after fallback
        if not eligible_cands:
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
                risk_adjusted_utility_db=0.0,
                explanation="No viable SAGIN node visible above operational elevation masks.",
                fallback_used=True,
                eligible_candidates=[],
            )
            self.decision_history.append(decision)
            return decision

        # Step 2: Compute dimensionless normalized utilities J_{u,j} for all eligible candidates
        evaluated_cands = {}
        for n_id, c in eligible_cands.items():
            is_curr = (n_id == current_serving_id)
            util_info = self.compute_normalized_utility(
                y_pred_db=c["y_pred"],
                q_lower_db=c["q_lower"],
                epistemic_std_db=c["epistemic_std"],
                latency_ms=c["est_latency"],
                node_load=c["node_load"],
                is_current_serving=is_curr,
                service_type=user_service_type,
            )
            evaluated_cands[n_id] = {**c, **util_info}

        # Step 3: Find candidate maximizing normalized utility
        best_cand_id = max(evaluated_cands.keys(), key=lambda nid: evaluated_cands[nid]["j_score"])
        best_eval = evaluated_cands[best_cand_id]

        # Case A: Initial network entry (user not yet connected)
        if current_serving_id is None or current_serving_id not in available_links:
            trigger_code = fallback_tag if fallback_used else "INITIAL_OPTIMAL_ATTACH"
            decision = ExplainableDecision(
                user_id=user_id,
                selected_node_id=best_cand_id,
                previous_node_id=current_serving_id,
                tier=best_eval["tier"],
                is_handover=(current_serving_id is not None),
                trigger_code=trigger_code,
                predicted_sinr_db=float(best_eval["y_pred"]),
                q_lower_bound_db=float(best_eval["q_lower"]),
                total_uncertainty_db=float(best_eval["total_unc"]),
                risk_adjusted_utility_db=float(best_eval["j_score"]),
                explanation=(
                    f"Initial connection to {best_cand_id} ({best_eval['tier']}) as optimal entry node "
                    f"(Normalized Utility J={best_eval['j_score']:.3f}, Delay={best_eval['est_latency']:.1f}ms)."
                    if not fallback_used else
                    f"Initial connection via {fallback_tag}: selected {best_cand_id} ({best_eval['tier']})."
                ),
                fallback_used=fallback_used,
                eligible_candidates=list(evaluated_cands.keys()),
            )
            self.decision_history.append(decision)
            return decision

        # Case B: User currently served
        curr_link = available_links[current_serving_id]
        curr_pred = predictions.get(current_serving_id, {})
        curr_vis_s = float(curr_link.get("remaining_visibility_s", 9999.0))
        curr_tier = curr_link.get("tier", "TBS")
        curr_q_lower = float(curr_pred.get("q_lower", curr_pred.get("y_pred", 15.0)))
        curr_est_lat = self.compute_estimated_latency(curr_link)
        l_max = 10.0 if user_service_type == "URLLC" else 50.0

        # Check feasibility of current serving link
        is_curr_setting = (curr_tier == "LEO" and curr_vis_s < self.ho_margin_s)
        is_curr_fading = (curr_q_lower < self.outage_thresh_db)
        is_curr_lat_violating = (user_service_type == "URLLC" and curr_est_lat > l_max and curr_tier == "LEO")

        # Decision Logic:
        # 1. Urgent Override if current link is setting or fading
        if is_curr_setting:
            trigger_code = "PROACTIVE_SATELLITE_DESCENT"
            explanation = (
                f"Proactive handover from {current_serving_id} triggered: remaining satellite visibility "
                f"{curr_vis_s:.1f}s is below safety margin {self.ho_margin_s:.1f}s."
            )
            selected = best_cand_id
            is_ho = (best_cand_id != current_serving_id)

        elif is_curr_fading:
            trigger_code = "PREDICTED_OUTAGE_AVOIDANCE"
            explanation = (
                f"Proactive handover triggered: lower confidence bound on {current_serving_id} "
                f"({curr_q_lower:.1f}dB) breaches minimum outage threshold {self.outage_thresh_db:.1f}dB."
            )
            selected = best_cand_id
            is_ho = (best_cand_id != current_serving_id)

        elif is_curr_lat_violating and best_eval["tier"] in ["TBS", "HAPS", "UAV"] and best_eval["est_latency"] <= l_max:
            trigger_code = "URLLC_LATENCY_OPTIMIZATION"
            explanation = (
                f"Offloaded URLLC user from {current_serving_id} (LEO delay {curr_est_lat:.1f}ms) to "
                f"{best_cand_id} ({best_eval['tier']} delay {best_eval['est_latency']:.1f}ms) to meet 10ms SLA."
            )
            selected = best_cand_id
            is_ho = (best_cand_id != current_serving_id)

        elif fallback_used:
            trigger_code = fallback_tag
            explanation = f"Fallback policy executed ({fallback_tag}): selected {best_cand_id} with maximal residual utility."
            selected = best_cand_id
            is_ho = (best_cand_id != current_serving_id)

        # 2. Opportunistic Migration (Hysteresis Gated)
        elif current_serving_id in evaluated_cands:
            curr_eval = evaluated_cands[current_serving_id]
            delta_j = best_eval["j_score"] - curr_eval["j_score"]

            if (best_cand_id != current_serving_id) and (delta_j > self.hysteresis_margin):
                trigger_code = "HYSTERESIS_UTILITY_IMPROVEMENT"
                explanation = (
                    f"Handover to {best_cand_id} triggered: normalized utility improvement Delta_J={delta_j:.3f} "
                    f"exceeds hysteresis margin {self.hysteresis_margin:.3f} (~2.4 dB gain)."
                )
                selected = best_cand_id
                is_ho = True
            else:
                trigger_code = "STEADY_STATE_OPTIMAL"
                explanation = (
                    f"Maintaining active connection on {current_serving_id} ({curr_eval['tier']}); "
                    f"link is fully SLA compliant and alternative candidates do not exceed hysteresis margin."
                )
                selected = current_serving_id
                is_ho = False
        else:
            trigger_code = "HYSTERESIS_UTILITY_IMPROVEMENT"
            explanation = f"Current node {current_serving_id} is no longer eligible; migrating to {best_cand_id}."
            selected = best_cand_id
            is_ho = True

        sel_eval = evaluated_cands[selected]
        decision = ExplainableDecision(
            user_id=user_id,
            selected_node_id=selected,
            previous_node_id=current_serving_id,
            tier=sel_eval["tier"],
            is_handover=is_ho,
            trigger_code=trigger_code,
            predicted_sinr_db=float(sel_eval["y_pred"]),
            q_lower_bound_db=float(sel_eval["q_lower"]),
            total_uncertainty_db=float(sel_eval["total_unc"]),
            risk_adjusted_utility_db=float(sel_eval["j_score"]),
            explanation=explanation,
            fallback_used=fallback_used,
            eligible_candidates=list(evaluated_cands.keys()),
        )
        self.decision_history.append(decision)
        return decision
