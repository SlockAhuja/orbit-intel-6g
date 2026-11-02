# ORBIT-INTEL 6G — PHYSICAL & MATHEMATICAL EQUATION VALIDATION REPORT

**Document ID**: `ORBIT-INTEL-P1-MATH-003`  
**Date**: November 2026  
**Status**: PEER-REVIEW READY  
**Standards Referenced**: WGS-84, 3GPP TR 38.811 Rel-17/18, 3GPP TR 38.901, 3GPP TR 36.777, ITU-R P.618-13, ITU-R P.530-17, ITU-R P.676-12, ITU-R P.838-3  

---

## 1. Orbital and Coordinate Kinematics

### 1.1 WGS-84 Geodetic to ECEF Transformation
The Earth is modeled as an oblate spheroid per WGS-84 with semi-major axis $a = 6378137.0\text{ m}$ and flattening $f = \frac{1}{298.257223563}$.  
First eccentricity squared:
$$e^2 = 2f - f^2 \approx 6.69437999014 \times 10^{-3}$$
The prime vertical radius of curvature $N(\phi)$ at geodetic latitude $\phi$:
$$N(\phi) = \frac{a}{\sqrt{1 - e^2 \sin^2 \phi}}$$
The Earth-Centered Earth-Fixed (ECEF) coordinates for latitude $\phi$, longitude $\lambda$, and ellipsoidal height $h$:
$$x_{\text{ECEF}} = (N(\phi) + h) \cos \phi \cos \lambda$$
$$y_{\text{ECEF}} = (N(\phi) + h) \cos \phi \sin \lambda$$
$$z_{\text{ECEF}} = \left(N(\phi)(1 - e^2) + h\right) \sin \phi$$

*Verification*: Automated round-trip transformation tests (`test_wgs84_roundtrip_transformation`) confirm positional closure error $< 10^{-6}\text{ deg}$ and height error $< 1\text{ mm}$.

### 1.2 Keplerian Circular Orbit Propagation
For a LEO satellite at nominal orbital altitude $h_{\text{orb}} = 600.0\text{ km}$:
Orbital radius: $r = a + h_{\text{orb}} = 6978137.0\text{ m}$.  
Standard gravitational parameter: $\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$.  
Mean motion:
$$n = \sqrt{\frac{\mu}{r^3}} \approx 1.0827 \times 10^{-3}\text{ rad/s}$$
Orbital velocity:
$$v_{\text{orb}} = \sqrt{\frac{\mu}{r}} = n \cdot r \approx 7562.3\text{ m/s}$$
Orbital period:
$$T_{\text{period}} = \frac{2\pi}{n} \approx 5803.2\text{ s} \approx 96.72\text{ min}$$
In orbital plane coordinates, position and velocity at time $t$ with initial mean anomaly $M_0$:
$$x_{\text{orb}} = r \cos(M_0 + n t), \quad y_{\text{orb}} = r \sin(M_0 + n t)$$
$$v_{x,\text{orb}} = -v_{\text{orb}} \sin(M_0 + n t), \quad v_{y,\text{orb}} = v_{\text{orb}} \cos(M_0 + n t)$$
Rotation to ECEF incorporates Earth's diurnal rotation ($\omega_E = 7.2921159 \times 10^{-5}\text{ rad/s}$) through effective right ascension of ascending node $\Omega_{\text{eff}}(t) = \Omega_0 - \omega_E t$ and inclination $i = 53^\circ$:
$$\mathbf{r}_{\text{ECEF}} = \mathbf{R}_z(-\Omega_{\text{eff}}) \mathbf{R}_x(-i) \mathbf{r}_{\text{orb}}$$
Velocity in the rotating ECEF frame includes the Coriolis velocity component:
$$\mathbf{v}_{\text{ECEF}} = \mathbf{v}_{\text{inertial}} - \boldsymbol{\omega}_E \times \mathbf{r}_{\text{ECEF}}$$

