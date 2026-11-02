"""
ORBIT-INTEL 6G: Network Nodes for Space-Air-Ground Integrated Network
Defines physical entities across LEO, HAPS, UAV, TBS, and User Equipments.
"""

from typing import Optional
import numpy as np
from src.simulation_engine.orbital import OrbitalMechanics, LEOSatelliteOrbit


class NetworkNode:
    """
    Abstract Base Class for all communication nodes in the SAGIN infrastructure.
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        tier: str,
        lat_deg: float,
        lon_deg: float,
        alt_m: float,
        tx_power_dbm: float,
        tx_gain_dbi: float,
        bandwidth_mhz: float,
        capacity_mbps: float,
        min_elevation_deg: float = 10.0,
        energy_capacity_wh: float = 1000.0,
    ):
        self.node_id = node_id
        self.name = name
        self.tier = tier  # "LEO", "HAPS", "UAV", "TBS"
        self.lat_deg = lat_deg
        self.lon_deg = lon_deg
        self.alt_m = alt_m

        self.pos_ecef = OrbitalMechanics.geodetic_to_ecef(lat_deg, lon_deg, alt_m)
        self.vel_ecef = np.zeros(3, dtype=np.float64)

        self.tx_power_dbm = tx_power_dbm
        self.tx_gain_dbi = tx_gain_dbi
        self.bandwidth_mhz = bandwidth_mhz
        self.capacity_mbps = capacity_mbps
        self.min_elevation_deg = min_elevation_deg

        self.energy_capacity_wh = energy_capacity_wh
        self.current_energy_wh = energy_capacity_wh
        self.current_load = 0.0  # Fraction between 0.0 and 1.0
        self.connected_users: list[str] = []
        self.is_active = True

    @property
    def normalized_energy(self) -> float:
        return float(np.clip(self.current_energy_wh / max(self.energy_capacity_wh, 1e-6), 0.0, 1.0))

    @property
    def available_bandwidth_mhz(self) -> float:
        return float(self.bandwidth_mhz * (1.0 - self.current_load))

    def update_position(self, t_seconds: float):
        """Default static node position update."""
        pass

    def allocate_load(self, rate_mbps: float):
        """Increases node traffic load."""
        added_load = rate_mbps / max(self.capacity_mbps, 1.0)
        self.current_load = min(1.0, self.current_load + added_load)

    def release_load(self, rate_mbps: float):
        """Releases allocated load."""
        subtracted = rate_mbps / max(self.capacity_mbps, 1.0)
        self.current_load = max(0.0, self.current_load - subtracted)

    def consume_energy(self, duration_s: float, tx_active: bool = True):
        """Energy consumption model."""
        base_power_w = 20.0
        tx_power_w = (10.0 ** ((self.tx_power_dbm - 30.0) / 10.0)) if tx_active else 0.0
        total_p_w = base_power_w + tx_power_w * (0.3 + 0.7 * self.current_load)
        consumed_wh = (total_p_w * duration_s) / 3600.0
        self.current_energy_wh = max(0.0, self.current_energy_wh - consumed_wh)


class LEOSatelliteNode(NetworkNode):
    """
    LEO Satellite communicating at 600 km altitude with fast orbital motion.
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        altitude_km: float = 600.0,
        inclination_deg: float = 53.0,
        raan_deg: float = 0.0,
        initial_mean_anomaly_deg: float = 0.0,
        tx_power_dbm: float = 43.0,
        tx_gain_dbi: float = 30.0,
        bandwidth_mhz: float = 100.0,
        capacity_mbps: float = 300.0,
    ):
        self.orbit = LEOSatelliteOrbit(
            sat_id=node_id,
            altitude_km=altitude_km,
            inclination_deg=inclination_deg,
            raan_deg=raan_deg,
            initial_mean_anomaly_deg=initial_mean_anomaly_deg,
        )
        pos, vel, lat, lon = self.orbit.get_state_at_time(0.0)

        super().__init__(
            node_id=node_id,
            name=name,
            tier="LEO",
            lat_deg=lat,
            lon_deg=lon,
            alt_m=altitude_km * 1000.0,
            tx_power_dbm=tx_power_dbm,
            tx_gain_dbi=tx_gain_dbi,
            bandwidth_mhz=bandwidth_mhz,
            capacity_mbps=capacity_mbps,
            min_elevation_deg=10.0,
            energy_capacity_wh=1200.0,
        )
        self.pos_ecef = pos
        self.vel_ecef = vel

    def update_position(self, t_seconds: float):
        pos, vel, lat, lon = self.orbit.get_state_at_time(t_seconds)
        self.pos_ecef = pos
        self.vel_ecef = vel
        self.lat_deg = lat
        self.lon_deg = lon

    def compute_remaining_visibility(
        self, user_ecef: np.ndarray, user_lat: float, user_lon: float, t_seconds: float
    ) -> float:
        return self.orbit.estimate_remaining_visibility(
            user_ecef, user_lat, user_lon, t_seconds, self.min_elevation_deg
        )


