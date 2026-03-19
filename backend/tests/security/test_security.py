"""
Security tests for Neo-Hack v3.1.
Tests rate limiting, input validation, and action authorization.

Blueprint Alignment: Section 3.5 (Security)
"""

import pytest

from src.middleware.security import (
    RateLimiter,
    GameActionRequest,
    ActionAuthorizer,
    game_action_limiter,
)
from src.rl.action_space import AttackerAction, DefenderAction
from fastapi import HTTPException
from pydantic import ValidationError


class TestRateLimiter:

    def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.is_allowed("client1") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("client1")
        assert limiter.is_allowed("client1") is False

    def test_separate_clients(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.is_allowed("client1") is False
        assert limiter.is_allowed("client2") is True

    def test_get_remaining(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        limiter.is_allowed("c1")
        limiter.is_allowed("c1")
        assert limiter.get_remaining("c1") == 3


class TestGameActionRequestValidation:

    def test_valid_request(self):
        req = GameActionRequest(
            session_id="abc123",
            player_role="attacker",
            action_type=0,
            target_node=3,
        )
        assert req.player_role == "attacker"

    def test_invalid_player_role(self):
        with pytest.raises(ValidationError):
            GameActionRequest(
                session_id="abc",
                player_role="hacker",
                action_type=0,
            )

    def test_invalid_action_type(self):
        with pytest.raises(ValidationError):
            GameActionRequest(
                session_id="abc",
                player_role="attacker",
                action_type=999,
            )

    def test_invalid_target_node_negative(self):
        with pytest.raises(ValidationError):
            GameActionRequest(
                session_id="abc",
                player_role="attacker",
                action_type=0,
                target_node=-1,
            )

    def test_invalid_target_node_too_large(self):
        with pytest.raises(ValidationError):
            GameActionRequest(
                session_id="abc",
                player_role="attacker",
                action_type=0,
                target_node=1000,
            )

    def test_target_node_optional(self):
        req = GameActionRequest(
            session_id="abc",
            player_role="defender",
            action_type=0,
        )
        assert req.target_node is None


class TestActionAuthorizer:

    def test_valid_attacker_action(self):
        assert ActionAuthorizer.validate_role_action("attacker", AttackerAction.SCAN_NETWORK) is True

    def test_invalid_attacker_action(self):
        assert ActionAuthorizer.validate_role_action("attacker", 99) is False

    def test_valid_defender_action(self):
        assert ActionAuthorizer.validate_role_action("defender", DefenderAction.MONITOR_LOGS) is True

    def test_invalid_role(self):
        assert ActionAuthorizer.validate_role_action("hacker", 0) is False

    def test_validate_turn_correct(self):
        assert ActionAuthorizer.validate_turn("attacker", "attacker") is True

    def test_validate_turn_wrong(self):
        assert ActionAuthorizer.validate_turn("attacker", "defender") is False

    def test_authorize_success(self):
        # Should not raise
        ActionAuthorizer.authorize("attacker", AttackerAction.SCAN_NETWORK, "attacker")

    def test_authorize_wrong_role_action(self):
        with pytest.raises(HTTPException) as exc:
            ActionAuthorizer.authorize("attacker", 99, "attacker")
        assert exc.value.status_code == 400

    def test_authorize_wrong_turn(self):
        with pytest.raises(HTTPException) as exc:
            ActionAuthorizer.authorize("defender", DefenderAction.MONITOR_LOGS, "attacker")
        assert exc.value.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
