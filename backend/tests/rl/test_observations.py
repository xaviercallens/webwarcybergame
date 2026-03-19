"""
Unit tests for partial observability (fog of war) mechanics.
Tests observation space implementation per blueprint Section 1.
"""

import pytest
import numpy as np

from src.rl.observation_space import (
    GameState,
    get_attacker_observation,
    get_defender_observation,
    observation_to_vector,
    get_observation_space_size,
)


class TestGameState:
    """Test GameState class."""
    
    def test_gamestate_creation(self):
        """Test creating GameState."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        assert gs.num_nodes == 10
        assert gs.max_turns == 50
        assert gs.turn == 0
        assert gs.alert_level == 0
    
    def test_gamestate_arrays_initialized(self):
        """Test GameState arrays are properly initialized."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        assert gs.full_topology.shape == (10, 10)
        assert gs.compromised_nodes.shape == (10,)
        assert gs.patched_nodes.shape == (10,)
        assert gs.vulnerabilities.shape == (10,)
        assert gs.attacker_owned_nodes.shape == (10,)
        assert gs.defender_detected_compromises.shape == (10,)
    
    def test_gamestate_resources_initialized(self):
        """Test GameState resources are initialized."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        assert "exploit_kits" in gs.attacker_resources
        assert "ir_budget" in gs.defender_resources
        assert gs.attacker_resources["exploit_kits"] > 0
        assert gs.defender_resources["ir_budget"] > 0


class TestAttackerObservation:
    """Test attacker partial observation."""
    
    def test_attacker_observation_structure(self):
        """Test attacker observation has correct structure."""
        gs = GameState(num_nodes=10, max_turns=50)
        obs = get_attacker_observation(gs)
        
        assert isinstance(obs, dict)
        assert "network_topology" in obs
        assert "compromised_nodes" in obs
        assert "vulnerabilities" in obs
        assert "alert_level" in obs
        assert "turn_number" in obs
        assert "resources" in obs
    
    def test_attacker_cannot_see_alert_level(self):
        """Test attacker's alert level is always 0 (hidden)."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.alert_level = 50
        
        obs = get_attacker_observation(gs)
        
        # Alert level should be 0 in attacker's observation
        assert obs["alert_level"][0] == 0
    
    def test_attacker_sees_discovered_topology(self):
        """Test attacker sees only discovered topology."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        # Set some discovered topology
        gs.attacker_discovered_topology[0, 1] = 1
        gs.attacker_discovered_topology[1, 0] = 1
        
        obs = get_attacker_observation(gs)
        
        # Should see discovered topology
        assert obs["network_topology"][0, 1] == 1
        assert obs["network_topology"][1, 0] == 1
    
    def test_attacker_sees_owned_nodes(self):
        """Test attacker sees only owned nodes."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        gs.attacker_owned_nodes[0] = 1
        gs.attacker_owned_nodes[2] = 1
        
        obs = get_attacker_observation(gs)
        
        assert obs["compromised_nodes"][0] == 1
        assert obs["compromised_nodes"][2] == 1
        assert obs["compromised_nodes"][1] == 0
    
    def test_attacker_observation_is_copy(self):
        """Test attacker observation is a copy (not reference)."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.attacker_owned_nodes[0] = 1
        
        obs = get_attacker_observation(gs)
        obs["compromised_nodes"][0] = 0
        
        # Original should be unchanged
        assert gs.attacker_owned_nodes[0] == 1


class TestDefenderObservation:
    """Test defender partial observation."""
    
    def test_defender_observation_structure(self):
        """Test defender observation has correct structure."""
        gs = GameState(num_nodes=10, max_turns=50)
        obs = get_defender_observation(gs)
        
        assert isinstance(obs, dict)
        assert "network_topology" in obs
        assert "compromised_nodes" in obs
        assert "vulnerabilities" in obs
        assert "alert_level" in obs
        assert "turn_number" in obs
        assert "resources" in obs
        assert "patched_nodes" in obs
        assert "isolated_nodes" in obs
    
    def test_defender_sees_full_topology(self):
        """Test defender sees full network topology."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        # Set full topology
        gs.full_topology[0, 1] = 1
        gs.full_topology[1, 0] = 1
        
        obs = get_defender_observation(gs)
        
        # Should see full topology
        assert obs["network_topology"][0, 1] == 1
        assert obs["network_topology"][1, 0] == 1
    
    def test_defender_sees_detected_compromises(self):
        """Test defender sees only detected compromises."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        # Attacker owns nodes but defender only detects some
        gs.attacker_owned_nodes[0] = 1
        gs.attacker_owned_nodes[1] = 1
        gs.defender_detected_compromises[0] = 1
        
        obs = get_defender_observation(gs)
        
        # Defender should only see detected compromises
        assert obs["compromised_nodes"][0] == 1
        assert obs["compromised_nodes"][1] == 0
    
    def test_defender_sees_alert_level(self):
        """Test defender sees alert level."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.alert_level = 50
        
        obs = get_defender_observation(gs)
        
        assert obs["alert_level"][0] == 50
    
    def test_defender_sees_patched_nodes(self):
        """Test defender sees patched nodes."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.patched_nodes[0] = 1
        gs.patched_nodes[2] = 1
        
        obs = get_defender_observation(gs)
        
        assert obs["patched_nodes"][0] == 1
        assert obs["patched_nodes"][2] == 1
    
    def test_defender_sees_isolated_nodes(self):
        """Test defender sees isolated nodes."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.isolated_nodes[0] = 1
        gs.isolated_nodes[3] = 1
        
        obs = get_defender_observation(gs)
        
        assert obs["isolated_nodes"][0] == 1
        assert obs["isolated_nodes"][3] == 1


