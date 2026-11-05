# PHASE 2 EXPERIMENTAL REPORT: MULTI-EPISODE GENERATION & SCENARIO COVERAGE

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Target Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Document:** Simulation Episode Generation & Dataset Catalog  
**Date:** November 2026  

---

## 1. Executive Summary

To provide a sound empirical foundation for predictive modeling free from temporal data leakage, an independent multi-episode simulation campaign was executed using the reconstructed physical network simulator.

A total of **30 distinct simulation episodes** of 60 seconds duration each were generated, yielding **36,908 telemetry feature-target samples**. The episodes systematically span all 5 operational network scenarios defined in the research framework:
1. Scenario 1: Nominal clear-sky communication.
2. Scenario 2: High traffic surge and terrestrial base station congestion.
3. Scenario 3: Sudden convective cloudburst and rain fade ($40\text{--}70\text{ mm/h}$).
4. Scenario 4: LEO satellite visibility reduction, topocentric departure, and inter-satellite handover.
5. Scenario 5: High channel volatility and multipath shadowing flutter ($\sigma_{\text{flutter}} \in [2.5, 4.5]\text{ dB}$).

Each episode was executed with an independent pseudo-random seed, varied user trajectories, and randomized atmospheric channel parameters. All individual episode traces are persisted in `phase2_experiments/episodes/`.

---

## 2. Scenario Distribution & Parameter Space

The 30 episodes are balanced across the 5 scenarios (6 episodes per scenario), parameterized as follows:

| Scenario ID | Scenario Name | Episodes | Duration | Rain Rate (mm/h) | Flutter Std (dB) | Key Physical Dynamics |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **Scen 1** | Normal Conditions | 0, 1, 2, 3, 4, 5 | 60 s | $0.0 - 2.0$ | $0.0 - 0.4$ | Stable multi-tier propagation; baseline clear sky. |
| **Scen 2** | High Congestion Surge | 6, 7, 8, 9, 10, 11 | 60 s | $0.0 - 3.0$ | $0.1 - 0.5$ | Terrestrial load reaches saturation ($>0.85$); users queue. |
| **Scen 3** | Sudden Rain Degradation | 12, 13, 14, 15, 16, 17 | 60 s | $40.0 - 70.0$ | $0.8 - 1.8$ | Severe cloudburst attenuation ($12\text{--}18\text{ dB}$ fade) at $t \approx 25\text{--}55\text{ s}$. |
| **Scen 4** | Satellite Visibility Handover | 18, 19, 20, 21, 22, 23 | 60 s | $2.0 - 10.0$ | $0.2 - 0.8$ | `SAT-01` drops below $10^\circ$; `SAT-02` ascends; handover executed. |
| **Scen 5** | High Uncertainty Flutter | 24, 25, 26, 27, 28, 29 | 60 s | $15.0 - 35.0$ | $2.5 - 4.5$ | Extreme log-normal shadowing variance; tests epistemic bounds. |

---

## 3. Dataset Summary Statistics

- **Total Episodes Executed**: 30
- **Total Telemetry Samples**: 36,908
- **Samples per Episode**: $\sim 1,170 - 1,280$
- **Candidate Prediction Horizons Recorded**: $H \in \{1, 3, 5, 10\}\text{ seconds}$
- **Continuous Targets**: `target_sinr_1s`, `target_sinr_3s`, `target_sinr_5s`, `target_sinr_10s`
- **Binary Classification Targets**: `target_outage_1s`, `target_outage_3s`, `target_outage_5s`, `target_outage_10s`, `target_degradation_10s`
- **Output Artifacts**:
  - `phase2_experiments/all_episodes_telemetry.csv` (Consolidated dataset)
  - `phase2_experiments/episodes_metadata.json` (Structured JSON metadata)
  - `phase2_experiments/episodes/episode_000_scen1.csv` through `episode_029_scen5.csv` (Per-episode traces)

---

## 4. Quality & Sanity Audit

1. **Physical Plausibility**: All SINR values lie within $[-25.0\text{ dB}, +32.0\text{ dB}]$, matching theoretical boundaries of thermal noise floor and maximum EIRP.
2. **Kinematic Smoothness**: Elevation angles, slant distances, and Doppler shifts evolve strictly according to orbital Keplerian dynamics.
3. **Absence of Synthetic Artifacts**: No duplicate records, no missing values (`NaN`), and no non-physical discontinuous jumps outside deliberate scenario transitions.

