"""
Observation space definitions for Neo-Hack v3.1.
Implements partial observability (fog of war) per blueprint Section 1.
"""

from typing import Dict, Any
import numpy as np


class GameState:
    """Represents the complete game state (known to backend only)."""
    
    def __init__(self, num_nodes: int = 10, max_turns: int = 50):
        self.num_nodes = num_nodes
        self.max_turns = max_turns
        self.turn = 0
        
        # Network state
        self.full_topology = np.zeros((num_nodes, num_nodes), dtype=np.int32)
        self.compromised_nodes = np.zeros(num_nodes, dtype=np.int32)
        self.patched_nodes = np.zeros(num_nodes, dtype=np.int32)
        self.isolated_nodes = np.zeros(num_nodes, dtype=np.int32)
        
        # Vulnerabilities
        self.vulnerabilities = np.random.randint(0, 3, size=num_nodes, dtype=np.int32)
        self.discovered_vulns = np.zeros(num_nodes, dtype=np.int32)
        
        # Attacker state
        self.attacker_discovered_topology = np.zeros((num_nodes, num_nodes), dtype=np.int32)
        self.attacker_owned_nodes = np.zeros(num_nodes, dtype=np.int32)
        self.attacker_scanned_vulns = np.zeros(num_nodes, dtype=np.int32)
        self.attacker_resources = {
            "exploit_kits": 10,
            "malware_payloads": 3,
            "time_remaining": max_turns
        }
        
        # Defender state
        self.defender_detected_compromises = np.zeros(num_nodes, dtype=np.int32)
        self.defender_alert_level = 0
        self.defender_resources = {
            "ir_budget": 100,
            "patches_available": 5,
            "scan_bandwidth": 2
        }
        
        # Detection state
        self.alert_level = 0
        self.detection_threshold = 70
        self.last_alert_location = None
        self.last_alert_time = None


def get_attacker_observation(game_state: GameState) -> Dict[str, Any]:
    """
    Get attacker's partial observation.
    Attacker only sees discovered network and owned nodes.
    Alert level is hidden from attacker.
    """
    return {
        "network_topology": game_state.attacker_discovered_topology.copy(),
        "compromised_nodes": game_state.attacker_owned_nodes.copy(),
        "vulnerabilities": game_state.attacker_scanned_vulns.copy(),
        "alert_level": np.array([0], dtype=np.float32),  # Hidden from attacker
        "turn_number": np.array([game_state.turn], dtype=np.int32),
        "resources": np.array([game_state.attacker_resources["exploit_kits"]], dtype=np.float32),
        "last_alert_location": game_state.last_alert_location,
        "last_alert_time": game_state.last_alert_time,
    }


def get_defender_observation(game_state: GameState) -> Dict[str, Any]:
    """
    Get defender's partial observation.
    Defender sees full topology but only detected compromises.
    Defender sees alert level.
    """
    return {
        "network_topology": game_state.full_topology.copy(),
        "compromised_nodes": game_state.defender_detected_compromises.copy(),
        "vulnerabilities": game_state.discovered_vulns.copy(),
        "alert_level": np.array([game_state.alert_level], dtype=np.float32),
        "turn_number": np.array([game_state.turn], dtype=np.int32),
        "resources": np.array([game_state.defender_resources["ir_budget"]], dtype=np.float32),
        "patched_nodes": game_state.patched_nodes.copy(),
        "isolated_nodes": game_state.isolated_nodes.copy(),
    }


def observation_to_vector(observation: Dict[str, Any]) -> np.ndarray:
    """
    Convert observation dict to flat vector for neural network input.
    """
    vectors = []
    
    # Flatten network topology
    if "network_topology" in observation:
        vectors.append(observation["network_topology"].flatten())
    
    # Flatten compromised nodes
    if "compromised_nodes" in observation:
        vectors.append(observation["compromised_nodes"].flatten())
    
    # Flatten vulnerabilities
    if "vulnerabilities" in observation:
        vectors.append(observation["vulnerabilities"].flatten())
    
    # Add scalar features
    if "alert_level" in observation:
        vectors.append(observation["alert_level"])
    
    if "turn_number" in observation:
        vectors.append(observation["turn_number"])
    
    if "resources" in observation:
        vectors.append(observation["resources"])
    
    # Flatten patched/isolated nodes if present
    if "patched_nodes" in observation:
        vectors.append(observation["patched_nodes"].flatten())
    
    if "isolated_nodes" in observation:
        vectors.append(observation["isolated_nodes"].flatten())
    
    return np.concatenate(vectors).astype(np.float32)


def get_observation_space_size(num_nodes: int, role: str = "attacker") -> int:
    """
    Calculate the size of the flattened observation vector.
    """
    # Network topology: num_nodes x num_nodes
    topology_size = num_nodes * num_nodes
    
    # Compromised nodes: num_nodes
    compromised_size = num_nodes
    
    # Vulnerabilities: num_nodes
    vulnerabilities_size = num_nodes
    
    # Alert level, turn number, resources: 3 scalars
    scalar_size = 3
    
    base_size = topology_size + compromised_size + vulnerabilities_size + scalar_size
    
    if role == "defender":
        # Add patched and isolated nodes for defender
        base_size += num_nodes * 2
    
    return base_size
