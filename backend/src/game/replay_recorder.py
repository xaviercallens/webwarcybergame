"""
Replay recording system for Neo-Hack v3.1.
Records match events for replay, analysis, and RL training data extraction.

Blueprint Alignment: Section 3.6 (Logging & Analytics)
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ReplayRecorder:
    """
    Records each turn of a game for replay and analysis.
    Stores initial state + event deltas for compact representation.
    """

    def __init__(self, session_id: str, scenario_name: str = ""):
        self.session_id = session_id
        self.scenario_name = scenario_name
        self.events: List[Dict[str, Any]] = []
        self.initial_state: Optional[Dict[str, Any]] = None
        self.metadata: Dict[str, Any] = {
            "created_at": time.time(),
            "scenario": scenario_name,
        }
        self._winner: Optional[str] = None

    def set_initial_state(self, state: Dict[str, Any]) -> None:
        """Record the initial game state."""
        self.initial_state = state

    def record_turn(self, turn_data: Dict[str, Any]) -> None:
        """
        Record a single turn event.

        Args:
            turn_data: Dict with turn, player, action, result, state_changes
        """
        event = {
            "turn": turn_data.get("turn", len(self.events)),
            "player": turn_data.get("player", "unknown"),
            "action": turn_data.get("action"),
            "action_name": turn_data.get("action_name", ""),
            "result": turn_data.get("result", {}),
            "state_changes": turn_data.get("state_changes", {}),
            "timestamp": time.time(),
        }
        self.events.append(event)

    def set_winner(self, winner: str) -> None:
        """Set the game winner."""
        self._winner = winner

    def get_winner(self) -> Optional[str]:
        """Get the game winner."""
        return self._winner

    def get_replay_data(self) -> Dict[str, Any]:
        """Get the full replay data."""
        return {
            "session_id": self.session_id,
            "initial_state": self.initial_state,
            "events": self.events,
            "metadata": {
                **self.metadata,
                "duration": len(self.events),
                "winner": self._winner,
                "scenario": self.scenario_name,
                "ended_at": time.time(),
            },
        }

    def save_to_file(self, directory: str = "replays") -> str:
        """
        Save replay to a JSON file.

        Args:
            directory: Directory to save replay files

        Returns:
            Path to saved file
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        filepath = path / f"{self.session_id}.json"
        with open(filepath, "w") as f:
            json.dump(self.get_replay_data(), f, indent=2, default=str)

        logger.info(f"Replay saved to {filepath}")
        return str(filepath)

    def extract_trajectories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract state-action trajectories for RL training.

        Returns:
            Dict with attacker and defender trajectories
        """
        attacker_trajectory = []
        defender_trajectory = []

        for event in self.events:
            entry = {
                "action": event["action"],
                "result": event.get("result", {}),
                "turn": event["turn"],
            }

            if event["player"] == "attacker":
                attacker_trajectory.append(entry)
            else:
                defender_trajectory.append(entry)

        return {
            "attacker": attacker_trajectory,
            "defender": defender_trajectory,
        }

    def get_action_sequence(self, player: Optional[str] = None) -> List[int]:
        """
        Get sequence of actions taken.

        Args:
            player: Filter by player, or None for all

        Returns:
            List of action IDs
        """
        events = self.events
        if player:
            events = [e for e in events if e["player"] == player]
        return [e["action"] for e in events if e["action"] is not None]

    def get_summary(self) -> Dict[str, Any]:
        """Get replay summary statistics."""
        attacker_actions = [e for e in self.events if e["player"] == "attacker"]
        defender_actions = [e for e in self.events if e["player"] == "defender"]

        attacker_successes = sum(
            1 for e in attacker_actions
            if e.get("result", {}).get("success", False)
        )
        defender_successes = sum(
            1 for e in defender_actions
            if e.get("result", {}).get("success", False)
        )

        return {
            "session_id": self.session_id,
            "total_turns": len(self.events),
            "attacker_actions": len(attacker_actions),
            "defender_actions": len(defender_actions),
            "attacker_successes": attacker_successes,
            "defender_successes": defender_successes,
            "winner": self._winner,
        }

    def __len__(self) -> int:
        return len(self.events)