### 1.3 Topocentric East-North-Up (ENU) Slant Geometry
Given ground observer position $\mathbf{r}_{\text{user}}$ and target node position $\mathbf{r}_{\text{target}}$:
Relative displacement: $\Delta \mathbf{r} = \mathbf{r}_{\text{target}} - \mathbf{r}_{\text{user}}$, slant range $d = \|\Delta \mathbf{r}\|$.  
The transformation to local topocentric East-North-Up coordinates:
$$\begin{bmatrix} e \\ n \\ u \end{bmatrix} = \begin{bmatrix} -\sin \lambda & \cos \lambda & 0 \\ -\sin \phi \cos \lambda & -\sin \phi \sin \lambda & \cos \phi \\ \cos \phi \cos \lambda & \cos \phi \sin \lambda & \sin \phi \end{bmatrix} \begin{bmatrix} \Delta x \\ \Delta y \\ \Delta z \end{bmatrix}$$
Topocentric elevation angle $\theta_{\text{elev}}$ and azimuth angle $\psi_{\text{az}}$:
$$\theta_{\text{elev}} = \arctan\left(\frac{u}{\sqrt{e^2 + n^2}}\right), \quad \psi_{\text{az}} = \operatorname{atan2}(e, n) \pmod{360^\circ}$$

---

## 2. Disaggregated Propagation Models

### 2.1 Free-Space Path Loss (FSPL)
Applicable across all line-of-sight propagation paths:
$$PL_{\text{FS}}(d, f) = 20 \log_{10}(d) + 20 \log_{10}(f) + 20 \log_{10}\left(\frac{4\pi}{c}\right)$$
For $f = 2.0\text{ GHz}$ and $d = 1000\text{ m}$:
$$PL_{\text{FS}} = 20 \log_{10}(1000) + 20 \log_{10}(2 \times 10^9) + 20 \log_{10}\left(\frac{4\pi}{3.0 \times 10^8}\right) = 98.46\text{ dB}$$

### 2.2 ITU-R P.618-13 Earth-Space Rain Attenuation (LEO & HAPS Only)
Specific attenuation $\gamma_R\text{ (dB/km)}$ from ITU-R P.838:
$$\gamma_R = k \cdot R^{\alpha}$$
where for S-band ($2\text{ GHz}$): $k \approx 0.0001 \cdot f_{\text{GHz}}^{2.2}$, $\alpha \approx 1.25$.  
Slant path length through the tropospheric rain layer ($h_R \approx 3.5\text{ km}$ above ground station):
$$L_s = \frac{h_R - h_s}{\sin \theta_{\text{elev}}}$$
Horizontal reduction factor $r_{0.01}$ accounts for non-uniform rain cell structure:
$$r_{0.01} = \frac{1}{1 + 0.78 \sqrt{\frac{L_s \gamma_R}{f}} - 0.38 (1 - e^{-2 d_G})}$$
where $d_G = L_s \cos \theta_{\text{elev}}$. Effective path length: $d_{\text{eff}} = L_s \cdot r_{0.01}$.  
Total Earth-space rain attenuation:
$$A_{\text{rain, Earth-space}} = \gamma_R \cdot d_{\text{eff}}\text{ dB}$$

*Physical Invariance Verified*: Attenuation increases monotonically as elevation decreases due to the longer slant path through the rain layer ($A_{\text{rain}} = 1.00\text{ dB}$ at $10^\circ$ vs $0.17\text{ dB}$ at $90^\circ$ for $R = 50\text{ mm/h}$).

### 2.3 ITU-R P.530-17 Terrestrial Rain Attenuation (TBS & UAV Below Cloud Base)
For ground base stations and low-altitude UAVs, path length is the actual terrestrial link distance $d_{\text{km}}$ ($d \le 2.5\text{ km}$):
$$d_{\text{eff}} = \frac{d_{\text{km}}}{1 + \frac{d_{\text{km}}}{d_0}}, \quad d_0 = 35 e^{-0.015 R}$$
$$A_{\text{rain, terr}} = \gamma_R \cdot d_{\text{eff}}\text{ dB}$$
For a $1.5\text{ km}$ terrestrial link at $2\text{ GHz}$ under $50\text{ mm/h}$ cloudburst, rain loss is $\approx 0.05\text{ dB}$, correctly contrasting with the multi-kilometer slant attenuation of satellite paths.

