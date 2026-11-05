# ORBIT-INTEL 6G — PHASE 4 EXECUTIVE BENCHMARKING SUMMARY

## 1. Experiment Overview

Phase 4 of the ORBIT-INTEL 6G project executed an exhaustive, mathematically controlled benchmarking campaign comparing four multi-tier SAGIN network orchestration paradigms:
- **M1 (Reactive Baseline):** Standard instantaneous SNR thresholding ($3.0\text{ dB}$) with greedy local attachment.
- **M2 (Threshold-Predictive Baseline):** Extrapolates first-order linear SINR trends over a sliding 5-second window.
- **M3 (Point-Prediction Baseline):** Multi-horizon ML point forecast ($\hat{q}_{50}$) without uncertainty bounds or latency feasibility gating.
- **M4 (Proposed CAPRO):** Confidence-Aware Predictive Reliability Orchestration integrating dual uncertainty, dimensionless normalized utility, hard SLA constraints, and hysteresis gating.

### Execution Scale
- **400 Monte Carlo Evaluation Runs:** 100 paired evaluation episodes per method across 5 standard operational scenarios and 20 distinct pseudo-random seeds ($S \in [101, 120]$).
- **Physical SAGIN Tiers:** LEO Satellites ($600\text{ km}$), HAPS ($20\text{ km}$), UAV ($300\text{ m}$), and Terrestrial Base Stations ($30\text{ m}$).
- **Evaluation Duration:** $60\text{ seconds}$ per run at $1.0\text{ s}$ physical time-steps ($24,000$ simulated network seconds total).

---

## 2. Key Empirical Findings

```mermaid
graph TD
    A["400 Paired Monte Carlo Runs"] --> B["Handover Stability"]
    A --> C["SLA Compliance"]
    A --> D["Fairness & Energy"]

    B --> B1["CAPRO: 2.20 HO/min<br>M1: 28.86 HO/min (-92.4%)<br>M2: 48.07 HO/min (-95.4%)"]
    C --> C1["Zero Handover Failures<br>P95 Latency: 12.98 ms<br>URLLC Violations: 50.05% vs 54.38% (M2)"]
    D --> D1["Jain's Fairness: 0.446 vs 0.399 (M2)<br>Energy Efficiency: 177.7 vs 180.4 J/Mbit (M2)"]
```

1. **Dramatic Elimination of Handover Ping-Pong:**
   - M2 suffered catastrophic handover thrashing ($48.07\text{ HO/min}$) due to fast fading sensitivity.
   - M1 exhibited $28.86\text{ HO/min}$ as users chased volatile instantaneous RSSI.
   - **CAPRO suppressed handover frequency to $2.20\text{ HO/min}$**---a **$92.38\%$ reduction vs M1** and **$95.42\%$ reduction vs M2** ($p < 10^{-34}$).
2. **Superiority over Threshold Prediction (M2):**
   - CAPRO outperformed M2 across all metrics: higher PDR ($+2.50\%$, $p < 10^{-26}$), lower mean latency ($-0.66\text{ ms}$, $p < 10^{-15}$), lower URLLC violations ($-4.33\%$, $p < 10^{-25}$), and zero handover failures (vs $0.41\%$, $p < 0.005$).
3. **Equitable Geographic Access:**
   - CAPRO maintained equity across all four user cohorts (Urban, Suburban, Remote, Maritime), improving Jain's Fairness Index by $+11.75\%$ over M2 ($0.446$ vs $0.399$, $p < 10^{-7}$).
4. **Energy Efficiency:**
   - Suppressing unnecessary handovers saved millions of control-plane messages, reducing energy consumption to $177.71\text{ J/Mbit}$ ($p < 10^{-18}$ vs M2).

---

## 3. Artifact Traceability & Compliance

All Phase 4 findings derive strictly from verifiable, saved machine CSV artifacts:
- Configuration: `phase4_benchmarking/BENCHMARK_CONFIGURATION.csv`
- Complete Episode Log: `phase4_benchmarking/MONTE_CARLO_RUN_MANIFEST.csv` ($400$ runs)
- Raw Measurements: `phase4_benchmarking/RAW_BENCHMARK_RESULTS.csv` ($193\text{ KB}$)
- Disaggregated Metrics: `BENCHMARK_METRICS_BY_METHOD.csv`, `BENCHMARK_METRICS_BY_SCENARIO.csv`, `BENCHMARK_METRICS_BY_SERVICE.csv`, `BENCHMARK_METRICS_BY_TIER.csv`
- Statistical Significance: `phase4_benchmarking/STATISTICAL_TEST_RESULTS.csv` ($36$ hypothesis tests)
- 95% Confidence Intervals: `phase4_benchmarking/METHOD_CONFIDENCE_INTERVALS.csv`

Phase 4 benchmarking is officially complete, validated, and ready for publication integration.
