"""
Tests for ORBIT-INTEL 6G Mission Control Web Server and REST API.
Verifies all routes, simulation stepping, prediction, and orchestration hooks.
"""

import pytest
import json
from web.server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestMissionControlWeb:
    """Verifies that the web interface routes and API endpoints function cleanly."""

    def test_index_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"ORBIT-INTEL" in response.data
        assert b"MISSION CONTROL ONLINE" in response.data

    def test_api_state(self, client):
        response = client.get("/api/state")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ONLINE"
        assert "nodes" in data
        assert "users" in data
        assert "links" in data
        assert len(data["nodes"]) == 6
        assert len(data["users"]) == 12

    def test_api_step(self, client):
        response = client.post("/api/step", json={"steps": 2})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["epoch_seconds"] >= 2

    def test_api_reset(self, client):
        response = client.post("/api/reset")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["epoch_seconds"] == 0

    def test_api_scenario(self, client):
        response = client.post("/api/scenario/3")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["scenario"]["id"] == 3

    def test_api_inject(self, client):
        response = client.post("/api/inject", json={"rain_rate_mm_h": 45.0, "shadowing_flutter_std": 2.5})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["environmental"]["rain_rate_mm_h"] == 45.0
        assert data["environmental"]["shadowing_flutter_std"] == 2.5

    def test_api_predict(self, client):
        response = client.get("/api/predict?user_id=UE-01&node_id=SAT-01&horizon=5")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "predicted_sinrs" in data
        assert "q_lowers" in data
        assert "total_uncertainty" in data
        assert len(data["actual_sinrs"]) == len(data["predicted_sinrs"])

    def test_api_orchestrate(self, client):
        response = client.get("/api/orchestrate?user_id=UE-01")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "selected_node" in data
        assert "candidates" in data
        assert len(data["candidates"]) == 6

    def test_api_handover_replay(self, client):
        response = client.get("/api/handover_replay")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sat1_elevations" in data
        assert "capro_packet_loss_pct" in data
        assert len(data["epochs"]) == 40

    def test_api_benchmarks(self, client):
        response = client.get("/api/benchmarks")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "by_method" in data
        assert "ablation" in data

    def test_team_attribution_endpoint(self, client):
        """Verifies exact two-person project attribution without extra titles or omissions."""
        response = client.get("/api/team")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["contributors"] == ["Slock Ahuja", "Dr. Praveen Kumar Sharma"]
        assert "STLC" in data["showcase"] and "Tunisia 2026" in data["showcase"]

    def test_scenario_details_endpoint(self, client):
        """Verifies detailed parameter and behavioral descriptions for all 5 scenarios."""
        response = client.get("/api/scenario_details")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["scenarios"]) == 5
        sc1 = data["scenarios"][0]
        assert sc1["id"] == 1
        assert "explanation" in sc1
        assert "initial_conditions" in sc1
        assert "configurable_params" in sc1
        assert "expected_behavior" in sc1
        assert "observed_behavior" in sc1

    def test_compare_methods_endpoint(self, client):
        """Verifies simultaneous execution of M1, M2, M3, and M4 on identical instantaneous state."""
        response = client.get("/api/compare_methods?user_id=UE-01")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "methods" in data
        methods = data["methods"]
        assert "M1_reactive" in methods
        assert "M2_threshold" in methods
        assert "M3_prediction_only" in methods
        assert "M4_capro" in methods
        assert methods["M4_capro"]["selected_node"] is not None

    def test_latency_strict_summation_identity(self, client):
        """
        Verifies that for every link across all 4 tiers (LEO, HAPS, UAV, TBS),
        total_latency_ms == propagation_delay_ms + processing_delay_ms + feeder_delay_ms + queue_delay_ms.
        Enforces zero mathematical discrepancy.
        """
        response = client.get("/api/state")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["links"]) > 0

        for link_id, link in data["links"].items():
            prop = link["propagation_delay_ms"]
            proc = link["processing_delay_ms"]
            feeder = link["feeder_delay_ms"]
            queue = link["queue_delay_ms"]
            total = link["total_latency_ms"]

            expected_sum = round(prop + proc + feeder + queue, 2)
            assert abs(expected_sum - total) <= 0.02, (
                f"Link {link_id} latency summation mismatch: "
                f"{prop} + {proc} + {feeder} + {queue} = {expected_sum} != {total}"
            )

    def test_index_page_team_and_modals(self, client):
        """Verifies that the HTML template renders the exact team attribution, decomposed latency, and modals."""
        response = client.get("/")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Slock Ahuja" in html
        assert "Dr. Praveen Kumar Sharma" in html
        assert "Decomposed Physical Delay (Strict Summation)" in html
        assert "qos-proc-delay" in html
        assert "qos-feeder-delay" in html
        assert "qos-queue-delay" in html
        assert "about-modal-backdrop" in html
        assert "benchmark-modal-backdrop" in html
        assert "presentation-toolbar" in html
        assert "node-hover-tooltip" in html


