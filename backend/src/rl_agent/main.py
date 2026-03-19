"""
RL Agent microservice for Neo-Hack v3.1.
FastAPI service that serves RL agent decisions.

Blueprint Alignment: Section 3.1 (Architecture) - Separate Cloud Run microservice.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.rl.train_agents import RandomAgent, RuleBasedAttacker, RuleBasedDefender
from src.rl.action_space import (
    ATTACKER_ACTIONS, DEFENDER_ACTIONS,
    ACTION_DESCRIPTIONS, BASE_SUCCESS_RATES,
    get_attacker_action_name, get_defender_action_name,
)
from src.rl.scenarios.scenario_loader import list_scenarios, load_scenario

logger = logging.getLogger(__name__)

# In-memory agent registry (rule-based for now, SB3 models loaded when available)
AGENTS: Dict[str, Any] = {}


def _load_agents() -> Dict[str, Any]:
    """Load all available agents into memory."""
    agents = {}

    # Rule-based agents as fallback (always available)
    agents["attacker_novice"] = RandomAgent(action_space_n=8)
    agents["attacker_normal"] = RuleBasedAttacker()
    agents["attacker_expert"] = RuleBasedAttacker()
    agents["defender_novice"] = RandomAgent(action_space_n=7)
    agents["defender_normal"] = RuleBasedDefender()
    agents["defender_expert"] = RuleBasedDefender()

    # TODO: Load SB3 models when trained .zip files are available
    # from stable_baselines3 import PPO
    # for difficulty in ("novice", "normal", "expert"):
    #     for role in ("attacker", "defender"):
    #         path = f"models/{role}_{difficulty}.zip"
    #         if Path(path).exists():
    #             agents[f"{role}_{difficulty}"] = PPO.load(path)

    logger.info(f"Loaded {len(agents)} agents")
    return agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup."""
    global AGENTS
    AGENTS = _load_agents()
    yield
    AGENTS.clear()


app = FastAPI(
    title="Neo-Hack RL Agent Service",
    description="RL agent decision service for Neo-Hack v3.1 turn-based cyber warfare",
    version="3.1.0",
    lifespan=lifespan,
)


# --- Request / Response models ---

class AIDecisionRequest(BaseModel):
    """Request body for /ai/decide endpoint."""
    role: str = Field(..., description="Agent role: 'attacker' or 'defender'")
    difficulty: str = Field("normal", description="Difficulty: 'novice', 'normal', or 'expert'")
    observation: List[float] = Field(..., description="Flattened observation vector")
    game_id: Optional[str] = Field(None, description="Game session ID for context")


class AIDecisionResponse(BaseModel):
    """Response body for /ai/decide endpoint."""
    action: int = Field(..., description="Action ID")
    action_name: str = Field(..., description="Human-readable action name")
    confidence: float = Field(..., description="Agent confidence (0-1)")
    description: str = Field("", description="Action description")
    success_rate: Optional[float] = Field(None, description="Base success rate")


class AvailableActionsRequest(BaseModel):
    """Request body for /ai/actions endpoint."""
    role: str = Field(..., description="Agent role: 'attacker' or 'defender'")


class GameScenarioResponse(BaseModel):
    """Response for scenario listing."""
    id: str
    name: str
    description: str
    difficulty: str
    num_nodes: int


# --- Endpoints ---

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_loaded": len(AGENTS),
        "version": "3.1.0",
    }


@app.post("/ai/decide", response_model=AIDecisionResponse)
async def get_ai_decision(request: AIDecisionRequest):
    """
    Get RL agent's action decision.

    The agent selects an action based on the current game observation.
    Uses the specified role and difficulty to select the appropriate model.
    """
    # Validate role
    if request.role not in ("attacker", "defender"):
        raise HTTPException(400, f"Invalid role: {request.role}. Must be 'attacker' or 'defender'")

    # Validate difficulty
    if request.difficulty not in ("novice", "normal", "expert"):
        raise HTTPException(400, f"Invalid difficulty: {request.difficulty}")

    # Look up agent
    model_key = f"{request.role}_{request.difficulty}"
    agent = AGENTS.get(model_key)
    if agent is None:
        raise HTTPException(404, f"Agent '{model_key}' not loaded")

    # Convert observation
    obs = np.array(request.observation, dtype=np.float32)

    # Get action
    action, _ = agent.predict(obs, deterministic=False)
    action = int(action)

    # Build response
    if request.role == "attacker":
        action_name = get_attacker_action_name(action)
        success_rate = BASE_SUCCESS_RATES.get(action_name)
    else:
        action_name = get_defender_action_name(action)
        success_rate = None

    description = ACTION_DESCRIPTIONS.get(action_name, "")

    return AIDecisionResponse(
        action=action,
        action_name=action_name,
        confidence=0.85,  # Placeholder until model confidence extraction
        description=description,
        success_rate=success_rate,
    )


@app.post("/ai/actions")
async def get_available_actions(request: AvailableActionsRequest):
    """
    Get list of available actions for a role.
    """
    if request.role == "attacker":
        actions = [
            {"id": k, "name": v, "description": ACTION_DESCRIPTIONS.get(v, "")}
            for k, v in ATTACKER_ACTIONS.items()
        ]
    elif request.role == "defender":
        actions = [
            {"id": k, "name": v, "description": ACTION_DESCRIPTIONS.get(v, "")}
            for k, v in DEFENDER_ACTIONS.items()
        ]
    else:
        raise HTTPException(400, f"Invalid role: {request.role}")

    return {"role": request.role, "actions": actions}


@app.get("/scenarios", response_model=List[GameScenarioResponse])
async def get_scenarios():
    """List all available game scenarios."""
    return list_scenarios()


@app.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a specific scenario by ID."""
    try:
        return load_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# Include game session routes
from src.rl_agent.routes import router as game_router
app.include_router(game_router)
