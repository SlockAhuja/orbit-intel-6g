# ORBIT-INTEL 6G: Physical and Mathematical Model Audit

---

## 1. Orbital Mechanics and Kinematic Geometry

### 1.1. WGS-84 Coordinate Transformations
- **Source**: `src/simulation_engine/orbital.py` (lines 20–74).
- **Mathematical Specification**:
  - Semi-major axis: $a = 6378137.0\text{ m}$.
  - Flattening: $f = 1 / 298.257223563$.
  - Eccentricity: $e^2 = 2f - f^2 \approx 6.69437999 \times 10^{-3}$.
  - Radius of curvature in prime vertical: $N(\phi) = \frac{a}{\sqrt{1 - e^2 \sin^2\phi}}$.
- **Independent Verification**:
  - Conversion of test coordinate $(23.5^\circ\text{ N}, 78.2^\circ\text{ E}, 550.0\text{ m})$ to ECEF and inverse conversion back to Geodetic yielded an error of $< 10^{-5}$ degrees in latitude/longitude and $< 0.01\text{ m}$ in altitude.
- **Audit Verdict**: **VERIFIED (Mathematically Exact)**.

### 1.2. Keplerian Circular Orbit Propagator
- **Source**: `src/simulation_engine/orbital.py` (lines 115–185).
- **Physical Derivation**:
  - Orbital radius: $r = R_E + h = 6378137.0 + 600000.0 = 6978137.0\text{ m}$.
  - Standard gravitational parameter: $\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$.
  - Mean orbital velocity:
    $$v_{\text{LEO}} = \sqrt{\frac{\mu}{r}} = \sqrt{\frac{3.986004418 \times 10^{14}}{6978137.0}} \approx 7562.2\text{ m/s} \quad (7.56\text{ km/s})$$
  - Orbital period:
    $$T = \frac{2\pi}{\sqrt{\mu / r^3}} = 2\pi \sqrt{\frac{(6978137.0)^3}{3.986004418 \times 10^{14}}} \approx 5797.7\text{ s} \quad (96.63\text{ minutes})$$
  - Earth rotation coupling: $\omega_E = 7.2921159 \times 10^{-5}\text{ rad/s}$ correctly rotates the Greenwich meridian under the orbit.
- **Audit Verdict**: **VERIFIED (Physically Sound)**.

### 1.3. Topocentric Elevation Angle & Slant Range
- **Source**: `src/simulation_engine/orbital.py` (lines 76–112).
- **Equation**:
  $$\vec{r}_{\text{ENU}} = \mathbf{R}_{\text{ECEF}\to\text{ENU}}(\phi, \lambda) \cdot (\vec{r}_{\text{sat}} - \vec{r}_{\text{user}})$$
  $$\theta = \arctan\left(\frac{U}{\sqrt{E^2 + N^2}}\right)$$
- **Numerical Check**: A target placed directly overhead ($U = 500\text{ km}, E=0, N=0$) produces $\theta = 90.0^\circ$. A target at the local horizon ($U=0$) produces $\theta = 0.0^\circ$.
- **Audit Verdict**: **VERIFIED**.

---

## 2. Radio Frequency Channel & Propagation Modeling

### 2.1. Free Space Path Loss (FSPL)
- **Source**: `src/channel_models/propagation.py` (lines 18–34).
- **Equation**:
  $$\mathrm{FSPL}(d, f_c) = 20\log_{10}(d) + 20\log_{10}(f_c) + 20\log_{10}\left(\frac{4\pi}{c}\right)$$
- **Independent Verification**:
  - Carrier frequency $f_c = 2.0\text{ GHz}$, distance $d = 1000\text{ km} = 10^6\text{ m}$:
    $$\mathrm{FSPL} = 20\log_{10}(10^6) + 20\log_{10}(2 \times 10^9) + 20\log_{10}\left(\frac{4\pi}{3 \times 10^8}\right) = 120 + 186.02 - 147.56 = 158.46\text{ dB}$$
  - The implementation yields $158.464\text{ dB}$.
- **Audit Verdict**: **VERIFIED**.

### 2.2. Atmospheric Gas Absorption (ITU-R P.676)
- **Source**: `src/channel_models/propagation.py` (lines 36–55).
- **Model**: Simplified ITU-R P.676 obliquity formula with frequency-dependent zenith attenuation:
  $$A_{\text{atm}}(\theta, f) = \frac{A_0(f)}{\sin\theta + \frac{0.01}{\sqrt{\sin^2\theta + 0.002}}}$$
- **Finding**: Zenith attenuation $A_0(f)$ includes a synthetic resonance term for the $22.2\text{ GHz}$ water vapor line. At $2.0\text{ GHz}$ (S-band), $A_0 \approx 0.035\text{ dB}$, producing an atmospheric attenuation of $\sim 0.2\text{ dB}$ at $\theta = 10^\circ$, which is standard for clear atmosphere.
- **Audit Verdict**: **VERIFIED (Simplified Approximation)**.

### 2.3. Rain Attenuation (ITU-R P.618-13)
- **Source**: `src/channel_models/propagation.py` (lines 57–95).
- **Equation**:
  $$\gamma_R = k \cdot R^{\alpha} \quad (\text{dB/km})$$
  $$d_{\text{eff}} = \frac{h_{\text{rain}} - h_{\text{station}}}{\sin\theta} \cdot r_{0.01}$$
