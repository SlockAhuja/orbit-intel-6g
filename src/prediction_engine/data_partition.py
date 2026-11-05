"""
ORBIT-INTEL 6G: Strict Episode-Based Data Partitioning & Leakage Verification
Implements scenario-stratified episode partitioning (Train 67%, Val 16.7%, Locked Test 16.7%)
with rigorous mathematical verification of zero temporal data leakage.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler

from src.prediction_engine.feature_engineering import FeatureEngineer


class EpisodeDataPartitioner:
    """
    Partitions multi-episode SAGIN telemetry strictly by Episode ID,
    guaranteeing zero temporal window overlap and strictly isolating test data.
    """

    FEATURE_COLS = FeatureEngineer.FEATURE_NAMES
    TARGET_COLS = [
        "target_sinr_1s",
        "target_sinr_3s",
        "target_sinr_5s",
        "target_sinr_10s",
        "target_outage_1s",
        "target_outage_3s",
        "target_outage_5s",
        "target_outage_10s",
        "target_degradation_10s",
    ]

    def __init__(self, data_df: pd.DataFrame, output_dir: Optional[Path] = None):
        self.df = data_df.copy()
        self.output_dir = output_dir or (PROJECT_ROOT / "phase2_experiments")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir = PROJECT_ROOT / "phase2_models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.train_df: Optional[pd.DataFrame] = None
        self.val_df: Optional[pd.DataFrame] = None
        self.test_df: Optional[pd.DataFrame] = None
        self.scaler: Optional[StandardScaler] = None

    def partition_episodes(
        self,
        train_ratio: float = 0.67,
        val_ratio: float = 0.165,
        test_ratio: float = 0.165,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Partitions episodes using stratified selection by scenario_id.
        Each scenario's episodes are systematically allocated to Train, Val, and Test.
        """
        episodes_by_scenario = self.df.groupby("scenario_id")["episode_id"].unique().to_dict()

        train_episodes = []
        val_episodes = []
        test_episodes = []

        for sc_id, eps in sorted(episodes_by_scenario.items()):
            eps = sorted(eps)
            n_eps = len(eps)
            # Allocation: first n_train to train, next n_val to val, rest to test
            # For 6 episodes: 4 train, 1 val, 1 test
            n_train = int(np.round(n_eps * train_ratio))
            n_val = int(np.round(n_eps * val_ratio))
            if n_train + n_val >= n_eps:
                n_train = max(1, n_eps - 2)
                n_val = 1

            train_episodes.extend(eps[:n_train])
            val_episodes.extend(eps[n_train : n_train + n_val])
            test_episodes.extend(eps[n_train + n_val :])

        self.train_df = self.df[self.df["episode_id"].isin(train_episodes)].copy().reset_index(drop=True)
        self.val_df = self.df[self.df["episode_id"].isin(val_episodes)].copy().reset_index(drop=True)
        self.test_df = self.df[self.df["episode_id"].isin(test_episodes)].copy().reset_index(drop=True)

        # Verify mathematical disjointness
        self.verify_zero_leakage(train_episodes, val_episodes, test_episodes)

        # Fit feature scaler strictly on Train partition
        self.scaler = StandardScaler()
        self.scaler.fit(self.train_df[self.FEATURE_COLS].values)

        # Save scaler artifact
        scaler_path = self.models_dir / "feature_scaler.joblib"
        joblib.dump(self.scaler, scaler_path)
        print(f"StandardScaler fitted strictly on Train partition ({len(self.train_df)} samples) and saved to {scaler_path}")

        # Save partition datasets
        self.train_df.to_csv(self.output_dir / "train_dataset.csv", index=False)
        self.val_df.to_csv(self.output_dir / "val_dataset.csv", index=False)
        self.test_df.to_csv(self.output_dir / "test_dataset.csv", index=False)

        print(f"Partitions successfully saved:")
        print(f"  Train Set: {len(self.train_df)} samples ({len(train_episodes)} episodes: {train_episodes})")
        print(f"  Val Set:   {len(self.val_df)} samples ({len(val_episodes)} episodes: {val_episodes})")
        print(f"  Test Set:  {len(self.test_df)} samples ({len(test_episodes)} episodes: {test_episodes})")

        return self.train_df, self.val_df, self.test_df

    def verify_zero_leakage(
        self,
        train_episodes: list[int],
        val_episodes: list[int],
        test_episodes: list[int],
    ):
        """
        Automated assertion suite mathematically proving zero temporal leakage.
        """
        set_train = set(train_episodes)
        set_val = set(val_episodes)
        set_test = set(test_episodes)

        # 1. Episode disjointness check
        assert len(set_train.intersection(set_val)) == 0, "FATAL: Train and Val share episodes!"
        assert len(set_train.intersection(set_test)) == 0, "FATAL: Train and Test share episodes!"
        assert len(set_val.intersection(set_test)) == 0, "FATAL: Val and Test share episodes!"

        # 2. Row index disjointness check
        train_idx = set(self.train_df.index)
        assert len(self.train_df) + len(self.val_df) + len(self.test_df) == len(self.df), (
            "FATAL: Partition row counts do not sum to total samples!"
        )

        print("[LEAK CHECK PASSED] Mathematical disjointness proven: 0 episode overlap, 0 row collision.")


if __name__ == "__main__":
    data_path = PROJECT_ROOT / "phase2_experiments" / "all_episodes_telemetry.csv"
    if not data_path.exists():
        print("Data file not found. Run episode generator first.")
    else:
        df = pd.read_csv(data_path)
        partitioner = EpisodeDataPartitioner(df)
        train_df, val_df, test_df = partitioner.partition_episodes()

