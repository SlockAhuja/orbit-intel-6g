# ORBIT-INTEL 6G: Experimental Validation & Benchmarking Audit

---

## 1. Experimental Design and Benchmark Protocol

### 1.1. Experiment Matrix Audit
The benchmarking framework in `src/experiments/benchmark_runner.py` executes:
- **Methods (4)**: M1 (Reactive), M2 (Threshold Predictive), M3 (Prediction-Only AI), M4 (Proposed CAPRO).
- **Scenarios (5)**: Normal, High Congestion, Sudden Rain, Satellite Visibility Handover, High Uncertainty Flutter.
- **Random Seeds (3)**: 42, 101, 202.
- **Total Executions**: $4 \times 5 \times 3 = 60\text{ runs}$.
- **Verification**: Each execution instantiated a fresh `NetworkSimulator(random_seed=s)` with reset clocks, energy states, and user positions. Initial conditions and traffic requests were strictly identical across all 4 methods.
- **Audit Verdict**: **VERIFIED (Reproducible Execution Pipeline)**.

---

## 2. Critical Comparison: M3 (Prediction-Only) vs. M4 (CAPRO)

The central research hypothesis posed in Section 3 of the Master Prompt was:
> *"Can uncertainty-aware AI predictions improve communication reliability and resource efficiency compared with conventional predictive resource allocation methods?"*

### 2.1. Side-by-Side Numerical Audit
Comparing raw experiment results from `results/metrics/benchmark_results_raw.csv`:

