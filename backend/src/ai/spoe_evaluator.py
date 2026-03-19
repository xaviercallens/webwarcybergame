"""
S-POE (Strategic Policy, Opponent, Environment) evaluation framework for Neo-Hack v3.1.
Benchmarks RL agents on situational awareness and opponent modeling.

Blueprint Alignment: Section 3.6 (Logging & Analytics), Spec v3 Section II
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SPOEEvaluator:
    """
    Strategic Policy, Opponent, Environment evaluation framework.
    Evaluates agents on:
    - MM-SA-Bench: Multi-Modal Situational Awareness
    - PsyR-OM-Bench: Psychological Reasoning – Opponent Modeling
    """

    def evaluate_situational_awareness(
        self,
        agent,
        scenarios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        MM-SA-Bench: Multi-Modal Situational Awareness.

        Tests:
        - Object detection: Can agent identify compromised nodes?
        - Spatial relationships: Understands network topology?
        - Situational reasoning: Predicts next attack vector?

        Args:
            agent: Agent with identify_threats, predict_lateral_movement,
                   predict_next_move methods
            scenarios: List of scenario dicts with game state data

        Returns:
            Evaluation scores dict
        """
        scores = {
            "object_detection": 0.0,
            "spatial_relationships": 0.0,
            "situational_reasoning": 0.0,
        }

        if not scenarios:
            return {"mmsa_score": 0.0, "breakdown": scores}

        for scenario in scenarios:
            compromised = scenario.get("compromised_nodes", [])
            attack_paths = scenario.get("attack_paths", [])
            next_target = scenario.get("next_target", None)

            # Test 1: Object detection
            if hasattr(agent, "identify_threats"):
                predicted = agent.identify_threats(scenario)
                scores["object_detection"] += self._f1_score(compromised, predicted)
            else:
                scores["object_detection"] += self._random_baseline_detection(
                    compromised, scenario.get("num_nodes", 10)
                )

            # Test 2: Spatial relationships
            if hasattr(agent, "predict_lateral_movement"):
                predicted_paths = agent.predict_lateral_movement(scenario)
                scores["spatial_relationships"] += self._path_accuracy(
                    attack_paths, predicted_paths
                )
            else:
                scores["spatial_relationships"] += 0.5  # Random baseline

            # Test 3: Situational reasoning
            if hasattr(agent, "predict_next_move"):
                agent_guess = agent.predict_next_move(scenario)
                scores["situational_reasoning"] += float(next_target == agent_guess)
            else:
                scores["situational_reasoning"] += 0.1  # Random baseline

        n = len(scenarios)
        for k in scores:
            scores[k] /= n

        # Weighted average per blueprint (30%, 40%, 30%)
        total = (
            scores["object_detection"] * 0.3
            + scores["spatial_relationships"] * 0.4
            + scores["situational_reasoning"] * 0.3
        )

        return {
            "mmsa_score": total * 100,
            "breakdown": scores,
        }

    def evaluate_opponent_modeling(
        self,
        agent,
        matches: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        PsyR-OM-Bench: Psychological Reasoning – Opponent Modeling.

        Infer latent traits:
        - Risk preference (aggressive vs. cautious)
        - Reward horizon (short-term vs. long-term)

        Args:
            agent: Agent with infer_risk_preference method
            matches: List of match history dicts

        Returns:
            Evaluation scores dict
        """
        predictions = []
        actuals = []

        for match in matches:
            opponent_actions = match.get("action_sequence", [])
            actual_risk = match.get("opponent_risk_preference", "unknown")

            if hasattr(agent, "infer_risk_preference"):
                predicted_risk = agent.infer_risk_preference(opponent_actions[:10])
            else:
                predicted_risk = self._classify_risk_from_actions(opponent_actions)

            predictions.append(predicted_risk)
            actuals.append(actual_risk)

        if not matches:
            return {"pom_score": 0.0, "prediction_accuracy": 0.0}

        accuracy = sum(p == a for p, a in zip(predictions, actuals)) / len(matches)

        return {
            "pom_score": accuracy * 100,
            "prediction_accuracy": accuracy,
        }

    def evaluate_full(
        self,
        agent,
        scenarios: List[Dict[str, Any]],
        matches: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run full S-POE evaluation suite.

        Returns:
            Combined evaluation results
        """
        sa_results = self.evaluate_situational_awareness(agent, scenarios)
        om_results = self.evaluate_opponent_modeling(agent, matches)

        overall = (sa_results["mmsa_score"] + om_results["pom_score"]) / 2

        return {
            "overall_score": overall,
            "situational_awareness": sa_results,
            "opponent_modeling": om_results,
        }

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _f1_score(actual: List, predicted: List) -> float:
        """Calculate F1 score between actual and predicted sets."""
        actual_set = set(actual)
        predicted_set = set(predicted)

        if not actual_set and not predicted_set:
            return 1.0
        if not actual_set or not predicted_set:
            return 0.0

        tp = len(actual_set & predicted_set)
        precision = tp / len(predicted_set) if predicted_set else 0
        recall = tp / len(actual_set) if actual_set else 0

        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    @staticmethod
    def _path_accuracy(actual_paths: List, predicted_paths: List) -> float:
        """Calculate accuracy of predicted attack paths."""
        if not actual_paths:
            return 1.0 if not predicted_paths else 0.0
        if not predicted_paths:
            return 0.0

        actual_set = set(map(tuple, actual_paths))
        predicted_set = set(map(tuple, predicted_paths))
        correct = len(actual_set & predicted_set)
        return correct / len(actual_set)

    @staticmethod
    def _random_baseline_detection(actual: List, num_nodes: int) -> float:
        """Calculate expected F1 for random guessing."""
        if not actual or num_nodes == 0:
            return 0.0
        proportion = len(actual) / num_nodes
        return proportion  # Rough estimate

    @staticmethod
    def _classify_risk_from_actions(actions: List[int]) -> str:
        """Classify opponent risk preference from action sequence."""
        if not actions:
            return "unknown"

        # High-risk actions: exploit, malware, exfiltrate (1, 3, 6)
        high_risk = {1, 3, 6}
        risky_count = sum(1 for a in actions if a in high_risk)
        risk_ratio = risky_count / len(actions)

        if risk_ratio > 0.5:
            return "aggressive"
        elif risk_ratio > 0.2:
            return "balanced"
        else:
            return "cautious"


def generate_benchmark_scenarios(
    num_scenarios: int = 20,
    num_nodes: int = 10,
) -> List[Dict[str, Any]]:
    """
    Generate benchmark scenarios for S-POE evaluation.

    Args:
        num_scenarios: Number of scenarios to generate
        num_nodes: Nodes per scenario

    Returns:
        List of scenario dicts
    """
    scenarios = []

    for i in range(num_scenarios):
        rng = np.random.RandomState(seed=i)

        # Random compromised nodes
        n_compromised = rng.randint(1, max(2, num_nodes // 3))
        compromised = rng.choice(num_nodes, size=n_compromised, replace=False).tolist()

        # Random attack paths (pairs of nodes)
        n_paths = rng.randint(1, max(2, n_compromised))
        paths = []
        for _ in range(n_paths):
            src = rng.randint(0, num_nodes)
            dst = rng.randint(0, num_nodes)
            if src != dst:
                paths.append([src, dst])

        # Next target
        remaining = [n for n in range(num_nodes) if n not in compromised]
        next_target = rng.choice(remaining) if remaining else None

        scenarios.append({
            "id": i,
            "num_nodes": num_nodes,
            "compromised_nodes": compromised,
            "attack_paths": paths,
            "next_target": int(next_target) if next_target is not None else None,
        })

    return scenarios


def generate_benchmark_matches(
    num_matches: int = 20,
) -> List[Dict[str, Any]]:
    """
    Generate benchmark match histories for opponent modeling evaluation.

    Args:
        num_matches: Number of matches to generate

    Returns:
        List of match dicts
    """
    matches = []

    for i in range(num_matches):
        rng = np.random.RandomState(seed=i + 100)

        risk_type = rng.choice(["aggressive", "balanced", "cautious"])

        if risk_type == "aggressive":
            actions = rng.choice([1, 3, 5, 6], size=20).tolist()
        elif risk_type == "balanced":
            actions = rng.choice([0, 1, 2, 5, 7], size=20).tolist()
        else:
            actions = rng.choice([0, 2, 7], size=20).tolist()

        matches.append({
            "id": i,
            "action_sequence": actions,
            "opponent_risk_preference": risk_type,
        })

    return matches