class HAPSNode(NetworkNode):
    """
    High-Altitude Platform Station at 20 km altitude (stratospheric).
    Quasi-stationary with slow station-keeping drift.
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        center_lat_deg: float,
        center_lon_deg: float,
        altitude_km: float = 20.0,
        drift_speed_m_s: float = 2.0,
        tx_power_dbm: float = 35.0,
        tx_gain_dbi: float = 20.0,
        bandwidth_mhz: float = 50.0,
        capacity_mbps: float = 150.0,
    ):
        super().__init__(
            node_id=node_id,
            name=name,
            tier="HAPS",
            lat_deg=center_lat_deg,
            lon_deg=center_lon_deg,
            alt_m=altitude_km * 1000.0,
            tx_power_dbm=tx_power_dbm,
            tx_gain_dbi=tx_gain_dbi,
            bandwidth_mhz=bandwidth_mhz,
            capacity_mbps=capacity_mbps,
            min_elevation_deg=5.0,
            energy_capacity_wh=800.0,
        )
        self.center_lat = center_lat_deg
        self.center_lon = center_lon_deg
        self.drift_speed = drift_speed_m_s

    def update_position(self, t_seconds: float):
        # Circular station-keeping loiter radius ~ 1.5 km
        omega = 2.0 * np.pi / 1800.0  # 30-min loiter period
        radius_deg = 0.015
        self.lat_deg = self.center_lat + radius_deg * np.cos(omega * t_seconds)
        self.lon_deg = self.center_lon + radius_deg * np.sin(omega * t_seconds)
        self.pos_ecef = OrbitalMechanics.geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_m)
        self.vel_ecef = np.array([
            -self.drift_speed * np.sin(omega * t_seconds),
            self.drift_speed * np.cos(omega * t_seconds),
            0.0,
        ], dtype=np.float64)


class UAVNode(NetworkNode):
    """
    Unmanned Aerial Vehicle relay at 300 m altitude with patrol velocity.
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        center_lat_deg: float,
        center_lon_deg: float,
        altitude_m: float = 300.0,
        speed_m_s: float = 15.0,
        tx_power_dbm: float = 28.0,
        tx_gain_dbi: float = 10.0,
        bandwidth_mhz: float = 20.0,
        capacity_mbps: float = 80.0,
    ):
        super().__init__(
            node_id=node_id,
            name=name,
            tier="UAV",
            lat_deg=center_lat_deg,
            lon_deg=center_lon_deg,
            alt_m=altitude_m,
            tx_power_dbm=tx_power_dbm,
            tx_gain_dbi=tx_gain_dbi,
            bandwidth_mhz=bandwidth_mhz,
            capacity_mbps=capacity_mbps,
            min_elevation_deg=15.0,
            energy_capacity_wh=300.0,
        )
        self.center_lat = center_lat_deg
        self.center_lon = center_lon_deg
        self.speed = speed_m_s

    def update_position(self, t_seconds: float):
        # Patrol figure-8 pattern
        omega = 2.0 * np.pi / 240.0
        radius_deg = 0.008
        self.lat_deg = self.center_lat + radius_deg * np.sin(omega * t_seconds)
        self.lon_deg = self.center_lon + radius_deg * np.sin(2.0 * omega * t_seconds) / 2.0
        self.pos_ecef = OrbitalMechanics.geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_m)


class TBSNode(NetworkNode):
    """
    Terrestrial Base Station ground tower (30 m).
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        lat_deg: float,
        lon_deg: float,
        tx_power_dbm: float = 43.0,
        tx_gain_dbi: float = 16.0,
        bandwidth_mhz: float = 100.0,
        capacity_mbps: float = 500.0,
        cell_radius_km: float = 2.5,
    ):
        super().__init__(
            node_id=node_id,
            name=name,
            tier="TBS",
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            alt_m=30.0,
            tx_power_dbm=tx_power_dbm,
            tx_gain_dbi=tx_gain_dbi,
            bandwidth_mhz=bandwidth_mhz,
            capacity_mbps=capacity_mbps,
            min_elevation_deg=0.0,
            energy_capacity_wh=5000.0,
        )
        self.cell_radius_km = cell_radius_km


class UserEquipmentNode:
    """
    Mobile user terminal requesting communication services (URLLC or eMBB).
    """

    def __init__(
        self,
        user_id: str,
        name: str,
        initial_lat_deg: float,
        initial_lon_deg: float,
        service_type: str = "URLLC",
        data_rate_mbps: float = 5.0,
        velocity_m_s: float = 15.0,
        rx_antenna_gain_dbi: float = 2.0,
    ):
        self.user_id = user_id
        self.name = name
        self.lat_deg = initial_lat_deg
        self.lon_deg = initial_lon_deg
        self.alt_m = 1.5  # Handheld/vehicular height

        self.pos_ecef = OrbitalMechanics.geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_m)
        self.vel_ecef = np.zeros(3, dtype=np.float64)
        self.velocity_m_s = velocity_m_s

        self.service_type = service_type  # "URLLC" or "eMBB"
        self.required_data_rate_mbps = data_rate_mbps
        self.rx_antenna_gain_dbi = rx_antenna_gain_dbi

        # SLA constraints
        self.max_latency_ms = 10.0 if service_type == "URLLC" else 50.0
        self.min_sinr_threshold_db = 3.0

        # Current serving attachment
        self.current_serving_node_id: Optional[str] = None
        self.handover_count = 0
        self.failed_handover_count = 0
        self.packets_generated = 0
        self.packets_delivered = 0
        self.outage_epochs = 0
        self.total_epochs = 0

    def update_position(self, t_seconds: float):
        # Linear vehicular motion east-northeast
        speed_deg_per_s = (self.velocity_m_s / 111320.0)
        self.lat_deg += 0.4 * speed_deg_per_s
        self.lon_deg += 0.8 * speed_deg_per_s
        self.pos_ecef = OrbitalMechanics.geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_m)

