# CAPRO OBJECTIVE NORMALIZATION & DIMENSIONLESS UTILITY SPECIFICATION

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Framework:** Confidence-Aware Predictive Reliability Orchestration (CAPRO)  
**Document:** Dimensional Homogeneity, Normalization Functions, and Weight Sensitivity  
**Date:** November 2026  

---

## 1. Problem Statement: Violation of Dimensional Homogeneity in Baseline Prototype

In the original preliminary prototype of CAPRO (`src/orchestration_engine/capro_engine.py`), the decision utility was computed via:
$$R_{\text{raw}} = \text{SINR}_{\text{pred}}[\text{dB}] - \kappa \cdot U[\text{dB}] - 0.8 \cdot (\text{latency}[\text{ms}] - 10) - 5.0 \cdot (\text{load})^2$$

This formulation violated the core physics principle of **dimensional homogeneity**:
- Decibels (logarithmic ratio of powers) were directly added to milliseconds (temporal duration) and dimensionless load squared.
- A $1\text{ ms}$ increase in queuing delay penalized the utility by $0.8$, whereas a $1\text{ dB}$ increase in signal power rewarded it by $1.0$. The implicit trade-off ratio between power and delay was arbitrary and scale-dependent.

To establish rigorous mathematical integrity, Phase 3 completely replaces this formulation with a **strictly dimensionless, unit-normalized multi-attribute utility framework**.

---

## 2. Dimensionless Normalization Functions

Every attribute $k \in \{\text{link}, \text{latency}, \text{capacity}, \text{handover}, \text{risk}\}$ is mapped into the normalized interval $[0, 1]$ via piecewise linear or smooth monotonic transfer functions:

### 2.1 Link Quality Utility $U_{\text{link}}(j)$
$$U_{\text{link}}(j) = \min\left(1.0, \max\left(0.0, \frac{\hat{q}_{50, j}(t+H) - \gamma_{\text{min}}}{\gamma_{\text{max}} - \gamma_{\text{min}}}\right)\right)$$
- Domain: $\gamma_{\text{min}} = 0.0\text{ dB}$, $\gamma_{\text{max}} = 30.0\text{ dB}$.
- At $\gamma = 0\text{ dB}$ (BPSK sensitivity threshold), $U_{\text{link}} = 0.0$.
- At $\gamma \ge 30\text{ dB}$ (highest 64-QAM/256-QAM MCS saturation), $U_{\text{link}} = 1.0$.

### 2.2 Latency Utility $U_{\text{latency}}(j)$
$$U_{\text{latency}}(j) = 1.0 - \min\left(1.0, \max\left(0.0, \frac{\hat{L}_j(t) - L_{\text{min}}}{L_{\text{max}, u} - L_{\text{min}}}\right)\right)$$
- Domain: $L_{\text{min}} = 1.0\text{ ms}$ (propagation delay of local terrestrial base station), $L_{\text{max}, u} \in \{10.0\text{ ms (URLLC)}, 50.0\text{ ms (eMBB)}\}$.
- For URLLC, when physical delay reaches $10.0\text{ ms}$, $U_{\text{latency}} = 0.0$. When delay is $1.0\text{ ms}$, $U_{\text{latency}} = 1.0$.
- Inverting the metric ensures higher utility represents superior (lower delay) performance.

### 2.3 Available Capacity Utility $U_{\text{capacity}}(j)$
$$U_{\text{capacity}}(j) = 1.0 - \rho_j(t), \quad \rho_j(t) \in [0.0, 1.0]$$
- $\rho_j(t) = \frac{\text{Allocated Bandwidth}}{\text{Total Available Bandwidth}}$.
- An idle node ($\rho = 0.0$) provides maximum capacity utility $1.0$; a saturated node ($\rho = 1.0$) yields $0.0$.

### 2.4 Handover Switching Cost $C_{\text{handover}}(j)$
$$C_{\text{handover}}(j) = \begin{cases} 0.0, & \text{if } j = s_u(t^-) \quad (\text{maintain current connection}) \\ 1.0, & \text{if } j \ne s_u(t^-) \quad (\text{execute inter-node handover}) \end{cases}$$
- Explicitly models the control plane mute window ($50\text{ ms}$), buffer reordering, and reassociation signaling overhead.

### 2.5 Epistemic Risk Cost $C_{\text{risk}}(j)$
$$C_{\text{risk}}(j) = \min\left(1.0, \max\left(0.0, \frac{\hat{\sigma}_{\text{epi}, j}(t+H)}{\sigma_{\text{epi, max}}}\right)\right)$$
- Domain: $\sigma_{\text{epi, max}} = 3.0\text{ dB}$.
- When tree variance across Random Forest estimators is small ($\le 0.1\text{ dB}$, high model certainty), $C_{\text{risk}} \approx 0.0$.
- When severe multipath flutter or OOD cloudburst causes tree splits to diverge ($\sigma_{\text{epi}} \ge 1.5\text{ dB}$), $C_{\text{risk}}$ penalizes the link.

---

## 3. Configurable Weight Vectors by Service Class

Weights are assigned based on 3GPP Service-Level Agreement (SLA) priorities:

| Weight Parameter | Symbol | URLLC Service Weight | eMBB Service Weight | Justification |
| :--- | :---: | :---: | :---: | :--- |
| **Link Quality Weight** | $w_1$ | $0.35$ | **$0.40$** | eMBB prioritizes peak spectral efficiency and high MCS. |
| **Latency Weight** | $w_2$ | **$0.35$** | $0.15$ | URLLC demands ultra-low end-to-end latency budget. |
| **Capacity Weight** | $w_3$ | $0.10$ | **$0.30$** | eMBB requires high bandwidth and low cell congestion. |
| **Handover Cost Weight**| $w_4$ | **$0.15$** | $0.10$ | Handover interruptions ($50\text{ ms}$) violate URLLC SLAs. |
| **Epistemic Risk Weight**| $w_5$ | $0.05$ | $0.05$ | Penalizes channel volatility and OOD model doubt. |
| **Sum of Weights** | $\sum w_i$| **$1.00$** | **$1.00$** | Strict convex combination simplex. |

---

## 4. Mathematical Properties of the Normalized Objective

1. **Boundedness:** $J_{u, j}(t) \in [-w_4 - w_5, w_1 + w_2 + w_3] \subseteq [-0.20, 1.00]$ for all links.
2. **Scale Invariance:** Multiplying underlying physical units (e.g. converting ms to seconds, or Watts to dBm) leaves $J_{u, j}$ completely unchanged.
3. **Monotonicity:** Utility is strictly increasing in predicted SINR, available capacity, and connection stability, and strictly decreasing in latency, congestion, and epistemic doubt.
