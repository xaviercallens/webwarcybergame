"""
Unit tests for probabilistic action execution.
Tests all 15 actions (8 attacker + 7 defender) with probabilistic outcomes.
Blueprint Alignment: Section 1 (Core Mechanics)
"""

import pytest
import random
import numpy as np

from src.rl.observation_space import GameState
from src.rl.action_space import AttackerAction, DefenderAction
from src.game.actions.attacker_actions import AttackerActionHandler
from src.game.actions.defender_actions import DefenderActionHandler
from src.game.actions.action_executor import ActionExecutor
from src.game.detection_engine import StealthAlertSystem
from src.game.resources import ResourceManager


@pytest.fixture
def game_state():
    gs = GameState(num_nodes=10, max_turns=50)
    # Create a connected topology
    for i in range(gs.num_nodes - 1):
        gs.full_topology[i, i + 1] = 1
        gs.full_topology[i + 1, i] = 1
    return gs


@pytest.fixture
def executor():
    return ActionExecutor(
        stealth_system=StealthAlertSystem(),
        resource_manager=ResourceManager(),
    )


# ------------------------------------------------------------------
# Attacker Action Tests
# ------------------------------------------------------------------

class TestAttackerScanNetwork:

    def test_scan_returns_result(self, game_state):
        random.seed(42)
        result = AttackerActionHandler.execute(AttackerAction.SCAN_NETWORK, game_state, 0)
        assert "success" in result
        assert "detected" in result
        assert result["action"] == "SCAN_NETWORK"

    def test_scan_discovers_topology(self, game_state):
        random.seed(1)  # Seed for success
        result = AttackerActionHandler.execute(AttackerAction.SCAN_NETWORK, game_state, 0)
        if result["success"]:
            assert game_state.attacker_discovered_topology[0, 1] == 1

    def test_scan_has_low_stealth_cost(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.SCAN_NETWORK, game_state, 0)
        assert result["stealth_cost"] <= 10


class TestAttackerExploit:

    def test_exploit_returns_result(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.EXPLOIT_VULNERABILITY, game_state, 0)
        assert result["action"] == "EXPLOIT_VULNERABILITY"

    def test_exploit_compromises_on_success(self, game_state):
        # Run many times to get at least one success
        for seed in range(100):
            random.seed(seed)
            gs = GameState(num_nodes=5)
            result = AttackerActionHandler.execute(AttackerAction.EXPLOIT_VULNERABILITY, gs, 0)
            if result["success"]:
                assert gs.attacker_owned_nodes[0] == 1
                break

    def test_exploit_harder_when_patched(self, game_state):
        successes_unpatched = 0
        successes_patched = 0
        n_trials = 500

        for i in range(n_trials):
            random.seed(i)
            gs = GameState(num_nodes=5)
            result = AttackerActionHandler.execute(AttackerAction.EXPLOIT_VULNERABILITY, gs, 0)
            if result["success"]:
                successes_unpatched += 1

        for i in range(n_trials):
            random.seed(i + 10000)
            gs = GameState(num_nodes=5)
            gs.patched_nodes[0] = 1
            result = AttackerActionHandler.execute(AttackerAction.EXPLOIT_VULNERABILITY, gs, 0)
            if result["success"]:
                successes_patched += 1

        assert successes_patched < successes_unpatched

    def test_exploit_harder_when_isolated(self, game_state):
        game_state.isolated_nodes[0] = 1
        successes = 0
        for i in range(200):
            random.seed(i)
            gs = GameState(num_nodes=5)
            gs.isolated_nodes[0] = 1
            result = AttackerActionHandler.execute(AttackerAction.EXPLOIT_VULNERABILITY, gs, 0)
            if result["success"]:
                successes += 1
        # Very low success when isolated
        assert successes < 50


class TestAttackerPhishing:

    def test_phishing_returns_result(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.PHISHING, game_state, 0)
        assert result["action"] == "PHISHING"

    def test_phishing_compromises_on_success(self, game_state):
        for seed in range(100):
            random.seed(seed)
            gs = GameState(num_nodes=5)
            result = AttackerActionHandler.execute(AttackerAction.PHISHING, gs, 0)
            if result["success"]:
                assert gs.attacker_owned_nodes[0] == 1
                break


class TestAttackerInstallMalware:

    def test_requires_owned_node(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.INSTALL_MALWARE, game_state, 0)
        assert result["success"] is False

    def test_installs_on_owned_node(self, game_state):
        game_state.attacker_owned_nodes[0] = 1
        for seed in range(100):
            random.seed(seed)
            result = AttackerActionHandler.execute(AttackerAction.INSTALL_MALWARE, game_state, 0)
            if result["success"]:
                assert result["details"]["malware_installed"] is True
                break


class TestAttackerElevatePrivileges:

    def test_requires_owned_node(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.ELEVATE_PRIVILEGES, game_state, 0)
        assert result["success"] is False

    def test_elevates_on_owned_node(self, game_state):
        game_state.attacker_owned_nodes[0] = 1
        result = AttackerActionHandler.execute(AttackerAction.ELEVATE_PRIVILEGES, game_state, 0)
        assert result["action"] == "ELEVATE_PRIVILEGES"


