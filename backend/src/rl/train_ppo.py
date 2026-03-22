"""
PPO training pipeline for Neo-Hack v3.1 RL agents.
Loads pretrained SB3 models, continues self-play training, saves improved models.

Usage (local):
    python -m src.rl.train_ppo --difficulty normal --timesteps 500000 --output ./models

Usage (GCP Cloud Run Job):
    Configured via environment variables:
        DIFFICULTY, TOTAL_TIMESTEPS, MODEL_INPUT_GCS, MODEL_OUTPUT_GCS
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import (
    BaseCallback,
    CheckpointCallback,
    EvalCallback,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure as configure_logger

from .neohack_env import NeoHackEnv
from .train_agents import (
    RuleBasedAttacker,
    RuleBasedDefender,
    RandomAgent,
    play_episode,
    DIFFICULTY_CONFIGS,
)
from .scenarios.scenario_loader import load_scenario, get_scenario_for_difficulty

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Default model directory
MODEL_DIR = Path(__file__).parent / "models"


# ---------------------------------------------------------------------------
# Vectorized environment factories
# ---------------------------------------------------------------------------

def make_env(role: str, num_nodes: int, max_turns: int, seed: int):
    """Factory that returns a function creating a monitored NeoHackEnv."""
    def _init():
        env = NeoHackEnv(role=role, num_nodes=num_nodes, max_turns=max_turns, seed=seed)
        env = Monitor(env)
        return env
    return _init


def make_vec_env(role: str, num_nodes: int, max_turns: int, n_envs: int = 4, seed: int = 0):
    """Create a vectorized environment with n_envs parallel instances."""
    env_fns = [make_env(role, num_nodes, max_turns, seed + i) for i in range(n_envs)]
    # Use DummyVecEnv to avoid OpenCV typing circular import in Cloud Run
    return DummyVecEnv(env_fns)


# ---------------------------------------------------------------------------
# Opponent callback — periodically plays against baselines during training
# ---------------------------------------------------------------------------

class SelfPlayCallback(BaseCallback):
    """Logs win-rate against rule-based opponent every eval_freq steps."""

    def __init__(self, role: str, num_nodes: int, max_turns: int,
                 eval_freq: int = 10_000, n_eval_games: int = 50, verbose: int = 1):
        super().__init__(verbose)
        self.role = role
        self.num_nodes = num_nodes
        self.max_turns = max_turns
        self.eval_freq = eval_freq
        self.n_eval_games = n_eval_games
        self.results_log = []

    def _on_step(self) -> bool:
        if self.num_timesteps % self.eval_freq == 0 and self.num_timesteps > 0:
            win_rate = self._evaluate()
            self.results_log.append({
                "timestep": self.num_timesteps,
                "win_rate": win_rate,
            })
            if self.verbose:
                logger.info(
                    f"[Eval @{self.num_timesteps}] {self.role} win-rate vs rule-based: {win_rate:.1%}"
                )
        return True

    def _evaluate(self) -> float:
        wins = 0
        for i in range(self.n_eval_games):
            if self.role == "attacker":
                opponent = RuleBasedDefender()
                result = play_episode(self.model, opponent, self.num_nodes, self.max_turns, seed=i + 99999)
                if result["winner"] == "attacker":
                    wins += 1
            else:
                opponent = RuleBasedAttacker()
                result = play_episode(opponent, self.model, self.num_nodes, self.max_turns, seed=i + 99999)
                if result["winner"] == "defender":
                    wins += 1
        return wins / self.n_eval_games


# ---------------------------------------------------------------------------
# Core training functions
# ---------------------------------------------------------------------------

def load_or_create_model(
    role: str,
    difficulty: str,
    vec_env,
    input_dir: Optional[Path] = None,
) -> PPO:
    """Load a pretrained model or create a fresh one."""
    config = DIFFICULTY_CONFIGS[difficulty]

    # Try loading existing model
    model_path = None
    if input_dir:
        candidate = input_dir / difficulty / f"ppo_{role}_latest.zip"
        if candidate.exists():
            model_path = candidate

    if model_path is None:
        # Fallback to local models dir
        candidate = MODEL_DIR / difficulty / f"ppo_{role}_latest.zip"
        if candidate.exists():
            model_path = candidate

    if model_path and model_path.exists():
        try:
            # Try loading and check if observation/action spaces match
            model = PPO.load(
                str(model_path),
                env=vec_env,
                learning_rate=config["learning_rate"],
                n_steps=config["n_steps"],
                batch_size=config["batch_size"],
                gamma=config["gamma"],
            )
            logger.info(f"Resumed from {model_path}")
        except ValueError as e:
            if "Observation spaces do not match" in str(e):
                logger.warning(f"Skipping {model_path} due to observation space mismatch: {e}")
                model = PPO(
                    "MlpPolicy",
                    vec_env,
                    learning_rate=config["learning_rate"],
                    n_steps=config["n_steps"],
                    batch_size=config["batch_size"],
                    gamma=config["gamma"],
                    ent_coef=0.01,
                    vf_coef=0.5,
                    max_grad_norm=0.5,
                    verbose=1,
                )
            else:
                raise
    else:
        logger.info(f"No pretrained model found for {role}/{difficulty}. Creating fresh PPO.")
        model = PPO(
            "MlpPolicy",
            vec_env,
            learning_rate=config["learning_rate"],
            n_steps=config["n_steps"],
            batch_size=config["batch_size"],
            gamma=config["gamma"],
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            verbose=1,
        )

    return model


def train_role(
    role: str,
    difficulty: str,
    total_timesteps: int,
    n_envs: int = 4,
    output_dir: Optional[Path] = None,
    input_dir: Optional[Path] = None,
    checkpoint_freq: int = 50_000,
) -> Dict[str, Any]:
    """
    Train a single role (attacker or defender) for a given difficulty.

    Returns dict with training metrics.
    """
    scenario = get_scenario_for_difficulty(difficulty)
    num_nodes = scenario["num_nodes"]
    max_turns = scenario["max_turns"]

    logger.info(f"=== Training {role} @ {difficulty} ===")
    logger.info(f"  Nodes: {num_nodes}, MaxTurns: {max_turns}, Timesteps: {total_timesteps}")
    logger.info(f"  Parallel envs: {n_envs}")

    # Create vectorized env
    vec_env = make_vec_env(role, num_nodes, max_turns, n_envs=n_envs)

    # Load or create model
    model = load_or_create_model(role, difficulty, vec_env, input_dir)

    # Set up output directory
    save_dir = (output_dir or MODEL_DIR) / difficulty
    save_dir.mkdir(parents=True, exist_ok=True)

    # Callbacks
    checkpoint_cb = CheckpointCallback(
        save_freq=max(checkpoint_freq // n_envs, 1),
        save_path=str(save_dir),
        name_prefix=f"ppo_{role}",
    )
    selfplay_cb = SelfPlayCallback(
        role=role,
        num_nodes=num_nodes,
        max_turns=max_turns,
        eval_freq=max(20_000 // n_envs, 1000),
        n_eval_games=30,
    )

    # Use SB3 default logging (TensorBoard logs will be written to save_dir/tb_logs)

    # Train
    t0 = time.time()
    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_cb, selfplay_cb],
        progress_bar=True,
    )
    elapsed = time.time() - t0

    # Save final model
    final_path = save_dir / f"ppo_{role}_latest"
    model.save(str(final_path))
    logger.info(f"Saved final model: {final_path}.zip")

    # Final evaluation
    logger.info("Running final evaluation...")
    final_wr = selfplay_cb._evaluate()
    logger.info(f"Final {role} win-rate vs rule-based: {final_wr:.1%}")

    vec_env.close()

    return {
        "role": role,
        "difficulty": difficulty,
        "total_timesteps": total_timesteps,
        "elapsed_seconds": elapsed,
        "final_win_rate": final_wr,
        "eval_history": selfplay_cb.results_log,
        "model_path": str(final_path) + ".zip",
    }


def train_all(
    difficulty: str = "normal",
    total_timesteps: int = 500_000,
    n_envs: int = 4,
    output_dir: Optional[Path] = None,
    input_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Train both attacker and defender for a given difficulty."""
    results = {}
    for role in ("attacker", "defender"):
        results[role] = train_role(
            role=role,
            difficulty=difficulty,
            total_timesteps=total_timesteps,
            n_envs=n_envs,
            output_dir=output_dir,
            input_dir=input_dir,
        )
    return results


