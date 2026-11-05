# ORBIT-INTEL 6G — URLLC PACKET LIFECYCLE & SLA VALIDATION REPORT

**Document ID**: `ORBIT-INTEL-CLARIF-URLLC-003`  
**Date**: November 2026  
**Status**: APPROVED & CANONICAL  
**Associated Dataset**: [`phase1_final_clarifications/URLLC_PACKET_LIFECYCLE_ANALYSIS.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_final_clarifications/URLLC_PACKET_LIFECYCLE_ANALYSIS.csv)  

---

## 1. Executive Summary & Core Physical Distinction

An independent audit of the packet lifecycle for Ultra-Reliable Low-Latency Communication (URLLC) users attached to the LEO satellite tier (`UE-07`, `UE-10`, `UE-12`) reveals a crucial scientific distinction:

> **Core Physical Reality**: Packets for `UE-07`, `UE-10`, and `UE-12` are **physically decodable and received with strong positive SINR** ($+3.3\text{ dB}$ to $+16.0\text{ dB}$ against a $+3.0\text{ dB}$ threshold). However, they are **explicitly discarded by an application-level SLA deadline filter** because the true end-to-end latency ($11.66\text{--}12.50\text{ ms}$) strictly exceeds the configured $10.0\text{ ms}$ URLLC deadline.

This is **not a packet-loss bug or routing failure**; it is the direct physical consequence of speed-of-light propagation over a $1500\text{--}1650\text{ km}$ slant path.

---

## 2. Complete Packet Lifecycle Trace

The complete end-to-end traversal of a URLLC packet is structured as follows:

```
[UE-07 / UE-10 / UE-12 Handheld Terminal]
      | (Packet generated: 256 bytes payload, Timestamp t)
      v
[Air Access Link: Slant range 1500 - 1650 km]
      | Propagation Delay: T_prop = d / c = 5.05 - 5.42 ms (Speed of light)
      | Transmission Delay: T_trans = 256 bytes * 8 / 5.0 Mbps = 0.4096 ms
      v
[LEO Satellite Payload: Regenerative Architecture]
      | Processing Delay: T_proc = 2.50 ms (On-board header parsing, demodulation, routing)
      | Queuing Delay: T_queue = 0.50 / (1 - 0.35) = 0.7692 ms (M/M/1 queue)
      v
[Feeder Gateway Backhaul Link: Slant range ~960 km]
      | Feeder Delay: T_feeder = 3.20 ms (Slant backhaul to optical/Ka ground station gateway)
      v
[Total End-to-End Latency at 6G Core Gateway: 11.66 - 12.03 ms]
      |
      +---> Check: Total Latency (12.02 ms) > Configured SLA Deadline (10.0 ms)?
      |
      v
[Application-Level SLA Deadline Filter: TrafficEngine.evaluate_packet_success]
      ===> DISCARDED DUE TO LATENCY SLA TIMEOUT (> 10.0 ms)
```

---

## 3. User-Specific Latency Variations

The end-to-end delay is not a uniform lumped constant; it varies dynamically with each user's exact topocentric slant range:

| User ID | Operational Cohort | Slant Distance ($d$) | $T_{\text{prop}}$ ($d/c$) | $T_{\text{feeder}}$ | $T_{\text{proc}}$ | $T_{\text{queue}}$ | $T_{\text{trans}}$ | Total One-Way Latency | Configured SLA | Discard Policy |
|---|---|---|---|---|---|---|---|---|---|---|
| `UE-07` | Remote / Rural Valley | $1625.9\text{ km}$ | $5.42\text{ ms}$ | $3.20\text{ ms}$ | $2.50\text{ ms}$ | $0.50\text{ ms}$ | $0.41\text{ ms}$ | **$12.03\text{ ms}$** | $10.0\text{ ms}$ | **Discard: SLA Timeout** |
| `UE-10` | Maritime Offshore Hub | $1623.0\text{ km}$ | $5.41\text{ ms}$ | $3.20\text{ ms}$ | $2.50\text{ ms}$ | $0.50\text{ ms}$ | $0.41\text{ ms}$ | **$12.02\text{ ms}$** | $10.0\text{ ms}$ | **Discard: SLA Timeout** |
| `UE-12` | Coastal Maritime Deep | $1516.2\text{ km}$ | $5.05\text{ ms}$ | $3.20\text{ ms}$ | $2.50\text{ ms}$ | $0.50\text{ ms}$ | $0.41\text{ ms}$ | **$11.66\text{ ms}$** | $10.0\text{ ms}$ | **Discard: SLA Timeout** |

---

## 4. Contrast with Enhanced Mobile Broadband (eMBB)

In contrast, eMBB users (`UE-08`, `UE-09`, `UE-11`) attached to the identical `SAT-01` satellite experience identical propagation and feeder delays ($T_{\text{e2e}} \approx 12.2\text{ ms}$), but because eMBB enforces a latency budget of `max_latency_ms = 50.0 ms`, **zero packets are discarded by the SLA filter**, achieving $70.5\%\text{--}78.2\%$ Packet Delivery Ratio.

---

## 5. 3GPP Rel-17/18 NTN Standards Alignment

This finding directly reflects international telecommunication standards:
1. **3GPP TR 38.821 (Solutions for NR to support NTN)**: Section 6.2 acknowledges that typical one-way access-plus-feeder propagation for a $600\text{ km}$ LEO constellation ranges from $6\text{--}15\text{ ms}$.
2. **Extreme URLLC (<10 ms) over NTN**: Cannot be realized over bent-pipe or feeder-ground-station architectures without on-board Edge Computing (MEC) deployed directly on the satellite payload.
3. **Research Significance**: This behavior demonstrates that the simulator enforces strict physical speed-of-light constraints and realistic multi-attribute SLA policies.

