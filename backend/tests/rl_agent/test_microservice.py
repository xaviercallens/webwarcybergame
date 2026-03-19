"""
Unit tests for RL Agent microservice endpoints.
Tests /ai/decide, /ai/actions, /scenarios, /health, and game session routes.
"""

import pytest
from fastapi.testclient import TestClient

from src.rl_agent.main import app, AGENTS, _load_agents


@pytest.fixture(autouse=True)
def load_agents():
    """Ensure agents are loaded before each test."""
    global AGENTS
    import src.rl_agent.main as mod
    mod.AGENTS = _load_agents()
    yield
    mod.AGENTS.clear()


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "3.1.0"
        assert data["models_loaded"] > 0


class TestAIDecideEndpoint:

    def test_attacker_decide(self, client):
        resp = client.post("/ai/decide", json={
            "role": "attacker",
            "difficulty": "normal",
            "observation": [0.0] * 50,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "action" in data
        assert "action_name" in data
        assert "confidence" in data
        assert isinstance(data["action"], int)

    def test_defender_decide(self, client):
        resp = client.post("/ai/decide", json={
            "role": "defender",
            "difficulty": "normal",
            "observation": [0.0] * 50,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["action"], int)

    def test_invalid_role(self, client):
        resp = client.post("/ai/decide", json={
            "role": "hacker",
            "observation": [0.0] * 10,
        })
        assert resp.status_code == 400

    def test_invalid_difficulty(self, client):
        resp = client.post("/ai/decide", json={
            "role": "attacker",
            "difficulty": "impossible",
            "observation": [0.0] * 10,
        })
        assert resp.status_code == 400

    def test_all_difficulties(self, client):
        for diff in ("novice", "normal", "expert"):
            resp = client.post("/ai/decide", json={
                "role": "attacker",
                "difficulty": diff,
                "observation": [0.0] * 50,
            })
            assert resp.status_code == 200


class TestAIActionsEndpoint:

    def test_attacker_actions(self, client):
        resp = client.post("/ai/actions", json={"role": "attacker"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "attacker"
        assert len(data["actions"]) > 0

    def test_defender_actions(self, client):
        resp = client.post("/ai/actions", json={"role": "defender"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["actions"]) > 0

    def test_invalid_role(self, client):
        resp = client.post("/ai/actions", json={"role": "invalid"})
        assert resp.status_code == 400


class TestScenariosEndpoint:

    def test_list_scenarios(self, client):
        resp = client.get("/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_get_scenario(self, client):
        resp = client.get("/scenarios/tutorial")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Tutorial - First Breach"

    def test_get_nonexistent_scenario(self, client):
        resp = client.get("/scenarios/nonexistent")
        assert resp.status_code == 404


class TestGameSessionEndpoints:

    def test_create_session(self, client):
        resp = client.post("/game/sessions", json={
            "scenario_id": "tutorial",
            "attacker_type": "human",
            "defender_type": "ai",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["current_player"] == "attacker"
        assert data["turn"] == 1

    def test_list_sessions(self, client):
        # Create a session first
        client.post("/game/sessions", json={"scenario_id": "tutorial"})
        resp = client.get("/game/sessions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_session_state(self, client):
        create_resp = client.post("/game/sessions", json={"scenario_id": "tutorial"})
        sid = create_resp.json()["session_id"]

        resp = client.get(f"/game/sessions/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == sid
        assert data["turn"] == 1

    def test_submit_action(self, client):
        create_resp = client.post("/game/sessions", json={"scenario_id": "tutorial"})
        sid = create_resp.json()["session_id"]

        resp = client.post(f"/game/sessions/{sid}/action", json={
            "session_id": sid,
            "player": "attacker",
            "action": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "action_name" in data
        assert "current_player" in data
        assert "observation" in data

    def test_submit_wrong_player(self, client):
        create_resp = client.post("/game/sessions", json={"scenario_id": "tutorial"})
        sid = create_resp.json()["session_id"]

        resp = client.post(f"/game/sessions/{sid}/action", json={
            "session_id": sid,
            "player": "defender",
            "action": 0,
        })
        assert resp.status_code == 400

    def test_play_full_turn(self, client):
        create_resp = client.post("/game/sessions", json={"scenario_id": "tutorial"})
        sid = create_resp.json()["session_id"]

        # Attacker turn
        resp = client.post(f"/game/sessions/{sid}/action", json={
            "session_id": sid, "player": "attacker", "action": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_player"] == "defender"

        # Defender turn
        resp = client.post(f"/game/sessions/{sid}/action", json={
            "session_id": sid, "player": "defender", "action": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_player"] == "attacker"
        assert data["turn"] == 2

    def test_get_observation(self, client):
        create_resp = client.post("/game/sessions", json={"scenario_id": "tutorial"})
        sid = create_resp.json()["session_id"]

        resp = client.get(f"/game/sessions/{sid}/observation/attacker")
        assert resp.status_code == 200
        data = resp.json()
        assert data["player"] == "attacker"
        assert isinstance(data["observation"], list)

    def test_delete_session(self, client):
        create_resp = client.post("/game/sessions", json={"scenario_id": "tutorial"})
        sid = create_resp.json()["session_id"]

        resp = client.delete(f"/game/sessions/{sid}")
        assert resp.status_code == 200

        resp = client.get(f"/game/sessions/{sid}")
        assert resp.status_code == 404

    def test_nonexistent_session(self, client):
        resp = client.get("/game/sessions/nonexistent")
        assert resp.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
