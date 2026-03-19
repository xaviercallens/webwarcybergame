"""
Tests for uncovered victory_conditions branches:
capture_flag, survival scenarios, get_objectives_status, get_game_score,
attacker/defender objective lists, alert-level game end.
"""

import pytest
import numpy as np

from src.rl.observation_space import GameState
from src.game.victory_conditions import (
    VictoryCondition,
    VictoryType,
    ScenarioObjectives,
    GameEndConditions,
)


@pytest.fixture
def gs():
    state = GameState(num_nodes=10, max_turns=30)
    for i in range(9):
        state.full_topology[i, i + 1] = 1
        state.full_topology[i + 1, i] = 1
    return state


class TestCaptureTheFlagScenario:

    def test_setup(self):
        obj = ScenarioObjectives(scenario={"type": "capture_flag", "num_nodes": 10})
        assert len(obj.objectives) == 2
        types = {o.condition_type for o in obj.objectives}
        assert VictoryType.ATTACKER_EXFILTRATE in types
        assert VictoryType.DEFENDER_CONTAINMENT in types

    def test_attacker_wins_by_exfiltration(self, gs):
        obj = ScenarioObjectives(scenario={"type": "capture_flag", "num_nodes": 10})
        gs.data_exfiltrated = 100
        result = obj.check_objectives(gs)
        assert result["game_won"] is True
        assert result["winner"] == "attacker"

    def test_defender_wins_by_containment(self, gs):
        obj = ScenarioObjectives(scenario={"type": "capture_flag", "num_nodes": 10})
        gs.isolated_nodes[:5] = 1
        result = obj.check_objectives(gs)
        assert result["game_won"] is True
        assert result["winner"] == "defender"


class TestSurvivalScenario:

    def test_setup(self):
        obj = ScenarioObjectives(scenario={"type": "survival", "num_nodes": 10})
        assert len(obj.objectives) == 2

    def test_attacker_wins_by_critical_compromise(self, gs):
        obj = ScenarioObjectives(scenario={"type": "survival", "num_nodes": 10})
        gs.attacker_owned_nodes[:3] = 1
        result = obj.check_objectives(gs)
        assert result["game_won"] is True
        assert result["winner"] == "attacker"

    def test_defender_wins_by_high_alert(self, gs):
        obj = ScenarioObjectives(scenario={"type": "survival", "num_nodes": 10})
        gs.alert_level = 90
        result = obj.check_objectives(gs)
        assert result["game_won"] is True
        assert result["winner"] == "defender"


class TestGetObjectivesStatus:

    def test_status_default(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 10})
        status = obj.get_objectives_status(gs)
        assert "objectives" in status
        assert len(status["objectives"]) == 2
        for o in status["objectives"]:
            assert "description" in o
            assert "met" in o
            assert "progress" in o

    def test_progress_increases(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 10})
        status1 = obj.get_objectives_status(gs)
        gs.attacker_owned_nodes[:3] = 1
        status2 = obj.get_objectives_status(gs)
        atk1 = [o for o in status1["objectives"] if o["winner"] == "attacker"][0]
        atk2 = [o for o in status2["objectives"] if o["winner"] == "attacker"][0]
        assert atk2["progress"] > atk1["progress"]


class TestObjectiveLists:

    def test_get_attacker_objectives(self):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 10})
        atk = obj.get_attacker_objectives()
        assert len(atk) >= 1
        assert all(isinstance(s, str) for s in atk)

    def test_get_defender_objectives(self):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 10})
        defs = obj.get_defender_objectives()
        assert len(defs) >= 1


class TestAlertLevelGameEnd:

    def test_alert_100_ends_game(self, gs):
        # Use a scenario type with no alert-based objective so the alert_level >= 100
        # check in GameEndConditions fires (not objective check)
        obj = ScenarioObjectives(scenario={"type": "capture_flag", "num_nodes": 10})
        end = GameEndConditions(max_turns=50)
        gs.alert_level = 100
        result = end.check_game_end(gs, 5, obj)
        assert result["game_over"] is True
        assert result["winner"] == "defender"
        assert "caught" in result["reason"].lower() or "detected" in result["reason"].lower()

    def test_alert_triggers_objective_in_default(self, gs):
        # In default scenario, alert=100 triggers the defender detection objective
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 10})
        end = GameEndConditions(max_turns=50)
        gs.alert_level = 100
        result = end.check_game_end(gs, 5, obj)
        assert result["game_over"] is True
        assert result["winner"] == "defender"
        assert result["reason"] == "Objective achieved"


class TestGetGameScore:

    def test_score_calculation(self, gs):
        end = GameEndConditions(max_turns=50)
        gs.attacker_owned_nodes[:3] = 1
        gs.defender_detected_compromises[:2] = 1
        gs.alert_level = 40
        score = end.get_game_score(gs)
        assert score["attacker"] == 30  # 3 * 10
        assert score["defender"] == 70  # 2*15 + 40


class TestUnknownScenarioType:

    def test_unknown_type_no_objectives(self):
        obj = ScenarioObjectives(scenario={"type": "unknown_type"})
        assert len(obj.objectives) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
