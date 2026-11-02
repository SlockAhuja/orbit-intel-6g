"""
ORBIT-INTEL 6G: Phase 1 Physical Validation Data and Plot Generator
Runs live physical simulations and produces:
1. phase1_validation/LATENCY_COMPONENT_ANALYSIS.csv
2. phase1_validation/USER_ATTACHMENT_DISTRIBUTION.csv
3. phase1_validation/SATELLITE_VISIBILITY_VALIDATION.csv
4. phase1_validation/CHANNEL_MODEL_VALIDATION.csv
5. phase1_validation/fig_phase1_tier_attachment.png
6. phase1_validation/fig_phase1_latency_decomposition.png
7. phase1_validation/fig_phase1_satellite_departure.png
8. phase1_validation/fig_phase1_doppler_trajectory.png
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.simulation_engine.network_simulator import NetworkSimulator
from src.simulation_engine.traffic import TrafficEngine
from src.channel_models.propagation import PropagationModel
from src.experiments.scenarios import apply_scenario_4

OUTPUT_DIR = "phase1_validation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set scientific plot style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
})


def generate_latency_csv_and_plot():
    """Generates LATENCY_COMPONENT_ANALYSIS.csv and fig_phase1_latency_decomposition.png."""
    sim = NetworkSimulator(random_seed=42)
    engine = TrafficEngine(speed_of_light=3.0e8)

    sample_links = [
        ("UE-01", "TBS-01", "TBS", 757.57, 50.0),
        ("UE-04", "UAV-01", "UAV", 1250.0, 30.0),
        ("UE-07", "HAPS-01", "HAPS", 23500.0, 40.0),
        ("UE-07", "SAT-01", "LEO", 780000.0, 50.0),
        ("UE-10", "SAT-01", "LEO", 920000.0, 50.0),
        ("UE-10", "SAT-02", "LEO", 1450000.0, 50.0),
    ]

    records = []
    for u_id, n_id, tier, dist_m, rate_mbps in sample_links:
        decomp = engine.compute_transmission_delay_ms(
            slant_distance_m=dist_m,
            packet_size_bytes=1500,
            allocated_rate_mbps=rate_mbps,
            node_load=0.35,
            tier=tier,
        )
        records.append({
            "User_ID": u_id,
            "Node_ID": n_id,
            "Tier": tier,
            "Slant_Distance_km": round(dist_m / 1000.0, 2),
            "Allocated_Rate_Mbps": rate_mbps,
            "Propagation_Delay_ms": round(decomp["t_prop_ms"], 4),
            "Transmission_Delay_ms": round(decomp["t_trans_ms"], 4),
            "Queuing_Delay_ms": round(decomp["t_queue_ms"], 4),
            "Processing_Delay_ms": round(decomp["t_proc_ms"], 4),
            "Feeder_Backhaul_ms": round(decomp["t_feeder_ms"], 4),
            "Total_OneWay_Access_ms": round(decomp["t_access_oneway_ms"], 4),
            "Total_EndToEnd_Latency_ms": round(decomp["t_e2e_total_ms"], 4),
            "Round_Trip_Time_ms": round(decomp["t_rtt_ms"], 4),
        })

    df = pd.DataFrame(records)
    csv_path = os.path.join(OUTPUT_DIR, "LATENCY_COMPONENT_ANALYSIS.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")

    # Plot decomposed delay
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=300)
    labels = [f"{r['Node_ID']} ({r['Tier']})\n{r['User_ID']}" for r in records]
    x = np.arange(len(labels))
    width = 0.55

    t_prop = [r["Propagation_Delay_ms"] for r in records]
    t_trans = [r["Transmission_Delay_ms"] for r in records]
    t_proc = [r["Processing_Delay_ms"] for r in records]
    t_queue = [r["Queuing_Delay_ms"] for r in records]
    t_feeder = [r["Feeder_Backhaul_ms"] for r in records]

    p1 = ax.bar(x, t_prop, width, label="Propagation (d/c)", color="#1f77b4")
    p2 = ax.bar(x, t_trans, width, bottom=t_prop, label="Transmission", color="#ff7f0e")
    p3 = ax.bar(x, t_proc, width, bottom=np.array(t_prop) + np.array(t_trans), label="Processing", color="#2ca02c")
    p4 = ax.bar(x, t_queue, width, bottom=np.array(t_prop) + np.array(t_trans) + np.array(t_proc), label="Queuing (M/M/1)", color="#d62728")
    p5 = ax.bar(x, t_feeder, width, bottom=np.array(t_prop) + np.array(t_trans) + np.array(t_proc) + np.array(t_queue), label="NTN Feeder Backhaul", color="#9467bd")

    ax.set_ylabel("One-Way End-to-End Latency (ms)")
    ax.set_title("Decomposed Latency Components Across 6G SAGIN Tiers")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc="upper left", frameon=True)
    plt.tight_layout()

    fig_path = os.path.join(OUTPUT_DIR, "fig_phase1_latency_decomposition.png")
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved {fig_path}")


def generate_user_attachment_csv_and_plot():
    """Generates USER_ATTACHMENT_DISTRIBUTION.csv and fig_phase1_tier_attachment.png."""
    sim = NetworkSimulator(random_seed=42)
    snapshot = sim.step()

    cohort_names = {
        "UE-01": "Urban", "UE-02": "Urban", "UE-03": "Urban",
        "UE-04": "Suburban", "UE-05": "Suburban", "UE-06": "Suburban",
        "UE-07": "Remote/Rural", "UE-08": "Remote/Rural", "UE-09": "Remote/Rural",
        "UE-10": "Maritime/Offshore", "UE-11": "Maritime/Offshore", "UE-12": "Maritime/Offshore",
    }

    records = []
    for u_id, user in sim.users.items():
        cohort = cohort_names[u_id]
        # Find best visible link by SINR
        best_node = None
        best_sinr = -999.0
        best_tier = "None"
        visible_nodes = []

        for n_id, node in sim.nodes.items():
            l_data = snapshot["links"][(u_id, n_id)]
            if l_data["is_visible"]:
                visible_nodes.append(f"{n_id}({l_data['sinr_db']:.1f}dB)")
                if l_data["sinr_db"] > best_sinr:
                    best_sinr = l_data["sinr_db"]
                    best_node = n_id
                    best_tier = node.tier

        records.append({
            "User_ID": u_id,
            "Cohort": cohort,
            "Service_Type": user.service_type,
            "Latitude_deg": round(user.lat_deg, 4),
            "Longitude_deg": round(user.lon_deg, 4),
            "Primary_Attached_Node": best_node,
            "Attached_Tier": best_tier,
            "Primary_Link_SINR_dB": round(best_sinr, 2),
            "All_Visible_Nodes": "; ".join(visible_nodes),
            "Visible_Node_Count": len(visible_nodes),
        })

    df = pd.DataFrame(records)
    csv_path = os.path.join(OUTPUT_DIR, "USER_ATTACHMENT_DISTRIBUTION.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")

    # Plot attachment breakdown
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=300)

    # 1. Tier count bar chart
    tier_counts = df["Attached_Tier"].value_counts()
    tiers = ["TBS", "UAV", "HAPS", "LEO"]
    counts = [tier_counts.get(t, 0) for t in tiers]
    colors = ["#2ca02c", "#ff7f0e", "#9467bd", "#1f77b4"]
    bars = ax1.bar(tiers, counts, color=colors, width=0.5)
    ax1.set_ylabel("Number of Attached Users")
    ax1.set_title("User Attachment Distribution by Tier")
    ax1.set_ylim(0, 8)
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, int(yval), ha="center", va="bottom", fontweight="bold")

    # 2. Cohort vs Tier Stacked Chart
    cohort_order = ["Urban", "Suburban", "Remote/Rural", "Maritime/Offshore"]
    cohort_tier_df = pd.crosstab(df["Cohort"], df["Attached_Tier"]).reindex(cohort_order)
    for t in tiers:
        if t not in cohort_tier_df.columns:
            cohort_tier_df[t] = 0
    cohort_tier_df = cohort_tier_df[tiers]

    cohort_tier_df.plot(kind="bar", stacked=True, ax=ax2, color=colors)
    ax2.set_ylabel("Users")
    ax2.set_title("User Cohort Tier Distribution")
    ax2.set_xticklabels(cohort_order, rotation=20, ha="right")
    ax2.legend(title="Tier", loc="upper left")

    plt.tight_layout()
    fig_path = os.path.join(OUTPUT_DIR, "fig_phase1_tier_attachment.png")
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved {fig_path}")


def generate_satellite_departure_csv_and_plot():
    """Generates SATELLITE_VISIBILITY_VALIDATION.csv, fig_phase1_satellite_departure.png, and fig_phase1_doppler_trajectory.png."""
    sim = NetworkSimulator(random_seed=42)

    records = []
    time_points = list(range(61))
    sat1_elev = []
    sat1_rem_vis = []
    sat1_slant_km = []
    sat1_doppler_khz = []
    sat1_sinr = []
    sat1_vis = []

    sat2_elev = []
    sat2_rem_vis = []
    sat2_doppler_khz = []
    sat2_sinr = []
    sat2_vis = []

    for t in time_points:
        apply_scenario_4(sim, t)
        snapshot = sim.step()

        l1 = snapshot["links"][("UE-01", "SAT-01")]
        l2 = snapshot["links"][("UE-10", "SAT-02")]

        sat1_elev.append(l1["elevation_deg"])
        sat1_rem_vis.append(l1["remaining_visibility_s"])
        sat1_slant_km.append(l1["slant_distance_m"] / 1000.0)
        sat1_doppler_khz.append(l1["doppler_shift_hz"] / 1000.0)
        sat1_sinr.append(l1["sinr_db"])
        sat1_vis.append(l1["is_visible"])

        sat2_elev.append(l2["elevation_deg"])
        sat2_rem_vis.append(l2["remaining_visibility_s"])
        sat2_doppler_khz.append(l2["doppler_shift_hz"] / 1000.0)
        sat2_sinr.append(l2["sinr_db"])
        sat2_vis.append(l2["is_visible"])

        records.append({
            "Time_s": t,
            "SAT01_Elevation_deg": round(l1["elevation_deg"], 2),
            "SAT01_Slant_Dist_km": round(l1["slant_distance_m"] / 1000.0, 2),
            "SAT01_Remaining_Vis_s": round(l1["remaining_visibility_s"], 1),
            "SAT01_Doppler_kHz": round(l1["doppler_shift_hz"] / 1000.0, 3),
            "SAT01_SINR_dB": round(l1["sinr_db"], 2),
            "SAT01_Is_Visible": l1["is_visible"],
            "SAT02_Elevation_deg": round(l2["elevation_deg"], 2),
            "SAT02_Remaining_Vis_s": round(l2["remaining_visibility_s"], 1),
            "SAT02_Doppler_kHz": round(l2["doppler_shift_hz"] / 1000.0, 3),
            "SAT02_SINR_dB": round(l2["sinr_db"], 2),
            "SAT02_Is_Visible": l2["is_visible"],
        })

    df = pd.DataFrame(records)
    csv_path = os.path.join(OUTPUT_DIR, "SATELLITE_VISIBILITY_VALIDATION.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")

    # Plot 1: Elevation and Handover Trigger
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, dpi=300)

    # Elevation profile
    ax1.plot(time_points, sat1_elev, "b-", linewidth=2.0, label="SAT-01 Elevation (Setting)")
    ax1.plot(time_points, sat2_elev, "g--", linewidth=2.0, label="SAT-02 Elevation (Rising)")
    ax1.axhline(10.0, color="r", linestyle=":", linewidth=1.5, label="10° Physical Horizon Threshold")
    ax1.axvline(25.0, color="orange", linestyle="-.", linewidth=1.2, label="Proactive Handover Trigger (t=25s)")
    ax1.axvline(35.0, color="red", linestyle="-.", linewidth=1.2, label="Physical Link Severance (t=35s)")
    ax1.set_ylabel("Elevation Angle (deg)")
    ax1.set_title("Scenario 4: Satellite Orbital Departure & Handover Continuity")
    ax1.legend(loc="upper right", frameon=True)
    ax1.set_ylim(6, 16)

    # Remaining visibility profile
    ax2.plot(time_points, sat1_rem_vis, "b-", linewidth=2.0, label="SAT-01 Remaining Visibility (s)")
    ax2.plot(time_points, sat2_rem_vis, "g--", linewidth=2.0, label="SAT-02 Remaining Visibility (s)")
    ax2.axhline(12.0, color="orange", linestyle=":", linewidth=1.5, label="12s Risk-Aversion Lookahead Threshold")
    ax2.set_xlabel("Simulation Time (s)")
    ax2.set_ylabel("Remaining Visibility (s)")
    ax2.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    fig_path = os.path.join(OUTPUT_DIR, "fig_phase1_satellite_departure.png")
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved {fig_path}")

    # Plot 2: Doppler Shift Trajectory
    fig, ax = plt.subplots(figsize=(8.5, 4.5), dpi=300)
    ax.plot(time_points, sat1_doppler_khz, "b-", linewidth=2.0, label="SAT-01 Doppler Shift (Departing)")
    ax.plot(time_points, sat2_doppler_khz, "g--", linewidth=2.0, label="SAT-02 Doppler Shift (Approaching)")
    ax.axhline(0.0, color="k", linestyle=":", linewidth=1.0)
    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Doppler Frequency Shift (kHz at 2 GHz)")
    ax.set_title("Doppler Frequency Dynamics During Satellite Pass & Handover")
    ax.legend(loc="best", frameon=True)
    plt.tight_layout()

    fig_doppler_path = os.path.join(OUTPUT_DIR, "fig_phase1_doppler_trajectory.png")
    plt.savefig(fig_doppler_path)
    plt.close()
    print(f"Saved {fig_doppler_path}")


def generate_channel_model_csv():
    """Generates CHANNEL_MODEL_VALIDATION.csv validating disaggregated path loss formulas."""
    prop = PropagationModel()
    fc_s_band = 2.0e9
    fc_ka_band = 28.0e9

    distances = [100.0, 500.0, 1500.0, 2000.0, 5000.0, 20000.0, 100000.0, 600000.0, 1200000.0]
    elevations = [10.0, 20.0, 30.0, 45.0, 60.0, 90.0]
    rain_rates = [0.0, 10.0, 25.0, 50.0]

    records = []
    # Test LEO over elevations and rain rates
    for elev in elevations:
        for r_rate in rain_rates:
            pl_info = prop.total_path_loss(
                distance_m=800000.0,
                elevation_deg=elev,
                frequency_hz=fc_s_band,
                tier="LEO",
                rain_rate_mm_h=r_rate,
                enable_fading=False,
            )
            records.append({
                "Tier": "LEO",
                "Distance_m": 800000.0,
                "Elevation_deg": elev,
                "Carrier_Freq_GHz": 2.0,
                "Rain_Rate_mm_h": r_rate,
                "Model_Used": pl_info["model_used"],
                "Basic_Loss_dB": round(pl_info["basic_loss_db"], 2),
                "Atmospheric_Gas_Loss_dB": round(pl_info["atm_loss_db"], 2),
                "Rain_Attenuation_dB": round(pl_info["rain_loss_db"], 2),
                "Total_Path_Loss_dB": round(pl_info["total_path_loss_db"], 2),
            })

    # Test TBS over distances and rain rates
    for d in [200.0, 500.0, 1000.0, 1500.0, 2200.0]:
        for r_rate in [0.0, 25.0, 50.0]:
            pl_info = prop.total_path_loss(
                distance_m=d,
                elevation_deg=1.5,
                frequency_hz=fc_s_band,
                tier="TBS",
                rain_rate_mm_h=r_rate,
                enable_fading=False,
            )
            records.append({
                "Tier": "TBS",
                "Distance_m": d,
                "Elevation_deg": 1.5,
                "Carrier_Freq_GHz": 2.0,
                "Rain_Rate_mm_h": r_rate,
                "Model_Used": pl_info["model_used"],
                "Basic_Loss_dB": round(pl_info["basic_loss_db"], 2),
                "Atmospheric_Gas_Loss_dB": round(pl_info["atm_loss_db"], 2),
                "Rain_Attenuation_dB": round(pl_info["rain_loss_db"], 2),
                "Total_Path_Loss_dB": round(pl_info["total_path_loss_db"], 2),
            })

    # Test UAV
    for d in [500.0, 1500.0, 2800.0]:
        for r_rate in [0.0, 25.0]:
            pl_info = prop.total_path_loss(
                distance_m=d,
                elevation_deg=25.0,
                frequency_hz=fc_s_band,
                tier="UAV",
                rain_rate_mm_h=r_rate,
                enable_fading=False,
            )
            records.append({
                "Tier": "UAV",
                "Distance_m": d,
                "Elevation_deg": 25.0,
                "Carrier_Freq_GHz": 2.0,
                "Rain_Rate_mm_h": r_rate,
                "Model_Used": pl_info["model_used"],
                "Basic_Loss_dB": round(pl_info["basic_loss_db"], 2),
                "Atmospheric_Gas_Loss_dB": round(pl_info["atm_loss_db"], 2),
                "Rain_Attenuation_dB": round(pl_info["rain_loss_db"], 2),
                "Total_Path_Loss_dB": round(pl_info["total_path_loss_db"], 2),
            })

    df = pd.DataFrame(records)
    csv_path = os.path.join(OUTPUT_DIR, "CHANNEL_MODEL_VALIDATION.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")


if __name__ == "__main__":
    generate_latency_csv_and_plot()
    generate_user_attachment_csv_and_plot()
    generate_satellite_departure_csv_and_plot()
    generate_channel_model_csv()
    print("All Phase 1 validation datasets and scientific figures generated successfully.")