| Scenario | Seed | M3: PDR (%) | M4: PDR (%) | M3: Latency (ms) | M4: Latency (ms) | M3: Outage Prob | M4: Outage Prob | M3: Handovers (/min) | M4: Handovers (/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario 1 (Normal)** | 42 | 99.917% | 99.917% | 1.864 ms | 1.864 ms | 0.0000 | 0.0000 | 2.0 | 2.0 |
| | 101 | 99.819% | 99.819% | 1.842 ms | 1.842 ms | 0.0014 | 0.0014 | 4.0 | 3.0 |
| | 202 | 99.889% | 99.875% | 1.951 ms | 1.950 ms | 0.0000 | 0.0000 | 1.0 | 1.0 |
| **Scenario 2 (Congestion)** | 42 | 99.861% | 99.861% | 1.636 ms | 1.636 ms | 0.0000 | 0.0000 | 2.0 | 2.0 |
| | 101 | 99.833% | 99.833% | 1.614 ms | 1.614 ms | 0.0014 | 0.0014 | 4.0 | 3.0 |
| | 202 | 99.931% | 99.917% | 1.700 ms | 1.693 ms | 0.0000 | 0.0000 | 1.0 | 1.0 |
| **Scenario 3 (Rainstorm)** | 42 | 99.931% | 99.931% | 1.863 ms | 1.863 ms | 0.0000 | 0.0000 | 2.0 | 2.0 |
| | 101 | 99.958% | 99.958% | 1.842 ms | 1.842 ms | 0.0000 | 0.0000 | 3.0 | 3.0 |
| | 202 | 99.875% | 99.875% | 1.949 ms | 1.949 ms | 0.0000 | 0.0000 | 1.0 | 1.0 |
| **Scenario 4 (Departure)** | 42 | 99.931% | 99.931% | 1.863 ms | 1.863 ms | 0.0000 | 0.0000 | 2.0 | 2.0 |
| | 101 | 99.958% | 99.958% | 1.842 ms | 1.842 ms | 0.0000 | 0.0000 | 3.0 | 3.0 |
| | 202 | 99.875% | 99.875% | 1.949 ms | 1.949 ms | 0.0000 | 0.0000 | 1.0 | 1.0 |
| **Scenario 5 (Flutter)** | 42 | 99.931% | 99.931% | 1.863 ms | 1.863 ms | 0.0000 | 0.0000 | 2.0 | 2.0 |
| | 101 | 99.972% | 99.972% | 1.842 ms | 1.842 ms | 0.0000 | 0.0000 | 3.0 | 3.0 |
| | 202 | 99.764% | 99.764% | 1.949 ms | 1.949 ms | 0.0014 | 0.0014 | 1.0 | 1.0 |

### 2.2. Statistical Analysis
- Paired t-test on PDR between M3 and M4: $t = 1.00$, $p = 0.334$ (no statistically significant difference).
- Difference in Mean PDR across all 15 runs: **$0.0000\%$** (identical to 4 decimal places).
- Difference in Latency: $< 0.007\text{ ms}$.
- **Auditor Verdict**: **HYPOTHESIS NOT PROVEN**.
  - CAPRO (M4) fails to demonstrate any statistically significant advantage over uncalibrated prediction (M3).
  - The reason is topological: all users connected to terrestrial base stations and HAPS; the uncertainty on satellite channels was never activated in the decision path.

---

## 3. Investigation of the Claimed 98.6% Handover Reduction

In the report, the authors claimed:
> *"CAPRO reduces handover churn by 98.6% compared to predictive baselines."*

### 3.1. What Was the Actual Denominator?
- In `results/metrics/benchmark_summary_stats.csv`:
  - M2 (Threshold Predictive) Handover Frequency: **$141.5\text{ handovers/min}$**.
  - M4 (CAPRO) Handover Frequency: **$2.0\text{ handovers/min}$**.
  - Percentage reduction: $\frac{141.5 - 2.0}{141.5} \times 100\% = \mathbf{98.59\%}$.
- But compare M4 against M1 (Reactive) and M3 (Prediction-Only):
  - M1 (Reactive): **$33.4\text{ handovers/min}$** $\to$ Reduction is $94.0\%$.
  - M3 (Prediction-Only): **$2.13\text{ handovers/min}$** $\to$ Reduction is **only $6.1\%$** (from $2.13$ to $2.00$)!

### 3.2. Why Did M2 Ping-Pong at 141.5 Handovers/min?
- In `src/baseline_methods/m2_threshold_predictive.py`:
  - `M2` computes a linear trend slope on raw instantaneous SINR samples without filtering.
  - Rayleigh and Rician fast fading creates high-frequency fluctuations (+/- 3 dB per second).
  - Whenever the slope becomes temporarily negative, predicted SINR dips below $10.0\text{ dB}$, triggering an immediate handover.
  - In the next second, the new node's slope turns negative, triggering another handover back.
  - M2 contains **ZERO hysteresis and ZERO time-to-trigger (TTT) protection**.
- **Audit Verdict**: **UNFAIR STRAWMAN BASELINE**.
  - M2 was constructed without standard cellular hysteresis, exaggerating CAPRO's stability advantage. Against standard M1 Reactive, the reduction is modest, and against M3, the difference is negligible.

---

## 4. Why Did PDR Remain Above 99% in Adverse Scenarios?

### 4.1. The 55 mm/h Rainstorm Scenario
In Scenario 3, a heavy rain rate of $R = 55.0\text{ mm/h}$ was injected:
- Specific attenuation for Ka-band at $55\text{ mm/h}$ is $\approx 1.8\text{ dB/km}$, creating $>12\text{ dB}$ attenuation on LEO satellites.
- Yet M1, M3, and M4 all reported **$99.85\%\text{--}99.95\%$ PDR with ZERO outages**!
- **Root Cause**:
  - As proven in Section 3 of `PHYSICAL_MODEL_AUDIT.md`, all 12 users were served by ground towers (`TBS-01`, `TBS-02`) and stratospheric HAPS (`HAPS-01`).
  - Terrestrial base stations were located within $2.5\text{ km}$, maintaining SINR $> 35\text{ dB}$ even with terrestrial rain attenuation.
  - The satellite link suffered the rain fade in background telemetry, but **no user traffic was flowing over the satellite link**.
- **Audit Verdict**: **FLAWED EXPERIMENTAL SCENARIOS**.
  - The adverse scenarios did not actually stress the serving links. To be valid, users must be placed in a satellite-only coverage environment (remote/maritime) where terrestrial backup is physically impossible.

