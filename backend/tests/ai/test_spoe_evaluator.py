"""
Unit tests for S-POE evaluation framework.
Tests MM-SA-Bench and PsyR-OM-Bench scoring.
"""

import pytest
import numpy as np

from src.ai.spoe_evaluator import (
    SPOEEvaluator,
    generate_benchmark_scenarios,
    generate_benchmark_matches,
)


@pytest.fixture
def evaluator():
    return SPOEEvaluator()


class TestF1Score:

    def test_perfect_match(self, evaluator):
        assert evaluator._f1_score([1, 2, 3], [1, 2, 3]) == 1.0

    def test_no_overlap(self, evaluator):
        assert evaluator._f1_score([1, 2], [3, 4]) == 0.0

    def test_partial_overlap(self, evaluator):
        f1 = evaluator._f1_score([1, 2, 3], [2, 3, 4])
        assert 0.5 < f1 < 1.0

    def test_both_empty(self, evaluator):
        assert evaluator._f1_score([], []) == 1.0

    def test_actual_empty(self, evaluator):
        assert evaluator._f1_score([], [1]) == 0.0

    def test_predicted_empty(self, evaluator):
        assert evaluator._f1_score([1], []) == 0.0


class TestPathAccuracy:

    def test_perfect(self, evaluator):
        paths = [[0, 1], [1, 2]]
        assert evaluator._path_accuracy(paths, paths) == 1.0

    def test_no_match(self, evaluator):
        assert evaluator._path_accuracy([[0, 1]], [[2, 3]]) == 0.0

    def test_both_empty(self, evaluator):
        assert evaluator._path_accuracy([], []) == 1.0

    def test_actual_empty_predicted_not(self, evaluator):
        assert evaluator._path_accuracy([], [[0, 1]]) == 0.0

    def test_predicted_empty_actual_not(self, evaluator):
        assert evaluator._path_accuracy([[0, 1]], []) == 0.0


class TestRiskClassification:

    def test_aggressive(self, evaluator):
        actions = [1, 3, 6, 1, 3, 6, 1, 6, 3, 1]
        assert evaluator._classify_risk_from_actions(actions) == "aggressive"

    def test_cautious(self, evaluator):
        actions = [0, 2, 7, 0, 2, 7, 0, 2, 7, 0]
        assert evaluator._classify_risk_from_actions(actions) == "cautious"

    def test_balanced(self, evaluator):
        actions = [0, 1, 2, 0, 0, 2, 7, 0, 2, 0]
        result = evaluator._classify_risk_from_actions(actions)
        assert result in ("balanced", "cautious")

    def test_empty(self, evaluator):
        assert evaluator._classify_risk_from_actions([]) == "unknown"


class TestRandomBaselineDetection:

    def test_nonzero(self, evaluator):
        score = evaluator._random_baseline_detection([0, 1], 10)
        assert score == pytest.approx(0.2)

    def test_empty_actual(self, evaluator):
        assert evaluator._random_baseline_detection([], 10) == 0.0

    def test_zero_nodes(self, evaluator):
        assert evaluator._random_baseline_detection([1], 0) == 0.0


class TestSituationalAwareness:

    def test_no_scenarios(self, evaluator):
        result = evaluator.evaluate_situational_awareness(object(), [])
        assert result["mmsa_score"] == 0.0

    def test_with_scenarios_no_agent_methods(self, evaluator):
        scenarios = generate_benchmark_scenarios(num_scenarios=5)
        result = evaluator.evaluate_situational_awareness(object(), scenarios)
        assert "mmsa_score" in result
        assert "breakdown" in result
        assert result["mmsa_score"] >= 0

    def test_with_smart_agent(self, evaluator):
        class SmartAgent:
            def identify_threats(self, scenario):
                return scenario.get("compromised_nodes", [])

            def predict_lateral_movement(self, scenario):
                return scenario.get("attack_paths", [])

            def predict_next_move(self, scenario):
                return scenario.get("next_target")

        agent = SmartAgent()
        scenarios = generate_benchmark_scenarios(num_scenarios=10)
        result = evaluator.evaluate_situational_awareness(agent, scenarios)
        assert result["mmsa_score"] == 100.0


