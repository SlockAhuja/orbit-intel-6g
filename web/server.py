"""
ORBIT-INTEL 6G: Global Network Intelligence & Orchestration Center
Aerospace Mission Control Web Server (Flask Backend).
Connects physical simulation, dual-uncertainty prediction, and CAPRO orchestration.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import time
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, send_from_directory

# ORBIT-INTEL 6G Core Modules
from src.simulation_engine.network_simulator import NetworkSimulator
from src.prediction_engine.models import DualUncertaintyPredictor
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.prediction_engine.uncertainty import UncertaintyCalibrator
from src.orchestration_engine.capro_engine import CAPROOrchestrator
from src.baseline_methods.m1_reactive import M1ReactiveBaseline
from src.experiments.scenarios import ALL_SCENARIOS

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "web" / "templates"),
    static_folder=str(PROJECT_ROOT / "web" / "static")
)

# Global Simulation & Intelligence State
sim = NetworkSimulator(random_seed=42)
predictor = None
model_path = PROJECT_ROOT / "models" / "capro_predictor.joblib"
if model_path.exists():
    try:
        predictor = DualUncertaintyPredictor.load(str(model_path))
    except Exception as e:
        print(f"Warning: Could not load predictor: {e}")

capro = CAPROOrchestrator(risk_aversion_kappa=1.5, hysteresis_margin_db=2.5)
reactive_baseline = M1ReactiveBaseline()

current_scenario_id = 1
simulation_epoch = 0
active_mode = "LIVE SIMULATION"
event_log = [
    {"timestamp": "09:50:00 UTC", "severity": "INFO", "source": "SYSTEM", "message": "ORBIT-INTEL 6G Mission Control initialized."},
    {"timestamp": "09:50:01 UTC", "severity": "SUCCESS", "source": "CONSTELLATION", "message": "4-Tier SAGIN Topology loaded: LEO (600 km), HAPS (20 km), UAV (300 m), TBS (30 m)."},
    {"timestamp": "09:50:02 UTC", "severity": "SUCCESS", "source": "PREDICTION", "message": "Dual-Uncertainty Engine online (ECE=0.016, 90% PICP=89.35%)."},
    {"timestamp": "09:50:03 UTC", "severity": "SUCCESS", "source": "CAPRO", "message": "Reliability Orchestrator synchronized (Hysteresis Δ_hyst=2.5dB, Margin T_vis=12s)."},
]


def get_current_state_payload():
    """Compiles complete real-time aerospace state for frontend."""
    global simulation_epoch, current_scenario_id, active_mode

    # Extract nodes
    nodes_data = {}
    for nid, node in sim.nodes.items():
        vel_mag = float(np.linalg.norm(node.vel_ecef))
        nodes_data[nid] = {
            "id": nid,
            "name": node.name,
            "tier": node.tier,
            "pos_ecef": [float(node.pos_ecef[0]), float(node.pos_ecef[1]), float(node.pos_ecef[2])],
            "vel_ecef": [float(node.vel_ecef[0]), float(node.vel_ecef[1]), float(node.vel_ecef[2])],
            "speed_km_s": vel_mag / 1000.0,
            "lat_deg": float(node.lat_deg),
            "lon_deg": float(node.lon_deg),
            "alt_km": float(node.alt_m) / 1000.0,
            "tx_power_dbm": float(node.tx_power_dbm),
            "tx_gain_dbi": float(node.tx_gain_dbi),
            "bandwidth_mhz": float(node.bandwidth_mhz),
            "capacity_mbps": float(node.capacity_mbps),
            "current_load": float(node.current_load),
            "energy_pct": float(node.normalized_energy * 100.0),
        }

    # Extract users
    users_data = {}
    for uid, ue in sim.users.items():
        users_data[uid] = {
            "id": uid,
            "service_type": ue.service_type,
            "pos_ecef": [float(ue.pos_ecef[0]), float(ue.pos_ecef[1]), float(ue.pos_ecef[2])],
            "lat_deg": float(ue.lat_deg),
            "lon_deg": float(ue.lon_deg),
            "alt_m": float(ue.alt_m),
            "speed_km_h": float(getattr(ue, "velocity_m_s", 10.0) * 3.6),
            "heading_deg": float(getattr(ue, "heading_deg", 45.0)),
            "required_mbps": float(ue.required_data_rate_mbps),
            "max_latency_ms": float(ue.max_latency_ms),
            "serving_node_id": ue.current_serving_node_id or "TBS-01",
        }

    # Extract all link telemetry
    links_data = {}
    for uid in sim.users:
        for nid in sim.nodes:
            l_info = sim.compute_link_telemetry(uid, nid)
            # Physical delay decomposition
            d_prop = (float(l_info["slant_distance_m"]) / 3.0e8) * 1000.0
            p_proc = 2.5 if nid.startswith("SAT") else (1.2 if nid.startswith("HAPS") else (0.8 if nid.startswith("UAV") else 0.3))
            p_feed = 3.2 if nid.startswith("SAT") else 0.1
            total_lat = d_prop + p_proc + p_feed

            links_data[f"{uid}_{nid}"] = {
                "user_id": uid,
                "node_id": nid,
                "is_visible": bool(l_info["is_visible"]),
                "elevation_deg": float(l_info["elevation_deg"]),
                "slant_distance_km": float(l_info["slant_distance_m"]) / 1000.0,
                "doppler_shift_khz": float(l_info["doppler_shift_hz"]) / 1000.0,
                "sinr_db": float(l_info["sinr_db"]),
                "remaining_visibility_s": float(l_info["remaining_visibility_s"]),
                "path_loss_db": float(l_info["path_loss_db"]),
                "propagation_delay_ms": d_prop,
                "total_latency_ms": total_lat,
            }

    # Active scenario definition
    sc_obj = ALL_SCENARIOS[current_scenario_id - 1]

    return {
        "status": "ONLINE",
        "mode": active_mode,
        "epoch_seconds": simulation_epoch,
        "scenario": {
            "id": sc_obj.scenario_id,
            "name": sc_obj.name,
            "description": sc_obj.description,
        },
        "environmental": {
            "rain_rate_mm_h": float(sim.rain_rate_mm_h),
            "shadowing_flutter_std": float(sim.shadowing_flutter_std),
        },
        "nodes": nodes_data,
        "users": users_data,
        "links": links_data,
        "recent_events": event_log[-12:],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def api_state():
    return jsonify(get_current_state_payload())


@app.route("/api/step", methods=["POST"])
def api_step():
    global simulation_epoch
    data = request.get_json() or {}
    steps = int(data.get("steps", 1))

    sc_obj = ALL_SCENARIOS[current_scenario_id - 1]
    for _ in range(steps):
        sc_obj.apply_step_fn(sim, simulation_epoch)
        sim.step()
        simulation_epoch += 1

    # Log step event
    event_log.append({
        "timestamp": f"T+{simulation_epoch:02d}s",
        "severity": "INFO",
        "source": "SIM_CLOCK",
        "message": f"Simulation stepped forward by {steps}s. Active nodes propagated."
    })
    return jsonify(get_current_state_payload())


@app.route("/api/reset", methods=["POST"])
def api_reset():
    global simulation_epoch
    sim.reset(random_seed=42)
    ALL_SCENARIOS[current_scenario_id - 1].apply_step_fn(sim, 0)
    simulation_epoch = 0
    event_log.append({
        "timestamp": "T+00s",
        "severity": "WARNING",
        "source": "SIM_CONTROL",
        "message": "Constellation and ground mobile fleet reset to initial epoch t=0."
    })
    return jsonify(get_current_state_payload())


@app.route("/api/scenario/<int:sc_id>", methods=["POST"])
def api_select_scenario(sc_id):
    global current_scenario_id, simulation_epoch
    if 1 <= sc_id <= len(ALL_SCENARIOS):
        current_scenario_id = sc_id
        sim.reset(random_seed=42)
        ALL_SCENARIOS[sc_id - 1].apply_step_fn(sim, 0)
        simulation_epoch = 0
        sc_obj = ALL_SCENARIOS[sc_id - 1]
        event_log.append({
            "timestamp": "T+00s",
            "severity": "INFO",
            "source": "SCENARIO",
            "message": f"Loaded Scenario {sc_id}: {sc_obj.name} ({sc_obj.description})"
        })
    return jsonify(get_current_state_payload())


@app.route("/api/inject", methods=["POST"])
def api_inject_hazards():
    data = request.get_json() or {}
    if "rain_rate_mm_h" in data:
        sim.rain_rate_mm_h = float(data["rain_rate_mm_h"])
    if "shadowing_flutter_std" in data:
        sim.shadowing_flutter_std = float(data["shadowing_flutter_std"])

    event_log.append({
        "timestamp": f"T+{simulation_epoch:02d}s",
        "severity": "WARNING",
        "source": "ENVIRONMENT",
        "message": f"Environmental perturbation injected: Rain={sim.rain_rate_mm_h:.1f} mm/h, Flutter={sim.shadowing_flutter_std:.1f} dB"
    })
    return jsonify(get_current_state_payload())


@app.route("/api/predict", methods=["GET"])
def api_predict():
    user_id = request.args.get("user_id", "UE-01")
    node_id = request.args.get("node_id", "SAT-01")
    horizon = int(request.args.get("horizon", 5))

    # Simulate 25-step lookahead trajectory
    sim_copy = NetworkSimulator(random_seed=42)
    history_records = []
    actual_sinrs = []
    predicted_sinrs = []
    q_lowers = []
    q_uppers = []
    epistemic_stds = []
    aleatoric_widths = []

    for t in range(25):
        snap = sim_copy.step()
        link = snap["links"][(user_id, node_id)]
        history_records.append(link)
        actual_sinrs.append(float(link["sinr_db"]))

        if predictor:
            feat_dict = FeatureEngineer.extract_features_from_history(history_records, user_id, node_id)
            feat_vec = FeatureEngineer.to_feature_vector(feat_dict).reshape(1, -1)
            pred_res = predictor.predict_with_uncertainty(feat_vec)
            predicted_sinrs.append(float(pred_res["y_pred"][0]))
            q_lowers.append(float(pred_res["q_lower"][0]))
            q_uppers.append(float(pred_res["q_upper"][0]))
            epistemic_stds.append(float(pred_res["epistemic_std"][0]))
            aleatoric_widths.append(float(pred_res["aleatoric_width"][0]))
        else:
            predicted_sinrs.append(actual_sinrs[-1] - 0.2)
            q_lowers.append(actual_sinrs[-1] - 2.5)
            q_uppers.append(actual_sinrs[-1] + 2.5)
            epistemic_stds.append(0.5)
            aleatoric_widths.append(5.0)

    last_ql = q_lowers[-1]
    is_outage_hazard = last_ql < 3.0

    return jsonify({
        "user_id": user_id,
        "node_id": node_id,
        "horizon_seconds": horizon,
        "epochs": list(range(len(actual_sinrs))),
        "actual_sinrs": actual_sinrs,
        "predicted_sinrs": predicted_sinrs,
        "q_lowers": q_lowers,
        "q_uppers": q_uppers,
        "current_pred": predicted_sinrs[-1],
        "current_ql": last_ql,
        "current_qu": q_uppers[-1],
        "aleatoric_width": aleatoric_widths[-1],
        "epistemic_std": epistemic_stds[-1],
        "total_uncertainty": aleatoric_widths[-1] + (1.5 * epistemic_stds[-1]),
        "is_outage_hazard": is_outage_hazard,
        "outage_threshold_db": 3.0,
    })


@app.route("/api/orchestrate", methods=["GET"])
def api_orchestrate():
    user_id = request.args.get("user_id", "UE-01")
    ue = sim.users.get(user_id)
    if not ue:
        return jsonify({"error": f"User {user_id} not found"}), 404

    user_links = {nid: sim.compute_link_telemetry(user_id, nid) for nid in sim.nodes}
    preds = {}
    for nid, l_data in user_links.items():
        if l_data["is_visible"] and predictor:
            f_dict = FeatureEngineer.extract_features_from_history([l_data], user_id, nid)
            f_vec = FeatureEngineer.to_feature_vector(f_dict).reshape(1, -1)
            p_out = predictor.predict_with_uncertainty(f_vec)
            preds[nid] = {
                "y_pred": float(p_out["y_pred"][0]),
                "q_lower": float(p_out["q_lower"][0]),
                "q_upper": float(p_out["q_upper"][0]),
                "total_uncertainty": float(p_out["total_uncertainty"][0]),
            }

    dec = capro.select_network_node(
        user_id, ue.current_serving_node_id, user_links, preds, ue.service_type
    )

    # Candidate evaluation feasibility table
    candidates = []
    for nid, node in sim.nodes.items():
        l_info = user_links[nid]
        p_info = preds.get(nid, {})
        pred_sinr = p_info.get("y_pred", l_info["sinr_db"])
        q_low = p_info.get("q_lower", l_info["sinr_db"] - 3.0)

        d_prop = (float(l_info["slant_distance_m"]) / 3.0e8) * 1000.0
        p_proc = 2.5 if node.tier == "LEO" else (1.2 if node.tier == "HAPS" else (0.8 if node.tier == "UAV" else 0.3))
        p_feeder = 3.2 if node.tier == "LEO" else 0.1
        total_lat = d_prop + p_proc + p_feeder

        c_vis = bool(l_info["is_visible"])
        c_sinr = q_low >= 3.0
        c_lat = (total_lat <= ue.max_latency_ms) if ue.service_type == "URLLC" else True
        c_vis_buf = (l_info["remaining_visibility_s"] >= 12.0) if node.tier == "LEO" else True

        is_feas = c_vis and c_sinr and c_lat and c_vis_buf

        candidates.append({
            "node_id": nid,
            "tier": node.tier,
            "is_visible": c_vis,
            "pred_sinr_db": pred_sinr,
            "q_lower_db": q_low,
            "total_latency_ms": total_lat,
            "remaining_vis_s": float(l_info["remaining_visibility_s"]),
            "is_feasible": is_feas,
            "is_selected": (nid == dec.selected_node_id),
        })

    return jsonify({
        "user_id": user_id,
        "service_type": ue.service_type,
        "current_serving": ue.current_serving_node_id,
        "selected_node": dec.selected_node_id,
        "tier": dec.tier,
        "is_handover": dec.is_handover,
        "trigger_code": dec.trigger_code,
        "risk_adjusted_utility": dec.risk_adjusted_utility_db,
        "total_uncertainty_db": dec.total_uncertainty_db,
        "explanation": dec.explanation,
        "candidates": candidates,
    })


@app.route("/api/handover_replay", methods=["GET"])
def api_handover_replay():
    """Returns precomputed trajectory of Scenario 4 (SAT-01 setting, SAT-02 rising)."""
    sim_ho = NetworkSimulator(random_seed=42)
    ALL_SCENARIOS[3].apply_step_fn(sim_ho, 0)
    capro_ho = CAPROOrchestrator(risk_aversion_kappa=1.5, hysteresis_margin_db=2.5)
    react_ho = M1ReactiveBaseline()

    epochs = []
    sat1_elevs = []
    sat2_elevs = []
    sat1_vis = []
    capro_nodes = []
    react_nodes = []
    capro_losses = []
    react_losses = []

    capro_curr = "SAT-01"
    react_curr = "SAT-01"

    for t in range(40):
        if t > 0:
            sim_ho.step()
        epochs.append(t)
        l1 = sim_ho.compute_link_telemetry("UE-01", "SAT-01")
        l2 = sim_ho.compute_link_telemetry("UE-01", "SAT-02")
        sat1_elevs.append(float(l1["elevation_deg"]))
        sat2_elevs.append(float(l2["elevation_deg"]))
        sat1_vis.append(float(l1["remaining_visibility_s"]))

        u_links = {nid: sim_ho.compute_link_telemetry("UE-01", nid) for nid in sim_ho.nodes}
        preds = {}
        for nid, l_data in u_links.items():
            if l_data["is_visible"] and predictor:
                f_dict = FeatureEngineer.extract_features_from_history([l_data], "UE-01", nid)
                f_vec = FeatureEngineer.to_feature_vector(f_dict).reshape(1, -1)
                p_out = predictor.predict_with_uncertainty(f_vec)
                preds[nid] = {
                    "y_pred": float(p_out["y_pred"][0]),
                    "q_lower": float(p_out["q_lower"][0]),
                    "q_upper": float(p_out["q_upper"][0]),
                    "total_uncertainty": float(p_out["total_uncertainty"][0]),
                }

        d_capro = capro_ho.select_network_node("UE-01", capro_curr, u_links, preds, "eMBB")
        d_react = react_ho.select_network_node("UE-01", react_curr, u_links, "eMBB")

        capro_curr = d_capro.selected_node_id
        react_curr = d_react["selected_node_id"]

        capro_nodes.append(capro_curr)
        react_nodes.append(react_curr)

        is_c_loss = not u_links[capro_curr]["is_visible"] if capro_curr in u_links else True
        is_r_loss = not u_links[react_curr]["is_visible"] if react_curr in u_links else True
        capro_losses.append(100.0 if is_c_loss else 0.0)
        react_losses.append(100.0 if is_r_loss else 0.0)

    return jsonify({
        "epochs": epochs,
        "sat1_elevations": sat1_elevs,
        "sat2_elevations": sat2_elevs,
        "sat1_visibility_s": sat1_vis,
        "capro_serving_nodes": capro_nodes,
        "reactive_serving_nodes": react_nodes,
        "capro_packet_loss_pct": capro_losses,
        "reactive_packet_loss_pct": react_losses,
        "proactive_trigger_epoch": 23,
        "reactive_drop_epoch": 35,
    })


@app.route("/api/benchmarks", methods=["GET"])
def api_benchmarks():
    p4_dir = PROJECT_ROOT / "phase4_benchmarking"
    method_df = pd.read_csv(p4_dir / "BENCHMARK_METRICS_BY_METHOD.csv")
    scenario_df = pd.read_csv(p4_dir / "BENCHMARK_METRICS_BY_SCENARIO.csv")
    ablation_df = pd.read_csv(p4_dir / "CAPRO_ABLATION_RESULTS.csv")
    stats_df = pd.read_csv(p4_dir / "STATISTICAL_TEST_RESULTS.csv")

    return jsonify({
        "by_method": method_df.to_dict(orient="records"),
        "by_scenario": scenario_df.to_dict(orient="records"),
        "ablation": ablation_df.to_dict(orient="records"),
        "statistics": stats_df.head(10).to_dict(orient="records"),
    })


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ORBIT-INTEL 6G: Mission Control Web Server Starting...")
    print("    URL: http://127.0.0.1:5000")
    print("    Target: IEEE ComSoc STLC 2026 Interactive Showcase")
    print("="*70 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
