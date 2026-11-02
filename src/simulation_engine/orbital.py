"""
ORBIT-INTEL 6G: Orbital Mechanics and Kinematic Geometry
Provides WGS84 Geodetic <-> ECEF conversions, LEO Keplerian propagation, and topocentric elevation/visibility calculation.
"""

import numpy as np


class OrbitalMechanics:
    """
    Simulates Keplerian orbital kinematics, WGS-84 coordinate transformations,
    and ground-satellite visibility geometry.
    """

    # WGS-84 ellipsoid constants
    A = 6378137.0          # Earth semi-major axis (meters)
    F = 1.0 / 298.257223563  # Flattening
    B = A * (1.0 - F)      # Semi-minor axis (meters)
    E2 = 2.0 * F - F ** 2  # First eccentricity squared
    MU = 3.986004418e14    # Earth standard gravitational parameter (m^3/s^2)
    OMEGA_EARTH = 7.2921159e-5  # Earth rotation rate (rad/s)

    @classmethod
    def geodetic_to_ecef(cls, lat_deg: float, lon_deg: float, alt_m: float) -> np.ndarray:
        """
        Converts Geodetic coordinates (lat, lon, altitude in meters) to ECEF (x, y, z).
        """
        phi = np.radians(lat_deg)
        lam = np.radians(lon_deg)
        sin_phi = np.sin(phi)
        cos_phi = np.cos(phi)

        n_phi = cls.A / np.sqrt(1.0 - cls.E2 * (sin_phi ** 2))

        x = (n_phi + alt_m) * cos_phi * np.cos(lam)
        y = (n_phi + alt_m) * cos_phi * np.sin(lam)
        z = (n_phi * (1.0 - cls.E2) + alt_m) * sin_phi

        return np.array([x, y, z], dtype=np.float64)

    @classmethod
    def ecef_to_geodetic(cls, pos_ecef: np.ndarray) -> tuple[float, float, float]:
        """
        Converts ECEF Cartesian coordinates (x, y, z in meters) to Geodetic (lat, lon, alt).
        """
        x, y, z = pos_ecef[0], pos_ecef[1], pos_ecef[2]
        p = np.sqrt(x ** 2 + y ** 2)
        if p < 1e-6:
            lat = 90.0 if z > 0 else -90.0
            return lat, 0.0, float(abs(z) - cls.B)

        lam = np.arctan2(y, x)
        theta = np.arctan2(z * cls.A, p * cls.B)

        phi = np.arctan2(
            z + ((cls.A ** 2 - cls.B ** 2) / cls.B) * (np.sin(theta) ** 3),
            p - cls.E2 * cls.A * (np.cos(theta) ** 3)
        )

        n_phi = cls.A / np.sqrt(1.0 - cls.E2 * (np.sin(phi) ** 2))
        h = p / np.cos(phi) - n_phi

        return float(np.degrees(phi)), float(np.degrees(lam)), float(h)

    @classmethod
    def compute_elevation_azimuth(
        cls, user_ecef: np.ndarray, target_ecef: np.ndarray, user_lat_deg: float, user_lon_deg: float
    ) -> tuple[float, float, float]:
        """
        Transforms relative ECEF vector to local Topocentric East-North-Up (ENU) frame
        and computes Elevation angle (deg), Azimuth angle (deg), and slant distance (m).
        """
        diff = target_ecef - user_ecef
        slant_dist = float(np.linalg.norm(diff))
        if slant_dist < 1e-3:
            return 90.0, 0.0, 0.0

        phi = np.radians(user_lat_deg)
        lam = np.radians(user_lon_deg)

        sin_phi, cos_phi = np.sin(phi), np.cos(phi)
        sin_lam, cos_lam = np.sin(lam), np.cos(lam)

        # ENU rotation matrix from ECEF
        r_ecef_to_enu = np.array([
            [-sin_lam, cos_lam, 0.0],
            [-sin_phi * cos_lam, -sin_phi * sin_lam, cos_phi],
            [cos_phi * cos_lam, cos_phi * sin_lam, sin_phi]
        ])

        enu = r_ecef_to_enu @ diff
        east, north, up = enu[0], enu[1], enu[2]

        horiz_dist = np.sqrt(east ** 2 + north ** 2)
        elev_rad = np.arctan2(up, max(horiz_dist, 1e-6))
        elev_deg = float(np.degrees(elev_rad))

        az_rad = np.arctan2(east, north)
        az_deg = float(np.degrees(az_rad) % 360.0)

        return elev_deg, az_deg, slant_dist


