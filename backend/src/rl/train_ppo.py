"""
Neo-Hack v3.2 — PPO Self-Play Training with Stable-Baselines3.

Trains attacker and defender PPO agents via alternating self-play.
Supports time-based training, periodic checkpointing, and CSV logging.

Usage:
    # Train for 4 hours across all difficulties
    python -m rl.train_ppo --hours 4

    # Train only expert difficulty for 2 hours
    python -m rl.train_ppo --hours 2 --difficulty expert

    # Quick 10-minute test run
    python -m rl.train_ppo --hours 0.16 --difficulty novice
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv

from rl.neohack_env import NeoHackEnv
from rl.train_agents import RuleBasedAttacker, RuleBasedDefender, RandomAgent
from rl.scenarios.scenario_loader import get_scenario_for_difficulty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_ppo")

MODEL_DIR = Path(__file__).parent / "models"
LOG_DIR = Path(__file__).parent / "training_logs"


# ── Opponent-wrapper env ──────────────────────────────────────────

class SelfPlayEnv(gym.Env):
    """
    Wraps NeoHackEnv for SB3 training.
    The learning agent plays one role; the opponent is driven by a fixed policy.
    Each step: agent acts → opponent acts → return next obs to agent.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        role: str = "attacker",
        opponent=None,
        num_nodes: int = 10,
        max_turns: int = 50,
        scenario: Optional[dict] = None,
    ):
        super().__init__()
        self.role = role
        self.opp_role = "defender" if role == "attacker" else "attacker"
        self.opponent = opponent or (RuleBasedDefender() if role == "attacker" else RuleBasedAttacker())
        self.num_nodes = num_nodes
        self.max_turns = max_turns
        self.scenario = scenario

        # Create both envs
        self._agent_env = NeoHackEnv(role=role, num_nodes=num_nodes, max_turns=max_turns, scenario=scenario)
        self._opp_env = NeoHackEnv(role=self.opp_role, num_nodes=num_nodes, max_turns=max_turns, scenario=scenario)

        self.observation_space = self._agent_env.observation_space
        self.action_space = self._agent_env.action_space

        # Stats
        self.episode_reward = 0.0
        self.episode_turns = 0
        self.wins = 0
        self.losses = 0
        self.total_episodes = 0
        self._episode_rewards = []

    def reset(self, seed=None, options=None):
        # Record completed episode stats before resetting
        if self.episode_turns > 0:
            self.total_episodes += 1
            self._episode_rewards.append(self.episode_reward)

        obs, info = self._agent_env.reset(seed=seed)
        self._opp_env.reset(seed=seed)
        self._opp_env.game_state = self._agent_env.game_state
        self.episode_reward = 0.0
        self.episode_turns = 0
        return obs, info

    def step(self, action):
        # 1. Agent acts
        obs, reward, terminated, truncated, info = self._agent_env.step(int(action))
        self._opp_env.game_state = self._agent_env.game_state
        self.episode_reward += reward
        self.episode_turns += 1

        if terminated or truncated:
            self._record_result(info)
            return obs, reward, terminated, truncated, info

        # 2. Opponent acts
        from rl.observation_space import get_attacker_observation, get_defender_observation, observation_to_vector
        if self.opp_role == "attacker":
            opp_obs_dict = get_attacker_observation(self._opp_env.game_state)
        else:
            opp_obs_dict = get_defender_observation(self._opp_env.game_state)
        opp_obs_vec = observation_to_vector(opp_obs_dict)

        opp_action, _ = self.opponent.predict(opp_obs_vec, deterministic=False)
        _, _, opp_term, opp_trunc, opp_info = self._opp_env.step(int(opp_action))
        self._agent_env.game_state = self._opp_env.game_state

        if opp_term or opp_trunc:
            # Opponent ended the game — get final obs for agent
            final_obs = self._agent_env._get_observation()
            final_info = self._agent_env._get_info()
            self._agent_env.game_over = True
            self._record_result(final_info)
            return final_obs, reward, True, False, final_info

        # Get agent's next observation
        next_obs = self._agent_env._get_observation()
        return next_obs, reward, False, False, info

    def _record_result(self, info):
        winner = info.get("winner")
        if winner == self.role:
            self.wins += 1
        elif winner is not None:
            self.losses += 1


# ── Callbacks ─────────────────────────────────────────────────────

