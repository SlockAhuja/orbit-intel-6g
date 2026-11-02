"""
ORBIT-INTEL 6G: Doppler Shift and Kinematic Rate Modeling
Calculates relative velocity projections, carrier Doppler displacement, and Doppler rate.
"""

import numpy as np


class DopplerModel:
    """
    Computes Doppler frequency shifts and rate of change of Doppler for SAGIN nodes.
    Supports S-band (2.0 GHz) and Ka-band (28.0 GHz) carrier frequencies.
    """

    def __init__(self, speed_of_light: float = 3.0e8):
        self.c = speed_of_light

    def compute_los_velocity(
        self,
        node_pos: np.ndarray,
        node_vel: np.ndarray,
        user_pos: np.ndarray,
        user_vel: np.ndarray,
    ) -> tuple[float, float]:
        """
        Calculates line-of-sight relative velocity and slant distance.
        v_los = (v_node - v_user) . u_los
        """
        diff_pos = node_pos - user_pos
        distance = float(np.linalg.norm(diff_pos))
        if distance < 1e-3:
            return 0.0, 0.0

        u_los = diff_pos / distance
        diff_vel = node_vel - user_vel
        v_los = float(np.dot(diff_vel, u_los))

        return v_los, distance

    def compute_doppler_shift(
        self,
        node_pos: np.ndarray,
        node_vel: np.ndarray,
        user_pos: np.ndarray,
        user_vel: np.ndarray,
        carrier_freq_hz: float,
    ) -> dict[str, float]:
        """
        Computes instantaneous Doppler shift in Hz.
        f_d = f_c * (v_los / c)
        """
        fc = float(carrier_freq_hz)
        v_los, distance = self.compute_los_velocity(node_pos, node_vel, user_pos, user_vel)
        # Physical Doppler: f_d = -f_c * (v_los / c) where v_los is range rate dr/dt.
        # When node approaches observer (v_los < 0), received frequency increases (f_d > 0).
        doppler_hz = float(-fc * (v_los / self.c))

        return {
            "v_los_m_s": v_los,
            "slant_distance_m": distance,
            "doppler_shift_hz": doppler_hz,
            "normalized_doppler": float(doppler_hz / fc),
        }

    def compute_doppler_rate(
        self, current_doppler_hz: float, previous_doppler_hz: float, delta_t_s: float
    ) -> float:
        """
        Computes Doppler rate (Hz/s).
        dot{f}_d = (f_d(t) - f_d(t-dt)) / dt
        """
        if delta_t_s <= 1e-6:
            return 0.0
        return float((current_doppler_hz - previous_doppler_hz) / delta_t_s)
