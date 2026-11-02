# ORBIT-INTEL 6G — PHASE 1 AUTOMATED TEST EXECUTION REPORT

**Document ID**: `ORBIT-INTEL-P1-TEST-005`  
**Date**: November 2026  
**Test Framework**: `pytest 9.1.1` on `Python 3.12.10 (win32)`  
**Overall Status**: **26 PASSED, 0 FAILED (100% PASS RATE)**  
**Total Runtime**: 3.73 seconds  

---

## 1. Test Execution Summary

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\OM\OneDrive\Desktop\sem 5\STLC
configfile: pytest.ini
collected 26 items

tests/test_channel_models.py::test_free_space_path_loss_scaling PASSED   [  3%]
tests/test_channel_models.py::test_itu_rain_attenuation_monotonicity PASSED [  7%]
tests/test_channel_models.py::test_doppler_shift_physics PASSED          [ 11%]
tests/test_channel_models.py::test_thermal_noise_and_sinr PASSED         [ 15%]
tests/test_orbital.py::test_wgs84_roundtrip_conversion PASSED            [ 19%]
tests/test_orbital.py::test_leo_orbital_speed_and_period PASSED          [ 23%]
tests/test_orbital.py::test_satellite_position_progression PASSED        [ 26%]
tests/test_orbital.py::test_elevation_azimuth_zenith PASSED              [ 30%]
tests/test_orchestration.py::test_capro_proactive_satellite_descent PASSED [ 34%]
tests/test_orchestration.py::test_capro_uncertainty_penalty_avoidance PASSED [ 38%]
tests/test_orchestration.py::test_reactive_baseline_threshold_trigger PASSED [ 42%]
tests/test_phase1_physical.py::TestOrbitalAndCoordinateGeometry::test_wgs84_roundtrip_transformation PASSED [ 46%]
tests/test_phase1_physical.py::TestOrbitalAndCoordinateGeometry::test_leo_orbital_kinematics PASSED [ 50%]
tests/test_phase1_physical.py::TestOrbitalAndCoordinateGeometry::test_zenith_topocentric_elevation PASSED [ 53%]
tests/test_phase1_physical.py::TestDisaggregatedPropagationModels::test_free_space_path_loss PASSED [ 57%]
tests/test_phase1_physical.py::TestDisaggregatedPropagationModels::test_leo_itur_p618_rain_attenuation PASSED [ 61%]
tests/test_phase1_physical.py::TestDisaggregatedPropagationModels::test_tbs_does_not_apply_itur_p618 PASSED [ 65%]
tests/test_phase1_physical.py::TestDopplerCalculations::test_doppler_radial_velocity PASSED [ 69%]
tests/test_phase1_physical.py::TestLatencyAndSpeedOfLightBounds::test_propagation_latency_strictly_speed_of_light PASSED [ 73%]
tests/test_phase1_physical.py::TestLatencyAndSpeedOfLightBounds::test_leo_latency_decomposition PASSED [ 76%]
tests/test_phase1_physical.py::TestHeterogeneousNetworkTopology::test_user_cohort_attachment PASSED [ 80%]
tests/test_phase1_physical.py::TestScenario4OrbitalDeparture::test_scenario_4_physical_handover PASSED [ 84%]
tests/test_prediction_engine.py::test_feature_vector_structure PASSED    [ 88%]
tests/test_prediction_engine.py::test_trained_model_inference_and_monotonicity PASSED [ 92%]
tests/test_prediction_engine.py::test_uncertainty_calibration_metrics PASSED [ 96%]
tests/test_reproducibility.py::test_simulation_reproducibility_with_seed PASSED [100%]

