"""
Stealth and alert system for Neo-Hack v3.1.
Manages detection mechanics and alert level progression.
"""

from typing import Dict, Any
import random


class StealthAlertSystem:
    """
    Manages stealth/alert mechanics.
    Tracks attacker visibility and defender detection capabilities.
    
    Blueprint Alignment: Section 1 (Core Mechanics)
    """
    
    def __init__(self):
        """Initialize stealth/alert system."""
        self.alert_level = 0
        self.max_alert_level = 100
        self.detection_threshold = 70
        self.last_alert_location = None
        self.last_alert_time = None
        self.alert_history = []
        self.detection_events = []
    
    def calculate_stealth_cost(self, action_name: str) -> int:
        """
        Calculate stealth cost (alert increase) for an action.
        Lower is stealthier.
        
        Args:
            action_name: Name of the action
        
        Returns:
            Stealth cost (0-100)
        """
        stealth_costs = {
            "SCAN_NETWORK": 5,
            "EXPLOIT_VULNERABILITY": 30,
            "PHISHING": 15,
            "INSTALL_MALWARE": 35,
            "ELEVATE_PRIVILEGES": 25,
            "LATERAL_MOVEMENT": 40,
            "EXFILTRATE_DATA": 50,
            "CLEAR_LOGS": 10,
        }
        return stealth_costs.get(action_name, 20)
    
    def calculate_detection_chance(self, action_name: str, alert_level: int) -> float:
        """
        Calculate chance of action being detected.
        Increases with alert level.
        
        Args:
            action_name: Name of the action
            alert_level: Current alert level (0-100)
        
        Returns:
            Detection probability (0.0-1.0)
        """
        base_chances = {
            "SCAN_NETWORK": 0.05,
            "EXPLOIT_VULNERABILITY": 0.40,
            "PHISHING": 0.20,
            "INSTALL_MALWARE": 0.50,
            "ELEVATE_PRIVILEGES": 0.35,
            "LATERAL_MOVEMENT": 0.45,
            "EXFILTRATE_DATA": 0.60,
            "CLEAR_LOGS": 0.15,
        }
        
        base_chance = base_chances.get(action_name, 0.30)
        
        # Alert level increases detection chance
        alert_multiplier = 1.0 + (alert_level / 100.0) * 0.5
        
        return min(1.0, base_chance * alert_multiplier)
    
    def raise_alert(self, stealth_cost: int, location: int = None) -> Dict[str, Any]:
        """
        Raise alert level based on action stealth cost.
        
        Args:
            stealth_cost: Stealth cost of the action
            location: Network node where action occurred
        
        Returns:
            Alert update dict
        """
        old_alert = self.alert_level
        self.alert_level = min(self.max_alert_level, self.alert_level + stealth_cost)
        
        self.alert_history.append({
            "old_level": old_alert,
            "new_level": self.alert_level,
            "cost": stealth_cost,
            "location": location,
        })
        
        self.last_alert_location = location
        self.last_alert_time = len(self.alert_history)
        
        result = {
            "alert_level": self.alert_level,
            "alert_increased": self.alert_level > old_alert,
            "threshold_exceeded": self.alert_level >= self.detection_threshold,
        }
        
        # Defender gets bonus action if threshold exceeded
        if self.alert_level >= self.detection_threshold:
            result["defender_bonus_action"] = True
        
        return result
    
    def record_detection(
        self,
        action_name: str,
        location: int,
        detected: bool
    ) -> Dict[str, Any]:
        """
        Record a detection event.
        
        Args:
            action_name: Name of detected action
            location: Network node where detected
            detected: Whether action was detected
        
        Returns:
            Detection event dict
        """
        event = {
            "action": action_name,
            "location": location,
            "detected": detected,
            "alert_level": self.alert_level,
        }
        
        self.detection_events.append(event)
        
        if detected:
            # Increase alert level for detected actions
            self.raise_alert(20, location)
        
        return event
    
    def get_defender_awareness(self) -> Dict[str, Any]:
        """
        Get defender's current awareness level.
        
        Returns:
            Awareness state dict
        """
        return {
            "alert_level": self.alert_level,
            "is_high_alert": self.alert_level >= self.detection_threshold,
            "recent_detections": self.detection_events[-5:],
            "last_alert_location": self.last_alert_location,
            "detection_confidence": min(1.0, self.alert_level / 100.0),
        }
    
    def reset(self) -> None:
        """Reset alert system."""
        self.alert_level = 0
        self.last_alert_location = None
        self.last_alert_time = None
        self.alert_history = []
        self.detection_events = []
    
    def get_summary(self) -> Dict[str, Any]:
        """Get stealth/alert system summary."""
        return {
            "current_alert_level": self.alert_level,
            "max_alert_level": self.max_alert_level,
            "detection_threshold": self.detection_threshold,
            "total_alerts": len(self.alert_history),
            "total_detections": len(self.detection_events),
            "detected_actions": sum(1 for e in self.detection_events if e["detected"]),
        }


class DetectionEngine:
    """
    Manages detection of attacker activities.
    Determines what defender can see based on alert level and actions.
    """
    
    def __init__(self):
        """Initialize detection engine."""
        self.detection_radius = 1  # Nodes away from detected activity
        self.detection_memory = 5  # Turns to remember detections
        self.detected_nodes = set()
        self.detection_timeline = []
    
    def detect_activity(
        self,
        node: int,
        action_name: str,
        alert_level: int
    ) -> bool:
        """
        Determine if activity at a node is detected.
        
        Args:
            node: Network node where activity occurred
            action_name: Type of activity
            alert_level: Current alert level
        
        Returns:
            Whether activity was detected
        """
        # Base detection chance
        base_chance = 0.3
        
        # Increase with alert level
        alert_factor = alert_level / 100.0
        
        # Some actions are easier to detect
        action_factors = {
            "EXFILTRATE_DATA": 1.5,
            "INSTALL_MALWARE": 1.3,
            "LATERAL_MOVEMENT": 1.2,
            "EXPLOIT_VULNERABILITY": 1.0,
            "PHISHING": 0.8,
            "SCAN_NETWORK": 0.5,
            "CLEAR_LOGS": 0.3,
        }
        
        action_factor = action_factors.get(action_name, 1.0)
        
        detection_chance = base_chance * (1.0 + alert_factor) * action_factor
        detection_chance = min(1.0, detection_chance)
        
        return random.random() < detection_chance
    
    def add_detected_node(self, node: int, turn: int) -> None:
        """Record a detected node."""
        self.detected_nodes.add(node)
        self.detection_timeline.append((node, turn))
    
    def get_detected_nodes(self, current_turn: int) -> set:
        """
        Get nodes detected within memory window.
        
        Args:
            current_turn: Current game turn
        
        Returns:
            Set of detected node IDs
        """
        detected = set()
        for node, turn in self.detection_timeline:
            if current_turn - turn < self.detection_memory:
                detected.add(node)
        return detected
    
    def clear_old_detections(self, current_turn: int) -> None:
        """Remove detections outside memory window."""
        self.detection_timeline = [
            (node, turn) for node, turn in self.detection_timeline
            if current_turn - turn < self.detection_memory
        ]
