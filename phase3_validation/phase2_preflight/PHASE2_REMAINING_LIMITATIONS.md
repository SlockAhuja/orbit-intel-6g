# PHASE 2 PRE-FLIGHT AUDIT: CATALOG OF REMAINING SCIENTIFIC LIMITATIONS

**Project:** ORBIT-INTEL 6G  
**Document:** Pre-Flight Assessment of Phase 2 Modeling & Statistical Boundaries  
**Date:** November 2026  
**Auditor:** Independent Scientific Audit Team  

---

## 1. Executive Summary

Prior to authorizing Phase 3 orchestration redesign and Phase 4 benchmarking, all remaining limitations, methodological approximations, and operational boundaries of the Phase 2 predictive engine are cataloged below.

---

## 2. Catalog of Audited Limitations

### 2.1 Limited Independent Trajectories in Locked Test Partition (Issue A)
- **Observation:** The locked test partition contains 6,153 link observations across 5 distinct continuous trajectory episodes (Episodes 5, 11, 17, 23, 29).
- **Limitation:** While 6,153 observations provide high sample density across elevation and distance, they originate from 5 distinct pseudo-random simulation seeds.
- **Required Action in Phase 4:** To establish broad statistical significance for CAPRO vs. baselines (M1–M3), benchmarking must execute **100 independent Monte Carlo seed iterations** across all operational environments, preventing seed-specific bias.

### 2.2 False-Positive Burden of Naive Lower-Bound Triggering (Issue B)
- **Observation:** The 5th percentile lower-bound detector ($\hat{q}_{05} < 3.0\text{ dB}$) achieves 100.0% recall on true outages, but produces **2,431 false alarms** (51.7% false alarm rate on non-outages).
- **Limitation:** If an orchestration algorithm uses $\hat{q}_{05} < 3.0\text{ dB}$ as an immediate, unconstrained binary handover trigger, it will initiate excessive, unnecessary handovers ("ping-pong" effect) on viable links experiencing minor transient dips.
- **Required Action in Phase 3:** CAPRO must **not** rely on raw binary quantile switching. Instead, it must integrate prediction intervals into a **normalized multi-objective utility function** governed by:
  1. Service-specific reliability constraints (e.g. URLLC vs eMBB).
  2. Handover switching costs and hysteresis margins ($H_{\text{hyst}} \ge 2.0\text{ dB}$).
  3. Minimum dwell-time timers to prevent ping-pong reassociation.

### 2.3 Wide Aggregate Interval Bounds for LEO Tier (Issue C)
- **Observation:** The 90% prediction interval width for LEO satellites averages $26.20\text{ dB}$, compared to $10.74\text{ dB}$ for HAPS.
- **Limitation:** At $H=10\text{ s}$, high orbital velocity ($7.56\text{ km/s}$) and rapid elevation mask approach create large physical dynamic swings. The lower bound $\hat{q}_{05}$ can dip substantially even when instantaneous link quality is acceptable.
- **Required Action in Phase 3:** Orchestration logic must evaluate remaining satellite visibility duration ($T_{\text{vis}}$) alongside $\hat{q}_{05}$, avoiding premature handovers when visibility margin exceeds the proactive handover buffer ($T_{\text{vis}} > 15\text{ s}$).

### 2.4 Extrapolation Boundaries of Random Forest Epistemic Uncertainty (Issue D)
- **Observation:** Random Forest tree disagreement provides a useful local anomaly detector within realistic variations (elevating $\sigma_{\text{epi}}$ by $+26.1\%$ to $+34.8\%$ under severe flutter and compound storm conditions).
- **Limitation:** Because axis-aligned decision trees predict constant leaf values outside the convex hull of training features, tree variance cannot extrapolate reliably to arbitrary, unbounded extremes.
- **Scientific Caveat:** The final publication must characterize tree variance as an **empirical channel volatility and local anomaly metric**, rather than an asymptotically guaranteed out-of-distribution detector.

### 2.5 Regression ECE Granularity (Issue E)
- **Observation:** The reported Expected Calibration Error ($\text{ECE} = 0.0277$) is calculated across 10 decile width bins around the nominal 90% confidence target.
- **Limitation:** While valid and informative, decile binning smooths intra-bin coverage variations.
- **Required Action:** Both tabular multi-level calibration (50%, 80%, 90%, 95%) and binned decile reliability curves must be reported side-by-side in the final manuscript.

