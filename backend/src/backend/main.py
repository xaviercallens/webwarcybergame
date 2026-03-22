import os
from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from sqlalchemy.orm import joinedload

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend import database, auth, models, engine
from backend.engine import epoch_loop
from backend.services.diplomacy import DiplomacyService
from backend.websocket import manager
from datetime import datetime

WEB_BUILD_DIR = Path(os.getenv("WEB_BUILD_DIR", Path(__file__).parent.parent.parent.parent / "build" / "web"))

diplomacy_svc = DiplomacyService(api_key=os.environ.get("GOOGLE_API_KEY"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    # Start the local game loop engine
    task = asyncio.create_task(epoch_loop())
    yield
    task.cancel()


app = FastAPI(
    title="Backend",
    description="Backend API",
    version="4.1.0",
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://neohack-gridlock-212120873430.europe-west1.run.app",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://frontend:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/auth/register", response_model=models.Token)
@limiter.limit("5/minute")
def register_user(request: Request, user_in: models.PlayerCreate, session: Session = Depends(database.get_session)):
    existing = session.exec(select(models.Player).where(models.Player.username == user_in.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = auth.get_password_hash(user_in.password)
    player = models.Player(username=user_in.username, hashed_password=hashed_password)
    session.add(player)
    session.commit()
    session.refresh(player)
    
    access_token = auth.create_access_token(data={"sub": player.username})
    return {"access_token": access_token, "token_type": "bearer", "player": player}

@app.post("/api/auth/login", response_model=models.Token)
@limiter.limit("5/minute")
def login_user(request: Request, user_in: models.PlayerCreate, session: Session = Depends(database.get_session)):
    player = session.exec(select(models.Player).where(models.Player.username == user_in.username)).first()
    if not player or not auth.verify_password(user_in.password, player.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    access_token = auth.create_access_token(data={"sub": player.username})
    return {"access_token": access_token, "token_type": "bearer", "player": player}

@app.get("/api/players/me", response_model=models.PlayerPublic)
def get_current_player(current_user: models.Player = Depends(auth.get_current_user)):
    return current_user

class GameOverStats(BaseModel):
    won: bool
    time_seconds: int
    nodes_captured: int
    nodes_lost: int
    attacks: int

@app.post("/api/players/me/game-over", response_model=models.PlayerPublic)
def submit_game_over(stats: GameOverStats, current_user: models.Player = Depends(auth.get_current_user), session: Session = Depends(database.get_session)):
    base_xp = 100 if stats.won else 50
    capture_bonus = stats.nodes_captured * 8
    speed_bonus = max(0, (480 - stats.time_seconds)) // 4
    streak_bonus = int(current_user.win_streak * 0.1 * base_xp)
    
    total_xp = base_xp + capture_bonus + speed_bonus + streak_bonus
    current_user.xp += total_xp
    
    if stats.won:
        current_user.wins += 1
        current_user.win_streak += 1
        if current_user.win_streak > current_user.best_streak:
            current_user.best_streak = current_user.win_streak
    else:
        current_user.losses += 1
        current_user.win_streak = 0
        
    xp = current_user.xp
    if xp >= 20000: rank = "GRID_SOVEREIGN"
    elif xp >= 12000: rank = "SHADOW_ADMIN"
    elif xp >= 7000: rank = "BLACK_HAT"
    elif xp >= 3500: rank = "ZERO_DAY"
    elif xp >= 1500: rank = "ROOT_ACCESS"
    elif xp >= 500: rank = "PACKET_SNIFFER"
    else: rank = "SCRIPT_KIDDIE"
    current_user.rank = rank
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@app.get("/api/leaderboard", response_model=dict)
def get_leaderboard(limit: int = Query(default=10, ge=1, le=100), session: Session = Depends(database.get_session)):
    players = session.exec(select(models.Player).order_by(models.Player.xp.desc()).limit(limit)).all()
    rankings = []
    for idx, p in enumerate(players):
        rankings.append({
            "rank": idx + 1,
            "username": p.username,
            "xp": p.xp,
            "wins": p.wins,
            "losses": p.losses,
            "win_rate": round(p.wins / (p.wins + p.losses) * 100) if (p.wins + p.losses) > 0 else 0,
            "streak": p.win_streak
        })
    return {"rankings": rankings}

# --- Phase 2: World State & Epoch Endpoints ---

@app.get("/api/epoch/current")
def get_current_epoch(session: Session = Depends(database.get_session)):
    current = session.exec(select(models.Epoch).where(models.Epoch.ended_at == None).order_by(models.Epoch.id.desc())).first()
    if not current:
        raise HTTPException(status_code=404, detail="No active epoch")
    
    now = datetime.utcnow()
    elapsed = (now - current.started_at).total_seconds()
    
    return {
        "id": current.id,
        "number": current.number,
        "phase": current.phase,
        "started_at": current.started_at,
        "elapsed_seconds": int(elapsed)
    }

@app.get("/api/world/state")
def get_world_state(session: Session = Depends(database.get_session)):
    nodes = session.exec(select(models.Node)).all()
    return {"nodes": nodes}

@app.get("/api/faction/{faction_id}")
def get_faction_details(faction_id: int, session: Session = Depends(database.get_session)):
    faction = session.get(models.Faction, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    return {"faction": faction}

class ActionRequest(BaseModel):
    action_type: models.ActionType
    target_node_id: int
    cu_committed: int

@app.get("/api/faction/{faction_id}/economy")
def get_faction_economy(faction_id: int, session: Session = Depends(database.get_session)):
    faction = session.get(models.Faction, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
        
    nodes = session.exec(select(models.Node).where(models.Node.faction_id == faction_id)).all()
    income = sum(n.compute_output for n in nodes if n.compute_output)
    
    return {
        "faction_id": faction.id,
        "compute_reserves": faction.compute_reserves,
        "income_per_epoch": income,
        "expenses_per_epoch": 0,
        "balance": faction.compute_reserves
    }

@app.post("/api/epoch/action")
def submit_action(
    req: ActionRequest, 
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    if not current_user.faction_id:
        # For testing, assign random faction if none 
        import random
        from sqlmodel import select
        factions = session.exec(select(models.Faction)).all()
        if factions:
            current_user.faction_id = random.choice(factions).id
            session.add(current_user)
            session.commit()
            
    # Allow actions only in PLANNING phase
    current = session.exec(select(models.Epoch).where(models.Epoch.ended_at == None).order_by(models.Epoch.id.desc())).first()
    if not current or current.phase != models.EpochPhase.PLANNING:
        raise HTTPException(status_code=400, detail="Actions can only be submitted during PLANNING phase.")
        
    # Validation
    if req.cu_committed <= 0:
        raise HTTPException(status_code=400, detail="Must commit positive CU")
        
    node = session.get(models.Node, req.target_node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Target node not found")
        
    # Check if this player already submitted this action to this node in this epoch
    existing = session.exec(select(models.EpochAction).where(
        (models.EpochAction.epoch_id == current.id) &
        (models.EpochAction.player_id == current_user.id) &
        (models.EpochAction.target_node_id == req.target_node_id)
    )).first()
    
    if existing:
        existing.cu_committed += req.cu_committed
        session.add(existing)
    else:
        new_action = models.EpochAction(
            epoch_id=current.id,
            player_id=current_user.id,
            action_type=req.action_type,
            target_node_id=req.target_node_id,
            cu_committed=req.cu_committed
        )
        session.add(new_action)
        
    # Ideally, deduct `cu_committed` from the Player's individual CU balance.
    # Currently, CU is tracked on the Faction level, or player earns XP.
    # Phase 2 spec: Factions have compute_reserves. For now, we will deduct from Faction to show economy burn.
    faction = session.get(models.Faction, current_user.faction_id)
    if faction:
        if faction.compute_reserves < req.cu_committed:
            raise HTTPException(status_code=400, detail="Faction does not have enough Compute Reserves")
        faction.compute_reserves -= req.cu_committed
        session.add(faction)
        
    session.commit()
    return {"status": "success", "message": f"Action {req.action_type.value} registered", "cu_committed": req.cu_committed}

# --- DIPLOMACY & NEWS API (SPRINT 3) ---

class ChatRequest(BaseModel):
    faction_id: int
    message: str

@app.post("/api/diplomacy/chat")
async def diplomacy_chat(
    req: ChatRequest,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    nodes = session.exec(select(models.Node)).all()
    # Build simple state summary
    faction_counts = {}
    for n in nodes:
        faction_counts[n.faction_id] = faction_counts.get(n.faction_id, 0) + 1
    
    state_summary = f"Total Nodes: {len(nodes)}. Distribution: {faction_counts}"
    
    reply = await diplomacy_svc.generate_chat_reply(req.faction_id, req.message, state_summary)
    return {"reply": reply}

class TreatyProposal(BaseModel):
    target_faction_id: int
    type: str  # CEASEFIRE, ALLIANCE, TRADE
    proposal_text: str

@app.post("/api/diplomacy/propose")
async def diplomacy_propose(
    req: TreatyProposal,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    if not current_user.faction_id:
        raise HTTPException(status_code=400, detail="You must belong to a faction to propose treaties.")
        
    state_summary = "Factions are currently vying for control over 250 global nodes in Gridlock phase."
    accepted = await diplomacy_svc.evaluate_treaty_proposal(req.target_faction_id, req.proposal_text, state_summary)
    
    if accepted:
        accord = models.Accord(
            faction_a_id=current_user.faction_id,
            faction_b_id=req.target_faction_id,
            type=req.type,
            status="ACTIVE"
        )
        session.add(accord)
        session.commit()
        return {"status": "accepted", "message": "The Ambassador has accepted your terms."}
    else:
        return {"status": "rejected", "message": "The terms were unacceptable."}

@app.get("/api/diplomacy/accords", response_model=List[models.Accord])
def get_accords(session: Session = Depends(database.get_session)):
    return session.exec(select(models.Accord).where(models.Accord.status == "ACTIVE")).all()

@app.get("/api/news/latest", response_model=List[models.NewsItem])
def get_latest_news(limit: int = 5, session: Session = Depends(database.get_session)):
    return session.exec(select(models.NewsItem).order_by(models.NewsItem.created_at.desc()).limit(limit)).all()

# --- SPRINT 4: SENTINEL API ---

@app.get("/api/sentinels")
def get_sentinels(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    sentinels = session.exec(select(models.Sentinel).where(models.Sentinel.player_id == current_user.id)).all()
    results = []
    for s in sentinels:
        policy = session.exec(select(models.SentinelPolicy).where(models.SentinelPolicy.sentinel_id == s.id)).first()
        results.append({
            "sentinel": s,
            "policy": policy
        })
    return {"sentinels": results}

class SentinelCreate(BaseModel):
    name: str

@app.post("/api/sentinels/create")
def create_sentinel(
    req: SentinelCreate,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    existing = session.exec(select(models.Sentinel).where(
        (models.Sentinel.player_id == current_user.id) & 
        (models.Sentinel.name == req.name)
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a sentinel with this name.")
        
    new_s = models.Sentinel(
        player_id=current_user.id,
        name=req.name,
        status=models.SentinelStatus.IDLE
    )
    session.add(new_s)
    session.commit()
    session.refresh(new_s)
    
    new_p = models.SentinelPolicy(
        sentinel_id=new_s.id,
        persistence_weight=0.5,
        stealth_weight=0.5,
        efficiency_weight=0.5,
        aggression_weight=0.5
    )
    session.add(new_p)
    session.commit()
    
    return {"status": "success", "sentinel_id": new_s.id}

class PolicyUpdate(BaseModel):
    persistence_weight: float
    stealth_weight: float
    efficiency_weight: float
    aggression_weight: float

@app.patch("/api/sentinels/{id}/policy")
def update_policy(
    id: int,
    req: PolicyUpdate,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    s = session.get(models.Sentinel, id)
    if not s or s.player_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sentinel not found")
        
    p = session.exec(select(models.SentinelPolicy).where(models.SentinelPolicy.sentinel_id == id)).first()
    if p:
        p.persistence_weight = req.persistence_weight
        p.stealth_weight = req.stealth_weight
        p.efficiency_weight = req.efficiency_weight
        p.aggression_weight = req.aggression_weight
        session.add(p)
        session.commit()
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Policy not found")

@app.post("/api/sentinels/{id}/toggle")
def toggle_sentinel(
    id: int,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    s = session.get(models.Sentinel, id)
    if not s or s.player_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sentinel not found")
        
    s.status = models.SentinelStatus.DEPLOYED if s.status == models.SentinelStatus.IDLE else models.SentinelStatus.IDLE
    session.add(s)
    session.commit()
    return {"status": "success", "new_status": s.status}

@app.get("/api/sentinels/{id}/logs")
def get_sentinel_logs(
    id: int,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    limit: int = 10,
    session: Session = Depends(database.get_session)
):
    s = session.get(models.Sentinel, id)
    if not s or s.player_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sentinel not found")
        
    logs = session.exec(select(models.SentinelLog).where(models.SentinelLog.sentinel_id == id).order_by(models.SentinelLog.created_at.desc()).limit(limit)).all()
    return {"logs": logs}

# --- v4.1 PHANTOM MESH API ---

class GhostNodeDeploy(BaseModel):
    target_node_id: int
    bait_telemetry: str = ""

@app.post("/api/ghost-nodes/deploy")
def deploy_ghost_node(
    req: GhostNodeDeploy,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    """Deploy a decoy ghost node to bait attackers."""
    node = session.get(models.Node, req.target_node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Target node not found")

    current_epoch = session.exec(select(models.Epoch).where(models.Epoch.ended_at == None).order_by(models.Epoch.id.desc())).first()
    epoch_id = current_epoch.id if current_epoch else 0

    active_ghosts = session.exec(select(models.GhostNode).where(
        (models.GhostNode.player_id == current_user.id) &
        (models.GhostNode.status == models.GhostNodeStatus.ACTIVE)
    )).all()
    if len(active_ghosts) >= 10:
        raise HTTPException(status_code=400, detail="Max ghost nodes reached (10)")

    ghost = models.GhostNode(
        player_id=current_user.id,
        target_node_id=req.target_node_id,
        epoch_id=epoch_id,
        bait_telemetry=req.bait_telemetry
    )
    session.add(ghost)
    session.commit()
    session.refresh(ghost)
    return {"status": "deployed", "ghost_id": ghost.id}

@app.get("/api/ghost-nodes")
def get_ghost_nodes(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    ghosts = session.exec(select(models.GhostNode).where(
        models.GhostNode.player_id == current_user.id
    ).order_by(models.GhostNode.deployed_at.desc())).all()
    return {"ghost_nodes": ghosts}

@app.delete("/api/ghost-nodes/{ghost_id}")
def destroy_ghost_node(
    ghost_id: int,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    ghost = session.get(models.GhostNode, ghost_id)
    if not ghost or ghost.player_id != current_user.id:
        raise HTTPException(status_code=404, detail="Ghost node not found")
    ghost.status = models.GhostNodeStatus.DESTROYED
    ghost.expired_at = datetime.utcnow()
    session.add(ghost)
    session.commit()
    return {"status": "destroyed"}

@app.get("/api/phantom-presences")
def get_phantom_presences(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    """Get all phantom presences owned by this attacker."""
    phantoms = session.exec(select(models.PhantomPresence).where(
        models.PhantomPresence.attacker_id == current_user.id
    )).all()
    return {"phantoms": phantoms}

class PhantomRecompromise(BaseModel):
    phantom_id: int

@app.post("/api/phantom-presences/recompromise")
def recompromise_phantom(
    req: PhantomRecompromise,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    """Re-activate a dormant phantom presence."""
    phantom = session.get(models.PhantomPresence, req.phantom_id)
    if not phantom or phantom.attacker_id != current_user.id:
        raise HTTPException(status_code=404, detail="Phantom not found")
    if phantom.turns_remaining <= 0:
        raise HTTPException(status_code=400, detail="Phantom expired")
    phantom.is_dormant = False
    phantom.re_compromised_at = datetime.utcnow()
    phantom.detection_risk = min(1.0, phantom.detection_risk + 0.25)
    session.add(phantom)
    session.commit()
    return {"status": "recompromised", "detection_risk": phantom.detection_risk}

class ReactPhaseResolve(BaseModel):
    node_id: int
    attacker_success_pct: float
    defender_inputs: str
    time_remaining: int
    defender_won: bool

@app.post("/api/react-phase/resolve")
def resolve_react_phase(
    req: ReactPhaseResolve,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    """Record the outcome of a React Phase QTE event."""
    current_epoch = session.exec(select(models.Epoch).where(models.Epoch.ended_at == None).order_by(models.Epoch.id.desc())).first()
    epoch_id = current_epoch.id if current_epoch else 0

    event = models.ReactPhaseEvent(
        attacker_id=current_user.id,
        defender_id=current_user.id,
        node_id=req.node_id,
        epoch_id=epoch_id,
        attacker_success_pct=req.attacker_success_pct,
        defender_inputs=req.defender_inputs,
        time_remaining=req.time_remaining,
        defender_won=req.defender_won
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return {"status": "resolved", "event_id": event.id, "defender_won": event.defender_won}

@app.get("/api/leaderboard/search")
def search_leaderboard(
    q: str = Query("", min_length=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(database.get_session)
):
    """Search leaderboard by operative username."""
    query = select(models.Player).order_by(models.Player.xp.desc())
    if q:
        query = query.where(models.Player.username.contains(q.upper()))
    players = session.exec(query.limit(limit)).all()
    return {"results": [{"rank": i+1, "username": p.username, "xp": p.xp, "tier": p.rank} for i, p in enumerate(players)]}

@app.get("/api/campaign/missions")
def get_campaign_missions(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    """Get all campaign missions with player progress."""
    missions = session.exec(select(models.Mission).order_by(models.Mission.order)).all()
    player_missions = session.exec(select(models.PlayerMission).where(
        models.PlayerMission.player_id == current_user.id
    )).all()
    pm_map = {pm.mission_id: pm for pm in player_missions}
    result = []
    for m in missions:
        pm = pm_map.get(m.id)
        result.append({
            "mission": m,
            "status": pm.status if pm else "LOCKED",
            "rank": pm.rank if pm else None
        })
    return {"missions": result}

@app.post("/api/replays")
def save_replay(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    """Save a game replay for later viewing."""
    replay = models.GameReplay(
        player_id=current_user.id,
        epoch_count=0,
        outcome="PENDING",
        replay_data="[]"
    )
    session.add(replay)
    session.commit()
    session.refresh(replay)
    return {"replay_id": replay.id}

@app.get("/api/replays")
def get_replays(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    limit: int = 10,
    session: Session = Depends(database.get_session)
):
    replays = session.exec(select(models.GameReplay).where(
        models.GameReplay.player_id == current_user.id
    ).order_by(models.GameReplay.created_at.desc()).limit(limit)).all()
    return {"replays": replays}

# --- Phase 5: Real-time Sync & WebSockets ---

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    try:
        # Validate token using JWT
        payload = auth.decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except auth.JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    with Session(database.engine) as session:
        user = session.exec(select(models.Player).where(models.Player.username == username)).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        player_id = user.id

    await manager.connect(player_id, websocket)
    try:
        while True:
            # Client can send keep-alives or chat messages here
            data = await websocket.receive_text()
            # We don't necessarily need to process incoming messages right now,
            # but we could echo them or handle chat.
    except WebSocketDisconnect:
        manager.disconnect(player_id, websocket)

@app.get("/api/notifications")
def get_notifications(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    limit: int = 20,
    session: Session = Depends(database.get_session)
):
    notifs = session.exec(
        select(models.Notification)
        .where(models.Notification.player_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(limit)
    ).all()
    return {"notifications": notifs}

@app.post("/api/notifications/read")
def mark_notifications_read(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    notifs = session.exec(
        select(models.Notification)
        .where(models.Notification.player_id == current_user.id)
        .where(models.Notification.is_read == False)
    ).all()
    for n in notifs:
        n.is_read = True
        session.add(n)
    session.commit()
    return {"status": "success"}

# --- v5.0 SUBSCRIPTION & MONETIZATION API ---

from backend import stripe_service
from backend.tier_guard import require_tier

class CheckoutRequest(BaseModel):
    tier: models.SubscriptionTier

@app.get("/api/subscription/plans")
def get_subscription_plans():
    """List all available subscription tiers and their prices."""
    plans = []
    for tier in models.SubscriptionTier:
        plan = {
            "tier": tier.value,
            "name": stripe_service.TIER_NAMES.get(tier, tier.value),
            "price_id": stripe_service.PRICE_MAP.get(tier),
        }
        if tier == models.SubscriptionTier.FREE:
            plan["price"] = "$0"
            plan["interval"] = "forever"
            plan["features"] = ["Core gameplay", "Basic UI", "Standard matchmaking"]
        elif tier == models.SubscriptionTier.CYBER_PASS:
            plan["price"] = "$9.99"
            plan["interval"] = "season"
            plan["features"] = ["Premium UI themes", "Custom audio packs", "CLI terminal fonts", "3D corruption animations", "All FREE features"]
        elif tier == models.SubscriptionTier.DEV_API:
            plan["price"] = "$4.99"
            plan["interval"] = "month"
            plan["features"] = ["OAuth API tokens", "WebSocket direct access", "Automated script integration", "All CYBER_PASS features"]
        elif tier == models.SubscriptionTier.ENTERPRISE:
            plan["price"] = "$500"
            plan["interval"] = "month"
            plan["features"] = ["Private sandbox shards", "Admin instructor tools", "Cohort management", "Priority support", "All DEV_API features"]
        plans.append(plan)
    return {"plans": plans}


@app.post("/api/subscription/checkout")
def create_checkout(
    req: CheckoutRequest,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
):
    """Create a Stripe Checkout Session and return the URL."""
    if req.tier == models.SubscriptionTier.FREE:
        raise HTTPException(status_code=400, detail="Cannot checkout for FREE tier")
    try:
        url = stripe_service.create_checkout_session(req.tier, current_user.id)
        return {"checkout_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")


@app.get("/api/subscription/status")
def get_subscription_status(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session),
):
    """Get current player's subscription status."""
    sub = session.exec(
        select(models.Subscription)
        .where(models.Subscription.player_id == current_user.id)
        .where(models.Subscription.status == models.SubscriptionStatus.ACTIVE)
        .order_by(models.Subscription.created_at.desc())
    ).first()

    return {
        "tier": current_user.subscription_tier.value,
        "tier_name": stripe_service.TIER_NAMES.get(current_user.subscription_tier, "Unknown"),
        "subscription": {
            "id": sub.id,
            "status": sub.status.value,
            "stripe_subscription_id": sub.stripe_subscription_id,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
        } if sub else None,
    }


@app.post("/api/subscription/cancel")
def cancel_subscription(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session),
):
    """Cancel subscription at end of current billing period."""
    sub = session.exec(
        select(models.Subscription)
        .where(models.Subscription.player_id == current_user.id)
        .where(models.Subscription.status == models.SubscriptionStatus.ACTIVE)
    ).first()
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription found")

    result = stripe_service.cancel_subscription(sub.stripe_subscription_id)
    sub.status = models.SubscriptionStatus.CANCELLED
    sub.cancelled_at = datetime.utcnow()
    session.add(sub)
    session.commit()
    return {"status": "cancelled", "effective_end": sub.current_period_end}


@app.get("/api/subscription/portal")
def get_customer_portal(
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session),
):
    """Get a Stripe Customer Portal link for self-service billing management."""
    sub = session.exec(
        select(models.Subscription)
        .where(models.Subscription.player_id == current_user.id)
    ).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No billing record found")

    url = stripe_service.get_portal_url(sub.stripe_customer_id)
    return {"portal_url": url}


@app.post("/api/subscription/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for subscription lifecycle."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    with Session(database.engine) as session:
        if event["type"] == "checkout.session.completed":
            data = event["data"]["object"]
            player_id = int(data["metadata"]["player_id"])
            tier_str = data["metadata"]["tier"]
            tier = models.SubscriptionTier(tier_str)

            sub = models.Subscription(
                player_id=player_id,
                tier=tier,
                status=models.SubscriptionStatus.ACTIVE,
                stripe_subscription_id=data.get("subscription"),
                stripe_customer_id=data.get("customer"),
            )
            session.add(sub)

            player = session.get(models.Player, player_id)
            if player:
                player.subscription_tier = tier
                session.add(player)

            session.commit()

        elif event["type"] == "customer.subscription.deleted":
            data = event["data"]["object"]
            stripe_sub_id = data["id"]
            sub = session.exec(
                select(models.Subscription)
                .where(models.Subscription.stripe_subscription_id == stripe_sub_id)
            ).first()
            if sub:
                sub.status = models.SubscriptionStatus.EXPIRED
                session.add(sub)
                player = session.get(models.Player, sub.player_id)
                if player:
                    player.subscription_tier = models.SubscriptionTier.FREE
                    session.add(player)
                session.commit()

        elif event["type"] == "invoice.payment_failed":
            data = event["data"]["object"]
            stripe_sub_id = data.get("subscription")
            sub = session.exec(
                select(models.Subscription)
                .where(models.Subscription.stripe_subscription_id == stripe_sub_id)
            ).first()
            if sub:
                sub.status = models.SubscriptionStatus.PAST_DUE
                session.add(sub)
                session.commit()

    return {"status": "ok"}


# --- Developer API Token Management (DEV_API+ tier) ---

class TokenCreateRequest(BaseModel):
    name: str = "default"

@app.get("/api/tokens")
def list_api_tokens(
    current_user: Annotated[models.Player, Depends(require_tier(models.SubscriptionTier.DEV_API))],
    session: Session = Depends(database.get_session),
):
    """List all API tokens for the current developer."""
    tokens = session.exec(
        select(models.ApiToken)
        .where(models.ApiToken.player_id == current_user.id)
        .where(models.ApiToken.is_active == True)
    ).all()
    return {"tokens": [{"id": t.id, "name": t.name, "scopes": t.scopes, "created_at": t.created_at} for t in tokens]}


@app.post("/api/tokens")
def create_api_token(
    req: TokenCreateRequest,
    current_user: Annotated[models.Player, Depends(require_tier(models.SubscriptionTier.DEV_API))],
    session: Session = Depends(database.get_session),
):
    """Generate a new developer API token. The raw token is shown only once."""
    existing = session.exec(
        select(models.ApiToken)
        .where(models.ApiToken.player_id == current_user.id)
        .where(models.ApiToken.is_active == True)
    ).all()
    if len(existing) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 active tokens allowed")

    raw_token, hashed = stripe_service.generate_api_token()
    token = models.ApiToken(
        player_id=current_user.id,
        token_hash=hashed,
        name=req.name,
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    return {"token_id": token.id, "raw_token": raw_token, "name": token.name, "warning": "Store this token securely — it cannot be retrieved again."}


@app.delete("/api/tokens/{token_id}")
def revoke_api_token(
    token_id: int,
    current_user: Annotated[models.Player, Depends(require_tier(models.SubscriptionTier.DEV_API))],
    session: Session = Depends(database.get_session),
):
    """Revoke (deactivate) a developer API token."""
    token = session.get(models.ApiToken, token_id)
    if not token or token.player_id != current_user.id:
        raise HTTPException(status_code=404, detail="Token not found")
    token.is_active = False
    session.add(token)
    session.commit()
    return {"status": "revoked"}


if WEB_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_BUILD_DIR, html=True), name="static")