"""
Unit tests for NeoHackEnv Gymnasium compliance.
Tests basic environment functionality and Gymnasium API compliance.
"""

import pytest
import numpy as np
from gymnasium import spaces

from src.rl.neohack_env import NeoHackEnv
from src.rl.action_space import AttackerAction, DefenderAction


class TestNeoHackEnvBasics:
    """Test basic environment functionality."""
    
    def test_env_creation_attacker(self):
        """Test creating attacker environment."""
        env = NeoHackEnv(role="attacker", num_nodes=10, max_turns=50)
        assert env.role == "attacker"
        assert env.num_nodes == 10
        assert env.max_turns == 50
        env.close()
    
    def test_env_creation_defender(self):
        """Test creating defender environment."""
        env = NeoHackEnv(role="defender", num_nodes=10, max_turns=50)
        assert env.role == "defender"
        assert env.num_nodes == 10
        assert env.max_turns == 50
        env.close()
    
    def test_action_space_attacker(self):
        """Test attacker action space."""
        env = NeoHackEnv(role="attacker")
        assert isinstance(env.action_space, spaces.Discrete)
        assert env.action_space.n == 8
        env.close()
    
    def test_action_space_defender(self):
        """Test defender action space."""
        env = NeoHackEnv(role="defender")
        assert isinstance(env.action_space, spaces.Discrete)
        assert env.action_space.n == 7
        env.close()
    
    def test_observation_space(self):
        """Test observation space."""
        env = NeoHackEnv(role="attacker", num_nodes=10)
        assert isinstance(env.observation_space, spaces.Box)
        assert env.observation_space.dtype == np.float32
        env.close()


class TestNeoHackEnvReset:
    """Test environment reset functionality."""
    
    def test_reset_returns_observation_and_info(self):
        """Test reset returns observation and info."""
        env = NeoHackEnv(role="attacker")
        obs, info = env.reset()
        
        assert isinstance(obs, np.ndarray)
        assert isinstance(info, dict)
        assert obs.dtype == np.float32
        assert "turn" in info
        assert "alert_level" in info
        env.close()
    
    def test_reset_initializes_state(self):
        """Test reset initializes game state properly."""
        env = NeoHackEnv(role="attacker", num_nodes=10)
        obs, info = env.reset()
        
        assert env.current_turn == 0
        assert env.game_over is False
        assert env.winner is None
        assert len(env.action_history) == 0
        env.close()
    
    def test_reset_with_seed(self):
        """Test reset with seed for reproducibility."""
        env1 = NeoHackEnv(role="attacker", seed=42)
        obs1, _ = env1.reset(seed=42)
        
        env2 = NeoHackEnv(role="attacker", seed=42)
        obs2, _ = env2.reset(seed=42)
        
        np.testing.assert_array_equal(obs1, obs2)
        env1.close()
        env2.close()
    
    def test_observation_shape(self):
        """Test observation has correct shape."""
        env = NeoHackEnv(role="attacker", num_nodes=10)
        obs, _ = env.reset()
        
        assert len(obs.shape) == 1
        assert obs.shape[0] > 0
        env.close()


class TestNeoHackEnvStep:
    """Test environment step functionality."""
    
    def test_step_returns_correct_format(self):
        """Test step returns correct tuple format."""
        env = NeoHackEnv(role="attacker")
        env.reset()
        
        obs, reward, terminated, truncated, info = env.step(0)
        
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, (float, np.floating))
        assert isinstance(terminated, (bool, np.bool_))
        assert isinstance(truncated, (bool, np.bool_))
        assert isinstance(info, dict)
        env.close()
    
    def test_step_increments_turn(self):
        """Test step increments turn counter."""
        env = NeoHackEnv(role="attacker")
        env.reset()
        
        assert env.current_turn == 0
        env.step(0)
        assert env.current_turn == 1
        env.close()
    
    def test_step_invalid_action(self):
        """Test step with invalid action raises error."""
        env = NeoHackEnv(role="attacker")
        env.reset()
        
        with pytest.raises(ValueError):
            env.step(100)
        env.close()
    
    def test_step_after_done(self):
        """Test step after episode is done raises error."""
        env = NeoHackEnv(role="attacker", max_turns=1)
        env.reset()
        
        env.step(0)
        with pytest.raises(RuntimeError):
            env.step(0)
        env.close()
    
    def test_multiple_steps(self):
        """Test multiple steps in sequence."""
        env = NeoHackEnv(role="attacker", max_turns=10)
        env.reset()
        
        for i in range(5):
            obs, reward, terminated, truncated, info = env.step(0)
            assert isinstance(obs, np.ndarray)
            assert env.current_turn == i + 1
        
        env.close()


