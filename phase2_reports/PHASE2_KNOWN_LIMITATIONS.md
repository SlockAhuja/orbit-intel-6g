# PHASE 2 AUDIT: SCIENTIFIC & TECHNICAL KNOWN LIMITATIONS

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Target Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Document:** Statement of Known Limitations & Scope Boundaries  
**Date:** November 2026  

---

## 1. Executive Summary

In adherence to the strict scientific integrity requirements of the IEEE Communications Society, all known technical limitations, modeling approximations, and domain boundaries of the Phase 2 predictive intelligence reconstruction are explicitly cataloged below.

---

## 2. Inventory of Known Limitations

### 2.1 Discrete-Time 1-Second Sampling & Small-Scale Fast Fading Abstraction
- **Current Architecture:** Telemetry features and link snapshots are collected at a discrete resolution of $\Delta t = 1.0\text{ s}$.
- **Physical Reality:** In high-velocity NTN links ($v_{\text{sat}} \approx 7.56\text{ km/s}$, carrier frequency $f_c = 20\text{ GHz}$), the maximum Doppler shift exceeds $\pm 480\text{ kHz}$, resulting in a channel coherence time on the order of milliseconds ($T_c \approx 1\text{--}10\text{ ms}$).
- **Modeling Approximation:** The simulator abstracts small-scale Rayleigh/Rician multipath fading into effective sample-averaged shadowing flutter ($\sigma_{\text{flutter}}$). The predictive model forecasts macroscopic, link-budget-scale SINR trends rather than sub-millisecond fast fading phases. This abstraction is standard in resource management literature, but should be explicitly noted.

### 2.2 Quantile Ensemble Inference Complexity
- **Current Architecture:** Quantile prediction utilizes 9 independent Gradient Boosted Regression Trees (one per alpha quantile), paired with a 40-tree Random Forest for epistemic variance.
- **Complexity Assessment:** Evaluating a single user-node pair requires $\sim 0.5\text{--}1.2\text{ ms}$ on standard x86 CPU. In a local cell with 12 users and 6 candidate nodes (72 links), inference completes in under $50\text{ ms}$, comfortably fitting within a 1-second orchestration tick.
- **Scalability Boundary:** In a massive constellation with 10,000 active beams and hundreds of thousands of active devices, parallel GPU acceleration, model distillation into lightweight neural networks, or single-pass Multi-Layer Perceptron (MLP) quantile regressors would be required for real-time edge execution.

### 2.3 Discrete Horizon Discretization
- **Current Architecture:** Independent models are trained for discrete forecast horizons $H \in \{1\text{ s}, 3\text{ s}, 5\text{ s}, 10\text{ s}\}$.
- **Limitation:** Predictions for intermediate time offsets (e.g., $t + 4.2\text{ s}$) require linear interpolation between discrete model outputs. Continuous-time models such as Neural Ordinary Differential Equations (Neural ODEs) or continuous autoregressive transformers represent a promising future research direction.

### 2.4 Unmodeled Meteorological Sensor Ingestion
- **Current Architecture:** The prediction engine extracts features solely from RF telemetry (SINR history, elevation, Doppler shift) and basic node state.
- **Physical Reality:** Operational NTN ground stations often ingest external meteorological data feeds, such as dual-polarization weather radar, water vapor radiometers, and numerical weather prediction (NWP) forecasts.
- **Future Scope:** Directly injecting satellite-borne radiometer feeds into the feature matrix would further sharpen the 10-second convective storm fade prediction.

### 2.5 Distribution-Shift Exchangeability Bounds
- **Current Architecture:** Split-conformal calibration assumes exchangeability between validation and test distributions.
- **Limitation:** In the presence of compound, unprecedented climate anomalies (Shift D: rain $>110\text{ mm/h}$ with flutter $>6.0\text{ dB}$), empirical coverage drops from $93.2\%$ to $79.6\%$. While the model's epistemic uncertainty correctly surges ($+34.8\%$), alerting the network to out-of-distribution conditions, the nominal intervals require adaptive online conformal recalibration to restore target coverage under extreme drift.

---

## 3. Impact Assessment on Conference Presentation

None of the above limitations invalidate the research conclusions or the conference presentation for IEEE STLC Tunisia 2026. Explicitly acknowledging these scope boundaries strengthens the paper's scientific defensibility and provides reviewers with a clear roadmap for future 6G NTN research.
