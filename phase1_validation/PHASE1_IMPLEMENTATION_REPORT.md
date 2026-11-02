# ORBIT-INTEL 6G — PHASE 1: PHYSICAL NETWORK SIMULATOR RECONSTRUCTION REPORT

**Document ID**: `ORBIT-INTEL-P1-REPORT-001`  
**Date**: November 2026  
**Status**: COMPLETED & SCIENTIFICALLY VALIDATED  
**Git Branch**: `phase1_physical_reconstruction`  
**Target Venue**: IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  

---

## 1. Executive Summary

Phase 1 of the Priority Corrections Roadmap addresses the foundational flaws identified in the independent scientific audit (`audit_v1/`). Prior to this phase, the simulation suffered from four critical physical invalidities:
1. **0% Satellite Traffic**: All users were placed within 4 km directly below two 20 W terrestrial base stations, resulting in zero users ever attaching to the LEO satellite tier.
2. **Channel Model Conflation**: The Earth-space propagation model (ITU-R P.618) was incorrectly applied indiscriminately across all network tiers, including terrestrial microcells.
3. **Lumped & Fabricated Latency**: End-to-end latency was calculated as an arbitrary hard-coded composite (~1.84 ms) that violated fundamental physical speed-of-light propagation bounds ($d/c$).
4. **No-Op Scenario 4**: Satellite visibility reduction contained a literal `pass` statement, with no genuine orbital descent or physical link severance.

In Phase 1, the physical simulation environment has been completely reconstructed, scientifically calibrated to 3GPP Release 17/18 NTN specifications, and verified through a 26-test automated suite.

---

## 2. Key Architectural Modifications

### 2.1 Parameter Recalibration (`config/simulation_config.yaml`)
All physical RF, antenna, and orbital parameters have been aligned with 3GPP TR 38.811 (Release 17/18, S-band Set-1 User Equipment and NTN payloads):
- **LEO Satellite**: $P_{\text{tx}} = 43.0\text{ dBm}$ ($20\text{ W}$), $G_{\text{tx}} = 34.0\text{ dBi}$ (steerable multibeam array), Channel Bandwidth $B = 30.0\text{ MHz}$, Carrier Frequency $f_c = 2.0\text{ GHz}$ (S-band MSS). Orbital speed corrected to circular Keplerian $v_{\text{orb}} = 7562\text{ m/s}$ at $h = 600\text{ km}$.
- **HAPS**: $P_{\text{tx}} = 38.0\text{ dBm}$, $G_{\text{tx}} = 24.0\text{ dBi}$, $B = 40.0\text{ MHz}$, Regional Footprint Radius $r = 25.0\text{ km}$, Station altitude $h = 20.0\text{ km}$.
- **UAV**: $P_{\text{tx}} = 30.0\text{ dBm}$, $G_{\text{tx}} = 12.0\text{ dBi}$, $B = 20.0\text{ MHz}$, Tactical Relay Radius $r = 3.0\text{ km}$, Flight altitude $h = 300\text{ m}$.
- **Terrestrial Base Stations (TBS)**: $P_{\text{tx}} = 43.0\text{ dBm}$, $G_{\text{tx}} = 18.0\text{ dBi}$, $B = 50.0\text{ MHz}$, Cell Horizon Radius $r = 2.5\text{ km}$, Antenna height $h = 30\text{ m}$.

### 2.2 Propagation Model Disaggregation (`src/channel_models/propagation.py`)
Each communication tier now utilizes its standard-specific channel formulation:
- **LEO Space-to-Earth**: 3GPP TR 38.811 NTN + ITU-R P.618-13 Earth-space slant path rain attenuation (through $3.5\text{ km}$ rain ceiling) + ITU-R P.676-12 atmospheric gas attenuation + elevation-dependent shadow fading.
- **HAPS Stratosphere-to-Earth**: Stratospheric free-space loss + ITU-R P.618 rain layer attenuation + ITU-R P.676 gas attenuation.
- **UAV Air-to-Ground**: 3GPP TR 36.777 / 38.901 Air-to-Ground Path Loss with probabilistic line-of-sight ($P_{\text{LoS}}(\theta)$) + ITU-R P.530 terrestrial rain attenuation below cloud ceiling.
- **Terrestrial Ground Links**: 3GPP TR 38.901 Urban Macro (UMa) path loss ($PL_{\text{UMa-LoS}}$ and $PL_{\text{UMa-NLoS}}$) + ITU-R P.530-17 terrestrial rain attenuation over ground distance $d \le 2.5\text{ km}$.

