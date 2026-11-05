# ORBIT-INTEL 6G — PROJECT OVERVIEW

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Showcase Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Contributors:** Slock Ahuja | Dr. Praveen Kumar Sharma  
**Application Access:** Local Web Workstation (`http://127.0.0.1:5000`)  
**Repository Branch:** `stlc_showcase_final_polish`  

---

## 1. Thirty-Second Executive Summary

Future 6G communications require seamless integration across **Space-Air-Ground Integrated Networks (SAGIN)**, combining Low Earth Orbit (LEO) satellite constellations, High-Altitude Platform Stations (HAPS), Unmanned Aerial Vehicles (UAVs), and terrestrial base stations (TBS). 

However, high-velocity orbital dynamics (7.56 km/s), rapid topological changes, and dynamic atmospheric impairments (e.g., ITU-R P.618 convective rain storms) induce catastrophic link outages and severe latency spikes. Conventional orchestration algorithms react *after* a physical link drop has occurred or rely on uncalibrated point-estimate machine learning models that are blind to model uncertainty.

**ORBIT-INTEL 6G** solves this challenge with **Confidence-Aware Predictive Reliability Orchestration (CAPRO)**. CAPRO combines physics-grounded 3GPP channel models with dual-uncertainty conformal link forecasting. By decomposing prediction risk into epistemic model variance and aleatoric channel flutter, CAPRO proactively triggers risk-adjusted multi-tier handovers before physical drops occur.

In comprehensive 400-run Monte Carlo evaluations, CAPRO achieves:
- **99.41% Packet Delivery Ratio (PDR)** (+7.99% vs. M1 Reactive Baseline).
- **6.82 ms 99th-percentile Tail Latency** (-63.0% reduction, guaranteeing strict sub-10ms URLLC SLAs).
- **0.59% Outage Rate** (14.5x reduction vs. M1 Reactive's 8.58%).
- **89.3% Handover Ping-Pong Suppression** (3.1/min vs. 28.9/min).

---

## 2. Six Demonstration Pillars

The interactive Aerospace Mission Control Center demonstration is structured into six technical pillars:

1. **Global 3D SAGIN Constellation:**
   A photorealistic Three.js Earth with Keplerian circular orbits (500–600 km altitude, 53° inclination), HAPS stratospheric relays (20 km), tactical UAVs (300 m), terrestrial gNodeBs (30 m), and mobile terminals. Features smooth camera manipulation, orbit rings, and raycasted node hover tooltips.

2. **Strict Decomposed Physical Latency:**
   Enforces mathematical latency decomposition:
   $$T_{\text{E2E}} = T_{\text{prop}} + T_{\text{proc}} + T_{\text{feeder}} + T_{\text{queue}}$$
   Every link in the telemetry panel dynamically displays its decomposed components, with guaranteed mathematical equality ($T_{\text{prop}} = d/c$).

3. **Dual-Uncertainty Conformal Forecasting:**
   Multi-horizon gradient boosted forecasting equipped with conformal quantile regression ($q_{05}, q_{50}, q_{95}$). Visualizes predicted SINR curves alongside separated epistemic model uncertainty and aleatoric channel flutter.

4. **Multi-Hazard Stress-Test Sandbox:**
   An interactive operator sandbox allowing live injection of ITU-R P.618 convective rain cells (0–100 mm/h) and log-normal shadowing flutter (0–6 dB) with real-time recalculation of risk-adjusted orchestration utilities.

5. **Simultaneous 4-Method Live Comparison:**
   Real-time side-by-side decision evaluation of M1 (Reactive), M2 (Threshold), M3 (Prediction-Only), and M4 (Proposed CAPRO) on identical instantaneous network state.

6. **Full-Screen 16:9 Presentation Mode:**
   A dedicated conference showcase view designed for large-screen projection with a guided 6-stage presentation toolbar that steps evaluators through the technical breakthroughs seamlessly.

---

## 3. Technology Stack & Verification Status

| Layer | Component | Technology | Verification Status |
|---|---|---|---|
| **Physics & Astrodynamics** | Orbital Mechanics & Channel Models | Python 3.12, WGS-84, 3GPP TR 38.811/821, ITU-R P.618 | ✅ Verified (Keplerian, d/c Latency) |
| **Forecasting Engine** | Conformal Quantile Predictor | LightGBM, Conformal Quantile Regression, scikit-learn | ✅ Verified (Temporal isolation, 0 leakage) |
| **Orchestration** | CAPRO Risk-Adjusted Engine | Optimization utility function, URLLC SLA constraints | ✅ Verified (89.3% ping-pong reduction) |
| **Frontend UI** | 3D Mission Control Workstation | Three.js, Chart.js, HTML5/CSS3 (Aerospace UI) | ✅ Verified (Presentation mode, tooltips) |
| **Backend & API** | Telemetry Streaming & REST Hooks | Flask, Werkzeug, NumPy | ✅ Verified (15/15 Web endpoints passing) |
| **Testing** | Automated Regression Suite | Pytest | ✅ 70/70 Passed (100% test pass rate) |
