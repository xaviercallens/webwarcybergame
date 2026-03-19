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
from .actions import ActionExecutor, AttackerActionHandler, DefenderActionHandler
from .replay_recorder import ReplayRecorder

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
    "ActionExecutor",
    "AttackerActionHandler",
    "DefenderActionHandler",
    "ReplayRecorder",
]
