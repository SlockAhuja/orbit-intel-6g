# ORBIT-INTEL 6G: Mathematical Formulation and System Model

## 1. Introduction and Architectural Overview

The **ORBIT-INTEL 6G** architecture models a four-tier heterogeneous Space-Air-Ground Integrated Network (SAGIN) composed of:
1. **Low Earth Orbit (LEO) Satellites** ($\mathcal{S}$): High-mobility platforms orbiting at altitudes $h_{\text{LEO}} \in [500, 1200]\text{ km}$ with orbital velocities $v_{\text{LEO}} \approx 7.56\text{ km/s}$, providing global wide-area coverage with one-way propagation delays of $15\text{--}35\text{ ms}$.
2. **High-Altitude Platform Stations (HAPS)** ($\mathcal{H}$): Stratospheric quasi-stationary platforms positioned at $h_{\text{HAPS}} \approx 20\text{ km}$, offering regional metropolitan and regional coverage with propagation delays of $2\text{--}5\text{ ms}$.
3. **Unmanned Aerial Vehicles (UAVs)** ($\mathcal{U}$): Low-altitude aerial communication relays operating at $h_{\text{UAV}} \in [200, 500]\text{ m}$, deployed dynamically to handle local traffic hotspots with delays of $1\text{--}3\text{ ms}$.
4. **Terrestrial Base Stations (TBS)** ($\mathcal{T}$): Ground cellular infrastructure delivering ultra-low-latency ($<1\text{ ms}$) broadband service within localized terrestrial cells ($r \le 2\text{ km}$).
5. **Mobile Users / User Equipments (UE)** ($\mathcal{M}$): Terrestrial, maritime, and vehicular mobile terminals requiring continuous, reliable high-QoS communication.

---

## 2. Dynamic SAGIN State Representation

At any discrete time epoch $t \in \{1, 2, \dots, T\}$, the network telemetry state between user $i \in \mathcal{M}$ and candidate serving node $j \in \mathcal{N} = \mathcal{S} \cup \mathcal{H} \cup \mathcal{U} \cup \mathcal{T}$ is characterized by the multi-dimensional tuple:

$$S_{i,j}(t) = \left[ \gamma_{i,j}(t), \, f_{d,i,j}(t), \, \rho_j(t), \, \tau_{\text{vis},i,j}(t), \, E_j(t), \, B_{\text{avail},j}(t), \, \theta_{i,j}(t) \right]^T$$

Where:
- $\gamma_{i,j}(t)$: Instantaneous Signal-to-Interference-plus-Noise Ratio (SINR) in dB.
- $f_{d,i,j}(t)$: Doppler shift in Hz induced by platform relative velocity.
- $\rho_j(t) \in [0, 1]$: Normalized instantaneous traffic load of node $j$.
- $\tau_{\text{vis},i,j}(t)$: Remaining geometric visibility duration (in seconds) before orbital line-of-sight is severed.
- $E_j(t) \in [0, 1]$: Normalized available on-board energy / battery state of charge.
- $B_{\text{avail},j}(t)$: Unallocated operational bandwidth in MHz.
- $\theta_{i,j}(t)$: Elevation angle (in degrees) of node $j$ with respect to the user local horizon.

---

## 3. Physical Channel Modeling & 3GPP TR 38.811 / ITU-R Formulations

### 3.1. Path Loss Model
In compliance with 3GPP TR 38.811 (Release 17/18 NTN specification), total path loss $\mathrm{PL}_{i,j}(t)$ in dB across link $(i,j)$ is decomposed as:

$$\mathrm{PL}_{i,j}(t) = \mathrm{FSPL}(d_{i,j}(t), f_c) + A_{\text{atm}}(\theta_{i,j}(t), f_c) + A_{\text{rain}}(t) + \chi_{\sigma}$$

1. **Free Space Path Loss (FSPL)**:
   $$\mathrm{FSPL}(d, f_c) = 20 \log_{10}(d) + 20 \log_{10}(f_c) + 20 \log_{10}\left(\frac{4\pi}{c}\right)$$
   Where $d_{i,j}(t)$ is the Euclidean slant distance in meters, $f_c$ is carrier frequency (e.g., $2.0\text{ GHz}$ S-band or $28.0\text{ GHz}$ Ka-band), and $c = 3 \times 10^8\text{ m/s}$.

2. **Atmospheric Gas Attenuation ($A_{\text{atm}}$)** (ITU-R P.676):
   $$A_{\text{atm}}(\theta, f_c) = \frac{A_0(f_c)}{\sin \theta + \frac{0.01}{\sqrt{\sin^2\theta + 0.002}}}$$
   Where $A_0(f_c)$ represents zenith attenuation.

3. **Rain Attenuation ($A_{\text{rain}}$)** (ITU-R P.618):
   $$A_{\text{rain}}(t) = \gamma_R \cdot d_{\text{eff}}(\theta)$$
   With specific rain attenuation $\gamma_R = k \cdot R^{\alpha}$ (where $R$ is rain rate in mm/h and $k, \alpha$ are frequency-dependent coefficients).