class TestAttackerLateralMovement:

    def test_lateral_returns_result(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.LATERAL_MOVEMENT, game_state, 1)
        assert result["action"] == "LATERAL_MOVEMENT"

    def test_lateral_easier_with_adjacent_owned(self, game_state):
        game_state.attacker_owned_nodes[0] = 1
        successes = 0
        for i in range(200):
            random.seed(i)
            gs = GameState(num_nodes=10)
            for j in range(9):
                gs.full_topology[j, j + 1] = 1
                gs.full_topology[j + 1, j] = 1
            gs.attacker_owned_nodes[0] = 1
            result = AttackerActionHandler.execute(AttackerAction.LATERAL_MOVEMENT, gs, 1)
            if result["success"]:
                successes += 1
        assert successes > 50  # Should succeed often with adjacency


class TestAttackerExfiltrateData:

    def test_requires_owned_node(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.EXFILTRATE_DATA, game_state, 0)
        assert result["success"] is False

    def test_exfiltrates_on_owned_node(self, game_state):
        game_state.attacker_owned_nodes[0] = 1
        for seed in range(100):
            random.seed(seed)
            result = AttackerActionHandler.execute(AttackerAction.EXFILTRATE_DATA, game_state, 0)
            if result["success"]:
                assert result["details"]["data_value"] > 0
                break


class TestAttackerClearLogs:

    def test_requires_owned_node(self, game_state):
        result = AttackerActionHandler.execute(AttackerAction.CLEAR_LOGS, game_state, 0)
        assert result["success"] is False

    def test_clears_logs_reduces_alert(self, game_state):
        game_state.attacker_owned_nodes[0] = 1
        game_state.alert_level = 50
        for seed in range(100):
            random.seed(seed)
            result = AttackerActionHandler.execute(AttackerAction.CLEAR_LOGS, game_state, 0)
            if result["success"]:
                assert result["details"]["alert_reduced"] > 0
                break


# ------------------------------------------------------------------
# Defender Action Tests
# ------------------------------------------------------------------

class TestDefenderMonitorLogs:

    def test_monitor_returns_result(self, game_state):
        result = DefenderActionHandler.execute(DefenderAction.MONITOR_LOGS, game_state, 0)
        assert result["action"] == "MONITOR_LOGS"

    def test_monitor_detects_compromise(self, game_state):
        game_state.compromised_nodes[1] = 1
        found = False
        for seed in range(200):
            random.seed(seed)
            gs = GameState(num_nodes=10)
            for j in range(9):
                gs.full_topology[j, j + 1] = 1
                gs.full_topology[j + 1, j] = 1
            gs.compromised_nodes[1] = 1
            result = DefenderActionHandler.execute(DefenderAction.MONITOR_LOGS, gs, 0)
            if result["success"]:
                found = True
                break
        assert found


class TestDefenderScanForMalware:

    def test_scan_returns_result(self, game_state):
        result = DefenderActionHandler.execute(DefenderAction.SCAN_FOR_MALWARE, game_state, 0)
        assert result["action"] == "SCAN_FOR_MALWARE"

    def test_scan_detects_compromised_node(self, game_state):
        game_state.compromised_nodes[0] = 1
        found = False
        for seed in range(200):
            random.seed(seed)
            result = DefenderActionHandler.execute(DefenderAction.SCAN_FOR_MALWARE, game_state, 0)
            if result["success"]:
                found = True
                break
        assert found


class TestDefenderApplyPatch:

    def test_patch_succeeds(self, game_state):
        result = DefenderActionHandler.execute(DefenderAction.APPLY_PATCH, game_state, 0)
        assert result["success"] is True
        assert game_state.patched_nodes[0] == 1

    def test_patch_reduces_vulnerabilities(self, game_state):
        game_state.vulnerabilities[0] = 2
        DefenderActionHandler.execute(DefenderAction.APPLY_PATCH, game_state, 0)
        assert game_state.vulnerabilities[0] < 2


class TestDefenderIsolateHost:

    def test_isolate_succeeds(self, game_state):
        result = DefenderActionHandler.execute(DefenderAction.ISOLATE_HOST, game_state, 0)
        assert result["success"] is True
        assert game_state.isolated_nodes[0] == 1


class TestDefenderRestoreBackup:

    def test_restore_cleans_node(self, game_state):
        game_state.compromised_nodes[0] = 1
        game_state.attacker_owned_nodes[0] = 1
        result = DefenderActionHandler.execute(DefenderAction.RESTORE_BACKUP, game_state, 0)
        assert result["success"] is True
        assert game_state.compromised_nodes[0] == 0
        assert game_state.attacker_owned_nodes[0] == 0


