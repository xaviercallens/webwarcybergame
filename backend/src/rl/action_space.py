"""
Action space definitions for Neo-Hack v3.1 game.
Defines all attacker and defender actions per blueprint Section 1.
"""

from enum import IntEnum
from typing import Dict, List


class AttackerAction(IntEnum):
    """Attacker action space - 8 actions per blueprint."""
    SCAN_NETWORK = 0
    EXPLOIT_VULNERABILITY = 1
    PHISHING = 2
    INSTALL_MALWARE = 3
    ELEVATE_PRIVILEGES = 4
    LATERAL_MOVEMENT = 5
    EXFILTRATE_DATA = 6
    CLEAR_LOGS = 7


class DefenderAction(IntEnum):
    """Defender action space - 7 actions per blueprint."""
    MONITOR_LOGS = 0
    SCAN_FOR_MALWARE = 1
    APPLY_PATCH = 2
    ISOLATE_HOST = 3
    RESTORE_BACKUP = 4
    FIREWALL_RULE = 5
    INCIDENT_RESPONSE = 6


ATTACKER_ACTIONS: Dict[int, str] = {
    AttackerAction.SCAN_NETWORK: "SCAN_NETWORK",
    AttackerAction.EXPLOIT_VULNERABILITY: "EXPLOIT_VULNERABILITY",
    AttackerAction.PHISHING: "PHISHING",
    AttackerAction.INSTALL_MALWARE: "INSTALL_MALWARE",
    AttackerAction.ELEVATE_PRIVILEGES: "ELEVATE_PRIVILEGES",
    AttackerAction.LATERAL_MOVEMENT: "LATERAL_MOVEMENT",
    AttackerAction.EXFILTRATE_DATA: "EXFILTRATE_DATA",
    AttackerAction.CLEAR_LOGS: "CLEAR_LOGS",
}

DEFENDER_ACTIONS: Dict[int, str] = {
    DefenderAction.MONITOR_LOGS: "MONITOR_LOGS",
    DefenderAction.SCAN_FOR_MALWARE: "SCAN_FOR_MALWARE",
    DefenderAction.APPLY_PATCH: "APPLY_PATCH",
    DefenderAction.ISOLATE_HOST: "ISOLATE_HOST",
    DefenderAction.RESTORE_BACKUP: "RESTORE_BACKUP",
    DefenderAction.FIREWALL_RULE: "FIREWALL_RULE",
    DefenderAction.INCIDENT_RESPONSE: "INCIDENT_RESPONSE",
}

ACTION_DESCRIPTIONS = {
    "SCAN_NETWORK": "Discover network topology and identify hosts",
    "EXPLOIT_VULNERABILITY": "Compromise a host using known vulnerability",
    "PHISHING": "Social engineering attack to gain credentials",
    "INSTALL_MALWARE": "Install persistent malware on compromised host",
    "ELEVATE_PRIVILEGES": "Escalate privileges to admin access",
    "LATERAL_MOVEMENT": "Move to adjacent network segment",
    "EXFILTRATE_DATA": "Steal sensitive data from compromised hosts",
    "CLEAR_LOGS": "Remove evidence of attack from logs",
    "MONITOR_LOGS": "Check system logs for suspicious activity",
    "SCAN_FOR_MALWARE": "Scan hosts for malware infections",
    "APPLY_PATCH": "Apply security patches to fix vulnerabilities",
    "ISOLATE_HOST": "Quarantine a host from network",
    "RESTORE_BACKUP": "Restore system from clean backup",
    "FIREWALL_RULE": "Add firewall rule to block connections",
    "INCIDENT_RESPONSE": "Active countermeasure against ongoing attack",
}

ACTION_COSTS = {
    "SCAN_NETWORK": 1,
    "EXPLOIT_VULNERABILITY": 2,
    "PHISHING": 1,
    "INSTALL_MALWARE": 2,
    "ELEVATE_PRIVILEGES": 2,
    "LATERAL_MOVEMENT": 1,
    "EXFILTRATE_DATA": 3,
    "CLEAR_LOGS": 1,
    "MONITOR_LOGS": 1,
    "SCAN_FOR_MALWARE": 1,
    "APPLY_PATCH": 2,
    "ISOLATE_HOST": 1,
    "RESTORE_BACKUP": 3,
    "FIREWALL_RULE": 1,
    "INCIDENT_RESPONSE": 2,
}

STEALTH_COSTS = {
    "SCAN_NETWORK": 5,
    "EXPLOIT_VULNERABILITY": 30,
    "PHISHING": 15,
    "INSTALL_MALWARE": 35,
    "ELEVATE_PRIVILEGES": 25,
    "LATERAL_MOVEMENT": 40,
    "EXFILTRATE_DATA": 50,
    "CLEAR_LOGS": 10,
}

BASE_SUCCESS_RATES = {
    "SCAN_NETWORK": 0.95,
    "EXPLOIT_VULNERABILITY": 0.70,
    "PHISHING": 0.60,
    "INSTALL_MALWARE": 0.75,
    "ELEVATE_PRIVILEGES": 0.65,
    "LATERAL_MOVEMENT": 0.80,
    "EXFILTRATE_DATA": 0.70,
    "CLEAR_LOGS": 0.85,
}

DETECTION_CHANCES = {
    "SCAN_NETWORK": 0.05,
    "EXPLOIT_VULNERABILITY": 0.40,
    "PHISHING": 0.20,
    "INSTALL_MALWARE": 0.50,
    "ELEVATE_PRIVILEGES": 0.35,
    "LATERAL_MOVEMENT": 0.45,
    "EXFILTRATE_DATA": 0.60,
    "CLEAR_LOGS": 0.15,
}


def get_attacker_action_name(action_id: int) -> str:
    """Get action name from ID."""
    return ATTACKER_ACTIONS.get(action_id, "UNKNOWN")


def get_defender_action_name(action_id: int) -> str:
    """Get action name from ID."""
    return DEFENDER_ACTIONS.get(action_id, "UNKNOWN")


def is_valid_attacker_action(action_id: int) -> bool:
    """Check if action ID is valid for attacker."""
    return action_id in ATTACKER_ACTIONS


def is_valid_defender_action(action_id: int) -> bool:
    """Check if action ID is valid for defender."""
    return action_id in DEFENDER_ACTIONS
