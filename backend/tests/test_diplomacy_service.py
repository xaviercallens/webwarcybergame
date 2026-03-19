"""Tests for backend.services.diplomacy — DiplomacyService chat, treaty, news."""
import os, pytest
from unittest.mock import MagicMock, AsyncMock, patch

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.services.diplomacy import DiplomacyService, FACTION_PERSONAS

class TestInit:
    def test_no_api_key(self):
        svc = DiplomacyService(api_key=None)
        assert svc.client is None
    @patch("backend.services.diplomacy.genai")
    def test_with_api_key(self, mock_genai):
        svc = DiplomacyService(api_key="test-key")
        assert svc.client is not None

class TestGetSystemPrompt:
    def test_all_factions(self):
        svc = DiplomacyService()
        for fid in range(1, 9):
            prompt = svc._get_system_prompt(fid)
            assert "Emotion Subtitle" in prompt
            assert FACTION_PERSONAS[fid]["name"] in prompt
    def test_unknown_faction_fallback(self):
        svc = DiplomacyService()
        prompt = svc._get_system_prompt(999)
        assert "Iron Grid" in prompt  # Falls back to faction 2

class TestGenerateChatReply:
    @pytest.mark.asyncio
    async def test_no_client(self):
        svc = DiplomacyService()
        r = await svc.generate_chat_reply(1, "Hello", "state")
        assert "unavailable" in r.lower() or "Missing API" in r

    @pytest.mark.asyncio
    async def test_with_client(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "[Stoic] We shall consider your proposal."
        svc.client.models.generate_content = MagicMock(return_value=mock_resp)
        r = await svc.generate_chat_reply(1, "Hello", "state")
        assert "Stoic" in r

    @pytest.mark.asyncio
    async def test_api_error(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        svc.client.models.generate_content = MagicMock(side_effect=Exception("API Error"))
        r = await svc.generate_chat_reply(1, "Hello", "state")
        assert "INTERRUPTED" in r or "refusing" in r

class TestEvaluateTreaty:
    @pytest.mark.asyncio
    async def test_no_client_accepts(self):
        svc = DiplomacyService()
        assert await svc.evaluate_treaty_proposal(1, "Peace", "state") is True

    @pytest.mark.asyncio
    async def test_accept(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        mock_resp = MagicMock(); mock_resp.text = "ACCEPT"
        svc.client.models.generate_content = MagicMock(return_value=mock_resp)
        assert await svc.evaluate_treaty_proposal(1, "Peace", "state") is True

    @pytest.mark.asyncio
    async def test_reject(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        mock_resp = MagicMock(); mock_resp.text = "REJECT"
        svc.client.models.generate_content = MagicMock(return_value=mock_resp)
        assert await svc.evaluate_treaty_proposal(1, "War", "state") is False

    @pytest.mark.asyncio
    async def test_api_error_rejects(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        svc.client.models.generate_content = MagicMock(side_effect=Exception("Error"))
        assert await svc.evaluate_treaty_proposal(1, "P", "s") is False

class TestGenerateEpochNews:
    @pytest.mark.asyncio
    async def test_no_client(self):
        svc = DiplomacyService()
        r = await svc.generate_epoch_news(["event1", "event2"])
        assert "BULLETIN" in r or "processed" in r

    @pytest.mark.asyncio
    async def test_with_client(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        mock_resp = MagicMock(); mock_resp.text = "Breaking: Massive cyber offensive!"
        svc.client.models.generate_content = MagicMock(return_value=mock_resp)
        r = await svc.generate_epoch_news(["Attack on Node X"], "Prior news")
        assert "Breaking" in r

    @pytest.mark.asyncio
    async def test_empty_events(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        mock_resp = MagicMock(); mock_resp.text = "The grid is quiet."
        svc.client.models.generate_content = MagicMock(return_value=mock_resp)
        r = await svc.generate_epoch_news([])
        assert "quiet" in r

    @pytest.mark.asyncio
    async def test_api_error(self):
        svc = DiplomacyService()
        svc.client = MagicMock()
        svc.client.models.generate_content = MagicMock(side_effect=Exception("boom"))
        r = await svc.generate_epoch_news(["x"])
        assert "DEADZONE" in r or "INTEL" in r

class TestFactionPersonas:
    def test_all_8_factions(self):
        assert len(FACTION_PERSONAS) == 8
    def test_all_have_keys(self):
        for fid, p in FACTION_PERSONAS.items():
            assert "name" in p and "leader" in p and "description" in p
