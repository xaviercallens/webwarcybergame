"""
Unit tests for Firestore sync module (in-memory fallback).
Tests session lifecycle, state updates, and multiplayer joins.
"""

import pytest

from src.cloud.firestore_sync import FirestoreGameSync


@pytest.fixture
def sync():
    return FirestoreGameSync()  # Uses in-memory fallback


class TestFirestoreGameSyncInit:

    def test_creates_without_firestore(self, sync):
        assert sync.db is None
        assert sync.is_connected is False

    def test_fallback_store_empty(self, sync):
        assert len(sync._fallback_store) == 0


class TestCreateSession:

    def test_create_session(self, sync):
        doc = sync.create_game_session("s1", {"name": "tutorial"})
        assert doc["scenario"] == "tutorial"
        assert doc["current_turn"] == 0
        assert doc["current_player"] == "attacker"
        assert doc["status"] == "waiting"
        assert doc["players"]["attacker"] is None
        assert doc["players"]["defender"] is None

    def test_create_multiple_sessions(self, sync):
        sync.create_game_session("s1", {"name": "a"})
        sync.create_game_session("s2", {"name": "b"})
        assert len(sync._fallback_store) == 2


class TestJoinSession:

    def test_join_attacker(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        result = sync.join_session("s1", "player1", "attacker")
        assert result is True
        session = sync.get_session("s1")
        assert session["players"]["attacker"] == "player1"

    def test_join_defender(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        result = sync.join_session("s1", "player2", "defender")
        assert result is True

    def test_join_both_starts_game(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        sync.join_session("s1", "p1", "attacker")
        sync.join_session("s1", "p2", "defender")
        session = sync.get_session("s1")
        assert session["status"] == "active"
        assert session["current_turn"] == 1

    def test_join_taken_role_fails(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        sync.join_session("s1", "p1", "attacker")
        result = sync.join_session("s1", "p2", "attacker")
        assert result is False

    def test_join_nonexistent_session(self, sync):
        result = sync.join_session("nope", "p1", "attacker")
        assert result is False


class TestUpdateGameState:

    def test_update_state(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        sync.update_game_state("s1", {"alert": 50, "turn": 3})
        session = sync.get_session("s1")
        assert session["game_state"]["alert"] == 50
        assert "updated_at" in session

    def test_update_nonexistent(self, sync):
        # Should not raise, just no-op
        sync.update_game_state("nope", {"alert": 50})


class TestUpdateTurn:

    def test_update_turn(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        sync.update_turn("s1", 5, "defender")
        session = sync.get_session("s1")
        assert session["current_turn"] == 5
        assert session["current_player"] == "defender"


class TestEndGame:

    def test_end_game_with_winner(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        sync.end_game("s1", winner="attacker")
        session = sync.get_session("s1")
        assert session["status"] == "finished"
        assert session["winner"] == "attacker"
        assert "ended_at" in session

    def test_end_game_draw(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        sync.end_game("s1", winner=None)
        session = sync.get_session("s1")
        assert session["status"] == "finished"
        assert session["winner"] is None


class TestGetSession:

    def test_get_existing(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        session = sync.get_session("s1")
        assert session is not None

    def test_get_nonexistent(self, sync):
        session = sync.get_session("nope")
        assert session is None


class TestDeleteSession:

    def test_delete_existing(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        result = sync.delete_session("s1")
        assert result is True
        assert sync.get_session("s1") is None

    def test_delete_nonexistent(self, sync):
        result = sync.delete_session("nope")
        assert result is False


class TestListActiveSessions:

    def test_list_active(self, sync):
        sync.create_game_session("s1", {"name": "a"})
        sync.create_game_session("s2", {"name": "b"})
        sessions = sync.list_active_sessions()
        assert len(sessions) == 2

    def test_finished_excluded(self, sync):
        sync.create_game_session("s1", {"name": "a"})
        sync.create_game_session("s2", {"name": "b"})
        sync.end_game("s1", winner="attacker")
        sessions = sync.list_active_sessions()
        assert len(sessions) == 1
        assert sessions[0]["id"] == "s2"

    def test_list_empty(self, sync):
        sessions = sync.list_active_sessions()
        assert sessions == []


class TestListenForUpdates:

    def test_listen_returns_none_without_firestore(self, sync):
        sync.create_game_session("s1", {"name": "test"})
        result = sync.listen_for_updates("s1", lambda *a: None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
