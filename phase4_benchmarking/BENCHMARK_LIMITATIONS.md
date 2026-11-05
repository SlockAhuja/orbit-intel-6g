# PHASE 4 AUDIT: BENCHMARK LIMITATIONS & EXPERIMENTAL THREATS TO VALIDITY

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Framework:** Confidence-Aware Predictive Reliability Orchestration (CAPRO)  
**Target Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Document:** Statement of Benchmarking Boundaries, Threats to Validity, and Scope Limitations  
**Date:** November 2026  

---

## 1. Executive Summary

In compliance with IEEE research reporting standards, all methodological boundaries, simulation simplifications, and threats to internal and external validity associated with the Phase 4 comparative benchmark are cataloged below.

---

## 2. Inventory of Threats to Validity

### 2.1 Simulation-Based Evaluation vs. Real-World NTN Testbeds
- **Nature of Evidence:** All results are generated from high-fidelity numerical simulation based on 3GPP TR 38.811 / TR 38.901 and ITU-R P.618 channel models.
- **Limitation:** The study does not incorporate live orbital hardware-in-the-loop (HIL) transceivers or actual satellite payload flight data.
- **Mitigation:** The physical simulator enforces speed-of-light propagation bounds, analytical Keplerian orbital ephemeris, vector line-of-sight Doppler shifts, and standard 3GPP control signaling mute windows. However, real-world deployment would involve additional hardware non-linearities (e.g., traveling-wave tube amplifier intermodulation distortion).

### 2.2 Discrete-Time 1-Second Scheduling Resolution
- **Nature of Evidence:** Orchestration decisions and channel telemetry are evaluated at $1.0\text{ s}$ intervals.
- **Limitation:** While macroscopic NTN resource allocation and beam switching typically occur on multi-second timescales, microscopic PHY-layer HARQ retransmissions operate on $1\text{ ms}$ subframe slots.
- **Modeling Assumption:** The simulation assumes that lower-layer fast link adaptation (MCS adaptation) operates autonomously within the $1\text{ s}$ window according to the local SINR margin.

### 2.3 Feeder Link Delay Parameterization
- **Nature of Evidence:** Feeder backhaul delay between LEO satellites and ground gateways is modeled as a standard $3.2\text{ ms}$ component.
- **Limitation:** In mega-constellations with inter-satellite optical links (ISLs), backhaul routing delay fluctuates depending on constellation topology and inter-plane laser link availability.

### 2.4 Baseline Method Optimality
- **Nature of Evidence:** Baselines M1 (Reactive), M2 (Threshold Predictive), and M3 (Prediction-Only AI) represent widely cited paradigms in literature.
- **Fairness Guarantee:** Baselines were provided identical simulation seeds, identical traffic arrivals, and identical channel fading traces. However, advanced proprietary vendor algorithms may implement heuristic multi-cell coordinate scheduling not captured by the standardized baselines.

---

## 3. Impact Assessment on Publication

These limitations represent standard scope boundaries in 6G Non-Terrestrial Network simulation research. Acknowledging them demonstrates mature academic rigor and provides clear directions for future hardware testbed extensions.
