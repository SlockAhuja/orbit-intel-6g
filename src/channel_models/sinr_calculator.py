"""
ORBIT-INTEL 6G: Antenna Radiation Patterns, Link Budget, and SINR Calculator
Implements 3GPP TR 38.811 antenna beamforming and multi-tier interference aggregation.
"""

import numpy as np


class SINRCalculator:
    """
    Computes received signal power, thermal noise floor, multi-tier interference,
    and resulting instantaneous SINR in dB.
    """

    def __init__(
        self,
        boltzmann_k: float = 1.380649e-23,
        temperature_k: float = 290.0,
        noise_figure_db: float = 7.0,
    ):
        self.k_b = boltzmann_k
        self.t_sys = temperature_k
        self.nf_db = noise_figure_db

    def compute_antenna_gain(
        self,
        off_axis_angle_deg: float,
        max_gain_dbi: float,
        beamwidth_3db_deg: float = 4.0,
        sidelobe_floor_dbi: float = -15.0,
    ) -> float:
        """
        3GPP TR 38.811 parabolic roll-off antenna radiation pattern.
        G(theta) = max(G_max - 12 * (theta / theta_3dB)^2, G_sidelobe)
        """
        theta = np.abs(off_axis_angle_deg)
        attenuation_db = 12.0 * ((theta / max(beamwidth_3db_deg, 0.1)) ** 2)
        gain_dbi = max_gain_dbi - attenuation_db
        return float(np.maximum(gain_dbi, sidelobe_floor_dbi))

    def compute_noise_power_watts(self, bandwidth_hz: float) -> float:
        """
        Calculates thermal noise power in Watts:
        P_n = k_B * T_sys * B * F_linear
        """
        nf_linear = 10.0 ** (self.nf_db / 10.0)
        p_noise_w = self.k_b * self.t_sys * bandwidth_hz * nf_linear
        return float(p_noise_w)

    def compute_noise_power_dbm(self, bandwidth_hz: float) -> float:
        """
        Thermal noise floor in dBm: -174 + 10*log10(B) + NF
        """
        p_watts = self.compute_noise_power_watts(bandwidth_hz)
        return float(10.0 * np.log10(p_watts) + 30.0)

    def calculate_link_budget(
        self,
        tx_power_dbm: float,
        tx_gain_dbi: float,
        rx_gain_dbi: float,
        total_path_loss_db: float,
    ) -> dict[str, float]:
        """
        Computes received signal power (dBm and Watts).
        P_rx = P_tx + G_tx + G_rx - PathLoss
        """
        p_rx_dbm = tx_power_dbm + tx_gain_dbi + rx_gain_dbi - total_path_loss_db
        p_rx_watts = 10.0 ** ((p_rx_dbm - 30.0) / 10.0)

        return {
            "p_rx_dbm": float(p_rx_dbm),
            "p_rx_watts": float(p_rx_watts),
        }

    def compute_sinr(
        self,
        p_rx_watts: float,
        bandwidth_hz: float,
        interference_watts: float = 0.0,
    ) -> dict[str, float]:
        """
        Calculates instantaneous SINR:
        SINR = P_rx / (Interference + Noise)
        """
        p_noise_w = self.compute_noise_power_watts(bandwidth_hz)
        total_impairment_w = max(interference_watts + p_noise_w, 1e-20)
        sinr_linear = max(p_rx_watts / total_impairment_w, 1e-6)
        sinr_db = 10.0 * np.log10(sinr_linear)

        return {
            "p_noise_watts": p_noise_w,
            "interference_watts": interference_watts,
            "sinr_linear": float(sinr_linear),
            "sinr_db": float(sinr_db),
        }

