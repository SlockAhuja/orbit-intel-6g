"""
ORBIT-INTEL 6G: Heterogeneous Space-Air-Ground Integrated Network Simulator
Coordinates 4-tier SAGIN nodes, disaggregated channel physics, orbital kinematics,
and realistic geographically distributed user cohorts (Urban, Suburban, Remote, Maritime).
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
    Models genuine multi-tier competition across LEO, HAPS, UAV, and Terrestrial Base Stations.
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
        self.propagation = PropagationModel(speed_of_light=float(self.cfg["system"]["speed_of_light_m_s"]))
        self.doppler = DopplerModel(speed_of_light=float(self.cfg["system"]["speed_of_light_m_s"]))
        self.sinr_calc = SINRCalculator(
            boltzmann_k=float(self.cfg["system"]["boltzmann_constant"]),
            temperature_k=float(self.cfg["system"]["temperature_system_k"]),
            noise_figure_db=float(self.cfg["user_equipment"]["noise_figure_db"]),
        )
        self.traffic_engine = TrafficEngine(speed_of_light=float(self.cfg["system"]["speed_of_light_m_s"]))

        # Network entity registries
        self.nodes: dict[str, NetworkNode] = {}
        self.users: dict[str, UserEquipmentNode] = {}

        # Simulation clock
        self.current_time_s = 0.0
        self.dt = 1.0

        # Environmental conditions (can be modified by scenarios)
        self.rain_rate_mm_h = 0.0
        self.carrier_freq_s_band = float(self.cfg["system"]["carrier_frequency_s_band_hz"])
        self.carrier_freq_ka_band = float(self.cfg["system"]["carrier_frequency_ka_band_hz"])
        self.shadowing_flutter_std = 0.0
        self.disabled_links: set[tuple[str, str]] = set()

        # Telemetry history for feature generation
        self.telemetry_history: list[dict] = []

        # Setup standard topology
        self.setup_default_topology()

    def setup_default_topology(self):
        """
        Builds a realistic heterogeneous SAGIN topology with geographically distributed
        user cohorts across Urban, Suburban, Remote, and Maritime zones.
        """
        self.nodes.clear()
        self.users.clear()

        # Geographic Reference Center (Urban Hub): 22.0° N, 75.0° E
        ref_lat, ref_lon = 22.0, 75.0

        # Tier 1: LEO Satellites (2 satellites in inclined circular orbits at 600 km)
        sat1 = LEOSatelliteNode(
            node_id="SAT-01",
            name="LEO-Constellation-01",
            altitude_km=float(self.cfg["leo_satellite"]["altitude_km"]),
            inclination_deg=53.0,
            raan_deg=75.0,
            initial_mean_anomaly_deg=18.0,  # Positioned for high elevation over reference area
            tx_power_dbm=float(self.cfg["leo_satellite"]["tx_power_dbm"]),
            tx_gain_dbi=float(self.cfg["leo_satellite"]["tx_antenna_gain_dbi"]),
            bandwidth_mhz=float(self.cfg["leo_satellite"]["bandwidth_mhz"]),
            capacity_mbps=float(self.cfg["leo_satellite"]["capacity_mbps"]),
        )
        sat2 = LEOSatelliteNode(
            node_id="SAT-02",
            name="LEO-Constellation-02",
            altitude_km=float(self.cfg["leo_satellite"]["altitude_km"]),
            inclination_deg=53.0,
            raan_deg=85.0,
            initial_mean_anomaly_deg=-10.0,  # Rising secondary satellite for handover target
            tx_power_dbm=float(self.cfg["leo_satellite"]["tx_power_dbm"]),
            tx_gain_dbi=float(self.cfg["leo_satellite"]["tx_antenna_gain_dbi"]),
            bandwidth_mhz=float(self.cfg["leo_satellite"]["bandwidth_mhz"]),
            capacity_mbps=float(self.cfg["leo_satellite"]["capacity_mbps"]),
        )
        self.nodes[sat1.node_id] = sat1
        self.nodes[sat2.node_id] = sat2

        # Tier 2: HAPS (Stratospheric platform at 20 km altitude, regional footprint radius ~25 km)
        haps = HAPSNode(
            node_id="HAPS-01",
            name="Stratospheric-HAPS-01",
            center_lat_deg=ref_lat,
            center_lon_deg=ref_lon,
            altitude_km=float(self.cfg["haps"]["altitude_km"]),
            drift_speed_m_s=float(self.cfg["haps"]["drift_speed_m_s"]),
            tx_power_dbm=float(self.cfg["haps"]["tx_power_dbm"]),
            tx_gain_dbi=float(self.cfg["haps"]["tx_antenna_gain_dbi"]),
            bandwidth_mhz=float(self.cfg["haps"]["bandwidth_mhz"]),
            capacity_mbps=float(self.cfg["haps"]["capacity_mbps"]),
        )
        setattr(haps, "coverage_radius_km", float(self.cfg["haps"].get("coverage_radius_km", 25.0)))
        self.nodes[haps.node_id] = haps

        # Tier 3: UAV Relay (Tactical airborne node at 300 m altitude, hotspot radius ~3 km)
        uav = UAVNode(
            node_id="UAV-01",
            name="Tactical-UAV-Relay",
            center_lat_deg=ref_lat + 0.045,  # Positioned over suburban hotspot (~5 km from center)
            center_lon_deg=ref_lon + 0.045,
            altitude_m=float(self.cfg["uav"]["altitude_km"]) * 1000.0,
            speed_m_s=float(self.cfg["uav"]["speed_m_s"]),
            tx_power_dbm=float(self.cfg["uav"]["tx_power_dbm"]),
            tx_gain_dbi=float(self.cfg["uav"]["tx_antenna_gain_dbi"]),
            bandwidth_mhz=float(self.cfg["uav"]["bandwidth_mhz"]),
            capacity_mbps=float(self.cfg["uav"]["capacity_mbps"]),
        )
        setattr(uav, "coverage_radius_km", float(self.cfg["uav"].get("coverage_radius_km", 3.0)))
        self.nodes[uav.node_id] = uav

        # Tier 4: Terrestrial Base Stations (2 localized ground cell towers, 30 m height, radius 2.5 km)
        tbs1 = TBSNode(
            node_id="TBS-01",
            name="Urban-gNodeB-North",
            lat_deg=ref_lat,
            lon_deg=ref_lon,
            tx_power_dbm=float(self.cfg["terrestrial_bs"]["tx_power_dbm"]),
            tx_gain_dbi=float(self.cfg["terrestrial_bs"]["tx_antenna_gain_dbi"]),
            bandwidth_mhz=float(self.cfg["terrestrial_bs"]["bandwidth_mhz"]),
            capacity_mbps=float(self.cfg["terrestrial_bs"]["capacity_mbps"]),
            cell_radius_km=float(self.cfg["terrestrial_bs"]["cell_radius_km"]),
        )
        tbs2 = TBSNode(
            node_id="TBS-02",
            name="Urban-gNodeB-South",
            lat_deg=ref_lat + 0.015,
            lon_deg=ref_lon - 0.012,
            tx_power_dbm=float(self.cfg["terrestrial_bs"]["tx_power_dbm"]),
            tx_gain_dbi=float(self.cfg["terrestrial_bs"]["tx_antenna_gain_dbi"]),
            bandwidth_mhz=float(self.cfg["terrestrial_bs"]["bandwidth_mhz"]),
            capacity_mbps=float(self.cfg["terrestrial_bs"]["capacity_mbps"]),
            cell_radius_km=float(self.cfg["terrestrial_bs"]["cell_radius_km"]),
        )
        self.nodes[tbs1.node_id] = tbs1
        self.nodes[tbs2.node_id] = tbs2

        # -------------------------------------------------------------
        # Geographically Disaggregated User Cohorts (Total 12 Users)
        # -------------------------------------------------------------
        # Cohort 1: Urban Users (UE-01 to UE-03) — Close to TBS-01/02 (<1.5 km)
        # Best link: Terrestrial gNB
        urban_configs = [
            ("UE-01", "Urban-URLLC-1", ref_lat + 0.005, ref_lon + 0.005, "URLLC", 5.0, 10.0),
            ("UE-02", "Urban-eMBB-1", ref_lat - 0.006, ref_lon - 0.004, "eMBB", 20.0, 15.0),
            ("UE-03", "Urban-URLLC-2", ref_lat + 0.012, ref_lon - 0.008, "URLLC", 5.0, 8.0),
        ]

        # Cohort 2: Suburban Hotspot (UE-04 to UE-06) — 5 km away, under UAV-01 loiter
        # Best link: UAV Relay or HAPS
        suburban_configs = [
            ("UE-04", "Suburban-UAV-1", ref_lat + 0.046, ref_lon + 0.044, "URLLC", 5.0, 12.0),
            ("UE-05", "Suburban-UAV-2", ref_lat + 0.044, ref_lon + 0.047, "eMBB", 20.0, 10.0),
            ("UE-06", "Suburban-HAPS-1", ref_lat + 0.080, ref_lon + 0.020, "eMBB", 15.0, 18.0),
        ]

        # Cohort 3: Remote / Rural Zone (UE-07 to UE-09) — 35 to 50 km away
        # Out of reach of TBS and UAV; under HAPS or LEO coverage
        remote_configs = [
            ("UE-07", "Remote-NTN-1", ref_lat + 0.28, ref_lon + 0.15, "URLLC", 5.0, 15.0),
            ("UE-08", "Remote-NTN-2", ref_lat + 0.32, ref_lon + 0.25, "eMBB", 20.0, 20.0),
            ("UE-09", "Rural-NTN-3", ref_lat + 0.22, ref_lon - 0.20, "eMBB", 15.0, 12.0),
        ]

        # Cohort 4: Maritime / Extreme Remote (UE-10 to UE-12) — 80 to 120 km away
        # Out of reach of TBS, UAV, and HAPS (>25 km footprint); SOLE LINK IS LEO SATELLITE
        maritime_configs = [
            ("UE-10", "Maritime-LEO-1", ref_lat + 0.85, ref_lon + 0.65, "URLLC", 5.0, 25.0),
            ("UE-11", "Maritime-LEO-2", ref_lat + 0.95, ref_lon + 0.80, "eMBB", 20.0, 22.0),
            ("UE-12", "Offshore-LEO-3", ref_lat - 0.80, ref_lon + 0.70, "URLLC", 5.0, 18.0),
        ]

        all_cohorts = urban_configs + suburban_configs + remote_configs + maritime_configs
        for u_id, name, lat, lon, stype, rate, vel in all_cohorts:
            ue = UserEquipmentNode(
                user_id=u_id,
                name=name,
                initial_lat_deg=lat,
                initial_lon_deg=lon,
                service_type=stype,
                data_rate_mbps=rate,
                velocity_m_s=vel,
                rx_antenna_gain_dbi=float(self.cfg["user_equipment"]["rx_antenna_gain_dbi"]),
            )
            self.users[u_id] = ue

    def compute_link_telemetry(self, user_id: str, node_id: str) -> dict:
        """
        Computes physical channel telemetry tuple S_{i,j}(t) using disaggregated models:
        - LEO: 3GPP TR 38.811 NTN + ITU-R P.618 Earth-space rain
        - HAPS: Stratospheric air-to-ground + rain layer
        - UAV: 3GPP TR 36.777 air-to-ground + ITU-R P.530
        - TBS: 3GPP TR 38.901 UMa + ITU-R P.530 terrestrial rain
        """
        user = self.users[user_id]
        node = self.nodes[node_id]

        # 1. Kinematic Geometry (WGS-84)
        elev_deg, az_deg, slant_dist_m = OrbitalMechanics.compute_elevation_azimuth(
            user.pos_ecef, node.pos_ecef, user.lat_deg, user.lon_deg
        )
        slant_dist_km = slant_dist_m / 1000.0

        # Calculate approximate horizontal 2D ground distance
        dx_km = (node.lat_deg - user.lat_deg) * 111.32
        dy_km = (node.lon_deg - user.lon_deg) * 111.32 * np.cos(np.radians(user.lat_deg))
        d_ground_km = float(np.sqrt(dx_km ** 2 + dy_km ** 2))

        # 2. Carrier Frequency
        fc = self.carrier_freq_ka_band if (node.tier == "LEO" and getattr(node, "use_ka_band", False)) else self.carrier_freq_s_band

        # 3. Physical Visibility & Line-of-Sight Determination
        is_visible = False
        vis_duration_s = 0.0

        if node.tier == "LEO" and isinstance(node, LEOSatelliteNode):
            vis_duration_s = node.compute_remaining_visibility(
                user.pos_ecef, user.lat_deg, user.lon_deg, self.current_time_s
            )
            # LEO requires elevation angle >= min_elevation_deg (10 degrees)
            is_visible = (elev_deg >= node.min_elevation_deg) and (vis_duration_s > 0.0)

        elif node.tier == "HAPS":
            # HAPS has a regional footprint radius of ~25 km and minimum elevation ~5 degrees
            cov_radius = getattr(node, "coverage_radius_km", 25.0)
            is_visible = (d_ground_km <= cov_radius) and (elev_deg >= node.min_elevation_deg)
            vis_duration_s = 1800.0 if is_visible else 0.0

        elif node.tier == "UAV":
            # UAV has localized coverage radius ~3 km and min elevation ~15 degrees
            cov_radius = getattr(node, "coverage_radius_km", 3.0)
            is_visible = (d_ground_km <= cov_radius) and (elev_deg >= node.min_elevation_deg)
            vis_duration_s = 600.0 if is_visible else 0.0

        elif node.tier == "TBS":
            # Ground base station has strict terrestrial radio horizon / cell radius (~2.5 km)
            cell_radius = getattr(node, "cell_radius_km", 2.5)
            is_visible = (d_ground_km <= cell_radius)
            vis_duration_s = 9999.0 if is_visible else 0.0

        # Check explicit link blockage / disable
        if (user_id, node_id) in self.disabled_links:
            is_visible = False

        # Non-visible link handling
        if not is_visible:
            return {
                "user_id": user_id,
                "node_id": node_id,
                "tier": node.tier,
                "is_visible": False,
                "elevation_deg": float(elev_deg),
                "slant_distance_m": float(slant_dist_m),
                "ground_distance_km": float(d_ground_km),
                "doppler_shift_hz": 0.0,
                "sinr_db": -25.0,
                "remaining_visibility_s": 0.0,
                "load": float(node.current_load),
                "energy": float(node.normalized_energy),
                "bandwidth_mhz": 0.0,
                "path_loss_db": 220.0,
            }

        # 4. Disaggregated Path Loss Computation
        pl_details = self.propagation.total_path_loss(
            distance_m=slant_dist_m,
            elevation_deg=elev_deg,
            frequency_hz=fc,
            tier=node.tier,
            rain_rate_mm_h=self.rain_rate_mm_h,
            enable_fading=True,
            rng=self.rng,
        )
        total_pl = pl_details["total_path_loss_db"]

        # Additional stochastic channel flutter
        if self.shadowing_flutter_std > 0.0:
            total_pl += float(self.rng.normal(0.0, self.shadowing_flutter_std))

        # 5. Doppler Shift Computation
        doppler_info = self.doppler.compute_doppler_shift(
            node.pos_ecef, node.vel_ecef, user.pos_ecef, user.vel_ecef, fc
        )

        # 6. Link Budget & SINR
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
            "ground_distance_km": float(d_ground_km),
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
