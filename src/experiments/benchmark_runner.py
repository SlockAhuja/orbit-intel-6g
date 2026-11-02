"""
ORBIT-INTEL 6G: Scientific Benchmark Runner and Comparative Evaluation Suite
Runs M1-M4 across 5 Scenarios with multi-seed statistical evaluation.
High-efficiency vectorized prediction batching for high CPU throughput.
"""

import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


def run_single_simulation(
    method_name: str,
    scenario: ScenarioConfig,
    predictor: DualUncertaintyPredictor,
    random_seed: int = 42,
    kappa: float = 1.5,
) -> dict:
    """
    Executes a single controlled simulation run for a designated method and scenario.
    Vectorized prediction batching across all links per time-step.
    """
    sim = NetworkSimulator(random_seed=random_seed)
    rng = np.random.default_rng(random_seed)

    # Initialize method orchestrator
    if method_name == "M1_Reactive":
        orchestrator = M1ReactiveBaseline()
    elif method_name == "M2_Threshold_Predictive":
        orchestrator = M2ThresholdPredictiveBaseline()
    elif method_name == "M3_Prediction_Only":
        orchestrator = M3PredictionOnlyBaseline()
    elif method_name == "M4_CAPRO":
        orchestrator = CAPROOrchestrator(risk_aversion_kappa=kappa)
    else:
        raise ValueError(f"Unknown method {method_name}")

    # Telemetry and history buffer
    history_window: list[dict] = []
    user_attachments: dict[str, Optional[str]] = {u_id: None for u_id in sim.users}

    # Tracking counters
    total_packets_gen = 0
    total_packets_delivered = 0
    total_latencies_ms: list[float] = []
    outage_occurrences = 0
    total_link_evaluations = 0
    handover_attempts = 0
    handover_failures = 0
    delivered_bits = 0.0

    needs_ml_predictions = method_name in ["M3_Prediction_Only", "M4_CAPRO"]

    for t in range(scenario.duration_s):
        scenario.apply_step_fn(sim, t)
        snapshot = sim.step()
        history_window.append(snapshot)

        # Batch-extract features for ML models
        link_keys_batch = []
        feat_vectors_batch = []
        user_link_features = {u_id: {} for u_id in sim.users}

        if needs_ml_predictions or method_name == "M2_Threshold_Predictive":
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
                        if needs_ml_predictions:
                            link_keys_batch.append((u_id, n_id))
                            feat_vectors_batch.append(FeatureEngineer.to_feature_vector(f_dict))

        # Vectorized batch prediction
        predictions_by_user = {u_id: {} for u_id in sim.users}
        if needs_ml_predictions and feat_vectors_batch:
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

        # Process each user
        for u_id, user in sim.users.items():
            curr_node_id = user_attachments[u_id]
            user_links = {
                n_id: snapshot["links"][(u_id, n_id)]
                for n_id in sim.nodes
            }

            # Orchestration node selection
            if method_name == "M1_Reactive":
                decision = orchestrator.select_network_node(u_id, curr_node_id, user_links, user.service_type)
                selected_node_id = decision["selected_node_id"]
                is_ho = decision["is_handover"]
            elif method_name == "M2_Threshold_Predictive":
                decision = orchestrator.select_network_node(
                    u_id, curr_node_id, user_links, user_link_features[u_id], user.service_type
                )
                selected_node_id = decision["selected_node_id"]
                is_ho = decision["is_handover"]
            elif method_name == "M3_Prediction_Only":
                pt_preds = {nid: p["y_pred"] for nid, p in predictions_by_user[u_id].items()}
                decision = orchestrator.select_network_node(
                    u_id, curr_node_id, user_links, pt_preds, user.service_type
                )
                selected_node_id = decision["selected_node_id"]
                is_ho = decision["is_handover"]
            else:  # M4_CAPRO
                exp_dec = orchestrator.select_network_node(
                    u_id, curr_node_id, user_links, predictions_by_user[u_id], user.service_type
                )
                selected_node_id = exp_dec.selected_node_id
                is_ho = exp_dec.is_handover

            # Handle handover execution
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

            # Packet transmission accounting
            total_packets_gen += 10
            total_link_evaluations += 1

            if active_node_id is None:
                outage_occurrences += 1
            else:
                link_state = user_links.get(active_node_id)
                active_node = sim.nodes[active_node_id]

                if not link_state or not link_state["is_visible"]:
                    outage_occurrences += 1
                else:
                    sinr = link_state["sinr_db"]
                    if sinr < user.min_sinr_threshold_db:
                        outage_occurrences += 1

                    # Latency
                    slant_m = link_state["slant_distance_m"]
                    delay_info = sim.traffic_engine.compute_transmission_delay_ms(
                        slant_distance_m=slant_m,
                        packet_size_bytes=256 if user.service_type == "URLLC" else 1500,
                        allocated_rate_mbps=user.required_data_rate_mbps,
                        node_load=active_node.current_load,
                        tier=active_node.tier,
                    )
                    lat_ms = delay_info["t_total_ms"]
                    total_latencies_ms.append(lat_ms)

                    # Success test
                    delivered = 0
                    for _ in range(10):
                        pkt_ok = sim.traffic_engine.evaluate_packet_success(
                            sinr_db=sinr,
                            sinr_threshold_db=user.min_sinr_threshold_db,
                            total_latency_ms=lat_ms,
                            max_latency_ms=user.max_latency_ms,
                            is_handover_in_progress=is_ho,
                            rng=rng,
                        )
                        if pkt_ok:
                            delivered += 1
                            delivered_bits += (256 if user.service_type == "URLLC" else 1500) * 8.0

                    total_packets_delivered += delivered

        # Node energy consumption
        tot_energy_consumed_wh = sum(n.energy_capacity_wh - n.current_energy_wh for n in sim.nodes.values())

    # Aggregate Key Performance Indicators (KPIs)
    pdr = (total_packets_delivered / max(total_packets_gen, 1)) * 100.0
    avg_latency = float(np.mean(total_latencies_ms)) if total_latencies_ms else 100.0
    outage_prob = float(outage_occurrences / max(total_link_evaluations, 1))
    sim_duration_min = scenario.duration_s / 60.0
    ho_freq = float(handover_attempts / max(sim_duration_min, 0.1))
    ho_failure_rate = (handover_failures / max(handover_attempts, 1)) * 100.0
    throughput_mbps = (delivered_bits / 1.0e6) / max(scenario.duration_s, 1.0)

    # Energy in Joules per delivered Megabit: 1 Wh = 3600 Joules
    tot_energy_j = tot_energy_consumed_wh * 3600.0
    delivered_mbits = delivered_bits / 1.0e6
    energy_per_mbit = float(tot_energy_j / max(delivered_mbits, 0.01))

    # Mean resource utilization across nodes
    avg_util = float(np.mean([n.current_load for n in sim.nodes.values()])) * 100.0

    return {
        "method": method_name,
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name,
        "seed": random_seed,
        "pdr_percent": float(pdr),
        "avg_latency_ms": float(avg_latency),
        "outage_prob": float(outage_prob),
        "throughput_mbps": float(throughput_mbps),
        "handover_frequency_per_min": float(ho_freq),
        "handover_failure_rate_percent": float(ho_failure_rate),
        "avg_resource_util_percent": float(avg_util),
        "energy_j_per_mbit": float(energy_per_mbit),
    }


