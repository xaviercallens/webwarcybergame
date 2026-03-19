"""
Resource management for Neo-Hack v3.1.
Tracks attacker and defender resources and constraints.
"""

from typing import Dict, Any, Optional


class ResourceManager:
    """
    Manages game resources for both players.
    Enforces resource constraints on actions.
    
    Blueprint Alignment: Section 1 (Core Mechanics)
    """
    
    def __init__(self, scenario: Optional[Dict[str, Any]] = None):
        """
        Initialize resource manager.
        
        Args:
            scenario: Optional scenario configuration
        """
        self.scenario = scenario or {}
        
        # Attacker resources
        self.attacker_resources = {
            "exploit_kits": scenario.get("attacker_exploit_budget", 10) if scenario else 10,
            "malware_payloads": scenario.get("attacker_malware_budget", 3) if scenario else 3,
            "time_remaining": scenario.get("max_turns", 50) if scenario else 50,
        }
        
        # Defender resources
        self.defender_resources = {
            "ir_budget": scenario.get("defender_ir_budget", 100) if scenario else 100,
            "patches_available": scenario.get("defender_patches", 5) if scenario else 5,
            "scan_bandwidth": scenario.get("defender_scan_bandwidth", 2) if scenario else 2,
        }
        
        # Track resource usage
        self.attacker_usage = {
            "exploits_used": 0,
            "malware_deployed": 0,
            "turns_used": 0,
        }
        
        self.defender_usage = {
            "ir_spent": 0,
            "patches_used": 0,
            "scans_performed": 0,
        }
    
    def can_attacker_exploit(self) -> bool:
        """Check if attacker has exploits remaining."""
        return self.attacker_resources["exploit_kits"] > 0
    
    def can_attacker_deploy_malware(self) -> bool:
        """Check if attacker has malware payloads remaining."""
        return self.attacker_resources["malware_payloads"] > 0
    
    def can_defender_patch(self) -> bool:
        """Check if defender has patches remaining."""
        return self.defender_resources["patches_available"] > 0
    
    def can_defender_scan(self) -> bool:
        """Check if defender has scan bandwidth remaining."""
        return self.defender_resources["scan_bandwidth"] > 0
    
    def use_attacker_exploit(self) -> bool:
        """
        Use one attacker exploit kit.
        
        Returns:
            True if successful, False if no exploits available
        """
        if self.can_attacker_exploit():
            self.attacker_resources["exploit_kits"] -= 1
            self.attacker_usage["exploits_used"] += 1
            return True
        return False
    
    def use_attacker_malware(self) -> bool:
        """
        Use one attacker malware payload.
        
        Returns:
            True if successful, False if no payloads available
        """
        if self.can_attacker_deploy_malware():
            self.attacker_resources["malware_payloads"] -= 1
            self.attacker_usage["malware_deployed"] += 1
            return True
        return False
    
    def use_defender_patch(self) -> bool:
        """
        Use one defender patch.
        
        Returns:
            True if successful, False if no patches available
        """
        if self.can_defender_patch():
            self.defender_resources["patches_available"] -= 1
            self.defender_usage["patches_used"] += 1
            return True
        return False
    
    def use_defender_scan(self) -> bool:
        """
        Use one defender scan.
        
        Returns:
            True if successful, False if no scans available
        """
        if self.can_defender_scan():
            self.defender_resources["scan_bandwidth"] -= 1
            self.defender_usage["scans_performed"] += 1
            return True
        return False
    
    def spend_defender_ir_budget(self, amount: int) -> bool:
        """
        Spend defender IR budget.
        
        Args:
            amount: Amount to spend
        
        Returns:
            True if successful, False if insufficient budget
        """
        if self.defender_resources["ir_budget"] >= amount:
            self.defender_resources["ir_budget"] -= amount
            self.defender_usage["ir_spent"] += amount
            return True
        return False
    
    def get_attacker_resources(self) -> Dict[str, int]:
        """Get current attacker resources."""
        return self.attacker_resources.copy()
    
    def get_defender_resources(self) -> Dict[str, int]:
        """Get current defender resources."""
        return self.defender_resources.copy()
    
    def get_attacker_usage(self) -> Dict[str, int]:
        """Get attacker resource usage statistics."""
        return self.attacker_usage.copy()
    
    def get_defender_usage(self) -> Dict[str, int]:
        """Get defender resource usage statistics."""
        return self.defender_usage.copy()
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get complete resource status."""
        return {
            "attacker": {
                "current": self.get_attacker_resources(),
                "usage": self.get_attacker_usage(),
            },
            "defender": {
                "current": self.get_defender_resources(),
                "usage": self.get_defender_usage(),
            },
        }
    
    def reset(self) -> None:
        """Reset resources to initial state."""
        self.__init__(self.scenario)


class ActionCostCalculator:
    """
    Calculates resource costs for actions.
    Determines what resources are consumed by each action.
    """
    
    # Action costs in terms of resources
    ACTION_COSTS = {
        "SCAN_NETWORK": {"cost": 1, "resource": None},
        "EXPLOIT_VULNERABILITY": {"cost": 1, "resource": "exploit_kits"},
        "PHISHING": {"cost": 1, "resource": None},
        "INSTALL_MALWARE": {"cost": 1, "resource": "malware_payloads"},
        "ELEVATE_PRIVILEGES": {"cost": 1, "resource": None},
        "LATERAL_MOVEMENT": {"cost": 1, "resource": None},
        "EXFILTRATE_DATA": {"cost": 1, "resource": None},
        "CLEAR_LOGS": {"cost": 1, "resource": None},
        "MONITOR_LOGS": {"cost": 1, "resource": None},
        "SCAN_FOR_MALWARE": {"cost": 1, "resource": "scan_bandwidth"},
        "APPLY_PATCH": {"cost": 1, "resource": "patches_available"},
        "ISOLATE_HOST": {"cost": 1, "resource": None},
        "RESTORE_BACKUP": {"cost": 5, "resource": "ir_budget"},
        "FIREWALL_RULE": {"cost": 1, "resource": None},
        "INCIDENT_RESPONSE": {"cost": 10, "resource": "ir_budget"},
    }
    
    @staticmethod
    def get_action_cost(action_name: str) -> Dict[str, Any]:
        """
        Get cost information for an action.
        
        Args:
            action_name: Name of the action
        
        Returns:
            Cost dict with cost and resource type
        """
        return ActionCostCalculator.ACTION_COSTS.get(
            action_name,
            {"cost": 1, "resource": None}
        )
    
    @staticmethod
    def can_afford_action(
        action_name: str,
        resources: Dict[str, int]
    ) -> bool:
        """
        Check if player can afford an action.
        
        Args:
            action_name: Name of the action
            resources: Current resources dict
        
        Returns:
            True if action is affordable
        """
        cost_info = ActionCostCalculator.get_action_cost(action_name)
        resource_type = cost_info.get("resource")
        cost = cost_info.get("cost", 1)
        
        if resource_type is None:
            return True
        
        return resources.get(resource_type, 0) >= cost
    
    @staticmethod
    def get_all_action_costs() -> Dict[str, Dict[str, Any]]:
        """Get all action costs."""
        return ActionCostCalculator.ACTION_COSTS.copy()
