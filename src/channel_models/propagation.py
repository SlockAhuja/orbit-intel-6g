"""
ORBIT-INTEL 6G: Propagation and Path-Loss Channel Models
Implements 3GPP TR 38.811 (Rel-17/18) and ITU-R P.618/P.676 recommendations for SAGIN.
"""

import numpy as np


class PropagationModel:
    """
    Physical channel propagation model calculating Free Space Path Loss,
    atmospheric attenuation, rain attenuation, shadow fading, and multi-path effects.
    """

    def __init__(self, speed_of_light: float = 3.0e8):
        self.c = speed_of_light

    def free_space_path_loss(self, distance_m: float | np.ndarray, frequency_hz: float) -> float | np.ndarray:
        """
        Calculates Free Space Path Loss (FSPL) in dB.
        FSPL = 20 * log10(d) + 20 * log10(f) + 20 * log10(4*pi / c)
        """
        f = float(frequency_hz)
        if isinstance(distance_m, np.ndarray):
            d = np.maximum(distance_m.astype(np.float64), 1.0)
            return 20.0 * np.log10(d) + 20.0 * np.log10(f) + 20.0 * np.log10(4.0 * np.pi / self.c)
        else:
            d = max(float(distance_m), 1.0)
            return float(20.0 * np.log10(d) + 20.0 * np.log10(f) + 20.0 * np.log10(4.0 * np.pi / self.c))

    def atmospheric_gas_attenuation(
        self, elevation_deg: float | np.ndarray, frequency_hz: float
    ) -> float | np.ndarray:
        """
        Calculates atmospheric attenuation based on ITU-R P.676.
        A_atm(theta, f) = A0(f) / [sin(theta) + 0.01 / sqrt(sin^2(theta) + 0.002)]
        """
        freq_ghz = float(frequency_hz) / 1.0e9
        if isinstance(elevation_deg, np.ndarray):
            theta_deg = np.maximum(elevation_deg.astype(np.float64), 2.0)
        else:
            theta_deg = max(float(elevation_deg), 2.0)
        theta_rad = np.radians(theta_deg)

        # Approximate zenith attenuation A0(f) for standard atmosphere (oxygen + water vapor)
        if freq_ghz <= 5.0:
            a0 = 0.035 * (freq_ghz / 2.0)
        elif freq_ghz <= 30.0:
            # Water vapor resonance peak around 22.2 GHz
            a0 = 0.08 + 0.02 * freq_ghz + 0.12 * np.exp(-((freq_ghz - 22.2) ** 2) / 8.0)
        else:
            a0 = 0.15 + 0.01 * freq_ghz

        obliquity_factor = 1.0 / (np.sin(theta_rad) + 0.01 / np.sqrt(np.sin(theta_rad) ** 2 + 0.002))
        return a0 * obliquity_factor

    def rain_attenuation(
        self, elevation_deg: float | np.ndarray, frequency_hz: float, rain_rate_mm_h: float
    ) -> float | np.ndarray:
        """
        ITU-R P.618 rain attenuation model.
        gamma_R = k * R^alpha
        Effective path length: d_eff = (h_rain - h_station) / sin(theta) * reduction_factor
        """
        r_rate = float(rain_rate_mm_h)
        if r_rate <= 0.01:
            return np.zeros_like(elevation_deg) if isinstance(elevation_deg, np.ndarray) else 0.0

        if isinstance(elevation_deg, np.ndarray):
            theta_deg = np.maximum(elevation_deg.astype(np.float64), 5.0)
        else:
            theta_deg = max(float(elevation_deg), 5.0)
        theta_rad = np.radians(theta_deg)
        freq_ghz = float(frequency_hz) / 1.0e9

        # ITU-R P.838 coefficients (circular polarization approximation)
        if freq_ghz < 10.0:
            k = 0.0001 * (freq_ghz ** 2.2)
            alpha = 1.25
        else:
            k = 0.003 * (freq_ghz ** 1.8)
            alpha = 1.05

        gamma_r = k * (rain_rate_mm_h ** alpha)  # dB/km

        # Rain height ~ 3.5 km above sea level
        h_rain_km = 3.5
        h_station_km = 0.0
        slant_path_km = (h_rain_km - h_station_km) / np.sin(theta_rad)

        # Horizontal reduction factor
        d_horiz = slant_path_km * np.cos(theta_rad)
        r001 = 1.0 / (1.0 + 0.78 * np.sqrt(slant_path_km * gamma_r / freq_ghz) - 0.38 * (1.0 - np.exp(-2.0 * d_horiz)))
        d_eff = slant_path_km * np.clip(r001, 0.2, 1.0)

        a_rain = gamma_r * d_eff
        return np.maximum(a_rain, 0.0)

    def shadow_fading(
        self, elevation_deg: float | np.ndarray, std_max_db: float = 8.0, std_min_db: float = 4.0, rng=None
    ) -> float | np.ndarray:
        """
        Elevation-dependent log-normal shadow fading.
        At high elevation (zenith), shadowing standard deviation is lower (LoS unobstructed).
        At low elevation, shadowing is severe.
        """
        if rng is None:
            rng = np.random.default_rng()

        theta_deg = np.clip(elevation_deg, 0.0, 90.0)
        norm_factor = (90.0 - theta_deg) / 90.0
        sigma = std_min_db + norm_factor * (std_max_db - std_min_db)

        if isinstance(elevation_deg, np.ndarray):
            return rng.normal(0.0, sigma, size=len(elevation_deg))
        return float(rng.normal(0.0, sigma))

    def fast_fading_rician(self, k_factor_db: float = 9.0, rng=None) -> float:
        """
        Rician fast fading power gain in dB for Line-of-Sight NTN links.
        K is ratio of dominant LoS component to scattered multi-path power.
        """
        if rng is None:
            rng = np.random.default_rng()

        k_linear = 10.0 ** (k_factor_db / 10.0)
        s = np.sqrt(k_linear / (k_linear + 1.0))
        sigma = np.sqrt(1.0 / (2.0 * (k_linear + 1.0)))

        # Complex Gaussian
        x = rng.normal(s, sigma)
        y = rng.normal(0.0, sigma)
        power_linear = x ** 2 + y ** 2
        power_db = 10.0 * np.log10(np.maximum(power_linear, 1e-6))
        return float(power_db)

    def total_path_loss(
        self,
        distance_m: float,
        elevation_deg: float,
        frequency_hz: float,
        rain_rate_mm_h: float = 0.0,
        enable_fading: bool = True,
        rng=None,
    ) -> dict[str, float]:
        """
        Computes decomposed and aggregate path loss in dB.
        """
        fspl = float(self.free_space_path_loss(distance_m, frequency_hz))
        atm = float(self.atmospheric_gas_attenuation(elevation_deg, frequency_hz))
        rain = float(self.rain_attenuation(elevation_deg, frequency_hz, rain_rate_mm_h))

        if enable_fading:
            sf = float(self.shadow_fading(elevation_deg, rng=rng))
            ff = float(self.fast_fading_rician(rng=rng))
        else:
            sf = 0.0
            ff = 0.0

        total_loss = fspl + atm + rain + sf - ff  # fast fading power gain adds to received power

        return {
            "fspl_db": fspl,
            "atm_loss_db": atm,
            "rain_loss_db": rain,
            "shadow_fading_db": sf,
            "fast_fading_gain_db": ff,
            "total_path_loss_db": total_loss,
        }
