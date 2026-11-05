# CAPRO ABLATION DESIGN: COMPONENT DECOMPOSITION & HYPOTHESIS SPECIFICATION

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Framework:** Confidence-Aware Predictive Reliability Orchestration (CAPRO)  
**Document:** Experimental Design of Controlled Ablation Variants  
**Date:** November 2026  

---

## 1. Executive Summary

To scientifically demonstrate that CAPRO's performance improvements stem from its principled constituent mechanisms rather than arbitrary parameter tuning, seven controlled ablation variants are formally defined. Each variant isolates a single architectural feature, enabling rigorous quantification of its contribution to network reliability, latency compliance, and service continuity.

---

## 2. Inventory of Ablation Variants

| Variant ID | Variant Designation | Modality Alteration | Parameter Adjustments | Scientific Hypothesis Isolated |
| :---: | :--- | :--- | :--- | :--- |
| **V1** | **No Uncertainty Awareness** | Removes both aleatoric bounds and epistemic penalties. | Uses point estimate $\hat{y}_{50}$ in $\mathcal{C}_{\text{rel}}$; sets $w_5 = 0.0$. | Quantifies the reliability penalty of relying on uncalibrated point forecasts. |
| **V2** | **Aleatoric Uncertainty Only** | Evaluates physical quantile bounds without epistemic model doubt. | Uses $\hat{q}_{05}$ in $\mathcal{C}_{\text{rel}}$; sets $w_5 = 0.0$. | Demonstrates physical fade protection while isolating the role of epistemic OOD detection. |
| **V3** | **Epistemic Uncertainty Only** | Evaluates model disagreement penalty without quantile margin bounds. | Uses point estimate $\hat{y}_{50}$ in $\mathcal{C}_{\text{rel}}$; retains $w_5 C_{\text{risk}}$. | Tests whether model variance alone can compensate for lack of physical lower-bound gating. |
| **V4** | **No Handover Cost / Hysteresis** | Disables switching cost penalty and hysteresis margin. | Sets $w_4 = 0.0$ and $\Delta_{\text{hyst}} = 0.0$. | Exposes the ping-pong handover churn and packet loss caused by unconstrained switching. |
| **V5** | **No Reliability Constraints** | Disables hard feasibility filter $\mathcal{C}_{\text{rel}}$. | Sets $\mathcal{F}_u(t) = \mathcal{N}_{\text{visible}}$; all visible nodes eligible. | Proves that soft utility optimization alone cannot prevent severe link outages. |
| **V6** | **No Latency Constraints** | Disables hard delay filtering $\mathcal{C}_{\text{lat}}$ for URLLC. | Permits URLLC users to attach to LEO links exceeding $10\text{ ms}$. | Demonstrates that without strict latency filtering, URLLC traffic is misallocated to LEO, violating SLAs. |
| **V7** | **Full CAPRO (Proposed)** | Complete normalized architecture with all mechanisms active. | Standard weights: $\mathbf{w}$, hard filter $\mathcal{F}_u(t)$, $\Delta_{\text{hyst}} = 0.08$. | Serves as the complete proposed research framework. |

---

## 3. Mathematical Parameter Matrix across Variants

| Parameter / Mechanism | V1 (No Unc) | V2 (Aleatoric) | V3 (Epistemic) | V4 (No HO Cost) | V5 (No Rel Filter) | V6 (No Lat Filter) | V7 (Full CAPRO) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reliability Check Filter** | $\hat{y}_{50} \ge 3\text{ dB}$ | $\hat{q}_{05} \ge 3\text{ dB}$ | $\hat{y}_{50} \ge 3\text{ dB}$ | $\hat{q}_{05} \ge 3\text{ dB}$ | **Disabled** | $\hat{q}_{05} \ge 3\text{ dB}$ | $\mathbf{\hat{q}_{05} \ge 3\text{ dB}}$ |
| **Latency Check Filter** | $\hat{L} \le L_{\text{max}}$ | $\hat{L} \le L_{\text{max}}$ | $\hat{L} \le L_{\text{max}}$ | $\hat{L} \le L_{\text{max}}$ | $\hat{L} \le L_{\text{max}}$ | **Disabled** | $\mathbf{\hat{L} \le L_{\text{max}}}$ |
| **Handover Cost Weight $w_4$** | $0.15$ | $0.15$ | $0.15$ | **$0.00$** | $0.15$ | $0.15$ | **$0.15$** |
| **Epistemic Risk Weight $w_5$** | **$0.00$** | **$0.00$** | $0.05$ | $0.05$ | $0.05$ | $0.05$ | **$0.05$** |
| **Hysteresis Margin $\Delta_{\text{hyst}}$** | $0.08$ | $0.08$ | $0.08$ | **$0.00$** | $0.08$ | $0.08$ | **$0.08$** |
| **Orbital Buffer $T_{\text{HO, min}}$** | $12\text{ s}$ | $12\text{ s}$ | $12\text{ s}$ | $12\text{ s}$ | $12\text{ s}$ | $12\text{ s}$ | **$12\text{ s}$** |

---

## 4. Expected Performance Trade-Offs

- **V1 vs. V7:** V1 will exhibit higher outage probability during convective rain cells (Scenario 3) and satellite departure (Scenario 4) because point estimates miss 68.9% of impending outages.
- **V4 vs. V7:** V4 will exhibit a dramatic spike in total handover count ($>3\times$) and elevated packet loss during execution ($>2.5\times$), proving the necessity of $\Delta_{\text{hyst}} = 0.08$.
- **V6 vs. V7:** V6 will exhibit severe URLLC SLA violation rates ($>40\%$) because URLLC users will attach to LEO satellites for high throughput, despite incurring $>11.6\text{ ms}$ delay.

