"""
Unit tests for StealthAlertSystem and DetectionEngine.
Tests stealth/detection mechanics per blueprint Section 1.
"""

import pytest
from src.game.detection_engine import StealthAlertSystem, DetectionEngine


class TestStealthAlertSystemBasics:
    """Test basic stealth/alert system functionality."""
    
    def test_system_creation(self):
        """Test creating stealth/alert system."""
        system = StealthAlertSystem()
        assert system.alert_level == 0
        assert system.max_alert_level == 100
        assert system.detection_threshold == 70
    
    def test_system_reset(self):
        """Test resetting the system."""
        system = StealthAlertSystem()
        system.alert_level = 50
        system.alert_history.append({"test": True})
        
        system.reset()
        
        assert system.alert_level == 0
        assert len(system.alert_history) == 0


class TestStealthCostCalculation:
    """Test stealth cost calculations."""
    
    def test_scan_is_stealthy(self):
        """Test scan has low stealth cost."""
        system = StealthAlertSystem()
        cost = system.calculate_stealth_cost("SCAN_NETWORK")
        assert cost <= 10
    
    def test_exfiltrate_is_noisy(self):
        """Test exfiltrate has high stealth cost."""
        system = StealthAlertSystem()
        cost = system.calculate_stealth_cost("EXFILTRATE_DATA")
        assert cost >= 40
    
    def test_unknown_action_has_default_cost(self):
        """Test unknown action gets default cost."""
        system = StealthAlertSystem()
        cost = system.calculate_stealth_cost("UNKNOWN_ACTION")
        assert cost == 20
    
    def test_clear_logs_is_quiet(self):
        """Test clear logs has low stealth cost."""
        system = StealthAlertSystem()
        cost = system.calculate_stealth_cost("CLEAR_LOGS")
        assert cost <= 15


class TestDetectionChance:
    """Test detection chance calculations."""
    
    def test_low_alert_low_detection(self):
        """Test low alert level gives low detection chance."""
        system = StealthAlertSystem()
        chance = system.calculate_detection_chance("SCAN_NETWORK", 0)
        assert chance < 0.2
    
    def test_high_alert_higher_detection(self):
        """Test high alert level increases detection chance."""
        system = StealthAlertSystem()
        low_chance = system.calculate_detection_chance("EXPLOIT_VULNERABILITY", 0)
        high_chance = system.calculate_detection_chance("EXPLOIT_VULNERABILITY", 80)
        assert high_chance > low_chance
    
    def test_detection_chance_capped_at_one(self):
        """Test detection chance never exceeds 1.0."""
        system = StealthAlertSystem()
        chance = system.calculate_detection_chance("EXFILTRATE_DATA", 100)
        assert chance <= 1.0
    
    def test_noisy_action_higher_detection(self):
        """Test noisy actions have higher detection chance."""
        system = StealthAlertSystem()
        scan_chance = system.calculate_detection_chance("SCAN_NETWORK", 50)
        exfil_chance = system.calculate_detection_chance("EXFILTRATE_DATA", 50)
        assert exfil_chance > scan_chance


class TestAlertRaising:
    """Test alert level management."""
    
    def test_raise_alert(self):
        """Test raising alert level."""
        system = StealthAlertSystem()
        result = system.raise_alert(20)
        
        assert system.alert_level == 20
        assert result["alert_level"] == 20
        assert result["alert_increased"] is True
    
    def test_alert_level_capped(self):
        """Test alert level cannot exceed max."""
        system = StealthAlertSystem()
        system.raise_alert(150)
        
        assert system.alert_level == 100
    
    def test_threshold_exceeded_bonus(self):
        """Test defender gets bonus when threshold exceeded."""
        system = StealthAlertSystem()
        system.raise_alert(80)
        
        result = system.raise_alert(10)
        assert result["threshold_exceeded"] is True
        assert result.get("defender_bonus_action") is True
    
    def test_alert_history_tracked(self):
        """Test alert history is tracked."""
        system = StealthAlertSystem()
        system.raise_alert(10)
        system.raise_alert(20)
        
        assert len(system.alert_history) == 2
    
    def test_alert_with_location(self):
        """Test alert records location."""
        system = StealthAlertSystem()
        system.raise_alert(10, location=5)
        
        assert system.last_alert_location == 5


class TestDetectionRecording:
    """Test detection event recording."""
    
    def test_record_detection(self):
        """Test recording a detection event."""
        system = StealthAlertSystem()
        event = system.record_detection("EXPLOIT_VULNERABILITY", 3, True)
        
        assert event["detected"] is True
        assert event["location"] == 3
        assert len(system.detection_events) == 1
    
    def test_detected_action_raises_alert(self):
        """Test detected action raises alert level."""
        system = StealthAlertSystem()
        initial_alert = system.alert_level
        
        system.record_detection("EXPLOIT_VULNERABILITY", 3, True)
        
        assert system.alert_level > initial_alert
    
    def test_undetected_action_no_extra_alert(self):
        """Test undetected action doesn't raise extra alert."""
        system = StealthAlertSystem()
        initial_alert = system.alert_level
        
        system.record_detection("SCAN_NETWORK", 3, False)
        
        assert system.alert_level == initial_alert


class TestDefenderAwareness:
    """Test defender awareness state."""
    
    def test_get_defender_awareness(self):
        """Test getting defender awareness."""
        system = StealthAlertSystem()
        awareness = system.get_defender_awareness()
        
        assert "alert_level" in awareness
        assert "is_high_alert" in awareness
        assert "detection_confidence" in awareness
    
    def test_high_alert_awareness(self):
        """Test awareness in high alert state."""
        system = StealthAlertSystem()
        system.alert_level = 80
        
        awareness = system.get_defender_awareness()
        assert awareness["is_high_alert"] is True


class TestStealthAlertSummary:
    """Test system summary."""
    
    def test_get_summary(self):
        """Test getting system summary."""
        system = StealthAlertSystem()
        system.raise_alert(10)
        system.record_detection("EXPLOIT_VULNERABILITY", 3, True)
        
        summary = system.get_summary()
        
        assert summary["current_alert_level"] > 0
        assert summary["total_alerts"] > 0
        assert summary["detected_actions"] == 1


class TestDetectionEngine:
    """Test DetectionEngine class."""
    
    def test_engine_creation(self):
        """Test creating detection engine."""
        engine = DetectionEngine()
        assert engine.detection_radius == 1
        assert engine.detection_memory == 5
    
    def test_add_detected_node(self):
        """Test adding detected node."""
        engine = DetectionEngine()
        engine.add_detected_node(3, turn=1)
        
        assert 3 in engine.detected_nodes
    
    def test_get_detected_nodes_within_memory(self):
        """Test getting nodes within memory window."""
        engine = DetectionEngine()
        engine.add_detected_node(3, turn=1)
        engine.add_detected_node(5, turn=2)
        
        detected = engine.get_detected_nodes(current_turn=3)
        assert 3 in detected
        assert 5 in detected
    
    def test_get_detected_nodes_expired(self):
        """Test expired detections are not returned."""
        engine = DetectionEngine()
        engine.add_detected_node(3, turn=1)
        
        detected = engine.get_detected_nodes(current_turn=100)
        assert 3 not in detected
    
    def test_clear_old_detections(self):
        """Test clearing old detections."""
        engine = DetectionEngine()
        engine.add_detected_node(3, turn=1)
        engine.add_detected_node(5, turn=10)
        
        engine.clear_old_detections(current_turn=10)
        
        # Node 3 (turn 1) should be cleared, node 5 (turn 10) should remain
        assert len(engine.detection_timeline) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
