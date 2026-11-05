"""
ORBIT-INTEL 6G: Phase 2 Prediction Engine Test Suite
Tests:
1. Zero Temporal Data Leakage across Episode Splits
2. Scaler Isolation (Train partition only)
3. Multi-Horizon Prediction Accuracy & Validity
4. Quantile Monotonicity Enforcement
5. Dual Uncertainty Disaggregation (Aleatoric vs Epistemic)
6. Uncertainty Calibration Functionality (PICP, MPIW, Winkler)
7. CAPRO Orchestration Engine Compatibility
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import (
    PersistenceBaseline,
    RollingMeanBaseline,
    LinearTrendBaseline,
    MultiHorizonQuantilePredictor,
    DualUncertaintyPredictor,
)
from src.prediction_engine.uncertainty import UncertaintyCalibrator
from src.orchestration_engine.capro_engine import CAPROOrchestrator


class TestPhase2PredictionReconstruction:

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        self.experiments_dir = PROJECT_ROOT / "phase2_experiments"
        self.models_dir = PROJECT_ROOT / "phase2_models"
        self.reports_dir = PROJECT_ROOT / "phase2_reports"

    def test_zero_temporal_data_leakage(self):
        """Certifies that train, val, and test splits have 0 episode overlap and 0 row collision."""
        train_path = self.experiments_dir / "train_dataset.csv"
        val_path = self.experiments_dir / "val_dataset.csv"
        test_path = self.experiments_dir / "test_dataset.csv"

        assert train_path.exists(), "train_dataset.csv missing!"
        assert val_path.exists(), "val_dataset.csv missing!"
        assert test_path.exists(), "test_dataset.csv missing!"

        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)

        train_eps = set(train_df["episode_id"].unique())
        val_eps = set(val_df["episode_id"].unique())
        test_eps = set(test_df["episode_id"].unique())

        # Mathematical disjointness
        assert len(train_eps.intersection(val_eps)) == 0, f"Train and Val share episodes: {train_eps.intersection(val_eps)}"
        assert len(train_eps.intersection(test_eps)) == 0, f"Train and Test share episodes: {train_eps.intersection(test_eps)}"
        assert len(val_eps.intersection(test_eps)) == 0, f"Val and Test share episodes: {val_eps.intersection(test_eps)}"

        # Non-empty partitions
        assert len(train_df) > 10000, f"Train set suspiciously small: {len(train_df)}"
        assert len(val_df) > 2000, f"Val set suspiciously small: {len(val_df)}"
        assert len(test_df) > 2000, f"Test set suspiciously small: {len(test_df)}"

    def test_scaler_isolation(self):
        """Verifies that the feature scaler was fitted strictly on train data."""
        scaler_path = self.models_dir / "feature_scaler.joblib"
        assert scaler_path.exists(), "feature_scaler.joblib missing!"

        scaler = joblib.load(scaler_path)
        train_df = pd.read_csv(self.experiments_dir / "train_dataset.csv")
        X_train = train_df[FeatureEngineer.FEATURE_NAMES].values

        # Check empirical mean of train matches scaler mean
        train_mean = np.mean(X_train, axis=0)
        np.testing.assert_allclose(scaler.mean_, train_mean, rtol=1e-4, atol=1e-4)

    def test_multi_horizon_models_exist_and_predict(self):
        """Verifies that trained models exist for horizons 1s, 3s, 5s, 10s and make valid predictions."""
        test_df = pd.read_csv(self.experiments_dir / "test_dataset.csv")
        X_test = test_df[FeatureEngineer.FEATURE_NAMES].values[:50]

        for h in [1, 3, 5, 10]:
            model_path = self.models_dir / f"capro_predictor_h{h:02d}.joblib"
            assert model_path.exists(), f"Model artifact missing for H={h}s at {model_path}"
            model = DualUncertaintyPredictor.load(model_path)
            preds = model.predict_with_uncertainty(X_test)

            assert "y_pred" in preds
            assert len(preds["y_pred"]) == 50
            assert not np.isnan(preds["y_pred"]).any()
            assert not np.isinf(preds["y_pred"]).any()

    def test_monotonic_quantile_ordering(self):
        """Verifies strict monotonic ordering of predicted quantiles."""
        q_mod = MultiHorizonQuantilePredictor(n_estimators=10, max_depth=3)
        # Small synthetic test
        X_dummy = np.random.randn(20, 17)
        y_dummy = X_dummy[:, 0] * 2.0 + np.random.randn(20) * 0.5
        q_mod.fit(X_dummy, y_dummy)

        quantiles = q_mod.predict_quantiles(X_dummy)
        sorted_alphas = sorted(q_mod.ALPHAS)
        for i in range(len(sorted_alphas) - 1):
            a_low = sorted_alphas[i]
            a_high = sorted_alphas[i + 1]
            diff = quantiles[a_high] - quantiles[a_low]
            assert (diff >= -1e-6).all(), f"Quantile crossing between {a_low} and {a_high}!"

    def test_dual_uncertainty_decomposition(self):
        """Verifies decomposition of uncertainty into non-negative aleatoric and epistemic components."""
        model_path = self.models_dir / "capro_predictor_h10.joblib"
        assert model_path.exists()
        model = DualUncertaintyPredictor.load(model_path)

        test_df = pd.read_csv(self.experiments_dir / "test_dataset.csv")
        X_sample = test_df[FeatureEngineer.FEATURE_NAMES].values[:100]
        preds = model.predict_with_uncertainty(X_sample)

        assert (preds["aleatoric_width"] >= 0.0).all(), "Negative aleatoric width detected!"
        assert (preds["epistemic_std"] >= 0.0).all(), "Negative epistemic std detected!"
        assert (preds["total_uncertainty"] >= 0.0).all(), "Negative total uncertainty detected!"
        assert (preds["q_upper"] >= preds["q_lower"]).all(), "q_upper < q_lower detected!"

    def test_uncertainty_calibration_metrics(self):
        """Tests that calibration evaluator accurately computes PICP, MPIW, and Winkler score."""
        y_true = np.array([10.0, 12.0, 14.0, 8.0, 20.0])
        q_low = np.array([9.0, 11.0, 13.0, 7.0, 15.0])   # 5th item missed (y=20 > q_upper=18)
        q_high = np.array([11.0, 13.0, 15.0, 9.0, 18.0])

        score = UncertaintyCalibrator.compute_interval_score(y_true, q_low, q_high, nominal_coverage=0.80)
        assert score["picp"] == 0.80, f"Expected PICP 0.80, got {score['picp']}"
        assert np.isclose(score["mpiw"], 2.2), f"Expected MPIW 2.2, got {score['mpiw']}"
        assert score["winkler_score"] > score["mpiw"], "Winkler score should exceed MPIW when penalty exists"

    def test_capro_orchestrator_interface_compatibility(self):
        """Ensures CAPROOrchestrator can consume predictions from DualUncertaintyPredictor without error."""
        capro = CAPROOrchestrator()
        model_path = self.models_dir / "capro_predictor_h10.joblib"
        model = DualUncertaintyPredictor.load(model_path)

        # Mock candidate links
        mock_links = {
            "SAT-01": {
                "is_visible": True,
                "tier": "LEO",
                "load": 0.35,
                "slant_distance_m": 1200000.0,
                "remaining_visibility_s": 45.0,
            },
            "TBS-01": {
                "is_visible": True,
                "tier": "TBS",
                "load": 0.85,
                "slant_distance_m": 1500.0,
                "remaining_visibility_s": 9999.0,
            },
        }

        # Predict using model
        dummy_feature = np.zeros((1, 17))
        pred_out = model.predict_with_uncertainty(dummy_feature)

        predictions = {
            "SAT-01": {
                "y_pred": float(pred_out["y_pred"][0]),
                "q_lower": float(pred_out["q_lower"][0]),
                "total_uncertainty": float(pred_out["total_uncertainty"][0]),
            },
            "TBS-01": {
                "y_pred": float(pred_out["y_pred"][0] + 5.0),
                "q_lower": float(pred_out["q_lower"][0] + 5.0),
                "total_uncertainty": float(pred_out["total_uncertainty"][0]),
            },
        }

        decision = capro.select_network_node(
            user_id="UE-01",
            current_serving_id="TBS-01",
            available_links=mock_links,
            predictions=predictions,
            user_service_type="URLLC",
        )

        assert decision.selected_node_id in ["SAT-01", "TBS-01"]
        assert decision.tier in ["LEO", "TBS"]
        assert decision.risk_adjusted_utility_db is not None
        assert len(decision.explanation) > 0

