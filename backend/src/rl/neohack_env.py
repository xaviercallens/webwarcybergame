"""
Custom Gymnasium environment for Neo-Hack v3.1 game.
Implements turn-based gameplay with partial observability.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Any, Tuple, Optional
import random

from .action_space import (
    AttackerAction, DefenderAction, ATTACKER_ACTIONS, DEFENDER_ACTIONS,
    ACTION_COSTS, STEALTH_COSTS, BASE_SUCCESS_RATES, DETECTION_CHANCES,
    get_attacker_action_name, get_defender_action_name
)
from .observation_space import (
    GameState, get_attacker_observation, get_defender_observation,
    observation_to_vector, get_observation_space_size
)


class NeoHackEnv(gym.Env):
    """
    Custom Gymnasium environment for Neo-Hack turn-based game.
    Supports both attacker and defender perspectives with partial observability.
    
    Blueprint Alignment: Section 1 (Core Mechanics) + Section 3.1 (Architecture)
    """
    
    metadata = {"render_modes": ["human"], "render_fps": 1}
    
    def __init__(
        self,
        role: str = "attacker",
        scenario: Optional[Dict[str, Any]] = None,
        num_nodes: int = 10,
        max_turns: int = 50,
        seed: Optional[int] = None
    ):
        """
        Initialize the Neo-Hack environment.
        
        Args:
            role: "attacker" or "defender"
            scenario: Optional scenario configuration dict
            num_nodes: Number of network nodes
            max_turns: Maximum turns per game
            seed: Random seed for reproducibility
        """
        super().__init__()
        
        self.role = role
        self.num_nodes = num_nodes
        self.max_turns = max_turns
        self.scenario = scenario or {}
        
        # Set random seed
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        # Game state
        self.game_state = GameState(num_nodes=num_nodes, max_turns=max_turns)
        self.current_turn = 0
        self.game_over = False
        self.winner = None
        
        # Define observation space
        obs_size = get_observation_space_size(num_nodes, role)
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(obs_size,),
            dtype=np.float32
        )
        
        # Define action space
        if role == "attacker":
            self.action_space = spaces.Discrete(8)  # 8 attacker actions
            self.valid_actions = list(ATTACKER_ACTIONS.keys())
        else:
            self.action_space = spaces.Discrete(7)  # 7 defender actions
            self.valid_actions = list(DEFENDER_ACTIONS.keys())
        
        # Tracking
        self.action_history = []
        self.reward_history = []
        self.last_action = None
        self.last_result = None
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to initial state.
        
        Returns:
            observation: Initial observation vector
            info: Additional information dict
        """
        super().reset(seed=seed)
        
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        # Reset game state
        self.game_state = GameState(num_nodes=self.num_nodes, max_turns=self.max_turns)
        self.current_turn = 0
        self.game_over = False
        self.winner = None
        self.action_history = []
        self.reward_history = []
        self.last_action = None
        self.last_result = None
        
        # Initialize network topology
        self._initialize_network()
        
        # Get initial observation
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action ID (0-7 for attacker, 0-6 for defender)
        
        Returns:
            observation: New observation after action
            reward: Reward for this step
            terminated: Whether episode is done
            truncated: Whether episode was truncated
            info: Additional information
        """
        if self.game_over:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")
        
        # Validate action
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action: {action}")
        
        # Execute action
        action_result = self._execute_action(action)
        self.last_action = action
        self.last_result = action_result
        
        # Calculate reward
        reward = self._calculate_reward(action, action_result)
        self.reward_history.append(reward)
        
        # Check win/loss conditions
        terminated = self._check_game_over()
        
        # Increment turn
        self.current_turn += 1
        truncated = self.current_turn >= self.max_turns
        
        if terminated or truncated:
            self.game_over = True
        
        # Get new observation
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _initialize_network(self) -> None:
        """Initialize network topology and vulnerabilities."""
        # Create random network topology
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if i != j and random.random() < 0.3:
                    self.game_state.full_topology[i, j] = 1
        
        # Ensure connectivity
        for i in range(self.num_nodes - 1):
            self.game_state.full_topology[i, i + 1] = 1
            self.game_state.full_topology[i + 1, i] = 1
        
        # Initialize vulnerabilities (0-2 per node)
        self.game_state.vulnerabilities = np.random.randint(0, 3, size=self.num_nodes, dtype=np.int32)
        
        # Attacker starts with no knowledge
        self.game_state.attacker_discovered_topology = np.zeros_like(self.game_state.full_topology)
        self.game_state.attacker_owned_nodes = np.zeros(self.num_nodes, dtype=np.int32)
        
        # Defender sees full topology but no compromises initially
        self.game_state.defender_detected_compromises = np.zeros(self.num_nodes, dtype=np.int32)
    
    def _execute_action(self, action: int) -> Dict[str, Any]:
        """Execute an action and return result."""
        if self.role == "attacker":
            return self._execute_attacker_action(action)
        else:
            return self._execute_defender_action(action)
    
    def _execute_attacker_action(self, action: int) -> Dict[str, Any]:
        """Execute attacker action with probabilistic outcome."""
        action_name = get_attacker_action_name(action)
        result = {
            "action": action_name,
            "success": False,
            "detected": False,
            "reward": 0,
            "details": {}
        }
        
        if action == AttackerAction.SCAN_NETWORK:
            # Discover adjacent nodes
            discovered_count = 0
            for i in range(self.num_nodes):
                if self.game_state.attacker_owned_nodes[i]:
                    # Discover neighbors
                    for j in range(self.num_nodes):
                        if self.game_state.full_topology[i, j]:
                            self.game_state.attacker_discovered_topology[i, j] = 1
                            discovered_count += 1
            
            result["success"] = discovered_count > 0
            result["details"]["discovered_nodes"] = discovered_count
            
        elif action == AttackerAction.EXPLOIT_VULNERABILITY:
            # Try to compromise a random discovered node
            discovered_nodes = np.where(
                (self.game_state.attacker_discovered_topology.sum(axis=0) > 0) &
                (self.game_state.attacker_owned_nodes == 0)
            )[0]
            
            if len(discovered_nodes) > 0:
                target = np.random.choice(discovered_nodes)
                success_rate = BASE_SUCCESS_RATES.get("EXPLOIT_VULNERABILITY", 0.7)
                
                # Adjust for patches
                if self.game_state.patched_nodes[target]:
                    success_rate *= 0.3
                
                if random.random() < success_rate:
                    self.game_state.attacker_owned_nodes[target] = 1
                    result["success"] = True
                    result["details"]["target"] = int(target)
                    result["reward"] = 10
                
                # Check detection
                detection_chance = DETECTION_CHANCES.get("EXPLOIT_VULNERABILITY", 0.4)
                if random.random() < detection_chance:
                    result["detected"] = True
                    self.game_state.alert_level = min(100, self.game_state.alert_level + 30)
        
        elif action == AttackerAction.LATERAL_MOVEMENT:
            # Move from one owned node to adjacent node
            owned_nodes = np.where(self.game_state.attacker_owned_nodes)[0]
            if len(owned_nodes) > 0:
                source = np.random.choice(owned_nodes)
                neighbors = np.where(self.game_state.full_topology[source])[0]
                unowned_neighbors = neighbors[self.game_state.attacker_owned_nodes[neighbors] == 0]
                
                if len(unowned_neighbors) > 0:
                    target = np.random.choice(unowned_neighbors)
                    if random.random() < 0.8:
                        self.game_state.attacker_owned_nodes[target] = 1
                        result["success"] = True
                        result["details"]["target"] = int(target)
                    
                    if random.random() < 0.45:
                        result["detected"] = True
                        self.game_state.alert_level = min(100, self.game_state.alert_level + 40)
        
        elif action == AttackerAction.EXFILTRATE_DATA:
            # Steal data from owned nodes
            owned_nodes = np.where(self.game_state.attacker_owned_nodes)[0]
            if len(owned_nodes) > 0:
                data_stolen = len(owned_nodes) * 5
                result["success"] = True
                result["details"]["data_stolen"] = data_stolen
                result["reward"] = data_stolen
                
                if random.random() < 0.6:
                    result["detected"] = True
                    self.game_state.alert_level = min(100, self.game_state.alert_level + 50)
        
        # Update alert level based on stealth cost
        if not result["detected"]:
            stealth_cost = STEALTH_COSTS.get(action_name, 20)
            self.game_state.alert_level = min(100, self.game_state.alert_level + stealth_cost)
        
        return result
    
    def _execute_defender_action(self, action: int) -> Dict[str, Any]:
        """Execute defender action."""
        action_name = get_defender_action_name(action)
        result = {
            "action": action_name,
            "success": False,
            "reward": 0,
            "details": {}
        }
        
        if action == DefenderAction.MONITOR_LOGS:
            # Detect compromised nodes based on alert level
            if self.game_state.alert_level > 30:
                detected = np.where(self.game_state.attacker_owned_nodes)[0]
                self.game_state.defender_detected_compromises[detected] = 1
                result["success"] = len(detected) > 0
                result["details"]["detected_nodes"] = len(detected)
                result["reward"] = len(detected) * 5
        
        elif action == DefenderAction.APPLY_PATCH:
            # Patch a random vulnerable node
            vulnerable_nodes = np.where(self.game_state.vulnerabilities > 0)[0]
            if len(vulnerable_nodes) > 0:
                target = np.random.choice(vulnerable_nodes)
                self.game_state.patched_nodes[target] = 1
                self.game_state.vulnerabilities[target] = 0
                result["success"] = True
                result["details"]["patched_node"] = int(target)
                result["reward"] = 3
        
        elif action == DefenderAction.ISOLATE_HOST:
            # Isolate a compromised node
            compromised = np.where(self.game_state.attacker_owned_nodes)[0]
            if len(compromised) > 0:
                target = np.random.choice(compromised)
                self.game_state.isolated_nodes[target] = 1
                self.game_state.full_topology[target, :] = 0
                self.game_state.full_topology[:, target] = 0
                result["success"] = True
                result["details"]["isolated_node"] = int(target)
                result["reward"] = 10
        
        elif action == DefenderAction.INCIDENT_RESPONSE:
            # Active response - remove malware from random node
            compromised = np.where(self.game_state.attacker_owned_nodes)[0]
            if len(compromised) > 0:
                target = np.random.choice(compromised)
                self.game_state.attacker_owned_nodes[target] = 0
                result["success"] = True
                result["details"]["cleaned_node"] = int(target)
                result["reward"] = 15
        
        return result
    
    def _calculate_reward(self, action: int, result: Dict[str, Any]) -> float:
        """Calculate reward for action."""
        reward = result.get("reward", 0)
        
        # Penalty for detected actions
        if result.get("detected"):
            reward -= 5
        
        # Penalty for failed actions
        if not result.get("success"):
            reward -= 1
        
        return float(reward)
    
    def _check_game_over(self) -> bool:
        """Check if game is over (win/loss condition)."""
        owned_count = np.sum(self.game_state.attacker_owned_nodes)
        
        # Attacker wins if owns >50% of nodes
        if self.role == "attacker" and owned_count >= self.num_nodes * 0.5:
            self.winner = "attacker"
            return True
        
        # Defender wins if alert level too high (attacker caught)
        if self.game_state.alert_level >= 100:
            self.winner = "defender"
            return True
        
        return False
    
    def _get_observation(self) -> np.ndarray:
        """Get current observation for the agent."""
        if self.role == "attacker":
            obs_dict = get_attacker_observation(self.game_state)
        else:
            obs_dict = get_defender_observation(self.game_state)
        
        return observation_to_vector(obs_dict)
    
    def _get_info(self) -> Dict[str, Any]:
        """Get additional information about current state."""
        return {
            "turn": self.current_turn,
            "alert_level": self.game_state.alert_level,
            "attacker_nodes": int(np.sum(self.game_state.attacker_owned_nodes)),
            "total_nodes": self.num_nodes,
            "game_over": self.game_over,
            "winner": self.winner,
            "last_action": self.last_action,
            "last_result": self.last_result,
        }
    
    def render(self) -> None:
        """Render the environment (human-readable output)."""
        if self.render_mode == "human":
            print(f"\n=== Turn {self.current_turn} ===")
            print(f"Role: {self.role}")
            print(f"Alert Level: {self.game_state.alert_level}/100")
            print(f"Attacker Nodes: {int(np.sum(self.game_state.attacker_owned_nodes))}/{self.num_nodes}")
            print(f"Last Action: {self.last_action}")
            if self.last_result:
                print(f"Last Result: {self.last_result}")
    
    def close(self) -> None:
        """Close the environment."""
        pass
