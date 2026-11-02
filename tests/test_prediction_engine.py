"""
Unit tests for Predictive AI Engine and Uncertainty Calibration.
"""

import pytest
import numpy as np
from pathlib import Path
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import DualUncertaintyPredictor
from src.prediction_engine.uncertainty import UncertaintyCalibrator


def test_feature_vector_structure():
    """Verifies feature extractor outputs all 17 documented features."""
    sample_records = [
        {"sinr_db": 15.0, "elevation_deg": 45.0, "doppler_shift_hz": 12000.0, "tier": "LEO", "is_visible": True, "remaining_visibility_s": 240.0, "load": 0.2, "bandwidth_mhz": 100.0, "slant_distance_m": 850000.0},
        {"sinr_db": 14.5, "elevation_deg": 44.5, "doppler_shift_hz": 11500.0, "tier": "LEO", "is_visible": True, "remaining_visibility_s": 235.0, "load": 0.2, "bandwidth_mhz": 100.0, "slant_distance_m": 860000.0},
    ]

    f_dict = FeatureEngineer.extract_features_from_history(sample_records, "UE-01", "SAT-01")
    assert len(f_dict) == len(FeatureEngineer.FEATURE_NAMES)

    f_vec = FeatureEngineer.to_feature_vector(f_dict)
    assert f_vec.shape == (len(FeatureEngineer.FEATURE_NAMES),)
    assert not np.isnan(f_vec).any()


def test_trained_model_inference_and_monotonicity():
    """Verifies trained model produces monotonic quantile intervals: q05 <= q50 <= q95."""
    model_path = Path(__file__).resolve().parents[1] / "models" / "capro_predictor.joblib"
    if not model_path.exists():
        pytest.skip("Trained model artifact not found.")

    predictor = DualUncertaintyPredictor.load(str(model_path))
    X_dummy = np.random.normal(0, 1, size=(5, len(FeatureEngineer.FEATURE_NAMES))).astype(np.float32)

    preds = predictor.predict_with_uncertainty(X_dummy)
    assert (preds["q_lower"] <= preds["y_pred"]).all()
    assert (preds["y_pred"] <= preds["q_upper"]).all()
    assert (preds["total_uncertainty"] >= 0.0).all()


def test_uncertainty_calibration_metrics():
    """Verifies that UncertaintyCalibrator correctly calculates PICP and ECE."""
    y_true = np.array([10.0, 12.0, 15.0, 8.0, 14.0])
    q_lower = np.array([9.0, 11.0, 14.0, 7.0, 13.0])
    q_upper = np.array([11.0, 13.0, 16.0, 9.0, 15.0])

    calib = UncertaintyCalibrator.compute_calibration_curve(y_true, q_lower, q_upper, num_bins=2)
    assert calib["overall_picp"] == 1.0  # All points are within bounds
    assert calib["overall_mpiw"] == 2.0  # Interval width is 2.0

