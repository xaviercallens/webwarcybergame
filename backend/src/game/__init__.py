"""
Game mechanics module for Neo-Hack v3.1 - Turn-based cyber warfare.
"""

from .turn_manager import TurnManager, GamePhase
from .detection_engine import StealthAlertSystem, DetectionEngine
from .resources import ResourceManager, ActionCostCalculator
from .victory_conditions import (
    VictoryCondition,
    VictoryType,
    ScenarioObjectives,
    GameEndConditions,
)

__all__ = [
    "TurnManager",
    "GamePhase",
    "StealthAlertSystem",
    "DetectionEngine",
    "ResourceManager",
    "ActionCostCalculator",
    "VictoryCondition",
    "VictoryType",
    "ScenarioObjectives",
    "GameEndConditions",
]