### 2.3 Comprehensive Latency Decomposition (`src/simulation_engine/traffic.py`)
Latency accounting has been restructured from arbitrary scalar additions to a rigorous multi-component decomposition:
$$T_{\text{access, one-way}} = T_{\text{prop}} + T_{\text{trans}} + T_{\text{proc}} + T_{\text{queue}}$$
$$T_{\text{e2e, total}} = T_{\text{access, one-way}} + T_{\text{feeder}}$$
$$T_{\text{RTT}} = 2 \cdot T_{\text{prop}} + 2 \cdot T_{\text{trans}} + T_{\text{proc}} + T_{\text{queue}} + 2 \cdot T_{\text{feeder}}$$
where:
- $T_{\text{prop}} = \frac{d_{\text{slant}}}{c}$ strictly enforced by the speed of light ($c = 3.0 \times 10^8\text{ m/s}$).
- $T_{\text{trans}} = \frac{L_{\text{packet}}}{R_{\text{alloc}}}$.
- $T_{\text{proc}}$ calibrated by tier: $2.5\text{ ms}$ (LEO regenerative payload), $1.2\text{ ms}$ (HAPS edge server), $0.8\text{ ms}$ (UAV relay), $0.3\text{ ms}$ (TBS fiber-connected BBU).
- $T_{\text{queue}}$ modeled via M/M/1 queuing approximation: $T_{\text{queue}} = \frac{T_0}{1 - \rho}$.
- $T_{\text{feeder}} = 3.2\text{ ms}$ for LEO (ground station gateway backhaul link, ~960 km slant distance).

### 2.4 Heterogeneous Topology & Multi-Tier Attachment (`src/simulation_engine/network_simulator.py`)
Reconstructed the simulation layout into 4 geographically distributed cohorts (12 total mobile users):
- **Cohort 1 (Urban, UE-01 to UE-03)**: Positioned within $0.5\text{--}1.5\text{ km}$ of `TBS-01` and `TBS-02`. Served by terrestrial macrocells ($>45\text{ dB}$ SINR, sub-millisecond propagation delay).
- **Cohort 2 (Suburban Hotspot, UE-04 to UE-06)**: Positioned $4\text{--}9\text{ km}$ outside the urban core. Served by `UAV-01` relay ($38\text{--}50\text{ dB}$ SINR) and `HAPS-01` ($21.6\text{ dB}$ SINR).
- **Cohort 3 (Remote / Rural, UE-07 to UE-09)**: Positioned $25\text{--}40\text{ km}$ away in rural valleys outside terrestrial and airborne footprints. Served exclusively by `SAT-01` ($5.2\text{--}19.5\text{ dB}$ SINR).
- **Cohort 4 (Maritime / Offshore, UE-10 to UE-12)**: Positioned $80\text{--}120\text{ km}$ offshore in coastal waters. No terrestrial or airborne radio coverage. **100% of maritime traffic is carried by the LEO satellite constellation** ($2.5\text{--}15.7\text{ dB}$ SINR).

### 2.5 Realization of Physical Orbital Departure (`src/experiments/scenarios.py`)
Scenario 4 has been overhauled from a no-op to an active orbital descent:
- `SAT-01` orbital mean anomaly is initialized such that remaining visibility over the ground hub is $35\text{ s}$ at $t = 0\text{ s}$ ($\theta_{\text{elev}} = 11.65^\circ$).
- At $t = 24\text{--}25\text{ s}$, remaining visibility drops below the $12\text{ s}$ threshold, triggering a proactive handover event.
- At $t = 34\text{--}35\text{ s}$, `SAT-01` physically sets below the $10.0^\circ$ minimum elevation threshold, cleanly severing the LoS path ($\text{is\_visible} = \text{False}$).
- Secondary satellite `SAT-02` rises above $10.0^\circ$ at $t = 26\text{ s}$ ($\text{elev} = 10.03^\circ$, remaining visibility $335\text{ s}$), ensuring flawless service continuity.

