"""
Unit tests for RL training and evaluation framework.
Tests self-play, baselines, and evaluation pipeline.
"""

import pytest
import numpy as np

from src.rl.train_agents import (
    RandomAgent,
    RuleBasedAttacker,
    RuleBasedDefender,
    play_episode,
    self_play_training_loop,
    DIFFICULTY_CONFIGS,
)
from src.rl.evaluate_agents import (
    evaluate_vs_random,
    evaluate_vs_rule_based,
    evaluate_head_to_head,
    run_full_evaluation,
)


class TestBaselineAgents:
    """Test baseline agent implementations."""

    def test_random_agent_predict(self):
        agent = RandomAgent(action_space_n=8)
        obs = np.zeros(10, dtype=np.float32)
        action, state = agent.predict(obs)
        assert 0 <= action < 8
        assert state is None

    def test_random_agent_range(self):
        agent = RandomAgent(action_space_n=5)
        actions = set()
        for _ in range(200):
            a, _ = agent.predict(np.zeros(10))
            actions.add(a)
        assert actions.issubset(set(range(5)))

    def test_rule_based_attacker(self):
        agent = RuleBasedAttacker()
        obs = np.zeros(10, dtype=np.float32)
        action, _ = agent.predict(obs)
        assert action in RuleBasedAttacker.PRIORITY

    def test_rule_based_attacker_cycles(self):
        agent = RuleBasedAttacker()
        obs = np.zeros(10)
        actions = [agent.predict(obs)[0] for _ in range(10)]
        assert actions[:5] == RuleBasedAttacker.PRIORITY

    def test_rule_based_defender(self):
        agent = RuleBasedDefender()
        obs = np.zeros(10, dtype=np.float32)
        action, _ = agent.predict(obs)
        assert action in RuleBasedDefender.PRIORITY


class TestPlayEpisode:
    """Test single episode gameplay."""

    def test_episode_completes(self):
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()
        result = play_episode(attacker, defender, num_nodes=5, max_turns=10, seed=42)

        assert "winner" in result
        assert result["winner"] in ("attacker", "defender")
        assert "attacker_reward" in result
        assert "defender_reward" in result

    def test_episode_trajectory(self):
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()
        result = play_episode(attacker, defender, num_nodes=5, max_turns=10, seed=42)

        assert "trajectory" in result
        assert len(result["trajectory"]) > 0
        assert result["trajectory"][0]["player"] == "attacker"

    def test_episode_with_random_agents(self):
        attacker = RandomAgent(action_space_n=8)
        defender = RandomAgent(action_space_n=7)
        result = play_episode(attacker, defender, num_nodes=5, max_turns=10, seed=42)

        assert result["winner"] in ("attacker", "defender")

    def test_episode_deterministic_with_seed(self):
        a1, d1 = RuleBasedAttacker(), RuleBasedDefender()
        r1 = play_episode(a1, d1, num_nodes=5, max_turns=10, seed=123)

        a2, d2 = RuleBasedAttacker(), RuleBasedDefender()
        r2 = play_episode(a2, d2, num_nodes=5, max_turns=10, seed=123)

        assert r1["winner"] == r2["winner"]
        assert r1["attacker_reward"] == r2["attacker_reward"]


class TestSelfPlayTraining:
    """Test self-play training loop."""

    def test_training_loop_runs(self):
        results = self_play_training_loop(
            n_episodes=10, num_nodes=5, max_turns=5, log_interval=5
        )

        assert results["total_episodes"] == 10
        assert results["attacker_wins"] + results["defender_wins"] == 10
        assert len(results["attacker_rewards"]) == 10

    def test_training_loop_records_rewards(self):
        results = self_play_training_loop(
            n_episodes=5, num_nodes=5, max_turns=5, log_interval=5
        )

        assert all(isinstance(r, float) for r in results["attacker_rewards"])
        assert all(isinstance(r, float) for r in results["defender_rewards"])


class TestDifficultyConfigs:
    """Test difficulty configuration."""

    def test_all_difficulties_defined(self):
        assert "novice" in DIFFICULTY_CONFIGS
        assert "normal" in DIFFICULTY_CONFIGS
        assert "expert" in DIFFICULTY_CONFIGS

    def test_configs_have_required_fields(self):
        for difficulty, config in DIFFICULTY_CONFIGS.items():
            assert "episodes" in config
            assert "learning_rate" in config
            assert config["episodes"] > 0
            assert config["learning_rate"] > 0

    def test_expert_trains_more(self):
        assert DIFFICULTY_CONFIGS["expert"]["episodes"] > DIFFICULTY_CONFIGS["novice"]["episodes"]


class TestEvalVsRandom:
    """Test evaluation against random opponent."""

    def test_eval_attacker_vs_random(self):
        agent = RuleBasedAttacker()
        result = evaluate_vs_random(agent, "attacker", n_games=10, num_nodes=5, max_turns=10)

        assert "win_rate" in result
        assert 0 <= result["win_rate"] <= 1
        assert result["total_games"] == 10

    def test_eval_defender_vs_random(self):
        agent = RuleBasedDefender()
        result = evaluate_vs_random(agent, "defender", n_games=10, num_nodes=5, max_turns=10)

        assert "win_rate" in result
        assert 0 <= result["win_rate"] <= 1


class TestEvalVsRuleBased:
    """Test evaluation against rule-based opponent."""

    def test_eval_attacker_vs_rulebased(self):
        agent = RuleBasedAttacker()
        result = evaluate_vs_rule_based(agent, "attacker", n_games=10, num_nodes=5, max_turns=10)

        assert "win_rate" in result
        assert result["total_games"] == 10

    def test_eval_defender_vs_rulebased(self):
        agent = RuleBasedDefender()
        result = evaluate_vs_rule_based(agent, "defender", n_games=10, num_nodes=5, max_turns=10)

        assert "win_rate" in result


class TestHeadToHead:
    """Test head-to-head evaluation."""

    def test_head_to_head(self):
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()
        result = evaluate_head_to_head(attacker, defender, n_games=10, num_nodes=5, max_turns=10)

        assert "attacker_win_rate" in result
        assert "defender_win_rate" in result
        assert abs(result["attacker_win_rate"] + result["defender_win_rate"] - 1.0) < 0.01

    def test_h2h_rewards(self):
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()
        result = evaluate_head_to_head(attacker, defender, n_games=10, num_nodes=5, max_turns=10)

        assert isinstance(result["avg_attacker_reward"], float)
        assert isinstance(result["avg_defender_reward"], float)


class TestFullEvaluation:
    """Test complete evaluation suite."""

    def test_full_evaluation_runs(self):
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()
        result = run_full_evaluation(
            attacker, defender, n_games=5, num_nodes=5, max_turns=5
        )

        assert "attacker_vs_random" in result
        assert "defender_vs_random" in result
        assert "attacker_vs_rulebased" in result
        assert "defender_vs_rulebased" in result
        assert "head_to_head" in result
        assert "summary" in result

    def test_full_evaluation_summary(self):
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()
        result = run_full_evaluation(
            attacker, defender, n_games=5, num_nodes=5, max_turns=5
        )

        summary = result["summary"]
        assert "attacker_vs_random_wr" in summary
        assert "defender_vs_random_wr" in summary
        assert "h2h_attacker_wr" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
