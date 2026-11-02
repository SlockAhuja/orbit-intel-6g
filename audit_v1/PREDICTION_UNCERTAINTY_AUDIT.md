# ORBIT-INTEL 6G: Predictive Intelligence & Uncertainty Quantification Audit

---

## 1. Feature Engineering and Data Preprocessing

### 1.1. Audit of the 17 Feature Variables
`src/prediction_engine/feature_engineering.py` declares 17 features:

| Index | Feature Name | Declared Physical Meaning | Units | Implemented Derivation | Status |
| :---: | :--- | :--- | :---: | :--- | :---: |
| 0 | `current_sinr_db` | Instantaneous SINR | dB | Telemetry query | **Verified** |
| 1 | `sinr_rolling_mean_5s` | 5-step rolling average SINR | dB | `np.mean(sinr_vals[-5:])` | **Verified** |
| 2 | `sinr_rolling_std_5s` | 5-step rolling variance | dB | `np.std(sinr_vals[-5:])` | **Verified** |
| 3 | `sinr_trend_slope` | First-order linear fit slope | dB/s | `np.polyfit(t, sinr_vals, 1)[0]` | **Verified** |
| 4 | `elevation_deg` | Topocentric elevation angle | degrees | Orbital ENU transform | **Verified** |
| 5 | `elevation_rate_deg_s` | Rate of change of elevation | deg/s | Backward difference | **Verified** |
| 6 | `slant_distance_km` | Geometric Euclidean distance | km | Slant distance / 1000 | **Verified** |
| 7 | `doppler_shift_khz` | Carrier Doppler shift | kHz | Doppler shift Hz / 1000 | **Verified** |
| 8 | `doppler_rate_khz_s` | Doppler rate | kHz/s | Backward difference | **Verified** |
| 9 | `remaining_visibility_s` | Time until $\theta < \theta_{\text{min}}$ | seconds | Orbital lookahead estimator | **Verified** |
| 10 | `node_load` | Fractional platform traffic | $[0, 1]$ | Query on node load | **Verified** |
| 11 | `available_bandwidth_mhz`| Residual spectral bandwidth | MHz | $B \times (1 - \text{load})$ | **Verified** |
| 12 | `tier_leo` | One-hot indicator for LEO | binary | $1.0$ if LEO else $0.0$ | **Verified** |
| 13 | `tier_haps` | One-hot indicator for HAPS | binary | $1.0$ if HAPS else $0.0$ | **Verified** |
| 14 | `tier_uav` | One-hot indicator for UAV | binary | $1.0$ if UAV else $0.0$ | **Verified** |
| 15 | `tier_tbs` | One-hot indicator for TBS | binary | $1.0$ if TBS else $0.0$ | **Verified** |
| 16 | `is_visible` | Physical line-of-sight flag | binary | $1.0$ if visible else $0.0$ | **Verified** |

- **Audit Finding**: All 17 features are actively extracted and mapped without dimension errors.
- **Audit Verdict**: **VERIFIED**.

---

## 2. Temporal Data Leakage Audit

### 2.1. Dataset Generation Structure
In `src/prediction_engine/data_collector.py`:
- 12 episodes of $50\text{ seconds}$ duration are simulated.
- Telemetry is recorded every $1\text{ second}$.
- For each time $t \in [5, 40]$, sliding-window features are paired with target $y = \text{SINR}(t + 10\text{s})$.
- Total samples generated: $12,425$.

