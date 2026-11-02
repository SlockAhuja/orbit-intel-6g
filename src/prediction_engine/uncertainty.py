"""
ORBIT-INTEL 6G: Uncertainty Calibration, Verification, and Risk Categorization
Calculates Expected Calibration Error (ECE), Prediction Interval Coverage Probability (PICP),
and classifies link degradation risk.
"""

import numpy as np


class UncertaintyCalibrator:
    """
    Statistical calibration evaluator and link risk classifier.
    Ensures prediction uncertainty is statistically grounded.
    """

    @staticmethod
    def compute_calibration_curve(
        y_true: np.ndarray,
        q_lower: np.ndarray,
        q_upper: np.ndarray,
        num_bins: int = 10,
    ) -> dict:
        """
        Calculates empirical coverage across uncertainty confidence bins.
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
        # Outage safety margin
        safety_margin_db = q_lower_db - outage_threshold_db

        # Risk rules
        if safety_margin_db <= 0.0 or total_uncertainty_db >= 4.0 or remaining_visibility_s < 12.0:
            risk_tier = "HIGH_RISK"
            risk_score = 0.85 + 0.15 * min(1.0, max(0.0, -safety_margin_db / 5.0))
            reason = "Imminent outage predicted within 90% confidence lower bound or satellite departing."
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

