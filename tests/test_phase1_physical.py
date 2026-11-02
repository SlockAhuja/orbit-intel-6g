"""
ORBIT-INTEL 6G: Phase 1 Physical Network Simulator Test Suite
Scientifically validates:
1. WGS-84 Geodetic <-> ECEF coordinate transformations.
2. Keplerian orbital kinematics and altitude/velocity conservation.
3. Topocentric elevation, azimuth, and slant distance.
4. Disaggregated propagation models (LEO: ITU-R P.618/P.676 vs TBS: 3GPP 38.901/ITU-R P.530).
5. Doppler shift calculations and velocity projection.
6. Speed-of-light bounded propagation latency (T_prop = d / c) and decomposition.
7. Heterogeneous network topology attachment across 4 cohorts.
8. Scenario 4 physical satellite orbital departure and handover continuity.
"""

import pytest
import numpy as np
from src.simulation_engine.orbital import OrbitalMechanics, LEOSatelliteOrbit
from src.channel_models.propagation import PropagationModel
from src.channel_models.doppler import DopplerModel
from src.simulation_engine.traffic import TrafficEngine
from src.simulation_engine.network_simulator import NetworkSimulator
from src.experiments.scenarios import apply_scenario_4


class TestOrbitalAndCoordinateGeometry:
    """Validates WGS-84 transformations and Keplerian orbital dynamics."""

    def test_wgs84_roundtrip_transformation(self):
        """Tests that Geodetic -> ECEF -> Geodetic roundtrip error is < 1 mm."""
        test_points = [
            (0.0, 0.0, 0.0),          # Equator / Prime Meridian
            (22.0, 75.0, 500.0),      # Central India Hub
            (45.0, -93.0, 250.0),     # Mid-latitude
            (89.0, 10.0, 1000.0),     # Near North Pole
            (-33.86, 151.2, 50.0),    # Southern Hemisphere
        ]
        for lat, lon, alt in test_points:
            ecef = OrbitalMechanics.geodetic_to_ecef(lat, lon, alt)
            lat_r, lon_r, alt_r = OrbitalMechanics.ecef_to_geodetic(ecef)
            assert abs(lat - lat_r) < 1e-6, f"Latitude roundtrip failed for ({lat}, {lon})"
            assert abs(lon - lon_r) < 1e-6, f"Longitude roundtrip failed for ({lat}, {lon})"
            assert abs(alt - alt_r) < 1e-3, f"Altitude roundtrip failed for ({lat}, {lon})"

    def test_leo_orbital_kinematics(self):
        """Tests circular Keplerian orbital period, velocity, and altitude preservation."""
        alt_km = 600.0
        orbit = LEOSatelliteOrbit("SAT-TEST", altitude_km=alt_km, inclination_deg=53.0)

        # Expected orbital period: T = 2 * pi * sqrt(r^3 / mu)
        r = OrbitalMechanics.A + alt_km * 1000.0
        expected_period_s = 2.0 * np.pi * np.sqrt((r ** 3) / OrbitalMechanics.MU)
        expected_speed_m_s = np.sqrt(OrbitalMechanics.MU / r)

        assert abs(orbit.period_s - expected_period_s) < 0.1
        assert abs(orbit.orbital_speed_m_s - expected_speed_m_s) < 0.1
        assert 5700.0 < orbit.period_s < 5900.0  # ~96.7 minutes
        assert 7500.0 < orbit.orbital_speed_m_s < 7650.0  # ~7.56 km/s

        # Test state propagation over 1 orbit: orbital radius must remain strictly conserved
        for t_s in [0.0, 60.0, 600.0, 1800.0, 3600.0, orbit.period_s]:
            pos, vel, lat, lon = orbit.get_state_at_time(t_s)
            radius_m = float(np.linalg.norm(pos))
            assert abs(radius_m - r) < 1e-3, f"Orbital radius deviated at t={t_s}"
            # Geodetic altitude on WGS-84 oblate ellipsoid varies slightly by latitude
            _, _, computed_alt = OrbitalMechanics.ecef_to_geodetic(pos)
            assert abs(computed_alt - alt_km * 1000.0) < 22000.0, f"Ellipsoidal altitude out of bounds at t={t_s}"

    def test_zenith_topocentric_elevation(self):
        """Tests that a point directly overhead has elevation 90 degrees."""
        user_lat, user_lon, user_alt = 22.0, 75.0, 0.0
        user_ecef = OrbitalMechanics.geodetic_to_ecef(user_lat, user_lon, user_alt)

        # Satellite directly at zenith 600 km overhead
        sat_ecef = OrbitalMechanics.geodetic_to_ecef(user_lat, user_lon, 600000.0)
        elev, az, slant = OrbitalMechanics.compute_elevation_azimuth(user_ecef, sat_ecef, user_lat, user_lon)

        assert abs(elev - 90.0) < 1e-4, f"Expected 90 deg elevation, got {elev}"
        assert abs(slant - 600000.0) < 10.0, f"Expected 600 km slant, got {slant}"


