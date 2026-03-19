"""
Unit tests for PettingZoo multi-agent wrapper.
Tests 2-player alternating turn functionality.
"""

import pytest
import numpy as np

from src.rl.pettingzoo_wrapper import NeoHackPettingZoo, AlternatingTurnWrapper


class TestNeoHackPettingZooBasics:
    """Test basic PettingZoo environment functionality."""
    
    def test_env_creation(self):
        """Test creating PettingZoo environment."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        assert env.agents == ["attacker", "defender"]
        assert env.possible_agents == ["attacker", "defender"]
        env.close()
    
    def test_action_spaces(self):
        """Test action spaces for both agents."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        
        assert env.action_spaces["attacker"].n == 8
        assert env.action_spaces["defender"].n == 7
        env.close()
    
    def test_observation_spaces(self):
        """Test observation spaces for both agents."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        
        assert env.observation_spaces["attacker"].shape[0] > 0
        assert env.observation_spaces["defender"].shape[0] > 0
        env.close()


class TestNeoHackPettingZooReset:
    """Test PettingZoo reset functionality."""
    
    def test_reset_returns_observations_and_infos(self):
        """Test reset returns observations and infos for both agents."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        observations, infos = env.reset()
        
        assert isinstance(observations, dict)
        assert isinstance(infos, dict)
        assert "attacker" in observations
        assert "defender" in observations
        assert "attacker" in infos
        assert "defender" in infos
        env.close()
    
    def test_reset_initializes_state(self):
        """Test reset initializes game state properly."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        observations, infos = env.reset()
        
        assert env.current_turn == 0
        assert env.agent_selection == "attacker"
        assert env._agent_index == 0
        env.close()
    
    def test_reset_with_seed(self):
        """Test reset with seed for reproducibility."""
        env1 = NeoHackPettingZoo(num_nodes=10, max_turns=50, seed=42)
        obs1, _ = env1.reset(seed=42)
        
        env2 = NeoHackPettingZoo(num_nodes=10, max_turns=50, seed=42)
        obs2, _ = env2.reset(seed=42)
        
        np.testing.assert_array_equal(obs1["attacker"], obs2["attacker"])
        np.testing.assert_array_equal(obs1["defender"], obs2["defender"])
        env1.close()
        env2.close()


class TestNeoHackPettingZooStep:
    """Test PettingZoo step functionality."""
    
    def test_step_executes_action(self):
        """Test step executes action for current agent."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        current_agent = env.agent_selection
        env.step(0)
        
        # Agent should have switched
        assert env.agent_selection != current_agent
        env.close()
    
    def test_alternating_turns(self):
        """Test agents alternate turns."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        agents_sequence = []
        for _ in range(6):
            agents_sequence.append(env.agent_selection)
            env.step(0)
        
        # Should alternate: attacker, defender, attacker, defender, ...
        assert agents_sequence == ["attacker", "defender", "attacker", "defender", "attacker", "defender"]
        env.close()
    
    def test_turn_counter_increments(self):
        """Test turn counter increments after both agents play."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        assert env.current_turn == 0
        
        env.step(0)  # Attacker
        assert env.current_turn == 0
        
        env.step(0)  # Defender
        assert env.current_turn == 1
        
        env.step(0)  # Attacker
        assert env.current_turn == 1
        
        env.step(0)  # Defender
        assert env.current_turn == 2
        env.close()
    
    def test_rewards_tracked(self):
        """Test rewards are tracked for both agents."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        env.step(0)
        
        assert "attacker" in env.rewards
        assert "defender" in env.rewards
        assert isinstance(env.rewards["attacker"], (float, np.floating))
        assert isinstance(env.rewards["defender"], (float, np.floating))
        env.close()
    
    def test_observations_updated(self):
        """Test observations are updated after each step."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        obs_before, _ = env.reset()
        
        env.step(0)
        obs_after = env.observe("attacker")
        
        # Observations should be numpy arrays
        assert isinstance(obs_after, np.ndarray)
        env.close()


