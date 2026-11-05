"""
ORBIT-INTEL 6G: Predictive Machine Learning Models & Baselines
Implements multi-horizon link quality forecasting:
- Baselines: Persistence (M0), Rolling Mean (M1), Linear Extrapolation (M2), Ridge Regression
- Machine Learning: Random Forest, Gradient Boosting, Quantile Gradient Boosting
- Dual Uncertainty: Disaggregated Aleatoric & Epistemic Uncertainty Estimation
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional, Union
import numpy as np
import joblib
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, median_absolute_error


class PersistenceBaseline:
    """M0 Baseline: Assumes future SINR equals current instantaneous SINR."""
    def __init__(self, current_sinr_idx: int = 0):
        self.idx = current_sinr_idx

    def predict(self, X: np.ndarray, horizon_s: float = 10.0) -> np.ndarray:
        return X[:, self.idx].copy()


class RollingMeanBaseline:
    """M1 Baseline: Assumes future SINR equals 5-second historical rolling average."""
    def __init__(self, rolling_mean_idx: int = 1):
        self.idx = rolling_mean_idx

    def predict(self, X: np.ndarray, horizon_s: float = 10.0) -> np.ndarray:
        return X[:, self.idx].copy()


class LinearTrendBaseline:
    """M2 Baseline: Extrapolates current SINR using 5-second trend slope."""
    def __init__(self, current_sinr_idx: int = 0, slope_idx: int = 3):
        self.current_idx = current_sinr_idx
        self.slope_idx = slope_idx

    def predict(self, X: np.ndarray, horizon_s: float = 10.0) -> np.ndarray:
        current_sinr = X[:, self.current_idx]
        slope = X[:, self.slope_idx]
        return current_sinr + slope * horizon_s


# Alias for backwards compatibility with original codebase
BaselineLinearPredictor = LinearTrendBaseline


class RidgeLinearPredictor:
    """Regularized Linear Regression Baseline."""
    def __init__(self, alpha: float = 1.0, random_state: int = 42):
        self.model = Ridge(alpha=alpha, random_state=random_state)

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray, horizon_s: float = 10.0) -> np.ndarray:
        return self.model.predict(X)


class MultiHorizonQuantilePredictor:
    """
    Quantile Gradient Boosting for Multi-Alpha Interval Estimation.
    Supports nominal coverage levels:
    - 50% interval: [q25, q75]
    - 80% interval: [q10, q90]
    - 90% interval: [q05, q95]
    - 95% interval: [q02.5, q97.5]
    - Median: q50
    """

    ALPHAS = [0.025, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.975]

    def __init__(self, n_estimators: int = 60, max_depth: int = 4, random_state: int = 42):
        self.random_state = random_state
        self.models: dict[float, GradientBoostingRegressor] = {}
        for a in self.ALPHAS:
            self.models[a] = GradientBoostingRegressor(
                loss="quantile",
                alpha=a,
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
            )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        for a, model in self.models.items():
            model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_quantiles(self, X: np.ndarray) -> dict[float, np.ndarray]:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction.")
        raw_preds = {a: self.models[a].predict(X) for a in self.ALPHAS}

        # Enforce strict quantile monotonicity: q(a1) <= q(a2) for a1 < a2
        # Using sorted array across alpha quantiles
        sorted_alphas = sorted(self.ALPHAS)
        preds_matrix = np.column_stack([raw_preds[a] for a in sorted_alphas])
        monotone_matrix = np.sort(preds_matrix, axis=1)

        return {a: monotone_matrix[:, i] for i, a in enumerate(sorted_alphas)}


class DualUncertaintyPredictor:
    """
    Primary CAPRO Predictive Intelligence Model (Horizon-Specific or Standard 10s).
    Combines:
    1. Quantile Gradient Boosting for Aleatoric Interval Estimation (5th, 50th, 95th percentiles).
    2. Random Forest Regressor for Epistemic Ensemble Tree Variance.
    """

    def __init__(
        self,
        n_estimators_gb: int = 60,
        n_estimators_rf: int = 40,
        max_depth_gb: int = 4,
        max_depth_rf: int = 6,
        random_state: int = 42,
    ):
        self.random_state = random_state
        self.model_q05 = GradientBoostingRegressor(
            loss="quantile", alpha=0.05, n_estimators=n_estimators_gb, max_depth=max_depth_gb, random_state=random_state
        )
        self.model_q50 = GradientBoostingRegressor(
            loss="quantile", alpha=0.50, n_estimators=n_estimators_gb, max_depth=max_depth_gb, random_state=random_state
        )
        self.model_q95 = GradientBoostingRegressor(
            loss="quantile", alpha=0.95, n_estimators=n_estimators_gb, max_depth=max_depth_gb, random_state=random_state
        )
        self.model_rf = RandomForestRegressor(
            n_estimators=n_estimators_rf, max_depth=max_depth_rf, random_state=random_state, n_jobs=-1
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model_q05.fit(X, y)
        self.model_q50.fit(X, y)
        self.model_q95.fit(X, y)
        self.model_rf.fit(X, y)
        self.is_fitted = True
        return self

    def predict_with_uncertainty(self, X: np.ndarray) -> dict[str, np.ndarray]:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction.")

        q05 = self.model_q05.predict(X)
        q50 = self.model_q50.predict(X)
        q95 = self.model_q95.predict(X)

        # Monotonicity enforcement
        q_lower = np.minimum(q05, q50)
        q_upper = np.maximum(q95, q50)
        aleatoric_spread = q_upper - q_lower

        # Epistemic variance from RF individual trees
        tree_preds = np.array([tree.predict(X) for tree in self.model_rf.estimators_])  # (n_trees, N)
        epistemic_variance = np.var(tree_preds, axis=0)
        epistemic_std = np.sqrt(epistemic_variance)

        # Total uncertainty score: U = sqrt(sigma_epi^2 + (spread / 3.29)^2)
        # Normal 90% interval corresponds to 2 * 1.645 = 3.29 * sigma
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
        preds = self.predict_with_uncertainty(X)
        y_pred = preds["y_pred"]
        q_lower = preds["q_lower"]
        q_upper = preds["q_upper"]

        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))
        medae = float(median_absolute_error(y_true, y_pred))
        picp_90 = float(np.mean((y_true >= q_lower) & (y_true <= q_upper)))
        mpiw_90 = float(np.mean(q_upper - q_lower))

        return {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "median_ae": medae,
            "picp_90": picp_90,
            "mpiw_90": mpiw_90,
        }

    def save(self, filepath: Union[str, Path]):
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "DualUncertaintyPredictor":
        return joblib.load(filepath)
