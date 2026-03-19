"""
Integration tests for all 4 game modes.
Tests Human-Human, Human-AI, AI-Human, AI-AI end-to-end flows.

Blueprint Alignment: Day 7 (Integration, Security & Testing)
"""

import pytest
from fastapi.testclient import TestClient

from src.rl_agent.main import app, _load_agents
from src.rl.train_agents import RuleBasedAttacker, RuleBasedDefender, RandomAgent, play_episode
from src.rl.observation_space import GameState
from src.game.turn_manager import TurnManager
from src.game.actions.action_executor import ActionExecutor
from src.game.detection_engine import StealthAlertSystem
from src.game.resources import ResourceManager
from src.game.victory_conditions import ScenarioObjectives, GameEndConditions
from src.rl.action_space import AttackerAction, DefenderAction


@pytest.fixture(autouse=True)
def load_agents_fixture():
    import src.rl_agent.main as mod
    mod.AGENTS = _load_agents()
    yield
    mod.AGENTS.clear()


@pytest.fixture
def client():
    return TestClient(app)


class TestHumanVsHuman:
    """Test human attacker vs. human defender (via API)."""

    def test_full_game_flow(self, client):
        """Play a complete human vs human game via API."""
        # Create session
        resp = client.post("/game/sessions", json={
            "scenario_id": "tutorial",
            "attacker_type": "human",
            "defender_type": "human",
        })
        assert resp.status_code == 200
        sid = resp.json()["session_id"]

        # Play 5 full rounds
        for turn in range(5):
            # Attacker turn
            resp = client.post(f"/game/sessions/{sid}/action", json={
                "session_id": sid,
                "player": "attacker",
                "action": 0,  # SCAN_NETWORK
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["current_player"] == "defender"

            # Defender turn
            resp = client.post(f"/game/sessions/{sid}/action", json={
                "session_id": sid,
                "player": "defender",
                "action": 0,  # MONITOR_LOGS
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["current_player"] == "attacker"

        # Verify state
        resp = client.get(f"/game/sessions/{sid}")
        assert resp.status_code == 200
        state = resp.json()
        assert state["turn"] == 6  # After 5 full rounds


class TestHumanVsAI:
    """Test human attacker vs. AI defender."""

    def test_human_attack_ai_defend(self, client):
        """Human attacks, AI defends via /ai/decide."""
        # Create session
        resp = client.post("/game/sessions", json={
            "scenario_id": "tutorial",
            "attacker_type": "human",
            "defender_type": "ai",
            "ai_difficulty": "normal",
        })
        assert resp.status_code == 200
        sid = resp.json()["session_id"]

        for turn in range(3):
            # Human attacker
            resp = client.post(f"/game/sessions/{sid}/action", json={
                "session_id": sid,
                "player": "attacker",
                "action": AttackerAction.SCAN_NETWORK,
            })
            assert resp.status_code == 200

            if resp.json()["game_over"]:
                break

            # Get AI defender decision
            obs_resp = client.get(f"/game/sessions/{sid}/observation/defender")
            assert obs_resp.status_code == 200
            obs = obs_resp.json()["observation"]

            ai_resp = client.post("/ai/decide", json={
                "role": "defender",
                "difficulty": "normal",
                "observation": obs,
            })
            assert ai_resp.status_code == 200
            ai_action = ai_resp.json()["action"]

            # Submit AI action
            resp = client.post(f"/game/sessions/{sid}/action", json={
                "session_id": sid,
                "player": "defender",
                "action": ai_action,
            })
            assert resp.status_code == 200


class TestAIVsHuman:
    """Test AI attacker vs. human defender."""

    def test_ai_attack_human_defend(self, client):
        """AI attacks, human defends."""
        resp = client.post("/game/sessions", json={
            "scenario_id": "tutorial",
            "attacker_type": "ai",
            "defender_type": "human",
            "ai_difficulty": "normal",
        })
        assert resp.status_code == 200
        sid = resp.json()["session_id"]

        for turn in range(3):
            # Get AI attacker decision
            obs_resp = client.get(f"/game/sessions/{sid}/observation/attacker")
            obs = obs_resp.json()["observation"]

            ai_resp = client.post("/ai/decide", json={
                "role": "attacker",
                "difficulty": "normal",
                "observation": obs,
            })
            ai_action = ai_resp.json()["action"]

            # Submit AI action
            resp = client.post(f"/game/sessions/{sid}/action", json={
                "session_id": sid,
                "player": "attacker",
                "action": ai_action,
            })
            assert resp.status_code == 200

            if resp.json()["game_over"]:
                break

            # Human defender
            resp = client.post(f"/game/sessions/{sid}/action", json={
                "session_id": sid,
                "player": "defender",
                "action": DefenderAction.MONITOR_LOGS,
            })
            assert resp.status_code == 200


class TestAIVsAI:
    """Test AI attacker vs. AI defender (simulation)."""

    def test_full_ai_vs_ai_game(self):
        """Run a full AI vs AI game using play_episode."""
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()
        result = play_episode(attacker, defender, num_nodes=5, max_turns=20, seed=42)

        assert result["winner"] in ("attacker", "defender")
        assert len(result["trajectory"]) > 0

    def test_ai_vs_ai_via_api(self, client):
        """Run AI vs AI via API endpoints."""
        resp = client.post("/game/sessions", json={
            "scenario_id": "tutorial",
            "attacker_type": "ai",
            "defender_type": "ai",
            "ai_difficulty": "normal",
        })
        sid = resp.json()["session_id"]

        for turn in range(10):
            state = client.get(f"/game/sessions/{sid}").json()
            if state["game_over"]:
                break

            player = state["current_player"]
            obs = client.get(f"/game/sessions/{sid}/observation/{player}").json()["observation"]

            ai_resp = client.post("/ai/decide", json={
                "role": player,
                "difficulty": "normal",
                "observation": obs,
            })
            action = ai_resp.json()["action"]

            resp = client.post(f"/game/sessions/{sid}/action", json={
                "session_id": sid,
                "player": player,
                "action": action,
            })
            assert resp.status_code == 200


class TestEndToEndGameFlow:
    """Test full end-to-end game flow with all subsystems."""

    def test_action_executor_integration(self):
        """Test ActionExecutor with TurnManager and resources."""
        gs = GameState(num_nodes=5, max_turns=10)
        for i in range(4):
            gs.full_topology[i, i + 1] = 1
            gs.full_topology[i + 1, i] = 1

        tm = TurnManager(scenario={"max_turns": 10})
        executor = ActionExecutor(
            stealth_system=StealthAlertSystem(),
            resource_manager=ResourceManager(),
        )
        tm.start_game()

        # Attacker scans
        result = executor.execute("attacker", AttackerAction.SCAN_NETWORK, gs, 0)
        assert "alert_update" in result
        tm.process_action("attacker", 0, result)

        # Defender monitors
        result = executor.execute("defender", DefenderAction.MONITOR_LOGS, gs, 0)
        tm.process_action("defender", 0, result)

        assert tm.current_turn == 2
        assert tm.current_player == "attacker"

    def test_victory_conditions_integration(self):
        """Test victory conditions with game state."""
        gs = GameState(num_nodes=5, max_turns=10)
        objectives = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end_conds = GameEndConditions(max_turns=10)

        # Not over yet
        result = end_conds.check_game_end(gs, 1, objectives)
        assert result["game_over"] is False

        # Compromise enough nodes for attacker win
        gs.attacker_owned_nodes[:3] = 1
        result = end_conds.check_game_end(gs, 1, objectives)
        assert result["game_over"] is True
        assert result["winner"] == "attacker"

    def test_replay_integration(self):
        """Test replay recording during game."""
        from src.game.replay_recorder import ReplayRecorder

        recorder = ReplayRecorder("test-session", "tutorial")
        recorder.set_initial_state({"num_nodes": 5})

        for i in range(5):
            recorder.record_turn({
                "turn": i,
                "player": "attacker" if i % 2 == 0 else "defender",
                "action": 0,
                "result": {"success": True},
            })

        recorder.set_winner("attacker")

        data = recorder.get_replay_data()
        assert len(data["events"]) == 5
        assert data["metadata"]["winner"] == "attacker"

        trajectories = recorder.extract_trajectories()
        assert len(trajectories["attacker"]) == 3
        assert len(trajectories["defender"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
