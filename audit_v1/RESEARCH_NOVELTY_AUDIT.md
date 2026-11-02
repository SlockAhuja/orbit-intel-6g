# ORBIT-INTEL 6G: Research Novelty and Workspace Overlap Audit

---

## 1. Audit Against Adjoining Research Manuscripts

A deep audit was conducted comparing the ORBIT-INTEL 6G codebase and claims against the pre-existing manuscripts in the user's workspace:

### 1.1. Prior Research 1: Safe-LPPO (ICC 2027)
- **File Location**: `sem 5/conferance/ADVANCE_6G/paper/ICC_2027_Final.tex`.
- **Title**: *"Safe-LPPO: Safe Adaptive Lagrangian Deep Reinforcement Learning for Dynamic Multi-Beam Slicing and Energy Efficiency in SAGIN 6G Networks"*.
- **Authors**: Slock Ahuja, Praveen Kumar Sharma, Sudarshan Sanap.
- **Overlap Analysis**:
  - *Shared Concepts*: Both papers model 4-tier Space-Air-Ground Integrated Networks (SAGIN) consisting of LEO satellites, HAPS, UAVs, and terrestrial base stations under 3GPP TR 38.811 channel assumptions.
  - *Mathematical Model Differences*:
    - Safe-LPPO formulates a Constrained Markov Decision Process (CMDP) with an actor-critic proximal policy optimization (PPO) agent that dynamically toggles satellite beam transceivers between active and sleep states to conserve solar battery depth-of-discharge.
    - ORBIT-INTEL 6G introduces CAPRO: a machine learning regression model forecasting future link quality, paired with statistical dual-uncertainty quantification and a risk-adjusted multi-tier selection score.
  - *Overlap Verdict*: **CLEAN SEPARATION OF PROBLEM AND METHOD**.
    - ORBIT-INTEL 6G does not reuse the Lagrangian PPO code, battery state MDP formulations, or beam-sleeping actions from Safe-LPPO.

### 1.2. Prior Research 2: Quantum-Secure FL Smart Cities
- **File Location**: `sem 5/papers/README.md` and `sem 5/papers/latex/main.tex`.
- **Title**: *"A Quantum-Secure Federated AI and Blockchain Framework for Secure Smart City Communications"*.
- **Overlap Analysis**:
  - Treats BB84 QKD, PBFT consortium blockchains, and coordinate-wise trimmed-mean federated learning.
  - *Overlap Verdict*: **ZERO OVERLAP**. The technical domains are entirely unrelated.

---

## 2. Reused Text, Equations, and Simulation Scripts

| Element | Prior Manuscript | ORBIT-INTEL 6G | Overlap Status |
| :--- | :--- | :--- | :--- |
| **Keplerian Orbit Physics** | Standard Keplerian velocity $\sqrt{\mu/r}$ | `src/simulation_engine/orbital.py` | Standard textbook physics (Common knowledge) |
| **ITU-R P.618 Rain Model** | ITU-R P.618-13 slant path equations | `src/channel_models/propagation.py` | Standard ITU-R recommendation equations |
| **Dataset & Telemetry Traces** | Safe-LPPO private traffic logs | `data/synthetic/sagin_telemetry_dataset.csv` | **100% Independent Synthetic Generation** |
| **Algorithms & Code** | PyTorch Actor-Critic PPO (`Safe-LPPO`) | Scikit-learn Quantile Gradient Boosting (`models.py`) | **100% Independent Source Code** |
| **Figures** | ICC 2027 beam-sleeping waterfall plots | `results/figures/fig1` to `fig7` | **100% Independent Figure Designs** |

---

## 3. Critical Assessment of the Novelty Claims

### 3.1. What is NOT Genuinely Novel
In the previous report, the authors claimed:
> *"CAPRO is the first architectural framework for heterogeneous 6G SAGIN that systematically pairs multi-step forecasting with calibrated uncertainty."*
- **Auditor Critique**:
  - Overclaiming "first framework of its kind" without an exhaustive patent and IEEE Xplore survey is hazardous for an IEEE ComSoc submission.
  - Uncertainty quantification in wireless link adaptation (using Gaussian processes, ensemble dropout, and quantile regression) has been studied in vehicular (V2X) and satellite systems (e.g., studies by Lin et al., *IEEE TWC 2022*; Rault et al., *IEEE Network 2022*).
  - Furthermore, because the current implementation has an inactive satellite decision path, the empirical claim of "uncertainty-driven multi-tier reliability improvement" is not experimentally demonstrated.

### 3.2. Defensible Novelty Statement
To maintain high academic integrity at IEEE ComSoc, the novelty must be framed accurately and defensibly:

> **Defensible Novelty Statement**:  
> *"ORBIT-INTEL 6G presents **CAPRO (Confidence-Aware Predictive Reliability Orchestration)**, a predictive framework for Space-Air-Ground Integrated Networks (SAGIN) that couples multi-horizon gradient boosted channel forecasting with calibrated dual-uncertainty estimation (epistemic ensemble variance and aleatoric pinball loss quantiles). By penalizing forecast variance within a risk-adjusted utility metric ($R^{\text{adj}}$) and enforcing orbital departure gating ($\tau_{\text{vis}} < 12\text{s}$), CAPRO mitigates tardy reactive handovers and suppresses ping-pong signaling oscillations across heterogeneous satellite, stratospheric, and terrestrial access layers."*