class TestNeoHackEnvGameplay:
    """Test game mechanics and state transitions."""
    
    def test_attacker_scan_action(self):
        """Test attacker scan action."""
        env = NeoHackEnv(role="attacker", num_nodes=5)
        env.reset()
        
        # Execute scan action
        obs, reward, terminated, truncated, info = env.step(AttackerAction.SCAN_NETWORK)
        
        assert isinstance(obs, np.ndarray)
        assert env.last_action == AttackerAction.SCAN_NETWORK
        env.close()
    
    def test_defender_monitor_action(self):
        """Test defender monitor action."""
        env = NeoHackEnv(role="defender", num_nodes=5)
        env.reset()
        
        obs, reward, terminated, truncated, info = env.step(DefenderAction.MONITOR_LOGS)
        
        assert isinstance(obs, np.ndarray)
        assert env.last_action == DefenderAction.MONITOR_LOGS
        env.close()
    
    def test_alert_level_increases(self):
        """Test alert level increases with attacker actions."""
        env = NeoHackEnv(role="attacker", num_nodes=5)
        env.reset()
        
        initial_alert = env.game_state.alert_level
        
        # Execute multiple attacker actions
        for _ in range(3):
            env.step(AttackerAction.SCAN_NETWORK)
        
        final_alert = env.game_state.alert_level
        assert final_alert >= initial_alert
        env.close()
    
    def test_game_over_on_max_turns(self):
        """Test game ends when max turns reached."""
        env = NeoHackEnv(role="attacker", max_turns=3)
        env.reset()
        
        terminated = False
        for i in range(5):
            obs, reward, terminated, truncated, info = env.step(0)
            if truncated:
                break
        
        assert truncated
        env.close()


class TestNeoHackEnvPartialObservability:
    """Test partial observability (fog of war) mechanics."""
    
    def test_attacker_limited_visibility(self):
        """Test attacker has limited network visibility."""
        env = NeoHackEnv(role="attacker", num_nodes=10)
        env.reset()
        
        # Attacker should not see full topology initially
        attacker_topology = env.game_state.attacker_discovered_topology
        full_topology = env.game_state.full_topology
        
        # Attacker topology should be subset of full topology
        discovered_edges = np.sum(attacker_topology)
        assert discovered_edges <= np.sum(full_topology)
        env.close()
    
    def test_defender_full_visibility(self):
        """Test defender sees full network topology."""
        env = NeoHackEnv(role="defender", num_nodes=10)
        env.reset()
        
        # Defender should see full topology
        defender_obs = env._get_observation()
        assert len(defender_obs) > 0
        env.close()
    
    def test_attacker_cannot_see_alert_level(self):
        """Test attacker observation doesn't include alert level."""
        env = NeoHackEnv(role="attacker", num_nodes=5)
        env.reset()
        
        # Increase alert level
        env.game_state.alert_level = 50
        
        # Get attacker observation
        obs_dict = env._get_observation()
        # Alert level should be 0 in attacker's view
        assert obs_dict[0:1].max() < 50
        env.close()


class TestNeoHackEnvRewards:
    """Test reward calculation."""
    
    def test_reward_is_float(self):
        """Test reward is always a float."""
        env = NeoHackEnv(role="attacker")
        env.reset()
        
        obs, reward, terminated, truncated, info = env.step(0)
        assert isinstance(reward, float)
        env.close()
    
    def test_reward_history(self):
        """Test reward history is tracked."""
        env = NeoHackEnv(role="attacker", max_turns=5)
        env.reset()
        
        for _ in range(3):
            env.step(0)
        
        assert len(env.reward_history) == 3
        assert all(isinstance(r, float) for r in env.reward_history)
        env.close()


class TestNeoHackEnvInfo:
    """Test info dictionary."""
    
    def test_info_contains_required_fields(self):
        """Test info dict contains required fields."""
        env = NeoHackEnv(role="attacker")
        env.reset()
        
        obs, reward, terminated, truncated, info = env.step(0)
        
        required_fields = ["turn", "alert_level", "attacker_nodes", "total_nodes", "game_over"]
        for field in required_fields:
            assert field in info
        env.close()
    
    def test_info_turn_counter(self):
        """Test info turn counter is accurate."""
        env = NeoHackEnv(role="attacker", max_turns=10)
        env.reset()
        
        for i in range(5):
            obs, reward, terminated, truncated, info = env.step(0)
            assert info["turn"] == i + 1
        env.close()


class TestNeoHackEnvGymCompliance:
    """Test Gymnasium API compliance."""
    
    def test_env_api_attacker(self):
        """Test environment API compliance (attacker)."""
        env = NeoHackEnv(role="attacker", num_nodes=5, max_turns=10)
        
        # Test basic API
        obs, info = env.reset()
        assert isinstance(obs, np.ndarray)
        assert isinstance(info, dict)
        
        obs, reward, terminated, truncated, info = env.step(0)
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        env.close()
    
    def test_env_api_defender(self):
        """Test environment API compliance (defender)."""
        env = NeoHackEnv(role="defender", num_nodes=5, max_turns=10)
        
        # Test basic API
        obs, info = env.reset()
        assert isinstance(obs, np.ndarray)
        assert isinstance(info, dict)
        
        obs, reward, terminated, truncated, info = env.step(0)
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        env.close()


class TestNeoHackEnvEdgeCases:
    """Test edge cases and error handling."""
    
    def test_single_node_network(self):
        """Test environment with single node."""
        env = NeoHackEnv(role="attacker", num_nodes=1, max_turns=10)
        obs, info = env.reset()
        
        assert env.num_nodes == 1
        obs, reward, terminated, truncated, info = env.step(0)
        env.close()
    
    def test_large_network(self):
        """Test environment with large network."""
        env = NeoHackEnv(role="attacker", num_nodes=50, max_turns=10)
        obs, info = env.reset()
        
        assert env.num_nodes == 50
        obs, reward, terminated, truncated, info = env.step(0)
        env.close()
    
    def test_zero_max_turns(self):
        """Test environment with zero max turns."""
        env = NeoHackEnv(role="attacker", max_turns=0)
        obs, info = env.reset()
        
        # Should immediately truncate
        obs, reward, terminated, truncated, info = env.step(0)
        assert truncated
        env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