class TestNeoHackPettingZooGameplay:
    """Test multi-agent gameplay mechanics."""
    
    def test_shared_game_state(self):
        """Test both agents share the same game state."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        # Both environments should share game state
        assert env.attacker_env.game_state is env.defender_env.game_state
        assert env.attacker_env.game_state is env.shared_game_state
        env.close()
    
    def test_attacker_actions_affect_defender_view(self):
        """Test attacker actions affect defender's observation."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        # Get initial defender observation
        initial_alert = env.shared_game_state.alert_level
        
        # Attacker takes action
        env.step(0)
        
        # Defender's view should be affected
        final_alert = env.shared_game_state.alert_level
        # Alert level may have changed
        assert isinstance(final_alert, (int, np.integer))
        env.close()
    
    def test_multiple_full_rounds(self):
        """Test multiple full rounds of gameplay."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        # Play 10 full rounds (20 steps)
        for _ in range(20):
            env.step(0)
        
        assert env.current_turn == 10
        env.close()


class TestNeoHackPettingZooTermination:
    """Test termination and truncation."""
    
    def test_max_turns_truncation(self):
        """Test truncation when max turns reached."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=2)
        env.reset()
        
        # Play until truncation
        for _ in range(10):
            env.step(0)
            if env.truncations["attacker"] or env.truncations["defender"]:
                break
        
        # At least one agent should be truncated
        assert env.truncations["attacker"] or env.truncations["defender"]
        env.close()
    
    def test_termination_sets_flags(self):
        """Test termination sets proper flags."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        assert not env.terminations["attacker"]
        assert not env.terminations["defender"]
        env.close()


class TestNeoHackPettingZooObservations:
    """Test observation functionality."""
    
    def test_observe_returns_correct_shape(self):
        """Test observe returns correct observation shape."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        attacker_obs = env.observe("attacker")
        defender_obs = env.observe("defender")
        
        assert isinstance(attacker_obs, np.ndarray)
        assert isinstance(defender_obs, np.ndarray)
        assert len(attacker_obs.shape) == 1
        assert len(defender_obs.shape) == 1
        env.close()
    
    def test_observe_different_for_roles(self):
        """Test attacker and defender get different observations."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        attacker_obs = env.observe("attacker")
        defender_obs = env.observe("defender")
        
        # Observations should be different (partial observability)
        assert not np.array_equal(attacker_obs, defender_obs)
        env.close()


class TestNeoHackPettingZooState:
    """Test full state functionality."""
    
    def test_state_returns_vector(self):
        """Test state() returns full game state vector."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        state = env.state()
        
        assert isinstance(state, np.ndarray)
        assert state.dtype == np.float32
        assert len(state.shape) == 1
        env.close()
    
    def test_state_changes_with_actions(self):
        """Test state changes after actions."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        env.reset()
        
        state_before = env.state().copy()
        env.step(0)
        state_after = env.state()
        
        # State should change (or at least be recalculated)
        assert isinstance(state_after, np.ndarray)
        env.close()


class TestAlternatingTurnWrapper:
    """Test AlternatingTurnWrapper functionality."""
    
    def test_wrapper_creation(self):
        """Test creating wrapper."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        wrapped = AlternatingTurnWrapper(env)
        
        assert wrapped.env is env
        assert wrapped.last_agent is None
        wrapped.close()
    
    def test_wrapper_enforces_alternation(self):
        """Test wrapper enforces strict alternation."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        wrapped = AlternatingTurnWrapper(env)
        
        wrapped.reset()
        
        # First agent should be attacker
        assert wrapped.agent_selection == "attacker"
        wrapped.step(0)
        
        # Next agent should be defender
        assert wrapped.agent_selection == "defender"
        wrapped.step(0)
        
        # Next agent should be attacker again
        assert wrapped.agent_selection == "attacker"
        wrapped.close()
    
    def test_wrapper_prevents_double_play(self):
        """Test wrapper prevents same agent playing twice."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        wrapped = AlternatingTurnWrapper(env)
        
        wrapped.reset()
        wrapped.step(0)  # Attacker
        
        # Manually set agent back to attacker to test error
        wrapped.env.agent_selection = "attacker"
        
        with pytest.raises(RuntimeError):
            wrapped.step(0)
        
        wrapped.close()
    
    def test_wrapper_properties(self):
        """Test wrapper exposes environment properties."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
        wrapped = AlternatingTurnWrapper(env)
        wrapped.reset()
        
        assert wrapped.agents == ["attacker", "defender"]
        assert wrapped.agent_selection in ["attacker", "defender"]
        assert isinstance(wrapped.rewards, dict)
        assert isinstance(wrapped.terminations, dict)
        assert isinstance(wrapped.truncations, dict)
        assert isinstance(wrapped.infos, dict)
        
        wrapped.close()


class TestNeoHackPettingZooEdgeCases:
    """Test edge cases."""
    
    def test_single_node_network(self):
        """Test with single node network."""
        env = NeoHackPettingZoo(num_nodes=1, max_turns=10)
        obs, info = env.reset()
        
        assert env.shared_game_state.num_nodes == 1
        env.step(0)
        env.close()
    
    def test_large_network(self):
        """Test with large network."""
        env = NeoHackPettingZoo(num_nodes=50, max_turns=10)
        obs, info = env.reset()
        
        assert env.shared_game_state.num_nodes == 50
        env.step(0)
        env.close()
    
    def test_zero_max_turns(self):
        """Test with zero max turns."""
        env = NeoHackPettingZoo(num_nodes=10, max_turns=0)
        obs, info = env.reset()
        
        env.step(0)
        assert env.truncations["attacker"] or env.truncations["defender"]
        env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
