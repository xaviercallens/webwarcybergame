"""
Unit tests for ResourceManager and ActionCostCalculator.
Tests resource management per blueprint Section 1.
"""

import pytest
from src.game.resources import ResourceManager, ActionCostCalculator


class TestResourceManagerBasics:
    """Test basic resource manager functionality."""
    
    def test_creation_default(self):
        rm = ResourceManager()
        assert rm.attacker_resources["exploit_kits"] == 10
        assert rm.defender_resources["ir_budget"] == 100
    
    def test_creation_with_scenario(self):
        scenario = {"attacker_exploit_budget": 20, "defender_ir_budget": 200}
        rm = ResourceManager(scenario=scenario)
        assert rm.attacker_resources["exploit_kits"] == 20
        assert rm.defender_resources["ir_budget"] == 200


class TestAttackerResources:
    """Test attacker resource operations."""
    
    def test_can_exploit(self):
        rm = ResourceManager()
        assert rm.can_attacker_exploit() is True
    
    def test_use_exploit(self):
        rm = ResourceManager()
        initial = rm.attacker_resources["exploit_kits"]
        assert rm.use_attacker_exploit() is True
        assert rm.attacker_resources["exploit_kits"] == initial - 1
    
    def test_exhaust_exploits(self):
        rm = ResourceManager(scenario={"attacker_exploit_budget": 1})
        assert rm.use_attacker_exploit() is True
        assert rm.use_attacker_exploit() is False
        assert rm.can_attacker_exploit() is False
    
    def test_use_malware(self):
        rm = ResourceManager()
        assert rm.use_attacker_malware() is True
        assert rm.attacker_usage["malware_deployed"] == 1
    
    def test_exhaust_malware(self):
        rm = ResourceManager(scenario={"attacker_malware_budget": 1})
        assert rm.use_attacker_malware() is True
        assert rm.use_attacker_malware() is False


class TestDefenderResources:
    """Test defender resource operations."""
    
    def test_can_patch(self):
        rm = ResourceManager()
        assert rm.can_defender_patch() is True
    
    def test_use_patch(self):
        rm = ResourceManager()
        initial = rm.defender_resources["patches_available"]
        assert rm.use_defender_patch() is True
        assert rm.defender_resources["patches_available"] == initial - 1
    
    def test_exhaust_patches(self):
        rm = ResourceManager(scenario={"defender_patches": 1})
        assert rm.use_defender_patch() is True
        assert rm.use_defender_patch() is False
    
    def test_spend_ir_budget(self):
        rm = ResourceManager()
        assert rm.spend_defender_ir_budget(10) is True
        assert rm.defender_resources["ir_budget"] == 90
    
    def test_overspend_ir_budget(self):
        rm = ResourceManager(scenario={"defender_ir_budget": 5})
        assert rm.spend_defender_ir_budget(10) is False
        assert rm.defender_resources["ir_budget"] == 5
    
    def test_use_scan(self):
        rm = ResourceManager()
        assert rm.use_defender_scan() is True
        assert rm.defender_usage["scans_performed"] == 1


class TestResourceStatus:
    """Test resource status reporting."""
    
    def test_get_attacker_resources(self):
        rm = ResourceManager()
        res = rm.get_attacker_resources()
        assert "exploit_kits" in res
        assert "malware_payloads" in res
    
    def test_get_defender_resources(self):
        rm = ResourceManager()
        res = rm.get_defender_resources()
        assert "ir_budget" in res
        assert "patches_available" in res
    
    def test_get_resource_status(self):
        rm = ResourceManager()
        status = rm.get_resource_status()
        assert "attacker" in status
        assert "defender" in status
        assert "current" in status["attacker"]
        assert "usage" in status["attacker"]
    
    def test_resource_reset(self):
        rm = ResourceManager()
        rm.use_attacker_exploit()
        rm.reset()
        assert rm.attacker_resources["exploit_kits"] == 10
        assert rm.attacker_usage["exploits_used"] == 0


class TestActionCostCalculator:
    """Test action cost calculator."""
    
    def test_get_action_cost(self):
        cost = ActionCostCalculator.get_action_cost("EXPLOIT_VULNERABILITY")
        assert "cost" in cost
        assert "resource" in cost
        assert cost["resource"] == "exploit_kits"
    
    def test_free_action(self):
        cost = ActionCostCalculator.get_action_cost("SCAN_NETWORK")
        assert cost["resource"] is None
    
    def test_can_afford_free_action(self):
        assert ActionCostCalculator.can_afford_action("SCAN_NETWORK", {}) is True
    
    def test_can_afford_with_resources(self):
        resources = {"exploit_kits": 5}
        assert ActionCostCalculator.can_afford_action("EXPLOIT_VULNERABILITY", resources) is True
    
    def test_cannot_afford_without_resources(self):
        resources = {"exploit_kits": 0}
        assert ActionCostCalculator.can_afford_action("EXPLOIT_VULNERABILITY", resources) is False
    
    def test_get_all_action_costs(self):
        costs = ActionCostCalculator.get_all_action_costs()
        assert len(costs) > 0
        assert "EXPLOIT_VULNERABILITY" in costs
        assert "INCIDENT_RESPONSE" in costs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
