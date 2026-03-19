"""
Comprehensive endpoint tests for main.py — Part 1: Auth, GameOver, Leaderboard, Epoch, WorldState.
"""
import os, pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.main import app
from backend.database import get_session
from backend.models import *
from backend.auth import get_password_hash, create_access_token

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    app.dependency_overrides[get_session] = lambda: session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def _mkplayer(session, username="player1", faction_id=None):
    p = Player(username=username, hashed_password=get_password_hash("Pass123!"), faction_id=faction_id)
    session.add(p); session.commit(); session.refresh(p); return p

def _mkfaction(session, name="TestFaction", cu=5000):
    f = Faction(name=name, color="#FF0000", compute_reserves=cu)
    session.add(f); session.commit(); session.refresh(f); return f

def _tok(p): return create_access_token(data={"sub": p.username})
def _hdr(t): return {"Authorization": f"Bearer {t}"}

class TestRegister:
    def test_success(self, client):
        r = client.post("/api/auth/register", json={"username":"u1","password":"Pass123!"})
        assert r.status_code == 200 and "access_token" in r.json()
    def test_duplicate(self, client):
        client.post("/api/auth/register", json={"username":"u1","password":"Pass123!"})
        assert client.post("/api/auth/register", json={"username":"u1","password":"X"}).status_code == 400

class TestLogin:
    def test_success(self, client):
        client.post("/api/auth/register", json={"username":"u1","password":"Pass123!"})
        assert client.post("/api/auth/login", json={"username":"u1","password":"Pass123!"}).status_code == 200
    def test_wrong_pw(self, client):
        client.post("/api/auth/register", json={"username":"u1","password":"Pass123!"})
        assert client.post("/api/auth/login", json={"username":"u1","password":"wrong"}).status_code == 401
    def test_no_user(self, client):
        assert client.post("/api/auth/login", json={"username":"x","password":"x"}).status_code == 401

class TestProfile:
    def test_authed(self, client, session):
        p = _mkplayer(session); r = client.get("/api/players/me", headers=_hdr(_tok(p)))
        assert r.status_code == 200 and r.json()["username"] == "player1"
    def test_no_auth(self, client):
        assert client.get("/api/players/me").status_code in [401, 403]

class TestGameOverRemoved:
    """v3.0: game-over endpoint removed to prevent XP exploit."""
    def test_endpoint_removed(self, client, session):
        p = _mkplayer(session)
        r = client.post("/api/players/me/game-over", headers=_hdr(_tok(p)),
            json={"won":True,"time_seconds":200,"nodes_captured":10,"nodes_lost":2,"attacks":5})
        assert r.status_code in [404, 405], "game-over endpoint must be removed"
    def test_calculate_rank_utility(self):
        from backend.main import calculate_rank
        assert calculate_rank(0) == "SCRIPT_KIDDIE"
        assert calculate_rank(500) == "PACKET_SNIFFER"
        assert calculate_rank(1500) == "ROOT_ACCESS"
        assert calculate_rank(3500) == "ZERO_DAY"
        assert calculate_rank(7000) == "BLACK_HAT"
        assert calculate_rank(12000) == "SHADOW_ADMIN"
        assert calculate_rank(20000) == "GRID_SOVEREIGN"

class TestLeaderboard:
    def test_empty(self, client): assert client.get("/api/leaderboard").json()["rankings"] == []
    def test_limit(self, client, session):
        for i in range(15): _mkplayer(session, f"u{i}")
        assert len(client.get("/api/leaderboard").json()["rankings"]) == 10
    def test_custom_limit(self, client, session):
        for i in range(10): _mkplayer(session, f"u{i}")
        assert len(client.get("/api/leaderboard?limit=3").json()["rankings"]) == 3
    def test_sorted(self, client, session):
        p1 = _mkplayer(session,"low"); p1.xp=10; p2 = _mkplayer(session,"high"); p2.xp=9999
        session.add_all([p1,p2]); session.commit()
        assert client.get("/api/leaderboard").json()["rankings"][0]["username"] == "high"
    def test_winrate(self, client, session):
        p = _mkplayer(session); p.wins=7; p.losses=3; session.add(p); session.commit()
        assert client.get("/api/leaderboard").json()["rankings"][0]["win_rate"] == 70
    def test_zero_games(self, client, session):
        _mkplayer(session)
        assert client.get("/api/leaderboard").json()["rankings"][0]["win_rate"] == 0

class TestEpoch:
    def test_none(self, client): assert client.get("/api/epoch/current").status_code == 404
    def test_active(self, client, session):
        session.add(Epoch(number=1, phase=EpochPhase.PLANNING)); session.commit()
        r = client.get("/api/epoch/current"); assert r.status_code == 200 and r.json()["phase"] == "PLANNING"

class TestWorldState:
    def test_empty(self, client): assert client.get("/api/world/state").json()["nodes"] == []
    def test_with_nodes(self, client, session):
        f = _mkfaction(session)
        session.add(Node(name="N1",lat=0,lng=0,faction_id=f.id)); session.commit()
        assert len(client.get("/api/world/state").json()["nodes"]) == 1

class TestFactionEndpoints:
    def test_get(self, client, session):
        f = _mkfaction(session)
        assert client.get(f"/api/faction/{f.id}").json()["faction"]["name"] == "TestFaction"
    def test_not_found(self, client): assert client.get("/api/faction/999").status_code == 404
    def test_economy(self, client, session):
        f = _mkfaction(session, cu=3000)
        session.add(Node(name="N1",lat=0,lng=0,faction_id=f.id,compute_output=25)); session.commit()
        d = client.get(f"/api/faction/{f.id}/economy").json()
        assert d["compute_reserves"] == 3000 and d["income_per_epoch"] == 25
    def test_economy_404(self, client): assert client.get("/api/faction/999/economy").status_code == 404
