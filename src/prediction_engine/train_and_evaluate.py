"""
ORBIT-INTEL 6G: Multi-Horizon Training, Test Evaluation, and Calibration Pipeline
Trains baseline and advanced ML models on leak-free Train partition,
evaluates on Locked Test partition across horizons, tiers, and scenarios,
and generates research CSV datasets and saved model artifacts.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    median_absolute_error,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import (
    PersistenceBaseline,
    RollingMeanBaseline,
    LinearTrendBaseline,
    RidgeLinearPredictor,
    MultiHorizonQuantilePredictor,
    DualUncertaintyPredictor,
)
from src.prediction_engine.uncertainty import UncertaintyCalibrator


def compute_classification_metrics(y_true_binary: np.ndarray, y_pred_binary: np.ndarray) -> dict[str, float]:
    """Computes Precision, Recall, F1, and Specificity."""
    tn, fp, fn, tp = confusion_matrix(y_true_binary, y_pred_binary, labels=[0, 1]).ravel()
    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    return {
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "specificity": spec,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def run_training_and_evaluation():
    print("--- 1. LOADING PARTITION DATASETS ---")
    data_dir = PROJECT_ROOT / "phase2_experiments"
    models_dir = PROJECT_ROOT / "phase2_models"
    reports_dir = PROJECT_ROOT / "phase2_reports"
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(data_dir / "train_dataset.csv")
    val_df = pd.read_csv(data_dir / "val_dataset.csv")
    test_df = pd.read_csv(data_dir / "test_dataset.csv")
    scaler = joblib.load(models_dir / "feature_scaler.joblib")

    feature_cols = FeatureEngineer.FEATURE_NAMES
    X_train_raw = train_df[feature_cols].values
    X_val_raw = val_df[feature_cols].values
    X_test_raw = test_df[feature_cols].values

    # Scaled feature matrices
    X_train_scaled = scaler.transform(X_train_raw)
    X_val_scaled = scaler.transform(X_val_raw)
    X_test_scaled = scaler.transform(X_test_raw)

    horizons = [1, 3, 5, 10]

    # Baseline predictors
    p_base = PersistenceBaseline()
    rm_base = RollingMeanBaseline()
    lt_base = LinearTrendBaseline()

    # --- 2. MULTI-HORIZON BENCHMARK ---
    print("\n--- 2. TRAINING & EVALUATING ACROSS PREDICTION HORIZONS ---")
    horizon_results = []
    models_by_horizon = {}
    quantile_models_by_horizon = {}

    for h in horizons:
        print(f"\nTraining models for Horizon H = {h}s...")
        target_col = f"target_sinr_{h}s"
        y_train = train_df[target_col].values
        y_val = val_df[target_col].values
        y_test = test_df[target_col].values

        # A. Baselines
        pred_p = p_base.predict(X_test_raw, horizon_s=h)
        pred_rm = rm_base.predict(X_test_raw, horizon_s=h)
        pred_lt = lt_base.predict(X_test_raw, horizon_s=h)

        # B. Ridge Linear
        ridge = RidgeLinearPredictor(alpha=1.0)
        ridge.fit(X_train_scaled, y_train)
        pred_ridge = ridge.predict(X_test_scaled)

        # C. Multi-Alpha Quantile Predictor
        print(f"  Fitting Quantile Regressors for H = {h}s...")
        q_predictor = MultiHorizonQuantilePredictor(n_estimators=50, max_depth=4)
        q_predictor.fit(X_train_raw, y_train)
        quantiles_test = q_predictor.predict_quantiles(X_test_raw)
        pred_gbr_median = quantiles_test[0.50]
        quantile_models_by_horizon[h] = q_predictor

        # D. Dual Uncertainty Predictor (CAPRO Model)
        print(f"  Fitting DualUncertaintyPredictor for H = {h}s...")
        dual_pred = DualUncertaintyPredictor(n_estimators_gb=50, n_estimators_rf=35, max_depth_gb=4, max_depth_rf=6)
        dual_pred.fit(X_train_raw, y_train)
        dual_preds_test = dual_pred.predict_with_uncertainty(X_test_raw)
        models_by_horizon[h] = dual_pred

        # Save model artifact
        dual_pred.save(models_dir / f"capro_predictor_h{h:02d}.joblib")
        if h == 10:
            # Also save as default capro predictor in models/
            default_path = PROJECT_ROOT / "models" / "capro_predictor.joblib"
            default_path.parent.mkdir(parents=True, exist_ok=True)
            dual_pred.save(default_path)
            print(f"  Saved default CAPRO model to {default_path}")

        # Metrics computation helper
        candidate_preds = {
            "M0_Persistence": pred_p,
            "M1_RollingMean": pred_rm,
            "M2_LinearTrend": pred_lt,
            "Ridge_Linear": pred_ridge,
            "Quantile_GBR_Median": pred_gbr_median,
            "M4_CAPRO_DualUncertainty": dual_preds_test["y_pred"],
        }

        for m_name, p_vals in candidate_preds.items():
            mae = float(mean_absolute_error(y_test, p_vals))
            rmse = float(np.sqrt(mean_squared_error(y_test, p_vals)))
            r2 = float(r2_score(y_test, p_vals))
            medae = float(median_absolute_error(y_test, p_vals))
            horizon_results.append({
                "horizon_s": h,
                "model_name": m_name,
                "mae_db": mae,
                "rmse_db": rmse,
                "r2_score": r2,
                "median_ae_db": medae,
            })
            print(f"  [{m_name} H={h}s] MAE: {mae:.3f} dB | RMSE: {rmse:.3f} dB | R2: {r2:.3f}")

    df_horizon = pd.DataFrame(horizon_results)
    df_horizon.to_csv(reports_dir / "PREDICTION_METRICS_BY_HORIZON.csv", index=False)
    print("\nSaved PREDICTION_METRICS_BY_HORIZON.csv")

    # --- 3. DISAGGREGATED METRICS (TIER & SCENARIO FOR H=10s) ---
    print("\n--- 3. COMPUTING DISAGGREGATED METRICS FOR H = 10s ---")
    capro_10s = models_by_horizon[10]
    test_preds_10s = capro_10s.predict_with_uncertainty(X_test_raw)
    y_test_10s = test_df["target_sinr_10s"].values

    # Add predictions to test dataframe for grouped evaluation
    test_eval_df = test_df.copy()
    test_eval_df["y_pred"] = test_preds_10s["y_pred"]
    test_eval_df["q_lower"] = test_preds_10s["q_lower"]
    test_eval_df["q_upper"] = test_preds_10s["q_upper"]
    test_eval_df["aleatoric_width"] = test_preds_10s["aleatoric_width"]
    test_eval_df["epistemic_std"] = test_preds_10s["epistemic_std"]
    test_eval_df["total_uncertainty"] = test_preds_10s["total_uncertainty"]
    test_eval_df["abs_error"] = np.abs(test_eval_df["target_sinr_10s"] - test_eval_df["y_pred"])
    test_eval_df["in_interval_90"] = (test_eval_df["target_sinr_10s"] >= test_eval_df["q_lower"]) & (
        test_eval_df["target_sinr_10s"] <= test_eval_df["q_upper"]
    )

    # Disaggregated by Network Tier
    tier_rows = []
    for tier, grp in test_eval_df.groupby("tier"):
        mae = float(mean_absolute_error(grp["target_sinr_10s"], grp["y_pred"]))
        rmse = float(np.sqrt(mean_squared_error(grp["target_sinr_10s"], grp["y_pred"])))
        r2 = float(r2_score(grp["target_sinr_10s"], grp["y_pred"]))
        picp = float(grp["in_interval_90"].mean())
        mpiw = float(grp["aleatoric_width"].mean())
        mean_epi = float(grp["epistemic_std"].mean())
        mean_tot = float(grp["total_uncertainty"].mean())

        tier_rows.append({
            "tier": tier,
            "sample_count": len(grp),
            "mae_db": mae,
            "rmse_db": rmse,
            "r2_score": r2,
            "picp_90": picp,
            "mpiw_90_db": mpiw,
            "mean_epistemic_std_db": mean_epi,
            "mean_total_uncertainty_db": mean_tot,
        })
    df_tier = pd.DataFrame(tier_rows)
    df_tier.to_csv(reports_dir / "PREDICTION_METRICS_BY_TIER.csv", index=False)
    print("Saved PREDICTION_METRICS_BY_TIER.csv")

    # Disaggregated by Scenario
    scen_rows = []
    for sc_id, grp in test_eval_df.groupby("scenario_id"):
        sc_name = grp["scenario_name"].iloc[0]
        mae = float(mean_absolute_error(grp["target_sinr_10s"], grp["y_pred"]))
        rmse = float(np.sqrt(mean_squared_error(grp["target_sinr_10s"], grp["y_pred"])))
        r2 = float(r2_score(grp["target_sinr_10s"], grp["y_pred"]))
        picp = float(grp["in_interval_90"].mean())
        mpiw = float(grp["aleatoric_width"].mean())
        mean_epi = float(grp["epistemic_std"].mean())
        mean_tot = float(grp["total_uncertainty"].mean())

        scen_rows.append({
            "scenario_id": sc_id,
            "scenario_name": sc_name,
            "sample_count": len(grp),
            "mae_db": mae,
            "rmse_db": rmse,
            "r2_score": r2,
            "picp_90": picp,
            "mpiw_90_db": mpiw,
            "mean_epistemic_std_db": mean_epi,
            "mean_total_uncertainty_db": mean_tot,
        })
    df_scen = pd.DataFrame(scen_rows)
    df_scen.to_csv(reports_dir / "PREDICTION_METRICS_BY_SCENARIO.csv", index=False)
    print("Saved PREDICTION_METRICS_BY_SCENARIO.csv")

    # --- 4. UNCERTAINTY QUANTIFICATION & MULTI-LEVEL CALIBRATION ---
    print("\n--- 4. MULTI-LEVEL UNCERTAINTY CALIBRATION (H = 10s) ---")
    q_mod_10s = quantile_models_by_horizon[10]
    q_test_quantiles = q_mod_10s.predict_quantiles(X_test_raw)
    df_calib_levels = UncertaintyCalibrator.evaluate_multi_level_calibration(y_test_10s, q_test_quantiles)
    df_calib_levels.to_csv(reports_dir / "UNCERTAINTY_METRICS_TABLE.csv", index=False)
    print("Saved UNCERTAINTY_METRICS_TABLE.csv")
    print(df_calib_levels.to_string(index=False))

    # Calibration Curve (Binned Coverage vs Width)
    calib_curve = UncertaintyCalibrator.compute_calibration_curve(
        y_test_10s, test_preds_10s["q_lower"], test_preds_10s["q_upper"], num_bins=10
    )
    df_bins = pd.DataFrame({
        "bin_index": np.arange(1, 11),
        "mean_interval_width_db": calib_curve["bin_mean_widths"],
        "empirical_coverage_picp": calib_curve["bin_coverages"],
        "target_coverage": 0.90,
    })
    df_bins.to_csv(reports_dir / "CALIBRATION_CURVE_DATA.csv", index=False)
    print(f"Saved CALIBRATION_CURVE_DATA.csv (Expected Calibration Error ECE = {calib_curve['expected_calibration_error']:.4f})")

    # --- 5. OUTAGE & DEGRADATION DETECTION METRICS ---
    print("\n--- 5. OUTAGE & DEGRADATION DETECTION (H = 10s) ---")
    # True outage: target_sinr_10s < 3.0 dB
    true_outage = (y_test_10s < 3.0).astype(int)
    # Predicted outage via median expectation
    pred_outage_point = (test_preds_10s["y_pred"] < 3.0).astype(int)
    # Predicted outage via conservative risk lower bound (q_lower < 3.0 dB)
    pred_outage_risk = (test_preds_10s["q_lower"] < 3.0).astype(int)

    # True degradation: link drops by >= 3.0 dB over 10s
    true_deg = test_df["target_degradation_10s"].values.astype(int)
    pred_deg = ((test_preds_10s["y_pred"] - test_df["current_sinr_db"].values) <= -3.0).astype(int)

    cls_point = compute_classification_metrics(true_outage, pred_outage_point)
    cls_risk = compute_classification_metrics(true_outage, pred_outage_risk)
    cls_deg = compute_classification_metrics(true_deg, pred_deg)

    outage_metrics_rows = [
        {"task": "Outage_Detection_Point_Forecast", **cls_point},
        {"task": "Outage_Detection_CAPRO_Risk_Lower_Bound", **cls_risk},
        {"task": "Degradation_Detection_Delta_3dB", **cls_deg},
    ]
    df_outage = pd.DataFrame(outage_metrics_rows)
    df_outage.to_csv(reports_dir / "OUTAGE_DETECTION_METRICS.csv", index=False)
    print("Saved OUTAGE_DETECTION_METRICS.csv")
    print(df_outage[["task", "precision", "recall", "f1_score", "specificity"]].to_string(index=False))

    # Save detailed predictions dataset for locked test partition
    test_eval_df.to_csv(data_dir / "test_evaluation_predictions.csv", index=False)
    print(f"\nSaved test_evaluation_predictions.csv with {len(test_eval_df)} rows.")

    return {
        "df_horizon": df_horizon,
        "df_tier": df_tier,
        "df_scen": df_scen,
        "df_calib": df_calib_levels,
        "df_outage": df_outage,
        "ece": calib_curve["expected_calibration_error"],
    }


if __name__ == "__main__":
    run_training_and_evaluation()

