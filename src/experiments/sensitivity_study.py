"""
ORBIT-INTEL 6G: Phase 5 Sensitivity, Robustness & Multi-Horizon Study Engine
Executes parameter sweeps, distribution shift stress tests, and prediction horizon studies.
Uses parallel execution for high-throughput scientific evaluation across 8 CPU workers.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
from typing import Optional
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from src.simulation_engine.network_simulator import NetworkSimulator
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.models import DualUncertaintyPredictor
from src.baseline_methods.m1_reactive import M1ReactiveBaseline
from src.baseline_methods.m2_threshold_predictive import M2ThresholdPredictiveBaseline
from src.baseline_methods.m3_prediction_only import M3PredictionOnlyBaseline
from src.orchestration_engine.capro_engine import CAPROOrchestrator
from src.experiments.scenarios import ALL_SCENARIOS, ScenarioConfig


def run_parameterized_episode(
    method_name: str,
    scenario: ScenarioConfig,
    predictor: DualUncertaintyPredictor,
    random_seed: int = 42,
    horizon_s: int = 3,
    delta_hyst: float = 0.08,
    custom_weights_urllc: Optional[dict] = None,
    custom_weights_embb: Optional[dict] = None,
    stress_rain_mm_h: float = 0.0,
    stress_flutter_std: float = 0.0,
    experiment_tag: str = "nominal",
    experiment_param: str = "default",
) -> dict:
    """
    Executes a single simulation episode parameterized for Phase 5 sensitivity/robustness sweeps.
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
        orchestrator = CAPROOrchestrator()
        orchestrator.hysteresis_margin = delta_hyst
        if custom_weights_urllc:
            orchestrator.weights_urllc.update(custom_weights_urllc)
        if custom_weights_embb:
            orchestrator.weights_embb.update(custom_weights_embb)
    else:
        raise ValueError(f"Unknown method {method_name}")

    user_attachments = {u_id: None for u_id in sim.users}
    history_window = []

    total_packets_gen = 0
    total_packets_delivered = 0
    total_packets_lost = 0
    latencies_all_ms = []
    sla_violations_total = 0
    sla_violations_urllc = 0
    sla_violations_embb = 0
    outage_occurrences = 0
    total_link_evaluations = 0
    handover_attempts = 0
    epistemic_stds = []

    def get_cohort(uid: str) -> str:
        idx = int(uid.split("-")[-1])
        if 1 <= idx <= 3:
            return "Urban"
        elif 4 <= idx <= 6:
            return "Suburban"
        elif 7 <= idx <= 9:
            return "Remote"
        return "Maritime"

    for t in range(scenario.duration_s):
        scenario.apply_step_fn(sim, t)

        # Apply stress overrides if requested (Distribution Shift test)
        if stress_rain_mm_h > 0 and 20 <= t <= 50:
            sim.rain_rate_mm_h = stress_rain_mm_h
        if stress_flutter_std > 0:
            sim.shadowing_flutter_std = stress_flutter_std

        snapshot = sim.step()
        history_window.append(snapshot)
        if len(history_window) > 10:
            history_window.pop(0)

        # Extract features
        feat_vectors_batch = []
        link_keys_batch = []
        needs_ml = method_name in ["M3_Prediction_Only"] or method_name.startswith("M4_CAPRO")

        if needs_ml:
            for u_id in sim.users:
                for n_id in sim.nodes:
                    link_state = snapshot["links"][(u_id, n_id)]
                    if link_state["is_visible"]:
                        f_dict = FeatureEngineer.extract_features_from_history(history_window, u_id, n_id)
                        link_keys_batch.append((u_id, n_id))
                        feat_vectors_batch.append(FeatureEngineer.to_feature_vector(f_dict))

        # Vectorized batch prediction
        predictions_by_user = {u_id: {} for u_id in sim.users}
        if needs_ml and feat_vectors_batch:
            X_batch = np.array(feat_vectors_batch, dtype=np.float32)
            preds_batch = predictor.predict_with_uncertainty(X_batch)
            for idx, (u_id, n_id) in enumerate(link_keys_batch):
                y_p = float(preds_batch["y_pred"][idx])
                q_low = float(preds_batch["q_lower"][idx])
                u_tot = float(preds_batch["total_uncertainty"][idx])
                s_epi = float(preds_batch["epistemic_std"][idx])

                # Physics-based uncertainty dilation over forecast horizon: sigma(H) = sigma * sqrt(H / 3)
                if horizon_s != 3:
                    dilation = np.sqrt(horizon_s / 3.0)
                    u_tot *= dilation
                    q_low = y_p - 1.645 * u_tot

                predictions_by_user[u_id][n_id] = {
                    "y_pred": y_p,
                    "q_lower": q_low,
                    "q_upper": float(preds_batch["q_upper"][idx]),
                    "epistemic_std": s_epi,
                    "aleatoric_width": float(preds_batch["aleatoric_width"][idx]),
                    "total_uncertainty": u_tot,
                }
                epistemic_stds.append(s_epi)

        # User attachment decision
        for u_id, user in sim.users.items():
            curr_node_id = user_attachments[u_id]
            user_links = {n_id: snapshot["links"][(u_id, n_id)] for n_id in sim.nodes}

            if method_name == "M1_Reactive":
                dec = orchestrator.select_network_node(u_id, curr_node_id, user_links, user.service_type)
                selected_node_id = dec["selected_node_id"]
                is_ho = dec["is_handover"]
            elif method_name == "M2_Threshold_Predictive":
                user_feats = {
                    n_id: FeatureEngineer.extract_features_from_history(history_window, u_id, n_id)
                    for n_id in sim.nodes
                }
                dec = orchestrator.select_network_node(u_id, curr_node_id, user_links, user_feats, user.service_type)
                selected_node_id = dec["selected_node_id"]
                is_ho = dec["is_handover"]
            elif method_name == "M3_Prediction_Only":
                pt_preds = {nid: p["y_pred"] for nid, p in predictions_by_user[u_id].items()}
                dec = orchestrator.select_network_node(u_id, curr_node_id, user_links, pt_preds, user.service_type)
                selected_node_id = dec["selected_node_id"]
                is_ho = dec["is_handover"]
            else:  # M4_CAPRO
                exp_dec = orchestrator.select_network_node(
                    u_id, curr_node_id, user_links, predictions_by_user[u_id], user.service_type
                )
                selected_node_id = exp_dec.selected_node_id
                is_ho = exp_dec.is_handover

            if is_ho and (selected_node_id != curr_node_id):
                handover_attempts += 1
                if curr_node_id and curr_node_id in sim.nodes:
                    sim.nodes[curr_node_id].release_load(user.required_data_rate_mbps)
                user_attachments[u_id] = selected_node_id
                if selected_node_id and selected_node_id in sim.nodes:
                    sim.nodes[selected_node_id].allocate_load(user.required_data_rate_mbps)
            elif curr_node_id is None and selected_node_id:
                user_attachments[u_id] = selected_node_id
                if selected_node_id in sim.nodes:
                    sim.nodes[selected_node_id].allocate_load(user.required_data_rate_mbps)

        # Packet transmission and SLA evaluation
        for u_id, user in sim.users.items():
            active_node_id = user_attachments[u_id]
            pkts_to_gen = 10
            total_packets_gen += pkts_to_gen

            if active_node_id is None:
                total_packets_lost += pkts_to_gen
                sla_violations_total += pkts_to_gen
                if user.service_type == "URLLC":
                    sla_violations_urllc += pkts_to_gen
                else:
                    sla_violations_embb += pkts_to_gen
                continue

            active_node = sim.nodes[active_node_id]
            link_state = snapshot["links"][(u_id, active_node_id)]
            total_link_evaluations += 1

            if not link_state["is_visible"]:
                outage_occurrences += 1
                total_packets_lost += pkts_to_gen
                sla_violations_total += pkts_to_gen
                if user.service_type == "URLLC":
                    sla_violations_urllc += pkts_to_gen
                else:
                    sla_violations_embb += pkts_to_gen
                continue

            sinr = link_state["sinr_db"]
            if sinr < user.min_sinr_threshold_db:
                outage_occurrences += 1

            delay_info = sim.traffic_engine.compute_transmission_delay_ms(
                slant_distance_m=link_state["slant_distance_m"],
                packet_size_bytes=256 if user.service_type == "URLLC" else 1500,
                allocated_rate_mbps=user.required_data_rate_mbps,
                node_load=active_node.current_load,
                tier=active_node.tier,
            )
            lat_ms = delay_info["t_total_ms"]
            latencies_all_ms.append(lat_ms)

            is_sla_delay_violated = (lat_ms > user.max_latency_ms)

            delivered = 0
            for _ in range(pkts_to_gen):
                if sinr < user.min_sinr_threshold_db or is_sla_delay_violated:
                    total_packets_lost += 1
                    sla_violations_total += 1
                    if user.service_type == "URLLC":
                        sla_violations_urllc += 1
                    else:
                        sla_violations_embb += 1
                    continue

                margin_db = sinr - user.min_sinr_threshold_db
                bler = 1e-4 if margin_db > 6.0 else (0.01 if margin_db > 2.0 else 0.08)
                if rng.random() > bler:
                    delivered += 1
                else:
                    total_packets_lost += 1

            total_packets_delivered += delivered

    pdr = (total_packets_delivered / max(1, total_packets_gen)) * 100.0
    sla_viol_pct = (sla_violations_total / max(1, total_packets_gen)) * 100.0
    sla_viol_urllc_pct = (sla_violations_urllc / max(1, total_packets_gen // 2)) * 100.0
    outage_prob = outage_occurrences / max(1, total_link_evaluations)
    mean_lat = float(np.mean(latencies_all_ms)) if latencies_all_ms else 100.0
    mean_epi = float(np.mean(epistemic_stds)) if epistemic_stds else 0.0

    return {
        "experiment_tag": experiment_tag,
        "experiment_param": experiment_param,
        "method": method_name,
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name,
        "seed": random_seed,
        "pdr_percent": float(pdr),
        "mean_latency_ms": float(mean_lat),
        "outage_probability": float(outage_prob),
        "sla_violation_rate_percent": float(sla_viol_pct),
        "sla_violation_urllc_percent": float(sla_viol_urllc_pct),
        "handover_count": int(handover_attempts),
        "mean_epistemic_uncertainty_db": float(mean_epi),
    }


def run_all_sensitivity_experiments():
    out_dir = PROJECT_ROOT / "phase5_robustness"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("--- 1. LOADING VALIDATED PREDICTOR ---")
    model_path = PROJECT_ROOT / "models" / "capro_predictor.joblib"
    predictor = DualUncertaintyPredictor.load(model_path)

    seeds = [101, 102, 103, 104, 105]  # 5 seeds per configuration

    # ==========================================
    # CAMPAIGN 1: PREDICTION HORIZON SWEEP (1, 3, 5, 10 s)
    # ==========================================
    print("\n--- 2. PREPARING PREDICTION HORIZON SWEEP (H in {1, 3, 5, 10} s) ---")
    horizon_tasks = []
    for h in [1, 3, 5, 10]:
        for sc in ALL_SCENARIOS:
            for s in seeds:
                horizon_tasks.append(("M4_CAPRO", sc, s, h, 0.08, None, None, 0.0, 0.0, "Horizon_Sweep", f"H_{h}s"))

    # ==========================================
    # CAMPAIGN 2: HYSTERESIS MARGIN SWEEP (Delta in [0.00 to 0.18])
    # ==========================================
    print("--- 3. PREPARING HYSTERESIS MARGIN SWEEP (Delta in [0.00, 0.02, 0.05, 0.08, 0.12, 0.18]) ---")
    hyst_tasks = []
    for d in [0.00, 0.02, 0.05, 0.08, 0.12, 0.18]:
        for sc in ALL_SCENARIOS:
            for s in seeds:
                hyst_tasks.append(("M4_CAPRO", sc, s, 3, d, None, None, 0.0, 0.0, "Hysteresis_Sweep", f"Delta_{d:.2f}"))

    # ==========================================
    # CAMPAIGN 3: MULTI-OBJECTIVE WEIGHT SENSITIVITY SWEEP
    # ==========================================
    print("--- 4. PREPARING MULTI-OBJECTIVE WEIGHT SENSITIVITY SWEEP ---")
    weight_profiles = {
        "Balanced_Nominal": {"w_link": 0.35, "w_lat": 0.35, "w_cap": 0.10, "w_ho": 0.15, "w_risk": 0.05},
        "Reliability_Dominant": {"w_link": 0.60, "w_lat": 0.15, "w_cap": 0.05, "w_ho": 0.15, "w_risk": 0.05},
        "Latency_Dominant": {"w_link": 0.15, "w_lat": 0.60, "w_cap": 0.05, "w_ho": 0.15, "w_risk": 0.05},
        "Capacity_Dominant": {"w_link": 0.20, "w_lat": 0.10, "w_cap": 0.50, "w_ho": 0.15, "w_risk": 0.05},
        "Stability_Dominant": {"w_link": 0.25, "w_lat": 0.25, "w_cap": 0.10, "w_ho": 0.35, "w_risk": 0.05},
    }
    weight_tasks = []
    for p_name, w_dict in weight_profiles.items():
        for sc in ALL_SCENARIOS:
            for s in seeds:
                weight_tasks.append(("M4_CAPRO", sc, s, 3, 0.08, w_dict, None, 0.0, 0.0, "Weight_Profile_Sweep", p_name))

    # ==========================================
    # CAMPAIGN 4: DISTRIBUTION SHIFT / STRESS TEST
    # ==========================================
    print("--- 5. PREPARING DISTRIBUTION SHIFT / STRESS TEST (Extreme Rain 90 mm/h + Flutter 5.0 dB) ---")
    stress_tasks = []
    for m in ["M1_Reactive", "M2_Threshold_Predictive", "M3_Prediction_Only", "M4_CAPRO"]:
        for sc in [ALL_SCENARIOS[2], ALL_SCENARIOS[4]]:  # Rain & Flutter scenarios
            for s in seeds:
                stress_tasks.append((m, sc, s, 3, 0.08, None, None, 90.0, 5.0, "Distribution_Shift_Stress", f"{m}_SevereOOD"))

    all_tasks = horizon_tasks + hyst_tasks + weight_tasks + stress_tasks
    print(f"\nTotal Sensitivity Episodes to Execute: {len(all_tasks)} across 8 parallel worker processes...")
    t0 = time.time()

    results = Parallel(n_jobs=8, backend="loky")(
        delayed(run_parameterized_episode)(
            m, sc, predictor, s, h, d, w_u, w_e, r_stress, f_stress, tag, param
        )
        for m, sc, s, h, d, w_u, w_e, r_stress, f_stress, tag, param in all_tasks
    )

    t_elapsed = time.time() - t0
    print(f"Completed {len(results)} sensitivity episodes in {t_elapsed:.1f} s ({len(results)/t_elapsed:.1f} eps/sec)!")

    df = pd.DataFrame(results)
    df.to_csv(out_dir / "PARAMETER_SWEEP_RESULTS.csv", index=False)
    print(f"Saved PARAMETER_SWEEP_RESULTS.csv with {len(df)} records.")

    # Aggregate robustness summary
    summary_robustness = df.groupby(["experiment_tag", "experiment_param"]).agg({
        "pdr_percent": ["mean", "std"],
        "mean_latency_ms": ["mean", "std"],
        "sla_violation_rate_percent": ["mean", "std"],
        "sla_violation_urllc_percent": ["mean", "std"],
        "outage_probability": ["mean", "std"],
        "handover_count": ["mean", "std"],
        "mean_epistemic_uncertainty_db": ["mean", "std"],
    }).reset_index()
    summary_robustness.columns = ["_".join(col).strip("_") for col in summary_robustness.columns.values]
    summary_robustness.to_csv(out_dir / "ROBUSTNESS_METRICS.csv", index=False)
    print("Saved ROBUSTNESS_METRICS.csv")


if __name__ == "__main__":
    run_all_sensitivity_experiments()
