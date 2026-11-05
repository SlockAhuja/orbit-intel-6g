# ORBIT-INTEL 6G: Interactive STLC 2026 Showcase Demonstration

**Conference:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Track:** Technical Project Demonstration & Exhibition  
**Framework:** Confidence-Aware Predictive Reliability Orchestration (CAPRO)  
**Target Environment:** Integrated 6G Space-Air-Ground Non-Terrestrial Networks (SAGIN)  
**Repository Branch:** `stlc_dashboard_first`  

---

## 1. Project Mission & Overview

ORBIT-INTEL 6G addresses the fundamental challenge of communication reliability in dynamic 6G Non-Terrestrial Networks (NTN). In integrated satellite-terrestrial topologies, user terminals face frequent line-of-sight dropouts due to rapid Low Earth Orbit (LEO) satellite motion, localized convective storm rain cells (ITU-R P.618), and multipath shadowing flutter.

Conventional reactive handovers (such as 3GPP A3/A4 events) only trigger after a link has already deteriorated below threshold, causing high packet loss and catastrophic ping-pong oscillations.

**ORBIT-INTEL 6G introduces CAPRO (Confidence-Aware Predictive Reliability Orchestration)**:
- **Dual-Uncertainty Link Forecasting:** Forecasts link SINR up to 10 seconds in advance, decomposing uncertainty into stochastic aleatoric flutter and epistemic model variance.
- **Reliability-Aware Hard Constraints:** Guarantees strict URLLC outage probability $P_{\text{outage}} \le 10^{-4}$ via conformal 5th percentile lower bounds ($\hat{q}_{05} \ge 3.0\text{ dB}$).
- **Proactive Orbital Handover:** Anticipates satellite horizon departure 12 seconds in advance, executing seamless make-before-break handovers with **0.0% packet loss**.
- **Transparent Explainability:** Produces human-readable natural language audit logs for every orchestration decision.

---

## 2. Interactive Showcase Dashboard Architecture

The project showcase is hosted via a high-performance Streamlit dashboard featuring 8 technical exhibition modules and dual-mode operational capability:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ORBIT-INTEL 6G SHOWCASE                         │
│   [ Mode A: Live Physical Simulation ]   [ Mode B: Benchmark Replay ]  │
├────────────────────────────────────────────────────────────────────────┤
│ Module 1: Main Overview & Executive Summary                            │
│ Module 2: Interactive 3D SAGIN Topology (Earth Globe & Constellation) │
│ Module 3: Satellite Telemetry & RF Tracking (Doppler ±48 kHz, FSPL)    │
│ Module 4: Predictive Intelligence & Calibrated Uncertainty Bounds      │
│ Module 5: CAPRO Intelligence Center & Explainable Decision Audit       │
│ Module 6: Satellite Handover Live Demonstration (Scenario 4 Replay)    │
│ Module 7: Rigorous Scientific Benchmarks (400 Monte Carlo Runs)        │
│ Module 8: Scenario Control Center & Live Stress Sandbox                │
└────────────────────────────────────────────────────────────────────────┘
```

### Dual Demonstration Modes
1. **Mode A (Live Physical Simulation):**
   - Directly executes the underlying 4-tier network simulator (`src/simulation_engine/`).
   - Evaluators can step time epoch-by-epoch, inject convective rain cells ($0\text{--}100\text{ mm/h}$) and multipath flutter ($0\text{--}6\text{ dB}$), and observe instant CAPRO vs. M1 Reactive baseline decisions.
2. **Mode B (Recorded Demonstration / Benchmark Replay):**
   - Ingests verified empirical campaign data across 400 Monte Carlo runs (`phase4_benchmarking/`) and 415 parameter sensitivity trials (`phase5_robustness/`).
   - Presents full statistical distributions, Cohen's d effect sizes, Wilcoxon signed-rank tests ($p < 10^{-15}$), and component ablation curves.

---

## 3. Quickstart & Demonstration Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Installed dependencies: `streamlit`, `plotly`, `pandas`, `numpy`, `scipy`, `joblib`, `pyyaml`

### Launching the Dashboard
Execute the following command from the workspace root:

```bash
streamlit run dashboard/app.py
```

The interactive dashboard will open automatically in your browser at:
`http://localhost:8501`

### Running the Verification Test Suite
```bash
pytest tests/test_dashboard_ui.py -v
```

---

## 4. Showcase Directory Structure

- `dashboard/app.py`: Full interactive Streamlit showcase application.
- `tests/test_dashboard_ui.py`: Automated regression tests for dashboard data loaders and simulation hooks.
- `STLC_SHOWCASE/DASHBOARD_IMPLEMENTATION_PLAN.md`: Technical design and reusability monograph.
- `STLC_SHOWCASE/DASHBOARD_USER_GUIDE.md`: Step-by-step evaluator instructions for all 8 modules.
- `STLC_SHOWCASE/DEMONSTRATION_SCRIPT.md`: 5-minute timed presentation script for conference judges.
- `STLC_SHOWCASE/API_DOCUMENTATION.md`: Technical architecture and data contract documentation.
- `STLC_SHOWCASE/DATA_SOURCE_MANIFEST.csv`: Traceability mapping connecting every UI metric to disk artifacts.
- `STLC_SHOWCASE/FEATURE_STATUS.md`: Comprehensive audit of all features.
- `STLC_SHOWCASE/TEST_REPORT.md`: Test execution results and verification summary.
