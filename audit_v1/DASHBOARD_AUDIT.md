# ORBIT-INTEL 6G: Interactive Dashboard & Demonstration Audit

---

## 1. Dashboard Architecture and Execution Verification

The Streamlit exhibition dashboard is located at `dashboard/app.py`. It was audited by examining source code, running execution tests, and evaluating data linkages.

- **Execution Command**: `python -m streamlit run dashboard/app.py`.
- **Import & Syntax Verification**: Verified clean with zero fatal syntax errors.
- **Visual Design**: Professional dark-themed scientific interface with IEEE ComSoc header metadata, Plotly 3D/2D graphs, and interactive parameter controls.

---

## 2. Page-by-Page Audit Findings

### Page 1: Network Overview (SAGIN Topology)
- **Implemented Features**:
  - Interactive 3D Plotly Earth-centered layout showing LEO orbits, HAPS platforms, UAV relays, and terrestrial base stations.
  - Real-time node registry displaying altitudes, transmit power, gains, and energy levels.
- **Audit Finding**: **VERIFIED (Fully Functional)**.
  - Dynamically queries `NetworkSimulator` coordinates. Geometry is rendered accurately.

### Page 2: Predictive Intelligence
- **Implemented Features**:
  - User and node dropdown selectors.
  - 25-step lookahead trajectory showing true simulated SINR vs. AI predicted expected SINR.
  - 90% calibrated prediction interval ribbon ($\hat{q}_{0.05}$ to $\hat{q}_{0.95}$).
  - Live risk categorization badge (Low Risk, Moderate Risk, High Risk).
- **Audit Finding**: **VERIFIED (Active ML Inference)**.
  - The model `models/capro_predictor.joblib` actively generates predictions on live simulator features.

### Page 3: Intelligent Orchestration
- **Implemented Features**:
  - Pie chart showing multi-tier allocation breakdown across active users.
  - Constraint monitor status (URLLC latency $\le 10\text{ ms}$, outage margin, hysteresis).
  - Transparent Explainable Decision Audit Log table.
- **Audit Finding**: **PARTIALLY VERIFIED**.
  - Logic executes cleanly, but highlights the topological limitation: $>80\%$ of users are allocated to `TBS` and `HAPS`; `LEO` is almost never assigned.

### Page 4: Experimental Comparison
- **Implemented Features**:
  - Reads `results/metrics/benchmark_results_raw.csv` and `benchmark_summary_stats.csv`.
  - PDR bar chart across scenarios.
  - Outage probability bar chart.
  - Summary table displaying means and standard deviations across independent seeds.
- **Audit Finding**: **VERIFIED (True Data Linkage)**.
  - Directly connected to real benchmark CSV files without placeholder data.

### Page 5: Research Analysis
- **Implemented Features**:
  - Displays $R^2$, MAE, RMSE from `results/metrics/model_training_metrics.json`.
  - Uncertainty Calibration Reliability Curve.
  - Ablation Study on Risk Coefficient $\kappa$.
  - BibTeX citation generator.
- **CRITICAL AUDIT FLAW**:
  - In lines 268–285 of `dashboard/app.py`:
    ```python
    cal_fig.add_trace(go.Scatter(x=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95], y=[0.518, 0.612, 0.708, 0.809, 0.908, 0.952], ...))
    k_fig.add_trace(go.Scatter(x=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0], y=[83.2, 88.5, 94.2, 97.4, 96.8, 95.1, 93.4], ...))
    ```
  - Both the calibration diagram and the ablation sensitivity curve are **hard-coded static arrays**. They are not computed from actual test runs!
- **Audit Verdict**: **UNACCEPTABLE SCIENTIFIC SHORTCUT**.
  - Must be replaced with dynamic evaluations of test predictions and true parameter sweeps.

### Page 6: Live Interactive Demonstration
- **Implemented Features**:
  - Rain rate slider ($0\text{--}100\text{ mm/h}$).
  - Channel flutter noise slider ($0\text{--}6\text{ dB}$).
  - `Advance 1 Second` simulation clock button.
  - Side-by-side comparison between Proposed CAPRO and M1 Reactive Baseline.
- **Audit Finding**: **VERIFIED (Interactive Sandbox)**.
  - Modifies simulator attributes in real time and updates decisions dynamically.

