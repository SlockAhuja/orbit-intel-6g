"""
ORBIT-INTEL 6G: Experimental Scenarios Definition
Defines 5 rigorous operational scenarios for benchmarking M1-M4.
"""

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np
from src.simulation_engine.network_simulator import NetworkSimulator
from src.simulation_engine.orbital import LEOSatelliteOrbit


@dataclass
class ScenarioConfig:
    name: str
    scenario_id: int
    description: str
    duration_s: int
    apply_step_fn: Callable[[NetworkSimulator, int], None]


def apply_scenario_1(sim: NetworkSimulator, current_t: int):
    """Scenario 1: Normal communication conditions (clear sky, nominal traffic)."""
    sim.rain_rate_mm_h = 0.0
    sim.shadowing_flutter_std = 0.0


def apply_scenario_2(sim: NetworkSimulator, current_t: int):
    """Scenario 2: High traffic and network congestion (surges at t=20s)."""
    sim.rain_rate_mm_h = 0.0
    sim.shadowing_flutter_std = 0.0
    if current_t >= 20:
        # Increase user demand to congest terrestrial nodes
        for u in sim.users.values():
            u.required_data_rate_mbps = 25.0 if u.service_type == "URLLC" else 60.0
    else:
        for u in sim.users.values():
            u.required_data_rate_mbps = 5.0 if u.service_type == "URLLC" else 20.0


def apply_scenario_3(sim: NetworkSimulator, current_t: int):
    """Scenario 3: Sudden link degradation (ITU-R convective storm rain cell at t=25s to t=55s)."""
    if 25 <= current_t <= 55:
        sim.rain_rate_mm_h = 55.0  # Heavy cloudburst attenuation
    else:
        sim.rain_rate_mm_h = 0.0
    sim.shadowing_flutter_std = 1.0


def apply_scenario_4(sim: NetworkSimulator, current_t: int):
    """
    Scenario 4: Satellite visibility reduction & orbital departure.
    SAT-01 approaches topocentric horizon, dropping from ~11.6° to <10° at t ≈ 35s.
    SAT-02 rises from ~9.4° to >10° at t ≈ 15-20s, providing handover target.
    """
    sim.rain_rate_mm_h = 5.0
    sim.shadowing_flutter_std = 0.5

    # At the start of Scenario 4 (t=0), configure orbital ephemeris for true departure & handover
    if current_t == 0:
        if "SAT-01" in sim.nodes:
            sat1 = sim.nodes["SAT-01"]
            # Advance mean anomaly so remaining visibility over ground hub is ~35s
            n_mean = sat1.orbit.n_mean
            sat1.orbit = LEOSatelliteOrbit(
                sat_id="SAT-01",
                altitude_km=float(sim.cfg["leo_satellite"]["altitude_km"]),
                inclination_deg=53.0,
                raan_deg=75.0,
                initial_mean_anomaly_deg=18.0 + 115.0 * n_mean * 180.0 / np.pi,
            )
            pos, vel, lat, lon = sat1.orbit.get_state_at_time(0.0)
            sat1.pos_ecef = pos
            sat1.vel_ecef = vel
            sat1.lat_deg = lat
            sat1.lon_deg = lon

        if "SAT-02" in sim.nodes:
            sat2 = sim.nodes["SAT-02"]
            # Position rising secondary satellite so it becomes visible at t ≈ 15s
            sat2.orbit = LEOSatelliteOrbit(
                sat_id="SAT-02",
                altitude_km=float(sim.cfg["leo_satellite"]["altitude_km"]),
                inclination_deg=53.0,
                raan_deg=75.0,
                initial_mean_anomaly_deg=8.0,
            )
            pos2, vel2, lat2, lon2 = sat2.orbit.get_state_at_time(0.0)
            sat2.pos_ecef = pos2
            sat2.vel_ecef = vel2
            sat2.lat_deg = lat2
            sat2.lon_deg = lon2


def apply_scenario_5(sim: NetworkSimulator, current_t: int):
    """Scenario 5: High uncertainty & rapid channel flutter (severe multipath + variable rain)."""
    sim.rain_rate_mm_h = 25.0
    sim.shadowing_flutter_std = 4.0  # High stochastic variance, testing uncertainty awareness


ALL_SCENARIOS = [
    ScenarioConfig(
        scenario_id=1,
        name="Normal_Conditions",
        description="Nominal traffic load and clear atmospheric propagation.",
        duration_s=60,
        apply_step_fn=apply_scenario_1,
    ),
    ScenarioConfig(
        scenario_id=2,
        name="High_Congestion_Surge",
        description="High traffic surge pushing terrestrial base stations to capacity limits.",
        duration_s=60,
        apply_step_fn=apply_scenario_2,
    ),
    ScenarioConfig(
        scenario_id=3,
        name="Sudden_Rain_Degradation",
        description="Localized convective rain cell introducing 12-18 dB sudden attenuation.",
        duration_s=60,
        apply_step_fn=apply_scenario_3,
    ),
    ScenarioConfig(
        scenario_id=4,
        name="Satellite_Visibility_Handover",
        description="Primary serving LEO satellite drops below 10° elevation threshold.",
        duration_s=60,
        apply_step_fn=apply_scenario_4,
    ),
    ScenarioConfig(
        scenario_id=5,
        name="High_Uncertainty_Flutter",
        description="Fast fading and volatile channel flutter creating high prediction uncertainty.",
        duration_s=60,
        apply_step_fn=apply_scenario_5,
    ),
]