### 2.2. The Leakage Mechanism
Lines 89–91 in `data_collector.py`:
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=random_seed
)
```
- **Evidence of Leakage**:
  - Sample $k$ corresponds to User 1, Node SAT-01 at $t=20\text{ s}$ (with target at $t=30\text{ s}$).
  - Sample $k+1$ corresponds to User 1, Node SAT-01 at $t=21\text{ s}$ (with target at $t=31\text{ s}$).
  - Random splitting assigns Sample $k$ to the training set and Sample $k+1$ to the testing set.
  - The feature vectors of Sample $k$ and Sample $k+1$ share $80\%$ of their sliding window history ($t \in [16, 20]$).
- **Audit Verdict**: **CRITICAL METHODOLOGICAL FLAW**.
  - The model effectively memorizes the channel trajectory because the test set contains points interleaved between training time-steps.
  - *Required Correction*: Data MUST be partitioned by independent simulation episodes (e.g., Episodes 0–8 for training, Episodes 9–11 for testing) or using forward-chaining rolling-origin cross-validation.

---

## 3. Uncertainty Formulation & Mathematical Consistency

### 3.1. Discrepancy Between Documentation and Implementation
- **Reported Formula in Manuscript & Formulation Document**:
  $$U_{i,j}(t+\Delta) = \sqrt{\sigma_{\text{epi},i,j}^2 + \sigma_{\text{ale},i,j}^2} + \lambda \cdot (\hat{q}_{0.95} - \hat{q}_{0.05})$$
- **Actual Implementation in `models.py` (lines 80–91)**:
  ```python
  q_lower = np.minimum(q05, q50)
  q_upper = np.maximum(q95, q50)
  aleatoric_spread = q_upper - q_lower

  tree_preds = np.array([tree.predict(X) for tree in self.model_rf.estimators_])
  epistemic_variance = np.var(tree_preds, axis=0)
  epistemic_std = np.sqrt(epistemic_variance)

  sigma_ale = aleatoric_spread / 3.29
  total_uncertainty = np.sqrt(epistemic_variance + sigma_ale ** 2)
  ```
- **Auditor Findings**:
  1. The term $+ \lambda (\hat{q}_{0.95} - \hat{q}_{0.05})$ is **COMPLETELY MISSING** from the code.
  2. The division `sigma_ale = aleatoric_spread / 3.29` assumes a Gaussian distribution where the $90\%$ confidence interval spans $2 \times 1.645\sigma = 3.29\sigma$.
  3. However, quantile regression is an explicitly non-parametric technique (pinball loss) designed to avoid Gaussianity assumptions. Converting an empirical quantile spread to an equivalent Gaussian standard deviation without validation is statistically unjustified.
- **Audit Verdict**: **INCORRECT / INCONSISTENT**.

---

## 4. Calibration Evaluation: PICP vs. Expected Calibration Error (ECE)

### 4.1. Audit of the Reported 90.76% PICP
- Prediction Interval Coverage Probability (PICP) was computed as:
  $$\mathrm{PICP} = \frac{1}{N} \sum_{n=1}^N \mathbb{I}\left( y_n \in [\hat{q}_{0.05, n}, \, \hat{q}_{0.95, n}] \right)$$
- On the held-out test split, the model covered $90.76\%$ of the samples for a nominal $90\%$ target.
- **Audit Finding**: While $90.76\%$ appears close to $90\%$, this result was obtained on a test set corrupted by temporal data leakage. On an independent trajectory, coverage will degrade.

### 4.2. Audit of the Reported 0.0160 ECE
- **Implementation in `uncertainty.py` (lines 18–38)**:
  ```python
  uncertainty = q_upper - q_lower
  sort_idx = np.argsort(uncertainty)
  ...
  for b in range(num_bins):
      covered = (y_sorted[start:end] >= ql_sorted[start:end]) & (y_sorted[start:end] <= qu_sorted[start:end])
      bin_coverages.append(float(np.mean(covered)))
  ece = float(np.mean([abs(cov - 0.90) for cov in bin_coverages]))
  ```
- **Critical Methodological Flaw**:
  - The Expected Calibration Error (ECE) metric introduced by Guo et al. (ICML 2017) applies strictly to **classification** models outputting class probabilities $p \in [0, 1]$.
  - The implementation in `uncertainty.py` sorts samples by prediction interval width, bins them into 10 deciles, computes coverage within each width bin, and takes the average difference from $0.90$.
  - This measures **interval sharpness homogeneity**, NOT calibration error!
  - In regression interval estimation, calibration must be evaluated across varying nominal coverage levels $\alpha \in \{0.1, 0.2, \dots, 0.9\}$ (Reliability Curve), or through the **Winkler Interval Score**:
    $$\mathrm{IS}_\alpha(l, u, y) = (u - l) + \frac{2}{\alpha}(l - y)\mathbb{I}(y < l) + \frac{2}{\alpha}(y - u)\mathbb{I}(y > u)$$
- **Audit Verdict**: **METHODOLOGICALLY FLAWED METRIC**.
  - Calling this metric "ECE" and reporting $0.0160$ misrepresents established machine learning terminology.

