"""
ORBIT-INTEL 6G: Baseline Method 3 (M3) — Prediction-Only AI (Uncertainty-Unaware)
Leverages AI forecasted link quality, but deliberately ignores prediction uncertainty.
"""

from typing import Optional
import numpy as np


class M3PredictionOnlyBaseline:
    """
    Conventional Predictive AI baseline.
    Uses AI point predictions (expected median SINR) for proactive orchestration.
    Does NOT quantify or penalize prediction uncertainty (epistemic/aleatoric risk = 0).
    Demonstrates vulnerability of uncalibrated AI under stochastic channel flutter.
    """

    def __init__(self, hysteresis_db: float = 2.0):
        self.hysteresis_db = hysteresis_db
        self.name = "M3_Prediction_Only"

    def select_network_node(
        self,
        user_id: str,
        current_serving_id: Optional[str],
        available_links: dict[str, dict],
        predicted_qualities: dict[str, float],
        user_service_type: str = "URLLC",
    ) -> dict:
        """
        Selects tier maximizing predicted future link quality:
        argmax_{j} Q_hat_j(t + Delta)
        No uncertainty penalty applied.
        """
        viable_nodes = {
            n_id: data for n_id, data in available_links.items()
            if data["is_visible"] and n_id in predicted_qualities
        }

        if not viable_nodes:
            return {
                "selected_node_id": None,
                "is_handover": False,
                "decision_reason": "M3_OUTAGE_NO_VISIBLE_PREDICTED_NODE",
                "risk_score": 1.0,
            }

        # Select candidate with highest point prediction
        best_cand_id = max(viable_nodes.keys(), key=lambda nid: predicted_qualities[nid])
        best_pred_sinr = predicted_qualities[best_cand_id]

        if current_serving_id in viable_nodes:
            curr_pred_sinr = predicted_qualities[current_serving_id]

            # Handover triggered if best predicted alternative exceeds current by hysteresis
            if (best_cand_id != current_serving_id) and (best_pred_sinr > curr_pred_sinr + self.hysteresis_db):
                return {
                    "selected_node_id": best_cand_id,
                    "is_handover": True,
                    "decision_reason": f"M3_PROACTIVE_AI_TRIGGER (Curr_pred={curr_pred_sinr:.1f}dB -> Target_pred={best_pred_sinr:.1f}dB)",
                    "risk_score": 0.35,
                }
            else:
                return {
                    "selected_node_id": current_serving_id,
                    "is_handover": False,
                    "decision_reason": f"M3_HOLD_CURRENT (Curr_pred={curr_pred_sinr:.1f}dB)",
                    "risk_score": 0.2 if curr_pred_sinr > 10.0 else 0.6,
                }

        return {
            "selected_node_id": best_cand_id,
            "is_handover": (current_serving_id is not None),
            "decision_reason": f"M3_INITIAL_SELECTION (Pred={best_pred_sinr:.1f}dB)",
            "risk_score": 0.3,
        }

