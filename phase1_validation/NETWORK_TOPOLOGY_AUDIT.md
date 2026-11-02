# ORBIT-INTEL 6G — HETEROGENEOUS NETWORK TOPOLOGY AUDIT

**Document ID**: `ORBIT-INTEL-P1-TOPO-002`  
**Date**: November 2026  
**Status**: VERIFIED & RECONSTRUCTED  
**Git Branch**: `phase1_physical_reconstruction`  

---

## 1. Problem Statement & Audit Finding Retrospective

The original independent scientific audit (`audit_v1/EXECUTIVE_AUDIT_REPORT.md` and `audit_v1/SOURCE_CODE_AUDIT.md`) uncovered a fatal structural flaw in the network topology design:

> **Audit Finding CRIT-01**: In the initial simulation implementation, all 12 simulated user equipments (UEs) were clustered within a tight $4\text{ km} \times 4\text{ km}$ geographic area directly beneath two $20\text{ W}$ Terrestrial Base Stations (`TBS-01` and `TBS-02`). Because terrestrial macrocells offered $+45\text{ dB}$ to $+62\text{ dB}$ SINR and $< 0.01\text{ ms}$ propagation delay, all 12 users attached exclusively to terrestrial nodes or nearby HAPS. The LEO satellite tier carried exactly 0% of the network load. Consequently, satellite communication performance was completely unvalidated, and the reported benchmark gains for NTN orchestration were physically ungrounded.

---

## 2. Reconstructed Heterogeneous SAGIN Topology

In Phase 1, the network geometry was fundamentally redesigned into a realistic Space-Air-Ground Integrated Network (SAGIN) spanning continental urban hubs, suburban transition zones, remote rural valleys, and deep offshore maritime waters.

### 2.1 Network Infrastructure Nodes

| Node ID | Tier | Platform Type | Geographic Coordinates | Altitude | Transmit Power ($P_{\text{tx}}$) | Tx Antenna Gain ($G_{\text{tx}}$) | Bandwidth ($B$) | Coverage Horizon Boundary |
|---|---|---|---|---|---|---|---|---|
| `TBS-01` | **TBS** | Urban Macro Cell Tower | $21.995^\circ\text{ N}, 74.995^\circ\text{ E}$ | $30\text{ m}$ | $43.0\text{ dBm}$ ($20\text{ W}$) | $18.0\text{ dBi}$ | $50\text{ MHz}$ | Cell radius $r \le 2.5\text{ km}$ |
| `TBS-02` | **TBS** | Urban Macro Cell Tower | $22.010^\circ\text{ N}, 75.010^\circ\text{ E}$ | $30\text{ m}$ | $43.0\text{ dBm}$ ($20\text{ W}$) | $18.0\text{ dBi}$ | $50\text{ MHz}$ | Cell radius $r \le 2.5\text{ km}$ |
| `UAV-01` | **UAV** | Tactical Tethered Drone Relay | $22.045^\circ\text{ N}, 75.045^\circ\text{ E}$ | $300\text{ m}$ | $30.0\text{ dBm}$ ($1\text{ W}$) | $12.0\text{ dBi}$ | $20\text{ MHz}$ | Hotspot radius $r \le 3.0\text{ km}$ |
| `HAPS-01` | **HAPS** | Stratospheric Airship / Plane | $22.000^\circ\text{ N}, 75.000^\circ\text{ E}$ | $20.0\text{ km}$ | $38.0\text{ dBm}$ ($6.3\text{ W}$) | $24.0\text{ dBi}$ | $40\text{ MHz}$ | Regional footprint $r \le 25.0\text{ km}$ |
| `SAT-01` | **LEO** | LEO-600 Constellation Sat 1 | Dynamic Orbit (Inc: $53^\circ$, RAAN: $75^\circ$) | $600.0\text{ km}$ | $43.0\text{ dBm}$ ($20\text{ W}$) | $34.0\text{ dBi}$ | $30\text{ MHz}$ | Topocentric elevation $\theta \ge 10.0^\circ$ |
| `SAT-02` | **LEO** | LEO-600 Constellation Sat 2 | Dynamic Orbit (Inc: $53^\circ$, RAAN: $75^\circ$) | $600.0\text{ km}$ | $43.0\text{ dBm}$ ($20\text{ W}$) | $34.0\text{ dBi}$ | $30\text{ MHz}$ | Topocentric elevation $\theta \ge 10.0^\circ$ |

---

## 3. Geographic User Cohort Characterization

The 12 user equipments are strictly divided into 4 realistic operational cohorts based on actual 6G deployment scenarios:

