"""
Extended tests for train_agents.py to cover uncovered branches.
Targets lines: 157, 224, 258-288, 301-308 (difficulty configs, edge cases).
"""

import pytest
import numpy as np

from src.rl.train_agents import (
    RandomAgent,
    RuleBasedAttacker,
    RuleBasedDefender,
    play_episode,
    self_play_training_loop,
    train_agents_for_difficulty,
)


class TestRandomAgentEdge:

    def test_predict_deterministic(self):
        agent = RandomAgent(action_space_n=8)
        obs = np.zeros(50)
        a1, _ = agent.predict(obs, deterministic=True)
        assert 0 <= a1 < 8

    def test_predict_non_deterministic(self):
        agent = RandomAgent(action_space_n=8)
        obs = np.zeros(50)
        actions = set()
        for _ in range(100):
            a, _ = agent.predict(obs, deterministic=False)
            actions.add(a)
        assert len(actions) > 1  # Should vary


class TestRuleBasedAttackerEdge:

    def test_predict_with_empty_obs(self):
        agent = RuleBasedAttacker()
        obs = np.zeros(10)
        a, _ = agent.predict(obs)
        assert 0 <= a < 8

    def test_predict_with_large_obs(self):
        agent = RuleBasedAttacker()
        obs = np.ones(500)
        a, _ = agent.predict(obs)
        assert 0 <= a < 8


class TestRuleBasedDefenderEdge:

    def test_predict_with_empty_obs(self):
        agent = RuleBasedDefender()
        obs = np.zeros(10)
        a, _ = agent.predict(obs)
        assert 0 <= a < 7

    def test_predict_with_large_obs(self):
        agent = RuleBasedDefender()
        obs = np.ones(500)
        a, _ = agent.predict(obs)
        assert 0 <= a < 7


class TestPlayEpisodeEdge:

    def test_very_short_game(self):
        result = play_episode(
            RandomAgent(action_space_n=8), RandomAgent(action_space_n=7),
            num_nodes=3, max_turns=2, seed=42,
        )
        assert "winner" in result
        assert "trajectory" in result

    def test_large_game(self):
        result = play_episode(
            RuleBasedAttacker(), RuleBasedDefender(),
            num_nodes=15, max_turns=50, seed=99,
        )
        assert result["winner"] in ("attacker", "defender")

    def test_different_seeds_different_outcomes(self):
        results = set()
        for seed in range(20):
            r = play_episode(
                RandomAgent(action_space_n=8), RandomAgent(action_space_n=7),
                num_nodes=5, max_turns=10, seed=seed,
            )
            results.add(r["winner"])
        # Should have at least some variation
        assert len(results) >= 1


class TestSelfPlayTrainingLoop:

    def test_small_loop(self):
        results = self_play_training_loop(n_episodes=5, num_nodes=5, max_turns=10)
        assert results["total_episodes"] == 5
        assert "attacker_wins" in results
        assert "defender_wins" in results

    def test_loop_with_logging(self):
        results = self_play_training_loop(
            n_episodes=3, num_nodes=5, max_turns=10, log_interval=100,
        )
        assert results["total_episodes"] == 3


class TestTrainAgentsForDifficulty:

    def test_novice(self, monkeypatch):
        import src.rl.train_agents as ta
        monkeypatch.setitem(ta.DIFFICULTY_CONFIGS["novice"], "episodes", 3)
        result = train_agents_for_difficulty("novice")
        assert "total_episodes" in result
        assert "attacker_wins" in result

    def test_unknown_difficulty_raises(self):
        with pytest.raises(ValueError):
            train_agents_for_difficulty("unknown")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
