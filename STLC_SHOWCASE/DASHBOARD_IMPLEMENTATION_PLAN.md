# ORBIT-INTEL 6G: STLC 2026 DASHBOARD-FIRST IMPLEMENTATION PLAN

**Target Event:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Track:** Interactive Project Showcase  
**Branch:** `stlc_dashboard_first`  
**System Architecture:** Confidence-Aware Predictive Reliability Orchestration (CAPRO) for 6G Space-Air-Ground Integrated Networks (SAGIN)  

---

## 1. Executive Summary & Objective

This document establishes the implementation blueprint for the **ORBIT-INTEL 6G Interactive Showcase Dashboard**. The purpose of this demonstration is to provide the IEEE ComSoc technical evaluation panel with an interactive, mathematically rigorous, and visually compelling experience demonstrating how predictive intelligence and calibrated uncertainty prevent catastrophic link failure in integrated non-terrestrial networks.

### Core Showcase Axioms:
1. **Dashboard-First Priority:** Pure focus on an interactive, operable software demonstration. No manuscript preparation, journal packages, or reviewer reports.
2. **Strict Scientific Traceability (Zero Fabrication):** Every metric, curve, probability, and decision in the dashboard originates either directly from live execution of the validated physical network simulator (`src/simulation_engine/`) and trained dual-uncertainty model (`models/capro_predictor.joblib`), or from verified empirical campaign artifacts (`phase4_benchmarking/` and `phase5_robustness/`).
3. **Dual-Mode Operational Architecture:**
   - **Mode A (Live Physical Simulation):** Interactive, user-driven execution with real-time parameter injection (rain rate, shadowing flutter, orbital velocity), step-by-step state progression, and instant CAPRO vs. baseline arbitration.
   - **Mode B (Recorded Demonstration / Benchmark Replay):** High-throughput playback of the 400 Monte Carlo campaign episodes and 415 parameter sweep trials, exposing full statistical distributions, hypothesis testing results, and ablation studies.

---

## 2. Reusability Analysis of Existing Codebase

| Component | Repository Path | Status | Reusability Plan |
|---|---|---|---|
| **Physical Network Simulator** | `src/simulation_engine/network_simulator.py` | Verified (Phase 1) | Reused directly in Mode A for real-time ECEF coordinates, slant range, elevation, Doppler shift ($\pm 48\text{ kHz}$), FSPL, and rain attenuation. |
| **Channel Models** | `src/channel_models/` | Verified (Phase 1) | Reused directly. Free-space path loss, atmospheric absorption, rain attenuation (ITU-R P.618), and log-normal shadowing flutter. |
| **Dual-Uncertainty Predictor** | `models/capro_predictor.joblib` | Trained & Calibrated (Phase 2) | Loaded via `st.cache_resource` for real-time prediction intervals $[\hat{q}_{05}, \hat{q}_{95}]$ and epistemic standard deviation $\sigma_{\text{RF}}$. |
| **Feature Engineer** | `src/prediction_engine/feature_engineering.py` | Verified (Phase 2) | Feeds time-lagged telemetry vectors into the dual-uncertainty predictor during live steps. |
| **CAPRO Orchestrator** | `src/orchestration_engine/capro_engine.py` | Formulated (Phase 3) | Generates unit-normalized utility evaluations $J \in [0, 1]$, enforces SLA constraints, and outputs `ExplainableDecision` objects. |
| **Baseline Algorithms (M1–M3)** | `src/baseline_methods/` | Implemented (Phase 4) | Enables real-time side-by-side comparison against Reactive (M1), Threshold (M2), and Prediction-Only (M3). |
| **Benchmark Datasets** | `phase4_benchmarking/*.csv` | 400 MC Episodes (Phase 4) | Ingested by Module 7 for statistical comparisons, ANOVA, Wilcoxon tests, and PDR/latency charts. |
| **Robustness Datasets** | `phase5_robustness/*.csv` | 415 Sensitivity Trials (Phase 5) | Ingested by Module 4 and 5 for prediction horizon trade-offs ($H \in \{1, 3, 5, 10\text{ s}\}$), hysteresis sweeps, and OOD stress testing. |

---

## 3. Showcase Module Architecture

