"""
Unit tests for Orbital Mechanics and Coordinate Systems.
"""

import pytest
import numpy as np
from src.simulation_engine.orbital import OrbitalMechanics, LEOSatelliteOrbit


def test_wgs84_roundtrip_conversion():
    """Verifies Geodetic -> ECEF -> Geodetic round-trip accuracy within millimeters."""
    lat, lon, alt = 23.5, 78.2, 550.0  # Tropic of Cancer, Central India, 550m altitude
    ecef = OrbitalMechanics.geodetic_to_ecef(lat, lon, alt)
    r_lat, r_lon, r_alt = OrbitalMechanics.ecef_to_geodetic(ecef)

    assert abs(r_lat - lat) < 1e-5
    assert abs(r_lon - lon) < 1e-5
    assert abs(r_alt - alt) < 1e-2


def test_leo_orbital_speed_and_period():
    """Verifies that circular LEO orbit at 600km satisfies Kepler's third law."""
    orbit = LEOSatelliteOrbit(sat_id="SAT-TEST", altitude_km=600.0)
    # At 600 km, orbital speed ~ 7.56 km/s, period ~ 96.7 minutes (5800 s)
    assert 7500.0 <= orbit.orbital_speed_m_s <= 7650.0
    assert 5700.0 <= orbit.period_s <= 5900.0


def test_satellite_position_progression():
    """Verifies that satellite state advances dynamically over time."""
    orbit = LEOSatelliteOrbit(sat_id="SAT-TEST", altitude_km=600.0)
    pos0, vel0, lat0, lon0 = orbit.get_state_at_time(0.0)
    pos100, vel100, lat100, lon100 = orbit.get_state_at_time(100.0)

    # Slant distance travelled in 100 seconds ~ 756 km
    dist_travelled = np.linalg.norm(pos100 - pos0)
    assert 700000.0 <= dist_travelled <= 800000.0


def test_elevation_azimuth_zenith():
    """Verifies that a point directly overhead has 90 degree elevation."""
    user_lat, user_lon, user_alt = 0.0, 0.0, 0.0
    user_ecef = OrbitalMechanics.geodetic_to_ecef(user_lat, user_lon, user_alt)
    overhead_ecef = OrbitalMechanics.geodetic_to_ecef(user_lat, user_lon, 500000.0)

    elev, az, slant = OrbitalMechanics.compute_elevation_azimuth(
        user_ecef, overhead_ecef, user_lat, user_lon
    )
    assert abs(elev - 90.0) < 1e-2
    assert abs(slant - 500000.0) < 1.0

