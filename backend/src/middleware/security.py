"""
Security middleware for Neo-Hack v3.1.
Rate limiting, input validation, and action authorization.

Blueprint Alignment: Section 3.5 (Security)
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Set
from collections import defaultdict

from fastapi import HTTPException, Request
from pydantic import BaseModel, field_validator

from src.rl.action_space import ATTACKER_ACTIONS, DEFENDER_ACTIONS

logger = logging.getLogger(__name__)


# --- Rate Limiter ---

class RateLimiter:
    """
    Simple in-memory rate limiter.
    Tracks requests per IP per window.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limit."""
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean old entries
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > cutoff
        ]

        if len(self._requests[client_id]) >= self.max_requests:
            return False

        self._requests[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests in window."""
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > cutoff
        ]
        return max(0, self.max_requests - len(self._requests[client_id]))


# Default rate limiters
game_action_limiter = RateLimiter(max_requests=100, window_seconds=60)
ai_decide_limiter = RateLimiter(max_requests=200, window_seconds=60)

# Security Configuration
# IPs of trusted proxies (e.g., Cloudflare, Nginx, etc.)
# Can be configured via TRUSTED_PROXIES environment variable (comma-separated)
TRUSTED_PROXIES: Set[str] = set(
    ip.strip() for ip in os.getenv("TRUSTED_PROXIES", "").split(",") if ip.strip()
)


# --- Input Validation ---

class GameActionRequest(BaseModel):
    """Validated game action request."""
    session_id: str
    player_role: str
    action_type: int
    target_node: Optional[int] = None

    @field_validator("player_role")
    @classmethod
    def validate_player_role(cls, v: str) -> str:
        if v not in ("attacker", "defender"):
            raise ValueError(f"Invalid player_role: {v}. Must be 'attacker' or 'defender'")
        return v

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: int) -> int:
        all_actions = set(ATTACKER_ACTIONS.keys()) | set(DEFENDER_ACTIONS.keys())
        if v not in all_actions:
            raise ValueError(f"Invalid action_type: {v}")
        return v

    @field_validator("target_node")
    @classmethod
    def validate_target_node(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 0 or v > 999):
            raise ValueError("Invalid node ID: must be 0-999")
        return v


# --- Action Authorization ---

class ActionAuthorizer:
    """
    Validates that a player can perform a given action.
    Checks role, turn, and resource constraints.
    """

    @staticmethod
    def validate_role_action(role: str, action_id: int) -> bool:
        """Check if action is valid for the given role."""
        if role == "attacker":
            return action_id in ATTACKER_ACTIONS
        elif role == "defender":
            return action_id in DEFENDER_ACTIONS
        return False

    @staticmethod
    def validate_turn(
        current_player: str,
        requesting_player: str,
    ) -> bool:
        """Check if it's the requesting player's turn."""
        return current_player == requesting_player

    @staticmethod
    def authorize(
        role: str,
        action_id: int,
        current_player: str,
    ) -> None:
        """
        Full authorization check. Raises HTTPException on failure.

        Args:
            role: Player role
            action_id: Action being requested
            current_player: Whose turn it is
        """
        if not ActionAuthorizer.validate_role_action(role, action_id):
            raise HTTPException(
                status_code=400,
                detail=f"Action {action_id} not valid for role '{role}'",
            )

        if not ActionAuthorizer.validate_turn(current_player, role):
            raise HTTPException(
                status_code=400,
                detail=f"Not your turn. Current player: {current_player}",
            )


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request.
    Only trusts X-Forwarded-For if the request comes from a trusted proxy.
    """
    client_host = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded and client_host in TRUSTED_PROXIES:
        return forwarded.split(",")[0].strip()

    return client_host
