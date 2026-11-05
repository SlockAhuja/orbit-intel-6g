# ORBIT-INTEL 6G — QUICKSTART GUIDE

## 🚀 5-Minute Fast Track

### 1. Environment Setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Comprehensive Test Suite (39 Tests)
```powershell
pytest tests/test_channel_models.py tests/test_orbital.py tests/test_phase1_physical.py tests/test_phase2_prediction.py tests/test_capro_redesign.py tests/test_end_to_end_pipeline.py
```

### 3. Launch the Interactive Mission Control Center (Primary Showcase)
```powershell
python run_mission_control.py
```
Open your browser at `http://127.0.0.1:5000` for the full futuristic Aerospace 6G Network Operations Center:
- Photorealistic 3D Earth globe with orbital Keplerian tracks (Three.js)
- Space-Air-Ground Integrated Network (LEO satellites, HAPS, UAV, TBS, 12 UEs)
- Real-time telemetry, Doppler shift (±48 kHz), attitude, and communication parameters
- Satellite passes schedule, tactical ground imagery, and live mission pipeline status
- **"🚀 LAUNCH INTERACTIVE EXPERIMENT"** sandbox with real-time hazard injection and CAPRO decision explainability

*(Alternative Streamlit view also available: `streamlit run dashboard/app.py` on port 8501)*

### 4. Re-run Large-Scale Monte Carlo Benchmark (400 Runs)
```powershell
python src/experiments/comprehensive_benchmark.py
```

### 5. Compile Camera-Ready IEEE Paper
```powershell
cd final_publication
pdflatex -interaction=nonstopmode ORBIT_INTEL_6G_IEEE_PAPER.tex
bibtex ORBIT_INTEL_6G_IEEE_PAPER
pdflatex -interaction=nonstopmode ORBIT_INTEL_6G_IEEE_PAPER.tex
pdflatex -interaction=nonstopmode ORBIT_INTEL_6G_IEEE_PAPER.tex
cd ..
```
Compiled PDF is saved to `final_publication/ORBIT_INTEL_6G_FINAL.pdf`.

