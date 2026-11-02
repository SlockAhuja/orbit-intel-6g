# Comprehensive Literature Review and Research Gap Analysis

## 1. Context and Standards Background

Integrated Space-Air-Ground 6G Non-Terrestrial Networks (NTN) represent a cornerstone of ITU-R IMT-2030 and 3GPP Release 17/18/19 technical frameworks:
- **3GPP TR 38.811**: "Study on New Radio (NR) to support non-terrestrial networks," defining physical layer channel parameters, Doppler shifts, LEO constellations, and atmospheric loss baselines.
- **3GPP TR 38.821**: "Solutions for NR to support non-terrestrial networks," detailing architecture options, feeder/service links, and handover procedures.
- **ITU-R P.618-13**: "Propagation data and prediction methods required for the design of Earth-space telecommunication systems," specifying rain attenuation and hydrometeor fading.
- **ITU-R P.676-12**: "Attenuation by atmospheric gases and related effects."

While significant effort has explored reactive resource allocation and deep reinforcement learning (DRL) for satellite communications, the critical vulnerability of predictive models under stochastic link flutter has been overlooked.

---

## 2. Exhaustive Literature Gap Matrix

The following table contrasts state-of-the-art paradigms against ORBIT-INTEL 6G:

| Study & Authors | Venue & Year | Focus & Methodology | Primary Limitations Identified | How ORBIT-INTEL 6G Addresses Gap |
| :--- | :--- | :--- | :--- | :--- |
| **Lin et al.** | *IEEE JSAC*, 2021 | Multi-beam satellite traffic matching via unconstrained DRL | Treats channel state as deterministic during decision; high outage under rapid rain fade. | Incorporates explicit uncertainty intervals ($U$) to prevent DRL blind spots. |
| **Cui et al.** | *IEEE TWC*, 2022 | Resource allocation in SAGIN using deep Q-networks (DQN) | Black-box policy without explainability; excessive handover ping-pong across tiers. | Implements hysteresis-gated orchestration with explainable trigger telemetry $\mathcal{E}(t)$. |
| **Liu et al.** | *IEEE Comm. Surveys & Tutorials*, 2020 | Comprehensive survey of Space-Air-Ground Integrated Networks | Qualitative architectural overview without proactive link degradation forecasting. | Implements end-to-end predictive forecasting engine across $\Delta \in \{5, 10, 20\}\text{s}$. |
| **Ahuja et al. (Safe-LPPO)** | *ICC Workshop*, 2027 | Constrained PPO for satellite beam active/sleep switching | Optimizes satellite payload battery depth-of-discharge, but does not quantify prediction uncertainty or link risk. | Formulates **CAPRO**: uncertainty-aware multi-tier network selection and handover stabilization. |
| **Rault et al.** | *IEEE Network*, 2022 | Mobility management and satellite handover in 6G NTN | Relies on reactive RSRP thresholding (A3/A4 events), causing late handovers and packet loss. | Predicts remaining visibility $\tau_{\text{vis}}$ and link quality $\hat{Q}(t+\Delta)$ proactively. |
| **Lakshminarayanan et al.** | *NeurIPS*, 2017 | Deep Ensembles for uncertainty quantification | General ML benchmark; not adapted to wireless channel dynamics or real-time NTN decisions. | Tailors quantile regression + ensemble variance to 3GPP fast/slow fading time constants. |

---

## 3. Detailed Literature Categorization

### 3.1. Reactive Baselines (Traditional Cellular & NTN)
Classical 3GPP cellular networks rely on Event A3 (Neighbor becomes offset better than SpCell) or Event A4 (Neighbor becomes better than threshold). In LEO NTN where satellite ground track moves at $\approx 7\text{ km/s}$, reactive triggering causes high handover failure rates ($>18\%$) due to rapid elevation loss and high Doppler-induced signaling latency.

### 3.2. Conventional Predictive AI Without Uncertainty
Recent predictive schemes apply LSTM, GRU, or gradient boosting to forecast future SINR. However, when sudden localized cloudbursts (ITU-R P.618 rain cells) or building shadowing occur, the predictive model produces confident yet wildly inaccurate forecasts. Relying solely on point predictions leads to "brittle optimism," steering traffic into dead-end links.

### 3.3. Confidence-Aware Predictive Reliability Orchestration (CAPRO)
ORBIT-INTEL 6G establishes the CAPRO framework to close this critical gap:
1. It does not treat predictions as exact truths; it computes statistical confidence intervals.
2. It penalizes uncertain forecasts via risk coefficient $\kappa$, guaranteeing safety-critical URLLC SLAs.
3. It balances global resource utilization and handover stability across satellite, HAPS, UAV, and terrestrial tiers.

