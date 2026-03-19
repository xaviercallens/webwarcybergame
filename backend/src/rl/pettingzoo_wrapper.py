"""
PettingZoo multi-agent wrapper for Neo-Hack v3.1.
Implements 2-player alternating turn environment.
"""

from pettingzoo import AECEnv
from gymnasium import spaces
import numpy as np
from typing import Dict, Any, Optional, Tuple

from .neohack_env import NeoHackEnv


class NeoHackPettingZoo(AECEnv):
    """
    2-player alternating turn environment using PettingZoo.
    Wraps NeoHackEnv for multi-agent RL training.
    
    Blueprint Alignment: Section 1 (Core Mechanics) + Section 3.1 (Architecture)
    """
    
    metadata = {
        "name": "neohack_v3.1",
        "render_modes": ["human"],
        "render_fps": 1,
    }
    
    def __init__(
        self,
        scenario: Optional[Dict[str, Any]] = None,
        num_nodes: int = 10,
        max_turns: int = 50,
        seed: Optional[int] = None,
    ):
        """
        Initialize the PettingZoo environment.
        
        Args:
            scenario: Optional scenario configuration
            num_nodes: Number of network nodes
            max_turns: Maximum turns per game
            seed: Random seed
        """
        super().__init__()
        
        self.agents = ["attacker", "defender"]
        self.possible_agents = self.agents[:]
        self._agent_ids = {agent: i for i, agent in enumerate(self.agents)}
        
        # Create separate environments for each agent
        self.attacker_env = NeoHackEnv(
            role="attacker",
            scenario=scenario,
            num_nodes=num_nodes,
            max_turns=max_turns,
            seed=seed
        )
        self.defender_env = NeoHackEnv(
            role="defender",
            scenario=scenario,
            num_nodes=num_nodes,
            max_turns=max_turns,
            seed=seed
        )
        
        # Share game state between environments
        self.shared_game_state = self.attacker_env.game_state
        self.defender_env.game_state = self.shared_game_state
        
        # Track current agent
        self.agent_selection = "attacker"
        self._agent_index = 0
        self.current_turn = 0
        self.max_turns = max_turns
        
        # Observations and rewards
        self.observations = {}
        self.rewards = {agent: 0.0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}
        
        # Define action and observation spaces
        self.action_spaces = {
            "attacker": spaces.Discrete(8),
            "defender": spaces.Discrete(7),
        }
        
        self.observation_spaces = {
            "attacker": self.attacker_env.observation_space,
            "defender": self.defender_env.observation_space,
        }
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, Any]]]:
        """
        Reset the environment.
        
        Returns:
            observations: Dict of observations for each agent
            infos: Dict of info dicts for each agent
        """
        # Reset both environments
        attacker_obs, attacker_info = self.attacker_env.reset(seed=seed)
        defender_obs, defender_info = self.defender_env.reset(seed=seed)
        
        # Share game state
        self.shared_game_state = self.attacker_env.game_state
        self.defender_env.game_state = self.shared_game_state
        
        # Initialize tracking
        self.agent_selection = "attacker"
        self._agent_index = 0
        self.current_turn = 0
        
        self.observations = {
            "attacker": attacker_obs,
            "defender": defender_obs,
        }
        
        self.rewards = {agent: 0.0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {
            "attacker": attacker_info,
            "defender": defender_info,
        }
        
        return self.observations, self.infos
    
    def step(self, action: int) -> None:
        """
        Execute one step for the current agent.
        
        Args:
            action: Action ID for current agent
        """
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            raise RuntimeError(
                f"Agent {self.agent_selection} is done. Call reset() to start a new episode."
            )
        
        # Execute action in appropriate environment
        if self.agent_selection == "attacker":
            obs, reward, terminated, truncated, info = self.attacker_env.step(action)
            self.observations["attacker"] = obs
        else:
            obs, reward, terminated, truncated, info = self.defender_env.step(action)
            self.observations["defender"] = obs
        
        # Update state
        self.rewards[self.agent_selection] = reward
        self.terminations[self.agent_selection] = terminated
        self.truncations[self.agent_selection] = truncated
        self.infos[self.agent_selection] = info
        
        # Check if game is over
        if terminated or truncated:
            self.terminations[self.agent_selection] = True
            self.truncations[self.agent_selection] = truncated
        
        # Switch to next agent
        self._switch_agent()
        
        # Increment turn counter when both agents have played
        if self.agent_selection == "attacker":
            self.current_turn += 1
    
    def _switch_agent(self) -> None:
        """Switch to the next agent."""
        self._agent_index = (self._agent_index + 1) % len(self.agents)
        self.agent_selection = self.agents[self._agent_index]
    
    def observe(self, agent: str) -> np.ndarray:
        """
        Get observation for a specific agent.
        
        Args:
            agent: Agent name ("attacker" or "defender")
        
        Returns:
            Observation vector
        """
        return self.observations.get(agent, np.array([]))
    
    def render(self) -> None:
        """Render the environment."""
        print(f"\n=== Turn {self.current_turn} ===")
        print(f"Current Agent: {self.agent_selection}")
        print(f"Alert Level: {self.shared_game_state.alert_level}/100")
        print(f"Attacker Nodes: {int(np.sum(self.shared_game_state.attacker_owned_nodes))}")
        print(f"Rewards: {self.rewards}")
    
    def close(self) -> None:
        """Close the environment."""
        self.attacker_env.close()
        self.defender_env.close()
    
    def state(self) -> np.ndarray:
        """
        Get the full game state (for centralized training if needed).
        
        Returns:
            Flattened game state vector
        """
        state_components = [
            self.shared_game_state.full_topology.flatten(),
            self.shared_game_state.compromised_nodes,
            self.shared_game_state.patched_nodes,
            self.shared_game_state.isolated_nodes,
            self.shared_game_state.vulnerabilities,
            np.array([self.shared_game_state.alert_level]),
            np.array([self.current_turn]),
        ]
        return np.concatenate(state_components).astype(np.float32)


class AlternatingTurnWrapper:
    """
    Wrapper to enforce strict alternating turns between agents.
    Useful for ensuring proper turn order in training.
    """
    
    def __init__(self, env: NeoHackPettingZoo):
        """
        Initialize the wrapper.
        
        Args:
            env: NeoHackPettingZoo environment
        """
        self.env = env
        self.last_agent = None
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
        """Reset the environment."""
        self.last_agent = None
        return self.env.reset(seed=seed, options=options)
    
    def step(self, action: int) -> None:
        """
        Execute step with turn validation.
        
        Args:
            action: Action for current agent
        
        Raises:
            RuntimeError: If agent tries to play out of turn
        """
        current = self.env.agent_selection
        
        if self.last_agent is not None and self.last_agent == current:
            raise RuntimeError(
                f"Agent {current} tried to play twice in a row. "
                f"Last agent was {self.last_agent}."
            )
        
        self.last_agent = current
        self.env.step(action)
    
    def observe(self, agent: str) -> np.ndarray:
        """Get observation for agent."""
        return self.env.observe(agent)
    
    def render(self) -> None:
        """Render the environment."""
        self.env.render()
    
    def close(self) -> None:
        """Close the environment."""
        self.env.close()
    
    @property
    def agents(self):
        """Get list of agents."""
        return self.env.agents
    
    @property
    def agent_selection(self):
        """Get current agent."""
        return self.env.agent_selection
    
    @property
    def rewards(self):
        """Get rewards dict."""
        return self.env.rewards
    
    @property
    def terminations(self):
        """Get terminations dict."""
        return self.env.terminations
    
    @property
    def truncations(self):
        """Get truncations dict."""
        return self.env.truncations
    
    @property
    def infos(self):
        """Get infos dict."""
        return self.env.infos
