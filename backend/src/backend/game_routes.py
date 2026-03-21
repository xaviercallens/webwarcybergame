"""
v3.2 Turn-based game session routes.
Bridges the frontend's /game/* endpoints to the RL agent's SessionManager
and rule-based pretrained agents.
"""

import logging
import random
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rl.neohack_env import NeoHackEnv
from rl.action_space import (
    ATTACKER_ACTIONS, DEFENDER_ACTIONS,
    ACTION_DESCRIPTIONS, BASE_SUCCESS_RATES, STEALTH_COSTS,
    get_attacker_action_name, get_defender_action_name,
)
from rl.observation_space import get_attacker_observation, get_defender_observation, observation_to_vector
from rl.scenarios.scenario_loader import load_scenario, list_scenarios
from rl.train_agents import RuleBasedAttacker, RuleBasedDefender, RandomAgent
from game.turn_manager import TurnManager
from game.detection_engine import StealthAlertSystem
from game.resources import ResourceManager
from game.victory_conditions import ScenarioObjectives, GameEndConditions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game", tags=["game-v32"])

# ── In-memory stores ──────────────────────────────────────────────

_sessions: Dict[str, "LiveSession"] = {}

_agents: Dict[str, Any] = {
    "attacker_novice": None,
    "attacker_normal": None,
    "attacker_expert": None,
    "defender_novice": None,
    "defender_normal": None,
    "defender_expert": None,
}


def _get_agent(role: str, difficulty: str):
    key = f"{role}_{difficulty}"
    if _agents.get(key) is None:
        # Try loading a trained PPO model first
        from pathlib import Path
        model_path = Path(__file__).parent.parent / "rl" / "models" / difficulty / f"ppo_{role}_latest.zip"
        if model_path.exists():
            try:
                from stable_baselines3 import PPO
                ppo = PPO.load(str(model_path.with_suffix('')), device="cpu")
                class PPOAgent:
                    def __init__(self, model):
                        self.model = model
                    def predict(self, obs, deterministic=False):
                        action, state = self.model.predict(obs, deterministic=deterministic)
                        return int(action), state
                _agents[key] = PPOAgent(ppo)
                logger.info(f"Loaded trained PPO model for {role}/{difficulty}: {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load PPO model {model_path}: {e}")
                _agents[key] = None

        if _agents.get(key) is None:
            # Fallback to rule-based agents
            if difficulty == "novice":
                n = 8 if role == "attacker" else 7
                _agents[key] = RandomAgent(action_space_n=n)
            else:
                _agents[key] = RuleBasedAttacker() if role == "attacker" else RuleBasedDefender()
            logger.info(f"Using rule-based agent for {role}/{difficulty}")
    return _agents[key]


# ── Pydantic DTOs ─────────────────────────────────────────────────

class CreateGameReq(BaseModel):
    role: str  # human's role
    difficulty: str = "normal"
    scenario: str = "corporate_network"


class ActionReq(BaseModel):
    session_id: str
    player_role: str
    action_type: str  # action name e.g. "SCAN_NETWORK"
    action_id: int
    target_node: Optional[int] = None


class EndTurnReq(BaseModel):
    session_id: str
    player_role: str


# ── Session wrapper ───────────────────────────────────────────────

