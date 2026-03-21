import os
from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
from typing import Annotated, List

from fastapi import FastAPI, Depends, HTTPException, status, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend import database, auth, models
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
    version="0.1.0",
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

if WEB_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_BUILD_DIR, html=True), name="static")