class TrainingMonitor(BaseCallback):
    """
    Periodic checkpoint saving, CSV logging, and time-limit enforcement.
    """

    def __init__(
        self,
        role: str,
        difficulty: str,
        max_seconds: float,
        checkpoint_interval: int = 900,  # seconds
        log_file: Optional[Path] = None,
        verbose: int = 1,
    ):
        super().__init__(verbose)
        self.role = role
        self.difficulty = difficulty
        self.max_seconds = max_seconds
        self.checkpoint_interval = checkpoint_interval
        self.log_file = log_file

        self._start_time = None
        self._last_checkpoint = None
        self._csv_writer = None
        self._csv_file = None
        self._episode_count = 0
        self._recent_rewards = []

    def _on_training_start(self):
        self._start_time = time.time()
        self._last_checkpoint = self._start_time

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self._csv_file = open(self.log_file, "w", newline="")
            self._csv_writer = csv.writer(self._csv_file)
            self._csv_writer.writerow([
                "timestamp", "timesteps", "episodes", "mean_reward_100",
                "win_rate", "elapsed_min",
            ])

    def _on_step(self) -> bool:
        now = time.time()
        elapsed = now - self._start_time

        # Time limit
        if elapsed >= self.max_seconds:
            logger.info(f"[{self.role}/{self.difficulty}] Time limit reached ({elapsed/3600:.1f}h). Stopping.")
            return False

        # Collect episode info from infos buffer
        if self.locals.get("infos"):
            for info in self.locals["infos"]:
                ep_info = info.get("episode")
                if ep_info:
                    self._episode_count += 1
                    self._recent_rewards.append(ep_info["r"])

        # Periodic checkpoint
        if now - self._last_checkpoint >= self.checkpoint_interval:
            self._save_checkpoint()
            self._last_checkpoint = now

        return True

    def _save_checkpoint(self):
        elapsed = time.time() - self._start_time
        model_path = MODEL_DIR / self.difficulty / f"ppo_{self.role}_latest"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(model_path))

        # Also save a timestamped copy every hour
        hours_elapsed = int(elapsed / 3600)
        ts_path = MODEL_DIR / self.difficulty / f"ppo_{self.role}_h{hours_elapsed}"
        self.model.save(str(ts_path))

        # Env stats — read directly from unwrapped SelfPlayEnv
        env = None
        if hasattr(self.training_env, 'envs'):
            env = self.training_env.envs[0]
            # Unwrap if needed
            while hasattr(env, 'env'):
                env = env.env

        wins = getattr(env, 'wins', 0) if env else 0
        total = getattr(env, 'total_episodes', 1) if env else 1
        ep_rewards = getattr(env, '_episode_rewards', []) if env else []
        win_rate = wins / max(total, 1)

        mean_r = float(np.mean(ep_rewards[-100:])) if ep_rewards else 0.0
        self._episode_count = total

        logger.info(
            f"[{self.role}/{self.difficulty}] "
            f"Steps: {self.num_timesteps:,} | "
            f"Episodes: {self._episode_count} | "
            f"Mean R(100): {mean_r:.1f} | "
            f"Win rate: {win_rate:.1%} | "
            f"Elapsed: {elapsed/60:.0f}min | "
            f"Saved → {model_path}"
        )

        # CSV log
        if self._csv_writer:
            self._csv_writer.writerow([
                datetime.now().isoformat(timespec="seconds"),
                self.num_timesteps,
                self._episode_count,
                f"{mean_r:.2f}",
                f"{win_rate:.3f}",
                f"{elapsed/60:.1f}",
            ])
            self._csv_file.flush()

    def _on_training_end(self):
        self._save_checkpoint()
        if self._csv_file:
            self._csv_file.close()
        logger.info(f"[{self.role}/{self.difficulty}] Training complete. Final steps: {self.num_timesteps:,}")


# ── Training orchestrator ─────────────────────────────────────────

DIFFICULTY_SCHEDULE = {
    "novice":  {"num_nodes": 5,  "max_turns": 20,  "lr": 1e-3,  "batch": 64,  "n_steps": 512},
    "normal":  {"num_nodes": 10, "max_turns": 50,  "lr": 3e-4,  "batch": 128, "n_steps": 1024},
    "expert":  {"num_nodes": 20, "max_turns": 80,  "lr": 3e-4,  "batch": 256, "n_steps": 2048},
}


def train_role(
    role: str,
    difficulty: str,
    max_seconds: float,
    opponent=None,
) -> PPO:
    """Train a single PPO agent for the given role and difficulty."""
    cfg = DIFFICULTY_SCHEDULE[difficulty]
    scenario = get_scenario_for_difficulty(difficulty)

    logger.info(f"{'='*60}")
    logger.info(f"Training PPO {role} | {difficulty} | nodes={cfg['num_nodes']} turns={cfg['max_turns']}")
    logger.info(f"Time budget: {max_seconds/60:.0f} min | LR={cfg['lr']} batch={cfg['batch']}")
    logger.info(f"{'='*60}")

    # Wrap env for SB3
    def make_env():
        return SelfPlayEnv(
            role=role,
            opponent=opponent,
            num_nodes=cfg["num_nodes"],
            max_turns=cfg["max_turns"],
            scenario=scenario,
        )

    vec_env = DummyVecEnv([make_env])

    # Check for existing checkpoint to resume from
    model_path = MODEL_DIR / difficulty / f"ppo_{role}_latest.zip"
    if model_path.exists():
        logger.info(f"Resuming from checkpoint: {model_path}")
        model = PPO.load(str(model_path.with_suffix('')), env=vec_env)
        model.learning_rate = cfg["lr"]
    else:
        model = PPO(
            "MlpPolicy",
            vec_env,
            learning_rate=cfg["lr"],
            n_steps=cfg["n_steps"],
            batch_size=cfg["batch"],
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            verbose=0,
            device="auto",
        )

    log_file = LOG_DIR / f"{role}_{difficulty}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    callback = TrainingMonitor(
        role=role,
        difficulty=difficulty,
        max_seconds=max_seconds,
        checkpoint_interval=900,  # checkpoint every 15 min
        log_file=log_file,
    )

    # total_timesteps set very high — the callback enforces the time limit
    model.learn(total_timesteps=10_000_000, callback=callback)

    vec_env.close()
    return model


