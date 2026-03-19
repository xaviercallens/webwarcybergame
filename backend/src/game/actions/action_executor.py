"""
Unified action executor for Neo-Hack v3.1.
Routes actions to the appropriate handler and applies stealth/detection logic.

Blueprint Alignment: Section 1 (Core Mechanics) - Probabilistic Action Execution
"""

from typing import Dict, Any, Optional

from src.rl.action_space import AttackerAction, DefenderAction, STEALTH_COSTS
from src.rl.observation_space import GameState
from src.game.detection_engine import StealthAlertSystem
from src.game.resources import ResourceManager, ActionCostCalculator

from .attacker_actions import AttackerActionHandler
from .defender_actions import DefenderActionHandler


class ActionExecutor:
    """
    Central action executor that:
    1. Validates action feasibility (resources, action points)
    2. Delegates to role-specific handler
    3. Applies stealth/alert consequences
    4. Returns unified result
    """

    def __init__(
        self,
        stealth_system: Optional[StealthAlertSystem] = None,
        resource_manager: Optional[ResourceManager] = None,
    ):
        self.stealth_system = stealth_system or StealthAlertSystem()
        self.resource_manager = resource_manager or ResourceManager()
        self.attacker_handler = AttackerActionHandler()
        self.defender_handler = DefenderActionHandler()

    def execute(
        self,
        player: str,
        action: int,
        game_state: GameState,
        target_node: int = 0,
    ) -> Dict[str, Any]:
        """
        Execute a player action with full game logic.

        Args:
            player: "attacker" or "defender"
            action: Action ID (AttackerAction or DefenderAction enum value)
            game_state: Current game state
            target_node: Target network node

        Returns:
            Unified action result dict
        """
        if player == "attacker":
            return self._execute_attacker(action, game_state, target_node)
        elif player == "defender":
            return self._execute_defender(action, game_state, target_node)
        else:
            raise ValueError(f"Unknown player: {player}")

    def _execute_attacker(
        self, action: int, gs: GameState, target_node: int
    ) -> Dict[str, Any]:
        """Execute attacker action with stealth consequences."""
        # Get action name for resource/cost lookup
        from src.rl.action_space import get_attacker_action_name
        action_name = get_attacker_action_name(action)

        # Check resource affordability
        attacker_res = self.resource_manager.get_attacker_resources()
        if not ActionCostCalculator.can_afford_action(action_name, attacker_res):
            return {
                "action": action_name,
                "success": False,
                "detected": False,
                "stealth_cost": 0,
                "details": {"error": f"Cannot afford action: {action_name}"},
                "alert_update": None,
            }

        # Consume resources
        cost_info = ActionCostCalculator.get_action_cost(action_name)
        if cost_info["resource"] == "exploit_kits":
            self.resource_manager.use_attacker_exploit()
        elif cost_info["resource"] == "malware_payloads":
            self.resource_manager.use_attacker_malware()

        # Execute the action
        result = self.attacker_handler.execute(action, gs, target_node)

        # Apply stealth consequences
        stealth_cost = result.get("stealth_cost", 0)
        alert_update = self.stealth_system.raise_alert(stealth_cost, location=target_node)

        # Sync alert level to game state
        gs.alert_level = self.stealth_system.alert_level

        # Record detection event
        if result.get("detected", False):
            self.stealth_system.record_detection(action_name, target_node, True)
            gs.defender_detected_compromises[target_node] = 1

        result["alert_update"] = alert_update
        return result

    def _execute_defender(
        self, action: int, gs: GameState, target_node: int
    ) -> Dict[str, Any]:
        """Execute defender action with resource consumption."""
        from src.rl.action_space import get_defender_action_name
        action_name = get_defender_action_name(action)

        # Check resource affordability
        defender_res = self.resource_manager.get_defender_resources()
        if not ActionCostCalculator.can_afford_action(action_name, defender_res):
            return {
                "action": action_name,
                "success": False,
                "detected": False,
                "stealth_cost": 0,
                "details": {"error": f"Cannot afford action: {action_name}"},
                "alert_update": None,
            }

        # Consume resources
        cost_info = ActionCostCalculator.get_action_cost(action_name)
        if cost_info["resource"] == "patches_available":
            self.resource_manager.use_defender_patch()
        elif cost_info["resource"] == "scan_bandwidth":
            self.resource_manager.use_defender_scan()
        elif cost_info["resource"] == "ir_budget":
            self.resource_manager.spend_defender_ir_budget(cost_info["cost"])

        # Execute the action
        result = self.defender_handler.execute(action, gs, target_node)

        # Sync alert level from game state (incident response may change it)
        self.stealth_system.alert_level = gs.alert_level

        result["alert_update"] = {"alert_level": gs.alert_level}
        return result

    def get_valid_actions(self, player: str, game_state: GameState) -> list:
        """
        Get list of valid actions for a player given current resources.

        Args:
            player: "attacker" or "defender"
            game_state: Current game state

        Returns:
            List of valid action IDs
        """
        if player == "attacker":
            from src.rl.action_space import ATTACKER_ACTIONS
            resources = self.resource_manager.get_attacker_resources()
            return [
                aid for aid, name in ATTACKER_ACTIONS.items()
                if ActionCostCalculator.can_afford_action(name, resources)
            ]
        else:
            from src.rl.action_space import DEFENDER_ACTIONS
            resources = self.resource_manager.get_defender_resources()
            return [
                aid for aid, name in DEFENDER_ACTIONS.items()
                if ActionCostCalculator.can_afford_action(name, resources)
            ]

    def reset(self) -> None:
        """Reset executor state for new game."""
        self.stealth_system.reset()
        self.resource_manager.reset()
