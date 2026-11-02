# ORBIT-INTEL 6G: CAPRO Mathematical Formulation & Algorithm Audit

---

## 1. Algorithmic Formulation Audit

The Confidence-Aware Predictive Reliability Orchestration (CAPRO) decision engine is implemented in `src/orchestration_engine/capro_engine.py`.

### 1.1. Dimensional Analysis of the Decision Score
- **Reported Objective**:
  $$R_{i,j}^{\text{adj}}(t+\Delta) = \hat{Q}_{i,j}(t+\Delta) - \kappa \cdot U_{i,j}(t+\Delta) - \mathcal{C}_{\text{latency}}(j) - \mathcal{C}_{\text{congestion}}(j)$$
- **Code Implementation** (`capro_engine.py`, lines 40–55):
  ```python
  base_utility = predicted_sinr_db - self.kappa * total_uncertainty_db
  if service_type == "URLLC":
      if latency_ms > 10.0:
          latency_penalty = (latency_ms - 10.0) * 0.8
  else:
      if latency_ms > 50.0:
          latency_penalty = (latency_ms - 50.0) * 0.2
  load_penalty = 5.0 * (node_load ** 2)
  return float(base_utility - latency_penalty - load_penalty)
  ```
- **Dimensional Verification**:
  1. $\hat{Q}_{i,j}$ has units of **decibels (dB)**: ratio of signal power to noise power.
  2. $U_{i,j}$ has units of **decibels (dB)**: standard deviation / spread of SINR.
  3. $\kappa$ is dimensionless. Therefore, $\hat{Q} - \kappa U$ is strictly in **dB**.
  4. $\text{latency\_ms}$ has units of **milliseconds (ms)**. The multiplier $0.8$ acts as an implicit conversion factor of $\left[\frac{\text{dB}}{\text{ms}}\right]$. However, this linear scaling has no empirical or physical derivation.
  5. $\text{node\_load} = \rho \in [0, 1]$ is **dimensionless**. The multiplier $5.0$ acts as an implicit penalty in $\text{dB}$.
- **Audit Verdict**: **INCORRECT (Dimensionally Inconsistent)**.
  - Adding logarithmic units directly to temporal milliseconds and load ratios without non-dimensional normalization (such as mapping all terms to a normalized cost function $\mathcal{J} \in [0, 1]$ via min-max or sigmoid scaling) violates dimensional analysis.

---

## 2. Did Uncertainty Actually Influence Orchestration Decisions?

### 2.1. Theoretical Expectation
The central premise of CAPRO is that if Candidate $A$ has $\hat{Q}_A = 22\text{ dB}$ with high uncertainty $U_A = 6\text{ dB}$, and Candidate $B$ has $\hat{Q}_B = 18\text{ dB}$ with low uncertainty $U_B = 1\text{ dB}$, with $\kappa = 1.5$:
- $R_A^{\text{adj}} = 22 - 1.5(6) = 13\text{ dB}$.
- $R_B^{\text{adj}} = 18 - 1.5(1) = 16.5\text{ dB}$.
Candidate $B$ should be chosen over Candidate $A$, preventing link drops.

### 2.2. Empirical Verification in Benchmark Runs
We audited the actual values of $\hat{Q}$, $U$, and selected nodes across all 12 users during the 60 benchmark runs:
1. **Terrestrial Nodes (`TBS-01`, `TBS-02`)**:
   - $\hat{Q}_{\text{TBS}} \approx +43\text{ to } +56\text{ dB}$.
   - $U_{\text{TBS}} \approx 0.8\text{ to } 1.5\text{ dB}$.
   - $R_{\text{TBS}}^{\text{adj}} \approx 42\text{ to } 54\text{ dB}$.
2. **Stratospheric Node (`HAPS-01`)**:
   - $\hat{Q}_{\text{HAPS}} \approx +18\text{ to } +26\text{ dB}$.
   - $U_{\text{HAPS}} \approx 1.0\text{ to } 2.0\text{ dB}$.
   - $R_{\text{HAPS}}^{\text{adj}} \approx 16\text{ to } 23\text{ dB}$.
