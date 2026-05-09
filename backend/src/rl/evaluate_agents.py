"""
RL agent evaluation framework for Neo-Hack v3.1.
Benchmarks agents against baselines and each other.

Blueprint Alignment: Section 3.2-3.3 (RL Integration)
"""

import logging
from typing import Dict, Any

import numpy as np

from .train_agents import (
    RandomAgent,
    RuleBasedAttacker,
    RuleBasedDefender,
    play_episode,
)

logger = logging.getLogger(__name__)


def evaluate_vs_random(
    agent,
    role: str,
    n_games: int = 100,
    num_nodes: int = 10,
    max_turns: int = 50,
) -> Dict[str, Any]:
    """
    Evaluate agent against random opponent.

    Args:
        agent: Agent with predict(obs) -> (action, state)
        role: "attacker" or "defender"
        n_games: Number of games to play
        num_nodes: Network size
        max_turns: Max turns per game

    Returns:
        Evaluation results
    """
    wins = 0
    total_reward = 0.0
    rewards = []

    for i in range(n_games):
        if role == "attacker":
            opponent = RandomAgent(action_space_n=7)
            result = play_episode(agent, opponent, num_nodes, max_turns, seed=i)
            reward = result["attacker_reward"]
            won = result["winner"] == "attacker"
        else:
            opponent = RandomAgent(action_space_n=8)
            result = play_episode(opponent, agent, num_nodes, max_turns, seed=i)
            reward = result["defender_reward"]
            won = result["winner"] == "defender"

        if won:
            wins += 1
        total_reward += reward
        rewards.append(reward)

    win_rate = wins / n_games
    return {
        "win_rate": win_rate,
        "avg_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "total_games": n_games,
        "wins": wins,
        "passes_threshold": win_rate >= 0.80,
    }


def evaluate_vs_rule_based(
    agent,
    role: str,
    n_games: int = 100,
    num_nodes: int = 10,
    max_turns: int = 50,
) -> Dict[str, Any]:
    """
    Evaluate agent against rule-based opponent.

    Args:
        agent: Agent with predict(obs) -> (action, state)
        role: "attacker" or "defender"
        n_games: Number of games to play
        num_nodes: Network size
        max_turns: Max turns per game

    Returns:
        Evaluation results
    """
    wins = 0
    rewards = []

    for i in range(n_games):
        if role == "attacker":
            opponent = RuleBasedDefender()
            result = play_episode(agent, opponent, num_nodes, max_turns, seed=i)
            reward = result["attacker_reward"]
            won = result["winner"] == "attacker"
        else:
            opponent = RuleBasedAttacker()
            result = play_episode(opponent, agent, num_nodes, max_turns, seed=i)
            reward = result["defender_reward"]
            won = result["winner"] == "defender"

        if won:
            wins += 1
        rewards.append(reward)

    win_rate = wins / n_games
    return {
        "win_rate": win_rate,
        "avg_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "total_games": n_games,
        "wins": wins,
    }


def evaluate_head_to_head(
    attacker,
    defender,
    n_games: int = 100,
    num_nodes: int = 10,
    max_turns: int = 50,
) -> Dict[str, Any]:
    """
    Evaluate attacker vs defender head-to-head.

    Returns:
        Head-to-head results
    """
    attacker_wins = 0
    attacker_rewards = []
    defender_rewards = []

    for i in range(n_games):
        result = play_episode(attacker, defender, num_nodes, max_turns, seed=i)
        if result["winner"] == "attacker":
            attacker_wins += 1
        attacker_rewards.append(result["attacker_reward"])
        defender_rewards.append(result["defender_reward"])

    return {
        "attacker_win_rate": attacker_wins / n_games,
        "defender_win_rate": (n_games - attacker_wins) / n_games,
        "avg_attacker_reward": float(np.mean(attacker_rewards)),
        "avg_defender_reward": float(np.mean(defender_rewards)),
        "total_games": n_games,
    }


def run_full_evaluation(
    attacker,
    defender,
    n_games: int = 50,
    num_nodes: int = 10,
    max_turns: int = 50,
) -> Dict[str, Any]:
    """
    Run complete evaluation suite for a pair of agents.

    Args:
        attacker: Attacker agent
        defender: Defender agent
        n_games: Games per evaluation
        num_nodes: Network size
        max_turns: Max turns

    Returns:
        Complete evaluation results
    """
    logger.info("Running full evaluation suite...")

    results = {}

    # 1. Attacker vs Random
    logger.info("Evaluating attacker vs random defender...")
    results["attacker_vs_random"] = evaluate_vs_random(
        attacker, "attacker", n_games, num_nodes, max_turns
    )

    # 2. Defender vs Random
    logger.info("Evaluating defender vs random attacker...")
    results["defender_vs_random"] = evaluate_vs_random(
        defender, "defender", n_games, num_nodes, max_turns
    )

    # 3. Attacker vs Rule-based
    logger.info("Evaluating attacker vs rule-based defender...")
    results["attacker_vs_rulebased"] = evaluate_vs_rule_based(
        attacker, "attacker", n_games, num_nodes, max_turns
    )

    # 4. Defender vs Rule-based
    logger.info("Evaluating defender vs rule-based attacker...")
    results["defender_vs_rulebased"] = evaluate_vs_rule_based(
        defender, "defender", n_games, num_nodes, max_turns
    )

    # 5. Head-to-head
    logger.info("Evaluating head-to-head...")
    results["head_to_head"] = evaluate_head_to_head(
        attacker, defender, n_games, num_nodes, max_turns
    )

    # Summary
    results["summary"] = {
        "attacker_vs_random_wr": results["attacker_vs_random"]["win_rate"],
        "defender_vs_random_wr": results["defender_vs_random"]["win_rate"],
        "attacker_vs_rulebased_wr": results["attacker_vs_rulebased"]["win_rate"],
        "defender_vs_rulebased_wr": results["defender_vs_rulebased"]["win_rate"],
        "h2h_attacker_wr": results["head_to_head"]["attacker_win_rate"],
    }

    logger.info(f"Evaluation complete: {results['summary']}")
    return results
