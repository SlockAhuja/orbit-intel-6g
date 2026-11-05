# ORBIT-INTEL 6G — QUICKSTART GUIDE

**Project:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Contributors:** Slock Ahuja | Dr. Praveen Kumar Sharma  
**Target:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Current Branch:** `stlc_showcase_final_polish`  

---

## 🚀 5-Minute Fast Track

### 1. Environment Setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Comprehensive Full Regression Test Suite (70/70 Passing)
```powershell
pytest -v
```
All 70 automated tests pass with 100% success rate, validating Keplerian orbital mechanics, ITU-R P.618 rain fading, conformal quantile prediction, strict latency summation identity, and REST API endpoints.

### 3. Launch the Interactive Mission Control Center (STLC Showcase)
```powershell
python run_mission_control.py
```
Open your browser at **`http://127.0.0.1:5000`** to experience the Aerospace 6G Mission Control Workstation:
- **3D Earth Viewport (Three.js):** Real-time Keplerian orbits, active beam rays, and raycasted node hover tooltips.
- **Decomposed Physical Latency:** Strict mathematical summation $T_{\text{E2E}} = T_{\text{prop}} + T_{\text{proc}} + T_{\text{feeder}} + T_{\text{queue}}$ with $0.00\text{ ms}$ discrepancy.
- **`[🖥️ PRESENTATION MODE]`:** Dedicated 16:9 fullscreen display mode with a 6-step guided demo controller for large-screen conference presentations.
- **`[📊 BENCHMARKS]`:** Side-by-side 4-Method Benchmark Comparison Modal (M1 Reactive, M2 Threshold, M3 Prediction-Only, M4 CAPRO) backed by 400 Monte Carlo runs.
- **`[🚀 LAUNCH EXPERIMENT]`:** Interactive Multi-Hazard Sandbox allowing live injection of rain storms (0–100 mm/h) and shadowing flutter (0–6 dB) with real-time conformal curve re-rendering.
- **`[ℹ️ ABOUT & TEAM]`:** Comprehensive project background, architecture summary, and official contributor attribution.

*(Alternative secondary Streamlit dashboard is also available: `streamlit run dashboard/app.py` on port 8501)*

### 4. Re-run Large-Scale Monte Carlo Benchmark (400 Runs)
```powershell
python src/experiments/comprehensive_benchmark.py
```
Outputs are written to `phase4_benchmarking/RAW_BENCHMARK_RESULTS.csv` and `BENCHMARK_METRICS_BY_METHOD.csv`.