The dashboard is structured into 8 cohesive exhibition modules, accessible through a persistent high-tech navigation sidebar:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ORBIT-INTEL 6G SHOWCASE                         │
│     [ Mode Toggle: ● Mode A (Live Physical Sim) | ○ Mode B (Replay) ]   │
├───────────────────┬────────────────────────────────────────────────────┤
│ SIDEBAR           │ WORKSPACE VIEWPORT                                 │
│ - Mode Selector   │                                                    │
│ - Module 1..8     │ Module 1: Executive Overview & Network KPIs        │
│ - Scenario Preset │ Module 2: 3D Interactive SAGIN Topology (Globe)    │
│ - Environmental   │ Module 3: Satellite Telemetry & Orbital Tracking   │
│   Injectors       │ Module 4: Predictive Intelligence & Uncertainty    │
│ - Live Controls   │ Module 5: CAPRO Intelligence Center & Audit Log    │
│   (Step, Reset)   │ Module 6: Satellite Handover Live Demonstration    │
│ - STLC Meta-Data  │ Module 7: Scientific Benchmark Comparison (M1-M4)  │
│                   │ Module 8: Interactive Scenario Control & Sandbox   │
└───────────────────┴────────────────────────────────────────────────────┘
```

### Module 1: Main Overview & Executive Summary
- **Purpose:** Immediate 10-second orientation for conference evaluators.
- **Components:**
  - 4 High-impact KPI metric cards (Active Constellation Nodes, Served Terminals, Outage Probability Guarantee, Handover Reduction).
  - Architecture breakdown across Space (LEO 600 km), Stratosphere (HAPS 20 km), Aerial (UAV 300 m), and Terrestrial (TBS 30 m) tiers.
  - Data provenance badge certifying live simulation execution and reproducible random seed control.

### Module 2: Interactive SAGIN Topology
- **Purpose:** High-fidelity 3D spatial representation of the integrated network.
- **Components:**
  - 3D Plotly ECEF visualization with realistic orbital altitudes and ground user terminal clusters (Urban, Suburban, Remote, Maritime).
  - Node selection dropdown / click interaction displaying dynamic telemetry cards (altitude, 3D velocity, carrier frequency, instantaneous load).
  - Color-coded RF beam lines representing active links and handover candidate paths.

### Module 3: Satellite & Network Monitoring
- **Purpose:** Deep-dive RF engineering and astrodynamics inspection.
- **Components:**
  - Time-series plots of elevation angle $\theta(t)$, slant distance $d(t)$, and Doppler frequency shift $f_D(t) \in [-48, +48]\text{ kHz}$.
  - Path loss decomposition chart (Free Space Path Loss + Atmospheric Absorption + Rain Attenuation + Fast Flutter).
  - Satellite line-of-sight status and remaining visibility time countdown $T_{\text{vis}}(t)$.

### Module 4: Predictive Intelligence Center
- **Purpose:** Demonstration of the dual-uncertainty prediction engine.
- **Components:**
  - Horizon selector $H \in \{1, 3, 5, 10\text{ s}\}$ showing real-time forecasting curves.
  - Actual simulated SINR vs. predicted median $\hat{y}$ with calibrated 90% prediction interval $[\hat{q}_{05}, \hat{q}_{95}]$.
  - Uncertainty decomposition bars: Aleatoric uncertainty (stochastic rain/fading) vs. Epistemic uncertainty (model lack-of-knowledge).
  - Early-warning degradation hazard banner triggered when $\hat{q}_{05} < 3.0\text{ dB}$.

### Module 5: CAPRO Intelligence Center
- **Purpose:** Interactive audit of the mathematical orchestration engine.
- **Components:**
  - Candidate node feasibility table evaluating hard constraints ($P_{\text{outage}} \le 10^{-4}$, delay $\le 10\text{ ms}$, visibility buffer $\ge 12\text{ s}$).
  - Multi-objective utility decomposition table ($U_{\text{link}}, U_{\text{lat}}, U_{\text{cap}}, C_{\text{ho}}, C_{\text{risk}}$).
  - Natural language explainability generator detailing the physical rationale behind every handover or serving node selection.

### Module 6: Interactive Satellite Handover Demonstration
- **Purpose:** Concrete live execution of Scenario 4 (Satellite-to-Satellite Handover).
- **Components:**
  - Dynamic trajectory tracker of SAT-01 setting below $10^\circ$ elevation and SAT-02 rising.
  - Live side-by-side comparison:
    - **M1 Reactive Baseline:** Waits until SAT-01 fully drops below horizon, causing connection loss and packet drops before seeking a new node.
    - **M4 CAPRO Proposed:** Detects $T_{\text{vis}} \le 12\text{ s}$, evaluates rising SAT-02, proactively executes make-before-break transition with 0.0% packet drop.

### Module 7: Rigorous Scientific Comparative Benchmarks
- **Purpose:** Conference evaluation panel review of the 400 Monte Carlo episodes.
- **Components:**
  - Bar charts and box plots comparing M1, M2, M3, and M4 across PDR (%), 95th-percentile tail latency (ms), outage rate, and handover frequency.
  - Interactive scenario filter (Scenarios 1 to 5).
  - Hypothesis testing table (Wilcoxon signed-rank and Mann-Whitney U test p-values showing $p < 10^{-15}$).
  - CAPRO component ablation visualization (V1 Full through V7 No Predictive).

### Module 8: Interactive Scenario Control & Sandbox
- **Purpose:** Live stress-testing sandbox for evaluators.
- **Components:**
  - Scenario preset loader (Scenarios 1 to 5).
  - Real-time environmental stress sliders: Rain rate ($0\text{ to }100\text{ mm/h}$) and fast fading flutter ($0\text{ to }6\text{ dB}$).
  - Live step controls: Step 1s, Step 5s, Auto-Play, and Reset.
  - Live terminal-by-terminal traffic inspector (URLLC vs. eMBB users).

---

## 4. UI/UX Design System Specification

- **Color Palette:**
  - Canvas Background: Dark Navy `#0a0e17`
  - Secondary Container: Slate Charcoal `#141b29`
  - Border Accents: Subdued Steel `#232f46`
  - Primary Accent (Space/LEO): Cyber Cyan `#00e5ff`
  - Success/Reliability Accent: Neon Green `#00e676`
  - HAPS Stratospheric Tier: Golden Amber `#ffd600`
  - UAV Aerial Tier: Safety Orange `#ff9100`
  - Warning/Degradation Accent: Amber Alert `#ffab00`
  - Critical/Outage Accent: High-Tech Crimson `#ff1744`
