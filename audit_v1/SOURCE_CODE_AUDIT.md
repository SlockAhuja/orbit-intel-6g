# ORBIT-INTEL 6G: Comprehensive Source-Code Audit

---

## 1. Audit Methodology

Every Python source file, configuration file, test module, and visualization script was audited against the following criteria:
1. **Mathematical & Physical Rigor**: Correct equations, units, coordinate systems, and standard-compliant assumptions.
2. **Implementation Correctness**: Type safety, edge cases, error handling, input validation, and boundary conditions.
3. **Data & Pipeline Integrity**: Absence of data leakage, seed reproducibility, and authentic serialization.
4. **Algorithmic Fairness**: Absence of strawman baselines, identical execution conditions, and proper convergence.
5. **Architectural Coherence**: Active connection of documented modules without dangling or bypass code.

---

## 2. Comprehensive Source-Code Audit Table

| File Path | Line Range | Severity | Classification | Finding & Code Evidence | Recommended Correction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/visualization/plots.py` | 125–127 | **CRITICAL** | **Incorrect / Fabricated Evidence** | Hard-coded empirical coverage array: `empirical_cov = np.array([0.518, 0.612, 0.708, ...])` used for publication Figure 4 instead of calculating from test data. | Replace hard-coded arrays with dynamic evaluation: load test predictions from `results/metrics/` and compute empirical coverage. |
| `src/visualization/plots.py` | 149–153 | **CRITICAL** | **Incorrect / Fabricated Evidence** | Hard-coded synthetic SINR curve: `sinr_true = 22.0 - 0.28 * time_pts + 0.8 * np.sin(...)` used for Figure 5 instead of logging live simulator state. | Log true simulation link telemetry from `NetworkSimulator` during Scenario 3 execution and plot actual recorded SINR. |
| `src/visualization/plots.py` | 175–177 | **CRITICAL** | **Incorrect / Fabricated Evidence** | Hard-coded parameter sensitivity arrays: `sweep_pdr = [83.2, 88.5, 94.2, ...]` for Figure 6 without running a parameter sweep. | Run an actual sensitivity sweep script iterating $\kappa \in [0.0, 3.0]$ and plot the resulting empirical metrics. |
| `src/prediction_engine/data_collector.py` | 89–91 | **CRITICAL** | **Methodological Flaw / Data Leakage** | `train_test_split(X, y, test_size=0.25)` shuffles samples across contiguous time steps, causing sliding-window lookahead leakage. | Implement chronological episode-level split: use Episodes 0–9 for training and held-out Episodes 10–14 for testing. |
| `src/experiments/scenarios.py` | 47–53 | **CRITICAL** | **Missing Implementation** | `apply_scenario_4` contains an empty `pass` statement: `if current_t >= 35: pass`. The intended orbital descent was never implemented. | Implement orbital descent logic: manipulate satellite true anomaly or elevation threshold to force satellite below $10^\circ$. |
| `src/orchestration_engine/capro_engine.py` | 62–74 | **HIGH** | **Mathematical Unit Inconsistency** | Direct subtraction of incompatible units in `R_adj`: $\text{dB} - \kappa \cdot \text{dB} - 0.8 \cdot \text{ms} - 5.0 \cdot (\text{ratio})^2$. | Apply dimensionless utility normalization (e.g., Min-Max or Sigmoidal normalization mapping each term to $[0, 1]$ before weighting). |
| `src/channel_models/propagation.py` | 82–105 | **HIGH** | **Physical Model Misapplication** | ITU-R P.618 Earth-space slant path rain model applied indiscriminately to terrestrial base station (TBS) links. | Disaggregate models: apply ITU-R P.618 only to LEO satellite links; use ITU-R P.530 for terrestrial ground links. |
| `src/simulation_engine/network_simulator.py` | 198–200 | **MEDIUM** | **Hard-Coded Deviation from Config** | S-band ($2\text{ GHz}$) hard-coded for all links: `fc = self.carrier_freq_s_band`, bypassing Ka-band ($28\text{ GHz}$) feeder link configuration. | Use `self.carrier_freq_ka_band` for LEO feeder/high-capacity links when appropriate, or make band selection explicit per node. |
| `src/prediction_engine/models.py` | 83–91 | **MEDIUM** | **Theoretical Inconsistency** | Dividing non-parametric quantile spread by $3.29$ (`sigma_ale = aleatoric_spread / 3.29`) assumes Gaussian distribution. | Keep quantile spread as non-parametric interval width without converting to Gaussian standard deviation. |
| `src/prediction_engine/models.py` | 83–91 | **MEDIUM** | **Documentation Discrepancy** | Formula in documentation ($U = \sqrt{\sigma_{\text{epi}}^2 + \sigma_{\text{ale}}^2} + \lambda(q_{95}-q_{05})$) does not match code ($U = \sqrt{\sigma_{\text{epi}}^2 + \sigma_{\text{ale}}^2}$). | Harmonize mathematical documentation and implementation code. |
| `src/prediction_engine/uncertainty.py` | 33–38 | **MEDIUM** | **Methodological Misapplication** | Classification ECE formula ($| \text{cov} - 0.90 |$) applied across interval width bins. | Use continuous calibration curve (Reliability Diagram over nominal $\tau \in [0.1, 0.9]$) and Winkler interval score. |
| `src/baseline_methods/m2_threshold_predictive.py` | 42–48 | **MEDIUM** | **Algorithmic Flaw (Strawman)** | Linear trend slope evaluated on noisy fast fading without smoothing or hysteresis, causing artificial ping-pong thrashing ($141.5\text{ HO/min}$). | Add moving average filter and standard $1.5\text{ dB}$ hysteresis margin to provide a credible predictive baseline. |
| `src/simulation_engine/nodes.py` | 100–108 | **LOW** | **Simplified Energy Model** | Energy consumption assumes linear transmitter load without amplifier efficiency curves ($PAE$). | Document the linear RF power approximation clearly in limitations. |
| `src/simulation_engine/traffic.py` | 43–49 | **LOW** | **M/M/1 Queuing Approximation** | Delay model uses idealized single-server queue with hard cap at $\rho = 0.98$. | Acceptable for system-level simulation, but note that 3GPP RAN scheduling uses token-bucket / PF schedulers. |
| `config/simulation_config.yaml` | 2–5 | **LOW** | **Verified** | System parameters (frequencies, noise figure, thresholds) are well-structured and properly parsed as explicit floats. | None. Well implemented. |
| `src/simulation_engine/orbital.py` | 27–120 | **NONE** | **Verified** | WGS-84 Geodetic $\leftrightarrow$ ECEF and Topocentric ENU transformations are fully vector-verified. | None. Numerically sound. |
| `tests/` | 1–15 | **LOW** | **Partial Coverage** | Test suite achieves 15/15 passing, but tests verify isolated units rather than multi-tier stress scenarios. | Add end-to-end integration tests for multi-tier satellite handover and rain fade degradation. |

---

## 3. Detailed File-by-File Analysis

### 3.1. `src/visualization/plots.py`
- **Integrity Violation**: Lines 125–127 define Figure 4's calibration curve using static literals:
  ```python
  nominal_levels = np.array([0.50, 0.60, 0.70, 0.80, 0.90, 0.95])
  empirical_cov = np.array([0.518, 0.612, 0.708, 0.809, 0.908, 0.952])
  uncalibrated_cov = np.array([0.410, 0.490, 0.580, 0.670, 0.750, 0.810])
  ```
  This means Figure 4 does not reflect the output of `models/capro_predictor.joblib` on any real test set.
- **Lines 149–153**: Figure 5 generates a synthetic sinusoidal signal rather than pulling simulation traces:
  ```python
  sinr_true = 22.0 - 0.28 * time_pts + 0.8 * np.sin(0.4 * time_pts)
  sinr_true[25:40] -= 16.0
  ```
- **Lines 175–177**: Figure 6 hard-codes ablation PDR numbers:
  ```python
  sweep_pdr = [83.2, 88.5, 94.2, 97.4, 96.8, 95.1, 93.4]
  sweep_ho_rate = [14.2, 11.5, 8.1, 5.8, 5.5, 6.2, 7.5]
  ```
- **Audit Verdict**: Unacceptable for publication. All figures must be generated dynamically from validated experiment CSV logs.

### 3.2. `src/prediction_engine/data_collector.py`
- **Data Leakage**: The data collection script samples telemetry at $1.0\text{ s}$ intervals. Because orbital passes and user motion exhibit strong temporal autocorrelation, randomly assigning samples to train and test sets violates the independent and identically distributed (i.i.d.) assumption.
- **Evidence**:
  ```python
  X_train, X_test, y_train, y_test = train_test_split(
      X, y, test_size=0.25, random_state=random_seed
  )
  ```
- **Consequence**: Test metrics ($R^2 = 0.851$, $\text{MAE} = 5.63\text{ dB}$) are artificially boosted because the model was evaluated on samples that were adjacent in time to training samples.

### 3.3. `src/orchestration_engine/capro_engine.py`
- **Dimensional Error**:
  ```python
  base_utility = predicted_sinr_db - self.kappa * total_uncertainty_db
  if service_type == "URLLC":
      if latency_ms > 10.0:
          latency_penalty = (latency_ms - 10.0) * 0.8
  load_penalty = 5.0 * (node_load ** 2)
  return float(base_utility - latency_penalty - load_penalty)
  ```
- **Dimensional Analysis**:
  $$[R^{\text{adj}}] = [\text{dB}] - \text{dimensionless} \cdot [\text{dB}] - \left[\frac{\text{dB}}{\text{ms}}\right] \cdot [\text{ms}] - [\text{dB}] \cdot [\text{ratio}]^2$$
  The coefficients $0.8$ and $5.0$ act as implicit dimensional conversion factors, but their numerical values are arbitrary and not calibrated to real operational trade-offs.

### 3.4. `src/experiments/scenarios.py`
- **Non-Functional Scenario 4**:
  ```python
  def apply_scenario_4(sim: NetworkSimulator, current_t: int):
      """Scenario 4: Satellite visibility reduction & orbital departure."""
      sim.rain_rate_mm_h = 5.0
      sim.shadowing_flutter_std = 0.5
      if current_t >= 35:
          pass
  ```
  The core hook for Scenario 4 contains no operational logic. The simulation runs identically to a low-rain scenario.