class TestOpponentModeling:

    def test_no_matches(self, evaluator):
        result = evaluator.evaluate_opponent_modeling(object(), [])
        assert result["pom_score"] == 0.0

    def test_with_matches_no_agent_method(self, evaluator):
        matches = generate_benchmark_matches(num_matches=10)
        result = evaluator.evaluate_opponent_modeling(object(), matches)
        assert "pom_score" in result
        assert result["pom_score"] >= 0

    def test_perfect_agent(self, evaluator):
        class PerfectAgent:
            def infer_risk_preference(self, actions):
                high_risk = {1, 3, 6}
                risky = sum(1 for a in actions if a in high_risk)
                ratio = risky / len(actions) if actions else 0
                if ratio > 0.5:
                    return "aggressive"
                elif ratio > 0.2:
                    return "balanced"
                return "cautious"

        matches = generate_benchmark_matches(num_matches=20)
        result = evaluator.evaluate_opponent_modeling(PerfectAgent(), matches)
        assert result["pom_score"] > 50


class TestFullEvaluation:

    def test_full_eval(self, evaluator):
        scenarios = generate_benchmark_scenarios(5)
        matches = generate_benchmark_matches(5)
        result = evaluator.evaluate_full(object(), scenarios, matches)
        assert "overall_score" in result
        assert "situational_awareness" in result
        assert "opponent_modeling" in result


class TestBenchmarkGenerators:

    def test_generate_scenarios(self):
        scenarios = generate_benchmark_scenarios(num_scenarios=10)
        assert len(scenarios) == 10
        for s in scenarios:
            assert "difficulty" in s
            assert "compromised_nodes" in s
            assert "attack_paths" in s
            assert "next_target" in s
            assert s["num_nodes"] in (5, 10, 20)

    def test_generate_scenarios_zero(self):
        scenarios = generate_benchmark_scenarios(num_scenarios=0)
        assert len(scenarios) == 0

    def test_generate_scenarios_negative(self):
        with pytest.raises(ValueError, match="num_scenarios cannot be negative"):
            generate_benchmark_scenarios(num_scenarios=-1)

    def test_generate_scenarios_empty_difficulty(self):
        with pytest.raises(ValueError, match="difficulty_levels cannot be empty"):
            generate_benchmark_scenarios(difficulty_levels=[])

    def test_generate_scenarios_invalid_difficulty(self):
        with pytest.raises(ValueError, match="Invalid difficulty level: 'impossible'"):
            generate_benchmark_scenarios(difficulty_levels=["impossible"])

    def test_generate_scenarios_difficulty_mapping(self):
        scenarios = generate_benchmark_scenarios(num_scenarios=1, difficulty_levels=["easy"])
        assert len(scenarios) == 1
        assert scenarios[0]["difficulty"] == "easy"
        assert scenarios[0]["num_nodes"] == 5

        scenarios = generate_benchmark_scenarios(num_scenarios=1, difficulty_levels=["medium"])
        assert scenarios[0]["difficulty"] == "medium"
        assert scenarios[0]["num_nodes"] == 10

        scenarios = generate_benchmark_scenarios(num_scenarios=1, difficulty_levels=["hard"])
        assert scenarios[0]["difficulty"] == "hard"
        assert scenarios[0]["num_nodes"] == 20

    def test_generate_scenarios_constraints(self):
        scenarios = generate_benchmark_scenarios(num_scenarios=50)
        for s in scenarios:
            comp_nodes = s["compromised_nodes"]
            next_target = s["next_target"]
            attack_paths = s["attack_paths"]

            # Target must not be in compromised nodes
            if next_target is not None:
                assert next_target not in comp_nodes

            # Attack paths must not be self-loops
            for path in attack_paths:
                assert len(path) == 2
                assert path[0] != path[1]

    def test_generate_matches(self):
        matches = generate_benchmark_matches(num_matches=15)
        assert len(matches) == 15
        for m in matches:
            assert "action_sequence" in m
            assert "opponent_risk_preference" in m
            assert m["opponent_risk_preference"] in ("aggressive", "balanced", "cautious")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