- **Typography:**
  - Monospace font for telemetry readings, coordinates, and latency numbers.
  - Clean sans-serif headers with clear hierarchical spacing.
- **Interaction Standards:**
  - Every button, dropdown, and slider must have an immediate visual feedback response.
  - Tooltips and context captions for all technical terms (Doppler shift, ECE, PICP, ECEF, SLA).

---

## 5. Verification & Testing Strategy

To guarantee flawless live execution during evaluator review:
1. `tests/test_dashboard_ui.py` will verify:
   - Successful loading of all benchmark CSVs and trained predictor models.
   - Simulation state stepping and telemetry generation across all 5 scenarios.
   - CAPRO decision generation without exceptions or null values.
   - Plotly chart generator functions returning valid figure objects.
2. Headless Streamlit smoke test to ensure clean startup without deprecation warnings or runtime crashes.

---

## 6. Implementation Deliverables

1. `dashboard/app.py`: Upgraded 8-module dual-mode interactive application.
2. `tests/test_dashboard_ui.py`: Automated test suite for dashboard data pipelines and rendering.
3. `STLC_SHOWCASE/README.md`: Showcase overview and architecture guide.
4. `STLC_SHOWCASE/DASHBOARD_USER_GUIDE.md`: Step-by-step evaluator instructions.
5. `STLC_SHOWCASE/DEMONSTRATION_SCRIPT.md`: 5-minute conference demonstration script.
6. `STLC_SHOWCASE/API_DOCUMENTATION.md`: Full architecture, data contracts, and simulation hooks.
7. `STLC_SHOWCASE/DATA_SOURCE_MANIFEST.csv`: Traceability mapping from UI components to disk artifacts.
8. `STLC_SHOWCASE/FEATURE_STATUS.md`: Comprehensive audit of all features.
9. `STLC_SHOWCASE/TEST_REPORT.md`: Automated test execution report.

