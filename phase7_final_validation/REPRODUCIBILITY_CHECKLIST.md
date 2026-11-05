# ORBIT-INTEL 6G — REPRODUCIBILITY CHECKLIST & REPLICATION GUIDE

## 1. Environment & Dependency Specifications

- **Operating System:** Microsoft Windows 11 (tested on 16 logical cores) / Linux (Ubuntu 22.04 LTS compatible)
- **Python Version:** 3.12.10
- **Primary Dependencies:**
  - `numpy >= 1.26.0`
  - `scipy >= 1.13.0`
  - `pandas >= 2.2.0`
  - `scikit-learn >= 1.4.0`
  - `joblib >= 1.4.0`
  - `pytest >= 8.0.0`
  - `streamlit >= 1.35.0`
  - `plotly >= 5.20.0`
  - `pyyaml >= 6.0.0`
- **LaTeX Compilation Toolchain:** MiKTeX / TeX Live (`pdflatex`, `bibtex`)

---

## 2. Step-by-Step Reproduction Instructions

### Step 1: Run Full Test Suite
Execute the 39 regression and end-to-end integration tests:
```powershell
pytest tests/test_channel_models.py tests/test_orbital.py tests/test_phase1_physical.py tests/test_phase2_prediction.py tests/test_capro_redesign.py tests/test_end_to_end_pipeline.py
```
*Expected Result:* 39 passed in ~65 seconds.

### Step 2: Reproduce 400-Run Monte Carlo Benchmark
Execute the large-scale benchmark campaign:
```powershell
python src/experiments/comprehensive_benchmark.py
```
*Output Artifacts:* Saved into `phase4_benchmarking/` (`RAW_BENCHMARK_RESULTS.csv`, `BENCHMARK_METRICS_BY_METHOD.csv`, `MONTE_CARLO_RUN_MANIFEST.csv`).

### Step 3: Reproduce Statistical Hypothesis Tests
Compute Paired $t$-tests, Wilcoxon signed-rank tests, Cohen's $d$, and 95% Confidence Intervals:
```powershell
python src/experiments/compute_statistical_tests.py
```
*Output Artifacts:* `phase4_benchmarking/STATISTICAL_TEST_RESULTS.csv`, `METHOD_CONFIDENCE_INTERVALS.csv`.

### Step 4: Reproduce Sensitivity & Horizon Sweeps
Execute the 415 parallel sensitivity episodes:
```powershell
python src/experiments/sensitivity_study.py
```
*Output Artifacts:* `phase5_robustness/PARAMETER_SWEEP_RESULTS.csv`, `ROBUSTNESS_METRICS.csv`.

### Step 5: Launch Interactive Demonstration Dashboard
Launch the Streamlit research dashboard:
```powershell
streamlit run dashboard/app.py
```

### Step 6: Compile IEEE Conference Manuscript
Compile the camera-ready research paper:
```powershell
cd final_publication
pdflatex -interaction=nonstopmode ORBIT_INTEL_6G_IEEE_PAPER.tex
bibtex ORBIT_INTEL_6G_IEEE_PAPER
pdflatex -interaction=nonstopmode ORBIT_INTEL_6G_IEEE_PAPER.tex
pdflatex -interaction=nonstopmode ORBIT_INTEL_6G_IEEE_PAPER.tex
cd ..
```
*Output Artifact:* `final_publication/ORBIT_INTEL_6G_FINAL.pdf`.

---

## 3. Seed Locking & Determinism Certification

All stochastic physical processes (Ricean shadow fading, ITU-R rain fluctuations, traffic packet generation) utilize explicit numpy random generators initialized with fixed seeds:
- Model Training: `random_seed = 42`
- Pre-flight Audit: `random_seed = 42`
- Monte Carlo Evaluation Runs: `seeds = [101, 102, ..., 120]` (20 paired seeds per scenario)
- Common Random Numbers (CRN) are strictly maintained across M1, M2, M3, and M4.

