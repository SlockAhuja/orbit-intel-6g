"""
ORBIT-INTEL 6G: Traffic and Packet Transmission Engine
Simulates packet generation, transmission delay, queue dynamics, and QoS compliance.
"""

import numpy as np


class TrafficEngine:
    """
    Manages packet generation, latency accounting, and delivery metrics.
    """

    def __init__(self, speed_of_light: float = 3.0e8):
        self.c = speed_of_light

    def compute_transmission_delay_ms(
        self,
        slant_distance_m: float,
        packet_size_bytes: int,
        allocated_rate_mbps: float,
        node_load: float,
        tier: str,
    ) -> dict[str, float]:
        """
        Computes decomposed end-to-end latency:
        T_e2e = T_prop + T_trans + T_queue + T_proc
        """
        # Propagation delay (one-way) in ms
        t_prop_ms = (slant_distance_m / self.c) * 1000.0

        # Transmission delay
        packet_bits = packet_size_bytes * 8.0
        rate_bps = max(allocated_rate_mbps, 0.1) * 1.0e6
        t_trans_ms = (packet_bits / rate_bps) * 1000.0

        # Queuing delay based on M/M/1 approximation
        # As load approaches 1.0, queuing delay escalates
        base_queue_ms = 0.5
        rho = np.clip(node_load, 0.0, 0.98)
        t_queue_ms = base_queue_ms / (1.0 - rho)

        # Processing delay by tier
        tier_proc_map = {
            "LEO": 2.5,   # Satellite on-board processing
            "HAPS": 1.2,  # Stratospheric edge server
            "UAV": 0.8,   # Tactical edge node
            "TBS": 0.3,   # Terrestrial fiber-connected BBU
        }
        t_proc_ms = tier_proc_map.get(tier, 1.0)

        t_total_ms = t_prop_ms + t_trans_ms + t_queue_ms + t_proc_ms

        return {
            "t_prop_ms": float(t_prop_ms),
            "t_trans_ms": float(t_trans_ms),
            "t_queue_ms": float(t_queue_ms),
            "t_proc_ms": float(t_proc_ms),
            "t_total_ms": float(t_total_ms),
        }

    def evaluate_packet_success(
        self,
        sinr_db: float,
        sinr_threshold_db: float,
        total_latency_ms: float,
        max_latency_ms: float,
        is_handover_in_progress: bool = False,
        rng=None,
    ) -> bool:
        """
        Determines whether a packet was successfully delivered under physical SINR
        and latency constraints.
        """
        if rng is None:
            rng = np.random.default_rng()

        # Handover interruption penalty: 15% packet drop probability during re-association
        if is_handover_in_progress and rng.random() < 0.15:
            return False

        # SINR threshold check
        if sinr_db < sinr_threshold_db:
            return False

        # Latency SLA constraint
        if total_latency_ms > max_latency_ms:
            return False

        # Physical layer Block Error Rate (BLER) curve model
        margin_db = sinr_db - sinr_threshold_db
        if margin_db > 6.0:
            bler = 1e-4
        elif margin_db > 2.0:
            bler = 0.01
        else:
            bler = 0.08

        return bool(rng.random() > bler)

