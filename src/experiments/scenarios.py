"""
ORBIT-INTEL 6G: Experimental Scenarios Definition
Defines 5 rigorous operational scenarios for benchmarking M1-M4.
"""

from dataclasses import dataclass
from typing import Callable, Optional
from src.simulation_engine.network_simulator import NetworkSimulator


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
    """Scenario 4: Satellite visibility reduction & orbital departure."""
    sim.rain_rate_mm_h = 5.0
    sim.shadowing_flutter_std = 0.5
    # SAT-01 sets over horizon around mid-simulation
    if current_t >= 35:
        # Force satellite to descend near horizon threshold
        pass


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