4. **Shadow Fading ($\chi_{\sigma}$)**:
   Modeled as log-normal shadowing $\chi_{\sigma} \sim \mathcal{N}(0, \sigma_{\text{SF}}^2)$, where standard deviation $\sigma_{\text{SF}}$ is a decreasing function of elevation angle $\theta$ (ranging from $4\text{ dB}$ at zenith to $8\text{ dB}$ at low elevation).

### 3.2. Doppler Shift Formulation
Relative orbital motion creates carrier frequency displacement:
$$f_{d,i,j}(t) = f_c \frac{\vec{v}_{rel,i,j}(t) \cdot \vec{u}_{i,j}(t)}{c}$$
Where $\vec{v}_{rel,i,j}(t) = \vec{v}_j(t) - \vec{v}_i(t)$ is relative velocity vector and $\vec{u}_{i,j}(t)$ is the unit line-of-sight directional vector. The Doppler rate (rate of change of frequency) is:
$$\dot{f}_{d,i,j}(t) = \frac{d}{dt} f_{d,i,j}(t)$$
For LEO satellites at $600\text{ km}$, maximum Doppler shift exceeds $\pm 48\text{ kHz}$ at S-band and $\pm 670\text{ kHz}$ at Ka-band, causing inter-carrier interference (ICI) if uncompensated.

### 3.3. Received Signal Power and SINR
The received signal power $P_{rx,i,j}(t)$ in dBm is:
$$P_{rx,i,j}(t) = P_{tx,j} + G_{tx,j}(\theta_{i,j}) + G_{rx,i}(\theta_{i,j}) - \mathrm{PL}_{i,j}(t)$$

Converting to Watts ($p_{rx} = 10^{(P_{rx}-30)/10}$), the instantaneous SINR is:
$$\gamma_{i,j}(t) = \frac{p_{rx,i,j}(t)}{\sum_{k \neq j, k \in \mathcal{N}} I_{i,k}(t) + N_0 B_{i,j}}$$
Where $N_0 = k_B T_{\text{sys}}$ is thermal noise power spectral density ($k_B = 1.3806 \times 10^{-23}\text{ J/K}$, $T_{\text{sys}} \approx 290\text{ K}$), and $I_{i,k}(t)$ is co-channel interference from overlapping beams.

---

## 4. Predictive Link-Risk Intelligence & Calibrated Uncertainty

### 4.1. Link-Quality Forecasting Operator
Given historical state observations over temporal window $W = \{t-k, \dots, t\}$, the predictive model $f_\theta$ forecasts the future link quality $\hat{Q}_{i,j}(t+\Delta)$ at lookahead horizon $\Delta \in \{5\text{s}, 10\text{s}, 20\text{s}\}$:

$$\hat{Q}_{i,j}(t+\Delta) = f_\theta\left( S_{i,j}(t-k:t) \right)$$

Target metric $Q_{i,j}$ corresponds to expected SINR $\gamma_{i,j}(t+\Delta)$ and link survivability.

### 4.2. Dual-Uncertainty Quantification ($g_\phi$)
Crucially, raw point predictions $\hat{Q}_{i,j}(t+\Delta)$ lack safety guarantees under stochastic fades. We formulate an uncertainty operator $g_\phi$:

$$U_{i,j}(t+\Delta) = g_\phi\left( S_{i,j}(t-k:t) \right) = \left[ \hat{q}_{\alpha/2}, \, \hat{q}_{1 - \alpha/2}, \, \sigma_{\text{total}}^2 \right]^T$$

Uncertainty is partitioned into two components:
1. **Aleatoric Uncertainty ($\sigma_{\text{ale}}^2$)**: Inherent stochasticity in the wireless channel (atmospheric turbulence, Rayleigh/Rician fast fading). Captured via pinball loss / quantile regression:
   $$\mathcal{L}_{\tau}(y, \hat{y}) = \max(\tau(y - \hat{y}), (\tau - 1)(y - \hat{y}))$$
   for nominal coverage $1 - \alpha = 0.90$ ($\tau \in \{0.05, 0.50, 0.95\}$).
2. **Epistemic Uncertainty ($\sigma_{\text{epi}}^2$)**: Model uncertainty stemming from sparse training samples in extreme geometric postures or rare weather anomalies, quantified through ensemble variance across $M$ estimators:
   $$\sigma_{\text{epi}}^2 = \frac{1}{M}\sum_{m=1}^M \left( \hat{y}^{(m)} - \bar{y} \right)^2$$

Total estimated uncertainty metric is formulated as:
$$U_{i,j}(t+\Delta) = \sqrt{\sigma_{\text{ale},i,j}^2 + \sigma_{\text{epi},i,j}^2} + \lambda \cdot (\hat{q}_{0.95} - \hat{q}_{0.05})$$