def run_self_play_cycle(
    difficulty: str,
    total_seconds: float,
):
    """
    Alternating self-play: train attacker, then defender, repeat.
    Each phase gets half the remaining time.
    """
    logger.info(f"\n{'#'*60}")
    logger.info(f"# Self-Play Cycle: {difficulty} — {total_seconds/3600:.1f} hours")
    logger.info(f"{'#'*60}\n")

    start = time.time()
    cycle = 0

    # Start with rule-based opponents
    att_opponent = RuleBasedDefender()
    def_opponent = RuleBasedAttacker()

    while True:
        elapsed = time.time() - start
        remaining = total_seconds - elapsed
        if remaining < 120:  # less than 2 min left
            break

        cycle += 1
        phase_time = remaining / 2  # split remaining time equally

        # Phase 1: Train attacker vs current best defender
        logger.info(f"\n--- Cycle {cycle} Phase 1: Train ATTACKER vs defender ---")
        att_model = train_role("attacker", difficulty, phase_time, opponent=att_opponent)

        # Update opponent for next phase
        class PPOOpponent:
            def __init__(self, model):
                self.model = model
            def predict(self, obs, deterministic=False):
                action, state = self.model.predict(obs, deterministic=deterministic)
                return int(action), state

        att_opponent_for_def = PPOOpponent(att_model)

        elapsed = time.time() - start
        remaining = total_seconds - elapsed
        if remaining < 120:
            break

        # Phase 2: Train defender vs trained attacker
        logger.info(f"\n--- Cycle {cycle} Phase 2: Train DEFENDER vs attacker ---")
        def_model = train_role("defender", difficulty, remaining, opponent=att_opponent_for_def)

        # Update opponents for next cycle
        def_opponent = PPOOpponent(def_model)
        att_opponent = def_opponent  # defender becomes attacker's next opponent

    logger.info(f"\nSelf-play cycle for {difficulty} complete. Cycles: {cycle}")


def main():
    parser = argparse.ArgumentParser(description="Neo-Hack PPO Self-Play Training")
    parser.add_argument("--hours", type=float, default=4.0, help="Total training time in hours")
    parser.add_argument("--difficulty", type=str, default=None,
                        help="Train specific difficulty (novice/normal/expert). Default: all")
    parser.add_argument("--role", type=str, default=None,
                        help="Train specific role only (attacker/defender). Default: self-play")
    args = parser.parse_args()

    total_seconds = args.hours * 3600
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Neo-Hack PPO Training — {args.hours:.1f} hours")
    logger.info(f"PyTorch device: {_get_device()}")
    logger.info(f"Model dir: {MODEL_DIR}")
    logger.info(f"Log dir: {LOG_DIR}")

    difficulties = [args.difficulty] if args.difficulty else ["novice", "normal", "expert"]

    if args.role:
        # Single role training
        time_per_diff = total_seconds / len(difficulties)
        for diff in difficulties:
            train_role(args.role, diff, time_per_diff)
    else:
        # Full self-play cycle
        time_per_diff = total_seconds / len(difficulties)
        for diff in difficulties:
            run_self_play_cycle(diff, time_per_diff)

    # Save training summary
    summary = {
        "completed_at": datetime.now().isoformat(),
        "total_hours": args.hours,
        "difficulties_trained": difficulties,
        "models": {},
    }
    for diff in difficulties:
        diff_dir = MODEL_DIR / diff
        if diff_dir.exists():
            models = [f.name for f in diff_dir.glob("ppo_*.zip")]
            summary["models"][diff] = models

    summary_path = MODEL_DIR / "training_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"\nTraining summary saved to {summary_path}")
    logger.info("Done.")


def _get_device():
    try:
        import torch
        if torch.cuda.is_available():
            return f"cuda ({torch.cuda.get_device_name(0)})"
        return "cpu"
    except:
        return "cpu"


if __name__ == "__main__":
    main()
