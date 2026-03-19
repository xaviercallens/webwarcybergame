"""
RL agent training for Neo-Hack v3.1.
Self-play training with PPO for attacker and defender agents.

Blueprint Alignment: Section 3.2-3.3 (RL Integration)
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

import numpy as np
import gymnasium as gym

from .neohack_env import NeoHackEnv
from .scenarios.scenario_loader import load_scenario, get_scenario_for_difficulty

logger = logging.getLogger(__name__)

# Training hyperparameters per difficulty level
DIFFICULTY_CONFIGS = {
    "novice": {
        "episodes": 10_000,
        "learning_rate": 1e-3,
        "n_steps": 1024,
        "batch_size": 64,
        "gamma": 0.95,
        "description": "Quick-trained agent for easy opponents",
    },
    "normal": {
        "episodes": 50_000,
        "learning_rate": 3e-4,
        "n_steps": 2048,
        "batch_size": 128,
        "gamma": 0.99,
        "description": "Balanced agent for standard difficulty",
    },
    "expert": {
        "episodes": 100_000,
        "learning_rate": 3e-4,
        "n_steps": 2048,
        "batch_size": 256,
        "gamma": 0.995,
        "description": "Extensively trained agent for expert play",
    },
}

MODEL_DIR = Path(__file__).parent / "models"


class RandomAgent:
    """Random baseline agent for evaluation."""

    def __init__(self, action_space_n: int):
        self.action_space_n = action_space_n

    def predict(self, obs: np.ndarray, deterministic: bool = False) -> Tuple[int, None]:
        return np.random.randint(0, self.action_space_n), None


class RuleBasedAttacker:
    """Simple rule-based attacker for bootstrapping training."""

    PRIORITY = [0, 1, 5, 6, 7]  # scan, exploit, lateral, exfiltrate, clear_logs

    def __init__(self):
        self._step = 0

    def predict(self, obs: np.ndarray, deterministic: bool = False) -> Tuple[int, None]:
        action = self.PRIORITY[self._step % len(self.PRIORITY)]
        self._step += 1
        return action, None


class RuleBasedDefender:
    """Simple rule-based defender for bootstrapping training."""

    PRIORITY = [0, 1, 2, 5, 6]  # monitor, scan, patch, firewall, incident_response

    def __init__(self):
        self._step = 0

    def predict(self, obs: np.ndarray, deterministic: bool = False) -> Tuple[int, None]:
        action = self.PRIORITY[self._step % len(self.PRIORITY)]
        self._step += 1
        return action, None


def play_episode(
    attacker,
    defender,
    num_nodes: int = 10,
    max_turns: int = 50,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Play a single episode between attacker and defender agents.

    Args:
        attacker: Agent with predict(obs) -> (action, state)
        defender: Agent with predict(obs) -> (action, state)
        num_nodes: Number of network nodes
        max_turns: Maximum game turns
        seed: Random seed

    Returns:
        Episode result dict
    """
    attacker_env = NeoHackEnv(role="attacker", num_nodes=num_nodes, max_turns=max_turns, seed=seed)
    defender_env = NeoHackEnv(role="defender", num_nodes=num_nodes, max_turns=max_turns, seed=seed)

    # Share game state
    att_obs, _ = attacker_env.reset(seed=seed)
    def_obs, _ = defender_env.reset(seed=seed)
    defender_env.game_state = attacker_env.game_state

    total_attacker_reward = 0.0
    total_defender_reward = 0.0
    trajectory = []

    for turn in range(max_turns):
        # Attacker turn
        att_action, _ = attacker.predict(att_obs, deterministic=False)
        att_obs, att_reward, att_term, att_trunc, att_info = attacker_env.step(int(att_action))
        total_attacker_reward += att_reward

        trajectory.append({
            "turn": turn,
            "player": "attacker",
            "action": int(att_action),
            "reward": float(att_reward),
            "info": {k: v for k, v in att_info.items() if k != "last_result"},
        })

        if att_term or att_trunc:
            break

        # Sync state
        defender_env.game_state = attacker_env.game_state

        # Defender turn
        def_action, _ = defender.predict(def_obs, deterministic=False)
        def_obs, def_reward, def_term, def_trunc, def_info = defender_env.step(int(def_action))
        total_defender_reward += def_reward

        trajectory.append({
            "turn": turn,
            "player": "defender",
            "action": int(def_action),
            "reward": float(def_reward),
            "info": {k: v for k, v in def_info.items() if k != "last_result"},
        })

        if def_term or def_trunc:
            break

        # Sync state back
        attacker_env.game_state = defender_env.game_state

    # Determine winner
    winner = attacker_env.winner or defender_env.winner
    if winner is None:
        owned = int(np.sum(attacker_env.game_state.attacker_owned_nodes))
        winner = "attacker" if owned >= num_nodes * 0.3 else "defender"

    attacker_env.close()
    defender_env.close()

    return {
        "winner": winner,
        "attacker_reward": total_attacker_reward,
        "defender_reward": total_defender_reward,
        "turns_played": turn + 1 if 'turn' in dir() else 0,
        "trajectory": trajectory,
    }


