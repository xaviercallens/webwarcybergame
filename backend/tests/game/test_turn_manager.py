"""
Unit tests for TurnManager.
Tests turn scheduling and game flow.
"""

import pytest
from src.game.turn_manager import TurnManager, GamePhase


class TestTurnManagerBasics:
    """Test basic turn manager functionality."""
    
    def test_turn_manager_creation(self):
        """Test creating turn manager."""
        tm = TurnManager()
        assert tm.current_turn == 0
        assert tm.current_player == "attacker"
        assert tm.game_over is False
    
    def test_turn_manager_with_scenario(self):
        """Test turn manager with scenario config."""
        scenario = {
            "max_turns": 100,
            "attacker_action_points": 2,
            "defender_action_points": 1,
        }
        tm = TurnManager(scenario=scenario)
        assert tm.max_turns == 100
        assert tm.action_points["attacker"] == 2
        assert tm.action_points["defender"] == 1


class TestTurnManagerGameStart:
    """Test game start functionality."""
    
    def test_start_game(self):
        """Test starting a game."""
        tm = TurnManager()
        state = tm.start_game()
        
        assert state["phase"] == GamePhase.ATTACKER_TURN.value
        assert state["turn"] == 1
        assert state["current_player"] == "attacker"
        assert tm.current_phase == GamePhase.ATTACKER_TURN
    
    def test_start_game_action_points(self):
        """Test action points are reset on game start."""
        tm = TurnManager()
        tm.start_game()
        
        assert tm.remaining_action_points["attacker"] > 0
        assert tm.remaining_action_points["defender"] > 0


class TestTurnManagerActionProcessing:
    """Test action processing and turn switching."""
    
    def test_process_action_valid(self):
        """Test processing a valid action."""
        tm = TurnManager()
        tm.start_game()
        
        action_result = {"success": True}
        turn_switched, state = tm.process_action("attacker", 0, action_result)
        
        assert not turn_switched  # Still attacker's turn (1 AP)
        assert len(tm.action_history) == 1
    
    def test_process_action_wrong_player(self):
        """Test processing action by wrong player raises error."""
        tm = TurnManager()
        tm.start_game()
        
        with pytest.raises(ValueError):
            tm.process_action("defender", 0, {})
    
    def test_process_action_no_action_points(self):
        """Test processing action with no action points raises error."""
        tm = TurnManager()
        tm.start_game()
        tm.remaining_action_points["attacker"] = 0
        
        with pytest.raises(ValueError):
            tm.process_action("attacker", 0, {})
    
    def test_turn_switch_attacker_to_defender(self):
        """Test turn switches from attacker to defender."""
        tm = TurnManager()
        tm.start_game()
        
        # Attacker uses all action points
        turn_switched, state = tm.process_action("attacker", 0, {})
        
        assert turn_switched is False  # Single AP per turn
        assert tm.current_player == "defender"
        assert tm.current_phase == GamePhase.DEFENDER_TURN
    
    def test_turn_switch_defender_to_attacker(self):
        """Test turn switches from defender back to attacker."""
        tm = TurnManager()
        tm.start_game()
        
        # Attacker's turn
        tm.process_action("attacker", 0, {})
        
        # Defender's turn
        turn_switched, state = tm.process_action("defender", 0, {})
        
        assert turn_switched is True  # Full round completed
        assert tm.current_player == "attacker"
        assert tm.current_turn == 2


class TestTurnManagerGameOver:
    """Test game over conditions."""
    
    def test_game_over_on_max_turns(self):
        """Test game ends when max turns reached."""
        tm = TurnManager(scenario={"max_turns": 2})
        tm.start_game()
        
        # Play until max turns
        for _ in range(4):
            tm.process_action(tm.current_player, 0, {})
        
        assert tm.game_over is True
        assert tm.current_phase == GamePhase.GAME_OVER
    
    def test_end_game(self):
        """Test ending game manually."""
        tm = TurnManager()
        tm.start_game()
        
        result = tm.end_game(winner="attacker")
        
        assert result["game_over"] is True
        assert result["winner"] == "attacker"
        assert tm.game_over is True


class TestTurnManagerActionHistory:
    """Test action history tracking."""
    
    def test_action_history_recorded(self):
        """Test actions are recorded in history."""
        tm = TurnManager()
        tm.start_game()
        
        tm.process_action("attacker", 0, {"success": True})
        tm.process_action("defender", 1, {"success": False})
        
        assert len(tm.action_history) == 2
        assert tm.action_history[0]["player"] == "attacker"
        assert tm.action_history[1]["player"] == "defender"
    
    def test_action_history_contains_details(self):
        """Test action history contains action details."""
        tm = TurnManager()
        tm.start_game()
        
        result = {"success": True, "target": 5}
        tm.process_action("attacker", 0, result)
        
        recorded = tm.action_history[0]
        assert recorded["action"] == 0
        assert recorded["result"]["success"] is True


class TestTurnManagerState:
    """Test state management."""
    
    def test_get_state(self):
        """Test getting current state."""
        tm = TurnManager()
        tm.start_game()
        
        state = tm.get_state()
        
        assert "phase" in state
        assert "turn" in state
        assert "current_player" in state
        assert "action_points" in state
    
    def test_get_turn_summary(self):
        """Test getting turn summary."""
        tm = TurnManager()
        tm.start_game()
        
        summary = tm.get_turn_summary()
        
        assert "turn_number" in summary
        assert "current_player" in summary
        assert "action_points_remaining" in summary


class TestTurnManagerMultipleActionPoints:
    """Test with multiple action points per turn."""
    
    def test_multiple_action_points(self):
        """Test turn with multiple action points."""
        scenario = {
            "attacker_action_points": 2,
            "defender_action_points": 2,
        }
        tm = TurnManager(scenario=scenario)
        tm.start_game()
        
        # First action
        turn_switched, _ = tm.process_action("attacker", 0, {})
        assert turn_switched is False
        assert tm.current_player == "attacker"
        
        # Second action
        turn_switched, _ = tm.process_action("attacker", 0, {})
        assert turn_switched is False
        assert tm.current_player == "defender"


class TestTurnManagerEdgeCases:
    """Test edge cases."""
    
    def test_game_over_prevents_actions(self):
        """Test actions are prevented when game is over."""
        tm = TurnManager()
        tm.start_game()
        tm.end_game()
        
        with pytest.raises(RuntimeError):
            tm.process_action("attacker", 0, {})
    
    def test_zero_max_turns(self):
        """Test with zero max turns."""
        tm = TurnManager(scenario={"max_turns": 0})
        tm.start_game()
        
        # Attacker plays, switches to defender
        tm.process_action("attacker", 0, {})
        # Defender plays, full round completes, turn increments to 2 > 0
        tm.process_action("defender", 0, {})
        assert tm.game_over is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