---

## 3. Evidence of Scientific Validation

All Phase 1 outputs have been generated directly from live simulation runs:
- [`LATENCY_COMPONENT_ANALYSIS.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/LATENCY_COMPONENT_ANALYSIS.csv)
- [`USER_ATTACHMENT_DISTRIBUTION.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/USER_ATTACHMENT_DISTRIBUTION.csv)
- [`SATELLITE_VISIBILITY_VALIDATION.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/SATELLITE_VISIBILITY_VALIDATION.csv)
- [`CHANNEL_MODEL_VALIDATION.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/CHANNEL_MODEL_VALIDATION.csv)
- [Scientific Figure 1: Tier Attachment Distribution](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/fig_phase1_tier_attachment.png)
- [Scientific Figure 2: Latency Decomposition](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/fig_phase1_latency_decomposition.png)
- [Scientific Figure 3: Satellite Departure & Handover Continuity](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/fig_phase1_satellite_departure.png)
- [Scientific Figure 4: Doppler Frequency Dynamics](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/fig_phase1_doppler_trajectory.png)

---

## 4. Acceptance Criteria Compliance Matrix

| # | Master Prompt 03 Acceptance Criterion | Verification Status | Evidence / Location |
|---|---|---|---|
| 1 | WGS-84 coordinate transformation validated | **VERIFIED** | Error < 1 mm in `tests/test_phase1_physical.py::test_wgs84_roundtrip_transformation` |
| 2 | Circular Keplerian orbit kinematics validated | **VERIFIED** | Orbital speed $7562\text{ m/s}$, period $5803\text{ s}$, radius conserved in `test_leo_orbital_kinematics` |
| 3 | Disaggregated propagation models implemented | **VERIFIED** | LEO (P.618), HAPS, UAV, TBS (38.901/P.530) in `src/channel_models/propagation.py` |
| 4 | ITU-R P.618 restricted strictly to Earth-space | **VERIFIED** | Verified in `test_tbs_does_not_apply_itur_p618` and `CHANNEL_MODEL_VALIDATION.csv` |
| 5 | Doppler shift and range rate physically correct | **VERIFIED** | Radial velocity projection with correct approaching/departing signs in `doppler.py` |
| 6 | Latency decomposition enforces $T_{\text{prop}} = d/c$ | **VERIFIED** | One-way propagation strictly $d/c$ in `LATENCY_COMPONENT_ANALYSIS.csv` |
| 7 | Heterogeneous network attachment across tiers | **VERIFIED** | 6 LEO, 1 HAPS, 2 UAV, 3 TBS users in `USER_ATTACHMENT_DISTRIBUTION.csv` |
| 8 | LEO carries traffic for remote/maritime users | **VERIFIED** | 100% of maritime & rural cohorts attached to LEO with viable SINR ($2.5\text{--}19.5\text{ dB}$) |
| 9 | Scenario 4 orbital departure physically validated | **VERIFIED** | $11.65^\circ \to 9.93^\circ$ at $t = 34\text{ s}$ with handover to `SAT-02` in `SATELLITE_VISIBILITY_VALIDATION.csv` |
| 10 | Complete automated test suite passing | **VERIFIED** | 26 / 26 tests passing in pytest (100% pass rate) |

---

## 5. Transition to Phase 2 Recommendation

Phase 1 physical reconstruction is 100% complete, scientifically validated, and documented. The physical foundation is now strictly defensible under rigorous peer review. 

Per Master Prompt 03 instructions, execution is paused here to await explicit user authorization before commencing Phase 2 (ML model retraining, CAPRO rule redesign, and benchmark re-execution).
