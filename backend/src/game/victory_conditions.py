"""
Victory conditions and win/loss logic for Neo-Hack v3.1.
Defines scenario objectives and victory criteria.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import numpy as np


class VictoryType(Enum):
    """Types of victory conditions."""
    ATTACKER_COMPROMISE = "attacker_compromise"
    ATTACKER_EXFILTRATE = "attacker_exfiltrate"
    DEFENDER_DETECTION = "defender_detection"
    DEFENDER_CONTAINMENT = "defender_containment"
    TIME_LIMIT = "time_limit"


class VictoryCondition:
    """
    Represents a single victory condition.
    """
    
    def __init__(
        self,
        condition_type: VictoryType,
        winner: str,
        threshold: int,
        description: str
    ):
        """
        Initialize victory condition.
        
        Args:
            condition_type: Type of victory condition
            winner: "attacker" or "defender"
            threshold: Threshold value for condition
            description: Human-readable description
        """
        self.condition_type = condition_type
        self.winner = winner
        self.threshold = threshold
        self.description = description
    
    def check(self, game_state: Any) -> bool:
        """
        Check if this victory condition is met.
        
        Args:
            game_state: Current game state
        
        Returns:
            True if condition is met
        """
        if self.condition_type == VictoryType.ATTACKER_COMPROMISE:
            owned_count = np.sum(game_state.attacker_owned_nodes)
            return owned_count >= self.threshold
        
        elif self.condition_type == VictoryType.ATTACKER_EXFILTRATE:
            # Check if attacker has exfiltrated enough data
            return getattr(game_state, "data_exfiltrated", 0) >= self.threshold
        
        elif self.condition_type == VictoryType.DEFENDER_DETECTION:
            return game_state.alert_level >= self.threshold
        
        elif self.condition_type == VictoryType.DEFENDER_CONTAINMENT:
            # Check if defender has isolated enough nodes
            isolated_count = np.sum(game_state.isolated_nodes)
            return isolated_count >= self.threshold
        
        elif self.condition_type == VictoryType.TIME_LIMIT:
            # Time limit is checked separately
            return False
        
        return False


class ScenarioObjectives:
    """
    Manages scenario objectives and victory conditions.
    
    Blueprint Alignment: Section 1 (Core Mechanics)
    """
    
    def __init__(self, scenario: Optional[Dict[str, Any]] = None):
        """
        Initialize scenario objectives.
        
        Args:
            scenario: Scenario configuration dict
        """
        self.scenario = scenario or {}
        self.objectives = []
        self.completed_objectives = []
        self._setup_objectives()
    
    def _setup_objectives(self) -> None:
        """Set up objectives based on scenario."""
        scenario_type = self.scenario.get("type", "default")
        
        if scenario_type == "default":
            self._setup_default_objectives()
        elif scenario_type == "capture_flag":
            self._setup_capture_flag_objectives()
        elif scenario_type == "survival":
            self._setup_survival_objectives()
    
    def _setup_default_objectives(self) -> None:
        """Set up default scenario objectives."""
        num_nodes = self.scenario.get("num_nodes", 10)
        
        # Attacker objectives
        self.objectives.append(
            VictoryCondition(
                VictoryType.ATTACKER_COMPROMISE,
                "attacker",
                int(num_nodes * 0.5),
                f"Compromise {int(num_nodes * 0.5)} nodes"
            )
        )
        
        # Defender objectives
        self.objectives.append(
            VictoryCondition(
                VictoryType.DEFENDER_DETECTION,
                "defender",
                100,
                "Raise alert level to 100"
            )
        )
    
    def _setup_capture_flag_objectives(self) -> None:
        """Set up capture the flag scenario objectives."""
        self.objectives.append(
            VictoryCondition(
                VictoryType.ATTACKER_EXFILTRATE,
                "attacker",
                100,
                "Exfiltrate 100 units of data"
            )
        )
        
        self.objectives.append(
            VictoryCondition(
                VictoryType.DEFENDER_CONTAINMENT,
                "defender",
                5,
                "Isolate 5 compromised nodes"
            )
        )
    
    def _setup_survival_objectives(self) -> None:
        """Set up survival scenario objectives."""
        self.objectives.append(
            VictoryCondition(
                VictoryType.ATTACKER_COMPROMISE,
                "attacker",
                3,
                "Compromise 3 critical nodes"
            )
        )
        
        self.objectives.append(
            VictoryCondition(
                VictoryType.DEFENDER_DETECTION,
                "defender",
                80,
                "Maintain alert level above 80 for 5 turns"
            )
        )
    
    def check_objectives(self, game_state: Any) -> Dict[str, Any]:
        """
        Check all objectives against current game state.
        
        Args:
            game_state: Current game state
        
        Returns:
            Dict with objective status
        """
        results = {
            "attacker_objectives_met": [],
            "defender_objectives_met": [],
            "game_won": False,
            "winner": None,
        }
        
        for objective in self.objectives:
            if objective.check(game_state):
                if objective.winner == "attacker":
                    results["attacker_objectives_met"].append(objective.description)
                    results["game_won"] = True
                    results["winner"] = "attacker"
                else:
                    results["defender_objectives_met"].append(objective.description)
                    results["game_won"] = True
                    results["winner"] = "defender"
        
        return results
    
    def get_objectives_status(self, game_state: Any) -> Dict[str, Any]:
        """
        Get detailed status of all objectives.
        
        Args:
            game_state: Current game state
        
        Returns:
            Detailed objective status
        """
        status = {
            "objectives": [],
            "progress": {},
        }
        
        for objective in self.objectives:
            obj_status = {
                "description": objective.description,
                "type": objective.condition_type.value,
                "winner": objective.winner,
                "threshold": objective.threshold,
                "met": objective.check(game_state),
            }
            
            # Calculate progress
            if objective.condition_type == VictoryType.ATTACKER_COMPROMISE:
                owned = np.sum(game_state.attacker_owned_nodes)
                obj_status["progress"] = owned / objective.threshold
            elif objective.condition_type == VictoryType.DEFENDER_DETECTION:
                obj_status["progress"] = game_state.alert_level / objective.threshold
            
            status["objectives"].append(obj_status)
        
        return status
    
    def get_attacker_objectives(self) -> List[str]:
        """Get attacker objectives."""
        return [
            obj.description for obj in self.objectives
            if obj.winner == "attacker"
        ]
    
    def get_defender_objectives(self) -> List[str]:
        """Get defender objectives."""
        return [
            obj.description for obj in self.objectives
            if obj.winner == "defender"
        ]


class GameEndConditions:
    """
    Manages all game end conditions.
    Determines when and why a game ends.
    """
    
    def __init__(self, max_turns: int = 50):
        """
        Initialize game end conditions.
        
        Args:
            max_turns: Maximum turns before time limit
        """
        self.max_turns = max_turns
    
    def check_game_end(
        self,
        game_state: Any,
        current_turn: int,
        objectives: ScenarioObjectives
    ) -> Dict[str, Any]:
        """
        Check if game should end.
        
        Args:
            game_state: Current game state
            current_turn: Current turn number
            objectives: Scenario objectives
        
        Returns:
            Game end dict with winner and reason
        """
        result = {
            "game_over": False,
            "winner": None,
            "reason": None,
        }
        
        # Check objectives
        obj_results = objectives.check_objectives(game_state)
        if obj_results["game_won"]:
            result["game_over"] = True
            result["winner"] = obj_results["winner"]
            result["reason"] = "Objective achieved"
            return result
        
        # Check time limit
        if current_turn >= self.max_turns:
            result["game_over"] = True
            result["reason"] = "Time limit reached"
            
            # Determine winner by score
            owned_count = np.sum(game_state.attacker_owned_nodes)
            if owned_count > game_state.num_nodes * 0.3:
                result["winner"] = "attacker"
            else:
                result["winner"] = "defender"
            
            return result
        
        # Check alert level max
        if game_state.alert_level >= 100:
            result["game_over"] = True
            result["winner"] = "defender"
            result["reason"] = "Attacker detected and caught"
            return result
        
        return result
    
    def get_game_score(self, game_state: Any) -> Dict[str, int]:
        """
        Calculate game scores for both players.
        
        Args:
            game_state: Current game state
        
        Returns:
            Score dict
        """
        attacker_score = 0
        defender_score = 0
        
        # Attacker points
        owned_count = np.sum(game_state.attacker_owned_nodes)
        attacker_score += owned_count * 10
        
        # Defender points
        detected_count = np.sum(game_state.defender_detected_compromises)
        defender_score += detected_count * 15
        
        # Alert level affects defender score
        defender_score += game_state.alert_level
        
        return {
            "attacker": attacker_score,
            "defender": defender_score,
        }
