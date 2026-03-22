"""
Neo-Hack: Gridlock v4.1 — Phantom Mesh Backend Tests
Tests all new v4.1 API endpoints: ghost nodes, phantom presences,
react phase, leaderboard search, campaign missions, and replays.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models import (
    Player, Node, Epoch, Faction, EpochPhase,
    GhostNode, GhostNodeStatus, PhantomPresence, ReactPhaseEvent,
    Mission, PlayerMission, MissionStatus, GameReplay,
)
from backend.auth import get_password_hash, create_access_token


# --- Helpers ---

def create_test_user(session: Session, username: str = "TEST_PHANTOM") -> Player:
    player = Player(
        username=username,
        hashed_password=get_password_hash("testpass123"),
        xp=500,
        rank="PACKET_SNIFFER",
    )
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


def create_test_faction(session: Session) -> Faction:
    faction = Faction(name="TestFaction", color="#00FFDD", compute_reserves=5000)
    session.add(faction)
    session.commit()
    session.refresh(faction)
    return faction


def create_test_node(session: Session, faction_id: int) -> Node:
    node = Node(name="NODE_TEST_01", lat=40.71, lng=-74.00, faction_id=faction_id)
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


def create_test_epoch(session: Session) -> Epoch:
    epoch = Epoch(number=1, phase=EpochPhase.PLANNING)
    session.add(epoch)
    session.commit()
    session.refresh(epoch)
    return epoch


def auth_header(player: Player) -> dict:
    token = create_access_token(data={"sub": player.username})
    return {"Authorization": f"Bearer {token}"}


# ============================================
# Ghost Node Tests
# ============================================

class TestGhostNodes:
    def test_deploy_ghost_node(self, client: TestClient, session: Session):
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        epoch = create_test_epoch(session)
        player = create_test_user(session)

        resp = client.post(
            "/api/ghost-nodes/deploy",
            json={"target_node_id": node.id, "bait_telemetry": "decoy_signal_alpha"},
            headers=auth_header(player),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deployed"
        assert "ghost_id" in data

    def test_list_ghost_nodes(self, client: TestClient, session: Session):
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        create_test_epoch(session)
        player = create_test_user(session)

        # Deploy 3 ghosts
        for _ in range(3):
            client.post(
                "/api/ghost-nodes/deploy",
                json={"target_node_id": node.id},
                headers=auth_header(player),
            )

        resp = client.get("/api/ghost-nodes", headers=auth_header(player))
        assert resp.status_code == 200
        assert len(resp.json()["ghost_nodes"]) == 3

    def test_ghost_node_budget_limit(self, client: TestClient, session: Session):
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        create_test_epoch(session)
        player = create_test_user(session)

        # Deploy 10 ghosts (max)
        for _ in range(10):
            client.post(
                "/api/ghost-nodes/deploy",
                json={"target_node_id": node.id},
                headers=auth_header(player),
            )

        # 11th should fail
        resp = client.post(
            "/api/ghost-nodes/deploy",
            json={"target_node_id": node.id},
            headers=auth_header(player),
        )
        assert resp.status_code == 400
        assert "Max ghost nodes" in resp.json()["detail"]

    def test_destroy_ghost_node(self, client: TestClient, session: Session):
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        create_test_epoch(session)
        player = create_test_user(session)

        deploy_resp = client.post(
            "/api/ghost-nodes/deploy",
            json={"target_node_id": node.id},
            headers=auth_header(player),
        )
        ghost_id = deploy_resp.json()["ghost_id"]

        resp = client.delete(
            f"/api/ghost-nodes/{ghost_id}",
            headers=auth_header(player),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "destroyed"

    def test_unauthorized_ghost_delete(self, client: TestClient, session: Session):
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        create_test_epoch(session)
        player_a = create_test_user(session, "PLAYER_A")
        player_b = create_test_user(session, "PLAYER_B")

        deploy_resp = client.post(
            "/api/ghost-nodes/deploy",
            json={"target_node_id": node.id},
            headers=auth_header(player_a),
        )
        ghost_id = deploy_resp.json()["ghost_id"]

        # Player B tries to delete Player A's ghost
        resp = client.delete(
            f"/api/ghost-nodes/{ghost_id}",
            headers=auth_header(player_b),
        )
        assert resp.status_code == 404


# ============================================
# Phantom Presence Tests
# ============================================

class TestPhantomPresence:
    def test_list_phantoms(self, client: TestClient, session: Session):
        create_test_epoch(session)
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        player = create_test_user(session)

        # Create phantom directly in DB
        phantom = PhantomPresence(
            attacker_id=player.id,
            node_id=node.id,
            epoch_id=1,
            encryption_level=4,
            turns_remaining=3,
        )
        session.add(phantom)
        session.commit()

        resp = client.get("/api/phantom-presences", headers=auth_header(player))
        assert resp.status_code == 200
        assert len(resp.json()["phantoms"]) == 1

    def test_recompromise_phantom(self, client: TestClient, session: Session):
        create_test_epoch(session)
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        player = create_test_user(session)

        phantom = PhantomPresence(
            attacker_id=player.id,
            node_id=node.id,
            epoch_id=1,
            turns_remaining=3,
            detection_risk=0.15,
        )
        session.add(phantom)
        session.commit()
        session.refresh(phantom)

        resp = client.post(
            "/api/phantom-presences/recompromise",
            json={"phantom_id": phantom.id},
            headers=auth_header(player),
        )
        assert resp.status_code == 200
        assert resp.json()["detection_risk"] == pytest.approx(0.40, abs=0.01)

    def test_recompromise_expired_phantom(self, client: TestClient, session: Session):
        create_test_epoch(session)
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        player = create_test_user(session)

        phantom = PhantomPresence(
            attacker_id=player.id,
            node_id=node.id,
            epoch_id=1,
            turns_remaining=0,
        )
        session.add(phantom)
        session.commit()
        session.refresh(phantom)

        resp = client.post(
            "/api/phantom-presences/recompromise",
            json={"phantom_id": phantom.id},
            headers=auth_header(player),
        )
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"]


# ============================================
# React Phase Tests
# ============================================

class TestReactPhase:
    def test_resolve_react_phase(self, client: TestClient, session: Session):
        create_test_epoch(session)
        faction = create_test_faction(session)
        node = create_test_node(session, faction.id)
        player = create_test_user(session)

        resp = client.post(
            "/api/react-phase/resolve",
            json={
                "node_id": node.id,
                "attacker_success_pct": 42.5,
                "defender_inputs": "w,a,s,d,w,a",
                "time_remaining": 7,
                "defender_won": True,
            },
            headers=auth_header(player),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["defender_won"] is True
        assert "event_id" in data


# ============================================
# Leaderboard Search Tests
# ============================================

class TestLeaderboardSearch:
    def test_search_leaderboard(self, client: TestClient, session: Session):
        create_test_user(session, "GHOST_ALPHA")
        create_test_user(session, "GHOST_BETA")
        create_test_user(session, "CYBER_OPS")

        resp = client.get("/api/leaderboard/search?q=GHOST")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) == 2
        assert all("GHOST" in r["username"] for r in results)

    def test_search_empty(self, client: TestClient, session: Session):
        resp = client.get("/api/leaderboard/search?q=NONEXISTENT")
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 0


# ============================================
# Campaign Mission Tests
# ============================================

class TestCampaign:
    def test_get_missions(self, client: TestClient, session: Session):
        player = create_test_user(session)

        # Seed missions
        for i, title in enumerate(["TUTORIAL", "BANK RUN", "HEIST"]):
            session.add(Mission(order=i, title=title, xp_reward=1000 * (i + 1)))
        session.commit()

        resp = client.get("/api/campaign/missions", headers=auth_header(player))
        assert resp.status_code == 200
        missions = resp.json()["missions"]
        assert len(missions) == 3
        assert missions[0]["status"] == "LOCKED"


# ============================================
# Game Replay Tests
# ============================================

class TestReplays:
    def test_save_and_list_replays(self, client: TestClient, session: Session):
        player = create_test_user(session)

        # Save replay
        resp = client.post("/api/replays", headers=auth_header(player))
        assert resp.status_code == 200
        assert "replay_id" in resp.json()

        # List replays
        resp = client.get("/api/replays", headers=auth_header(player))
        assert resp.status_code == 200
        assert len(resp.json()["replays"]) == 1

    def test_replay_isolation(self, client: TestClient, session: Session):
        player_a = create_test_user(session, "REPLAY_A")
        player_b = create_test_user(session, "REPLAY_B")

        # Player A saves a replay
        client.post("/api/replays", headers=auth_header(player_a))

        # Player B should not see it
        resp = client.get("/api/replays", headers=auth_header(player_b))
        assert len(resp.json()["replays"]) == 0
