"""
ORBIT-INTEL 6G: Unified Space-Air-Ground Integrated Network Simulator
Coordinates 4-tier SAGIN nodes, channel physics, orbital kinematics, and telemetry state generation.
"""

from typing import Optional
import numpy as np
import yaml
from pathlib import Path

from src.simulation_engine.nodes import (
    NetworkNode,
    LEOSatelliteNode,
    HAPSNode,
    UAVNode,
    TBSNode,
    UserEquipmentNode,
)
from src.simulation_engine.orbital import OrbitalMechanics
from src.channel_models.propagation import PropagationModel
from src.channel_models.doppler import DopplerModel
from src.channel_models.sinr_calculator import SINRCalculator
from src.simulation_engine.traffic import TrafficEngine


class NetworkSimulator:
    """
    Discrete-time SAGIN simulator for 6G Non-Terrestrial Networks.
    """

    def __init__(self, config_path: Optional[str] = None, random_seed: int = 42):
        self.seed = random_seed
        self.rng = np.random.default_rng(self.seed)

        # Load configuration
        if config_path is None:
            config_path = str(Path(__file__).resolve().parents[2] / "config" / "simulation_config.yaml")

        with open(config_path, "r") as f:
            self.cfg = yaml.safe_load(f)

        # Channel & physics engines
        self.propagation = PropagationModel(speed_of_light=self.cfg["system"]["speed_of_light_m_s"])
        self.doppler = DopplerModel(speed_of_light=self.cfg["system"]["speed_of_light_m_s"])
        self.sinr_calc = SINRCalculator(
            boltzmann_k=self.cfg["system"]["boltzmann_constant"],
            temperature_k=self.cfg["system"]["temperature_system_k"],
            noise_figure_db=self.cfg["user_equipment"]["noise_figure_db"],
        )
        self.traffic_engine = TrafficEngine(speed_of_light=self.cfg["system"]["speed_of_light_m_s"])

        # Network entity registries
        self.nodes: dict[str, NetworkNode] = {}
        self.users: dict[str, UserEquipmentNode] = {}

        # Simulation clock
        self.current_time_s = 0.0
        self.dt = 1.0

        # Environmental conditions (can be modified by scenarios)
        self.rain_rate_mm_h = 0.0
        self.carrier_freq_s_band = self.cfg["system"]["carrier_frequency_s_band_hz"]
        self.carrier_freq_ka_band = self.cfg["system"]["carrier_frequency_ka_band_hz"]
        self.shadowing_flutter_std = 0.0
        self.disabled_links: set[tuple[str, str]] = set()

        # Telemetry history for feature generation
        self.telemetry_history: list[dict] = []

        # Setup standard topology
        self.setup_default_topology()

    def setup_default_topology(self):
        """Builds default heterogeneous SAGIN network topology."""
        self.nodes.clear()
        self.users.clear()

        # Reference center: 22.0° N, 75.0° E
        ref_lat, ref_lon = 22.0, 75.0

        # Tier 1: LEO Satellites (2 satellites in orbit)
        sat1 = LEOSatelliteNode(
            node_id="SAT-01",
            name="LEO-Polar-1",
            altitude_km=self.cfg["leo_satellite"]["altitude_km"],
            inclination_deg=53.0,
            raan_deg=75.0,
            initial_mean_anomaly_deg=10.0,
            tx_power_dbm=self.cfg["leo_satellite"]["tx_power_dbm"],
            tx_gain_dbi=self.cfg["leo_satellite"]["tx_antenna_gain_dbi"],
            bandwidth_mhz=self.cfg["leo_satellite"]["bandwidth_mhz"],
            capacity_mbps=self.cfg["leo_satellite"]["capacity_mbps"],
        )
        sat2 = LEOSatelliteNode(
            node_id="SAT-02",
            name="LEO-Polar-2",
            altitude_km=self.cfg["leo_satellite"]["altitude_km"],
            inclination_deg=53.0,
            raan_deg=85.0,
            initial_mean_anomaly_deg=-15.0,
            tx_power_dbm=self.cfg["leo_satellite"]["tx_power_dbm"],
            tx_gain_dbi=self.cfg["leo_satellite"]["tx_antenna_gain_dbi"],
            bandwidth_mhz=self.cfg["leo_satellite"]["bandwidth_mhz"],
            capacity_mbps=self.cfg["leo_satellite"]["capacity_mbps"],
        )
        self.nodes[sat1.node_id] = sat1
        self.nodes[sat2.node_id] = sat2

        # Tier 2: HAPS (Stratospheric)
        haps = HAPSNode(
            node_id="HAPS-01",
            name="Stratospheric-Relay-1",
            center_lat_deg=ref_lat,
            center_lon_deg=ref_lon,
            altitude_km=self.cfg["haps"]["altitude_km"],
            drift_speed_m_s=self.cfg["haps"]["drift_speed_m_s"],
            tx_power_dbm=self.cfg["haps"]["tx_power_dbm"],
            tx_gain_dbi=self.cfg["haps"]["tx_antenna_gain_dbi"],
            bandwidth_mhz=self.cfg["haps"]["bandwidth_mhz"],
            capacity_mbps=self.cfg["haps"]["capacity_mbps"],
        )
        self.nodes[haps.node_id] = haps

        # Tier 3: UAV Relay (Hotspot loiter)
        uav = UAVNode(
            node_id="UAV-01",
            name="Airborne-Hotspot-1",
            center_lat_deg=ref_lat + 0.02,
            center_lon_deg=ref_lon + 0.02,
            altitude_m=self.cfg["uav"]["altitude_km"] * 1000.0,
            speed_m_s=self.cfg["uav"]["speed_m_s"],
            tx_power_dbm=self.cfg["uav"]["tx_power_dbm"],
            tx_gain_dbi=self.cfg["uav"]["tx_antenna_gain_dbi"],
            bandwidth_mhz=self.cfg["uav"]["bandwidth_mhz"],
            capacity_mbps=self.cfg["uav"]["capacity_mbps"],
        )
        self.nodes[uav.node_id] = uav

        # Tier 4: Terrestrial Base Stations (2 ground towers)
        tbs1 = TBSNode(
            node_id="TBS-01",
            name="Ground-gNB-Sector1",
            lat_deg=ref_lat,
            lon_deg=ref_lon,
            tx_power_dbm=self.cfg["terrestrial_bs"]["tx_power_dbm"],
            tx_gain_dbi=self.cfg["terrestrial_bs"]["tx_antenna_gain_dbi"],
            bandwidth_mhz=self.cfg["terrestrial_bs"]["bandwidth_mhz"],
            capacity_mbps=self.cfg["terrestrial_bs"]["capacity_mbps"],
            cell_radius_km=self.cfg["terrestrial_bs"]["cell_radius_km"],
        )
        tbs2 = TBSNode(
            node_id="TBS-02",
            name="Ground-gNB-Sector2",
            lat_deg=ref_lat + 0.03,
            lon_deg=ref_lon - 0.02,
            tx_power_dbm=self.cfg["terrestrial_bs"]["tx_power_dbm"],
            tx_gain_dbi=self.cfg["terrestrial_bs"]["tx_antenna_gain_dbi"],
            bandwidth_mhz=self.cfg["terrestrial_bs"]["bandwidth_mhz"],
            capacity_mbps=self.cfg["terrestrial_bs"]["capacity_mbps"],
            cell_radius_km=self.cfg["terrestrial_bs"]["cell_radius_km"],
        )
        self.nodes[tbs1.node_id] = tbs1
        self.nodes[tbs2.node_id] = tbs2

        # User Equipments (default 8 users: mixed URLLC and eMBB)
        num_users = self.cfg["scenarios"]["num_users"]
        for idx in range(num_users):
            u_id = f"UE-{idx+1:02d}"
            lat_offset = float(self.rng.uniform(-0.04, 0.04))
            lon_offset = float(self.rng.uniform(-0.04, 0.04))
            is_urllc = (idx % 2 == 0)
            stype = "URLLC" if is_urllc else "eMBB"
            req_rate = 5.0 if is_urllc else 20.0

            ue = UserEquipmentNode(
                user_id=u_id,
                name=f"User-{stype}-{idx+1}",
                initial_lat_deg=ref_lat + lat_offset,
                initial_lon_deg=ref_lon + lon_offset,
                service_type=stype,
                data_rate_mbps=req_rate,
                velocity_m_s=float(self.rng.uniform(5.0, 25.0)),
            )
            self.users[u_id] = ue

    def compute_link_telemetry(self, user_id: str, node_id: str) -> dict:
        """
        Computes instantaneous physical channel telemetry tuple S_{i,j}(t).
        """
        user = self.users[user_id]
        node = self.nodes[node_id]

        # Geometry
        elev_deg, az_deg, slant_dist_m = OrbitalMechanics.compute_elevation_azimuth(
            user.pos_ecef, node.pos_ecef, user.lat_deg, user.lon_deg
        )

        # Carrier frequency: S-band (2.0 GHz) for standard 3GPP NTN mobile user access links
        fc = self.carrier_freq_s_band

        # Visibility
        if node.tier == "LEO" and isinstance(node, LEOSatelliteNode):
            vis_duration_s = node.compute_remaining_visibility(
                user.pos_ecef, user.lat_deg, user.lon_deg, self.current_time_s
            )
            is_visible = (elev_deg >= node.min_elevation_deg) and (vis_duration_s > 0.0)
        elif node.tier == "TBS":
            dist_km = slant_dist_m / 1000.0
            is_visible = dist_km <= getattr(node, "cell_radius_km", 2.5)
            vis_duration_s = 9999.0 if is_visible else 0.0
        else:
            is_visible = elev_deg >= node.min_elevation_deg
            vis_duration_s = 1800.0 if is_visible else 0.0

        # Check explicit link blockage/disable
        if (user_id, node_id) in self.disabled_links:
            is_visible = False

        if not is_visible:
            return {
                "user_id": user_id,
                "node_id": node_id,
                "tier": node.tier,
                "is_visible": False,
                "elevation_deg": float(elev_deg),
                "slant_distance_m": float(slant_dist_m),
                "doppler_shift_hz": 0.0,
                "sinr_db": -25.0,
                "remaining_visibility_s": 0.0,
                "load": float(node.current_load),
                "energy": float(node.normalized_energy),
                "bandwidth_mhz": 0.0,
                "path_loss_db": 200.0,
            }

        # Path Loss
        pl_details = self.propagation.total_path_loss(
            distance_m=slant_dist_m,
            elevation_deg=elev_deg,
            frequency_hz=fc,
            rain_rate_mm_h=self.rain_rate_mm_h,
            enable_fading=True,
            rng=self.rng,
        )
        total_pl = pl_details["total_path_loss_db"]

        # Additional flutter noise for uncertain channel scenarios
        if self.shadowing_flutter_std > 0.0:
            total_pl += float(self.rng.normal(0.0, self.shadowing_flutter_std))

        # Doppler
        doppler_info = self.doppler.compute_doppler_shift(
            node.pos_ecef, node.vel_ecef, user.pos_ecef, user.vel_ecef, fc
        )

        # Link budget & SINR
        lb = self.sinr_calc.calculate_link_budget(
            tx_power_dbm=node.tx_power_dbm,
            tx_gain_dbi=node.tx_gain_dbi,
            rx_gain_dbi=user.rx_antenna_gain_dbi,
            total_path_loss_db=total_pl,
        )

        sinr_info = self.sinr_calc.compute_sinr(
            p_rx_watts=lb["p_rx_watts"],
            bandwidth_hz=node.bandwidth_mhz * 1.0e6,
            interference_watts=0.0,
        )

        return {
            "user_id": user_id,
            "node_id": node_id,
            "tier": node.tier,
            "is_visible": True,
            "elevation_deg": float(elev_deg),
            "slant_distance_m": float(slant_dist_m),
            "doppler_shift_hz": float(doppler_info["doppler_shift_hz"]),
            "sinr_db": float(sinr_info["sinr_db"]),
            "remaining_visibility_s": float(vis_duration_s),
            "load": float(node.current_load),
            "energy": float(node.normalized_energy),
            "bandwidth_mhz": float(node.available_bandwidth_mhz),
            "path_loss_db": float(total_pl),
        }

    def step(self):
        """Advances simulation by dt seconds."""
        self.current_time_s += self.dt

        # Update all node positions and states
        for node in self.nodes.values():
            node.update_position(self.current_time_s)
            node.consume_energy(self.dt, tx_active=len(node.connected_users) > 0)

        # Update all user positions
        for user in self.users.values():
            user.update_position(self.current_time_s)

        # Record snapshot telemetry
        snapshot = {
            "time_s": self.current_time_s,
            "links": {},
        }
        for u_id in self.users:
            for n_id in self.nodes:
                link_data = self.compute_link_telemetry(u_id, n_id)
                snapshot["links"][(u_id, n_id)] = link_data

        self.telemetry_history.append(snapshot)
        return snapshot

    def reset(self, random_seed: Optional[int] = None):
        """Resets the simulator state."""
        if random_seed is not None:
            self.seed = random_seed
            self.rng = np.random.default_rng(self.seed)

        self.current_time_s = 0.0
        self.rain_rate_mm_h = 0.0
        self.shadowing_flutter_std = 0.0
        self.disabled_links.clear()
        self.telemetry_history.clear()
        self.setup_default_topology()
