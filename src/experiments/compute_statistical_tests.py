"""
ORBIT-INTEL 6G: Statistical Significance & Hypothesis Testing Engine
Computes rigorous Paired t-tests, Wilcoxon signed-rank tests, Cohen's d effect sizes,
and 95% Confidence Intervals for M4 (CAPRO) vs M1, M2, and M3 baselines.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "phase4_benchmarking"


def run_statistical_analysis():
    raw_csv = OUT_DIR / "RAW_BENCHMARK_RESULTS.csv"
    if not raw_csv.exists():
        print(f"Error: {raw_csv} does not exist yet.")
        return

    df = pd.read_csv(raw_csv)
    print(f"Loaded {len(df)} benchmark records from {raw_csv.name}")

    # Metrics of primary scientific interest
    test_metrics = [
        ("pdr_percent", "Packet Delivery Ratio (%)", "max"),
        ("mean_latency_ms", "Mean Latency (ms)", "min"),
        ("p95_latency_ms", "95th Percentile Latency (ms)", "min"),
        ("outage_prob", "Link Outage Probability", "min"),
        ("sla_violation_rate_percent", "Total SLA Violation Rate (%)", "min"),
        ("sla_violation_urllc_percent", "URLLC SLA Violation Rate (%)", "min"),
        ("sla_violation_embb_percent", "eMBB SLA Violation Rate (%)", "min"),
        ("throughput_mbps", "Network Throughput (Mbps)", "max"),
        ("handover_frequency_per_min", "Handover Frequency (HO/min)", "min"),
        ("handover_failure_rate_percent", "Handover Failure Rate (%)", "min"),
        ("energy_j_per_mbit", "Energy Efficiency (J/Mbit)", "min"),
        ("jain_fairness_index", "Jain's Fairness Index", "max"),
    ]

    # Ensure paired sorting by scenario_id and seed
    # M4_CAPRO is our proposed method
    df_m4 = df[df["method"] == "M4_CAPRO"].sort_values(by=["scenario_id", "seed"]).reset_index(drop=True)
    n_pairs = len(df_m4)
    print(f"Found {n_pairs} paired evaluation episodes per baseline method.")

    baselines = [
        ("M1_Reactive", "M1 (Reactive)"),
        ("M2_Threshold_Predictive", "M2 (Threshold Predictive)"),
        ("M3_Prediction_Only", "M3 (Point Prediction Only)"),
    ]

    stat_records = []

    for base_id, base_label in baselines:
        df_b = df[df["method"] == base_id].sort_values(by=["scenario_id", "seed"]).reset_index(drop=True)

        # Check perfect seed & scenario alignment
        assert (df_m4["scenario_id"].values == df_b["scenario_id"].values).all(), "Scenario alignment mismatch"
        assert (df_m4["seed"].values == df_b["seed"].values).all(), "Seed alignment mismatch"

        for col, col_name, direction in test_metrics:
            x_m4 = df_m4[col].values
            x_b = df_b[col].values
            diff = x_m4 - x_b

            mean_m4 = float(np.mean(x_m4))
            std_m4 = float(np.std(x_m4, ddof=1))
            mean_b = float(np.mean(x_b))
            std_b = float(np.std(x_b, ddof=1))

            mean_diff = float(np.mean(diff))
            std_diff = float(np.std(diff, ddof=1))

            # Cohen's d for paired differences
            cohen_d = mean_diff / (std_diff + 1e-12)

            # Paired Student's t-test
            t_res = stats.ttest_rel(x_m4, x_b)
            t_stat = float(t_res.statistic)
            t_pval = float(t_res.pvalue)

            # Wilcoxon signed-rank test
            # Note: zero differences handled via Pratt or Wilcox
            try:
                w_res = stats.wilcoxon(x_m4, x_b, zero_method="pratt")
                w_stat = float(w_res.statistic)
                w_pval = float(w_res.pvalue)
            except Exception:
                w_stat = 0.0
                w_pval = 1.0

            # 95% Confidence Interval for mean difference
            ci_half = stats.t.ppf(0.975, df=n_pairs - 1) * (std_diff / np.sqrt(n_pairs))
            ci_low = mean_diff - ci_half
            ci_high = mean_diff + ci_half

            # Relative improvement percentage
            if abs(mean_b) > 1e-6:
                if direction == "max":
                    rel_gain_pct = ((mean_m4 - mean_b) / mean_b) * 100.0
                else:
                    rel_gain_pct = ((mean_b - mean_m4) / mean_b) * 100.0
            else:
                rel_gain_pct = 0.0

            stat_records.append({
                "baseline_method": base_id,
                "baseline_label": base_label,
                "metric_id": col,
                "metric_name": col_name,
                "mean_m4": mean_m4,
                "std_m4": std_m4,
                "mean_baseline": mean_b,
                "std_baseline": std_b,
                "mean_difference": mean_diff,
                "std_difference": std_diff,
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "relative_improvement_pct": rel_gain_pct,
                "cohen_d": cohen_d,
                "t_statistic": t_stat,
                "t_pvalue": t_pval,
                "wilcoxon_statistic": w_stat,
                "wilcoxon_pvalue": w_pval,
                "statistically_significant_001": bool(t_pval < 0.01),
                "statistically_significant_005": bool(t_pval < 0.05),
            })

    df_stats = pd.DataFrame(stat_records)
    df_stats.to_csv(OUT_DIR / "STATISTICAL_TEST_RESULTS.csv", index=False)
    print(f"Saved STATISTICAL_TEST_RESULTS.csv with {len(df_stats)} hypothesis test records.")

    # Also compute 95% CI for each method individually
    method_ci_records = []
    for m in ["M1_Reactive", "M2_Threshold_Predictive", "M3_Prediction_Only", "M4_CAPRO"]:
        df_sub = df[df["method"] == m]
        n_m = len(df_sub)
        for col, col_name, _ in test_metrics:
            vals = df_sub[col].values
            mean_v = float(np.mean(vals))
            std_v = float(np.std(vals, ddof=1))
            ci_half = stats.t.ppf(0.975, df=n_m - 1) * (std_v / np.sqrt(n_m))
            method_ci_records.append({
                "method": m,
                "metric_id": col,
                "metric_name": col_name,
                "mean": mean_v,
                "std": std_v,
                "median": float(np.median(vals)),
                "iqr": float(np.percentile(vals, 75) - np.percentile(vals, 25)),
                "ci95_low": mean_v - ci_half,
                "ci95_high": mean_v + ci_half,
            })
    pd.DataFrame(method_ci_records).to_csv(OUT_DIR / "METHOD_CONFIDENCE_INTERVALS.csv", index=False)
    print("Saved METHOD_CONFIDENCE_INTERVALS.csv")


if __name__ == "__main__":
    run_statistical_analysis()