3. **Satellite Node (`SAT-01`)**:
   - $\hat{Q}_{\text{SAT}} \approx -3.4\text{ to } +5.0\text{ dB}$.
   - $U_{\text{SAT}} \approx 2.5\text{ to } 7.0\text{ dB}$.
   - $R_{\text{SAT}}^{\text{adj}} \approx -10\text{ to } -2\text{ dB}$.

### 2.3. The Inactive Uncertainty Penalty
- **Audit Finding**: In the current simulation setup, the baseline SINR difference between terrestrial/HAPS nodes and the satellite is **$> 20\text{ dB}$**.
- Because $R_{\text{TBS}}^{\text{adj}} \gg R_{\text{HAPS}}^{\text{adj}} \gg R_{\text{SAT}}^{\text{adj}}$, the uncertainty penalty $\kappa U$ ($1.5 \times 4\text{ dB} = 6\text{ dB}$) was **never large enough to bridge the $20\text{--}40\text{ dB}$ gap between tiers**.
- Consequently, **M3 (Prediction-Only) and M4 (CAPRO) made identical node selections at every single time epoch**.
- **Audit Verdict**: **NOT VERIFIED (Uncertainty Term was Dormant)**.
  - The uncertainty penalty was mathematically coded, but due to scenario design and node geometry, it never altered a decision between satellite and terrestrial tiers.

---

## 3. Threshold and Hysteresis Parameter Audit

### 3.1. Orbital Visibility Lookahead Margin ($T_{\text{HO\_margin}} = 12.0\text{ s}$)
- **Source**: `capro_engine.py` (lines 35, 115).
- **Justification Audit**:
  - The parameter is declared in `simulation_config.yaml` as `handover_margin_s: 12.0`.
  - Is $12\text{ s}$ justified? In 3GPP TR 38.821 (NTN Solutions), the random access and RRC reconfiguration procedure over an NTN feeder-plus-service link takes approximately $80\text{--}150\text{ ms}$. A lookahead margin of $12\text{ seconds}$ represents roughly $2\%$ of a $10\text{-minute}$ LEO pass.
  - **Audit Finding**: $12\text{ seconds}$ is an intuitive operational buffer, but **no sensitivity analysis or experimental ablation** was performed to compare $T_{\text{HO\_margin}} \in [5\text{s}, 10\text{s}, 20\text{s}, 30\text{s}]$. It is an arbitrary design parameter.

### 3.2. Elevation Hysteresis Margin ($\Delta_{\text{hyst}} = 2.5\text{ dB}$)
- **Source**: `capro_engine.py` (line 34).
- **Justification Audit**:
  - In 3GPP Event A3 cellular handover specifications, hysteresis margins typically range from $1.0\text{ to } 3.0\text{ dB}$ with a Time-To-Trigger (TTT) of $40\text{--}320\text{ ms}$.
  - The chosen value ($2.5\text{ dB}$) is standard cellular practice.
  - However, in `plots.py`, Figure 6 claims to show an ablation of $\kappa$, but no ablation was ever run for $\Delta_{\text{hyst}}$.
- **Audit Verdict**: **PARTIALLY VERIFIED (Standard Heuristic, Lacks Empirical Calibration)**.

---

## 4. Constraint Enforcement & Fallback Logic

- **Outage SLA Constraint** ($P_{\text{outage}} \le 10^{-4}$):
  - In `capro_engine.py`:
    ```python
    if q_lower < self.outage_thresh_db:
        r_adj -= 15.0
    ```
    This applies a soft penalty rather than a hard constraint filter. If all nodes have $q_{\text{lower}} < 3.0\text{ dB}$, it still selects the best available link.
- **Global Fallback Logic**:
  - If no node is visible, the orchestrator returns `GLOBAL_OUTAGE_NO_VIABLE_TIER` with `selected_node_id = None`. This was verified and functions correctly.
- **Audit Verdict**: **VERIFIED (Soft-Constraint Fallback Mechanism)**.

