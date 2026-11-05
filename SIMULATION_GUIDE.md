# ORBIT-INTEL 6G — SIMULATION & EXPERIMENTATION GUIDE

## 1. Network Simulation Architecture

The simulation engine (`src/simulation_engine/network_simulator.py`) implements a discrete-time, physics-based Space-Air-Ground Integrated Network (SAGIN) operating in discrete epochs ($\Delta t = 1.0\text{ s}$).

### Node Specifications:
1. **LEO Satellites (SAT-01, SAT-02):**
   - Altitude: $600\text{ km}$
   - Orbital Inclination: $53^\circ$
   - Velocity: $\approx 7.56\text{ km/s}$
   - Frequency: S-band ($2.0\text{ GHz}$)
   - Transmit Power: $43.0\text{ dBm}$
   - Min. Elevation Angle: $10^\circ$
2. **HAPS Platform (HAPS-01):**
   - Altitude: $20\text{ km}$ (Stratosphere)
   - Velocity: $0.0\text{ km/s}$ (Quasi-stationary)
   - Transmit Power: $38.0\text{ dBm}$
   - Min. Elevation Angle: $5^\circ$
3. **UAV Relay (UAV-01):**
   - Altitude: $300\text{ m}$ (Airborne loiter)
   - Coverage Radius: $3.0\text{ km}$
   - Transmit Power: $30.0\text{ dBm}$
4. **Terrestrial Base Stations (TBS-01, TBS-02, TBS-03):**
   - Antenna Height: $30\text{ m}$
   - Cell Radius: $2.5\text{ km}$
   - Inter-Site Distance: $1.5\text{ km}$
   - Transmit Power: $46.0\text{ dBm}$

---

## 2. Experimental Scenarios

1. **Scenario 1: Normal Conditions**
   - Clear sky ($R = 0\text{ mm/h}$), nominal traffic ($5\text{ Mbps}$ URLLC, $20\text{ Mbps}$ eMBB).
2. **Scenario 2: Traffic Congestion Surge**
   - Congestion surge at $t = 20\text{ s}$ pushing terrestrial loads to capacity limits.
3. **Scenario 3: Sudden Rain Degradation**
   - Convective storm cloudburst ($R = 55\text{ mm/h}$) active from $t = 25\text{ s}$ to $55\text{ s}$.
4. **Scenario 4: Satellite Visibility Handover**
   - SAT-01 departs below $10^\circ$ elevation at $t \approx 35\text{ s}$; SAT-02 ascends above horizon.
5. **Scenario 5: High Uncertainty Flutter**
   - Volatile shadow fading flutter ($\sigma_{\text{flutter}} = 4.0\text{ dB}$) testing uncertainty awareness.

---

## 3. Benchmarked Orchestration Paradigms

1. **M1 (Reactive Baseline):** Triggered when link drops below $3.0\text{ dB}$; attaches greedily to instantaneous strongest node.
2. **M2 (Threshold-Predictive):** First-order linear trend extrapolation over a 5-second sliding window.
3. **M3 (Point-Prediction):** Gradient boosting point forecast ($\hat{q}_{50}$) without uncertainty bounds or latency gating.
4. **M4 (Proposed CAPRO):** Confidence-aware predictive orchestration with dual uncertainty, normalized utility, and hysteresis gating.
