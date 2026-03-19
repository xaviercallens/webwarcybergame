"""
Attacker action implementations for Neo-Hack v3.1.
All 8 attacker actions with probabilistic outcomes per blueprint Section 1.
"""

import random
from typing import Dict, Any

import numpy as np

from src.rl.action_space import (
    AttackerAction,
    BASE_SUCCESS_RATES,
    STEALTH_COSTS,
    DETECTION_CHANCES,
)
from src.rl.observation_space import GameState


class AttackerActionHandler:
    """
    Executes attacker actions against the game state.
    Each action has a base success rate, stealth cost, and detection chance
    that are modified by game state conditions.
    """

    @staticmethod
    def execute(action: int, game_state: GameState, target_node: int = 0) -> Dict[str, Any]:
        """
        Execute an attacker action.

        Args:
            action: AttackerAction enum value
            game_state: Current game state
            target_node: Target network node (clamped to valid range)

        Returns:
            Action result dict with success, detected, stealth_cost, details
        """
        target_node = max(0, min(target_node, game_state.num_nodes - 1))

        handlers = {
            AttackerAction.SCAN_NETWORK: AttackerActionHandler._scan_network,
            AttackerAction.EXPLOIT_VULNERABILITY: AttackerActionHandler._exploit_vulnerability,
            AttackerAction.PHISHING: AttackerActionHandler._phishing,
            AttackerAction.INSTALL_MALWARE: AttackerActionHandler._install_malware,
            AttackerAction.ELEVATE_PRIVILEGES: AttackerActionHandler._elevate_privileges,
            AttackerAction.LATERAL_MOVEMENT: AttackerActionHandler._lateral_movement,
            AttackerAction.EXFILTRATE_DATA: AttackerActionHandler._exfiltrate_data,
            AttackerAction.CLEAR_LOGS: AttackerActionHandler._clear_logs,
        }

        handler = handlers.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}"}

        return handler(game_state, target_node)

    # ------------------------------------------------------------------
    # Individual action implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _scan_network(gs: GameState, target: int) -> Dict[str, Any]:
        """Discover network topology and identify hosts."""
        action_name = "SCAN_NETWORK"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        nodes_discovered = 0
        if success:
            # Reveal a row of the real topology for the target node
            gs.attacker_discovered_topology[target] = gs.full_topology[target]
            gs.attacker_discovered_topology[:, target] = gs.full_topology[:, target]
            nodes_discovered = int(np.sum(gs.full_topology[target]))

            # Discover vulnerabilities on scanned node
            gs.attacker_scanned_vulns[target] = gs.vulnerabilities[target]

        return _build_result(action_name, success, detected, stealth_cost, {
            "nodes_discovered": nodes_discovered,
            "target": target,
        })

    @staticmethod
    def _exploit_vulnerability(gs: GameState, target: int) -> Dict[str, Any]:
        """Compromise a host using a known vulnerability."""
        action_name = "EXPLOIT_VULNERABILITY"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        # Modifiers
        if gs.patched_nodes[target]:
            success_rate *= 0.3  # Much harder if patched
        if gs.isolated_nodes[target]:
            success_rate *= 0.1  # Nearly impossible if isolated
        if gs.attacker_scanned_vulns[target] > 0:
            success_rate = min(1.0, success_rate * 1.2)  # Easier with vuln knowledge

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        if success:
            gs.compromised_nodes[target] = 1
            gs.attacker_owned_nodes[target] = 1

        return _build_result(action_name, success, detected, stealth_cost, {
            "target": target,
            "was_patched": bool(gs.patched_nodes[target]),
        })

    @staticmethod
    def _phishing(gs: GameState, target: int) -> Dict[str, Any]:
        """Social engineering attack to gain credentials."""
        action_name = "PHISHING"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        # Harder against already-compromised targets (users warned)
        if gs.defender_detected_compromises[target]:
            success_rate *= 0.5

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        if success:
            gs.compromised_nodes[target] = 1
            gs.attacker_owned_nodes[target] = 1

        return _build_result(action_name, success, detected, stealth_cost, {
            "target": target,
        })

    @staticmethod
    def _install_malware(gs: GameState, target: int) -> Dict[str, Any]:
        """Install persistent malware on compromised host."""
        action_name = "INSTALL_MALWARE"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        # Must own the node first
        if not gs.attacker_owned_nodes[target]:
            return _build_result(action_name, False, False, stealth_cost, {
                "target": target,
                "error": "Must own node to install malware",
            })

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        malware_installed = False
        if success:
            malware_installed = True
            # Malware makes the node harder to clean
            gs.vulnerabilities[target] = max(gs.vulnerabilities[target], 2)

        return _build_result(action_name, success, detected, stealth_cost, {
            "target": target,
            "malware_installed": malware_installed,
        })

    @staticmethod
    def _elevate_privileges(gs: GameState, target: int) -> Dict[str, Any]:
        """Escalate privileges to admin access."""
        action_name = "ELEVATE_PRIVILEGES"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        # Must own the node
        if not gs.attacker_owned_nodes[target]:
            return _build_result(action_name, False, False, stealth_cost, {
                "target": target,
                "error": "Must own node to escalate privileges",
            })

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        return _build_result(action_name, success, detected, stealth_cost, {
            "target": target,
            "privileges_escalated": success,
        })

    @staticmethod
    def _lateral_movement(gs: GameState, target: int) -> Dict[str, Any]:
        """Move to adjacent network segment."""
        action_name = "LATERAL_MOVEMENT"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        # Need at least one owned node adjacent to target
        has_adjacent_owned = False
        for i in range(gs.num_nodes):
            if gs.attacker_owned_nodes[i] and gs.full_topology[i, target]:
                has_adjacent_owned = True
                break

        if not has_adjacent_owned and not gs.attacker_owned_nodes[target]:
            # Can still attempt but much lower chance
            success_rate *= 0.2

        if gs.isolated_nodes[target]:
            success_rate *= 0.05  # Isolated nodes are nearly unreachable

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        if success:
            gs.compromised_nodes[target] = 1
            gs.attacker_owned_nodes[target] = 1
            # Discover topology around new node
            gs.attacker_discovered_topology[target] = gs.full_topology[target]

        return _build_result(action_name, success, detected, stealth_cost, {
            "target": target,
            "had_adjacent_owned": has_adjacent_owned,
        })

    @staticmethod
    def _exfiltrate_data(gs: GameState, target: int) -> Dict[str, Any]:
        """Steal sensitive data from compromised hosts."""
        action_name = "EXFILTRATE_DATA"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        if not gs.attacker_owned_nodes[target]:
            return _build_result(action_name, False, False, stealth_cost, {
                "target": target,
                "error": "Must own node to exfiltrate data",
            })

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        data_value = 0
        if success:
            data_value = int(10 + gs.vulnerabilities[target] * 5)
            if not hasattr(gs, "data_exfiltrated"):
                gs.data_exfiltrated = 0
            gs.data_exfiltrated += data_value

        return _build_result(action_name, success, detected, stealth_cost, {
            "target": target,
            "data_value": data_value,
        })

    @staticmethod
    def _clear_logs(gs: GameState, target: int) -> Dict[str, Any]:
        """Remove evidence of attack from logs."""
        action_name = "CLEAR_LOGS"
        success_rate = BASE_SUCCESS_RATES[action_name]
        stealth_cost = STEALTH_COSTS[action_name]
        detection_chance = DETECTION_CHANCES[action_name]

        if not gs.attacker_owned_nodes[target]:
            return _build_result(action_name, False, False, stealth_cost, {
                "target": target,
                "error": "Must own node to clear logs",
            })

        success = random.random() < success_rate
        detected = random.random() < detection_chance

        alert_reduced = 0
        if success:
            # Reduce alert level
            alert_reduced = min(gs.alert_level, 15)
            gs.alert_level = max(0, gs.alert_level - alert_reduced)
            # May clear defender detection on this node
            if random.random() < 0.5:
                gs.defender_detected_compromises[target] = 0

        return _build_result(action_name, success, detected, stealth_cost, {
            "target": target,
            "alert_reduced": alert_reduced,
        })


def _build_result(
    action_name: str,
    success: bool,
    detected: bool,
    stealth_cost: int,
    details: Dict[str, Any],
) -> Dict[str, Any]:
    """Build standardized action result dict."""
    return {
        "action": action_name,
        "success": success,
        "detected": detected,
        "stealth_cost": stealth_cost,
        "details": details,
    }
