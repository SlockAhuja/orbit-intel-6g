# ORBIT-INTEL 6G — LIVE DEMONSTRATION & PRESENTATION SCRIPT

**Project:** ORBIT-INTEL 6G: Global Network Intelligence & Mission Control Center  
**Contributors:** Slock Ahuja | Dr. Praveen Kumar Sharma  
**Showcase Venue:** IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026  
**Application URL:** `http://127.0.0.1:5000`  
**Optimal Viewport:** Fullscreen 16:9 Display (F11 + Presentation Mode)  

---

## 1. Quick Launch Instructions

```bash
# 1. Clone repository
git clone https://github.com/SlockAhuja/orbit-intel-6g.git
cd orbit-intel-6g

# 2. Setup environment & install dependencies
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
# source venv/bin/activate
pip install -r requirements.txt

# 3. Launch the Mission Control Workstation
python run_mission_control.py
```
Open your browser to: **`http://127.0.0.1:5000`**

Click the **`[🖥️ Presentation Mode]`** button in the top navigation header.

---

## 2. Six-Step Guided Demonstration Walkthrough

Use the floating presentation toolbar at the bottom of the screen (`1. Overview` -> `6. Benchmark`) to guide the presentation.

---

### Step 1: Global SAGIN Architecture (`1. Overview`)

* **What the Evaluator Sees:**
  - Fullscreen 3D Earth surrounded by circular Keplerian orbital rings.
  - LEO satellites (`SAT-01`, `SAT-02`), stratospheric pseudo-satellite relay (`HAPS-01`), tactical drone (`UAV-01`), and ground towers (`TBS-01`).
  - Active serving green beam connecting terminal `UE-01` to its serving node.
  - Live UTC telemetry clock and mission status indicators.
* **Demonstrator Action:**
  - Hover over nodes to show the dynamic hover tooltip (`node-hover-tooltip`).
  - Point to the header: *"ORBIT-INTEL 6G is developed by Slock Ahuja and Dr. Praveen Kumar Sharma for the IEEE ComSoc STLC Tunisia 2026 Showcase."*
* **Key Message:**
  - *"Traditional networks treat space, air, and ground as disjoint silos. ORBIT-INTEL 6G establishes a unified, 4-tier Space-Air-Ground Integrated Network operated from a unified mission control engine."*

---

### Step 2: 4-Tier Constellation Fleet (`2. 4-Tier NTN`)

* **What the Evaluator Sees:**
  - Camera rotates smoothly and focuses closer to the stratospheric layer.
  - Right telemetry switches to the **Fleet Resources** tab.
  - Details 2 LEO satellites (600 km altitude, 7.56 km/s), 1 HAPS relay (20 km altitude), 1 tactical UAV (300 m altitude), and 3 terrestrial base stations (30 m).
* **Demonstrator Action:**
  - Select `HAPS-01` in the left sidebar or globe. Show how the HUD updates altitude to 20.0 km and load utilization.
* **Key Message:**
  - *"Each tier has distinct physical constraints: LEO provides broad coverage at the cost of high Doppler shifts and propagation delays. Terrestrial offers sub-millisecond latencies but zero mobility resilience. HAPS and UAVs act as dynamic relays."*

---

### Step 3: Keplerian Kinematics & Strict Latency Decomposition (`3. Kinematics`)

* **What the Evaluator Sees:**
  - Right telemetry switches to the **Link QoS** tab.
  - The **Decomposed Physical Delay (Strict Summation)** box is prominently visible:
    1. Propagation Delay ($d/c$): dynamically computed.
    2. Access Processing: tier-specific ($2.50\text{ ms}$ for LEO, $0.30\text{ ms}$ for TBS).
    3. Feeder / Backhaul: tier-specific ($3.20\text{ ms}$ for LEO, $0.10\text{ ms}$ for TBS).
    4. Queueing Delay: dynamically tracked ($0.50\text{ ms}$).
    - **Total End-to-End Latency**: exact mathematical sum of all four components.
    - URLLC SLA Status: `✅ PASS (<10ms)` or `⚠️ VIOLATION (>10ms)`.
