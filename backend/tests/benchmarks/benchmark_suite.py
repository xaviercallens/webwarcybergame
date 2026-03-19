"""
Performance benchmarks for Neo-Hack v3.1.
Tests turn processing latency, RL inference time, and Firestore sync.

Blueprint Alignment: Day 7 (Performance Benchmarking)
"""

import time
import pytest
import numpy as np

from src.rl.observation_space import GameState
from src.rl.action_space import AttackerAction, DefenderAction
from src.game.actions.action_executor import ActionExecutor
from src.game.turn_manager import TurnManager
from src.game.detection_engine import StealthAlertSystem
from src.game.resources import ResourceManager
from src.rl.train_agents import RuleBasedAttacker, RuleBasedDefender
from src.cloud.firestore_sync import FirestoreGameSync


class TestTurnProcessingLatency:
    """Benchmark: Turn processing should be <100ms."""

    def test_turn_latency_under_100ms(self):
        gs = GameState(num_nodes=10, max_turns=50)
        for i in range(9):
            gs.full_topology[i, i + 1] = 1
            gs.full_topology[i + 1, i] = 1

        executor = ActionExecutor(
            stealth_system=StealthAlertSystem(),
            resource_manager=ResourceManager(),
        )

        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            executor.execute("attacker", AttackerAction.SCAN_NETWORK, gs, 0)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg = np.mean(latencies)
        p95 = np.percentile(latencies, 95)

        assert avg < 100, f"Average turn latency {avg:.2f}ms exceeds 100ms target"
        assert p95 < 200, f"P95 turn latency {p95:.2f}ms exceeds 200ms target"

    def test_defender_action_latency(self):
        gs = GameState(num_nodes=10, max_turns=50)
        gs.compromised_nodes[3] = 1
        gs.compromised_nodes[7] = 1

        executor = ActionExecutor()

        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            executor.execute("defender", DefenderAction.INCIDENT_RESPONSE, gs, 0)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg = np.mean(latencies)
        assert avg < 100, f"Defender action latency {avg:.2f}ms exceeds 100ms"


class TestRLInferenceLatency:
    """Benchmark: RL inference should be <500ms."""

    def test_rl_inference_under_500ms(self):
        attacker = RuleBasedAttacker()
        obs = np.zeros(100, dtype=np.float32)

        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            attacker.predict(obs, deterministic=False)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg = np.mean(latencies)
        assert avg < 500, f"RL inference {avg:.2f}ms exceeds 500ms target"

    def test_defender_inference_latency(self):
        defender = RuleBasedDefender()
        obs = np.zeros(100, dtype=np.float32)

        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            defender.predict(obs)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg = np.mean(latencies)
        assert avg < 500, f"Defender inference {avg:.2f}ms exceeds 500ms target"


class TestFirestoreSyncLatency:
    """Benchmark: Firestore sync should be <200ms (in-memory fallback)."""

    def test_state_update_latency(self):
        sync = FirestoreGameSync()  # Falls back to in-memory
        sync.create_game_session("bench-session", {"name": "benchmark"})

        latencies = []
        for i in range(20):
            start = time.perf_counter()
            sync.update_game_state("bench-session", {"turn": i, "alert": i * 5})
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg = np.mean(latencies)
        assert avg < 200, f"State update {avg:.2f}ms exceeds 200ms target"

    def test_session_creation_latency(self):
        sync = FirestoreGameSync()

        latencies = []
        for i in range(10):
            start = time.perf_counter()
            sync.create_game_session(f"bench-{i}", {"name": f"bench-{i}"})
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg = np.mean(latencies)
        assert avg < 200, f"Session creation {avg:.2f}ms exceeds 200ms target"


class TestGameThroughput:
    """Benchmark: System throughput for concurrent-like workloads."""

    def test_full_game_under_5_seconds(self):
        """A 50-turn game should complete in under 5 seconds."""
        gs = GameState(num_nodes=10, max_turns=50)
        for i in range(9):
            gs.full_topology[i, i + 1] = 1
            gs.full_topology[i + 1, i] = 1

        tm = TurnManager(scenario={"max_turns": 50})
        executor = ActionExecutor()
        attacker = RuleBasedAttacker()
        defender = RuleBasedDefender()

        tm.start_game()
        obs = np.zeros(50, dtype=np.float32)

        start = time.perf_counter()

        for _ in range(50):
            if tm.game_over:
                break

            # Attacker
            action, _ = attacker.predict(obs)
            result = executor.execute("attacker", int(action), gs, 0)
            tm.process_action("attacker", int(action), result)

            if tm.game_over:
                break

            # Defender
            action, _ = defender.predict(obs)
            result = executor.execute("defender", int(action), gs, 0)
            tm.process_action("defender", int(action), result)

        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"Full game took {elapsed:.2f}s, exceeds 5s target"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
