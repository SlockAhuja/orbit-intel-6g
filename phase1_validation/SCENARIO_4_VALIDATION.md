# ORBIT-INTEL 6G — SCENARIO 4: SATELLITE VISIBILITY DEPARTURE & HANDOVER VALIDATION

**Document ID**: `ORBIT-INTEL-P1-SCEN4-004`  
**Date**: November 2026  
**Status**: VERIFIED & REPRODUCIBLE  
**Associated Dataset**: [`phase1_validation/SATELLITE_VISIBILITY_VALIDATION.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/SATELLITE_VISIBILITY_VALIDATION.csv)  
**Associated Figures**: [`phase1_validation/fig_phase1_satellite_departure.png`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/fig_phase1_satellite_departure.png), [`phase1_validation/fig_phase1_doppler_trajectory.png`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/fig_phase1_doppler_trajectory.png)  

---

## 1. Audit Retrospective & Remediation

The initial audit revealed that Scenario 4 was non-functional:
> "Scenario 4 contained a literal `pass` statement at line 55 of `src/experiments/scenarios.py`, failing to trigger satellite descent, reduce visibility, or evaluate proactive handover mechanisms."

In Phase 1, `apply_scenario_4` was completely redesigned to initialize Keplerian ephemeris parameters such that `SAT-01` actively transits towards the local topocentric horizon and sets below the $10^\circ$ elevation angle, while a rising satellite `SAT-02` enters the field of view.

---

## 2. Chronological Telemetry Breakdown

The live simulation was run for 60 seconds with 1-second sampling. The resulting telemetry confirms four distinct operational regimes:

```
t = 0s                t = 24s                   t = 26s                  t = 34s                t = 60s
  |----------------------|-------------------------|------------------------|----------------------|
SAT-01 Serving       Handover Trigger         SAT-02 Visible           SAT-01 Severed        SAT-02 Serving
elev = 11.65°        rem_vis = 10.0s < 12s    elev = 10.03° > 10°      elev = 9.98° < 10°    elev = 12.01°
rem_vis = 35.0s      (Proactive Alert)        Handover Window Open     is_visible = False    rem_vis = 285s
```

### Phase A: Normal Service with Imminent Departure ($t = 0\text{ s}$ to $t = 23\text{ s}$)
- At $t = 0\text{ s}$, `SAT-01` is serving ground terminals at topocentric elevation $\theta_{\text{elev}} = 11.65^\circ$ with remaining visibility $t_{\text{rem}} = 35.0\text{ s}$ and slant distance $d = 1812.2\text{ km}$.
- Secondary satellite `SAT-02` is below the horizon ($\theta_{\text{elev}} = 8.49^\circ$, $\text{is\_visible} = \text{False}$).
- As `SAT-01` moves along its orbital trajectory, its slant distance increases from $1812\text{ km}$ to $1902\text{ km}$ and carrier Doppler shifts negatively from $-20.8\text{ kHz}$ to $-22.3\text{ kHz}$.

### Phase B: Proactive Handover Trigger Activation ($t = 24\text{ s}$)
- At $t = 24\text{ s}$, `SAT-01` remaining visibility drops to $10.0\text{ s}$, crossing below the $12.0\text{ s}$ CAPRO lookahead safety horizon ($t_{\text{rem}} < 12.0\text{ s}$).
- This physical event signals an immediate proactive handover trigger to the orchestration engine, warning of imminent link termination.

### Phase C: Dual-Satellite Handover Execution Window ($t = 26\text{ s}$ to $t = 33\text{ s}$)
- At $t = 26\text{ s}$, `SAT-02` rises above the minimum elevation horizon ($\theta_{\text{elev}} = 10.03^\circ > 10.0^\circ$, remaining visibility $t_{\text{rem}} = 335.0\text{ s}$, approaching Doppler $+26.95\text{ kHz}$).
- Between $t = 26\text{ s}$ and $t = 33\text{ s}$ (an 8-second overlap window), **both satellites are simultaneously visible**.
- A predictive orchestrator (such as CAPRO) has ample time to pre-allocate radio bearers, exchange handover signaling, and migrate mobile traffic without service interruption.

### Phase D: Physical Link Severance & Single-Link Continuity ($t = 34\text{ s}$ to $t = 60\text{ s}$)
- At $t = 34\text{ s}$, `SAT-01` drops below the minimum elevation threshold ($\theta_{\text{elev}} = 9.98^\circ < 10.0^\circ$).
- Physical line-of-sight is severed: `is_visible` drops to `False`, remaining visibility becomes $0.0\text{ s}$, and path loss is clamped to link disconnection ($220.0\text{ dB}$, $\text{SINR} = -25.0\text{ dB}$).
- `SAT-02` remains fully operational, rising steadily to $\theta_{\text{elev}} = 12.01^\circ$ at $t = 60\text{ s}$ ($285.0\text{ s}$ remaining visibility), providing uninterrupted service to remote and maritime terminals.

---

## 3. Physical Metric Progression Table

Extracted directly from [`phase1_validation/SATELLITE_VISIBILITY_VALIDATION.csv`](file:///C:/Users/OM/OneDrive/Desktop/sem%205/STLC/phase1_validation/SATELLITE_VISIBILITY_VALIDATION.csv):

| Time $t$ | `SAT-01` Elev | `SAT-01` Slant Dist | `SAT-01` Rem Vis | `SAT-01` Doppler | `SAT-01` Vis | `SAT-02` Elev | `SAT-02` Rem Vis | `SAT-02` Doppler | `SAT-02` Vis | Operational State |
|---|---|---|---|---|---|---|---|---|---|---|
| $0\text{ s}$ | $11.65^\circ$ | $1812.2\text{ km}$ | $35.0\text{ s}$ | $-20.80\text{ kHz}$ | **True** | $8.49^\circ$ | $0.0\text{ s}$ | $0.00\text{ kHz}$ | **False** | Nominal Serving Link |
| $10\text{ s}$ | $11.19^\circ$ | $1850.5\text{ km}$ | $25.0\text{ s}$ | $-21.05\text{ kHz}$ | **True** | $9.08^\circ$ | $0.0\text{ s}$ | $0.00\text{ kHz}$ | **False** | Orbital Descent |
| $20\text{ s}$ | $10.67^\circ$ | $1892.5\text{ km}$ | $15.0\text{ s}$ | $-21.95\text{ kHz}$ | **True** | $9.68^\circ$ | $0.0\text{ s}$ | $0.00\text{ kHz}$ | **False** | Approaching Horizon |
| $24\text{ s}$ | $10.48^\circ$ | $1905.8\text{ km}$ | **$10.0\text{ s}$** | $-22.45\text{ kHz}$ | **True** | $9.92^\circ$ | $0.0\text{ s}$ | $0.00\text{ kHz}$ | **False** | **Proactive Handover Trigger** |
| $26\text{ s}$ | $10.38^\circ$ | $1912.6\text{ km}$ | $10.0\text{ s}$ | $-22.70\text{ kHz}$ | **True** | **$10.03^\circ$** | **$335.0\text{ s}$** | $+26.95\text{ kHz}$ | **True** | **Overlap Window Opens** |
| $30\text{ s}$ | $10.18^\circ$ | $1926.3\text{ km}$ | $5.0\text{ s}$ | $-23.19\text{ kHz}$ | **True** | $10.27^\circ$ | $330.0\text{ s}$ | $+26.53\text{ kHz}$ | **True** | Handover Execution |
| $34\text{ s}$ | **$9.98^\circ$** | $1940.3\text{ km}$ | **$0.0\text{ s}$** | $0.00\text{ kHz}$ | **False** | $10.50^\circ$ | $330.0\text{ s}$ | $+26.10\text{ kHz}$ | **True** | **SAT-01 Severed; SAT-02 Serving** |
| $45\text{ s}$ | $9.43^\circ$ | $1980.3\text{ km}$ | $0.0\text{ s}$ | $0.00\text{ kHz}$ | **False** | $11.14^\circ$ | $315.0\text{ s}$ | $+24.85\text{ kHz}$ | **True** | Single-Link Stable Service |
| $60\text{ s}$ | $8.69^\circ$ | $2037.2\text{ km}$ | $0.0\text{ s}$ | $0.00\text{ kHz}$ | **False** | $12.01^\circ$ | $285.0\text{ s}$ | $+22.95\text{ kHz}$ | **True** | Nominal Serving Link |

---

## 4. Conclusion

Scenario 4 is now physically genuine, geometrically exact, and reproducible. It establishes an uncompromised scientific testbed for comparing reactive handovers (which fail at $t = 34\text{ s}$) with proactive confidence-aware orchestration (which safely transitions between $t = 26\text{ s}$ and $t = 33\text{ s}$).
