"""
ORBIT-INTEL 6G: Distribution Shift & Out-of-Distribution (OOD) Stress Testing
Evaluates trained CAPRO prediction model under unseen channel regimes:
- Shift A: Extreme Tropical Cloudburst (Rain 80-120 mm/h)
- Shift B: Severe Shadowing Flutter (Flutter std 4.5-6.5 dB)
- Shift C: Extreme Congestion Saturation (Data demand 50-80 Mbps)
Verifies that epistemic uncertainty increases under distribution shifts.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.simulation_engine.network_simulator import NetworkSimulator
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import DualUncertaintyPredictor


def run_distribution_shift_experiment(
    shift_type: str,
    rain_rate: float,
    flutter_std: float,
    high_demand: bool = False,
    duration_s: int = 60,
    seed: int = 8888,
) -> pd.DataFrame:
    """
    Simulates a SAGIN episode under extreme distribution-shift conditions.
    """
    sim = NetworkSimulator(random_seed=seed)
    sim.rain_rate_mm_h = rain_rate
    sim.shadowing_flutter_std = flutter_std

    if high_demand:
        for u in sim.users.values():
            u.required_data_rate_mbps = 50.0 if u.service_type == "URLLC" else 80.0

    episode_history = []
    for t in range(1, duration_s + 1):
        snapshot = sim.step()
        episode_history.append(snapshot)

    # Extract features with 10s lookahead
    rows = []
    min_history = 5
    lookahead = 10

    for t_idx in range(min_history, len(episode_history) - lookahead):
        current_snap = episode_history[t_idx]
        sim_time = current_snap["time_s"]

        for (u_id, n_id), link in current_snap["links"].items():
            if not link["is_visible"]:
                continue

            history_window = [
                episode_history[tau]["links"][(u_id, n_id)]
                for tau in range(t_idx - min_history, t_idx + 1)
            ]

            features = FeatureEngineer.extract_features_from_history(history_window, u_id, n_id)
            future_snap = episode_history[t_idx + lookahead]
            future_link = future_snap["links"][(u_id, n_id)]

            features["shift_type"] = shift_type
            features["time_s"] = sim_time
            features["user_id"] = u_id
            features["node_id"] = n_id
            features["tier"] = link["tier"]
            features["target_sinr_10s"] = float(future_link["sinr_db"])
            rows.append(features)

    return pd.DataFrame(rows)


def evaluate_distribution_shifts():
    print("--- EVALUATING DISTRIBUTION SHIFT & UNCERTAINTY RESPONSE ---")
    models_dir = PROJECT_ROOT / "phase2_models"
    reports_dir = PROJECT_ROOT / "phase2_reports"
    model_path = models_dir / "capro_predictor_h10.joblib"

    if not model_path.exists():
        model_path = PROJECT_ROOT / "models" / "capro_predictor.joblib"

    predictor = DualUncertaintyPredictor.load(model_path)
    feature_cols = FeatureEngineer.FEATURE_NAMES

    # Define test regimes
    regimes = [
        ("Nominal_In_Distribution", 0.0, 0.0, False),
        ("Shift_A_Extreme_Cloudburst", 95.0, 1.0, False),
        ("Shift_B_Severe_Flutter", 20.0, 5.5, False),
        ("Shift_C_Extreme_Congestion", 5.0, 0.5, True),
        ("Shift_D_Compound_Storm_Flutter", 110.0, 6.0, True),
    ]

    results = []
    all_shift_dfs = []

    for name, rain, flutter, demand in regimes:
        print(f"Testing Regime: {name} (Rain={rain} mm/h, Flutter={flutter} dB, HeavyLoad={demand})...")
        df_shift = run_distribution_shift_experiment(
            shift_type=name,
            rain_rate=rain,
            flutter_std=flutter,
            high_demand=demand,
            duration_s=60,
            seed=9901,
        )
        all_shift_dfs.append(df_shift)

        X_shift = df_shift[feature_cols].values
        y_shift = df_shift["target_sinr_10s"].values

        preds = predictor.predict_with_uncertainty(X_shift)
        y_pred = preds["y_pred"]
        q_lower = preds["q_lower"]
        q_upper = preds["q_upper"]
        ale_width = preds["aleatoric_width"]
        epi_std = preds["epistemic_std"]
        tot_unc = preds["total_uncertainty"]

        mae = float(mean_absolute_error(y_shift, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_shift, y_pred)))
        r2 = float(r2_score(y_shift, y_pred))
        picp_90 = float(np.mean((y_shift >= q_lower) & (y_shift <= q_upper)))
        mean_ale = float(np.mean(ale_width))
        mean_epi = float(np.mean(epi_std))
        mean_tot = float(np.mean(tot_unc))

        results.append({
            "regime": name,
            "rain_rate_mm_h": rain,
            "flutter_std_db": flutter,
            "sample_count": len(df_shift),
            "mae_db": mae,
            "rmse_db": rmse,
            "r2_score": r2,
            "picp_90": picp_90,
            "mean_aleatoric_width_db": mean_ale,
            "mean_epistemic_std_db": mean_epi,
            "mean_total_uncertainty_db": mean_tot,
            "epistemic_elevation_factor": mean_epi / 1.0,  # relative to ID
        })
        print(f"  MAE: {mae:.2f} dB | PICP: {picp_90*100:.1f}% | Epistemic std: {mean_epi:.3f} dB | Total unc: {mean_tot:.3f} dB")

    df_results = pd.DataFrame(results)
    # Compute relative epistemic elevation factor compared to in-distribution
    base_epi = df_results.loc[df_results["regime"] == "Nominal_In_Distribution", "mean_epistemic_std_db"].values[0]
    df_results["epistemic_elevation_factor"] = df_results["mean_epistemic_std_db"] / base_epi

    df_results.to_csv(reports_dir / "DISTRIBUTION_SHIFT_METRICS.csv", index=False)
    print("\nSaved DISTRIBUTION_SHIFT_METRICS.csv")
    print(df_results[["regime", "mae_db", "picp_90", "mean_epistemic_std_db", "epistemic_elevation_factor"]].to_string(index=False))

    # Save compiled shift dataset
    compiled_df = pd.concat(all_shift_dfs, ignore_index=True)
    compiled_df.to_csv(PROJECT_ROOT / "phase2_experiments" / "distribution_shift_telemetry.csv", index=False)
    print("Saved distribution_shift_telemetry.csv")

    return df_results


if __name__ == "__main__":
    evaluate_distribution_shifts()

