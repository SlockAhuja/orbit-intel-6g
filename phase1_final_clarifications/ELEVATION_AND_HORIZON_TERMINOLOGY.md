# ORBIT-INTEL 6G — ELEVATION AND HORIZON TERMINOLOGY STANDARDIZATION

**Document ID**: `ORBIT-INTEL-CLARIF-ELEV-001`  
**Date**: November 2026  
**Status**: APPROVED & CANONICAL  
**Scope**: Definitive clarification of topocentric elevation terms, geometric horizon limits, and operational elevation masks.  

---

## 1. Definitive Terminology Standards

To eliminate ambiguity across all research documentation, simulation metrics, and publication figures, the following four terms are strictly distinguished:

| Term | Mathematical Definition | Physical Meaning in SAGIN / NTN | Status in Simulator |
|---|---|---|---|
| **Geometric Horizon** | $\theta_{\text{elev}} = 0.0^\circ$ | The tangent plane to the local oblate WGS-84 reference ellipsoid at the observer's geodetic position. Line-of-sight is geometrically blocked by the curvature of the Earth when $\theta < 0^\circ$. | Physical limit of Earth geometry. |
| **Minimum Operational Elevation Mask** | $\theta_{\text{elev}} = 10.0^\circ$ | The international 3GPP TR 38.811 and ITU-R operational threshold below which satellite-to-handheld radio links are excluded due to excessive multipath, building blockage, and long tropospheric slant attenuation. | Configured simulation eligibility threshold (`min_elevation_deg = 10.0`). |
| **Geometrically Visible** | $\theta_{\text{elev}} \ge 0.0^\circ$ | A direct mathematical straight line connects the ground terminal and satellite without intersecting the WGS-84 Earth ellipsoid. | Necessary condition, but insufficient for bearer scheduling. |
| **Operationally Eligible** | $\theta_{\text{elev}} \ge 10.0^\circ$ and $t_{\text{rem}} > 0.0\text{ s}$ | The satellite satisfies both the geometric horizon and the minimum operational elevation mask, making it eligible for radio bearer allocation and user traffic. | Required condition for active service attachment. |

---

## 2. Clarification of Scenario 4 Trajectory

In Scenario 4, `SAT-01` orbital descent across $t \in [0, 60]\text{ s}$ exhibits the following exact elevation states:

```
t = 0s:  theta = 11.642°  ===> Geometrically Visible & Operationally Eligible (Above 10° Mask)
t = 24s: theta = 10.518°  ===> Operationally Eligible; Proactive Warning Trigger (rem_vis = 10s < 12s)
t = 34s: theta = 10.022°  ===> Operationally Eligible; Last Active Service Second
t = 35s: theta = 9.971°   ===> GEOMETRICALLY VISIBLE (> 0°), but BELOW OPERATIONAL MASK (< 10°)
t = 60s: theta = 8.688°   ===> GEOMETRICALLY VISIBLE (> 0°), but BELOW OPERATIONAL MASK (< 10°)
```

### Specific Clarifications
1. **SAT-01 does NOT set below the geometric horizon at $t = 35\text{ s}$**: At $t = 35\text{ s}$, `SAT-01` has an elevation angle of $9.971^\circ$, which is well above the $0^\circ$ geometric horizon. It remains geometrically above the horizon throughout the entire 60-second scenario.
2. **Operational Eligibility Drops to False at $t = 35\text{ s}$**: Because `SAT-01` breaches the $10.0^\circ$ minimum operational elevation mask ($\theta < 10.0^\circ$), the simulator sets `is_visible = False`, terminating radio link eligibility.
3. **No Orbital Mechanics Alteration**: The physical orbital kinematics are completely valid and unaltered; only the descriptive terminology has been refined from "crossing the physical horizon" to **"crossing below the 10° minimum operational elevation mask."**
