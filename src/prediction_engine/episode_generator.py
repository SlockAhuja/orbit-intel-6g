"""
ORBIT-INTEL 6G: Independent Multi-Episode Generator
Generates reproducible, diverse simulation episodes across Scenarios 1-5
without temporal leakage, recording multi-horizon link quality targets.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from dataclasses import dataclass, asdict
from typing import Optional
import numpy as np
import pandas as pd

from src.simulation_engine.network_simulator import NetworkSimulator
from src.simulation_engine.orbital import LEOSatelliteOrbit
from src.prediction_engine.feature_engineering import FeatureEngineer
from src.experiments.scenarios import ALL_SCENARIOS


@dataclass
class EpisodeMetadata:
    episode_id: int
    scenario_id: int
    scenario_name: str
    random_seed: int
    duration_s: int
    rain_rate_base_mm_h: float
    flutter_std_base: float
    num_samples: int
    num_active_links: int


class EpisodeGenerator:
    """
    Generates distinct, isolated simulation episodes for research-grade
    predictive link intelligence and uncertainty calibration.
    """

    HORIZONS = [1, 3, 5, 10]

    def __init__(self, base_seed: int = 1000, output_dir: Optional[Path] = None):
        self.base_seed = base_seed
        self.output_dir = output_dir or (PROJECT_ROOT / "phase2_experiments" / "episodes")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_episode(
        self,
        episode_id: int,
        scenario_id: int,
        duration_s: int = 60,
    ) -> tuple[pd.DataFrame, EpisodeMetadata]:
        """
        Executes a single simulation episode under specified scenario and seed.
        """
        seed = self.base_seed + episode_id * 107
        rng = np.random.default_rng(seed)

        scenario_cfg = ALL_SCENARIOS[scenario_id - 1]
        sim = NetworkSimulator(random_seed=seed)

        # Apply scenario-specific stochastic parameterizations
        rain_rate_base = 0.0
        flutter_std_base = 0.0

        if scenario_id == 1:
            # Nominal conditions: clear sky to very light drizzle
            rain_rate_base = float(rng.uniform(0.0, 2.0))
            flutter_std_base = float(rng.uniform(0.0, 0.4))
        elif scenario_id == 2:
            # Congestion surge
            rain_rate_base = float(rng.uniform(0.0, 3.0))
            flutter_std_base = float(rng.uniform(0.1, 0.5))
        elif scenario_id == 3:
            # Convective rain event: varying peak intensity and duration
            rain_rate_base = float(rng.uniform(40.0, 70.0))
            flutter_std_base = float(rng.uniform(0.8, 1.8))
        elif scenario_id == 4:
            # Satellite departure / handover: varying initial mean anomaly
            rain_rate_base = float(rng.uniform(2.0, 10.0))
            flutter_std_base = float(rng.uniform(0.2, 0.8))
        elif scenario_id == 5:
            # High volatility and channel flutter
            rain_rate_base = float(rng.uniform(15.0, 35.0))
            flutter_std_base = float(rng.uniform(2.5, 4.5))

        # Initial scenario step setup at t=0
        scenario_cfg.apply_step_fn(sim, 0)

        # Apply stochastic variations to scenario
        if scenario_id == 3:
            # Modify rain intensity
            storm_start = int(rng.integers(20, 28))
            storm_end = int(rng.integers(50, 58))
        elif scenario_id == 4:
            # Perturb initial mean anomaly slightly (+- 0.8 deg) so handover timing varies naturally
            sat1 = sim.nodes.get("SAT-01")
            if sat1 and isinstance(sat1.orbit, LEOSatelliteOrbit):
                anom_jitter = float(rng.uniform(-0.8, 0.8))
                n_mean = sat1.orbit.n_mean
                sat1.orbit = LEOSatelliteOrbit(
                    sat_id="SAT-01",
                    altitude_km=float(sim.cfg["leo_satellite"]["altitude_km"]),
                    inclination_deg=53.0,
                    raan_deg=75.0,
                    initial_mean_anomaly_deg=18.0 + (115.0 + anom_jitter) * n_mean * 180.0 / np.pi,
                )
                pos, vel, lat, lon = sat1.orbit.get_state_at_time(0.0)
                sat1.pos_ecef, sat1.vel_ecef, sat1.lat_deg, sat1.lon_deg = pos, vel, lat, lon

        # Execute simulation trajectory
        episode_history = []
        for t in range(1, duration_s + 1):
            if scenario_id == 3:
                sim.rain_rate_mm_h = rain_rate_base if (storm_start <= t <= storm_end) else 0.0
                sim.shadowing_flutter_std = flutter_std_base
            elif scenario_id == 5:
                sim.rain_rate_mm_h = rain_rate_base
                sim.shadowing_flutter_std = flutter_std_base
            else:
                scenario_cfg.apply_step_fn(sim, t)
                if scenario_id in (1, 2):
                    sim.rain_rate_mm_h = rain_rate_base
                    sim.shadowing_flutter_std = flutter_std_base

            snapshot = sim.step()
            episode_history.append(snapshot)

        # Extract features and multi-horizon future targets
        max_lookahead = max(self.HORIZONS)  # 10s
        min_history = 5                     # 5s window
        rows = []

        for t_idx in range(min_history, len(episode_history) - max_lookahead):
            current_snap = episode_history[t_idx]
            sim_time = current_snap["time_s"]

            for (u_id, n_id), link in current_snap["links"].items():
                # We retain all visible links or links with viable history
                if not link["is_visible"]:
                    continue

                # Construct chronological history window up to t_idx
                history_window = [
                    episode_history[tau]["links"][(u_id, n_id)]
                    for tau in range(t_idx - min_history, t_idx + 1)
                ]

                features = FeatureEngineer.extract_features_from_history(history_window, u_id, n_id)

                # Record metadata
                features["episode_id"] = episode_id
                features["scenario_id"] = scenario_id
                features["scenario_name"] = scenario_cfg.name
                features["time_s"] = sim_time
                features["user_id"] = u_id
                features["node_id"] = n_id
                features["tier"] = link["tier"]
                features["current_sinr_db"] = link["sinr_db"]
                features["rain_rate_mm_h"] = sim.rain_rate_mm_h
                features["flutter_std"] = sim.shadowing_flutter_std

                # Multi-horizon future targets
                for h in self.HORIZONS:
                    future_snap = episode_history[t_idx + h]
                    future_link = future_snap["links"][(u_id, n_id)]
                    features[f"target_sinr_{h}s"] = float(future_link["sinr_db"])
                    features[f"target_outage_{h}s"] = 1.0 if future_link["sinr_db"] < 3.0 else 0.0

                # Degradation target over 10s horizon (link drops by >= 3.0 dB)
                features["target_degradation_10s"] = (
                    1.0 if (features["target_sinr_10s"] - features["current_sinr_db"]) <= -3.0 else 0.0
                )

                rows.append(features)

        df_episode = pd.DataFrame(rows)

        metadata = EpisodeMetadata(
            episode_id=episode_id,
            scenario_id=scenario_id,
            scenario_name=scenario_cfg.name,
            random_seed=seed,
            duration_s=duration_s,
            rain_rate_base_mm_h=rain_rate_base,
            flutter_std_base=flutter_std_base,
            num_samples=len(df_episode),
            num_active_links=df_episode["node_id"].nunique() if len(df_episode) > 0 else 0,
        )

        return df_episode, metadata

    def generate_all_episodes(
        self,
        episodes_per_scenario: int = 6,
        duration_s: int = 60,
    ) -> tuple[pd.DataFrame, list[EpisodeMetadata]]:
        """
        Generates full dataset across all 5 scenarios with balanced episode counts.
        Total episodes = 5 * episodes_per_scenario (e.g. 5 * 6 = 30 episodes).
        """
        all_dfs = []
        all_metadata = []
        episode_counter = 0

        print(f"Generating {5 * episodes_per_scenario} independent simulation episodes...")
        for sc_id in range(1, 6):
            for i in range(episodes_per_scenario):
                df_ep, meta = self.run_episode(
                    episode_id=episode_counter,
                    scenario_id=sc_id,
                    duration_s=duration_s,
                )
                all_dfs.append(df_ep)
                all_metadata.append(meta)

                # Save individual episode CSV
                ep_file = self.output_dir / f"episode_{episode_counter:03d}_scen{sc_id}.csv"
                df_ep.to_csv(ep_file, index=False)

                episode_counter += 1
                if episode_counter % 5 == 0:
                    print(f"  Completed {episode_counter}/{5 * episodes_per_scenario} episodes...")

        consolidated_df = pd.concat(all_dfs, ignore_index=True)
        print(f"Consolidated dataset generated: {len(consolidated_df)} samples across {episode_counter} episodes.")

        # Save consolidated dataset
        consolidated_path = self.output_dir.parent / "all_episodes_telemetry.csv"
        consolidated_df.to_csv(consolidated_path, index=False)

        # Save metadata JSON
        meta_dict = [asdict(m) for m in all_metadata]
        meta_path = self.output_dir.parent / "episodes_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta_dict, f, indent=2)

        return consolidated_df, all_metadata


if __name__ == "__main__":
    gen = EpisodeGenerator()
    df, meta = gen.generate_all_episodes(episodes_per_scenario=6, duration_s=60)
    print("Done. Generated samples:", len(df))

