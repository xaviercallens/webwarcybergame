"""
Firestore real-time sync for Neo-Hack v3.1 multiplayer.
Manages game session state in Firestore for real-time updates.

Blueprint Alignment: Section 5.3 (Firestore Integration)
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

# Firestore client is optional — gracefully degrade when not available
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logger.warning("google-cloud-firestore not installed. Using in-memory fallback.")


class FirestoreGameSync:
    """
    Manages game session state in Firestore for real-time multiplayer.
    Falls back to in-memory dict when Firestore is unavailable.
    """

    COLLECTION_SESSIONS = "game_sessions"
    COLLECTION_REPLAYS = "match_replays"

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Firestore sync.

        Args:
            project_id: GCP project ID (uses default if None)
        """
        self.db = None
        self._fallback_store: Dict[str, Dict[str, Any]] = {}

        if FIRESTORE_AVAILABLE:
            try:
                self.db = firestore.Client(project=project_id) if project_id else firestore.Client()
                logger.info("Firestore client initialized")
            except Exception as e:
                logger.warning(f"Firestore init failed, using fallback: {e}")

    @property
    def is_connected(self) -> bool:
        return self.db is not None

    def create_game_session(self, session_id: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Create new multiplayer game session."""
        doc = {
            "created_at": time.time(),
            "scenario": scenario.get("name", "unknown"),
            "scenario_config": scenario,
            "current_turn": 0,
            "current_player": "attacker",
            "game_state": {},
            "players": {
                "attacker": None,
                "defender": None,
            },
            "status": "waiting",
        }

        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            ref.set(doc)
        else:
            self._fallback_store[session_id] = doc

        return doc

    def join_session(self, session_id: str, player_id: str, role: str) -> bool:
        """
        Player joins a session.

        Args:
            session_id: Game session ID
            player_id: Player identifier
            role: "attacker" or "defender"

        Returns:
            True if join succeeded
        """
        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            doc = ref.get()
            if not doc.exists:
                return False
            data = doc.to_dict()
            if data["players"][role] is not None:
                return False  # Role taken
            ref.update({f"players.{role}": player_id})
            # Start game if both players present
            other = "defender" if role == "attacker" else "attacker"
            if data["players"][other] is not None:
                ref.update({"status": "active", "current_turn": 1})
        else:
            doc = self._fallback_store.get(session_id)
            if not doc or doc["players"][role] is not None:
                return False
            doc["players"][role] = player_id
            other = "defender" if role == "attacker" else "attacker"
            if doc["players"][other] is not None:
                doc["status"] = "active"
                doc["current_turn"] = 1

        return True

    def update_game_state(self, session_id: str, new_state: Dict[str, Any]) -> None:
        """Real-time state update (<200ms target)."""
        update = {
            "game_state": new_state,
            "updated_at": time.time(),
        }

        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            ref.update(update)
        else:
            doc = self._fallback_store.get(session_id)
            if doc:
                doc.update(update)

    def update_turn(self, session_id: str, turn: int, player: str) -> None:
        """Update current turn and player."""
        update = {
            "current_turn": turn,
            "current_player": player,
            "updated_at": time.time(),
        }

        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            ref.update(update)
        else:
            doc = self._fallback_store.get(session_id)
            if doc:
                doc.update(update)

    def end_game(self, session_id: str, winner: Optional[str] = None) -> None:
        """Mark game as ended."""
        update = {
            "status": "finished",
            "winner": winner,
            "ended_at": time.time(),
        }

        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            ref.update(update)
        else:
            doc = self._fallback_store.get(session_id)
            if doc:
                doc.update(update)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            doc = ref.get()
            return doc.to_dict() if doc.exists else None
        else:
            return self._fallback_store.get(session_id)

    def listen_for_updates(self, session_id: str, callback: Callable) -> Any:
        """
        Subscribe to real-time updates.

        Args:
            session_id: Game session ID
            callback: Function called on updates

        Returns:
            Watch handle (for unsubscribing)
        """
        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            return ref.on_snapshot(callback)
        else:
            logger.warning("Real-time listeners not available without Firestore")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a game session."""
        if self.db:
            ref = self.db.collection(self.COLLECTION_SESSIONS).document(session_id)
            ref.delete()
        else:
            if session_id in self._fallback_store:
                del self._fallback_store[session_id]
                return True
            return False
        return True

    def list_active_sessions(self) -> list:
        """List all active (non-finished) sessions."""
        if self.db:
            query = (
                self.db.collection(self.COLLECTION_SESSIONS)
                .where("status", "==", "active")
                .limit(50)
            )
            return [doc.to_dict() | {"id": doc.id} for doc in query.stream()]
        else:
            return [
                v | {"id": k}
                for k, v in self._fallback_store.items()
                if v.get("status") != "finished"
            ]
