# ORBIT-INTEL 6G: STLC SHOWCASE VERIFICATION & TEST REPORT

**Target Conference:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Branch:** `stlc_dashboard_first`  
**Test Framework:** Pytest 9.1.1, Python 3.12.10 (win32)  
**Execution Timestamp:** November 2026  

---

## 1. Test Suite Summary

The verification campaign covers both unit-level component tests and end-to-end integration workflows across the physical simulator, prediction pipeline, CAPRO orchestration engine, baseline algorithms, and dashboard UI data pipelines.

| Test Module | Test Focus | Tests Run | Passed | Failed |
|---|---|---|---|---|
| `tests/test_dashboard_ui.py` | Dashboard Data Loaders, Inference & Scenarios | 9 | 9 | 0 |
| `tests/test_capro_redesign.py` | CAPRO Mathematical Formulation & Constraints | 8 | 8 | 0 |
| `tests/test_channel_models.py` | FSPL, Rain Attenuation & Doppler Physics | 4 | 4 | 0 |
| `tests/test_end_to_end_pipeline.py` | Full Pipeline Execution Across Scenarios | 5 | 5 | 0 |
| `tests/test_orbital.py` | Keplerian Orbit Kinematics & ECEF Transformations | 4 | 4 | 0 |
| `tests/test_orchestration.py` | Proactive Satellite Descent & Penalty Avoidance | 3 | 3 | 0 |
| `tests/test_phase1_physical.py` | Physical Disaggregated Propagation & Handover | 9 | 9 | 0 |
| `tests/test_phase2_prediction.py` | Prediction Calibration, Zero Temporal Leakage | 7 | 7 | 0 |
| `tests/test_prediction_engine.py` | Feature Vectors, Calibration & Monotonicity | 5 | 5 | 0 |
| `tests/test_reproducibility.py` | Deterministic Seed Reproducibility | 1 | 1 | 0 |
| **TOTAL** | **Full System Verification** | **55** | **55** | **0** |

---

## 2. Dashboard UI Specific Test Cases (`tests/test_dashboard_ui.py`)

1. `test_load_predictor_model`: Confirms `models/capro_predictor.joblib` loads into memory and exposes `predict_with_uncertainty` method.
2. `test_load_benchmark_datasets`: Validates loading of `RAW_BENCHMARK_RESULTS.csv`, `BENCHMARK_METRICS_BY_METHOD.csv`, `BENCHMARK_METRICS_BY_SCENARIO.csv`, `CAPRO_ABLATION_RESULTS.csv`, and `STATISTICAL_TEST_RESULTS.csv`.
3. `test_load_robustness_datasets`: Confirms `PARAMETER_SWEEP_RESULTS.csv` and `ROBUSTNESS_METRICS.csv` load properly with `Horizon_Sweep` parameter tags.
4. `test_simulation_step_and_telemetry`: Verifies 4-tier network stepping and generation of elevation, slant distance, Doppler shift, and remaining visibility.
5. `test_feature_extraction_and_prediction`: Validates rolling feature extraction from simulator telemetry and quantile ordering ($\hat{q}_{05} \le \hat{y} \le \hat{q}_{95}$).
6. `test_capro_orchestration_decision`: Confirms CAPRO outputs valid `ExplainableDecision` with unit-normalized utility $J \in [0, 1]$ and non-empty explanation text.
7. `test_m1_reactive_baseline_decision`: Verifies M1 Reactive baseline outputs valid decisions.
8. `test_scenario_4_orbital_handover_initialization`: Validates Scenario 4 topocentric initial conditions (SAT-01 setting at $11.6^\circ$, SAT-02 rising at $9.4^\circ$).
9. `test_scenario_stepping_and_environmental_injection`: Verifies dynamic injection of rain rate ($50\text{ mm/h}$) and fast shadowing flutter ($3\text{ dB}$).

---

## 3. Headless Streamlit Smoke Verification

`dashboard/app.py` was compiled and syntax-checked:
- `python -m py_compile dashboard/app.py`: Clean execution with exit code 0.
- All LaTeX escape sequences formatted with raw strings (`r"""`) to avoid syntax warnings.
- Plotly templates configured with `plotly_dark` for unified styling.

---

## 4. Certification

The ORBIT-INTEL 6G Interactive Showcase Dashboard is **verified, stable, fully functional, and ready for evaluation** at the IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026.