class TestDefenderFirewallRule:

    def test_firewall_returns_result(self, game_state):
        result = DefenderActionHandler.execute(DefenderAction.FIREWALL_RULE, game_state, 0)
        assert result["action"] == "FIREWALL_RULE"
        assert result["success"] is True


class TestDefenderIncidentResponse:

    def test_ir_detects_compromises(self, game_state):
        game_state.compromised_nodes[3] = 1
        game_state.compromised_nodes[7] = 1
        found = False
        for seed in range(100):
            random.seed(seed)
            result = DefenderActionHandler.execute(DefenderAction.INCIDENT_RESPONSE, game_state, 0)
            if result["success"]:
                found = True
                break
        assert found

    def test_ir_raises_alert(self, game_state):
        initial_alert = game_state.alert_level
        DefenderActionHandler.execute(DefenderAction.INCIDENT_RESPONSE, game_state, 0)
        assert game_state.alert_level > initial_alert


# ------------------------------------------------------------------
# ActionExecutor Integration Tests
# ------------------------------------------------------------------

class TestActionExecutorIntegration:

    def test_executor_attacker_action(self, executor, game_state):
        result = executor.execute("attacker", AttackerAction.SCAN_NETWORK, game_state, 0)
        assert "alert_update" in result
        assert result["action"] == "SCAN_NETWORK"

    def test_executor_defender_action(self, executor, game_state):
        result = executor.execute("defender", DefenderAction.MONITOR_LOGS, game_state, 0)
        assert "alert_update" in result

    def test_executor_invalid_player(self, executor, game_state):
        with pytest.raises(ValueError):
            executor.execute("hacker", 0, game_state)

    def test_executor_tracks_alert(self, executor, game_state):
        initial = executor.stealth_system.alert_level
        executor.execute("attacker", AttackerAction.EXPLOIT_VULNERABILITY, game_state, 0)
        assert executor.stealth_system.alert_level > initial

    def test_executor_consumes_resources(self, executor, game_state):
        initial = executor.resource_manager.attacker_resources["exploit_kits"]
        executor.execute("attacker", AttackerAction.EXPLOIT_VULNERABILITY, game_state, 0)
        assert executor.resource_manager.attacker_resources["exploit_kits"] == initial - 1

    def test_executor_valid_actions_attacker(self, executor, game_state):
        actions = executor.get_valid_actions("attacker", game_state)
        assert len(actions) > 0
        assert AttackerAction.SCAN_NETWORK in actions

    def test_executor_valid_actions_defender(self, executor, game_state):
        actions = executor.get_valid_actions("defender", game_state)
        assert len(actions) > 0

    def test_executor_reset(self, executor, game_state):
        executor.execute("attacker", AttackerAction.EXPLOIT_VULNERABILITY, game_state, 0)
        executor.reset()
        assert executor.stealth_system.alert_level == 0

    def test_executor_resource_exhaustion(self, game_state):
        rm = ResourceManager(scenario={"attacker_exploit_budget": 1})
        ex = ActionExecutor(resource_manager=rm)

        ex.execute("attacker", AttackerAction.EXPLOIT_VULNERABILITY, game_state, 0)
        result = ex.execute("attacker", AttackerAction.EXPLOIT_VULNERABILITY, game_state, 0)
        assert result["success"] is False
        assert "Cannot afford" in result["details"].get("error", "")


class TestProbabilisticOutcomes:
    """Test that outcomes are truly probabilistic and configurable."""

    def test_actions_not_always_succeed(self, game_state):
        """Over many trials, exploit should sometimes fail."""
        successes = 0
        for i in range(200):
            random.seed(i)
            gs = GameState(num_nodes=5)
            result = AttackerActionHandler.execute(AttackerAction.EXPLOIT_VULNERABILITY, gs, 0)
            if result["success"]:
                successes += 1
        assert 0 < successes < 200  # Not always, not never

    def test_detection_is_probabilistic(self, game_state):
        """Over many trials, detection should sometimes trigger."""
        detections = 0
        for i in range(200):
            random.seed(i)
            gs = GameState(num_nodes=5)
            result = AttackerActionHandler.execute(AttackerAction.EXPLOIT_VULNERABILITY, gs, 0)
            if result["detected"]:
                detections += 1
        assert 0 < detections < 200

    def test_stealth_actions_less_detected(self):
        """Stealthy actions should be detected less often than noisy ones."""
        scan_detections = 0
        exfil_detections = 0
        n = 500

        for i in range(n):
            random.seed(i)
            gs = GameState(num_nodes=5)
            r = AttackerActionHandler.execute(AttackerAction.SCAN_NETWORK, gs, 0)
            if r["detected"]:
                scan_detections += 1

        for i in range(n):
            random.seed(i + 10000)
            gs = GameState(num_nodes=5)
            gs.attacker_owned_nodes[0] = 1
            r = AttackerActionHandler.execute(AttackerAction.EXFILTRATE_DATA, gs, 0)
            if r["detected"]:
                exfil_detections += 1

        assert scan_detections < exfil_detections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
