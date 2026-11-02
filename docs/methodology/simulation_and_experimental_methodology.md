# ORBIT-INTEL 6G: Simulation and Experimental Methodology

## 1. Simulation Design Principles

The simulation framework models a realistic Space-Air-Ground Integrated Network (SAGIN) over continuous and discrete time:
- **Simulation Time Step**: $\delta t = 1.0\text{ s}$ for orbital kinematics and channel updates; micro-steps for discrete packet events.
- **Orbital Propagation**: Simulates Walker-Delta LEO constellation orbits with inclination $i = 53^\circ$, altitude $h = 600\text{ km}$, orbital period $T \approx 96.7\text{ min}$, and orbital speed $v \approx 7.56\text{ km/s}$.
- **Ground Coordinates**: Reference ground stations and mobile user terminals located across realistic latitude/longitude geographic regions (e.g., $18^\circ\text{--}28^\circ\text{ N}$, $72^\circ\text{--}80^\circ\text{ E}$).
- **Elevation Gating**: Minimum elevation angle for satellite communication is $\theta_{\text{min}} = 10^\circ$. Visibility duration $\tau_{\text{vis}}$ is computed dynamically based on ground-track geometry.

---

## 2. Experimental Scenarios

To ensure rigorous benchmarking, five distinct operational scenarios are defined:

1. **Scenario 1 — Normal Communication Conditions**:
   - Nominal traffic demand ($2\text{--}10\text{ Mbps}$ per user).
   - Clear sky / standard atmospheric absorption.
   - Smooth satellite pass with predictable Doppler profile.
2. **Scenario 2 — High Traffic & Network Congestion**:
   - Traffic bursts up to $50\text{ Mbps}$ per user exceeding base station capacities.
   - Node utilization $\rho_j > 85\%$.
   - Requires intelligent tier offloading (UAV/HAPS).
3. **Scenario 3 — Sudden Link Degradation**:
   - Localized ITU-R P.618 heavy convective rain cells ($R = 50\text{ mm/h}$) causing sharp $10\text{--}15\text{ dB}$ attenuation on satellite links.
   - Sudden physical blockage / shadowing.
4. **Scenario 4 — Satellite Visibility Reduction & Handover**:
   - Primary LEO satellite descends below $10^\circ$ elevation.
   - Remaining visibility $\tau_{\text{vis}} < 15\text{ s}$.
   - Tests proactive vs. reactive handover timing and packet loss.
5. **Scenario 5 — High Uncertainty & Rapid Channel Flutter**:
   - Highly dynamic multi-path fast fading, mixed weather, and high Doppler rate ($\dot{f}_d$).
   - AI prediction variance $U$ escalates sharply.
   - Tests whether algorithms avoid committing to deceptively high-gain but volatile links.

---

## 3. Evaluated Methods (M1 - M4)

1. **M1: Reactive Baseline**:
   - Re-evaluates serving tier at $t$ based strictly on current SINR $\gamma(t)$.
   - Switches when another node is $\Delta_{\text{react}}$ dB better.
   - No forward lookahead; blind to impending satellite disappearance or incoming rain cells.
2. **M2: Threshold-Based Predictive**:
   - Uses linear or fixed-threshold extrapolation of SINR trend.
   - Initiates handover if predicted SINR drops below static threshold $\gamma_{\text{th}} = 10\text{ dB}$.
   - Ignores uncertainty and network capacity constraints.
3. **M3: Prediction-Only AI**:
   - Uses trained ML model to forecast $\hat{Q}(t+\Delta)$.
   - Selects tier maximizing $\hat{Q}(t+\Delta)$ without uncertainty penalty ($U = 0$).
   - Prone to catastrophic misallocation when prediction error is high.
4. **M4: Proposed CAPRO**:
   - Combines multi-step prediction $\hat{Q}(t+\Delta)$ with calibrated uncertainty $U(t+\Delta)$.
   - Evaluates risk-adjusted utility $R^{\text{adj}} = \hat{Q} - \kappa \cdot U$.
   - Enforces proactive orbital lookahead, hysteresis gating, and SLA compliance.

---

## 4. Key Performance Indicators (KPIs)

- **Packet Delivery Ratio (PDR, %)**: Total successfully delivered packets over generated packets.
- **End-to-End Latency (ms)**: Total propagation + transmission + queuing delay.
- **Throughput (Mbps)**: Total delivered data per unit time.
- **Outage Probability ($P_{\text{outage}}$)**: Fraction of time epochs where SINR drops below connection threshold ($3\text{ dB}$).
- **Handover Failure Rate (%)**: Ratio of failed handovers (due to insufficient target resources or premature loss) to total handover attempts.
- **Handover Frequency (count/min)**: Number of tier switches per minute (lower is better to avoid signaling storms).
- **Resource Utilization Efficiency (%)**: Balanced load distribution across active nodes.
- **Energy Consumption (Joules/Mbit)**: Energy expended per megabit successfully delivered.
- **Prediction MAE & RMSE (dB)**: Accuracy of link-quality forecaster.
- **Calibration Quality (ECE & PICP)**: Reliability and validity of prediction intervals.

