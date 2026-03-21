"""
Turn-based game manager for Neo-Hack v3.1.
Manages turn scheduling, action validation, and game state transitions.
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import random


class GamePhase(Enum):
    """Game phases."""
    SETUP = "setup"
    ATTACKER_TURN = "attacker_turn"
    DEFENDER_TURN = "defender_turn"
    GAME_OVER = "game_over"


class TurnManager:
    """
    Manages turn-based gameplay.
    Enforces action points, turn order, and game flow.
    
    Blueprint Alignment: Section 1 (Core Mechanics)
    """
    
    def __init__(self, scenario: Optional[Dict[str, Any]] = None):
        """
        Initialize turn manager.
        
        Args:
            scenario: Optional scenario configuration
        """
        self.scenario = scenario or {}
        self.current_turn = 0
        self.max_turns = scenario.get("max_turns", 50) if scenario else 50
        self.current_player = "attacker"
        self.current_phase = GamePhase.SETUP
        
        # Action points per turn
        self.action_points = {
            "attacker": scenario.get("attacker_action_points", 1) if scenario else 1,
            "defender": scenario.get("defender_action_points", 1) if scenario else 1,
        }
        
        # Track remaining action points this turn
        self.remaining_action_points = {
            "attacker": self.action_points["attacker"],
            "defender": self.action_points["defender"],
        }
        
        # Game state
        self.game_over = False
        self.winner = None
        self.turn_history = []
        self.action_history = []
    
    def start_game(self) -> Dict[str, Any]:
        """
        Start the game.
        
        Returns:
            Game state dict
        """
        self.current_phase = GamePhase.ATTACKER_TURN
        self.current_turn = 1
        self.current_player = "attacker"
        self.remaining_action_points["attacker"] = self.action_points["attacker"]
        self.remaining_action_points["defender"] = self.action_points["defender"]
        
        return {
            "phase": self.current_phase.value,
            "turn": self.current_turn,
            "current_player": self.current_player,
            "action_points": self.remaining_action_points.copy(),
        }
    
    def process_action(
        self,
        player: str,
        action: int,
        action_result: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a player action and manage turn flow.
        
        Args:
            player: "attacker" or "defender"
            action: Action ID
            action_result: Result from action execution
        
        Returns:
            (turn_switched, state_dict)
        """
        if self.game_over:
            raise RuntimeError("Game is already over")
        
        if player != self.current_player:
            raise ValueError(f"It's {self.current_player}'s turn, not {player}'s")
        
        # Validate action points
        if self.remaining_action_points[player] <= 0:
            raise ValueError(f"{player} has no action points remaining")
        
        # Deduct action points
        self.remaining_action_points[player] -= 1
        
        # Record action
        self.action_history.append({
            "turn": self.current_turn,
            "player": player,
            "action": action,
            "result": action_result,
        })
        
        # Check if turn should switch
        turn_switched = False
        if self.remaining_action_points[player] <= 0:
            turn_switched = self._switch_turn()
        
        return turn_switched, self._get_state()
    
    def _switch_turn(self) -> bool:
        """
        Switch to the next player's turn.
        
        Returns:
            True if full round completed (both players played)
        """
        if self.current_player == "attacker":
            self.current_player = "defender"
            self.current_phase = GamePhase.DEFENDER_TURN
            self.remaining_action_points["defender"] = self.action_points["defender"]
            return False
        else:
            self.current_player = "attacker"
            self.current_phase = GamePhase.ATTACKER_TURN
            self.remaining_action_points["attacker"] = self.action_points["attacker"]
            self.current_turn += 1
            
            # Check if game should end
            if self.current_turn > self.max_turns:
                self.game_over = True
                self.current_phase = GamePhase.GAME_OVER
            
            return True
    
    def check_victory(self, game_state: Any) -> Optional[str]:
        """
        Check if game has a winner.
        
        Args:
            game_state: Current game state
        
        Returns:
            Winner ("attacker" or "defender") or None
        """
        import numpy as np
        
        # Attacker wins if owns >50% of nodes
        owned_count = np.sum(game_state.attacker_owned_nodes)
        if owned_count >= game_state.num_nodes * 0.5:
            return "attacker"
        
        # Defender wins if alert level maxed out (attacker caught)
        if game_state.alert_level >= 100:
            return "defender"
        
        # Game over on max turns - check who's winning
        if self.current_turn > self.max_turns:
            if owned_count > game_state.num_nodes * 0.3:
                return "attacker"
            else:
                return "defender"
        
        return None
    
    def end_game(self, winner: Optional[str] = None) -> Dict[str, Any]:
        """
        End the game.
        
        Args:
            winner: Winner ("attacker", "defender", or None for draw)
        
        Returns:
            Game end state
        """
        self.game_over = True
        self.winner = winner
        self.current_phase = GamePhase.GAME_OVER
        
        return {
            "game_over": True,
            "winner": winner,
            "final_turn": self.current_turn,
            "total_actions": len(self.action_history),
        }
    
    def _get_state(self) -> Dict[str, Any]:
        """Get current turn state."""
        return {
            "phase": self.current_phase.value,
            "turn": self.current_turn,
            "current_player": self.current_player,
            "action_points": self.remaining_action_points.copy(),
            "game_over": self.game_over,
            "winner": self.winner,
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get current game state."""
        return self._get_state()
    
    def has_action_points(self, player: str) -> bool:
        """Check if player has action points remaining."""
        return self.remaining_action_points.get(player, 0) > 0

    @property
    def actions_left(self) -> int:
        """Remaining action points for the current player."""
        return self.remaining_action_points.get(self.current_player, 0)

    def force_end_turn(self):
        """Force-end the current player's turn (skip remaining AP)."""
        if self.game_over:
            return
        self.remaining_action_points[self.current_player] = 0
        self._switch_turn()
    
    def get_turn_summary(self) -> Dict[str, Any]:
        """Get summary of current turn."""
        return {
            "turn_number": self.current_turn,
            "current_player": self.current_player,
            "phase": self.current_phase.value,
            "action_points_remaining": self.remaining_action_points.copy(),
            "total_actions_this_game": len(self.action_history),
        }
