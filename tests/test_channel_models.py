"""
Unit tests for 3GPP and ITU-R Channel Models.
"""

import pytest
import numpy as np
from src.channel_models.propagation import PropagationModel
from src.channel_models.doppler import DopplerModel
from src.channel_models.sinr_calculator import SINRCalculator


def test_free_space_path_loss_scaling():
    """FSPL must scale by 20 dB per decade of distance (Friis formula)."""
    prop = PropagationModel()
    fc = 2.0e9  # 2 GHz S-band
    pl_1km = prop.free_space_path_loss(1000.0, fc)
    pl_10km = prop.free_space_path_loss(10000.0, fc)

    # Delta should be exactly 20.0 dB
    assert abs((pl_10km - pl_1km) - 20.0) < 1e-4


def test_itu_rain_attenuation_monotonicity():
    """Rain attenuation must be zero for clear sky and increase monotonically with rain rate."""
    prop = PropagationModel()
    elev = 30.0
    fc = 28.0e9  # 28 GHz Ka-band

    a_clear = prop.rain_attenuation(elev, fc, rain_rate_mm_h=0.0)
    a_moderate = prop.rain_attenuation(elev, fc, rain_rate_mm_h=25.0)
    a_heavy = prop.rain_attenuation(elev, fc, rain_rate_mm_h=60.0)

    assert a_clear == 0.0
    assert a_moderate > 0.0
    assert a_heavy > a_moderate


def test_doppler_shift_physics():
    """Verifies Doppler shift equation fd = fc * (v / c)."""
    doppler = DopplerModel()
    fc = 2.0e9  # 2 GHz
    c = 3.0e8

    node_pos = np.array([10000.0, 0.0, 0.0], dtype=np.float64)
    user_pos = np.array([0.0, 0.0, 0.0], dtype=np.float64)

    # Approaching at 300 m/s
    node_vel = np.array([-300.0, 0.0, 0.0], dtype=np.float64)
    user_vel = np.array([0.0, 0.0, 0.0], dtype=np.float64)

    res = doppler.compute_doppler_shift(node_pos, node_vel, user_pos, user_vel, fc)
    expected_fd = -fc * (300.0 / c)  # negative sign indicates approaching/receding depending on convention
    assert abs(abs(res["doppler_shift_hz"]) - abs(expected_fd)) < 1e-3


def test_thermal_noise_and_sinr():
    """Verifies thermal noise floor at 290K for 100 MHz bandwidth is ~ -87 dBm with NF=7 dB."""
    sinr_calc = SINRCalculator(noise_figure_db=7.0)
    bw_hz = 100.0e6
    p_noise_dbm = sinr_calc.compute_noise_power_dbm(bw_hz)

    # -174 + 10*log10(1e8) + 7 = -174 + 80 + 7 = -87 dBm
    assert abs(p_noise_dbm - (-87.0)) < 0.5

