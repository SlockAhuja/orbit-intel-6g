"""
ORBIT-INTEL 6G: Baseline Method 1 (M1) — Reactive Resource Allocation
Selects communication resources strictly based on current instantaneous link conditions.
"""

from typing import Optional


class M1ReactiveBaseline:
    """
    Conventional reactive resource manager.
    Makes layer and handover decisions based purely on current t instantaneous SINR.
    Triggers handover only after channel deteriorates below reactive margin.
    """

    def __init__(
        self,
        sinr_outage_thresh_db: float = 3.0,
        handover_hysteresis_db: float = 3.0,
    ):
        self.sinr_outage_thresh_db = sinr_outage_thresh_db
        self.handover_hysteresis_db = handover_hysteresis_db
        self.name = "M1_Reactive"

    def select_network_node(
        self,
        user_id: str,
        current_serving_id: Optional[str],
        available_links: dict[str, dict],
        user_service_type: str = "URLLC",
    ) -> dict:
        """
        Selects candidate node with highest current instantaneous SINR.
        No forward prediction or uncertainty quantification.
        """
        # Filter visible nodes with positive capacity
        viable_nodes = {
            n_id: data for n_id, data in available_links.items()
            if data["is_visible"] and data["bandwidth_mhz"] > 0.0
        }

        if not viable_nodes:
            return {
                "selected_node_id": None,
                "is_handover": False,
                "decision_reason": "REACTIVE_OUTAGE_NO_VISIBLE_NODE",
                "risk_score": 1.0,
            }

        # If currently served, check if current node is still adequate
        if current_serving_id in viable_nodes:
            curr_sinr = viable_nodes[current_serving_id]["sinr_db"]
            # Find best alternative
            best_alt_id = max(viable_nodes.keys(), key=lambda nid: viable_nodes[nid]["sinr_db"])
            best_alt_sinr = viable_nodes[best_alt_id]["sinr_db"]

            # Reactive trigger: only switch if current SINR < threshold OR alternative is significantly better
            if (curr_sinr < self.sinr_outage_thresh_db) or (best_alt_sinr > curr_sinr + self.handover_hysteresis_db):
                return {
                    "selected_node_id": best_alt_id,
                    "is_handover": (best_alt_id != current_serving_id),
                    "decision_reason": f"REACTIVE_TRIGGER_BEST_INSTANTANEOUS (SINR={best_alt_sinr:.1f}dB)",
                    "risk_score": 0.5 if best_alt_sinr > 10.0 else 0.8,
                }
            else:
                return {
                    "selected_node_id": current_serving_id,
                    "is_handover": False,
                    "decision_reason": f"REACTIVE_HOLD_CURRENT (SINR={curr_sinr:.1f}dB)",
                    "risk_score": 0.2 if curr_sinr > 10.0 else 0.6,
                }

        # Initial connection or reconnection
        best_id = max(viable_nodes.keys(), key=lambda nid: viable_nodes[nid]["sinr_db"])
        return {
            "selected_node_id": best_id,
            "is_handover": (current_serving_id is not None),
            "decision_reason": f"REACTIVE_INITIAL_ATTACH (SINR={viable_nodes[best_id]['sinr_db']:.1f}dB)",
            "risk_score": 0.3,
        }