class TestDisaggregatedPropagationModels:
    """Validates physical propagation formulas across tiers."""

    def test_free_space_path_loss(self):
        """Tests Friis FSPL: FSPL(dB) = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)."""
        prop = PropagationModel()
        d_m = 1000.0
        fc_hz = 2.0e9
        c = prop.c
        expected_fspl = 20.0 * np.log10(d_m) + 20.0 * np.log10(fc_hz) + 20.0 * np.log10(4.0 * np.pi / c)
        actual_fspl = prop.free_space_path_loss(d_m, fc_hz)
        assert abs(actual_fspl - expected_fspl) < 1e-6

    def test_leo_itur_p618_rain_attenuation(self):
        """Tests ITU-R P.618 Earth-space rain attenuation on LEO links."""
        prop = PropagationModel()
        fc = 2.0e9
        dist_m = 800000.0

        # Zero rain: no rain attenuation
        res_norain = prop.total_path_loss(dist_m, elevation_deg=30.0, frequency_hz=fc, tier="LEO", rain_rate_mm_h=0.0)
        assert res_norain["rain_loss_db"] == 0.0

        # Heavy rain (50 mm/h): rain attenuation increases as elevation decreases (longer slant path)
        res_high_elev = prop.total_path_loss(dist_m, elevation_deg=60.0, frequency_hz=fc, tier="LEO", rain_rate_mm_h=50.0)
        res_low_elev = prop.total_path_loss(dist_m, elevation_deg=15.0, frequency_hz=fc, tier="LEO", rain_rate_mm_h=50.0)

        assert res_high_elev["rain_loss_db"] > 0.0
        assert res_low_elev["rain_loss_db"] > res_high_elev["rain_loss_db"], "Lower elevation must have higher slant path rain loss"

    def test_tbs_does_not_apply_itur_p618(self):
        """Verifies that terrestrial base stations use 3GPP UMa / ITU-R P.530 and NOT ITU-R P.618."""
        prop = PropagationModel()
        fc = 2.0e9
        d_m = 1500.0

        res_tbs_rain = prop.total_path_loss(d_m, elevation_deg=1.0, frequency_hz=fc, tier="TBS", rain_rate_mm_h=50.0)
        # For 1.5 km terrestrial path, rain attenuation is gamma_R * d_eff (P.530), order of 0.01 - 0.2 dB at 2 GHz
        assert res_tbs_rain["model_used"].startswith("3GPP TR 38.901 UMa")
        assert res_tbs_rain["rain_loss_db"] < 1.0, "Terrestrial 1.5 km S-band rain loss cannot be large satellite slant loss"


class TestDopplerCalculations:
    """Validates Doppler frequency shift computation and rate."""

    def test_doppler_radial_velocity(self):
        """Tests Doppler formula: Delta_f = -f_c * (v_rel . r_hat) / c."""
        calc = DopplerModel()
        fc = 2.0e9
        c = calc.c

        # Satellite moving directly towards user at 7000 m/s
        user_pos = np.array([0.0, 0.0, 0.0])
        user_vel = np.array([0.0, 0.0, 0.0])
        sat_pos = np.array([1000000.0, 0.0, 0.0])
        sat_vel = np.array([-7000.0, 0.0, 0.0])  # approaching

        res = calc.compute_doppler_shift(sat_pos, sat_vel, user_pos, user_vel, fc)
        expected_shift = -fc * (-7000.0) / c  # +46.67 kHz
        assert abs(res["doppler_shift_hz"] - expected_shift) < 1.0
        assert res["doppler_shift_hz"] > 0.0  # Approaching => positive Doppler shift


class TestLatencyAndSpeedOfLightBounds:
    """Validates strict speed-of-light propagation latency bounds."""

    def test_propagation_latency_strictly_speed_of_light(self):
        """Tests T_prop = d / c for all distances."""
        c = 3.0e8
        engine = TrafficEngine(speed_of_light=c)
        distances = [100.0, 1500.0, 20000.0, 600000.0, 1500000.0]

        for d in distances:
            decomp = engine.compute_transmission_delay_ms(
                slant_distance_m=d,
                packet_size_bytes=1500,
                allocated_rate_mbps=100.0,
                node_load=0.2,
                tier="LEO" if d > 100000.0 else "TBS",
            )
            expected_prop_ms = (d / c) * 1000.0
            assert abs(decomp["t_prop_ms"] - expected_prop_ms) < 1e-6
            assert decomp["t_rtt_ms"] >= 2.0 * decomp["t_prop_ms"]

    def test_leo_latency_decomposition(self):
        """Verifies LEO one-way propagation latency is 2.5 - 9.0 ms, total E2E 8-25 ms, RTT > 14 ms."""
        engine = TrafficEngine(speed_of_light=3.0e8)
        decomp = engine.compute_transmission_delay_ms(
            slant_distance_m=800000.0,  # 800 km
            packet_size_bytes=1500,
            allocated_rate_mbps=50.0,
            node_load=0.3,
            tier="LEO",
        )
        assert 2.5 <= decomp["t_prop_ms"] <= 9.0
        assert decomp["t_feeder_ms"] > 0.0
        assert decomp["t_proc_ms"] >= 2.0
        assert 8.0 <= decomp["t_e2e_total_ms"] <= 25.0
        assert decomp["t_rtt_ms"] >= 14.0