class LEOSatelliteOrbit:
    """
    Keplerian circular orbit propagator for LEO satellites with J0 gravitational model
    and Earth rotation coupling.
    """

    def __init__(
        self,
        sat_id: str,
        altitude_km: float = 600.0,
        inclination_deg: float = 53.0,
        raan_deg: float = 0.0,
        initial_mean_anomaly_deg: float = 0.0,
    ):
        self.sat_id = sat_id
        self.h_m = altitude_km * 1000.0
        self.r_orbit = OrbitalMechanics.A + self.h_m
        self.inc_rad = np.radians(inclination_deg)
        self.raan_rad = np.radians(raan_deg)
        self.m0_rad = np.radians(initial_mean_anomaly_deg)

        # Mean orbital motion (rad/s)
        self.n_mean = np.sqrt(OrbitalMechanics.MU / (self.r_orbit ** 3))
        self.orbital_speed_m_s = self.n_mean * self.r_orbit
        self.period_s = 2.0 * np.pi / self.n_mean

    def get_state_at_time(self, t_seconds: float) -> tuple[np.ndarray, np.ndarray, float, float]:
        """
        Calculates ECEF position (m), ECEF velocity (m/s), latitude (deg), and longitude (deg)
        at elapsed simulation time t_seconds.
        """
        # True anomaly for circular orbit equals mean anomaly
        nu = self.m0_rad + self.n_mean * t_seconds

        # Orbital plane coordinates
        x_orb = self.r_orbit * np.cos(nu)
        y_orb = self.r_orbit * np.sin(nu)

        vx_orb = -self.orbital_speed_m_s * np.sin(nu)
        vy_orb = self.orbital_speed_m_s * np.cos(nu)

        # Earth rotation angle since t=0
        theta_g = OrbitalMechanics.OMEGA_EARTH * t_seconds
        raan_eff = self.raan_rad - theta_g

        cos_raan, sin_raan = np.cos(raan_eff), np.sin(raan_eff)
        cos_inc, sin_inc = np.cos(self.inc_rad), np.sin(self.inc_rad)

        # Transform to ECEF
        x_ecef = cos_raan * x_orb - sin_raan * cos_inc * y_orb
        y_ecef = sin_raan * x_orb + cos_raan * cos_inc * y_orb
        z_ecef = sin_inc * y_orb

        pos_ecef = np.array([x_ecef, y_ecef, z_ecef], dtype=np.float64)

        # Velocity in ECEF including frame rotation cross-product
        vx_inertial = cos_raan * vx_orb - sin_raan * cos_inc * vy_orb
        vy_inertial = sin_raan * vx_orb + cos_raan * cos_inc * vy_orb
        vz_inertial = sin_inc * vy_orb

        vx_ecef = vx_inertial + OrbitalMechanics.OMEGA_EARTH * y_ecef
        vy_ecef = vy_inertial - OrbitalMechanics.OMEGA_EARTH * x_ecef
        vz_ecef = vz_inertial

        vel_ecef = np.array([vx_ecef, vy_ecef, vz_ecef], dtype=np.float64)

        lat_deg, lon_deg, _ = OrbitalMechanics.ecef_to_geodetic(pos_ecef)
        return pos_ecef, vel_ecef, lat_deg, lon_deg

    def estimate_remaining_visibility(
        self, user_ecef: np.ndarray, user_lat_deg: float, user_lon_deg: float, current_t_s: float, min_elevation_deg: float = 10.0
    ) -> float:
        """
        Numerical lookahead to compute remaining visibility duration (in seconds)
        until satellite drops below min_elevation_deg.
        """
        step_s = 5.0
        max_lookahead_s = 900.0  # 15 minutes max pass
        elapsed = 0.0

        # Check current elevation
        pos, _, _, _ = self.get_state_at_time(current_t_s)
        cur_elev, _, _ = OrbitalMechanics.compute_elevation_azimuth(user_ecef, pos, user_lat_deg, user_lon_deg)
        if cur_elev < min_elevation_deg:
            return 0.0

        t = current_t_s + step_s
        while (t - current_t_s) < max_lookahead_s:
            pos_t, _, _, _ = self.get_state_at_time(t)
            elev_t, _, _ = OrbitalMechanics.compute_elevation_azimuth(user_ecef, pos_t, user_lat_deg, user_lon_deg)
            if elev_t < min_elevation_deg:
                return float(t - current_t_s)
            t += step_s

        return float(max_lookahead_s)

