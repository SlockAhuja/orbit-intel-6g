# PROJECT CONTRIBUTORS & TEAM INFORMATION

**Project Name:** ORBIT-INTEL 6G — Global Network Intelligence & Mission Control Center  
**Full Project Title:** Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks  
**Core Framework:** Confidence-Aware Predictive Reliability Orchestration (CAPRO)  
**Showcase Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  

---

## 1. Project Contributors

The ORBIT-INTEL 6G project is contributed by:

1. **Slock Ahuja**
2. **Dr. Praveen Kumar Sharma**

> **Attribution Policy Notice:** Both contributors are acknowledged equally as the official project contributors. In accordance with strict conference integrity policies, no fabricated academic affiliations, invented corporate titles, degrees, or student designations have been introduced.

---

## 2. Shared Research Roles & Contributions

### 1. Slock Ahuja
- **Research Software Architecture:** Conceived, implemented, and benchmarked the full-stack simulation, forecasting, and real-time visualization platform.
- **CAPRO Orchestration Algorithm:** Co-designed the Confidence-Aware Predictive Reliability Orchestration framework, integrating risk-adjusted utility functions and hard URLLC reliability constraints.
- **Physical Modeling & 3GPP Simulation:** Implemented the 4-tier Space-Air-Ground Integrated Network (SAGIN) simulator including Keplerian orbital mechanics, ITU-R P.618 rain fading, and speed-of-light propagation bounds.
- **Mission Control Visualization:** Engineered the Three.js 3D Earth, interactive telemetry overlays, raycasted hover tooltips, and presentation mode controls for IEEE STLC 2026.

### 2. Dr. Praveen Kumar Sharma
- **Theoretical Formulation & Scientific Guidance:** Provided rigorous scientific oversight on non-terrestrial network (NTN) propagation physics, 3GPP Release 17/18 NTN standards, and reliability-aware resource allocation.
- **Dual-Uncertainty AI Framework:** Guided the mathematical formulation of conformal quantile regression and the decomposition of prediction variance into epistemic model uncertainty and aleatoric channel flutter.
- **Experimental Methodology & Verification:** Supervised the 400-run Monte Carlo experimental validation, statistical benchmark comparisons against reactive and threshold baselines, and independent audit compliance.

---

## 3. Project Identity in Application Interfaces

The project identity is prominently integrated into every user-facing layer:
- **Mission Control Web Header:** Top navigation display: `PROJECT CONTRIBUTORS: Slock Ahuja | Dr. Praveen Kumar Sharma`.
- **"About the Project & Team" Modal (`#about-modal-backdrop`):** Interactive modal presenting the project's background, contributors, core innovation, and conference venue.
- **REST API Endpoint (`/api/team`):** Machine-readable endpoint returning exact contributor names and conference metadata.
- **Automated Regression Suite (`tests/test_mission_control_web.py`):** Verified by `test_team_attribution_endpoint` ensuring persistent attribution integrity.
