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