def run_comprehensive_benchmark(
    seeds: list[int] = [42, 101, 202],
    model_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Executes all 4 methods across all 5 scenarios with multiple random seeds.
    Aggregates means, standard deviations, and exports reproducible research artifacts.
    """
    if model_path is None:
        model_path = str(PROJECT_ROOT / "models" / "capro_predictor.joblib")
    predictor = DualUncertaintyPredictor.load(model_path)

    methods = [
        "M1_Reactive",
        "M2_Threshold_Predictive",
        "M3_Prediction_Only",
        "M4_CAPRO",
    ]

    all_results = []
    total_runs = len(methods) * len(ALL_SCENARIOS) * len(seeds)
    print(f"Starting optimized benchmark: {total_runs} simulation runs...")

    count = 0
    for sc in ALL_SCENARIOS:
        for m in methods:
            for s in seeds:
                count += 1
                res = run_single_simulation(m, sc, predictor, random_seed=s)
                all_results.append(res)
                if count % 5 == 0 or count == total_runs:
                    print(f"[{count:02d}/{total_runs}] Done: {m:23s} | {sc.name:28s} (Seed {s}) | PDR={res['pdr_percent']:5.1f}%, Outage={res['outage_prob']:.3f}, Lat={res['avg_latency_ms']:4.1f}ms")

    df = pd.DataFrame(all_results)

    # Save raw runs
    if output_dir is None:
        output_dir = PROJECT_ROOT / "results" / "metrics"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_dir / "benchmark_results_raw.csv", index=False)

    # Summary statistics: Mean and Std Dev grouped by scenario and method
    summary_df = df.groupby(["scenario_id", "scenario_name", "method"]).agg({
        "pdr_percent": ["mean", "std"],
        "avg_latency_ms": ["mean", "std"],
        "outage_prob": ["mean", "std"],
        "throughput_mbps": ["mean", "std"],
        "handover_frequency_per_min": ["mean", "std"],
        "handover_failure_rate_percent": ["mean", "std"],
        "energy_j_per_mbit": ["mean", "std"],
    }).reset_index()

    summary_df.columns = ["_".join(col).strip("_") for col in summary_df.columns.values]
    summary_df.to_csv(output_dir / "benchmark_summary_stats.csv", index=False)

    with open(output_dir / "benchmark_summary.json", "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2)

    print(f"\nBenchmark completed successfully! Artifacts saved in {output_dir}")
    return df


if __name__ == "__main__":
    run_comprehensive_benchmark(seeds=[42, 101, 202])
