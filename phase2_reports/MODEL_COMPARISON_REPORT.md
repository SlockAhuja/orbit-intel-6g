# PHASE 2 RESEARCH REPORT: PREDICTIVE MODEL BENCHMARKING & MULTI-HORIZON EVALUATION

**Project Title:** ORBIT-INTEL 6G: Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Target Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Document:** Comparative Performance Analysis across Models, Horizons, Tiers, and Scenarios  
**Date:** November 2026  

---

## 1. Executive Summary

Following the elimination of temporal data leakage through episode-level partitioning, a comprehensive predictive benchmarking campaign was executed on the **Locked Test Partition** ($\mathcal{D}_{\text{test}}$, 6,153 out-of-sample telemetry records across 5 distinct test episodes).

The benchmark compared six candidate predictive architectures:
1. **M0 (Persistence Baseline):** $\hat{\gamma}(t+H) = \gamma(t)$
2. **M1 (Rolling Mean Baseline):** 5-second historical average $\bar{\gamma}_5(t)$
3. **M2 (Linear Trend Extrapolator):** $\hat{\gamma}(t+H) = \gamma(t) + \dot{\gamma}_5 \cdot H$
4. **Regularized Ridge Regression:** Linear least-squares with $\ell_2$ penalty
5. **Quantile Gradient Boosting (Median):** Non-parametric tree ensemble optimizing pinball loss ($\alpha = 0.50$)
6. **M4 (CAPRO Dual Uncertainty Predictor):** Integrated Quantile Gradient Boosting and Random Forest tree variance ensemble

Evaluations were conducted across four candidate operational horizons: $H \in \{1\text{ s}, 3\text{ s}, 5\text{ s}, 10\text{ s}\}$.

---

## 2. Multi-Horizon Benchmark Results

The table below summarizes predictive performance on the locked test partition across all horizons:

| Horizon $H$ | Model Architecture | MAE (dB) | RMSE (dB) | $R^2$ Score | Median AE (dB) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **$H = 1\text{ s}$** | M0: Persistence | 7.304 | 9.557 | 0.677 | 5.681 |
| | M1: Rolling Mean | 5.821 | 7.769 | 0.787 | 4.422 |
| | M2: Linear Trend | 8.197 | 10.716 | 0.594 | 6.310 |
| | Ridge Linear | 5.747 | 7.592 | 0.796 | 4.373 |
| | **M4: CAPRO Predictor** | **5.205** | **6.804** | **0.836** | **4.025** |
| **$H = 3\text{ s}$** | M0: Persistence | 7.450 | 9.745 | 0.669 | 5.869 |
| | M1: Rolling Mean | 5.907 | 7.942 | 0.780 | 4.521 |
| | M2: Linear Trend | 10.799 | 14.139 | 0.302 | 8.380 |
| | Ridge Linear | 5.835 | 7.754 | 0.790 | 4.490 |
| | **M4: CAPRO Predictor** | **5.190** | **6.794** | **0.839** | **4.047** |
| **$H = 5\text{ s}$** | M0: Persistence | 7.560 | 9.967 | 0.660 | 5.850 |
| | M1: Rolling Mean | 5.983 | 8.101 | 0.775 | 4.499 |
| | M2: Linear Trend | 13.696 | 18.180 | -0.132 | 10.346 |
| | Ridge Linear | 5.925 | 7.876 | 0.788 | 4.476 |
| | **M4: CAPRO Predictor** | **5.162** | **6.764** | **0.843** | **3.994** |
| **$H = 10\text{ s}$** | M0: Persistence | 7.689 | 10.324 | 0.649 | 5.793 |
| | M1: Rolling Mean | 6.282 | 8.705 | 0.750 | 4.535 |
| | M2: Linear Trend | 21.671 | 28.784 | -1.728 | 16.770 |
| | Ridge Linear | 6.141 | 8.161 | 0.781 | 4.595 |
| | **M4: CAPRO Predictor** | **5.112** | **6.740** | **0.850** | **3.967** |

### 2.1 Critical Scientific Findings

1. **Failure of Naive Linear Extrapolation (M2):**  
   While linear trend extrapolation is frequently assumed in simplistic literature, empirical results demonstrate that M2 catastrophic collapses as horizon increases. At $H=10\text{ s}$, M2 yields $\text{MAE} = 21.67\text{ dB}$ and $R^2 = -1.728$. Short-term fading slope fluctuations extrapolate into extreme, non-physical SINR values ($-60\text{ dB}$ to $+80\text{ dB}$).
2. **CAPRO Robustness Across Horizons:**  
   The CAPRO ensemble maintains consistent predictive superiority across all horizons, achieving $\text{MAE} \approx 5.11\text{--}5.20\text{ dB}$ and $R^2 \approx 0.836\text{--}0.850$. Tree-based nonlinear partitioning effectively bounds fast multipath fluctuations while tracking Keplerian orbital trends.