def self_play_training_loop(
    n_episodes: int = 1000,
    num_nodes: int = 10,
    max_turns: int = 50,
    log_interval: int = 100,
) -> Dict[str, Any]:
    """
    Run self-play training loop using rule-based agents as baseline.
    This is the CPU-only version that collects experience without SB3.

    Args:
        n_episodes: Number of episodes to play
        num_nodes: Network size
        max_turns: Max turns per episode
        log_interval: How often to log stats

    Returns:
        Training results dict
    """
    attacker = RuleBasedAttacker()
    defender = RuleBasedDefender()

    results = {
        "attacker_wins": 0,
        "defender_wins": 0,
        "total_episodes": 0,
        "attacker_rewards": [],
        "defender_rewards": [],
        "win_rate_history": [],
    }

    for ep in range(n_episodes):
        episode_result = play_episode(
            attacker, defender,
            num_nodes=num_nodes,
            max_turns=max_turns,
            seed=ep,
        )

        results["total_episodes"] += 1
        results["attacker_rewards"].append(episode_result["attacker_reward"])
        results["defender_rewards"].append(episode_result["defender_reward"])

        if episode_result["winner"] == "attacker":
            results["attacker_wins"] += 1
        else:
            results["defender_wins"] += 1

        if (ep + 1) % log_interval == 0:
            win_rate = results["attacker_wins"] / results["total_episodes"]
            avg_att_reward = np.mean(results["attacker_rewards"][-log_interval:])
            avg_def_reward = np.mean(results["defender_rewards"][-log_interval:])
            results["win_rate_history"].append(win_rate)

            logger.info(
                f"Episode {ep+1}/{n_episodes} | "
                f"Attacker WR: {win_rate:.2%} | "
                f"Avg Att R: {avg_att_reward:.1f} | "
                f"Avg Def R: {avg_def_reward:.1f}"
            )

    return results


def train_agents_for_difficulty(
    difficulty: str = "normal",
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Train attacker and defender agents for a given difficulty.

    Args:
        difficulty: "novice", "normal", or "expert"
        output_dir: Directory to save results

    Returns:
        Training results dict
    """
    if difficulty not in DIFFICULTY_CONFIGS:
        raise ValueError(f"Unknown difficulty: {difficulty}. Use: {list(DIFFICULTY_CONFIGS.keys())}")

    config = DIFFICULTY_CONFIGS[difficulty]
    scenario = get_scenario_for_difficulty(difficulty)

    logger.info(f"Training {difficulty} agents: {config['description']}")
    logger.info(f"Episodes: {config['episodes']}, LR: {config['learning_rate']}")

    results = self_play_training_loop(
        n_episodes=min(config["episodes"], 1000),  # Cap for CPU training
        num_nodes=scenario["num_nodes"],
        max_turns=scenario["max_turns"],
        log_interval=100,
    )

    # Save results
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        results_file = out_path / f"training_results_{difficulty}.json"
        serializable = {
            k: v for k, v in results.items()
            if k not in ("attacker_rewards", "defender_rewards")
        }
        serializable["avg_attacker_reward"] = float(np.mean(results["attacker_rewards"]))
        serializable["avg_defender_reward"] = float(np.mean(results["defender_rewards"]))
        with open(results_file, "w") as f:
            json.dump(serializable, f, indent=2)

    return results


def train_all_difficulties(output_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Train agents for all difficulty levels.

    Args:
        output_dir: Directory to save results

    Returns:
        Dict mapping difficulty to results
    """
    all_results = {}
    for difficulty in DIFFICULTY_CONFIGS:
        logger.info(f"\n{'='*50}")
        logger.info(f"Training {difficulty} agents")
        logger.info(f"{'='*50}")
        all_results[difficulty] = train_agents_for_difficulty(difficulty, output_dir)

    return all_results
