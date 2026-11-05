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

### 3. Launch the Interactive Exhibition Dashboard
```powershell
streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501` to explore:
- 3D SAGIN Constellation & Orbit Viewer
- Multi-Horizon Predictive Uncertainty Decomposition
- CAPRO Transparent Decision Audit Log
- Monte Carlo Comparative Benchmarks (M1–M4)
- Live Interactive Stress Sandbox

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
