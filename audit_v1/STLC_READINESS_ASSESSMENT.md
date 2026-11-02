# ORBIT-INTEL 6G: STLC Tunisia 2026 Readiness Assessment

**Conference**: IEEE Communications Society (ComSoc) Student Tech Leadership Conference (STLC)  
**Location**: Tunisia 2026  
**Auditor**: Independent Senior Scientific and Technical Audit Panel  
**Evaluation Target**: Student Project Showcase, Oral Technical Presentation, and Live Software Demonstration  

---

## 1. Overall Audit Verdict & Category Determination

### **Overall Project Rating: CATEGORY C — Major Revision Required**

The project embodies sophisticated software engineering and an elegant, modern architecture. However, due to critical scientific shortcuts (hard-coded publication figures, temporal data leakage in predictive models, dimensionally inconsistent cost functions, and experimental scenarios where the satellite tier was completely starved of user traffic), the current scientific claims are **not defensible before an international IEEE ComSoc technical committee**.

---

## 2. Track-by-Track Readiness Decisions

```
+-----------------------------------------------------------------------------------------+
|                               TRACK READINESS MATRIX                                    |
+------------------------------------+--------------------------+-------------------------+
| Track / Target Venue               | Decision                 | Primary Blocker         |
+------------------------------------+--------------------------+-------------------------+
| 1. STLC Student Project Showcase   | CONDITIONALLY VIABLE     | Needs figure & scenario |
|                                    | (Pending Phase 1 Fixes)  | corrections             |
| 2. Live Interactive Demo Session   | READY WITH CAVEATS       | Demo operates smoothly  |
|                                    |                          | but Page 5 is hardcoded |
| 3. IEEE Transactions / Conference  | NOT READY (REJECT)       | Data leakage & identical|
|    Peer-Reviewed Submission        |                          | M3 vs M4 performance    |
| 4. Commercial / Prototype System   | NOT READY                | Lacks 3GPP MAC/RLC stack|
+------------------------------------+--------------------------+-------------------------+
```

---

## 3. Detailed Assessment for STLC Tunisia 2026

### 3.1. Strengths of the Current Submission
1. **Exceptional Software Modularity**: The codebase is cleanly split across `simulation_engine`, `channel_models`, `prediction_engine`, `orchestration_engine`, `baseline_methods`, `experiments`, `visualization`, and `dashboard`.
2. **True CPU-First Reproducibility**: 100% CPU-compatible, executing without GPU requirements, and supported by a passing test suite (`15/15 passed`).
3. **Rigorous Orbital Kinematics**: WGS-84 coordinate transforms, circular LEO propagation ($7.56\text{ km/s}$), Doppler projections, and Friis free-space path loss are verified with mathematical precision.
4. **Interactive Exhibition Dashboard**: The Streamlit interface is aesthetically modern, featuring 3D Plotly orbital globes, active ML inference ribbons, and real-time parameter sandbox controls.

### 3.2. Critical Vulnerabilities That IEEE Judges Will Uncover
If presented in its current form to IEEE ComSoc reviewers and international judges at STLC 2026, the following severe flaws will be immediately identified during the technical Q&A:
1. **The "1.84 ms Satellite Latency" Claim**: Any satellite communications expert will point out that a LEO satellite at $600\text{ km}$ altitude has a minimum one-way propagation delay of $2.0\text{ ms}$ at zenith, and $6.16\text{ ms}$ at $10^\circ$ elevation ($12.3\text{ ms}$ RTT). Claiming $1.84\text{ ms}$ average latency reveals that no users were actually using the satellite.
2. **The Hard-Coded Publication Figures**: Reviewers inspecting `src/visualization/plots.py` will find literal hard-coded arrays for Figure 4 (Calibration), Figure 5 (Temporal SINR trace), and Figure 6 (Ablation). This constitutes a violation of IEEE research integrity.
3. **M3 vs. M4 Indistinguishability**: In Scenarios 3, 4, and 5, M3 (Prediction-Only) and M4 (CAPRO) achieve identical PDR ($99.921\%$) down to four decimal places. When asked: *"Where is the empirical proof that uncertainty improves reliability over uncalibrated AI?"*, the current dataset provides no evidence.
4. **The "98.6% Handover Reduction" Claim**: Reviewers will see that this reduction is calculated against an un-tuned M2 threshold baseline that was ping-ponging at an absurd $141.5\text{ handovers/min}$ due to lack of standard hysteresis. Compared to standard M1 Reactive, the handover reduction is modest, and compared to M3, it is only $6\%$.
5. **Data Leakage in Model Evaluation**: Evaluators examining the ML methodology will note that randomly splitting time-series samples across contiguous seconds invalidates the reported $R^2 = 0.851$.

---

## 4. Remediation Plan Prior to STLC Presentation

To upgrade this project from **Category C** to **Category A (Scientifically Validated)**, execute the following targeted 6-step remediation protocol:

### Step 1: Fix Network Topology & User Placement
- Distribute users into three realistic cohorts:
  - Cohort A: 4 Urban Users (under Terrestrial Base Station coverage).
  - Cohort B: 4 Rural/Suburban Users (under HAPS coverage).
  - Cohort C: 4 Remote/Maritime Users (outside terrestrial and HAPS cells, forced to use LEO satellites).
- This ensures the satellite tier is actively carrying traffic and subject to rain fades and horizon departures.

### Step 2: Fix Propagation Model Disaggregation
- Restrict ITU-R P.618 rain attenuation strictly to LEO Earth-space links.
- Apply standard ITU-R P.530 / 3GPP TR 38.901 path loss to terrestrial base station links.

### Step 3: Implement Functional Orbital Descent in Scenario 4
- Replace the empty `pass` statement in `apply_scenario_4` with true orbital propagation that drives `SAT-01` below the $10^\circ$ elevation threshold at $t = 35\text{ s}$, forcing a genuine inter-satellite or satellite-to-HAPS handover.

### Step 4: Retrain Predictive Models with Trajectory-Based Splitting
- Train the `DualUncertaintyPredictor` on Episodes 0–9 and evaluate on strictly held-out Episodes 10–14.
- Report honest, leakage-free $R^2$, MAE, and Winkler Interval Scores.

### Step 5: Regenerate All Benchmark Results & Figures Dynamically
- Re-run `benchmark_runner.py` with the updated topology and scenarios.
- Update `plots.py` and `dashboard/app.py` so that Figures 4, 5, and 6 are generated dynamically from saved experiment CSV logs without hard-coded numbers.

### Step 6: Update Documentation and STLC Presentation Slides
- Reframe the novelty and latency claims honestly: report satellite latency as $8\text{--}14\text{ ms}$ and terrestrial latency as $<2\text{ ms}$.
- Highlight CAPRO's genuine demonstrated benefit: preventing radio link dropouts when remote satellite users experience severe rain cells or orbital departures.

---

## 5. Auditor Recommendation

**DO NOT MODIFY PROJECT FILES YET.**  
Present this complete audit package to the research supervisors and project lead. Once the findings are reviewed and approved, execute the remediation roadmap to achieve an **internationally defensible, award-worthy IEEE ComSoc exhibition showcase**.

