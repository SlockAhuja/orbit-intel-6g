# ORBIT-INTEL 6G: 5-MINUTE STLC DEMONSTRATION SCRIPT

**Event:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Session:** Interactive Project Showcase / Technical Jury Review  
**Presenter Team:** Slock Ahuja, Praveen Kumar Sharma, Sudarshan Sanap  
**System:** ORBIT-INTEL 6G Dashboard (`dashboard/app.py`)  

---

## Timeline Overview

| Timestamp | Duration | Section | Primary UI Screen |
|---|---|---|---|
| **0:00 – 0:45** | 45 sec | 1. Introduction & The NTN Reliability Problem | Module 1: Main Overview & KPIs |
| **0:45 – 1:30** | 45 sec | 2. 4-Tier Heterogeneous SAGIN Constellation | Module 2: Interactive 3D Topology |
| **1:30 – 2:30** | 60 sec | 3. Dual-Uncertainty Prediction & Outage Hazard Alert | Module 4: Predictive Intelligence |
| **2:30 – 3:30** | 60 sec | 4. CAPRO Orchestration & Transparent Explainability | Module 5: CAPRO Intelligence Center |
| **3:30 – 4:30** | 60 sec | 5. Live Orbital Handover Breakthrough (Scenario 4) | Module 6: Satellite Handover Live Demo |
| **4:30 – 5:00** | 30 sec | 6. Empirical Validation & Conclusion | Module 7: Scientific Benchmarks |

---

## Detailed Step-by-Step Script

### Minute 0:00 – 0:45: Introduction & The NTN Reliability Challenge
- **UI Action:** Open dashboard landing screen (`Module 1: Main Overview & KPIs`).
- **Spoken Narration:**
  > "Distinguished IEEE ComSoc evaluators, welcome to ORBIT-INTEL 6G. Non-terrestrial networks are central to the 6G vision of ubiquitous coverage. However, integrating Low Earth Orbit satellites, stratospheric HAPS, aerial UAVs, and terrestrial base stations introduces extreme link instability. 
  > 
  > Rapid satellite orbital velocities of 7.5 km/s create severe Doppler shifts, while sudden convective rain cells cause up to 18 dB attenuation in seconds. Conventional reactive handover methods only respond after a link breaks, causing high packet drop rates and endless ping-pong handovers. 
  > 
  > In this demonstration, we present CAPRO: Confidence-Aware Predictive Reliability Orchestration, which combines calibrated dual-uncertainty link forecasting with proactive, reliability-constrained optimization."
- **Visual Highlight:** Point to the top metric cards showing the 4-tier constellation and the **92.4% reduction in ping-pong handovers**.

---

### Minute 0:45 – 1:30: 4-Tier Heterogeneous SAGIN Constellation
- **UI Action:** Navigate to `Module 2: 3D SAGIN Topology`. Rotate the 3D globe using mouse controls.
- **Spoken Narration:**
  > "Here in Module 2 is our 3D geometric network topology, mapped in Earth-Centered Earth-Fixed coordinates. 
  > 
  > Notice the four distinct tiers:
  > - Two LEO satellites orbiting at 600 km altitude in cyber cyan.
  > - A stratospheric HAPS platform at 20 km altitude in yellow, acting as a regional relay.
  > - A tactical UAV at 300 m in orange.
  > - And terrestrial base stations in green serving ground terminals across urban, suburban, remote, and maritime environments.
  > 
  > If we select node `SAT-01`, we immediately see real-time physical telemetry: an orbital speed of 7.56 km/s, 30 MHz bandwidth, and precise ECEF velocity vectors."
- **Visual Highlight:** Click `SAT-01` to display the telemetry card.

---

### Minute 1:30 – 2:30: Dual-Uncertainty Prediction & Outage Hazard Alert
- **UI Action:** Navigate to `Module 4: Predictive Intelligence Center`.
- **Spoken Narration:**
  > "The brain of ORBIT-INTEL 6G is our Dual-Uncertainty Link Predictor. Rather than predicting just a point estimate, our engine predicts calibrated quantiles: the 5th, 50th, and 95th percentiles.
  > 
  > The shaded blue band represents the 90% Calibrated Prediction Interval. Notice how it decomposes uncertainty into two physical sources:
  > 1. Aleatoric uncertainty from real stochastic rain flutter.
  > 2. Epistemic uncertainty representing model lack-of-knowledge.
  > 
  > Look at the red warning banner: our model detects that the lower bound q_05 drops below the 3.0 dB threshold seconds before the physical link actually collapses. This allows the orchestrator to trigger proactive handovers before any packet is lost."
- **Visual Highlight:** Toggle the Lookahead Horizon from 1s to 5s to show the widening uncertainty interval and the active Hazard Alert Banner.

---

### Minute 2:30 – 3:30: CAPRO Orchestration & Explainable Decisions
- **UI Action:** Navigate to `Module 5: CAPRO Intelligence Center`.
- **Spoken Narration:**
  > "In Module 5, we see how CAPRO uses these predictions to make optimal routing decisions.
  > 
  > Unlike black-box neural networks, CAPRO enforces strict, auditable constraints:
  > First, a hard outage constraint: the 5th percentile lower bound must exceed 3.0 dB.
  > Second, URLLC traffic is strictly bounded to latency under 10 ms.
  > And third, orbital nodes must have at least 12 seconds of remaining line-of-sight visibility.
  > 
  > In the candidate feasibility table, candidates failing these constraints are immediately marked infeasible. Below, our explainability generator details the exact mathematical rationale for every assignment."
- **Visual Highlight:** Point to the Decision Audit Card showing the transparent natural language explanation.

---

### Minute 3:30 – 4:30: Live Orbital Handover Breakthrough (Scenario 4)
- **UI Action:** Navigate to `Module 6: Satellite Handover Live Demonstration`.
- **Spoken Narration:**
  > "Now, let us examine the core breakthrough of CAPRO in Module 6: a head-to-head live replay of Scenario 4.
  > 
  > SAT-01 is setting over the horizon, while SAT-02 is rising.
  > 
  > Watch what happens as we drag the time epoch slider to t = 23 seconds:
  > CAPRO observes that SAT-01 remaining visibility has reached the 12-second margin. It proactively transfers the user terminal to rising SAT-02. The packet loss remains strictly at 0.0%.
  > 
  > Now observe the conventional M1 Reactive baseline on the right: it stays attached to SAT-01 all the way until t = 35 seconds, when SAT-01 plunges below 10 degrees. The link drops, packets are lost, and the baseline scrambles to recover."
- **Visual Highlight:** Drag the slider from $t=20$ to $t=36\text{ s}$ showing the green 0% loss for CAPRO vs. the red 100% loss outage for M1.

---

### Minute 4:30 – 5:00: Empirical Validation & Conclusion
- **UI Action:** Navigate to `Module 7: Rigorous Scientific Benchmarks`.
- **Spoken Narration:**
  > "Finally, our claims are backed by an extensive empirical campaign of 400 Monte Carlo runs and 415 parameter sweep trials.
  > 
  > Across all scenarios, CAPRO achieves superior reliability while reducing handover frequency by over 92% compared to reactive baselines. Formal Wilcoxon signed-rank tests confirm statistical significance with p-values below 10^-15.
  > 
  > Evaluators can also use Module 8 to inject real-time rain cells and test the system live. Thank you, and we welcome your questions."
- **Visual Highlight:** Quick switch between the PDR and Handover Reduction tabs in Module 7.