### 2.4 3GPP TR 38.901 Urban Macro (UMa) Model (TBS)
For terrestrial base station links with $h_{\text{BS}} = 30\text{ m}$ and $h_{\text{UT}} = 1.5\text{ m}$:
- Line-of-Sight ($d_{2\text{D}} < 800\text{ m}$):
$$PL_{\text{UMa-LoS}} = 28.0 + 22.0 \log_{10}(d_{3\text{D}}) + 20.0 \log_{10}(f_{\text{GHz}})$$
- Non-Line-of-Sight ($d_{2\text{D}} \ge 800\text{ m}$):
$$PL_{\text{UMa-NLoS}} = 13.54 + 39.08 \log_{10}(d_{3\text{D}}) + 20.0 \log_{10}(f_{\text{GHz}}) - 0.6(h_{\text{UT}} - 1.5)$$

---

## 3. Doppler Shift Kinematics

Relative separation range rate:
$$\dot{r} = v_{\text{los}} = (\mathbf{v}_{\text{node}} - \mathbf{v}_{\text{user}}) \cdot \hat{\mathbf{u}}_{\text{los}}$$
where $\hat{\mathbf{u}}_{\text{los}} = \frac{\mathbf{r}_{\text{node}} - \mathbf{r}_{\text{user}}}{\|\mathbf{r}_{\text{node}} - \mathbf{r}_{\text{user}}\|}$.  
The physical carrier Doppler frequency shift:
$$f_d = -\frac{f_c}{c} \dot{r} = -\frac{f_c}{c} v_{\text{los}}$$
- When the satellite approaches the observer ($\dot{r} < 0$), wavefronts compress: $f_d > 0$ (+26.9 kHz at $t=26\text{ s}$ for rising `SAT-02`).
- When the satellite recedes from the observer ($\dot{r} > 0$), wavefronts dilate: $f_d < 0$ (-22.5 kHz at $t=25\text{ s}$ for setting `SAT-01`).

---

## 4. Latency Decomposition Equations

End-to-end latency is decomposed into strictly bounded physical and processing components:
$$T_{\text{prop}} = \frac{d_{\text{slant}}}{c} \times 10^3\text{ ms}$$
$$T_{\text{trans}} = \frac{L_{\text{packet}} \times 8}{R_{\text{alloc}} \times 10^6} \times 10^3\text{ ms}$$
$$T_{\text{queue}} = \frac{T_0}{1 - \rho}, \quad \rho = \min(\text{load}, 0.98)$$
$$T_{\text{proc}} = \begin{cases} 2.5\text{ ms} & \text{LEO (On-board regenerative routing)} \\ 1.2\text{ ms} & \text{HAPS (Stratospheric edge server)} \\ 0.8\text{ ms} & \text{UAV (Airborne tactical relay)} \\ 0.3\text{ ms} & \text{TBS (BBU/CU pool)} \end{cases}$$
$$T_{\text{feeder}} = \begin{cases} 3.2\text{ ms} & \text{LEO (Slant gateway backhaul path)} \\ 0.5\text{ ms} & \text{HAPS (Point-to-point backhaul)} \\ 0.1\text{ ms} & \text{TBS (Terrestrial fiber)} \end{cases}$$
$$T_{\text{e2e, total}} = T_{\text{prop}} + T_{\text{trans}} + T_{\text{proc}} + T_{\text{queue}} + T_{\text{feeder}}$$
$$T_{\text{RTT}} = 2 \cdot T_{\text{prop}} + 2 \cdot T_{\text{trans}} + T_{\text{proc}} + T_{\text{queue}} + 2 \cdot T_{\text{feeder}}$$

*Validation*: Every link in [`LATENCY_COMPONENT_ANALYSIS.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/LATENCY_COMPONENT_ANALYSIS.csv) strictly complies with $T_{\text{prop}} \equiv d/c$ and $T_{\text{RTT}} > 2 T_{\text{prop}}$.