### 4.3. Statistical Calibration Metrics
To ensure $U_{i,j}$ represents rigorous probability rather than arbitrary heuristics:
- **Prediction Interval Coverage Probability (PICP)**:
  $$\mathrm{PICP} = \frac{1}{N} \sum_{n=1}^N \mathbb{I}\left( y_n \in [\hat{q}_{\alpha/2, n}, \, \hat{q}_{1-\alpha/2, n}] \right) \ge 1 - \alpha$$
- **Mean Prediction Interval Width (MPIW)** (Sharpness):
  $$\mathrm{MPIW} = \frac{1}{N} \sum_{n=1}^N (\hat{q}_{1-\alpha/2, n} - \hat{q}_{\alpha/2, n})$$
- **Expected Calibration Error (ECE)** across $K$ binned probability intervals:
  $$\mathrm{ECE} = \sum_{k=1}^K \frac{|B_k|}{N} \left| \mathrm{acc}(B_k) - \mathrm{conf}(B_k) \right|$$

---

## 5. Confidence-Aware Predictive Reliability Orchestration (CAPRO)

### 5.1. Risk-Adjusted Link Utility
CAPRO introduces a confidence-penalized link valuation:
$$R_{i,j}^{\text{adj}}(t+\Delta) = \hat{Q}_{i,j}(t+\Delta) - \kappa \cdot U_{i,j}(t+\Delta)$$
Where $\kappa \ge 0$ is a configurable risk-aversion coefficient. When channel variance is high or the ML model is uncertain, $R^{\text{adj}}$ automatically penalizes fragile high-nominal-SINR candidates in favor of robust, lower-variance links.

### 5.2. Multi-Objective Optimization Formulation
Let $a_i(t) \in \mathcal{N}$ denote the network tier allocated to user $i$. The global objective function $J(a, t)$ balances reliability, latency, handover stability, energy, and resource efficiency:

$$\min_{a(t)} \sum_{i \in \mathcal{M}} \left[ w_1 \mathcal{C}_{\text{outage}}(a_i, t) + w_2 \mathcal{C}_{\text{latency}}(a_i, t) + w_3 \mathcal{C}_{\text{handover}}(a_i, t) + w_4 \mathcal{C}_{\text{energy}}(a_i, t) + w_5 \mathcal{C}_{\text{resource}}(a_i, t) \right]$$

Subject to:
1. **Outage Reliability SLA**:
   $$P_{\text{outage}}(a_i, t+\Delta) = \mathbb{P}\left(\gamma_{i, a_i}(t+\Delta) < \gamma_{\text{th}}\right) \le \epsilon_{\text{max}} = 10^{-4} \quad (\text{URLLC})$$
2. **End-to-End Latency Constraint**:
   $$T_{\text{latency}}(a_i, t) = T_{\text{prop}}(a_i) + T_{\text{trans}}(a_i, t) + T_{\text{proc}} \le T_{\text{max}}$$
3. **Bandwidth Capacity Constraint**:
   $$\sum_{i: a_i(t) = j} B_{\text{req}, i} \le B_{\text{cap}, j}, \quad \forall j \in \mathcal{N}$$
4. **Orbital Visibility Feasibility**:
   $$\tau_{\text{vis}, i, j}(t) \ge T_{\text{HO\_exec}} + T_{\text{dwell\_min}}, \quad \forall j \in \mathcal{S}$$
5. **Hysteresis Handover Gating**:
   A handover from current node $j_{\text{curr}}$ to target $j_{\text{tgt}}$ is triggered only if:
   $$R_{i, j_{\text{tgt}}}^{\text{adj}}(t+\Delta) - R_{i, j_{\text{curr}}}^{\text{adj}}(t+\Delta) > \Delta_{\text{hysteresis}} + \eta \cdot \mathbb{I}(j_{\text{tgt}} \in \mathcal{S})$$
   preventing catastrophic ping-pong oscillations.

---

## 6. Decision Explainability Logic

Every orchestration choice produces an explainable decision vector:
$$\mathcal{E}_i(t) = \left\{ \text{chosen\_tier}, \, \Delta R^{\text{adj}}, \, \text{predicted\_outage\_risk}, \, \text{uncertainty\_score}, \, \text{gating\_reason} \right\}$$
Categorizing the trigger as:
- `PROACTIVE_SATELLITE_DESCENT`: Handover initiated because $\tau_{\text{vis}} < 15\text{s}$.
- `UNCERTAINTY_AVOIDANCE`: High-SINR LEO rejected due to rain flutter ($U > 4.5\text{ dB}$); fallback to robust HAPS/TBS.
- `CONGESTION_OFFLOAD`: Node load $\rho_j > 0.85$; traffic steered to UAV relay.
- `STEADY_STATE_OPTIMAL`: Current link adheres to all SLA boundaries.