```
[Maritime Waters: 80 - 120 km Offshore] ------------------> UE-10, UE-11, UE-12  ===> ONLY LEO SATELLITE
[Remote Mountains & Rural Valleys: 25 - 40 km] -----------> UE-07, UE-08, UE-09  ===> LEO SATELLITE
[Suburban Expansion & Hotspot: 4 - 9 km] -----------------> UE-04, UE-05, UE-06  ===> UAV Relay & HAPS
[Dense Urban Core: 0 - 2 km] -----------------------------> UE-01, UE-02, UE-03  ===> Terrestrial Base Stations
```

### 3.1 Live Attachment Audit Results

From live simulation snapshot execution (`phase1_validation/USER_ATTACHMENT_DISTRIBUTION.csv`):

| User ID | Operational Cohort | Coordinates (Lat, Lon) | Distance to Hub Center | Primary Attached Node | Primary Tier | Best Link SINR | Alternative Visible Candidates |
|---|---|---|---|---|---|---|---|
| `UE-01` | Urban | $22.005^\circ, 75.005^\circ$ | $0.76\text{ km}$ | `TBS-01` | **TBS** | $+49.1\text{ dB}$ | `HAPS-01` ($22.0\text{ dB}$), `SAT-01` ($3.3\text{ dB}$), `TBS-02` ($7.7\text{ dB}$) |
| `UE-02` | Urban | $21.994^\circ, 74.996^\circ$ | $0.78\text{ km}$ | `TBS-01` | **TBS** | $+46.7\text{ dB}$ | `HAPS-01` ($29.6\text{ dB}$), `SAT-01` ($9.6\text{ dB}$), `TBS-02` ($4.7\text{ dB}$) |
| `UE-03` | Urban | $22.012^\circ, 74.992^\circ$ | $1.57\text{ km}$ | `TBS-02` | **TBS** | $+62.4\text{ dB}$ | `HAPS-01` ($27.0\text{ dB}$), `SAT-01` ($10.3\text{ dB}$) |
| `UE-04` | Suburban | $22.046^\circ, 75.044^\circ$ | $6.9\text{ km}$ | `UAV-01` | **UAV** | $+50.2\text{ dB}$ | `HAPS-01` ($26.4\text{ dB}$), `SAT-01` ($7.0\text{ dB}$) |
| `UE-05` | Suburban | $22.044^\circ, 75.047^\circ$ | $6.8\text{ km}$ | `UAV-01` | **UAV** | $+38.3\text{ dB}$ | `HAPS-01` ($25.3\text{ dB}$), `SAT-01` ($8.0\text{ dB}$) |
| `UE-06` | Suburban | $22.080^\circ, 75.020^\circ$ | $9.1\text{ km}$ | `HAPS-01` | **HAPS** | $+21.6\text{ dB}$ | `SAT-01` ($9.9\text{ dB}$) |
| `UE-07` | Remote/Rural | $22.280^\circ, 75.150^\circ$ | $34.5\text{ km}$ | `SAT-01` | **LEO** | $+19.5\text{ dB}$ | *None (Outside TBS, UAV, HAPS)* |
| `UE-08` | Remote/Rural | $22.320^\circ, 75.250^\circ$ | $43.9\text{ km}$ | `SAT-01` | **LEO** | $+5.2\text{ dB}$ | *None (Outside TBS, UAV, HAPS)* |
| `UE-09` | Remote/Rural | $22.220^\circ, 74.800^\circ$ | $31.8\text{ km}$ | `SAT-01` | **LEO** | $+9.5\text{ dB}$ | *None (Outside TBS, UAV, HAPS)* |
| `UE-10` | Maritime | $22.850^\circ, 75.650^\circ$ | $114.2\text{ km}$ | `SAT-01` | **LEO** | $+6.7\text{ dB}$ | *None (Outside TBS, UAV, HAPS)* |
| `UE-11` | Maritime | $22.950^\circ, 75.800^\circ$ | $134.1\text{ km}$ | `SAT-01` | **LEO** | $+15.7\text{ dB}$ | *None (Outside TBS, UAV, HAPS)* |
| `UE-12` | Maritime | $21.200^\circ, 75.700^\circ$ | $113.6\text{ km}$ | `SAT-01` | **LEO** | $+2.5\text{ dB}$ | *None (Outside TBS, UAV, HAPS)* |

---

## 4. Key Architectural Takeaways

1. **LEO Satellite Tier Genuinely Carries Traffic**: Exactly 6 out of 12 users ($50\%$ of the network population) are attached to `SAT-01`. For these 6 users, satellite connectivity is the sole physical communication medium available.
2. **Realistic Multi-Tier Competition**: In the Urban and Suburban cohorts, multiple technologies compete simultaneously (e.g., `UE-01` sees `TBS-01`, `TBS-02`, `HAPS-01`, and `SAT-01`), enabling realistic multi-attribute orchestration and offloading decisions.
3. **No Artificial Bias**: User attachment is not hardcoded; it is the natural consequence of topocentric visibility geometry, physical radio horizon cutoffs, path loss, and antenna beam gains.
