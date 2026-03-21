"""
Scenario loader for Neo-Hack v3.1.
Loads and validates game scenario configurations.
"""

from typing import Dict, Any, List
from pathlib import Path
import json


# Built-in scenario definitions
DEFAULT_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "tutorial": {
        "name": "Tutorial - First Breach",
        "description": "Simple 5-node network. Learn the basics of attack and defense.",
        "type": "default",
        "num_nodes": 5,
        "max_turns": 20,
        "attacker_action_points": 1,
        "defender_action_points": 1,
        "attacker_exploit_budget": 10,
        "attacker_malware_budget": 3,
        "defender_ir_budget": 100,
        "defender_patches": 5,
        "defender_scan_bandwidth": 2,
        "difficulty": "novice",
    },
    "corporate_network": {
        "name": "Corporate Network Intrusion",
        "description": "Medium 10-node corporate network with segmented zones.",
        "type": "default",
        "num_nodes": 10,
        "max_turns": 50,
        "attacker_action_points": 1,
        "defender_action_points": 1,
        "attacker_exploit_budget": 8,
        "attacker_malware_budget": 3,
        "defender_ir_budget": 80,
        "defender_patches": 5,
        "defender_scan_bandwidth": 2,
        "difficulty": "normal",
    },
    "data_center": {
        "name": "Data Center Siege",
        "description": "Large 20-node data center. High-value exfiltration target.",
        "type": "capture_flag",
        "num_nodes": 20,
        "max_turns": 80,
        "attacker_action_points": 2,
        "defender_action_points": 2,
        "attacker_exploit_budget": 12,
        "attacker_malware_budget": 5,
        "defender_ir_budget": 150,
        "defender_patches": 8,
        "defender_scan_bandwidth": 3,
        "difficulty": "normal",
    },
    "critical_infrastructure": {
        "name": "Critical Infrastructure Defense",
        "description": "30-node SCADA/ICS network. Nation-state level threat.",
        "type": "survival",
        "num_nodes": 30,
        "max_turns": 100,
        "attacker_action_points": 2,
        "defender_action_points": 1,
        "attacker_exploit_budget": 15,
        "attacker_malware_budget": 5,
        "defender_ir_budget": 200,
        "defender_patches": 10,
        "defender_scan_bandwidth": 3,
        "difficulty": "expert",
    },
}

REQUIRED_FIELDS = [
    "name", "type", "num_nodes", "max_turns",
    "attacker_action_points", "defender_action_points",
]


def load_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Load a scenario by ID.

    Args:
        scenario_id: Built-in scenario ID or path to JSON file.

    Returns:
        Scenario configuration dict.

    Raises:
        ValueError: If scenario not found or invalid.
    """
    if scenario_id in DEFAULT_SCENARIOS:
        return DEFAULT_SCENARIOS[scenario_id].copy()

    # Try loading from JSON file
    path = Path(scenario_id)
    if path.exists() and path.suffix == ".json":
        return load_scenario_from_file(str(path))

    raise ValueError(
        f"Scenario '{scenario_id}' not found. "
        f"Available: {list(DEFAULT_SCENARIOS.keys())}"
    )


def load_scenario_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load a scenario from a JSON file.

    Args:
        file_path: Path to JSON scenario file.

    Returns:
        Scenario configuration dict.
    """
    with open(file_path, "r") as f:
        scenario = json.load(f)

    validate_scenario(scenario)
    return scenario


def validate_scenario(scenario: Dict[str, Any]) -> bool:
    """
    Validate a scenario configuration.

    Args:
        scenario: Scenario dict to validate.

    Returns:
        True if valid.

    Raises:
        ValueError: If scenario is invalid.
    """
    for field in REQUIRED_FIELDS:
        if field not in scenario:
            raise ValueError(f"Missing required field: {field}")

    if scenario["num_nodes"] < 1:
        raise ValueError("num_nodes must be >= 1")

    if scenario["max_turns"] < 1:
        raise ValueError("max_turns must be >= 1")

    if scenario["type"] not in ("default", "capture_flag", "survival"):
        raise ValueError(f"Unknown scenario type: {scenario['type']}")

    return True


def list_scenarios() -> List[Dict[str, str]]:
    """
    List all available built-in scenarios.

    Returns:
        List of scenario summaries.
    """
    return [
        {
            "id": sid,
            "name": s["name"],
            "description": s["description"],
            "difficulty": s.get("difficulty", "normal"),
            "num_nodes": s["num_nodes"],
        }
        for sid, s in DEFAULT_SCENARIOS.items()
    ]


def get_scenario_for_difficulty(difficulty: str) -> Dict[str, Any]:
    """
    Get a scenario matching the requested difficulty.

    Args:
        difficulty: "novice", "normal", or "expert"

    Returns:
        Scenario config dict.
    """
    for scenario in DEFAULT_SCENARIOS.values():
        if scenario.get("difficulty") == difficulty:
            return scenario.copy()

    return DEFAULT_SCENARIOS["corporate_network"].copy()