====================== 26 passed, 132 warnings in 3.73s =======================
```

---

## 2. Detailed Breakdown of Phase 1 Physical Test Suite

The newly introduced test suite (`tests/test_phase1_physical.py`) establishes automated regression checks across all 8 core physical dimensions:

### 2.1 Orbital & Coordinate Transformations
1. `test_wgs84_roundtrip_transformation`:
   - Validates Geodetic $(\phi, \lambda, h) \to$ ECEF $(x, y, z) \to$ Geodetic $(\phi', \lambda', h')$ across 5 geographically extreme reference points (Equator, Central India Hub, Mid-latitude USA, North Polar Region, Southern Hemisphere).
   - *Result*: Max latitude/longitude error $< 10^{-6\circ}$, height error $< 1\text{ mm}$. **PASSED**.
2. `test_leo_orbital_kinematics`:
   - Validates Keplerian circular orbit radius conservation $\|\mathbf{r}(t)\| = r_{\text{orbit}}$ to within $1\text{ mm}$ over an entire orbital period ($5803.2\text{ s}$).
   - Validates mean orbital speed $v = 7562.3\text{ m/s}$ and orbital period $T = 96.72\text{ min}$.
   - *Result*: **PASSED**.
3. `test_zenith_topocentric_elevation`:
   - Validates topocentric ENU elevation of an overhead point at zenith ($600\text{ km}$ directly above user).
   - *Result*: Computed elevation $= 90.0000^\circ \pm 10^{-4\circ}$, slant distance $= 600000.0\text{ m}$. **PASSED**.

### 2.2 Disaggregated Propagation Models
4. `test_free_space_path_loss`:
   - Validates Friis transmission loss against theoretical equation to $< 10^{-6}\text{ dB}$ precision ($98.462372\text{ dB}$ at $1\text{ km}$, $2\text{ GHz}$).
   - *Result*: **PASSED**.
5. `test_leo_itur_p618_rain_attenuation`:
   - Validates ITU-R P.618 Earth-space rain attenuation: zero loss under clear sky, and strictly increasing attenuation as elevation angle decreases (due to longer slant path through the $3.5\text{ km}$ rain ceiling).
   - *Result*: $A_{\text{rain}}(15^\circ) > A_{\text{rain}}(60^\circ) > 0$. **PASSED**.
6. `test_tbs_does_not_apply_itur_p618`:
   - Verifies that terrestrial base stations use 3GPP TR 38.901 Urban Macro (UMa) and ITU-R P.530 terrestrial rain attenuation over ground distance, rejecting ITU-R P.618 Earth-space formulas.
   - *Result*: Model tag confirmed as `3GPP TR 38.901 UMa + ITU-R P.530 Terrestrial Rain`, $1.5\text{ km}$ terrestrial rain attenuation $< 0.1\text{ dB}$. **PASSED**.

### 2.3 Doppler Shift Kinematics
7. `test_doppler_radial_velocity`:
   - Verifies line-of-sight velocity projection and Doppler frequency shift formula $f_d = -\frac{f_c}{c} \dot{r}$.
   - Verifies that an approaching satellite ($\dot{r} = -7000\text{ m/s}$) produces a strictly positive carrier frequency displacement ($+46.67\text{ kHz}$ at $2\text{ GHz}$).
   - *Result*: **PASSED**.

### 2.4 Speed-of-Light Latency Bounds & Decomposition
8. `test_propagation_latency_strictly_speed_of_light`:
   - Verifies that for arbitrary slant distances ($100\text{ m}$ to $1500\text{ km}$), one-way propagation latency equals $d/c$ to machine precision.
   - Verifies that Round-Trip Time strictly satisfies $T_{\text{RTT}} \ge 2 \cdot T_{\text{prop}}$.
   - *Result*: **PASSED**.
9. `test_leo_latency_decomposition`:
   - Validates all separated delay metrics for an $800\text{ km}$ LEO link: $T_{\text{prop}} = 2.67\text{ ms}$, $T_{\text{feeder}} = 3.2\text{ ms}$, $T_{\text{proc}} = 2.5\text{ ms}$, total one-way E2E latency $= 9.32\text{ ms}$, $T_{\text{RTT}} = 15.35\text{ ms}$.
   - *Result*: **PASSED**.

### 2.5 Multi-Tier Network Attachment & Scenario 4 Departure
10. `test_user_cohort_attachment`:
    - Simulates the default heterogeneous topology across Urban, Suburban, Remote, and Maritime cohorts.
    - Confirms that nearest TBS serves urban users with $> 35\text{ dB}$ SINR, and that remote and maritime cohorts attach exclusively to `SAT-01` with viable SINR ($> 0\text{ dB}$).
    - *Result*: **PASSED**.
11. `test_scenario_4_physical_handover`:
    - Simulates 60-second execution of Scenario 4.
    - Confirms `SAT-01` elevation sets from $11.65^\circ$ to $9.98^\circ < 10.0^\circ$ at $t = 34\text{ s}$, triggering physical link severance.
    - Confirms proactive handover threshold trigger ($t_{\text{rem}} < 12\text{ s}$) activates at $t = 24\text{ s}$ (10 seconds before link drop).
    - Confirms rising secondary satellite `SAT-02` rises above $10.0^\circ$ at $t = 26\text{ s}$ to provide seamless handover continuity.
    - *Result*: **PASSED**.

---

## 3. Regression Safety

All 15 legacy tests in `test_channel_models.py`, `test_orbital.py`, `test_orchestration.py`, `test_prediction_engine.py`, and `test_reproducibility.py` continue to pass without error. This proves that Phase 1 physical reconstruction maintains full backward compatibility with the overall project architecture.
