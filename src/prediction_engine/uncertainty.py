"""
ORBIT-INTEL 6G: Uncertainty Calibration, Verification, and Risk Categorization
Calculates Prediction Interval Coverage Probability (PICP), Mean Prediction Interval Width (MPIW),
Winkler Interval Scores, Conformal Calibration, and Link Risk Categorization.
"""

from typing import Optional
import numpy as np
import pandas as pd


class UncertaintyCalibrator:
    """
    Statistical uncertainty quantification and calibration engine.
    Ensures link quality uncertainty is calibrated, bounded, and risk-aware.
    """

    @staticmethod
    def compute_interval_score(
        y_true: np.ndarray,
        q_lower: np.ndarray,
        q_upper: np.ndarray,
        nominal_coverage: float = 0.90,
    ) -> dict[str, float]:
        """
        Computes Prediction Interval Coverage Probability (PICP), Mean Prediction Interval Width (MPIW),
        and Winkler Interval Score (S_alpha).
        
        Winkler Score:
            S_alpha = (u - l) + (2 / alpha) * (l - y) * I(y < l) + (2 / alpha) * (y - u) * I(y > u)
        Lower Winkler score denotes a superior interval (tight width + low penalty for missed coverage).
        """
        alpha = 1.0 - nominal_coverage
        width = q_upper - q_lower
        underage = np.maximum(0.0, q_lower - y_true)
        overage = np.maximum(0.0, y_true - q_upper)

        penalties = (2.0 / alpha) * underage + (2.0 / alpha) * overage
        interval_scores = width + penalties

        picp = float(np.mean((y_true >= q_lower) & (y_true <= q_upper)))
        mpiw = float(np.mean(width))
        winkler_score = float(np.mean(interval_scores))

        return {
            "nominal_coverage": nominal_coverage,
            "picp": picp,
            "mpiw": mpiw,
            "winkler_score": winkler_score,
            "coverage_error": picp - nominal_coverage,
        }

    @staticmethod
    def evaluate_multi_level_calibration(
        y_true: np.ndarray,
        quantiles_dict: dict[float, np.ndarray],
    ) -> pd.DataFrame:
        """
        Evaluates coverage and Winkler scores across standard nominal levels:
        - 50% interval: [q25, q75]
        - 80% interval: [q10, q90]
        - 90% interval: [q05, q95]
        - 95% interval: [q02.5, q97.5]
        """
        levels = [
            (0.50, 0.25, 0.75),
            (0.80, 0.10, 0.90),
            (0.90, 0.05, 0.95),
            (0.95, 0.025, 0.975),
        ]

        rows = []
        for nominal, q_low_a, q_high_a in levels:
            if q_low_a in quantiles_dict and q_high_a in quantiles_dict:
                ql = quantiles_dict[q_low_a]
                qu = quantiles_dict[q_high_a]
                res = UncertaintyCalibrator.compute_interval_score(y_true, ql, qu, nominal)
                rows.append({
                    "nominal_coverage_pct": int(nominal * 100),
                    "target_picp": nominal,
                    "empirical_picp": res["picp"],
                    "mpiw_db": res["mpiw"],
                    "winkler_score": res["winkler_score"],
                    "coverage_gap": res["coverage_error"],
                })

        return pd.DataFrame(rows)

    @staticmethod
    def calibrate_conformal_margin(
        y_val: np.ndarray,
        q_lower_val: np.ndarray,
        q_upper_val: np.ndarray,
        target_coverage: float = 0.90,
    ) -> float:
        """
        Computes split-conformal calibration offset delta on validation set.
        delta is the (1 - target_coverage) quantile of non-conformity scores:
            E_i = max(q_lower - y, y - q_upper)
        """
        scores = np.maximum(q_lower_val - y_val, y_val - q_upper_val)
        n = len(scores)
        p = np.clip(np.ceil((n + 1) * target_coverage) / n, 0.0, 1.0)
        delta = float(np.quantile(scores, p))
        return delta

    @staticmethod
    def compute_calibration_curve(
        y_true: np.ndarray,
        q_lower: np.ndarray,
        q_upper: np.ndarray,
        num_bins: int = 10,
    ) -> dict:
        """
        Calculates empirical coverage across uncertainty confidence bins and Expected Calibration Error (ECE).
        """
        uncertainty = q_upper - q_lower
        sort_idx = np.argsort(uncertainty)
        y_sorted = y_true[sort_idx]
        ql_sorted = q_lower[sort_idx]
        qu_sorted = q_upper[sort_idx]
        u_sorted = uncertainty[sort_idx]

        bin_size = len(y_true) // num_bins
        bin_coverages = []
        bin_mean_widths = []

        for b in range(num_bins):
            start = b * bin_size
            end = (b + 1) * bin_size if b < num_bins - 1 else len(y_true)
            covered = (y_sorted[start:end] >= ql_sorted[start:end]) & (y_sorted[start:end] <= qu_sorted[start:end])
            bin_coverages.append(float(np.mean(covered)))
            bin_mean_widths.append(float(np.mean(u_sorted[start:end])))

        ece = float(np.mean([abs(cov - 0.90) for cov in bin_coverages]))

        return {
            "bin_coverages": bin_coverages,
            "bin_mean_widths": bin_mean_widths,
            "expected_calibration_error": ece,
            "overall_picp": float(np.mean((y_true >= q_lower) & (y_true <= q_upper))),
            "overall_mpiw": float(np.mean(uncertainty)),
        }

    @staticmethod
    def classify_link_risk(
        predicted_sinr_db: float,
        q_lower_db: float,
        total_uncertainty_db: float,
        outage_threshold_db: float = 3.0,
        remaining_visibility_s: float = 300.0,
    ) -> dict:
        """
        Classifies future link risk into LOW_RISK, MODERATE_RISK, or HIGH_RISK.
        Considers lower confidence bound (worst-case plausible condition) and remaining visibility.
        """
        safety_margin_db = q_lower_db - outage_threshold_db

        if safety_margin_db <= 0.0 or total_uncertainty_db >= 4.0 or remaining_visibility_s < 12.0:
            risk_tier = "HIGH_RISK"
            risk_score = 0.85 + 0.15 * min(1.0, max(0.0, -safety_margin_db / 5.0))
            reason = "Imminent outage predicted within confidence lower bound or satellite departing."
        elif safety_margin_db < 4.0 or total_uncertainty_db >= 2.5 or remaining_visibility_s < 25.0:
            risk_tier = "MODERATE_RISK"
            risk_score = 0.50 + 0.10 * (total_uncertainty_db / 4.0)
            reason = "Moderate fade or elevated uncertainty; link requires monitoring."
        else:
            risk_tier = "LOW_RISK"
            risk_score = max(0.05, 0.30 - 0.05 * safety_margin_db)
            reason = "Robust link with strong SINR margin and low prediction uncertainty."

        return {
            "risk_tier": risk_tier,
            "risk_score": float(np.clip(risk_score, 0.0, 1.0)),
            "safety_margin_db": float(safety_margin_db),
            "explanation": reason,
        }
