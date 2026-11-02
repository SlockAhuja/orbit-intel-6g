"""
ORBIT-INTEL 6G: Predictive Machine Learning Models
Implements Gradient Boosting Quantile Regressors, Random Forest Ensembles, and Baselines.
"""

from typing import Optional
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class BaselineLinearPredictor:
    """
    M2 baseline: Deterministic linear trend extrapolation.
    """

    def predict(self, X: np.ndarray, horizon_s: float = 10.0) -> np.ndarray:
        # Assumes feature 0 is current_sinr and feature 3 is sinr_trend_slope
        current_sinr = X[:, 0]
        slope = X[:, 3]
        return current_sinr + slope * horizon_s


class DualUncertaintyPredictor:
    """
    Core CAPRO Predictive Intelligence Model.
    Combines:
    1. Quantile Gradient Boosting for Aleatoric Interval Estimation (tau=0.05, 0.50, 0.95).
    2. Random Forest Regressor for Epistemic Ensemble Variance.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state

        # Quantile models for aleatoric channel bounds (90% prediction interval)
        self.model_q05 = GradientBoostingRegressor(
            loss="quantile", alpha=0.05, n_estimators=60, max_depth=4, random_state=random_state
        )
        self.model_q50 = GradientBoostingRegressor(
            loss="quantile", alpha=0.50, n_estimators=60, max_depth=4, random_state=random_state
        )
        self.model_q95 = GradientBoostingRegressor(
            loss="quantile", alpha=0.95, n_estimators=60, max_depth=4, random_state=random_state
        )

        # Random Forest for epistemic tree variance
        self.model_rf = RandomForestRegressor(
            n_estimators=40, max_depth=6, random_state=random_state, n_jobs=-1
        )

        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fits all models on training features X and future SINR target y."""
        self.model_q05.fit(X, y)
        self.model_q50.fit(X, y)
        self.model_q95.fit(X, y)
        self.model_rf.fit(X, y)
        self.is_fitted = True

    def predict_with_uncertainty(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """
        Generates point predictions and decomposed uncertainty metrics.
        Returns:
            - y_pred (median expectation q50)
            - q_lower (5th percentile)
            - q_upper (95th percentile)
            - aleatoric_width (q_upper - q_lower)
            - epistemic_std (std dev across RF decision trees)
            - total_uncertainty_score
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predicting.")

        q05 = self.model_q05.predict(X)
        q50 = self.model_q50.predict(X)
        q95 = self.model_q95.predict(X)

        # Enforce monotonicity: q05 <= q50 <= q95
        q_lower = np.minimum(q05, q50)
        q_upper = np.maximum(q95, q50)
        aleatoric_spread = q_upper - q_lower

        # Epistemic variance from Random Forest individual tree estimators
        tree_preds = np.array([tree.predict(X) for tree in self.model_rf.estimators_])  # shape: (n_trees, N)
        epistemic_variance = np.var(tree_preds, axis=0)
        epistemic_std = np.sqrt(epistemic_variance)

        # Total uncertainty metric: U = sqrt(sigma_epi^2 + (spread / 3.29)^2)
        # 90% normal interval corresponds to ~3.29 * sigma
        sigma_ale = aleatoric_spread / 3.29
        total_uncertainty = np.sqrt(epistemic_variance + sigma_ale ** 2)

        return {
            "y_pred": q50,
            "q_lower": q_lower,
            "q_upper": q_upper,
            "aleatoric_width": aleatoric_spread,
            "epistemic_std": epistemic_std,
            "total_uncertainty": total_uncertainty,
        }

    def evaluate(self, X: np.ndarray, y_true: np.ndarray) -> dict[str, float]:
        """Evaluates predictive accuracy and interval quality."""
        preds = self.predict_with_uncertainty(X)
        y_pred = preds["y_pred"]
        q_lower = preds["q_lower"]
        q_upper = preds["q_upper"]

        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))

        # Prediction Interval Coverage Probability (PICP) for nominal 90%
        covered = (y_true >= q_lower) & (y_true <= q_upper)
        picp = float(np.mean(covered))

        # Mean Prediction Interval Width (MPIW)
        mpiw = float(np.mean(q_upper - q_lower))

        return {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "picp_90": picp,
            "mpiw": mpiw,
        }

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "DualUncertaintyPredictor":
        return joblib.load(filepath)

