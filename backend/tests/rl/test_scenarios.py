"""
Unit tests for scenario loader.
"""

import pytest

from src.rl.scenarios.scenario_loader import (
    load_scenario,
    list_scenarios,
    validate_scenario,
    get_scenario_for_difficulty,
    DEFAULT_SCENARIOS,
)


class TestLoadScenario:

    def test_load_builtin_tutorial(self):
        s = load_scenario("tutorial")
        assert s["name"] == "Tutorial - First Breach"
        assert s["num_nodes"] == 5

    def test_load_builtin_corporate(self):
        s = load_scenario("corporate_network")
        assert s["num_nodes"] == 10

    def test_load_unknown_raises(self):
        with pytest.raises(ValueError):
            load_scenario("nonexistent_scenario")

    def test_load_returns_copy(self):
        s1 = load_scenario("tutorial")
        s2 = load_scenario("tutorial")
        s1["num_nodes"] = 999
        assert s2["num_nodes"] == 5


class TestListScenarios:

    def test_list_returns_list(self):
        scenarios = list_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) == len(DEFAULT_SCENARIOS)

    def test_list_contains_required_fields(self):
        for s in list_scenarios():
            assert "id" in s
            assert "name" in s
            assert "difficulty" in s


class TestValidateScenario:

    def test_valid_scenario(self):
        s = load_scenario("tutorial")
        assert validate_scenario(s) is True

    def test_missing_field_raises(self):
        with pytest.raises(ValueError, match="Missing required field"):
            validate_scenario({"name": "test"})

    def test_invalid_num_nodes(self):
        s = load_scenario("tutorial")
        s["num_nodes"] = 0
        with pytest.raises(ValueError):
            validate_scenario(s)

    def test_invalid_type(self):
        s = load_scenario("tutorial")
        s["type"] = "invalid_type"
        with pytest.raises(ValueError):
            validate_scenario(s)


class TestGetScenarioForDifficulty:

    def test_novice(self):
        s = get_scenario_for_difficulty("novice")
        assert s["difficulty"] == "novice"

    def test_expert(self):
        s = get_scenario_for_difficulty("expert")
        assert s["difficulty"] == "expert"

    def test_unknown_falls_back(self):
        s = get_scenario_for_difficulty("unknown")
        assert s is not None
        assert "num_nodes" in s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
