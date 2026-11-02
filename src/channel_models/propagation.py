"""
ORBIT-INTEL 6G: Disaggregated Physical Propagation Channel Models
Implements tier-specific channel physics:
- LEO: 3GPP TR 38.811 (Rel-17/18 NTN), ITU-R P.618-13 (Earth-space rain), ITU-R P.676 (gas)
- HAPS: Stratospheric air-to-ground propagation (3GPP TR 38.811)
- UAV: Low-altitude air-to-ground propagation (3GPP TR 36.777 / TR 38.901)
- TBS: 3GPP TR 38.901 Urban Macro (UMa) & ITU-R P.530-17 terrestrial rain attenuation
"""

import numpy as np


class PropagationModel:
    """
    Tier-specific physical channel propagation model calculating Free Space Path Loss,
    3GPP TR 38.901 terrestrial loss, ITU-R P.618 Earth-space rain attenuation,
    ITU-R P.530 terrestrial rain attenuation, and elevation-dependent shadowing.
    """

    def __init__(self, speed_of_light: float = 3.0e8):
        self.c = float(speed_of_light)

    def free_space_path_loss(self, distance_m: float | np.ndarray, frequency_hz: float) -> float | np.ndarray:
        """
        Free Space Path Loss (FSPL) in dB:
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
        Atmospheric gas attenuation based on ITU-R P.676-12.
        Applies to Earth-space and stratospheric paths traversing the troposphere.
        A_atm(theta, f) = A0(f) / [sin(theta) + 0.01 / sqrt(sin^2(theta) + 0.002)]
        """
        freq_ghz = float(frequency_hz) / 1.0e9
        if isinstance(elevation_deg, np.ndarray):
            theta_deg = np.maximum(elevation_deg.astype(np.float64), 2.0)
        else:
            theta_deg = max(float(elevation_deg), 2.0)
        theta_rad = np.radians(theta_deg)

        # Zenith attenuation A0(f) for standard atmosphere
        if freq_ghz <= 5.0:
            a0 = 0.035 * (freq_ghz / 2.0)
        elif freq_ghz <= 30.0:
            a0 = 0.08 + 0.02 * freq_ghz + 0.12 * np.exp(-((freq_ghz - 22.2) ** 2) / 8.0)
        else:
            a0 = 0.15 + 0.01 * freq_ghz

        obliquity = 1.0 / (np.sin(theta_rad) + 0.01 / np.sqrt(np.sin(theta_rad) ** 2 + 0.002))
        return float(a0 * obliquity) if not isinstance(elevation_deg, np.ndarray) else (a0 * obliquity)

    def rain_attenuation_earth_space_p618(
        self, elevation_deg: float, frequency_hz: float, rain_rate_mm_h: float
    ) -> float:
        """
        ITU-R P.618-13 rain attenuation model strictly for Earth-to-Space paths (LEO and HAPS).
        The slant path traverses the complete tropospheric rain layer (h_rain ~ 3.5 km).
        """
        r_rate = float(rain_rate_mm_h)
        if r_rate <= 0.01:
            return 0.0

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

        gamma_r = k * (r_rate ** alpha)  # dB/km specific attenuation

        # Rain height ~ 3.5 km above sea level
        h_rain_km = 3.5
        h_station_km = 0.0
        slant_path_km = (h_rain_km - h_station_km) / np.sin(theta_rad)

        # Horizontal reduction factor r0.01 (ITU-R P.618 eq. 30)
        d_horiz = slant_path_km * np.cos(theta_rad)
        r001 = 1.0 / (1.0 + 0.78 * np.sqrt(slant_path_km * gamma_r / freq_ghz) - 0.38 * (1.0 - np.exp(-2.0 * d_horiz)))
        d_eff = slant_path_km * np.clip(r001, 0.2, 1.0)

        a_rain = gamma_r * d_eff
        return float(max(a_rain, 0.0))

    def rain_attenuation(
        self, elevation_deg: float, frequency_hz: float, rain_rate_mm_h: float
    ) -> float:
        """Backward-compatible alias for Earth-space ITU-R P.618 rain attenuation."""
        return self.rain_attenuation_earth_space_p618(elevation_deg, frequency_hz, rain_rate_mm_h)

    def rain_attenuation_terrestrial_p530(
        self, distance_m: float, frequency_hz: float, rain_rate_mm_h: float
    ) -> float:
        """
        ITU-R P.530-17 rain attenuation model for terrestrial line-of-sight paths.
        Path length is the actual ground distance d, NOT an Earth-space slant path.
        """
        r_rate = float(rain_rate_mm_h)
        if r_rate <= 0.01:
            return 0.0

        d_km = min(float(distance_m) / 1000.0, 10.0)
        freq_ghz = float(frequency_hz) / 1.0e9

        # Specific attenuation gamma_R
        if freq_ghz < 10.0:
            k = 0.0001 * (freq_ghz ** 2.2)
            alpha = 1.25
        else:
            k = 0.003 * (freq_ghz ** 1.8)
            alpha = 1.05

        gamma_r = k * (r_rate ** alpha)  # dB/km

        # ITU-R P.530 distance factor r
        d_0 = 35.0 * np.exp(-0.015 * r_rate)
        r_factor = 1.0 / (1.0 + d_km / max(d_0, 1.0))
        d_eff = d_km * r_factor

        return float(max(gamma_r * d_eff, 0.0))

    def terrestrial_urban_macro_loss(
        self, distance_m: float, frequency_hz: float, is_los: bool = True
    ) -> float:
        """
        3GPP TR 38.901 Urban Macro (UMa) path loss model for terrestrial ground base stations.
        f_c in GHz, d in meters (10 m <= d <= 5000 m).
        h_BS = 30 m, h_UT = 1.5 m.
        """
        d_2d = max(float(distance_m), 10.0)
        freq_ghz = float(frequency_hz) / 1.0e9

        # Breakpoint distance d_BP = 4 * h_BS * h_UT * f_c / c
        d_bp = 4.0 * 30.0 * 1.5 * float(frequency_hz) / self.c  # ~ 1200 m for 2 GHz

        if is_los:
            if d_2d <= d_bp:
                pl_db = 28.0 + 22.0 * np.log10(d_2d) + 20.0 * np.log10(freq_ghz)
            else:
                pl_db = 28.0 + 40.0 * np.log10(d_2d / d_bp) + 22.0 * np.log10(d_bp) + 20.0 * np.log10(freq_ghz)
        else:
            pl_los = 28.0 + 22.0 * np.log10(d_2d) + 20.0 * np.log10(freq_ghz)
            pl_nlos = 13.54 + 39.08 * np.log10(d_2d) + 20.0 * np.log10(freq_ghz) - 0.6 * (1.5 - 1.5)
            pl_db = max(pl_los, pl_nlos)

        return float(pl_db)

    def uav_air_to_ground_loss(
        self, distance_m: float, elevation_deg: float, frequency_hz: float
    ) -> float:
        """
        3GPP TR 36.777 / 38.901 Air-to-Ground path loss for UAVs at altitude 300 m.
        LoS probability is a sigmoid function of elevation angle theta.
        """
        theta = max(float(elevation_deg), 0.0)
        d = max(float(distance_m), 10.0)
        fspl = float(self.free_space_path_loss(d, frequency_hz))

        # LoS probability P(LoS) for Urban/Suburban UAV
        # P_LoS = 1 / (1 + a * exp(-b * (theta - a)))
        p_los = 1.0 / (1.0 + 9.61 * np.exp(-0.16 * (theta - 9.61)))

        # Excessive path loss: eta_LoS ~ 1.0 dB, eta_NLoS ~ 20.0 dB
        excess_loss = p_los * 1.0 + (1.0 - p_los) * 18.0
        return float(fspl + excess_loss)

    def shadow_fading(
        self, elevation_deg: float, tier: str = "LEO", rng=None
    ) -> float:
        """
        Tier-dependent shadow fading standard deviation.
        LEO: 4 to 8 dB decreasing with elevation.
        TBS: 4 to 6 dB.
        HAPS: 2 to 4 dB.
        UAV: 3 to 5 dB.
        """
        if rng is None:
            rng = np.random.default_rng()

        theta = np.clip(float(elevation_deg), 0.0, 90.0)

        if tier == "LEO":
            sigma = 4.0 + ((90.0 - theta) / 90.0) * 4.0  # 4 dB at zenith, 8 dB at horizon
        elif tier == "HAPS":
            sigma = 2.0 + ((90.0 - theta) / 90.0) * 2.0  # 2 dB at zenith, 4 dB at horizon
        elif tier == "UAV":
            sigma = 3.0 + ((90.0 - theta) / 90.0) * 2.0
        else:  # TBS
            sigma = 5.0

        return float(rng.normal(0.0, sigma))

    def fast_fading_rician(self, tier: str = "LEO", rng=None) -> float:
        """
        Rician fast fading gain in dB.
        HAPS/LEO LoS has high K-factor (9 to 12 dB).
        TBS has lower K-factor (0 to 3 dB).
        """
        if rng is None:
            rng = np.random.default_rng()

        k_map = {"LEO": 9.0, "HAPS": 12.0, "UAV": 7.0, "TBS": 2.0}
        k_db = k_map.get(tier, 6.0)
        k_lin = 10.0 ** (k_db / 10.0)

        s = np.sqrt(k_lin / (k_lin + 1.0))
        sigma = np.sqrt(1.0 / (2.0 * (k_lin + 1.0)))

        x = rng.normal(s, sigma)
        y = rng.normal(0.0, sigma)
        power_lin = x ** 2 + y ** 2
        return float(10.0 * np.log10(max(power_lin, 1e-6)))

    def total_path_loss(
        self,
        distance_m: float,
        elevation_deg: float,
        frequency_hz: float,
        tier: str = "LEO",
        rain_rate_mm_h: float = 0.0,
        enable_fading: bool = True,
        rng=None,
    ) -> dict[str, float]:
        """
        Computes rigorously disaggregated path loss per access tier.
        """
        f_hz = float(frequency_hz)
        d_m = float(distance_m)
        elev_deg = float(elevation_deg)
        r_rate = float(rain_rate_mm_h)

        if tier == "LEO":
            basic_loss = float(self.free_space_path_loss(d_m, f_hz))
            atm_loss = float(self.atmospheric_gas_attenuation(elev_deg, f_hz))
            rain_loss = float(self.rain_attenuation_earth_space_p618(elev_deg, f_hz, r_rate))
        elif tier == "HAPS":
            basic_loss = float(self.free_space_path_loss(d_m, f_hz))
            atm_loss = float(self.atmospheric_gas_attenuation(elev_deg, f_hz))
            # HAPS at 20 km traverses the 3.5 km tropospheric rain layer
            rain_loss = float(self.rain_attenuation_earth_space_p618(elev_deg, f_hz, r_rate))
        elif tier == "UAV":
            basic_loss = float(self.uav_air_to_ground_loss(d_m, elev_deg, f_hz))
            atm_loss = 0.0  # Negligible in lowest 300 m
            # Below rain ceiling: terrestrial rain model applies
            rain_loss = float(self.rain_attenuation_terrestrial_p530(d_m, f_hz, r_rate))
        elif tier == "TBS":
            # 3GPP TR 38.901 Urban Macro
            basic_loss = float(self.terrestrial_urban_macro_loss(d_m, f_hz, is_los=(d_m < 800.0)))
            atm_loss = 0.0
            # ITU-R P.530 terrestrial rain attenuation over ground distance
            rain_loss = float(self.rain_attenuation_terrestrial_p530(d_m, f_hz, r_rate))
        else:
            basic_loss = float(self.free_space_path_loss(d_m, f_hz))
            atm_loss = 0.0
            rain_loss = 0.0

        if enable_fading:
            sf = self.shadow_fading(elev_deg, tier=tier, rng=rng)
            ff = self.fast_fading_rician(tier=tier, rng=rng)
        else:
            sf = 0.0
            ff = 0.0

        total_loss = basic_loss + atm_loss + rain_loss + sf - ff

        model_name = {
            "LEO": "3GPP TR 38.811 NTN + ITU-R P.618 Earth-space",
            "HAPS": "Stratospheric Air-to-Ground + ITU-R P.618 Rain",
            "UAV": "3GPP TR 36.777 ATG + ITU-R P.530 Terrestrial Rain",
            "TBS": "3GPP TR 38.901 UMa + ITU-R P.530 Terrestrial Rain",
        }.get(tier, "Free Space")

        return {
            "tier": tier,
            "model_used": model_name,
            "basic_loss_db": float(basic_loss),
            "atm_loss_db": float(atm_loss),
            "rain_loss_db": float(rain_loss),
            "shadow_fading_db": float(sf),
            "fast_fading_gain_db": float(ff),
            "total_path_loss_db": float(total_loss),
        }
