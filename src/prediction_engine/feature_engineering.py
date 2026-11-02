"""
ORBIT-INTEL 6G: Feature Engineering for Predictive Link Intelligence
Extracts kinematic, RF, and temporal window features from SAGIN link telemetry.
"""

import numpy as np
import pandas as pd


class FeatureEngineer:
    """
    Transforms raw SAGIN telemetry state sequences into engineered feature vectors
    for multi-horizon link quality and uncertainty estimation.
    """

    FEATURE_NAMES = [
        "current_sinr_db",
        "sinr_rolling_mean_5s",
        "sinr_rolling_std_5s",
        "sinr_trend_slope",
        "elevation_deg",
        "elevation_rate_deg_s",
        "slant_distance_km",
        "doppler_shift_khz",
        "doppler_rate_khz_s",
        "remaining_visibility_s",
        "node_load",
        "available_bandwidth_mhz",
        "tier_leo",
        "tier_haps",
        "tier_uav",
        "tier_tbs",
        "is_visible",
    ]

    @classmethod
    def extract_features_from_history(
        cls, history_records: list[dict], user_id: str, node_id: str
    ) -> dict[str, float]:
        """
        Extracts temporal and kinematic features from a window of telemetry records.
        history_records: chronological list of telemetry dicts for the specified user-node pair.
        """
        if not history_records:
            return {f: 0.0 for f in cls.FEATURE_NAMES}

        recent = history_records[-1]
        sinr_vals = [r.get("sinr_db", -25.0) for r in history_records[-5:]]
        elev_vals = [r.get("elevation_deg", 0.0) for r in history_records[-5:]]
        doppler_vals = [r.get("doppler_shift_hz", 0.0) / 1000.0 for r in history_records[-5:]]

        # Rolling statistics
        cur_sinr = float(recent.get("sinr_db", -25.0))
        mean_sinr = float(np.mean(sinr_vals))
        std_sinr = float(np.std(sinr_vals)) if len(sinr_vals) > 1 else 0.1

        # Trend slope (linear fit over recent samples)
        if len(sinr_vals) >= 2:
            time_idx = np.arange(len(sinr_vals))
            slope, _ = np.polyfit(time_idx, sinr_vals, 1)
        else:
            slope = 0.0

        # Elevation and elevation rate
        cur_elev = float(recent.get("elevation_deg", 0.0))
        if len(elev_vals) >= 2:
            elev_rate = float(elev_vals[-1] - elev_vals[-2])
        else:
            elev_rate = 0.0

        # Doppler and Doppler rate
        cur_doppler_khz = float(recent.get("doppler_shift_hz", 0.0)) / 1000.0
        if len(doppler_vals) >= 2:
            doppler_rate = float(doppler_vals[-1] - doppler_vals[-2])
        else:
            doppler_rate = 0.0

        tier = recent.get("tier", "TBS")

        return {
            "current_sinr_db": cur_sinr,
            "sinr_rolling_mean_5s": mean_sinr,
            "sinr_rolling_std_5s": std_sinr,
            "sinr_trend_slope": float(slope),
            "elevation_deg": cur_elev,
            "elevation_rate_deg_s": elev_rate,
            "slant_distance_km": float(recent.get("slant_distance_m", 1000.0)) / 1000.0,
            "doppler_shift_khz": cur_doppler_khz,
            "doppler_rate_khz_s": doppler_rate,
            "remaining_visibility_s": float(recent.get("remaining_visibility_s", 0.0)),
            "node_load": float(recent.get("load", 0.0)),
            "available_bandwidth_mhz": float(recent.get("bandwidth_mhz", 50.0)),
            "tier_leo": 1.0 if tier == "LEO" else 0.0,
            "tier_haps": 1.0 if tier == "HAPS" else 0.0,
            "tier_uav": 1.0 if tier == "UAV" else 0.0,
            "tier_tbs": 1.0 if tier == "TBS" else 0.0,
            "is_visible": 1.0 if recent.get("is_visible", False) else 0.0,
        }

    @classmethod
    def to_feature_vector(cls, feature_dict: dict[str, float]) -> np.ndarray:
        return np.array([feature_dict.get(k, 0.0) for k in cls.FEATURE_NAMES], dtype=np.float32)

