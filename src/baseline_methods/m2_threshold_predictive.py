"""
ORBIT-INTEL 6G: Baseline Method 2 (M2) — Threshold-Based Predictive Method
Applies linear trend extrapolation and deterministic fixed threshold triggers.
"""

from typing import Optional


class M2ThresholdPredictiveBaseline:
    """
    Fixed-Threshold Predictive Baseline.
    Extrapolates SINR trend over lookahead horizon Delta.
    Initiates proactive handover if predicted SINR drops below static threshold.
    Does not account for model uncertainty or multi-tier load.
    """

    def __init__(
        self,
        predicted_sinr_threshold_db: float = 10.0,
        lookahead_horizon_s: float = 10.0,
    ):
        self.thresh_db = predicted_sinr_threshold_db
        self.horizon_s = lookahead_horizon_s
        self.name = "M2_Threshold_Predictive"

    def select_network_node(
        self,
        user_id: str,
        current_serving_id: Optional[str],
        available_links: dict[str, dict],
        link_features: dict[str, dict],
        user_service_type: str = "URLLC",
    ) -> dict:
        """
        Predicts future SINR via linear extrapolation:
        Q_hat = cur_sinr + slope * horizon
        """
        predicted_qualities = {}
        for n_id, data in available_links.items():
            if not data["is_visible"]:
                continue
            cur_sinr = data["sinr_db"]
            feat = link_features.get(n_id, {})
            slope = feat.get("sinr_trend_slope", 0.0)
            pred_sinr = cur_sinr + slope * self.horizon_s
            predicted_qualities[n_id] = pred_sinr

        if not predicted_qualities:
            return {
                "selected_node_id": None,
                "is_handover": False,
                "decision_reason": "M2_PREDICTED_OUTAGE_NO_VISIBLE_NODE",
                "risk_score": 1.0,
            }

        # Check current node predicted quality
        if current_serving_id in predicted_qualities:
            curr_pred = predicted_qualities[current_serving_id]
            best_cand_id = max(predicted_qualities.keys(), key=lambda nid: predicted_qualities[nid])
            best_pred = predicted_qualities[best_cand_id]

            # If current predicted SINR falls below threshold and better option exists
            if curr_pred < self.thresh_db and best_cand_id != current_serving_id:
                return {
                    "selected_node_id": best_cand_id,
                    "is_handover": True,
                    "decision_reason": f"M2_PROACTIVE_THRESHOLD_BREACH (Pred={curr_pred:.1f}dB < {self.thresh_db}dB -> Target={best_pred:.1f}dB)",
                    "risk_score": 0.4,
                }
            else:
                return {
                    "selected_node_id": current_serving_id,
                    "is_handover": False,
                    "decision_reason": f"M2_HOLD_PREDICTED_ADEQUATE (Pred={curr_pred:.1f}dB)",
                    "risk_score": 0.2 if curr_pred > 12.0 else 0.5,
                }

        # Initial attach
        best_id = max(predicted_qualities.keys(), key=lambda nid: predicted_qualities[nid])
        return {
            "selected_node_id": best_id,
            "is_handover": (current_serving_id is not None),
            "decision_reason": f"M2_INITIAL_SELECTION (Pred={predicted_qualities[best_id]:.1f}dB)",
            "risk_score": 0.3,
        }