* **Demonstrator Action:**
  - Click `▶️ +1s` or `⏩ +5s` to advance time. Show that satellite orbital motion causes propagation delay and Doppler shift to change dynamically, while total latency strictly equals the sum with zero rounding mismatch.
* **Key Message:**
  - *"We enforce physical rigor. There are no synthetic latency values. Propagation delay is strictly bounded by the speed of light ($d/c$), and end-to-end latency is decomposed into access processing, feeder transport, and queueing."*

---

### Step 4: AI Dual-Uncertainty Conformal Forecasting (`4. AI Conformal`)

* **What the Evaluator Sees:**
  - Opens the **Interactive Experiment & Stress-Test Sandbox**.
  - A real-time Chart.js graph displays the 5-second forecasting horizon with Actual SINR, Predicted Median SINR, and the 90% Conformal Upper ($q_{95}$) and Lower ($q_{05}$) bounds.
  - The Live Multi-Method Decision Comparison grid evaluates M1, M2, M3, and M4 simultaneously.
* **Demonstrator Action:**
  - Drag the **Rain Rate Slider** from `0.0 mm/h` to `65.0 mm/h`.
  - Watch the conformal lower bound ($q_{05}$) drop. The alert badge changes to `⚠️ OUTAGE HAZARD DETECTED (q_05 < 3.0 dB)`.
  - Notice that while M1 and M2 stay dangerously attached to the degraded satellite, M4 CAPRO instantly triggers `PROACTIVE_RAIN_FADE_TRIGGER` and transfers the terminal to a ground node with zero latency penalty.
* **Key Message:**
  - *"Standard AI models output point estimates without knowing how uncertain they are. When atmospheric storm cells strike, point estimates fail silently. CAPRO separates epistemic uncertainty from aleatoric flutter, identifying impending link failures seconds before they occur."*

---

### Step 5: Preemptive Handover & Disaster Recovery (`5. Handover`)

* **What the Evaluator Sees:**
  - The sandbox transitions to Scenario 4 (Satellite Handover Replay).
  - Primary satellite `SAT-01` is descending toward the topocentric horizon, while `SAT-02` rises above 10° elevation.
* **Demonstrator Action:**
  - Advance the simulation by 5 seconds.
  - Show the event log: `[CAPRO_ORCHESTRATOR] [INFO] UE-01: PROACTIVE_DEPARTURE_TRIGGER: Target=SAT-02 (T_vis=8s <= 12s)`.
  - Point out that M1 Reactive waits until `SAT-01` drops below the 0 dB threshold at $t=35\text{s}$, causing a 100% packet drop outage. CAPRO switched at $t=23\text{s}$ with 0.0% packet drop.
* **Key Message:**
  - *"In high-speed LEO constellations, reactive handovers are unacceptable for URLLC missions. CAPRO guarantees continuous connectivity by initiating handovers during the overlapping visibility window."*

---

### Step 6: 4-Method Comprehensive Benchmark Evaluation (`6. Benchmark`)

* **What the Evaluator Sees:**
  - The **4-Method Benchmark Comparison Modal** opens, showing verified statistical evidence from 400 Monte Carlo trials across all scenarios.
* **Demonstrator Action:**
  - Walk the evaluators through the four key metric columns:
    1. **Packet Delivery Ratio (PDR):** CAPRO achieves **99.41%** (vs. M1's 91.42%, M2's 94.18%, M3's 96.85%).
    2. **99th-Percentile Tail Latency:** CAPRO delivers **6.82 ms** (strictly satisfying the &lt;10ms URLLC SLA, while M1 suffers 18.45 ms).
    3. **Outage Probability:** Reduced to **0.59%** (a 14.5x reduction vs. M1's 8.58%).
    4. **Handover Ping-Pong Frequency:** Reduced by **89.3%** (3.1/min vs. 28.9/min).
* **Key Message:**
  - *"These results demonstrate that confidence-aware predictive intelligence is not an incremental improvement—it is an essential requirement for reliable 6G non-terrestrial networking."*
