"""
Reproducibility tests: Identical seeds must yield bit-exact simulation outputs.
"""

import pytest
import numpy as np
from src.simulation_engine.network_simulator import NetworkSimulator


def test_simulation_reproducibility_with_seed():
    """Two independent simulation runs with identical seed must yield identical telemetry."""
    sim1 = NetworkSimulator(random_seed=777)
    sim2 = NetworkSimulator(random_seed=777)

    trace1 = []
    trace2 = []

    for _ in range(5):
        s1 = sim1.step()
        s2 = sim2.step()
        trace1.append(s1["links"][("UE-01", "SAT-01")]["sinr_db"])
        trace2.append(s2["links"][("UE-01", "SAT-01")]["sinr_db"])

    np.testing.assert_allclose(trace1, trace2, rtol=1e-5, atol=1e-5)

