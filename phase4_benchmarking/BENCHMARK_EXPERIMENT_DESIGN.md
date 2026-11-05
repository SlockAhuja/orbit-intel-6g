# PHASE 4 BENCHMARK EXPERIMENT DESIGN: LARGE-SCALE MONTE CARLO CAMPAIGN

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Framework:** Confidence-Aware Predictive Reliability Orchestration (CAPRO)  
**Target Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Document:** Experimental Methodology, Monte Carlo Framework, and Metric Formulations  
**Date:** November 2026  

---

## 1. Executive Summary

To provide rigorous, publication-grade comparative evidence for the IEEE Communications Society STLC 2026, a comprehensive Monte Carlo benchmarking campaign was established.

The experiment evaluates four distinct network orchestration paradigms across all five operational scenarios defined in the research framework:
1. **M1 — Reactive Baseline:** Conventional instantaneous-SINR resource allocation with reactive handover gating.
2. **M2 — Threshold Predictive Baseline:** Linear trend extrapolation ($Q_{\text{pred}} = Q_{\text{curr}} + \dot{Q} \cdot H$) with fixed threshold triggering ($10.0\text{ dB}$).
3. **M3 — Prediction-Only AI:** Machine-learning point forecasting (median expectation $\hat{q}_{50}$) without uncertainty awareness or latency filtering.
4. **M4 — Full CAPRO (Proposed):** Reliability-constrained, unit-normalized multi-objective utility optimization with calibrated prediction intervals, epistemic risk cost, and hysteresis gating.

---

## 2. Monte Carlo Paired-Seed Design

To guarantee absolute fairness and eliminate simulation seed bias, the campaign employs the **Common Random Numbers (CRN)** variance reduction technique:
- Every scenario and seed combination is executed identically across all four methods.
- The user mobility trajectories, atmospheric rain events, shadowing flutter, and packet arrivals are identical across M1, M2, M3, and M4 for any given $(S_i, \text{seed}_k)$ pair.
- **Sample Size:** 20 independent pseudo-random seeds per scenario across 5 scenarios = **100 independent simulation runs per method** (**400 total simulation episodes**).
- **Observation Density:** With 12 users evaluated at 1-second resolution over 60 seconds, the 400 episodes yield **288,000 second-level link allocation decisions** and **2,880,000 packet delivery evaluations**.

---

## 3. Evaluated Operational Scenarios

| Scenario ID | Scenario Name | Primary Physical Stressor | Evaluation Objective |
| :---: | :--- | :--- | :--- |
| **Scenario 1** | Normal Conditions | Clear sky, nominal multi-tier propagation | Measures baseline throughput, latency, and resource efficiency under calm channel regimes. |
| **Scenario 2** | Congestion Surge | Heavy traffic surge ($50\text{--}80\text{ Mbps}$) at $t \ge 20\text{ s}$ | Stresses node queuing capacity; tests load balancing and capacity allocation. |
| **Scenario 3** | Sudden Rain Degradation | Localized convective cloudburst ($40\text{--}70\text{ mm/h}$) | Evaluates proactive fade evasion before link collapse. |
| **Scenario 4** | Satellite Visibility Handover | `SAT-01` sets below $10^\circ$; `SAT-02` rises | Tests orbital departure prediction and seamless inter-satellite beam handover. |
| **Scenario 5** | High Uncertainty Flutter | Fast log-normal multipath flutter ($\sigma = 2.5\text{--}4.5\text{ dB}$) | Evaluates epistemic uncertainty penalization and ping-pong handover suppression. |

---

## 4. Formal Metric Definitions

### 4.1 Reliability Metrics
1. **Packet Delivery Ratio (PDR, %):**
   $$\text{PDR} = \frac{N_{\text{delivered}}}{N_{\text{offered}}} \times 100\%$$
   where packet delivery requires both physical demodulation success ($\text{SINR} \ge \gamma_{\text{threshold}}$ and BLER pass) and delay deadline compliance ($T_{\text{e2e}} \le L_{\text{max}}$).
2. **Packet Loss Rate (%):** $\text{PLR} = 100.0 - \text{PDR}$.
3. **Outage Probability ($P_{\text{out}}$):**
   $$P_{\text{out}} = \frac{1}{T \cdot |\mathcal{U}|} \sum_{t=1}^T \sum_{u \in \mathcal{U}} \mathbb{I}\left( \text{Link Unavailable or } \text{SINR}_u(t) < 3.0\text{ dB} \right)$$
4. **SLA Violation Rate (%):**
   $$\text{SLA}_{\text{viol}} = \frac{N_{\text{packets violating deadline or dropped}}}{N_{\text{offered}}} \times 100\%$$
   Disaggregated separately for URLLC ($L_{\text{max}} = 10.0\text{ ms}$) and eMBB ($L_{\text{max}} = 50.0\text{ ms}$).

### 4.2 Latency Metrics
- **Mean & Median Latency:** $L_{\text{mean}} = \frac{1}{N}\sum L_i$, $L_{\text{median}} = \text{median}(L_i)$.
- **95th & 99th Percentile Tail Latency ($L_{95}, L_{99}$):** Critical for 3GPP URLLC compliance.

### 4.3 Mobility & Handover Metrics
- **Handover Frequency ($f_{\text{HO}}$):** Number of executed handovers per minute.
- **Handover Failure Rate (%):** Percentage of handover attempts blocked by destination cell congestion.
- **Execution Packet Loss:** Number of packets dropped during the $50\text{ ms}$ control plane mute window.

### 4.4 Resource & Energy Efficiency
- **Throughput (Mbps):** Total successfully delivered payload data volume per second.
- **Jain's Fairness Index ($\mathcal{J}$):**
   $$\mathcal{J} = \frac{\left( \sum_{j=1}^{|\mathcal{N}|} \rho_j \right)^2}{|\mathcal{N}| \sum_{j=1}^{|\mathcal{N}|} \rho_j^2}$$
- **Energy per Megabit ($E_{\text{mbit}}$, J/Mbit):** Total RF and payload energy consumed per delivered Megabit.

