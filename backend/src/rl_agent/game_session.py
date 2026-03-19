"""
Game session management for Neo-Hack v3.1.
Manages active game sessions with turn-based play via API.
"""

import uuid
import time
from typing import Dict, Any, Optional, List

import numpy as np
from pydantic import BaseModel, Field

from src.rl.observation_space import GameState, get_attacker_observation, get_defender_observation, observation_to_vector
from src.rl.neohack_env import NeoHackEnv
from src.rl.scenarios.scenario_loader import load_scenario
from src.game.turn_manager import TurnManager
from src.game.detection_engine import StealthAlertSystem
from src.game.resources import ResourceManager
from src.game.victory_conditions import ScenarioObjectives, GameEndConditions


# --- Pydantic models ---

class CreateSessionRequest(BaseModel):
    scenario_id: str = Field("corporate_network", description="Scenario ID to use")
    attacker_type: str = Field("human", description="'human' or 'ai'")
    defender_type: str = Field("ai", description="'human' or 'ai'")
    ai_difficulty: str = Field("normal", description="AI difficulty level")


class CreateSessionResponse(BaseModel):
    session_id: str
    scenario: Dict[str, Any]
    attacker_type: str
    defender_type: str
    current_player: str
    turn: int


class SubmitActionRequest(BaseModel):
    session_id: str
    player: str
    action: int
    target_node: Optional[int] = None


class SubmitActionResponse(BaseModel):
    success: bool
    action_name: str
    action_result: Dict[str, Any]
    turn_switched: bool
    current_player: str
    turn: int
    game_over: bool
    winner: Optional[str] = None
    alert_level: int
    attacker_nodes: int
    observation: List[float]


class SessionStateResponse(BaseModel):
    session_id: str
    turn: int
    current_player: str
    alert_level: int
    attacker_nodes: int
    total_nodes: int
    game_over: bool
    winner: Optional[str] = None
    attacker_resources: Dict[str, int]
    defender_resources: Dict[str, int]
    objectives: Dict[str, Any]


# --- Session store ---

def _sanitize_numpy(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_numpy(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


class GameSession:
    """Represents an active game session."""

    def __init__(
        self,
        session_id: str,
        scenario: Dict[str, Any],
        attacker_type: str,
        defender_type: str,
        ai_difficulty: str,
    ):
        self.session_id = session_id
        self.scenario = scenario
        self.attacker_type = attacker_type
        self.defender_type = defender_type
        self.ai_difficulty = ai_difficulty
        self.created_at = time.time()

        num_nodes = scenario.get("num_nodes", 10)
        max_turns = scenario.get("max_turns", 50)

        # Core components
        self.attacker_env = NeoHackEnv(role="attacker", scenario=scenario, num_nodes=num_nodes, max_turns=max_turns)
        self.defender_env = NeoHackEnv(role="defender", scenario=scenario, num_nodes=num_nodes, max_turns=max_turns)
        self.turn_manager = TurnManager(scenario=scenario)
        self.stealth_system = StealthAlertSystem()
        self.resources = ResourceManager(scenario=scenario)
        self.objectives = ScenarioObjectives(scenario=scenario)
        self.end_conditions = GameEndConditions(max_turns=max_turns)

        # Initialize envs
        self.attacker_env.reset()
        self.defender_env.reset()
        self.defender_env.game_state = self.attacker_env.game_state
        self.turn_manager.start_game()

    @property
    def game_state(self) -> GameState:
        return self.attacker_env.game_state

    def submit_action(self, player: str, action: int) -> Dict[str, Any]:
        """Process a player action and return result."""
        # Execute in the right env
        if player == "attacker":
            obs, reward, terminated, truncated, info = self.attacker_env.step(action)
            self.defender_env.game_state = self.attacker_env.game_state
        else:
            obs, reward, terminated, truncated, info = self.defender_env.step(action)
            self.attacker_env.game_state = self.defender_env.game_state

        # Process turn
        action_result = info.get("last_result", {}) or {}
        turn_switched, turn_state = self.turn_manager.process_action(player, action, action_result)

        # Check game end
        end_check = self.end_conditions.check_game_end(
            self.game_state, self.turn_manager.current_turn, self.objectives
        )

        if end_check["game_over"] or terminated or truncated:
            self.turn_manager.end_game(winner=end_check.get("winner"))

        return {
            "success": action_result.get("success", False) if action_result else False,
            "action_result": action_result or {},
            "reward": float(reward),
            "turn_switched": turn_switched,
            "current_player": self.turn_manager.current_player,
            "turn": self.turn_manager.current_turn,
            "game_over": self.turn_manager.game_over,
            "winner": self.turn_manager.winner,
            "alert_level": self.game_state.alert_level,
            "attacker_nodes": int(np.sum(self.game_state.attacker_owned_nodes)),
            "observation": obs.tolist(),
        }

    def get_state(self) -> Dict[str, Any]:
        """Get full session state."""
        objectives = _sanitize_numpy(self.objectives.get_objectives_status(self.game_state))
        return {
            "session_id": self.session_id,
            "turn": int(self.turn_manager.current_turn),
            "current_player": self.turn_manager.current_player,
            "alert_level": int(self.game_state.alert_level),
            "attacker_nodes": int(np.sum(self.game_state.attacker_owned_nodes)),
            "total_nodes": int(self.game_state.num_nodes),
            "game_over": bool(self.turn_manager.game_over),
            "winner": self.turn_manager.winner,
            "attacker_resources": self.resources.get_attacker_resources(),
            "defender_resources": self.resources.get_defender_resources(),
            "objectives": objectives,
        }

    def get_observation(self, player: str) -> List[float]:
        """Get observation vector for a player."""
        if player == "attacker":
            obs_dict = get_attacker_observation(self.game_state)
        else:
            obs_dict = get_defender_observation(self.game_state)
        return observation_to_vector(obs_dict).tolist()


class SessionManager:
    """Manages all active game sessions."""

    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}

    def create_session(
        self,
        scenario_id: str,
        attacker_type: str = "human",
        defender_type: str = "ai",
        ai_difficulty: str = "normal",
    ) -> GameSession:
        session_id = str(uuid.uuid4())[:8]
        scenario = load_scenario(scenario_id)
        session = GameSession(
            session_id=session_id,
            scenario=scenario,
            attacker_type=attacker_type,
            defender_type=defender_type,
            ai_difficulty=ai_difficulty,
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[GameSession]:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "scenario": s.scenario.get("name", ""),
                "turn": s.turn_manager.current_turn,
                "game_over": s.turn_manager.game_over,
            }
            for s in self.sessions.values()
        ]