class TestObservationToVector:
    """Test observation to vector conversion."""
    
    def test_observation_to_vector_returns_array(self):
        """Test observation_to_vector returns numpy array."""
        gs = GameState(num_nodes=10, max_turns=50)
        obs = get_attacker_observation(gs)
        
        vec = observation_to_vector(obs)
        
        assert isinstance(vec, np.ndarray)
        assert vec.dtype == np.float32
    
    def test_observation_to_vector_is_flat(self):
        """Test observation vector is 1D."""
        gs = GameState(num_nodes=10, max_turns=50)
        obs = get_attacker_observation(gs)
        
        vec = observation_to_vector(obs)
        
        assert len(vec.shape) == 1
    
    def test_observation_to_vector_consistency(self):
        """Test observation_to_vector produces consistent output."""
        gs = GameState(num_nodes=10, max_turns=50)
        obs = get_attacker_observation(gs)
        
        vec1 = observation_to_vector(obs)
        vec2 = observation_to_vector(obs)
        
        np.testing.assert_array_equal(vec1, vec2)
    
    def test_observation_to_vector_size(self):
        """Test observation vector has expected size."""
        gs = GameState(num_nodes=10, max_turns=50)
        obs = get_attacker_observation(gs)
        
        vec = observation_to_vector(obs)
        
        # Should contain flattened topology, nodes, vulns, and scalars
        expected_min_size = (10 * 10) + 10 + 10 + 3  # topology + nodes + vulns + scalars
        assert len(vec) >= expected_min_size
    
    def test_observation_to_vector_defender_larger(self):
        """Test defender observation vector is larger (more info)."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        attacker_obs = get_attacker_observation(gs)
        defender_obs = get_defender_observation(gs)
        
        attacker_vec = observation_to_vector(attacker_obs)
        defender_vec = observation_to_vector(defender_obs)
        
        # Defender should have more information
        assert len(defender_vec) > len(attacker_vec)


class TestObservationSpaceSize:
    """Test observation space size calculation."""
    
    def test_observation_space_size_attacker(self):
        """Test observation space size for attacker."""
        size = get_observation_space_size(num_nodes=10, role="attacker")
        
        assert isinstance(size, int)
        assert size > 0
    
    def test_observation_space_size_defender(self):
        """Test observation space size for defender."""
        size = get_observation_space_size(num_nodes=10, role="defender")
        
        assert isinstance(size, int)
        assert size > 0
    
    def test_observation_space_size_defender_larger(self):
        """Test defender observation space is larger."""
        attacker_size = get_observation_space_size(num_nodes=10, role="attacker")
        defender_size = get_observation_space_size(num_nodes=10, role="defender")
        
        assert defender_size > attacker_size
    
    def test_observation_space_size_scales_with_nodes(self):
        """Test observation space size scales with number of nodes."""
        size_10 = get_observation_space_size(num_nodes=10, role="attacker")
        size_20 = get_observation_space_size(num_nodes=20, role="attacker")
        
        # Should scale roughly quadratically (topology matrix)
        assert size_20 > size_10
    
    def test_observation_space_size_matches_vector(self):
        """Test observation space size matches actual vector size."""
        num_nodes = 10
        expected_size = get_observation_space_size(num_nodes=num_nodes, role="attacker")
        
        gs = GameState(num_nodes=num_nodes, max_turns=50)
        obs = get_attacker_observation(gs)
        vec = observation_to_vector(obs)
        
        assert len(vec) == expected_size


class TestPartialObservabilityInherent:
    """Test that partial observability is inherent to the design."""
    
    def test_attacker_and_defender_different_views(self):
        """Test attacker and defender have fundamentally different views."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        # Set up game state
        gs.full_topology[0, 1] = 1
        gs.attacker_discovered_topology[0, 1] = 1
        gs.attacker_owned_nodes[0] = 1
        gs.defender_detected_compromises[0] = 0  # Defender doesn't know yet
        gs.alert_level = 30
        
        attacker_obs = get_attacker_observation(gs)
        defender_obs = get_defender_observation(gs)
        
        # Attacker sees owned node but defender doesn't
        assert attacker_obs["compromised_nodes"][0] == 1
        assert defender_obs["compromised_nodes"][0] == 0
        
        # Defender sees alert level but attacker doesn't
        assert defender_obs["alert_level"][0] == 30
        assert attacker_obs["alert_level"][0] == 0
    
    def test_information_asymmetry(self):
        """Test information asymmetry between roles."""
        gs = GameState(num_nodes=10, max_turns=50)
        
        # Attacker discovers some nodes
        gs.attacker_discovered_topology[0, 1] = 1
        gs.attacker_discovered_topology[1, 2] = 1
        
        # But full topology has more connections
        gs.full_topology[0, 1] = 1
        gs.full_topology[1, 2] = 1
        gs.full_topology[2, 3] = 1
        gs.full_topology[3, 4] = 1
        
        attacker_obs = get_attacker_observation(gs)
        defender_obs = get_defender_observation(gs)
        
        attacker_discovered = np.sum(attacker_obs["network_topology"])
        defender_discovered = np.sum(defender_obs["network_topology"])
        
        # Defender should see more of the network
        assert defender_discovered > attacker_discovered


class TestObservationEdgeCases:
    """Test edge cases in observation handling."""
    
    def test_empty_network(self):
        """Test observation with empty network (no nodes)."""
        gs = GameState(num_nodes=1, max_turns=50)
        
        obs = get_attacker_observation(gs)
        vec = observation_to_vector(obs)
        
        assert isinstance(vec, np.ndarray)
        assert len(vec) > 0
    
    def test_fully_compromised_network(self):
        """Test observation when all nodes are compromised."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.attacker_owned_nodes[:] = 1
        
        obs = get_attacker_observation(gs)
        
        assert np.sum(obs["compromised_nodes"]) == 10
    
    def test_max_alert_level(self):
        """Test observation at maximum alert level."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.alert_level = 100
        
        obs = get_defender_observation(gs)
        
        assert obs["alert_level"][0] == 100
    
    def test_all_nodes_patched(self):
        """Test observation when all nodes are patched."""
        gs = GameState(num_nodes=10, max_turns=50)
        gs.patched_nodes[:] = 1
        
        obs = get_defender_observation(gs)
        
        assert np.sum(obs["patched_nodes"]) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
