"""
Game session API routes for Neo-Hack v3.1.
REST endpoints for creating and managing turn-based game sessions.
"""

from fastapi import APIRouter, HTTPException

from .game_session import (
    SessionManager,
    CreateSessionRequest,
    CreateSessionResponse,
    SubmitActionRequest,
    SubmitActionResponse,
    SessionStateResponse,
)

router = APIRouter(prefix="/game", tags=["game"])

# Shared session manager
session_manager = SessionManager()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new game session."""
    try:
        session = session_manager.create_session(
            scenario_id=request.scenario_id,
            attacker_type=request.attacker_type,
            defender_type=request.defender_type,
            ai_difficulty=request.ai_difficulty,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return CreateSessionResponse(
        session_id=session.session_id,
        scenario=session.scenario,
        attacker_type=session.attacker_type,
        defender_type=session.defender_type,
        current_player=session.turn_manager.current_player,
        turn=session.turn_manager.current_turn,
    )


@router.get("/sessions")
async def list_sessions():
    """List all active game sessions."""
    return session_manager.list_sessions()


@router.get("/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """Get current state of a game session."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return session.get_state()


@router.post("/sessions/{session_id}/action", response_model=SubmitActionResponse)
async def submit_action(session_id: str, request: SubmitActionRequest):
    """Submit an action in a game session."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(404, f"Session '{session_id}' not found")

    if session.turn_manager.game_over:
        raise HTTPException(400, "Game is already over")

    if request.player != session.turn_manager.current_player:
        raise HTTPException(
            400,
            f"It's {session.turn_manager.current_player}'s turn, not {request.player}'s",
        )

    try:
        result = session.submit_action(request.player, request.action)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))

    from src.rl.action_space import get_attacker_action_name, get_defender_action_name

    if request.player == "attacker":
        action_name = get_attacker_action_name(request.action)
    else:
        action_name = get_defender_action_name(request.action)

    return SubmitActionResponse(
        success=result["success"],
        action_name=action_name,
        action_result=result["action_result"],
        turn_switched=result["turn_switched"],
        current_player=result["current_player"],
        turn=result["turn"],
        game_over=result["game_over"],
        winner=result["winner"],
        alert_level=result["alert_level"],
        attacker_nodes=result["attacker_nodes"],
        observation=result["observation"],
    )


@router.get("/sessions/{session_id}/observation/{player}")
async def get_observation(session_id: str, player: str):
    """Get the current observation for a player."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(404, f"Session '{session_id}' not found")

    if player not in ("attacker", "defender"):
        raise HTTPException(400, f"Invalid player: {player}")

    return {"player": player, "observation": session.get_observation(player)}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a game session."""
    if session_manager.delete_session(session_id):
        return {"deleted": True, "session_id": session_id}
    raise HTTPException(404, f"Session '{session_id}' not found")
