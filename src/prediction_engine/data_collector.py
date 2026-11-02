"""
ORBIT-INTEL 6G: Synthetic Dataset Generator & Model Training Pipeline
Collects multi-trajectory SAGIN telemetry, builds feature matrices, and trains the CAPRO predictive models.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.simulation_engine.network_simulator import NetworkSimulator
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import DualUncertaintyPredictor
from src.prediction_engine.uncertainty import UncertaintyCalibrator


def generate_training_data(
    num_episodes: int = 15,
    episode_duration_s: int = 60,
    lookahead_s: int = 10,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates synthetic training dataset by executing multi-condition SAGIN simulation runs.
    """
    sim = NetworkSimulator(random_seed=random_seed)
    rng = np.random.default_rng(random_seed)

    rows = []

    print(f"Generating training data across {num_episodes} diverse simulation episodes...")
    for ep in range(num_episodes):
        # Vary weather and flutter across episodes to expose model to diverse channel regimes
        rain_rate = 0.0
        if ep % 3 == 1:
            rain_rate = float(rng.uniform(15.0, 50.0))  # Moderate to heavy rain
        elif ep % 3 == 2:
            rain_rate = float(rng.uniform(50.0, 90.0))  # Severe storm fade

        flutter_std = 0.0 if ep % 2 == 0 else float(rng.uniform(1.5, 3.5))

        sim.reset(random_seed=random_seed + ep * 100)
        sim.rain_rate_mm_h = rain_rate
        sim.shadowing_flutter_std = flutter_std

        # Run episode
        episode_history = []
        for t in range(episode_duration_s):
            snapshot = sim.step()
            episode_history.append(snapshot)

        # Build feature-target pairs with lookahead
        for t_idx in range(5, episode_duration_s - lookahead_s):
            future_snapshot = episode_history[t_idx + lookahead_s]

            for (u_id, n_id), future_link in future_snapshot["links"].items():
                if not future_link["is_visible"]:
                    continue  # Only learn on viable channel regimes

                # Window of history up to t_idx
                history_window = [
                    episode_history[tau]["links"][(u_id, n_id)]
                    for tau in range(max(0, t_idx - 5), t_idx + 1)
                ]

                features = FeatureEngineer.extract_features_from_history(history_window, u_id, n_id)
                features["target_future_sinr_db"] = future_link["sinr_db"]
                features["target_future_outage"] = 1.0 if future_link["sinr_db"] < 3.0 else 0.0
                features["episode"] = ep
                features["rain_rate_mm_h"] = rain_rate
                rows.append(features)

    df = pd.DataFrame(rows)
    print(f"Dataset generated: {len(df)} samples across {df['is_visible'].sum()} active links.")

    # Save raw synthetic dataset
    out_dir = Path(__file__).resolve().parents[2] / "data" / "synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "sagin_telemetry_dataset.csv", index=False)

    return df


def train_and_evaluate_pipeline(
    data_df: pd.DataFrame,
    model_output_path: Optional[str] = None,
    metrics_output_path: Optional[str] = None,
    random_seed: int = 42,
) -> dict:
    """
    Trains DualUncertaintyPredictor and evaluates prediction calibration.
    """
    feature_cols = FeatureEngineer.FEATURE_NAMES
    X = data_df[feature_cols].values
    y = data_df["target_future_sinr_db"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_seed
    )

    print(f"Training CAPRO DualUncertaintyPredictor on {len(X_train)} samples...")
    predictor = DualUncertaintyPredictor(random_state=random_seed)
    predictor.fit(X_train, y_train)

    print("Evaluating predictive accuracy and calibration...")
    eval_metrics = predictor.evaluate(X_test, y_test)
    preds = predictor.predict_with_uncertainty(X_test)

    # Calibration analysis
    calib = UncertaintyCalibrator.compute_calibration_curve(
        y_test, preds["q_lower"], preds["q_upper"], num_bins=10
    )
    eval_metrics["ece"] = calib["expected_calibration_error"]
    eval_metrics["mean_epistemic_std"] = float(np.mean(preds["epistemic_std"]))
    eval_metrics["mean_aleatoric_width"] = float(np.mean(preds["aleatoric_width"]))

    print(f"Results: MAE = {eval_metrics['mae']:.3f} dB, RMSE = {eval_metrics['rmse']:.3f} dB, R2 = {eval_metrics['r2']:.3f}")
    print(f"PICP (nominal 90%) = {eval_metrics['picp_90']*100:.2f}%, ECE = {eval_metrics['ece']:.4f}")

    # Save model
    if model_output_path is None:
        model_output_path = str(Path(__file__).resolve().parents[2] / "models" / "capro_predictor.joblib")
    predictor.save(model_output_path)
    print(f"Model saved to {model_output_path}")

    # Save metrics
    if metrics_output_path is None:
        metrics_output_path = str(Path(__file__).resolve().parents[2] / "results" / "metrics" / "model_training_metrics.json")
    Path(metrics_output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_output_path, "w") as f:
        json.dump(eval_metrics, f, indent=2)

    return eval_metrics


if __name__ == "__main__":
    df = generate_training_data(num_episodes=12, episode_duration_s=50, lookahead_s=10)
    train_and_evaluate_pipeline(df)
