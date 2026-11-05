"""
ORBIT-INTEL 6G: Publication Figure Generator for Phase 2
Generates IEEE STLC 2026 publication-grade figures strictly from saved CSV outputs:
1. fig_phase2_prediction_vs_ground_truth.png
2. fig_phase2_error_by_horizon.png
3. fig_phase2_calibration_curves.png
4. fig_phase2_distribution_shift_uncertainty.png
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Configure publication-grade styling
plt.rcParams.update({
    "font.size": 11,
    "font.family": "serif",
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "lines.linewidth": 1.8,
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
    "figure.dpi": 300,
})

VALIDATION_DIR = PROJECT_ROOT / "phase2_validation"
REPORTS_DIR = PROJECT_ROOT / "phase2_reports"
EXPERIMENTS_DIR = PROJECT_ROOT / "phase2_experiments"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


def plot_prediction_vs_ground_truth():
    """Figure 1: Prediction vs Ground Truth on Locked Test Set."""
    test_eval_path = EXPERIMENTS_DIR / "test_evaluation_predictions.csv"
    if not test_eval_path.exists():
        print(f"Skipping Figure 1: {test_eval_path} not found.")
        return

    df = pd.read_csv(test_eval_path)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot A: Scatter Plot with 1:1 Line
    tier_colors = {"LEO": "#1f77b4", "HAPS": "#ff7f0e", "UAV": "#2ca02c", "TBS": "#d62728"}
    for tier, grp in df.groupby("tier"):
        ax1.scatter(
            grp["target_sinr_10s"],
            grp["y_pred"],
            label=f"{tier} (N={len(grp)})",
            color=tier_colors.get(tier, "gray"),
            alpha=0.35,
            edgecolors="none",
            s=22,
        )

    # 1:1 Line
    min_val = min(df["target_sinr_10s"].min(), df["y_pred"].min()) - 2.0
    max_val = max(df["target_sinr_10s"].max(), df["y_pred"].max()) + 2.0
    ax1.plot([min_val, max_val], [min_val, max_val], "k--", linewidth=1.5, label="Ideal 1:1 Line")
    ax1.axvline(3.0, color="red", linestyle=":", label="Outage Threshold (3 dB)")
    ax1.axhline(3.0, color="red", linestyle=":")

    ax1.set_xlabel("True Future SINR at H=10s (dB)")
    ax1.set_ylabel("CAPRO Predicted Median SINR (dB)")
    ax1.set_title("(a) True vs. Predicted SINR (Locked Test Set)")
    ax1.set_xlim(min_val, max_val)
    ax1.set_ylim(min_val, max_val)
    ax1.grid(True)
    ax1.legend(loc="upper left", framealpha=0.85)

    # Subplot B: Trajectory Trace with 90% Prediction Intervals
    # Sample a continuous trajectory segment from one episode and link
    sample_ep = df["episode_id"].iloc[0]
    leo_links = df[(df["episode_id"] == sample_ep) & (df["tier"] == "LEO")]
    if len(leo_links) > 0:
        sample_node = leo_links["node_id"].iloc[0]
        sample_user = leo_links["user_id"].iloc[0]
        traj = df[(df["episode_id"] == sample_ep) & (df["node_id"] == sample_node) & (df["user_id"] == sample_user)].sort_values("time_s")
    else:
        traj = df.head(35).sort_values("time_s")

    t = traj["time_s"].values
    y_true = traj["target_sinr_10s"].values
    y_pred = traj["y_pred"].values
    ql = traj["q_lower"].values
    qu = traj["q_upper"].values

    ax2.plot(t, y_true, "k.-", label="True Future SINR (t+10s)", markersize=6)
    ax2.plot(t, y_pred, "b--", label="CAPRO Median Forecast", markersize=4)
    ax2.fill_between(t, ql, qu, color="blue", alpha=0.2, label="90% Prediction Interval [q05, q95]")
    ax2.axhline(3.0, color="red", linestyle=":", label="Outage Threshold")

    ax2.set_xlabel("Simulation Elapsed Time t (seconds)")
    ax2.set_ylabel("SINR at Horizon H=10s (dB)")
    ax2.set_title(f"(b) Interval Forecasting Trace ({sample_user} to {sample_node})")
    ax2.grid(True)
    ax2.legend(loc="lower left", framealpha=0.85)

    plt.tight_layout()
    out_path = VALIDATION_DIR / "fig_phase2_prediction_vs_ground_truth.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")


def plot_error_by_horizon():
    """Figure 2: MAE and RMSE across Candidate Prediction Horizons."""
    horizon_path = REPORTS_DIR / "PREDICTION_METRICS_BY_HORIZON.csv"
    if not horizon_path.exists():
        print(f"Skipping Figure 2: {horizon_path} not found.")
        return

    df = pd.read_csv(horizon_path)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    models_to_plot = [
        ("M0_Persistence", "M0: Persistence", "gray", "o"),
        ("M1_RollingMean", "M1: Rolling Mean", "purple", "s"),
        ("M2_LinearTrend", "M2: Linear Trend", "orange", "^"),
        ("Ridge_Linear", "Ridge Regression", "green", "d"),
        ("M4_CAPRO_DualUncertainty", "M4: CAPRO Predictor", "blue", "P"),
    ]

    horizons = sorted(df["horizon_s"].unique())

    for m_key, m_label, color, marker in models_to_plot:
        sub = df[df["model_name"] == m_key].sort_values("horizon_s")
        if len(sub) > 0:
            ax1.plot(sub["horizon_s"], sub["mae_db"], marker=marker, label=m_label, color=color, markersize=7)
            ax2.plot(sub["horizon_s"], sub["rmse_db"], marker=marker, label=m_label, color=color, markersize=7)

    ax1.set_xlabel("Prediction Horizon H (seconds)")
    ax1.set_ylabel("Mean Absolute Error (dB)")
    ax1.set_title("(a) Mean Absolute Error (MAE) vs. Horizon")
    ax1.set_xticks(horizons)
    ax1.grid(True)
    ax1.legend(framealpha=0.85)

    ax2.set_xlabel("Prediction Horizon H (seconds)")
    ax2.set_ylabel("Root Mean Squared Error (dB)")
    ax2.set_title("(b) Root Mean Squared Error (RMSE) vs. Horizon")
    ax2.set_xticks(horizons)
    ax2.grid(True)
    ax2.legend(framealpha=0.85)

    plt.tight_layout()
    out_path = VALIDATION_DIR / "fig_phase2_error_by_horizon.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")


def plot_calibration_curves():
    """Figure 3: Multi-Level Calibration & Reliability Diagram."""
    calib_table_path = REPORTS_DIR / "UNCERTAINTY_METRICS_TABLE.csv"
    curve_data_path = REPORTS_DIR / "CALIBRATION_CURVE_DATA.csv"

    if not calib_table_path.exists() or not curve_data_path.exists():
        print("Skipping Figure 3: calibration CSVs not found.")
        return

    df_levels = pd.read_csv(calib_table_path)
    df_curve = pd.read_csv(curve_data_path)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Subplot A: Target vs Empirical PICP
    nom = df_levels["target_picp"].values * 100
    emp = df_levels["empirical_picp"].values * 100

    ax1.plot([40, 100], [40, 100], "k--", label="Ideal Calibration Line")
    ax1.plot(nom, emp, "bo-", linewidth=2.0, markersize=8, label="Empirical PICP")
    for x, y, w in zip(nom, emp, df_levels["mpiw_db"]):
        ax1.annotate(f"{y:.1f}%\n(w={w:.1f}dB)", (x, y - 4), ha="center", fontsize=9)

    ax1.set_xlabel("Nominal Target Coverage (%)")
    ax1.set_ylabel("Empirical Test Coverage PICP (%)")
    ax1.set_title("(a) Multi-Level Coverage Calibration")
    ax1.set_xlim(45, 100)
    ax1.set_ylim(45, 105)
    ax1.grid(True)
    ax1.legend(loc="upper left")

    # Subplot B: Binned Reliability Diagram
    bins = df_curve["bin_index"].values
    cov = df_curve["empirical_coverage_picp"].values * 100
    widths = df_curve["mean_interval_width_db"].values

    ax2.bar(bins, cov, color="#4C72B0", alpha=0.75, edgecolor="black", label="Bin Coverage")
    ax2.axhline(90.0, color="red", linestyle="--", linewidth=1.8, label="Nominal Target (90%)")

    # Secondary axis for interval width
    ax2_twin = ax2.twinx()
    ax2_twin.plot(bins, widths, "r^-", linewidth=2.0, markersize=6, label="Mean Interval Width")
    ax2_twin.set_ylabel("Mean Interval Width (dB)", color="red")
    ax2_twin.tick_params(axis="y", labelcolor="red")
    ax2_twin.grid(False)

    ax2.set_xlabel("Uncertainty Decile Bin (Low to High)")
    ax2.set_ylabel("Empirical Coverage (%)")
    ax2.set_title("(b) Reliability Diagram (Binned Deciles for 90% Bound)")
    ax2.set_ylim(50, 105)
    ax2.set_xticks(bins)
    ax2.grid(True)
    ax2.legend(loc="lower left")

    plt.tight_layout()
    out_path = VALIDATION_DIR / "fig_phase2_calibration_curves.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")


def plot_distribution_shift_uncertainty():
    """Figure 4: Distribution Shift and Epistemic Uncertainty Elevation."""
    shift_path = REPORTS_DIR / "DISTRIBUTION_SHIFT_METRICS.csv"
    if not shift_path.exists():
        print("Skipping Figure 4: DISTRIBUTION_SHIFT_METRICS.csv not found.")
        return

    df = pd.read_csv(shift_path)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    regime_labels = [
        "In-Dist\nNominal",
        "Shift A\nExtreme Rain",
        "Shift B\nHigh Flutter",
        "Shift C\nCongestion",
        "Shift D\nCompound",
    ]
    x = np.arange(len(df))

    # Subplot A: Accuracy & Coverage Degradation
    width = 0.35
    ax1.bar(x - width/2, df["mae_db"], width=width, label="MAE (dB)", color="#4C72B0")
    ax1_twin = ax1.twinx()
    ax1_twin.plot(x, df["picp_90"] * 100, "ro-", linewidth=2.0, markersize=7, label="Coverage PICP (%)")
    ax1_twin.axhline(90.0, color="gray", linestyle=":")
    ax1_twin.set_ylabel("Coverage PICP (%)", color="red")
    ax1_twin.tick_params(axis="y", labelcolor="red")
    ax1_twin.set_ylim(50, 100)
    ax1_twin.grid(False)

    ax1.set_xticks(x)
    ax1.set_xticklabels(regime_labels)
    ax1.set_ylabel("Mean Absolute Error (dB)")
    ax1.set_title("(a) Predictive Performance Under Distribution Shift")
    ax1.grid(True)
    ax1.legend(loc="upper left")

    # Subplot B: Epistemic Uncertainty Elevation
    colors = ["#2ca02c" if i == 0 else "#d62728" for i in range(len(df))]
    bars = ax2.bar(x, df["mean_epistemic_std_db"], color=colors, alpha=0.8, edgecolor="black")
    for bar, factor in zip(bars, df["epistemic_elevation_factor"]):
        yval = bar.get_height()
        ax2.annotate(f"{factor:.2f}x", (bar.get_x() + bar.get_width() / 2, yval + 0.05),
                     ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax2.set_xticks(x)
    ax2.set_xticklabels(regime_labels)
    ax2.set_ylabel("Epistemic Uncertainty $\sigma_{epi}$ (dB)")
    ax2.set_title("(b) Epistemic Uncertainty Response (OOD Detection)")
    ax2.grid(True)

    plt.tight_layout()
    out_path = VALIDATION_DIR / "fig_phase2_distribution_shift_uncertainty.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")


def generate_all_figures():
    print("--- GENERATING PUBLICATION FIGURES FOR PHASE 2 ---")
    plot_prediction_vs_ground_truth()
    plot_error_by_horizon()
    plot_calibration_curves()
    plot_distribution_shift_uncertainty()
    print("--- ALL PHASE 2 FIGURES GENERATED SUCCESSFULLY ---")


if __name__ == "__main__":
    generate_all_figures()