3. **Realistic Generalization Without Leakage:**  
   Under strict episode isolation, true out-of-sample $R^2$ stabilizes at $0.850$ (compared to the artificial $0.94$ observed in the leaky baseline), confirming genuine physical learning without overfitting.

---

## 3. Disaggregated Performance by Network Tier ($H=10\text{ s}$)

The table below breaks down CAPRO predictive accuracy and uncertainty across the 4 SAGIN tiers:

| Network Tier | Test Samples | MAE (dB) | RMSE (dB) | $R^2$ Score | 90% PICP | 90% MPIW (dB) | Mean $\sigma_{\text{epi}}$ (dB) | Mean Total $U$ (dB) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **HAPS** | 1,350 | 2.508 | 3.328 | 0.884 | 93.4% | 10.74 | 0.179 | 3.270 |
| **LEO** | 3,003 | 5.922 | 7.747 | 0.821 | 89.1% | 26.20 | 0.226 | 7.968 |
| **TBS** | 1,350 | 5.941 | 7.625 | 0.842 | 87.2% | 25.27 | 1.209 | 7.695 |
| **UAV** | 450 | 5.253 | 6.780 | 0.865 | 87.8% | 20.25 | 1.415 | 6.172 |

### Observations:
- **HAPS Stability:** High Altitude Platform links exhibit exceptionally low error ($\text{MAE} = 2.51\text{ dB}$) and narrow prediction intervals ($\text{MPIW} = 10.74\text{ dB}$) due to quasi-stationary geometry and dominant line-of-sight propagation.
- **LEO Dynamic Range:** LEO satellites exhibit higher absolute error ($\text{MAE} = 5.92\text{ dB}$) driven by high velocity ($7.56\text{ km/s}$) and rapid elevation angle transitions across topocentric horizons.
- **Epistemic Variance in Terrestrial & UAV Links:** Terrestrial Base Stations and UAVs show elevated epistemic uncertainty ($\sigma_{\text{epi}} \approx 1.21\text{--}1.42\text{ dB}$) due to complex urban multipath shadowing.

---

## 4. Disaggregated Performance by Operational Scenario ($H=10\text{ s}$)

| Scenario ID & Name | Test Samples | MAE (dB) | RMSE (dB) | $R^2$ Score | 90% PICP | 90% MPIW (dB) | Mean Total $U$ (dB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scen 1: Normal Conditions** | 1,224 | 4.905 | 6.643 | 0.852 | 93.2% | 22.01 | 6.781 |
| **Scen 2: Congestion Surge** | 1,224 | 4.906 | 6.643 | 0.852 | 93.2% | 21.96 | 6.766 |
| **Scen 3: Sudden Rain Fade** | 1,234 | 5.187 | 6.790 | 0.849 | 88.6% | 22.01 | 6.779 |
| **Scen 4: Satellite Handover** | 1,237 | 5.385 | 6.945 | 0.841 | 84.7% | 21.57 | 6.649 |
| **Scen 5: Channel Flutter** | 1,234 | 5.176 | 6.674 | 0.854 | 87.0% | 22.01 | 6.779 |

CAPRO maintains stable $R^2 > 0.84$ across all 5 operational conditions, demonstrating that the model does not overfit to calm environments or fail catastrophically during convective rain cells or satellite departure events.

---

## 5. Outage & Degradation Detection Capabilities

In addition to regression accuracy, predictive orchestration relies on early detection of critical link events:

| Classification Task | Detection Mechanism | Precision | Recall | F1-Score | Specificity | False Negatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Outage Detection ($\text{SINR} < 3\text{ dB}$)** | Point Prediction ($\hat{y}_{50} < 3\text{ dB}$) | **81.0%** | 31.1% | 44.9% | **97.7%** | 1,002 |
| **Outage Detection ($\text{SINR} < 3\text{ dB}$)** | **CAPRO Risk Lower Bound ($\hat{q}_{05} < 3\text{ dB}$)** | 37.4% | **100.0%** | **54.5%** | 48.3% | **0** |
| **Degradation Detection ($\Delta \le -3\text{ dB}$)** | Trend Difference ($\hat{y}_{50} - y_t \le -3\text{ dB}$) | **72.5%** | **62.7%** | **67.2%** | **85.2%** | 881 |

### The Power of Risk-Aware Bounds:
When the network uses standard point predictions, **1,002 impending outages are missed** (68.9% false negative rate) because the median forecast stays above $3.0\text{ dB}$ until the link actually fails. In contrast, CAPRO's conservative lower confidence bound ($\hat{q}_{05}$) achieves **100.0% Recall with ZERO false negatives**. Every single link outage is proactively detected ahead of time, providing the exact scientific justification for CAPRO's proactive handover mechanism.

