"""
Defender action implementations for Neo-Hack v3.1.
All 7 defender actions with probabilistic outcomes per blueprint Section 1.
"""

import random
from typing import Dict, Any

import numpy as np

from src.rl.action_space import DefenderAction
from src.rl.observation_space import GameState


class DefenderActionHandler:
    """
    Executes defender actions against the game state.
    Defender actions focus on detection, mitigation, and containment.
    """

    @staticmethod
    def execute(action: int, game_state: GameState, target_node: int = 0) -> Dict[str, Any]:
        """
        Execute a defender action.

        Args:
            action: DefenderAction enum value
            game_state: Current game state
            target_node: Target network node (clamped to valid range)

        Returns:
            Action result dict
        """
        target_node = max(0, min(target_node, game_state.num_nodes - 1))

        handlers = {
            DefenderAction.MONITOR_LOGS: DefenderActionHandler._monitor_logs,
            DefenderAction.SCAN_FOR_MALWARE: DefenderActionHandler._scan_for_malware,
            DefenderAction.APPLY_PATCH: DefenderActionHandler._apply_patch,
            DefenderAction.ISOLATE_HOST: DefenderActionHandler._isolate_host,
            DefenderAction.RESTORE_BACKUP: DefenderActionHandler._restore_backup,
            DefenderAction.FIREWALL_RULE: DefenderActionHandler._firewall_rule,
            DefenderAction.INCIDENT_RESPONSE: DefenderActionHandler._incident_response,
        }

        handler = handlers.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}"}

        return handler(game_state, target_node)

    # ------------------------------------------------------------------
    # Individual action implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _monitor_logs(gs: GameState, target: int) -> Dict[str, Any]:
        """Check system logs for suspicious activity."""
        # Detection chance increases with alert level
        base_detection = 0.3 + (gs.alert_level / 100.0) * 0.4

        compromised_found = []
        # Check target and adjacent nodes
        nodes_to_check = [target]
        for i in range(gs.num_nodes):
            if gs.full_topology[target, i]:
                nodes_to_check.append(i)

        for node in nodes_to_check:
            if gs.compromised_nodes[node] and random.random() < base_detection:
                gs.defender_detected_compromises[node] = 1
                compromised_found.append(node)

        return {
            "action": "MONITOR_LOGS",
            "success": len(compromised_found) > 0,
            "detected": False,
            "stealth_cost": 0,
            "details": {
                "target": target,
                "nodes_checked": len(nodes_to_check),
                "compromised_found": compromised_found,
            },
        }

    @staticmethod
    def _scan_for_malware(gs: GameState, target: int) -> Dict[str, Any]:
        """Scan hosts for malware infections."""
        scan_success = 0.6 + (gs.alert_level / 100.0) * 0.2

        malware_found = []
        # Scan target node
        if gs.compromised_nodes[target] and random.random() < scan_success:
            gs.defender_detected_compromises[target] = 1
            malware_found.append(target)

        # Bonus: check if vulnerability level is high (indicates malware)
        if gs.vulnerabilities[target] >= 2 and random.random() < scan_success:
            gs.discovered_vulns[target] = gs.vulnerabilities[target]

        return {
            "action": "SCAN_FOR_MALWARE",
            "success": len(malware_found) > 0,
            "detected": False,
            "stealth_cost": 0,
            "details": {
                "target": target,
                "malware_found": malware_found,
                "vulns_discovered": bool(gs.discovered_vulns[target]),
            },
        }

    @staticmethod
    def _apply_patch(gs: GameState, target: int) -> Dict[str, Any]:
        """Apply security patches to fix vulnerabilities."""
        already_patched = bool(gs.patched_nodes[target])

        gs.patched_nodes[target] = 1
        gs.vulnerabilities[target] = max(0, gs.vulnerabilities[target] - 1)

        # If node was compromised and patched, chance to remove compromise
        removed_compromise = False
        if gs.compromised_nodes[target] and random.random() < 0.4:
            gs.compromised_nodes[target] = 0
            gs.attacker_owned_nodes[target] = 0
            removed_compromise = True

        return {
            "action": "APPLY_PATCH",
            "success": True,
            "detected": False,
            "stealth_cost": 0,
            "details": {
                "target": target,
                "already_patched": already_patched,
                "removed_compromise": removed_compromise,
            },
        }

    @staticmethod
    def _isolate_host(gs: GameState, target: int) -> Dict[str, Any]:
        """Quarantine a host from network."""
        gs.isolated_nodes[target] = 1

        # Severed connections prevent lateral movement
        # The topology stays, but isolated flag blocks traversal

        return {
            "action": "ISOLATE_HOST",
            "success": True,
            "detected": False,
            "stealth_cost": 0,
            "details": {
                "target": target,
                "was_compromised": bool(gs.compromised_nodes[target]),
            },
        }

    @staticmethod
    def _restore_backup(gs: GameState, target: int) -> Dict[str, Any]:
        """Restore system from clean backup."""
        was_compromised = bool(gs.compromised_nodes[target])

        # Restore cleans the node completely
        gs.compromised_nodes[target] = 0
        gs.attacker_owned_nodes[target] = 0
        gs.vulnerabilities[target] = 0
        gs.patched_nodes[target] = 1
        gs.isolated_nodes[target] = 0  # Un-isolate after restore

        return {
            "action": "RESTORE_BACKUP",
            "success": True,
            "detected": False,
            "stealth_cost": 0,
            "details": {
                "target": target,
                "was_compromised": was_compromised,
                "node_cleaned": True,
            },
        }

    @staticmethod
    def _firewall_rule(gs: GameState, target: int) -> Dict[str, Any]:
        """Add firewall rule to block connections to/from a node."""
        # Reduces connectivity — attacker lateral movement harder
        blocked_connections = 0
        for i in range(gs.num_nodes):
            if gs.full_topology[target, i] and random.random() < 0.5:
                # Firewall blocks some connections
                blocked_connections += 1

        # Increase detection chance on this node
        gs.discovered_vulns[target] = max(gs.discovered_vulns[target], 1)

        return {
            "action": "FIREWALL_RULE",
            "success": True,
            "detected": False,
            "stealth_cost": 0,
            "details": {
                "target": target,
                "blocked_connections": blocked_connections,
            },
        }

    @staticmethod
    def _incident_response(gs: GameState, target: int) -> Dict[str, Any]:
        """Active countermeasure against ongoing attack."""
        # Most powerful action — scans widely and cleans aggressively
        compromised_found = []
        compromised_cleaned = []

        for node in range(gs.num_nodes):
            # High detection rate
            if gs.compromised_nodes[node] and random.random() < 0.7:
                gs.defender_detected_compromises[node] = 1
                compromised_found.append(node)

                # Chance to clean each detected compromise
                if random.random() < 0.4:
                    gs.compromised_nodes[node] = 0
                    gs.attacker_owned_nodes[node] = 0
                    compromised_cleaned.append(node)

        # Boost alert level (defender is now fully engaged)
        gs.alert_level = min(100, gs.alert_level + 20)

        return {
            "action": "INCIDENT_RESPONSE",
            "success": len(compromised_found) > 0,
            "detected": False,
            "stealth_cost": 0,
            "details": {
                "compromised_found": compromised_found,
                "compromised_cleaned": compromised_cleaned,
                "alert_level": gs.alert_level,
            },
        }
