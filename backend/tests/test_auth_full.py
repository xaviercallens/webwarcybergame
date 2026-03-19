"""
Comprehensive tests for backend.auth module.
Covers password hashing, JWT creation/verification, and get_current_user.
"""

import os
import pytest
import jwt
from datetime import timedelta, datetime
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
)
from backend.models import Player


class TestVerifyPassword:
    def test_valid_password(self):
        hashed = get_password_hash("TestPass123!")
        assert verify_password("TestPass123!", hashed) is True

    def test_invalid_password(self):
        hashed = get_password_hash("TestPass123!")
        assert verify_password("WrongPass", hashed) is False

    def test_empty_password(self):
        hashed = get_password_hash("something")
        assert verify_password("", hashed) is False

    def test_malformed_hash_returns_false(self):
        assert verify_password("test", "not-a-valid-bcrypt-hash") is False

    def test_unicode_password(self):
        hashed = get_password_hash("тест123")
        assert verify_password("тест123", hashed) is True


class TestGetPasswordHash:
    def test_returns_string(self):
        result = get_password_hash("password")
        assert isinstance(result, str)

    def test_returns_bcrypt_format(self):
        result = get_password_hash("password")
        assert result.startswith("$2b$") or result.startswith("$2a$")

    def test_different_calls_produce_different_hashes(self):
        h1 = get_password_hash("password")
        h2 = get_password_hash("password")
        assert h1 != h2  # Different salts

    def test_roundtrip(self):
        pw = "MySecure!Pass99"
        hashed = get_password_hash(pw)
        assert verify_password(pw, hashed) is True


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(data={"sub": "user1"})
        assert isinstance(token, str)

    def test_default_expiry(self):
        token = create_access_token(data={"sub": "user1"})
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded
        assert decoded["sub"] == "user1"

    def test_custom_expiry(self):
        delta = timedelta(hours=2)
        token = create_access_token(data={"sub": "user1"}, expires_delta=delta)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Expiry should be roughly 2 hours from now
        exp = datetime.utcfromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        diff = (exp - now).total_seconds()
        assert 7100 < diff < 7300  # ~2 hours

    def test_payload_preserved(self):
        token = create_access_token(data={"sub": "alice", "extra": "data"})
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "alice"
        assert decoded["extra"] == "data"


class TestGetCurrentUser:
    def test_valid_token_returns_user(self):
        token = create_access_token(data={"sub": "testuser"})
        mock_session = MagicMock()
        mock_player = Player(id=1, username="testuser", hashed_password="x")
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_player
        mock_session.query.return_value = mock_query
        
        user = get_current_user(token=token, session=mock_session)
        assert user.username == "testuser"

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalid.token.here", session=MagicMock())
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        token = create_access_token(
            data={"sub": "user1"}, 
            expires_delta=timedelta(seconds=-10)
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, session=MagicMock())
        assert exc_info.value.status_code == 401

    def test_missing_sub_raises_401(self):
        token = create_access_token(data={"other": "field"})
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, session=MagicMock())
        assert exc_info.value.status_code == 401

    def test_user_not_found_raises_401(self):
        token = create_access_token(data={"sub": "nonexistent"})
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, session=mock_session)
        assert exc_info.value.status_code == 401


class TestConstants:
    def test_secret_key_set(self):
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0

    def test_algorithm(self):
        assert ALGORITHM == "HS256"

    def test_expire_minutes(self):
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24 * 7

    def test_oauth2_scheme_url(self):
        assert oauth2_scheme.model.flows.password.tokenUrl == "api/auth/login"