# ---------------------------------------------------------------------------
# GCS helpers (used when running on GCP)
# ---------------------------------------------------------------------------

def download_models_from_gcs(gcs_uri: str, local_dir: Path) -> None:
    """Download pretrained models from GCS."""
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        return

    bucket_name = gcs_uri.replace("gs://", "").split("/")[0]
    prefix = "/".join(gcs_uri.replace("gs://", "").split("/")[1:])

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    for blob in blobs:
        rel_path = blob.name[len(prefix):].lstrip("/")
        if not rel_path:
            continue
        local_path = local_dir / rel_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        logger.info(f"Downloaded: gs://{bucket_name}/{blob.name} -> {local_path}")


def upload_models_to_gcs(local_dir: Path, gcs_uri: str) -> None:
    """Upload trained models to GCS."""
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        return

    bucket_name = gcs_uri.replace("gs://", "").split("/")[0]
    prefix = "/".join(gcs_uri.replace("gs://", "").split("/")[1:])

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    for local_path in local_dir.rglob("*.zip"):
        rel_path = local_path.relative_to(local_dir)
        blob_name = f"{prefix}/{rel_path}" if prefix else str(rel_path)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path))
        logger.info(f"Uploaded: {local_path} -> gs://{bucket_name}/{blob_name}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Neo-Hack PPO Training Pipeline")
    parser.add_argument("--difficulty", default="normal", choices=["novice", "normal", "expert", "all"])
    parser.add_argument("--timesteps", type=int, default=500_000, help="Total timesteps per role")
    parser.add_argument("--n-envs", type=int, default=4, help="Parallel environments")
    parser.add_argument("--output", type=str, default=None, help="Output directory for models")
    parser.add_argument("--input", type=str, default=None, help="Input directory with pretrained models")
    parser.add_argument("--gcs-input", type=str, default=None, help="GCS URI for pretrained models")
    parser.add_argument("--gcs-output", type=str, default=None, help="GCS URI to upload trained models")
    args = parser.parse_args()

    # Override from environment (for Cloud Run Jobs)
    difficulty = os.environ.get("DIFFICULTY", args.difficulty)
    total_timesteps = int(os.environ.get("TOTAL_TIMESTEPS", args.timesteps))
    n_envs = int(os.environ.get("N_ENVS", args.n_envs))
    gcs_input = os.environ.get("MODEL_INPUT_GCS", args.gcs_input)
    gcs_output = os.environ.get("MODEL_OUTPUT_GCS", args.gcs_output)

    output_dir = Path(args.output) if args.output else Path("/tmp/rl_models")
    input_dir = Path(args.input) if args.input else None

    # Download pretrained models from GCS if specified
    if gcs_input:
        input_dir = Path("/tmp/pretrained_models")
        input_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading pretrained models from {gcs_input}...")
        download_models_from_gcs(gcs_input, input_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Neo-Hack PPO Training Pipeline")
    logger.info(f"  Difficulty: {difficulty}")
    logger.info(f"  Timesteps/role: {total_timesteps:,}")
    logger.info(f"  Parallel envs: {n_envs}")
    logger.info(f"  Output: {output_dir}")
    logger.info("=" * 60)

    t_start = time.time()

    if difficulty == "all":
        all_results = {}
        for diff in ("novice", "normal", "expert"):
            all_results[diff] = train_all(
                difficulty=diff,
                total_timesteps=total_timesteps,
                n_envs=n_envs,
                output_dir=output_dir,
                input_dir=input_dir,
            )
        results = all_results
    else:
        results = train_all(
            difficulty=difficulty,
            total_timesteps=total_timesteps,
            n_envs=n_envs,
            output_dir=output_dir,
            input_dir=input_dir,
        )

    total_elapsed = time.time() - t_start

    # Save training report
    report = {
        "total_elapsed_seconds": total_elapsed,
        "difficulty": difficulty,
        "total_timesteps": total_timesteps,
        "results": _make_serializable(results),
    }
    report_path = output_dir / "training_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Training report saved: {report_path}")

    # Upload to GCS if specified
    if gcs_output:
        logger.info(f"Uploading trained models to {gcs_output}...")
        upload_models_to_gcs(output_dir, gcs_output)

    logger.info(f"Training complete in {total_elapsed / 60:.1f} minutes.")


def _make_serializable(obj):
    """Convert numpy types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


if __name__ == "__main__":
    main()
