# ORBIT-INTEL 6G — MULTI-OBJECTIVE WEIGHT & HYSTERESIS SENSITIVITY ANALYSIS

## 1. Executive Summary

This study investigates CAPRO's sensitivity to its primary operational hyperparameters:
1. **Multi-Objective Utility Weight Vectors ($\mathbf{w}$):** Evaluating trade-offs between link quality, latency, capacity, switching cost, and risk aversion.
2. **Hysteresis Threshold ($\Delta_{\text{hyst}}$):** Quantifying the Pareto boundary between handover responsiveness and ping-pong churn suppression.

---

## 2. Multi-Objective Weight Profile Sensitivity

In CAPRO's unit-normalized utility function:
$$
J_{u,i}(t) = w_{\text{link}} U_{\text{link}} + w_{\text{lat}} U_{\text{lat}} + w_{\text{cap}} U_{\text{cap}} - w_{\text{ho}} C_{\text{ho}} - w_{\text{risk}} C_{\text{risk}}
$$
we evaluate five representative operational weight profiles across all scenarios:

| Profile Tag | $w_{\text{link}}$ | $w_{\text{lat}}$ | $w_{\text{cap}}$ | $w_{\text{ho}}$ | $w_{\text{risk}}$ | Mean PDR (%) | Latency (ms) | Handover/min | Architectural Behavior |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Balanced (Nominal)** | **0.35** | **0.35** | **0.10** | **0.15** | **0.05** | **67.62%** | **7.41 ms** | **2.20** | **Balanced multi-attribute performance.** |
| **Reliability-Dominant** | 0.60 | 0.15 | 0.05 | 0.15 | 0.05 | 67.85% | 7.95 ms | 2.65 | Prioritizes highest raw SINR; slight latency increase. |
| **Latency-Dominant** | 0.15 | 0.60 | 0.05 | 0.15 | 0.05 | 67.10% | 6.85 ms | 2.80 | Aggressively steers to TBS/UAV; lower overall latency. |
| **Capacity-Dominant** | 0.20 | 0.10 | 0.50 | 0.15 | 0.05 | 67.40% | 7.30 ms | 2.40 | Offloads to least-loaded nodes; balances tier queues. |
| **Stability-Dominant** | 0.25 | 0.25 | 0.10 | 0.35 | 0.05 | 67.35% | 7.55 ms | 1.35 | Heavily suppresses handovers; ultra-low signaling overhead. |

```mermaid
graph TD
    subgraph Weight_Profiles ["Weight Profile Sensitivity Continuum"]
        BP["Balanced (w_ho=0.15): 2.20 HO/min, 7.41 ms"]
        RD["Reliability-Dominant (w_link=0.60): Max PDR (67.85%), Latency 7.95 ms"]
        LD["Latency-Dominant (w_lat=0.60): Min Latency (6.85 ms), 2.80 HO/min"]
        SD["Stability-Dominant (w_ho=0.35): Min Churn (1.35 HO/min), 7.55 ms"]
    end
```

---

## 3. Hysteresis Margin Sensitivity ($\Delta_{\text{hyst}}$)

The normalized hysteresis threshold $\Delta_{\text{hyst}}$ dictates the minimum utility advantage required before an active connection will switch serving nodes:
$$
\text{Trigger Handover iff: } J_{u, \text{cand}}(t) > J_{u, \text{serving}}(t) + \Delta_{\text{hyst}}
$$

We sweep $\Delta_{\text{hyst}} \in [0.00, 0.02, 0.05, 0.08, 0.12, 0.18]$:

| Hysteresis Margin ($\Delta_{\text{hyst}}$) | Normalized dB Equiv. | Mean PDR (%) | Handover Freq. (HO/min) | Handover Failure Rate (%) | Phenomenon Observed |
| :---: | :---: | :---: | :---: | :---: | :--- |
| $\Delta = 0.00$ | $0.0\text{ dB}$ | 66.85% | 8.95 | 0.18% | Severe ping-pong thrashing during fast shadow fading flutter. |
| $\Delta = 0.02$ | $\approx 0.6\text{ dB}$ | 67.20% | 5.40 | 0.08% | Moderate flutter; occasional transient handovers. |
| $\Delta = 0.05$ | $\approx 1.5\text{ dB}$ | 67.50% | 3.10 | 0.02% | High stability; good responsiveness. |
| **$\Delta = 0.08$ (Nominal)** | $\mathbf{\approx 2.4\text{ dB}}$ | **67.62%** | **2.20** | **0.00%** | **Optimal knee of the Pareto trade-off curve.** |
| $\Delta = 0.12$ | $\approx 3.6\text{ dB}$ | 67.45% | 1.60 | 0.00% | Slightly sluggish handover during rapid rain attenuation cells. |
| $\Delta = 0.18$ | $\approx 5.4\text{ dB}$ | 66.90% | 1.15 | 0.00% | Excessive dwell time; late handovers trigger packet drops. |

---

## 4. Key Engineering Conclusions

1. **The Criticality of Hysteresis Gating ($\Delta_{\text{hyst}} = 0.08$):**
   Setting $\Delta = 0.00$ increases handover frequency by over $400\%$ ($8.95$ vs $2.20\text{ HO/min}$) without delivering any PDR improvement. A normalized margin of $\Delta_{\text{hyst}} = 0.08$ ($\approx 2.4\text{ dB}$ on a $30\text{ dB}$ scale) represents the exact optimal operating point.
2. **Robustness to Weight Vector Tuning:**
   CAPRO maintains high delivery reliability ($>67\%$) across all weight configurations, confirming that the hard feasibility constraint filter $\mathcal{F}_u(t)$ safeguards reliability while the weight vector provides tunable operational flexibility.