- **CRITICAL FLAW IDENTIFIED**:
  In `src/simulation_engine/network_simulator.py` (line 237), this model is called for **ALL** active nodes:
  - For a satellite at $\theta = 30^\circ$, $d_{\text{eff}} \approx \frac{3.5}{\sin 30^\circ} \times 0.8 = 5.6\text{ km}$, yielding $\sim 3\text{--}15\text{ dB}$ rain attenuation depending on $R$. This is physically correct for Earth-space links.
  - However, for a Terrestrial Base Station (TBS) located on a $30\text{ m}$ tower with user distance $1.5\text{ km}$, the elevation angle is $\theta \approx 0.6^\circ$. Substituting $\theta = 0.6^\circ$ into the ITU-R P.618 formula forces slant path $d_{\text{slant}} = \frac{3.5}{\sin 0.6^\circ} \approx 334\text{ km}$! Even with clipping ($r_{0.01} \ge 0.2$), effective path length is computed as $>60\text{ km}$ through rain for a $1.5\text{ km}$ terrestrial link!
- **Audit Verdict**: **INCORRECT (Misapplication of Recommendation)**.
  - *Correction*: ITU-R P.618 applies strictly to satellite paths where the wave traverses the troposphere from space. Ground links must use ITU-R P.530 where $d_{\text{eff}} = d_{\text{horizontal}} \cdot r$.

### 2.4. Doppler Shift Physics
- **Source**: `src/channel_models/doppler.py` (lines 35–65).
- **Equation**:
  $$v_{\text{los}} = (\vec{v}_{\text{sat}} - \vec{v}_{\text{user}}) \cdot \frac{\vec{r}_{\text{sat}} - \vec{r}_{\text{user}}}{\|\vec{r}_{\text{sat}} - \vec{r}_{\text{user}}\|}$$
  $$f_d = f_c \frac{v_{\text{los}}}{c}$$
- **Numerical Check**: At $v_{\text{los}} = 7.2\text{ km/s} = 7200\text{ m/s}$ and $f_c = 2.0\text{ GHz}$:
  $$f_d = 2 \times 10^9 \times \frac{7200}{3 \times 10^8} = 48000\text{ Hz} \quad (48\text{ kHz})$$
  The implementation matches theoretical physics exactly.
- **Audit Verdict**: **VERIFIED**.

---

## 3. Investigation of the 1.84 ms Reported Latency

### 3.1. The Physical Paradox
In the previous report, ORBIT-INTEL 6G claimed:
> *"CAPRO maintains top reliability (99.89% PDR) with an average end-to-end latency of approximately 1.84 ms."*

**Theoretical Lower Bound for LEO Satellite Communications**:
- Altitude: $h = 600\text{ km}$.
- Slant distance at $10^\circ$ elevation:
  $$d_{\text{slant}} = \sqrt{(R_E + h)^2 - R_E^2 \cos^2\theta} - R_E \sin\theta \approx 1849\text{ km}$$
- One-way speed-of-light propagation delay:
  $$T_{\text{prop, one-way}} = \frac{1849 \times 10^3\text{ m}}{3 \times 10^8\text{ m/s}} \approx 6.16\text{ ms}$$
- Two-way Round-Trip Time (RTT):
  $$T_{\text{prop, RTT}} = 2 \times 6.16\text{ ms} = 12.32\text{ ms}$$
- Even at zenith ($\theta = 90^\circ$, $d = 600\text{ km}$), one-way propagation delay is:
  $$T_{\text{prop, zenith}} = \frac{600 \times 10^3\text{ m}}{3 \times 10^8\text{ m/s}} = 2.00\text{ ms}$$

### 3.2. Why Did the Code Report 1.84 ms?
An audit of `src/experiments/benchmark_runner.py` and node selection telemetry revealed:
1. In `src/simulation_engine/traffic.py` (lines 20–40):
   ```python
   t_prop_ms = (slant_distance_m / self.c) * 1000.0
   t_proc_ms = tier_proc_map.get(tier, 1.0)  # TBS: 0.3 ms, HAPS: 1.2 ms, LEO: 2.5 ms
   t_queue_ms = base_queue_ms / (1.0 - rho)  # ~ 0.5 ms
   t_total_ms = t_prop_ms + t_trans_ms + t_queue_ms + t_proc_ms
   ```
   The formula in `traffic.py` is physically correct.
2. **The Root Cause**: Users were **NEVER CONNECTED** to the LEO satellite!
   - `UE-01` through `UE-12` were located at ground coordinates $(22.0^\circ \pm 0.04^\circ, 75.0^\circ \pm 0.04^\circ)$, within $1.5\text{--}3.5\text{ km}$ of `TBS-01` and `TBS-02`, and beneath `HAPS-01` ($20\text{ km}$).
   - `TBS-01` offered $+46.7\text{ dB}$ SINR and propagation delay $< 0.01\text{ ms}$.
   - Total latency for TBS was: $T_{\text{prop}}(0.01) + T_{\text{trans}}(0.03) + T_{\text{proc}}(0.3) + T_{\text{queue}}(0.5) \approx 0.84\text{ ms}$.
   - Total latency for HAPS was: $T_{\text{prop}}(0.07) + T_{\text{trans}}(0.03) + T_{\text{proc}}(1.2) + T_{\text{queue}}(0.5) \approx 1.80\text{ ms}$.
   - Total latency for LEO (if connected) would have been: $T_{\text{prop}}(6.16) + T_{\text{trans}}(0.03) + T_{\text{proc}}(2.5) + T_{\text{queue}}(0.5) \approx 9.19\text{ ms}$.

### 3.3. Audit Finding on Delay
- **Finding**: The reported $1.84\text{ ms}$ latency is physically correct for a terrestrial and stratospheric network, but **completely misrepresents satellite NTN latency**.
- **Scientific Impact**: Claiming that ORBIT-INTEL 6G delivers satellite LEO communications at $1.84\text{ ms}$ latency is physically false and violates fundamental relativistic physics ($c = 3 \times 10^8\text{ m/s}$). In reality, the orchestrator bypassed the satellite tier entirely.

