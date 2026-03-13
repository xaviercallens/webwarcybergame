import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from backend import database, auth, models

WEB_BUILD_DIR = Path(os.getenv("WEB_BUILD_DIR", Path(__file__).parent.parent.parent.parent / "build" / "web"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="Backend",
    description="Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/auth/register", response_model=models.Token)
def register_user(user_in: models.PlayerCreate, session: Session = Depends(database.get_session)):
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
def login_user(user_in: models.PlayerCreate, session: Session = Depends(database.get_session)):
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
def get_leaderboard(limit: int = 10, session: Session = Depends(database.get_session)):
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

if WEB_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_BUILD_DIR, html=True), name="static")