class LiveSession:
    """Wraps the RL env pair + turn manager for one live game."""

    def __init__(self, session_id: str, scenario: dict, human_role: str, difficulty: str):
        self.session_id = session_id
        self.scenario = scenario
        self.human_role = human_role
        self.ai_role = "defender" if human_role == "attacker" else "attacker"
        self.difficulty = difficulty

        num_nodes = scenario.get("num_nodes", 10)
        max_turns = scenario.get("max_turns", 50)

        self.att_env = NeoHackEnv(role="attacker", scenario=scenario, num_nodes=num_nodes, max_turns=max_turns)
        self.def_env = NeoHackEnv(role="defender", scenario=scenario, num_nodes=num_nodes, max_turns=max_turns)
        self.turn_mgr = TurnManager(scenario=scenario)
        self.stealth = StealthAlertSystem()
        self.resources = ResourceManager(scenario=scenario)
        self.objectives = ScenarioObjectives(scenario=scenario)
        self.end_cond = GameEndConditions(max_turns=max_turns)

        self.att_env.reset()
        self.def_env.reset()
        self.def_env.game_state = self.att_env.game_state
        self.turn_mgr.start_game()

        self.ai_agent = _get_agent(self.ai_role, difficulty)

    @property
    def gs(self):
        return self.att_env.game_state

    # ── helpers ────────────────────────────────────────────
    def _obs_for(self, role):
        if role == "attacker":
            return get_attacker_observation(self.gs)
        return get_defender_observation(self.gs)

    def _action_name(self, role, action_id):
        if role == "attacker":
            return get_attacker_action_name(action_id)
        return get_defender_action_name(action_id)

    def _step(self, role, action_id):
        if role == "attacker":
            obs, rew, term, trunc, info = self.att_env.step(action_id)
            self.def_env.game_state = self.att_env.game_state
        else:
            obs, rew, term, trunc, info = self.def_env.step(action_id)
            self.att_env.game_state = self.def_env.game_state

        action_result = info.get("last_result", {}) or {}
        turn_switched, _ = self.turn_mgr.process_action(role, action_id, action_result)

        end = self.end_cond.check_game_end(self.gs, self.turn_mgr.current_turn, self.objectives)
        if end["game_over"] or term or trunc:
            self.turn_mgr.end_game(winner=end.get("winner"))

        return {
            "success": bool(action_result.get("success", False)),
            "detected": bool(action_result.get("detected", False)),
            "message": action_result.get("message", f"{self._action_name(role, action_id)} executed"),
            "details": _sanitize(action_result),
            "turn_switched": turn_switched,
            "game_over": self.turn_mgr.game_over,
            "winner": self.turn_mgr.winner,
        }

    def run_ai_turn(self):
        """Let the AI take its turn until the turn switches or game ends."""
        results = []
        safety = 0
        while (
            self.turn_mgr.current_player == self.ai_role
            and not self.turn_mgr.game_over
            and safety < 10
        ):
            obs_dict = self._obs_for(self.ai_role)
            obs_vec = observation_to_vector(obs_dict)
            action_id, _ = self.ai_agent.predict(obs_vec, deterministic=False)
            action_id = int(action_id)
            res = self._step(self.ai_role, action_id)
            res["action_name"] = self._action_name(self.ai_role, action_id)
            results.append(res)
            safety += 1

            if res["turn_switched"] or res["game_over"]:
                break

        return results

    def snapshot(self) -> dict:
        """Build the game_state dict the frontend expects."""
        gs = self.gs
        compromised = []
        discovered = []
        detected = []

        for i in range(gs.num_nodes):
            if gs.attacker_owned_nodes[i]:
                compromised.append(i)
            if gs.attacker_scanned_vulns[i]:
                discovered.append(i)
            if gs.defender_detected_compromises[i]:
                detected.append(i)

        nodes = []
        for i in range(gs.num_nodes):
            nodes.append({
                "id": i,
                "name": f"NODE-{i:02d}",
                "owned_by": "attacker" if gs.attacker_owned_nodes[i] else "defender",
                "defense_level": int(gs.vulnerabilities[i]),
                "discovered": bool(gs.attacker_scanned_vulns[i]),
                "detected": bool(gs.defender_detected_compromises[i]),
                "patched": bool(gs.patched_nodes[i]),
                "isolated": bool(gs.isolated_nodes[i]),
            })

        connections = []
        adj = gs.full_topology
        for i in range(gs.num_nodes):
            for j in range(i + 1, gs.num_nodes):
                if adj[i][j]:
                    connections.append({"source": i, "target": j})

        # Stealth: 100 - alert_level as a proxy
        stealth = max(0, 100 - int(gs.alert_level))

        return {
            "current_turn": int(self.turn_mgr.current_turn),
            "max_turns": int(self.scenario.get("max_turns", 50)),
            "current_player": self.turn_mgr.current_player,
            "action_points_remaining": int(self.turn_mgr.actions_left),
            "alert_level": int(gs.alert_level),
            "stealth_level": stealth,
            "nodes": nodes,
            "connections": connections,
            "discovered_nodes": discovered,
            "compromised_nodes": compromised,
            "detected_nodes": detected,
            "resources": {
                "attacker": _sanitize(self.resources.get_attacker_resources()),
                "defender": _sanitize(self.resources.get_defender_resources()),
            },
            "objectives": _sanitize(self.objectives.get_objectives_status(gs)),
            "game_over": bool(self.turn_mgr.game_over),
            "winner": self.turn_mgr.winner,
        }


def _sanitize(obj):
    """Convert numpy types to native Python."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


# ── Routes ────────────────────────────────────────────────────────

@router.post("/create")
async def create_game(req: CreateGameReq):
    """Create a new turn-based game session using rule-based AI agents."""
    scenario_id = req.scenario
    if scenario_id in ("default", "sandbox"):
        scenario_id = "corporate_network"

    try:
        scenario = load_scenario(scenario_id)
    except ValueError:
        scenario = load_scenario("corporate_network")

    sid = f"gs-{random.randint(10000, 99999)}"
    session = LiveSession(sid, scenario, req.role, req.difficulty)
    _sessions[sid] = session

    # If AI moves first, run its turn
    if session.turn_mgr.current_player == session.ai_role:
        session.run_ai_turn()

    logger.info(f"[GAME] Created session {sid} | role={req.role} scenario={scenario_id} difficulty={req.difficulty}")

    return {
        "session_id": sid,
        "game_state": session.snapshot(),
    }


@router.post("/action")
async def submit_action(req: ActionReq):
    """Submit a human player action."""
    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.turn_mgr.game_over:
        raise HTTPException(400, "Game is already over")
    if session.turn_mgr.current_player != req.player_role:
        raise HTTPException(400, f"It's {session.turn_mgr.current_player}'s turn")

    result = session._step(req.player_role, req.action_id)

    # After human action, if turn switched to AI, run AI turn
    ai_actions = []
    if result["turn_switched"] and not result["game_over"]:
        if session.turn_mgr.current_player == session.ai_role:
            ai_actions = session.run_ai_turn()

    return {
        "success": result["success"],
        "detected": result["detected"],
        "message": result["message"],
        "details": result["details"],
        "ai_actions": ai_actions,
        "game_state": session.snapshot(),
    }


@router.post("/end-turn")
async def end_turn(req: EndTurnReq):
    """End turn — skip remaining AP. AI takes over."""
    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.turn_mgr.game_over:
        raise HTTPException(400, "Game already over")

    # Force turn switch
    session.turn_mgr.force_end_turn()

    # Run AI turn
    ai_actions = []
    if session.turn_mgr.current_player == session.ai_role and not session.turn_mgr.game_over:
        ai_actions = session.run_ai_turn()

    return {
        "ai_actions": ai_actions,
        "game_state": session.snapshot(),
    }


@router.get("/state/{session_id}")
async def get_state(session_id: str):
    """Get current game state for polling."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"game_state": session.snapshot()}


@router.get("/scenarios")
async def get_scenarios():
    """List available scenarios."""
    return {"scenarios": list_scenarios()}