class TestHeterogeneousNetworkTopology:
    """Validates 4-cohort user distribution and genuine LEO satellite attachment."""

    def test_user_cohort_attachment(self):
        """Simulates default topology and verifies multi-tier traffic distribution."""
        sim = NetworkSimulator(random_seed=42)
        snapshot = sim.step()

        # Group users by cohort
        urban_users = ["UE-01", "UE-02", "UE-03"]
        suburban_users = ["UE-04", "UE-05", "UE-06"]
        remote_users = ["UE-07", "UE-08", "UE-09"]
        maritime_users = ["UE-10", "UE-11", "UE-12"]

        # Urban users must see at least one TBS as visible with high SINR (> 35 dB)
        for u in urban_users:
            tbs1 = snapshot["links"][(u, "TBS-01")]
            tbs2 = snapshot["links"][(u, "TBS-02")]
            assert tbs1["is_visible"] or tbs2["is_visible"], f"Urban user {u} must see a TBS"
            assert max(tbs1["sinr_db"], tbs2["sinr_db"]) > 35.0, f"Urban user {u} must have high SINR from nearest TBS"

        # Remote users (outside TBS/UAV coverage) must have SAT-01 visible
        for u in remote_users:
            assert not snapshot["links"][(u, "TBS-01")]["is_visible"]
            assert not snapshot["links"][(u, "TBS-02")]["is_visible"]
            assert not snapshot["links"][(u, "UAV-01")]["is_visible"]
            sat_link = snapshot["links"][(u, "SAT-01")]
            assert sat_link["is_visible"], f"Remote user {u} must see SAT-01"
            assert sat_link["sinr_db"] > 0.0

        # Maritime users (far offshore, > 80 km) must have ONLY SAT-01 visible
        for u in maritime_users:
            for terrestrial_node in ["TBS-01", "TBS-02", "UAV-01", "HAPS-01"]:
                assert not snapshot["links"][(u, terrestrial_node)]["is_visible"], f"{u} should not reach {terrestrial_node}"
            sat_link = snapshot["links"][(u, "SAT-01")]
            assert sat_link["is_visible"], f"Maritime user {u} must see SAT-01"
            assert sat_link["sinr_db"] > 0.0


class TestScenario4OrbitalDeparture:
    """Validates Scenario 4 physical departure, horizon drop, and handover continuity."""

    def test_scenario_4_physical_handover(self):
        """Verifies SAT-01 descent, handover trigger at t=25s, drop at t=35s, and SAT-02 rise."""
        sim = NetworkSimulator(random_seed=42)

        sat1_elevations = []
        sat1_rem_vis = []
        sat1_visibilities = []
        sat2_visibilities = []

        for t in range(60):
            apply_scenario_4(sim, t)
            snapshot = sim.step()

            l1 = snapshot["links"][("UE-01", "SAT-01")]
            l2 = snapshot["links"][("UE-10", "SAT-02")]

            sat1_elevations.append(l1["elevation_deg"])
            sat1_rem_vis.append(l1["remaining_visibility_s"])
            sat1_visibilities.append(l1["is_visible"])
            sat2_visibilities.append(l2["is_visible"])

        # 1. At t=0, SAT-01 must be visible with elev between 11° and 15°
        assert 11.0 <= sat1_elevations[0] <= 15.0
        assert sat1_visibilities[0] is True
        assert 30.0 <= sat1_rem_vis[0] <= 45.0

        # 2. At t=25, remaining visibility must drop below 12s trigger threshold
        assert sat1_rem_vis[25] < 12.0

        # 3. At t=35, SAT-01 must drop below 10° elevation and is_visible must be False
        assert sat1_elevations[35] < 10.0
        assert sat1_visibilities[35] is False
        assert sat1_rem_vis[35] == 0.0

        # 4. SAT-02 must be visible by t=35s to absorb handover traffic
        assert sat2_visibilities[35] is True, "SAT-02 must be visible when SAT-01 drops"
        assert sat2_visibilities[35] is True, "SAT-02 must be visible when SAT-01 drops"
