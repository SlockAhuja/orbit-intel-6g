# ORBIT-INTEL 6G — PHASE 6 DASHBOARD IMPLEMENTATION & VERIFICATION REPORT

## 1. Executive Summary

This report documents the architectural verification, data provenance integration, and empirical audit of the **ORBIT-INTEL 6G Interactive Demonstration Dashboard** (`dashboard/app.py`).

The dashboard is engineered for high-visibility international scientific exhibition at the **IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026** and subsequent IEEE technical symposia.

### Key Verification Milestones:
- **Zero Hard-Coded Performance Metrics:** All performance indicators, comparative bar charts, and calibration plots dynamically ingest verified empirical artifacts from `phase4_benchmarking/` and `phase5_robustness/`.
- **Data Provenance System:** Every dashboard module displays active data provenance indicators reporting the source CSV file path, observation count, and git commit hash.
- **Seven Interactive Modules:**
  1. Multi-Tier SAGIN Topology & 3D Constellation Orbit Viewer
  2. Multi-Horizon Predictive Intelligence & Dual Uncertainty Calibration
  3. CAPRO Intelligent Orchestration Engine & Transparent Explainability Log
  4. Large-Scale Multi-Tier Benchmarks (M1 vs M2 vs M3 vs M4)
  5. Statistical Hypothesis Testing & Significance Deep Dive
  6. Controlled Component Ablations (V1–V7) & Sensitivity Sweeps
  7. Live Interactive Simulation Sandbox with Real-Time Rain & Flutter Injection

---

## 2. Module-by-Module Technical Verification

### Module 1: SAGIN Topology & Orbital Mechanics
- Visualizes 3D ECEF position coordinates for 2 LEO Satellites ($600\text{ km}$, $53^\circ$ inclination), 1 HAPS Stratospheric Relay ($20\text{ km}$), 1 UAV Loiter Cell ($300\text{ m}$), and 3 Terrestrial Base Stations ($30\text{ m}$).
- Renders 12 geographically distributed mobile terminals across Urban, Suburban, Remote, and Maritime cohorts.
- Dynamically updates Doppler shift ($\pm 48\text{ kHz}$) and topocentric elevation angles.

### Module 2: Predictive Link Intelligence
- Ingests validated model artifacts from `models/capro_predictor.joblib` and `phase2_preflight/PHASE2_METRIC_REPRODUCTION.csv`.
- Displays real-time dual uncertainty decomposition: Quantile Gradient Boosting aleatoric interval ($\hat{q}_{05}$ to $\hat{q}_{95}$) and Random Forest ensemble tree variance ($s_{\text{RF}}^2$).
- Verified regression calibration curve displaying Empirical Coverage (PICP = $89.35\%$) and Expected Calibration Error ($\text{ECE} = 0.016$).

### Module 3: CAPRO Decision Engine & Explainability Audit Log
- Implements normalized multi-attribute utility $J_{u,i} \in [0, 1]$ across link quality, latency SLA, node capacity, handover cost, and epistemic risk.
- Displays transparent explainability records for each user attachment decision, logging trigger codes (`INITIAL_OPTIMAL_ATTACH`, `STEADY_STATE_OPTIMAL`, `PROACTIVE_SATELLITE_DESCENT`, `FALLBACK_RELAXED_LATENCY_SLA`).

### Module 4: Rigorous Scientific Comparative Benchmarks
- Directly ingests `phase4_benchmarking/RAW_BENCHMARK_RESULTS.csv` ($400$ runs) and `BENCHMARK_METRICS_BY_METHOD.csv`.
- Renders disaggregated comparisons across PDR, outage probability, P95 tail latency, URLLC SLA compliance, and handover frequency.
- Empirically displays CAPRO's $95.42\%$ reduction in handover churn relative to M2.

### Module 5: Statistical Significance & Hypothesis Testing
- Directly ingests `phase4_benchmarking/STATISTICAL_TEST_RESULTS.csv` ($36$ hypothesis tests) and `METHOD_CONFIDENCE_INTERVALS.csv`.
- Formats paired Student's $t$-statistics, Wilcoxon signed-rank $p$-values, Cohen's $d$ effect sizes, and exact $95\%$ Confidence Intervals.

### Module 6: Controlled Ablation & Sensitivity Sweeps
- Dynamically renders ablation performance across variants V1 through V7 (`phase4_benchmarking/CAPRO_ABLATION_RESULTS.csv` and `phase5_robustness/ROBUSTNESS_METRICS.csv`).
- Visualizes multi-horizon stability curves ($H \in \{1, 3, 5, 10\text{ s}\}$) and hysteresis margin sweeps ($\Delta_{\text{hyst}} \in [0.00, 0.18]$).

### Module 7: Live Stress-Testing Sandbox
- Allows exhibition attendees to dynamically inject severe convective cloudburst rain cells ($R = 0\text{--}100\text{ mm/h}$) and intense shadow flutter ($\sigma = 0\text{--}6\text{ dB}$).
- Provides a side-by-side live comparison between CAPRO and the M1 Reactive baseline, highlighting CAPRO's predictive lookahead vs. reactive link dropouts.
