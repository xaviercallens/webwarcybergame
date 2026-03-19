"""
Unit tests for ReplayRecorder.
Tests event recording, trajectory extraction, summaries, and file saving.
"""

import pytest
import json
import tempfile
import os

from src.game.replay_recorder import ReplayRecorder


@pytest.fixture
def recorder():
    r = ReplayRecorder("test-session-001", "tutorial")
    r.set_initial_state({"num_nodes": 5, "max_turns": 20})
    return r


class TestReplayRecorderInit:

    def test_creates_with_ids(self):
        r = ReplayRecorder("s1", "advanced")
        assert r.session_id == "s1"
        assert r.scenario_name == "advanced"
        assert len(r.events) == 0

    def test_initial_state(self, recorder):
        assert recorder.initial_state == {"num_nodes": 5, "max_turns": 20}


class TestRecordTurn:

    def test_record_single_turn(self, recorder):
        recorder.record_turn({
            "turn": 0,
            "player": "attacker",
            "action": 0,
            "action_name": "SCAN_NETWORK",
            "result": {"success": True},
            "state_changes": {"discovered": [1]},
        })
        assert len(recorder) == 1
        assert recorder.events[0]["player"] == "attacker"
        assert recorder.events[0]["action"] == 0

    def test_record_multiple_turns(self, recorder):
        for i in range(10):
            recorder.record_turn({
                "turn": i,
                "player": "attacker" if i % 2 == 0 else "defender",
                "action": i % 8,
                "result": {"success": i % 3 == 0},
            })
        assert len(recorder) == 10

    def test_records_timestamp(self, recorder):
        recorder.record_turn({"turn": 0, "player": "attacker", "action": 0})
        assert "timestamp" in recorder.events[0]

    def test_defaults_for_missing_fields(self, recorder):
        recorder.record_turn({})
        event = recorder.events[0]
        assert event["player"] == "unknown"
        assert event["action"] is None


class TestWinner:

    def test_set_and_get_winner(self, recorder):
        assert recorder.get_winner() is None
        recorder.set_winner("attacker")
        assert recorder.get_winner() == "attacker"


class TestGetReplayData:

    def test_replay_structure(self, recorder):
        recorder.record_turn({"turn": 0, "player": "attacker", "action": 0, "result": {}})
        recorder.set_winner("defender")
        data = recorder.get_replay_data()

        assert data["session_id"] == "test-session-001"
        assert data["initial_state"] is not None
        assert len(data["events"]) == 1
        assert data["metadata"]["winner"] == "defender"
        assert data["metadata"]["duration"] == 1
        assert data["metadata"]["scenario"] == "tutorial"
        assert "ended_at" in data["metadata"]


class TestExtractTrajectories:

    def test_splits_by_role(self, recorder):
        for i in range(6):
            recorder.record_turn({
                "turn": i,
                "player": "attacker" if i % 2 == 0 else "defender",
                "action": i,
                "result": {"success": True},
            })
        trajectories = recorder.extract_trajectories()
        assert len(trajectories["attacker"]) == 3
        assert len(trajectories["defender"]) == 3

    def test_empty_trajectories(self, recorder):
        trajectories = recorder.extract_trajectories()
        assert trajectories["attacker"] == []
        assert trajectories["defender"] == []


class TestGetActionSequence:

    def test_all_actions(self, recorder):
        for i in range(4):
            recorder.record_turn({"turn": i, "player": "attacker", "action": i})
        seq = recorder.get_action_sequence()
        assert seq == [0, 1, 2, 3]

    def test_filtered_by_player(self, recorder):
        recorder.record_turn({"turn": 0, "player": "attacker", "action": 0})
        recorder.record_turn({"turn": 1, "player": "defender", "action": 5})
        recorder.record_turn({"turn": 2, "player": "attacker", "action": 1})

        assert recorder.get_action_sequence("attacker") == [0, 1]
        assert recorder.get_action_sequence("defender") == [5]

    def test_skips_none_actions(self, recorder):
        recorder.record_turn({"turn": 0, "player": "attacker", "action": None})
        assert recorder.get_action_sequence() == []


class TestGetSummary:

    def test_summary_structure(self, recorder):
        recorder.record_turn({"turn": 0, "player": "attacker", "action": 0, "result": {"success": True}})
        recorder.record_turn({"turn": 1, "player": "defender", "action": 0, "result": {"success": False}})
        recorder.record_turn({"turn": 2, "player": "attacker", "action": 1, "result": {"success": False}})
        recorder.set_winner("defender")

        summary = recorder.get_summary()
        assert summary["session_id"] == "test-session-001"
        assert summary["total_turns"] == 3
        assert summary["attacker_actions"] == 2
        assert summary["defender_actions"] == 1
        assert summary["attacker_successes"] == 1
        assert summary["defender_successes"] == 0
        assert summary["winner"] == "defender"


class TestSaveToFile:

    def test_saves_json(self, recorder):
        recorder.record_turn({"turn": 0, "player": "attacker", "action": 0, "result": {}})
        recorder.set_winner("attacker")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = recorder.save_to_file(directory=tmpdir)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert data["session_id"] == "test-session-001"
            assert len(data["events"]) == 1

    def test_creates_directory(self, recorder):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "sub", "dir")
            path = recorder.save_to_file(directory=nested)
            assert os.path.exists(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
