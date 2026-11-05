"""
ORBIT-INTEL 6G: Comprehensive Multi-Tier Benchmark Runner & Statistical Evaluation
Executes large-scale Monte Carlo benchmark (400 runs across M1-M4) and Ablation Study (175 runs across V1-V7).
Produces all Phase 4 research deliverables with complete statistical disaggregation.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import json
from typing import Optional
import numpy as np
import pandas as pd

from src.simulation_engine.network_simulator import NetworkSimulator
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import DualUncertaintyPredictor
from src.baseline_methods.m1_reactive import M1ReactiveBaseline
from src.baseline_methods.m2_threshold_predictive import M2ThresholdPredictiveBaseline
from src.baseline_methods.m3_prediction_only import M3PredictionOnlyBaseline
from src.orchestration_engine.capro_engine import CAPROOrchestrator
from src.experiments.scenarios import ALL_SCENARIOS, ScenarioConfig


def run_benchmark_episode(
    method_name: str,
    scenario: ScenarioConfig,
    predictor: DualUncertaintyPredictor,
    random_seed: int = 42,
    ablation_mode: Optional[str] = None,
) -> dict:
    """
    Executes a single controlled simulation episode with granular packet-level,
    per-tier, per-cohort, and latency-percentile tracking.
    """
    sim = NetworkSimulator(random_seed=random_seed)
    rng = np.random.default_rng(random_seed)

    # Instantiate orchestrator
    if method_name == "M1_Reactive":
        orchestrator = M1ReactiveBaseline()
    elif method_name == "M2_Threshold_Predictive":
        orchestrator = M2ThresholdPredictiveBaseline()
    elif method_name == "M3_Prediction_Only":
        orchestrator = M3PredictionOnlyBaseline()
    elif method_name.startswith("M4_CAPRO"):
        orchestrator = CAPROOrchestrator(ablation_mode=ablation_mode)
    else:
        raise ValueError(f"Unknown method {method_name}")

    user_attachments: dict[str, Optional[str]] = {u_id: None for u_id in sim.users}
    history_window: list[dict] = []

    # Detailed counters
    total_packets_gen = 0
    total_packets_delivered = 0
    total_packets_lost = 0
    delivered_bits = 0.0

    latencies_all_ms: list[float] = []
    latencies_urllc_ms: list[float] = []
    latencies_embb_ms: list[float] = []

    sla_violations_total = 0
    sla_violations_urllc = 0
    sla_violations_embb = 0
    urllc_packets_total = 0
    embb_packets_total = 0

    outage_occurrences = 0
    total_link_evaluations = 0

    handover_attempts = 0
    handover_failures = 0
    handover_execution_packet_loss = 0

    # Per-tier attachment time (seconds user spent attached to tier)
    tier_attachment_counts = {"LEO": 0, "HAPS": 0, "UAV": 0, "TBS": 0, "NONE": 0}

    # Per-cohort packet tracking: (delivered, generated)
    cohort_stats = {
        "Urban": {"gen": 0, "del": 0, "lat": []},
        "Suburban": {"gen": 0, "del": 0, "lat": []},
        "Remote": {"gen": 0, "del": 0, "lat": []},
        "Maritime": {"gen": 0, "del": 0, "lat": []},
    }

    def get_cohort(uid: str) -> str:
        idx = int(uid.split("-")[-1])
        if 1 <= idx <= 3:
            return "Urban"
        elif 4 <= idx <= 6:
            return "Suburban"
        elif 7 <= idx <= 9:
            return "Remote"
        else:
            return "Maritime"

    needs_ml = method_name in ["M3_Prediction_Only"] or method_name.startswith("M4_CAPRO")

    # Simulation loop across duration
    for t in range(scenario.duration_s):
        scenario.apply_step_fn(sim, t)
        snapshot = sim.step()
        history_window.append(snapshot)

        # Batch-extract features for ML models
        feat_vectors_batch = []
        link_keys_batch = []
        user_link_features = {u_id: {} for u_id in sim.users}

        if needs_ml or method_name == "M2_Threshold_Predictive":
            for u_id in sim.users:
                for n_id in sim.nodes:
                    l_data = snapshot["links"][(u_id, n_id)]
                    if l_data["is_visible"]:
                        past_records = [
                            snap["links"][(u_id, n_id)]
                            for snap in history_window[-6:]
                        ]
                        f_dict = FeatureEngineer.extract_features_from_history(past_records, u_id, n_id)
                        user_link_features[u_id][n_id] = f_dict
                        if needs_ml:
                            link_keys_batch.append((u_id, n_id))
                            feat_vectors_batch.append(FeatureEngineer.to_feature_vector(f_dict))

        # Vectorized batch prediction
        predictions_by_user = {u_id: {} for u_id in sim.users}
        if needs_ml and feat_vectors_batch:
            X_batch = np.array(feat_vectors_batch, dtype=np.float32)
            preds_batch = predictor.predict_with_uncertainty(X_batch)
            for idx, (u_id, n_id) in enumerate(link_keys_batch):
                predictions_by_user[u_id][n_id] = {
                    "y_pred": float(preds_batch["y_pred"][idx]),
                    "q_lower": float(preds_batch["q_lower"][idx]),
                    "q_upper": float(preds_batch["q_upper"][idx]),
                    "epistemic_std": float(preds_batch["epistemic_std"][idx]),
                    "aleatoric_width": float(preds_batch["aleatoric_width"][idx]),
                    "total_uncertainty": float(preds_batch["total_uncertainty"][idx]),
                }

        # Process each user allocation decision
        for u_id, user in sim.users.items():
            curr_node_id = user_attachments[u_id]
            user_links = {n_id: snapshot["links"][(u_id, n_id)] for n_id in sim.nodes}
            cohort = get_cohort(u_id)

            if method_name == "M1_Reactive":
                dec = orchestrator.select_network_node(u_id, curr_node_id, user_links, user.service_type)
                selected_node_id = dec["selected_node_id"]
                is_ho = dec["is_handover"]
            elif method_name == "M2_Threshold_Predictive":
                dec = orchestrator.select_network_node(
                    u_id, curr_node_id, user_links, user_link_features[u_id], user.service_type
                )
                selected_node_id = dec["selected_node_id"]
                is_ho = dec["is_handover"]
            elif method_name == "M3_Prediction_Only":
                pt_preds = {nid: p["y_pred"] for nid, p in predictions_by_user[u_id].items()}
                dec = orchestrator.select_network_node(u_id, curr_node_id, user_links, pt_preds, user.service_type)
                selected_node_id = dec["selected_node_id"]
                is_ho = dec["is_handover"]
            else:  # M4_CAPRO (or ablation)
                exp_dec = orchestrator.select_network_node(
                    u_id, curr_node_id, user_links, predictions_by_user[u_id], user.service_type
                )
                selected_node_id = exp_dec.selected_node_id
                is_ho = exp_dec.is_handover

            # Handover execution handling
            if is_ho and (selected_node_id != curr_node_id):
                handover_attempts += 1
                target_node = sim.nodes.get(selected_node_id)
                if target_node and target_node.available_bandwidth_mhz < 5.0:
                    handover_failures += 1
                else:
                    if curr_node_id and curr_node_id in sim.nodes:
                        sim.nodes[curr_node_id].release_load(user.required_data_rate_mbps)
                    user_attachments[u_id] = selected_node_id
                    if target_node:
                        target_node.allocate_load(user.required_data_rate_mbps)
            elif curr_node_id is None and selected_node_id:
                user_attachments[u_id] = selected_node_id
                sim.nodes[selected_node_id].allocate_load(user.required_data_rate_mbps)

            active_node_id = user_attachments[u_id]
            total_link_evaluations += 1

            # Record tier attachment
            if active_node_id is None:
                tier_attachment_counts["NONE"] += 1
            else:
                tier_attachment_counts[sim.nodes[active_node_id].tier] += 1

            # Traffic and packet transmission
            pkts_to_gen = 10
            total_packets_gen += pkts_to_gen
            cohort_stats[cohort]["gen"] += pkts_to_gen
            if user.service_type == "URLLC":
                urllc_packets_total += pkts_to_gen
            else:
                embb_packets_total += pkts_to_gen

            if active_node_id is None:
                outage_occurrences += 1
                total_packets_lost += pkts_to_gen
                sla_violations_total += pkts_to_gen
                if user.service_type == "URLLC":
                    sla_violations_urllc += pkts_to_gen
                else:
                    sla_violations_embb += pkts_to_gen
            else:
                link_state = user_links.get(active_node_id)
                active_node = sim.nodes[active_node_id]

                if not link_state or not link_state["is_visible"]:
                    outage_occurrences += 1
                    total_packets_lost += pkts_to_gen
                    sla_violations_total += pkts_to_gen
                    if user.service_type == "URLLC":
                        sla_violations_urllc += pkts_to_gen
                    else:
                        sla_violations_embb += pkts_to_gen
                else:
                    sinr = link_state["sinr_db"]
                    if sinr < user.min_sinr_threshold_db:
                        outage_occurrences += 1

                    # Latency computation
                    delay_info = sim.traffic_engine.compute_transmission_delay_ms(
                        slant_distance_m=link_state["slant_distance_m"],
                        packet_size_bytes=256 if user.service_type == "URLLC" else 1500,
                        allocated_rate_mbps=user.required_data_rate_mbps,
                        node_load=active_node.current_load,
                        tier=active_node.tier,
                    )
                    lat_ms = delay_info["t_total_ms"]
                    latencies_all_ms.append(lat_ms)
                    cohort_stats[cohort]["lat"].append(lat_ms)

                    if user.service_type == "URLLC":
                        latencies_urllc_ms.append(lat_ms)
                    else:
                        latencies_embb_ms.append(lat_ms)

                    # Check SLA delay threshold
                    is_sla_delay_violated = (lat_ms > user.max_latency_ms)

                    # Packet success evaluation
                    delivered = 0
                    for _ in range(pkts_to_gen):
                        # Handover packet drop
                        if is_ho and rng.random() < 0.15:
                            handover_execution_packet_loss += 1
                            total_packets_lost += 1
                            sla_violations_total += 1
                            if user.service_type == "URLLC":
                                sla_violations_urllc += 1
                            else:
                                sla_violations_embb += 1
                            continue

                        if sinr < user.min_sinr_threshold_db or is_sla_delay_violated:
                            total_packets_lost += 1
                            sla_violations_total += 1
                            if user.service_type == "URLLC":
                                sla_violations_urllc += 1
                            else:
                                sla_violations_embb += 1
                            continue

                        # 3GPP BLER check
                        margin_db = sinr - user.min_sinr_threshold_db
                        bler = 1e-4 if margin_db > 6.0 else (0.01 if margin_db > 2.0 else 0.08)
                        if rng.random() > bler:
                            delivered += 1
                            delivered_bits += (256 if user.service_type == "URLLC" else 1500) * 8.0
                        else:
                            total_packets_lost += 1

                    total_packets_delivered += delivered
                    cohort_stats[cohort]["del"] += delivered

        # Energy consumption accounting
        tot_energy_consumed_wh = sum(n.energy_capacity_wh - n.current_energy_wh for n in sim.nodes.values())

    # Aggregate Key Performance Indicators (KPIs)
    pdr = (total_packets_delivered / max(total_packets_gen, 1)) * 100.0
    packet_loss_rate = 100.0 - pdr
    outage_prob = float(outage_occurrences / max(total_link_evaluations, 1))

    # Latency percentiles
    if latencies_all_ms:
        mean_lat = float(np.mean(latencies_all_ms))
        median_lat = float(np.median(latencies_all_ms))
        p95_lat = float(np.percentile(latencies_all_ms, 95))
        p99_lat = float(np.percentile(latencies_all_ms, 99))
    else:
        mean_lat = median_lat = p95_lat = p99_lat = 100.0

    mean_urllc_lat = float(np.mean(latencies_urllc_ms)) if latencies_urllc_ms else 100.0
    mean_embb_lat = float(np.mean(latencies_embb_ms)) if latencies_embb_ms else 100.0

    # SLA violation rates
    sla_viol_total_pct = (sla_violations_total / max(total_packets_gen, 1)) * 100.0
    sla_viol_urllc_pct = (sla_violations_urllc / max(urllc_packets_total, 1)) * 100.0
    sla_viol_embb_pct = (sla_violations_embb / max(embb_packets_total, 1)) * 100.0

    # Throughput
    throughput_mbps = (delivered_bits / 1.0e6) / max(scenario.duration_s, 1.0)
    sim_duration_min = scenario.duration_s / 60.0
    ho_freq = float(handover_attempts / max(sim_duration_min, 0.1))
    ho_failure_rate = (handover_failures / max(handover_attempts, 1)) * 100.0

    # Energy efficiency in Joules per delivered Megabit
    tot_energy_j = tot_energy_consumed_wh * 3600.0
    delivered_mbits = delivered_bits / 1.0e6
    energy_per_mbit = float(tot_energy_j / max(delivered_mbits, 0.01))

    # Jain's Fairness Index for node load balancing
    loads = [n.current_load for n in sim.nodes.values()]
    sum_loads = sum(loads)
    sum_sq_loads = sum(l ** 2 for l in loads)
    jain_fairness = float((sum_loads ** 2) / (len(loads) * sum_sq_loads)) if sum_sq_loads > 0 else 1.0
    avg_util = float(np.mean(loads)) * 100.0

    # Tier attachment percentages
    total_att = sum(tier_attachment_counts.values())
    tier_shares = {
        f"share_{tier.lower()}": float(tier_attachment_counts[tier] / max(total_att, 1)) * 100.0
        for tier in ["LEO", "HAPS", "UAV", "TBS"]
    }

    # Cohort PDRs
    cohort_pdrs = {
        f"pdr_{c.lower()}": float(cohort_stats[c]["del"] / max(cohort_stats[c]["gen"], 1)) * 100.0
        for c in ["Urban", "Suburban", "Remote", "Maritime"]
    }

    return {
        "method": method_name,
        "ablation_mode": ablation_mode or "N/A",
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name,
        "seed": random_seed,
        "duration_s": scenario.duration_s,
        "pdr_percent": float(pdr),
        "packet_loss_rate_percent": float(packet_loss_rate),
        "outage_prob": float(outage_prob),
        "mean_latency_ms": float(mean_lat),
        "median_latency_ms": float(median_lat),
        "p95_latency_ms": float(p95_lat),
        "p99_latency_ms": float(p99_lat),
        "mean_latency_urllc_ms": float(mean_urllc_lat),
        "mean_latency_embb_ms": float(mean_embb_lat),
        "sla_violation_rate_percent": float(sla_viol_total_pct),
        "sla_violation_urllc_percent": float(sla_viol_urllc_pct),
        "sla_violation_embb_percent": float(sla_viol_embb_pct),
        "throughput_mbps": float(throughput_mbps),
        "handover_count": int(handover_attempts),
        "handover_frequency_per_min": float(ho_freq),
        "handover_failure_rate_percent": float(ho_failure_rate),
        "handover_packet_loss": int(handover_execution_packet_loss),
        "energy_j_per_mbit": float(energy_per_mbit),
        "avg_resource_util_percent": float(avg_util),
        "jain_fairness_index": float(jain_fairness),
        **tier_shares,
        **cohort_pdrs,
    }


def execute_full_benchmarking_campaign():
    out_dir = PROJECT_ROOT / "phase4_benchmarking"
    out_dir.mkdir(parents=True, exist_ok=True)
    models_dir = PROJECT_ROOT / "phase4_benchmarking"

    print("--- 1. LOADING VALIDATED CAPRO PREDICTOR ---")
    model_path = PROJECT_ROOT / "models" / "capro_predictor.joblib"
    predictor = DualUncertaintyPredictor.load(model_path)

    # 20 paired random seeds per scenario
    seeds = [101 + i for i in range(20)]
    methods = [
        "M1_Reactive",
        "M2_Threshold_Predictive",
        "M3_Prediction_Only",
        "M4_CAPRO",
    ]

    total_main_runs = len(methods) * len(ALL_SCENARIOS) * len(seeds)  # 4 * 5 * 20 = 400 runs
    print(f"\n--- 2. STARTING COMPREHENSIVE BENCHMARK: {total_main_runs} MONTE CARLO RUNS (100 runs per method) ---")
    t0 = time.time()
    main_results = []
    manifest_rows = []

    count = 0
    for sc in ALL_SCENARIOS:
        for s in seeds:
            for m in methods:
                count += 1
                res = run_benchmark_episode(m, sc, predictor, random_seed=s)
                main_results.append(res)
                manifest_rows.append({
                    "run_id": f"RUN_{count:04d}",
                    "method": m,
                    "scenario_id": sc.scenario_id,
                    "scenario_name": sc.name,
                    "seed": s,
                    "duration_s": sc.duration_s,
                    "pdr_percent": res["pdr_percent"],
                    "mean_latency_ms": res["mean_latency_ms"],
                    "outage_prob": res["outage_prob"],
                    "sla_violation_urllc_percent": res["sla_violation_urllc_percent"],
                    "status": "COMPLETED_VALID",
                })
                if count % 20 == 0 or count == total_main_runs:
                    elapsed = time.time() - t0
                    print(f"[{count:03d}/{total_main_runs}] Elapsed: {elapsed:5.1f}s | {m:23s} | {sc.name:28s} (Seed {s}) | PDR: {res['pdr_percent']:5.1f}%, Lat: {res['mean_latency_ms']:4.1f}ms, SLA_Viol: {res['sla_violation_rate_percent']:4.1f}%")

    df_raw = pd.DataFrame(main_results)
    df_raw.to_csv(out_dir / "RAW_BENCHMARK_RESULTS.csv", index=False)
    print(f"\nSaved RAW_BENCHMARK_RESULTS.csv with {len(df_raw)} records in {time.time()-t0:.1f} s.")

    df_manifest = pd.DataFrame(manifest_rows)
    df_manifest.to_csv(out_dir / "MONTE_CARLO_RUN_MANIFEST.csv", index=False)
    print("Saved MONTE_CARLO_RUN_MANIFEST.csv")

    # Export Configuration CSV
    config_rows = [
        {"parameter": "Total_Monte_Carlo_Runs", "value": total_main_runs},
        {"parameter": "Runs_Per_Method", "value": len(ALL_SCENARIOS) * len(seeds)},
        {"parameter": "Distinct_Seeds_Per_Scenario", "value": len(seeds)},
        {"parameter": "Seed_Range", "value": f"{min(seeds)} to {max(seeds)}"},
        {"parameter": "Scenarios_Covered", "value": "Scenarios 1 through 5"},
        {"parameter": "Duration_Per_Episode_s", "value": 60},
        {"parameter": "Active_Users_Per_Episode", "value": 12},
        {"parameter": "Heterogeneous_Tiers", "value": "LEO, HAPS, UAV, TBS"},
        {"parameter": "Hysteresis_Margin_Delta_J", "value": 0.08},
        {"parameter": "Orbital_Buffer_Margin_s", "value": 12.0},
        {"parameter": "Outage_Threshold_dB", "value": 3.0},
    ]
    pd.DataFrame(config_rows).to_csv(out_dir / "BENCHMARK_CONFIGURATION.csv", index=False)
    print("Saved BENCHMARK_CONFIGURATION.csv")

    # Summary by Method
    summary_method = df_raw.groupby("method").agg({
        "pdr_percent": ["mean", "std", "median"],
        "packet_loss_rate_percent": ["mean", "std"],
        "mean_latency_ms": ["mean", "std", "median"],
        "p95_latency_ms": ["mean", "std"],
        "outage_prob": ["mean", "std"],
        "sla_violation_rate_percent": ["mean", "std"],
        "sla_violation_urllc_percent": ["mean", "std"],
        "sla_violation_embb_percent": ["mean", "std"],
        "throughput_mbps": ["mean", "std"],
        "handover_frequency_per_min": ["mean", "std"],
        "handover_failure_rate_percent": ["mean", "std"],
        "energy_j_per_mbit": ["mean", "std"],
        "jain_fairness_index": ["mean", "std"],
    }).reset_index()
    summary_method.columns = ["_".join(col).strip("_") for col in summary_method.columns.values]
    summary_method.to_csv(out_dir / "BENCHMARK_METRICS_BY_METHOD.csv", index=False)
    print("Saved BENCHMARK_METRICS_BY_METHOD.csv")

    # Summary by Scenario
    summary_scen = df_raw.groupby(["scenario_id", "scenario_name", "method"]).agg({
        "pdr_percent": ["mean", "std"],
        "mean_latency_ms": ["mean", "std"],
        "outage_prob": ["mean", "std"],
        "sla_violation_rate_percent": ["mean", "std"],
        "throughput_mbps": ["mean", "std"],
        "handover_frequency_per_min": ["mean", "std"],
        "energy_j_per_mbit": ["mean", "std"],
    }).reset_index()
    summary_scen.columns = ["_".join(col).strip("_") for col in summary_scen.columns.values]
    summary_scen.to_csv(out_dir / "BENCHMARK_METRICS_BY_SCENARIO.csv", index=False)
    print("Saved BENCHMARK_METRICS_BY_SCENARIO.csv")

    # Summary by Tier Attachment
    tier_cols = ["share_leo", "share_haps", "share_uav", "share_tbs"]
    summary_tier = df_raw.groupby("method")[tier_cols].agg(["mean", "std"]).reset_index()
    summary_tier.columns = ["_".join(col).strip("_") for col in summary_tier.columns.values]
    summary_tier.to_csv(out_dir / "BENCHMARK_METRICS_BY_TIER.csv", index=False)
    print("Saved BENCHMARK_METRICS_BY_TIER.csv")

    # Summary by Service Class and Cohort
    service_cols = [
        "sla_violation_urllc_percent", "sla_violation_embb_percent",
        "mean_latency_urllc_ms", "mean_latency_embb_ms",
        "pdr_urban", "pdr_suburban", "pdr_remote", "pdr_maritime",
    ]
    summary_service = df_raw.groupby("method")[service_cols].agg(["mean", "std"]).reset_index()
    summary_service.columns = ["_".join(col).strip("_") for col in summary_service.columns.values]
    summary_service.to_csv(out_dir / "BENCHMARK_METRICS_BY_SERVICE.csv", index=False)
    print("Saved BENCHMARK_METRICS_BY_SERVICE.csv")

    # --- 3. ABLATION STUDY CAMPAIGN (V1 to V7) ---
    print("\n--- 3. STARTING CONTROLLED ABLATION STUDY (V1 to V7) ---")
    ablation_modes = [
        ("V1_NoUncertainty", "NoUncertainty"),
        ("V2_AleatoricOnly", "AleatoricOnly"),
        ("V3_EpistemicOnly", "EpistemicOnly"),
        ("V4_NoHandoverCost", "NoHandoverCost"),
        ("V5_NoReliabilityConstraint", "NoReliabilityConstraint"),
        ("V6_NoLatencyConstraint", "NoLatencyConstraint"),
        ("V7_FullCAPRO", "FullCAPRO"),
    ]
    ablation_seeds = [101, 102, 103, 104, 105]  # 5 seeds * 5 scenarios = 25 runs per variant
    ablation_results = []
    total_abl_runs = len(ablation_modes) * len(ALL_SCENARIOS) * len(ablation_seeds)

    count_abl = 0
    t_abl0 = time.time()
    for v_tag, v_mode in ablation_modes:
        for sc in ALL_SCENARIOS:
            for s in ablation_seeds:
                count_abl += 1
                res = run_benchmark_episode(
                    f"M4_CAPRO_{v_mode}", sc, predictor, random_seed=s, ablation_mode=v_mode
                )
                res["variant_tag"] = v_tag
                ablation_results.append(res)
                if count_abl % 25 == 0 or count_abl == total_abl_runs:
                    print(f"[{count_abl:03d}/{total_abl_runs}] Ablation: {v_tag:25s} | {sc.name:28s} (Seed {s}) | PDR: {res['pdr_percent']:5.1f}%, HO: {res['handover_count']}")

    df_abl = pd.DataFrame(ablation_results)
    summary_abl = df_abl.groupby(["variant_tag", "ablation_mode"]).agg({
        "pdr_percent": ["mean", "std"],
        "mean_latency_ms": ["mean", "std"],
        "outage_prob": ["mean", "std"],
        "sla_violation_rate_percent": ["mean", "std"],
        "sla_violation_urllc_percent": ["mean", "std"],
        "handover_count": ["mean", "std"],
        "handover_packet_loss": ["mean", "std"],
        "throughput_mbps": ["mean", "std"],
    }).reset_index()
    summary_abl.columns = ["_".join(col).strip("_") for col in summary_abl.columns.values]
    summary_abl.to_csv(out_dir / "CAPRO_ABLATION_RESULTS.csv", index=False)
    print(f"Saved CAPRO_ABLATION_RESULTS.csv in {time.time()-t_abl0:.1f} s.")

    print(f"\n========================================================")
    print(f"COMPREHENSIVE BENCHMARK COMPLETED: {total_main_runs + total_abl_runs} TOTAL RUNS")
    print(f"========================================================")


if __name__ == "__main__":
    execute_full_benchmarking_campaign()

