# ORBIT-INTEL 6G: System Architecture

```mermaid
flowchart TD
    subgraph Physical_SAGIN_Space ["Tier 1: Multi-Tier Physical Network (SAGIN)"]
        LEO["LEO Satellites (h=600 km, v=7.56 km/s)"]
        HAPS["HAPS Platforms (h=20 km, stratospheric)"]
        UAV["UAV Relays (h=300 m, tactical)"]
        TBS["Terrestrial Base Stations (h=30 m)"]
        UE["Mobile 6G Users (Terrestrial / Vehicular)"]
        
        LEO --- UE
        HAPS --- UE
        UAV --- UE
        TBS --- UE
    end

    subgraph Channel_Environment ["Tier 2: 3GPP TR 38.811 Channel & Doppler Physics"]
        FSPL["Free-Space Path Loss"]
        Doppler["Doppler Shift (fd = fc*v/c)"]
        Weather["ITU-R P.618 Rain & Atmospheric Fade"]
        Shadow["Log-Normal Shadow Fading"]
        SINR["Instantaneous Multi-Tier SINR"]
        
        LEO --> Doppler
        LEO --> FSPL
        HAPS --> FSPL
        Weather --> SINR
        Shadow --> SINR
        FSPL --> SINR
        Doppler --> SINR
    end

    subgraph Telemetry_State ["Tier 3: Network Telemetry State S(t)"]
        State["S(t) = [SINR, Doppler, Load, Visibility, Energy, Bandwidth, Elevation]"]
        SINR --> State
    end

    subgraph AI_Intelligence ["Tier 4: Predictive Link-Risk & Calibrated Uncertainty"]
        Predictor["Multi-Horizon Forecaster f_theta(S)"]
        Uncertainty["Quantile Regression & Dual Uncertainty g_phi(S)"]
        RiskClf["Link Degradation Risk Classifier"]
        
        State --> Predictor
        State --> Uncertainty
        Predictor --> RiskClf
        Uncertainty --> RiskClf
    end

    subgraph Orchestration ["Tier 5: Confidence-Aware Orchestration (CAPRO)"]
        Utility["Risk-Adjusted Link Utility: R_adj = Q_hat - kappa * U"]
        Constraints["Reliability SLAs (P_outage <= 10^-4, Delay, Bandwidth)"]
        Engine["CAPRO Decision Engine & Multi-Tier Handover Gating"]
        Explainer["Explainable Audit Log Generator"]
        
        Predictor --> Utility
        Uncertainty --> Utility
        Utility --> Engine
        Constraints --> Engine
        Engine --> Explainer
        Engine --> Physical_SAGIN_Space
    end
```

---

## Architecture Components

1. **`simulation_engine`**:
   - Manages physical node geometry, orbital kinematics (Keplerian / SGP4 / Skyfield mechanics), user mobility trajectories, and dynamic traffic demands.
2. **`channel_models`**:
   - Implements 3GPP TR 38.811 and ITU-R P.618 propagation physics, Doppler shifts, fast/slow fading, and multi-tier SINR calculations.
3. **`prediction_engine`**:
   - Trains and executes high-efficiency Gradient Boosted and Random Forest estimators with quantile heads ($\tau = 0.05, 0.50, 0.95$) for calibrated prediction intervals.
4. **`orchestration_engine`**:
   - Houses the core CAPRO logic, risk-adjusted utility evaluation, proactive handover gating, and explainable decision records.
5. **`baseline_methods`**:
   - Implements M1 (Reactive), M2 (Threshold-based), and M3 (Prediction-only AI) for rigorous scientific benchmarking under identical scenario seeds.
6. **`experiments`**:
   - Runs Monte Carlo simulations over 5 standard scenarios, calculating 10 key performance indicators (KPIs) with confidence intervals.
7. **`visualization`**:
   - Produces publication-grade 300-DPI charts (Matplotlib / Seaborn) and interactive Plotly figures.
8. **`dashboard`**:
   - Multi-page interactive Streamlit research exhibition platform.

