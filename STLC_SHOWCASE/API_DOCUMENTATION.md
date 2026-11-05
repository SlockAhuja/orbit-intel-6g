# ORBIT-INTEL 6G: ARCHITECTURE & API DOCUMENTATION

**Branch:** `stlc_dashboard_first`  
**System:** Interactive 6G SAGIN Showcase Architecture  
**Target:** IEEE ComSoc Technical Demonstrations & Scientific Evaluation  

---

## 1. System Architecture Overview

ORBIT-INTEL 6G is architectured as a multi-tier pipeline separating physical kinematics, channel propagation, predictive intelligence, reliability-aware orchestration, and reactive presentation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER (UI)                          │
│               Streamlit Dashboard (`dashboard/app.py`)                 │
│         [ Modules 1 - 8 ] ── [ Dual-Mode Operational Engine ]         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┼───────────────────────────┐
       ▼                            ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│ EMPIRICAL     │           │ PREDICTIVE    │           │ PHYSICAL      │
│ DATA LOADERS  │           │ INFERENCE     │           │ SIMULATOR     │
│ phase4/ csvs  │           │ DualUncertainty│           │ NetworkSim    │
│ phase5/ csvs  │           │ FeatureEng    │           │ Orbital/Kepler│
└───────────────┘           └───────┬───────┘           └───────┬───────┘
                                    │                           │
                                    └─────────────┬─────────────┘
                                                  ▼
                                    ┌───────────────────────────┐
                                    │ ORCHESTRATION ENGINE      │
                                    │ CAPROOrchestrator         │
                                    │ M1-M3 Baselines           │
                                    └───────────────────────────┘
```

---

## 2. Core Python Classes & Interfaces

### 2.1 Physical Network Simulator
- **Module:** `src.simulation_engine.network_simulator.NetworkSimulator`
- **Constructor:** `NetworkSimulator(random_seed=42)`
- **Key Methods:**
  - `sim.step() -> dict`: Advances discrete simulation clock by $\Delta t = 1.0\text{ s}$. Updates orbital Keplerian state, user positions, path loss, and returns telemetry dictionary with key `"links"`.
  - `sim.reset(random_seed=42)`: Resets constellation and mobile terminals to deterministic initial state.
  - `sim.compute_link_telemetry(user_id: str, node_id: str) -> dict`: Returns instant link metrics:
    - `elevation_deg`: Topocentric elevation angle ($\ge 10^\circ$ for line-of-sight).
    - `slant_distance_m`: Geometric 3D vector length between UE and node.
    - `doppler_shift_hz`: Relative radial velocity Doppler shift ($f_D \in [-48, +48]\text{ kHz}$).
    - `sinr_db`: Instantaneous Signal-to-Interference-plus-Noise Ratio.
    - `remaining_visibility_s`: Countdown until topocentric setting below horizon.
    - `path_loss_db`: Total attenuation (FSPL + atmospheric + rain + flutter).

### 2.2 Dual-Uncertainty Link Predictor
- **Module:** `src.prediction_engine.models.DualUncertaintyPredictor`
- **Model Storage:** `models/capro_predictor.joblib`
- **Key Methods:**
  - `DualUncertaintyPredictor.load(path: str)`: Loads serialized multi-horizon predictor and conformal calibrator.
  - `predictor.predict_with_uncertainty(X: np.ndarray) -> dict`:
    - `y_pred`: Median link quality forecast ($\hat{q}_{50}$).
    - `q_lower`: Conformal 5th percentile lower bound ($\hat{q}_{05}$).
    - `q_upper`: Conformal 95th percentile upper bound ($\hat{q}_{95}$).
    - `epistemic_std`: Ensemble tree variance ($\sigma_{\text{RF}}$).
    - `aleatoric_width`: Interval width ($\hat{q}_{95} - \hat{q}_{05}$).
    - `total_uncertainty`: Composite uncertainty metric $U = \text{aleatoric} + \kappa \cdot \text{epistemic}$.

### 2.3 Feature Engineer
- **Module:** `src.prediction_engine.feature_engineering.FeatureEngineer`
- **Key Methods:**
  - `FeatureEngineer.extract_features_from_history(history: list[dict], user_id: str, node_id: str) -> dict`: Computes rolling statistics (mean, trend, Doppler slope, remaining visibility).
  - `FeatureEngineer.to_feature_vector(feat_dict: dict) -> np.ndarray`: Converts feature dictionary into normalized 1D vector matching trained model schema.

### 2.4 CAPRO Orchestrator
- **Module:** `src.orchestration_engine.capro_engine.CAPROOrchestrator`
- **Constructor:** `CAPROOrchestrator(risk_aversion_kappa=1.5, hysteresis_margin_db=2.5)`
- **Key Method:**
  ```python
  def select_network_node(
      self,
      user_id: str,
      current_serving_id: Optional[str],
      available_links: dict[str, dict],
      predictions: dict[str, dict],
      user_service_type: str = "URLLC"
  ) -> ExplainableDecision
  ```
- **Return Type:** `ExplainableDecision` dataclass:
  - `selected_node_id`: Target network node assigned to terminal.
  - `previous_node_id`: Previously serving node ID.
  - `tier`: Access tier (`"LEO"`, `"HAPS"`, `"UAV"`, `"TBS"`).
  - `is_handover`: Boolean flag indicating whether handover was initiated.
  - `trigger_code`: Formal reason code (e.g. `PROACTIVE_DEPARTURE_HANDOVER`, `OPTIMAL_SERVING_SELECTION`).
  - `predicted_sinr_db`: Expected future SINR.
  - `q_lower_bound_db`: Conformal lower bound ($\hat{q}_{05}$).
  - `risk_adjusted_utility_db`: Unit-normalized objective score $J \in [0, 1]$.
  - `explanation`: Human-readable audit text explaining assignment.

---

## 3. Data Contracts & Empirical CSV Schemas

### 3.1 Benchmark Metrics by Method (`phase4_benchmarking/BENCHMARK_METRICS_BY_METHOD.csv`)
- Ingested by **Module 1** and **Module 7**.
- Core columns: `method`, `pdr_percent_mean`, `pdr_percent_std`, `mean_latency_ms_mean`, `p95_latency_ms_mean`, `outage_prob_mean`, `sla_violation_urllc_percent_mean`, `handover_frequency_per_min_mean`.

### 3.2 Benchmark Metrics by Scenario (`phase4_benchmarking/BENCHMARK_METRICS_BY_SCENARIO.csv`)
- Ingested by **Module 7**.
- Core columns: `scenario_id`, `scenario_name`, `method`, `pdr_percent_mean`, `mean_latency_ms_mean`, `outage_prob_mean`, `handover_frequency_per_min_mean`.

### 3.3 CAPRO Component Ablation (`phase4_benchmarking/CAPRO_ABLATION_RESULTS.csv`)
- Ingested by **Module 7**.
- Core columns: `variant_tag`, `ablation_mode`, `pdr_percent_mean`, `handover_count_mean`, `sla_violation_urllc_percent_mean`.

### 3.4 Robustness & Sweep Metrics (`phase5_robustness/ROBUSTNESS_METRICS.csv`)
- Ingested by **Module 4**.
- Core columns: `experiment_tag`, `experiment_param`, `pdr_percent_mean`, `mean_latency_ms_mean`, `handover_count_mean`, `outage_probability_mean`.
