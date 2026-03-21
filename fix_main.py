import re

with open("backend/src/backend/main.py", "r") as f:
    content = f.read()

# 1. Fix get_sentinel_logs syntax error
content = content.replace("""@app.get("/api/sentinels/{id}/logs")
def get_sentinel_logs(
    id: int,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    limit: int = 10,
    session: Session = Depends(database.get_session)
        
    logs = session.exec(select(models.SentinelLog).where(models.SentinelLog.sentinel_id == id).order_by(models.SentinelLog.created_at.desc()).limit(limit)).all()""", """@app.get("/api/sentinels/{id}/logs")
def get_sentinel_logs(
    id: int,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    limit: int = 10,
    session: Session = Depends(database.get_session)
):
    s = session.get(models.Sentinel, id)
    if not s or s.player_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sentinel not found")
        
    logs = session.exec(select(models.SentinelLog).where(models.SentinelLog.sentinel_id == id).order_by(models.SentinelLog.created_at.desc()).limit(limit)).all()""")


# 2. Fix WS
content = content.replace("""@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        
    try:""", """@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        token = data.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    try:""")

# 3. Game Over Exploit
content = content.replace("""@app.post("/api/players/me/game-over", response_model=models.PlayerPublic)
def submit_game_over(stats: GameOverStats, current_user: models.Player = Depends(auth.get_current_user), session: Session = Depends(database.get_session)):
    base_xp = 100 if stats.won else 50
    capture_bonus = stats.nodes_captured * 8
    speed_bonus = max(0, (480 - stats.time_seconds)) // 4""", """@app.post("/api/players/me/game-over", response_model=models.PlayerPublic)
def submit_game_over(stats: GameOverStats, current_user: models.Player = Depends(auth.get_current_user), session: Session = Depends(database.get_session)):
    if stats.nodes_captured > 250:
        raise HTTPException(status_code=400, detail="Invalid node capture count.")
        
    base_xp = 100 if stats.won else 50
    capture_bonus = stats.nodes_captured * 8
    speed_bonus = max(0, (900 - stats.time_seconds)) // 4""")

# 4. Chat Rate Limit
content = content.replace("""@app.post("/api/diplomacy/chat")
async def diplomacy_chat(
    req: ChatRequest,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],""", """@app.post("/api/diplomacy/chat")
@limiter.limit("5/minute")
async def diplomacy_chat(
    req: ChatRequest,
    request: Request,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],""")

# 5. Infinite Money Glitch
content = content.replace("""@app.post("/api/diplomacy/propose")
async def diplomacy_propose(
    req: TreatyProposal,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    if not current_user.faction_id:
        raise HTTPException(status_code=400, detail="You must belong to a faction to propose treaties.")
        
    state_summary = "Factions are currently vying for control over 250 global nodes in Gridlock phase." """, """@app.post("/api/diplomacy/propose")
async def diplomacy_propose(
    req: TreatyProposal,
    current_user: Annotated[models.Player, Depends(auth.get_current_user)],
    session: Session = Depends(database.get_session)
):
    if not current_user.faction_id:
        raise HTTPException(status_code=400, detail="You must belong to a faction to propose treaties.")
        
    if req.type == "TRADE":
        from sqlmodel import select
        existing_trade = session.exec(select(models.Accord).where(
            (models.Accord.status == "ACTIVE") &
            (models.Accord.type == "TRADE") &
            (((models.Accord.faction_a_id == current_user.faction_id) & (models.Accord.faction_b_id == req.target_faction_id)) |
             ((models.Accord.faction_a_id == req.target_faction_id) & (models.Accord.faction_b_id == current_user.faction_id)))
        )).first()
        if existing_trade:
            raise HTTPException(status_code=400, detail="A TRADE accord is already active with this faction.")
            
    state_summary = "Factions are currently vying for control over 250 global nodes in Gridlock phase." """)

with open("backend/src/backend/main.py", "w") as f:
    f.write(content)

print("Applied fixes via python script.")
