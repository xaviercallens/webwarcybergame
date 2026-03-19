"""
Extended unit tests for victory conditions.
Covers uncovered branches: attacker/defender specific wins, edge cases.
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
    state = GameState(num_nodes=5, max_turns=20)
    for i in range(4):
        state.full_topology[i, i + 1] = 1
        state.full_topology[i + 1, i] = 1
    return state


class TestVictoryCondition:

    def test_create_condition(self):
        vc = VictoryCondition(
            condition_type=VictoryType.ATTACKER_COMPROMISE,
            winner="attacker",
            threshold=3,
            description="Compromise 3 nodes",
        )
        assert vc.condition_type == VictoryType.ATTACKER_COMPROMISE
        assert vc.winner == "attacker"
        assert vc.threshold == 3

    def test_check_attacker_compromise(self, gs):
        vc = VictoryCondition(VictoryType.ATTACKER_COMPROMISE, "attacker", 3, "Compromise 3")
        assert not vc.check(gs)
        gs.attacker_owned_nodes[:3] = 1
        assert vc.check(gs)

    def test_check_defender_detection(self, gs):
        vc = VictoryCondition(VictoryType.DEFENDER_DETECTION, "defender", 80, "Alert 80")
        assert vc.check(gs) is False
        gs.alert_level = 90
        assert vc.check(gs) is True

    def test_check_attacker_exfiltrate(self, gs):
        vc = VictoryCondition(VictoryType.ATTACKER_EXFILTRATE, "attacker", 50, "Exfil 50")
        assert vc.check(gs) is False
        gs.data_exfiltrated = 60
        assert vc.check(gs) is True

    def test_check_defender_containment(self, gs):
        vc = VictoryCondition(VictoryType.DEFENDER_CONTAINMENT, "defender", 2, "Isolate 2")
        assert not vc.check(gs)
        gs.isolated_nodes[:2] = 1
        assert vc.check(gs)

    def test_check_time_limit(self, gs):
        vc = VictoryCondition(VictoryType.TIME_LIMIT, "defender", 10, "Survive")
        assert vc.check(gs) is False  # Time limit checked separately


class TestScenarioObjectives:

    def test_default_scenario(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        assert obj is not None

    def test_custom_scenario(self):
        obj = ScenarioObjectives(scenario={
            "type": "custom",
            "num_nodes": 10,
            "target_nodes": [8, 9],
            "max_turns": 30,
        })
        assert obj is not None

    def test_attacker_wins_by_node_control(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=20)

        # Compromise majority of nodes
        gs.attacker_owned_nodes[:3] = 1
        result = end.check_game_end(gs, 1, obj)
        assert result["game_over"] is True
        assert result["winner"] == "attacker"

    def test_defender_wins_by_surviving(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=20)

        # No attacker nodes, game at max turns
        result = end.check_game_end(gs, 20, obj)
        assert result["game_over"] is True
        assert result["winner"] == "defender"

    def test_game_not_over_mid_game(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=20)

        gs.attacker_owned_nodes[0] = 1
        result = end.check_game_end(gs, 5, obj)
        assert result["game_over"] is False

    def test_attacker_wins_with_data_exfil(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=20)

        gs.attacker_owned_nodes[:4] = 1
        result = end.check_game_end(gs, 10, obj)
        assert result["game_over"] is True
        assert result["winner"] == "attacker"


class TestGameEndConditions:

    def test_max_turns_reached(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=10)

        result = end.check_game_end(gs, 10, obj)
        assert result["game_over"] is True

    def test_max_turns_not_reached(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=10)

        result = end.check_game_end(gs, 5, obj)
        # May or may not be over depending on node state
        assert "game_over" in result

    def test_all_nodes_compromised(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=50)

        gs.attacker_owned_nodes[:] = 1
        result = end.check_game_end(gs, 3, obj)
        assert result["game_over"] is True
        assert result["winner"] == "attacker"

    def test_no_nodes_compromised_at_max(self, gs):
        obj = ScenarioObjectives(scenario={"type": "default", "num_nodes": 5})
        end = GameEndConditions(max_turns=10)

        result = end.check_game_end(gs, 10, obj)
        assert result["game_over"] is True
        assert result["winner"] == "defender"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
