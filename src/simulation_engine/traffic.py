"""
ORBIT-INTEL 6G: Traffic and Comprehensive Latency Accounting Engine
Calculates decomposed delay components:
- One-way radio propagation delay (d / c)
- Radio transmission delay
- Processing delay (on-board payload / edge server / BBU)
- M/M/1 queuing delay
- Gateway backhaul transport delay (for NTN feeder links)
- Round-Trip Time (RTT)
- Total End-to-End Latency
"""

import numpy as np


class TrafficEngine:
    """
    Manages packet generation, decomposed latency accounting, and QoS compliance.
    Strictly enforces speed-of-light propagation bounds:
    Propagation delay = distance / c
    """

    def __init__(self, speed_of_light: float = 3.0e8):
        self.c = float(speed_of_light)

    def compute_transmission_delay_ms(
        self,
        slant_distance_m: float,
        packet_size_bytes: int,
        allocated_rate_mbps: float,
        node_load: float,
        tier: str,
    ) -> dict[str, float]:
        """
        Computes all separated latency metrics:
        1. One-way propagation delay: T_prop = d / c
        2. Transmission delay: T_trans = bits / rate
        3. Queuing delay: T_queue = f(load)
        4. Processing delay: T_proc
        5. Feeder backhaul delay: T_feeder (for LEO NTN gateway link)
        6. Round-Trip Time (RTT): 2 * T_prop + 2 * T_trans + T_proc + T_queue
        7. Total End-to-End Latency: T_prop + T_trans + T_queue + T_proc + T_feeder
        """
        d_m = max(float(slant_distance_m), 1.0)

        # 1. Physical one-way propagation delay strictly bounded by speed of light
        t_prop_ms = (d_m / self.c) * 1000.0

        # 2. Transmission delay
        packet_bits = float(packet_size_bytes) * 8.0
        rate_bps = max(float(allocated_rate_mbps), 0.1) * 1.0e6
        t_trans_ms = (packet_bits / rate_bps) * 1000.0

        # 3. Queuing delay based on M/M/1 approximation
        base_queue_ms = 0.5
        rho = float(np.clip(node_load, 0.0, 0.98))
        t_queue_ms = base_queue_ms / (1.0 - rho)

        # 4. Processing delay by access tier
        tier_proc_map = {
            "LEO": 2.5,   # Satellite on-board regenerative payload & routing
            "HAPS": 1.2,  # Stratospheric edge server
            "UAV": 0.8,   # Tactical edge relay
            "TBS": 0.3,   # Terrestrial fiber-connected BBU/CU
        }
        t_proc_ms = tier_proc_map.get(tier, 1.0)

        # 5. Feeder link gateway backhaul delay
        # LEO satellite packets must traverse a feeder link to a ground station gateway (~600-1200 km slant path)
        if tier == "LEO":
            t_feeder_ms = 3.2  # ~ 960 km feeder path one-way
        elif tier == "HAPS":
            t_feeder_ms = 0.5
        else:
            t_feeder_ms = 0.1  # Fiber terrestrial backhaul

        # 6. One-way radio access delay (terminal to serving node)
        t_access_oneway_ms = t_prop_ms + t_trans_ms + t_proc_ms + t_queue_ms

        # 7. Total End-to-End Latency (terminal through serving node to core network gateway)
        t_e2e_total_ms = t_access_oneway_ms + t_feeder_ms

        # 8. Round-Trip Time (RTT)
        t_rtt_ms = (2.0 * t_prop_ms) + (2.0 * t_trans_ms) + t_proc_ms + t_queue_ms + (2.0 * t_feeder_ms)

        return {
            "t_prop_ms": float(t_prop_ms),
            "t_trans_ms": float(t_trans_ms),
            "t_queue_ms": float(t_queue_ms),
            "t_proc_ms": float(t_proc_ms),
            "t_feeder_ms": float(t_feeder_ms),
            "t_access_oneway_ms": float(t_access_oneway_ms),
            "t_total_ms": float(t_e2e_total_ms),
            "t_e2e_total_ms": float(t_e2e_total_ms),
            "t_rtt_ms": float(t_rtt_ms),
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

        # Handover signaling interruption: 15% packet drop probability during re-association
        if is_handover_in_progress and rng.random() < 0.15:
            return False

        # Physical link SINR threshold check
        if sinr_db < sinr_threshold_db:
            return False

        # Latency SLA constraint check
        if total_latency_ms > max_latency_ms:
            return False

        # 3GPP Block Error Rate (BLER) curve model
        margin_db = sinr_db - sinr_threshold_db
        if margin_db > 6.0:
            bler = 1e-4
        elif margin_db > 2.0:
            bler = 0.01
        else:
            bler = 0.08

        return bool(rng.random() > bler)
