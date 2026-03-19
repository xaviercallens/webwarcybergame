"""Tests for backend.websocket — ConnectionManager connect, disconnect, send, broadcast."""
import os, pytest
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.websocket import ConnectionManager

@pytest.fixture
def mgr():
    return ConnectionManager()

def _mock_ws():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    return ws

class TestConnect:
    @pytest.mark.asyncio
    async def test_connect_adds(self, mgr):
        ws = _mock_ws()
        await mgr.connect(1, ws)
        assert 1 in mgr.active_connections
        assert ws in mgr.active_connections[1]
        ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_tabs(self, mgr):
        ws1, ws2 = _mock_ws(), _mock_ws()
        await mgr.connect(1, ws1)
        await mgr.connect(1, ws2)
        assert len(mgr.active_connections[1]) == 2

class TestDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_removes(self, mgr):
        ws = _mock_ws()
        await mgr.connect(1, ws)
        mgr.disconnect(1, ws)
        assert 1 not in mgr.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_one_of_many(self, mgr):
        ws1, ws2 = _mock_ws(), _mock_ws()
        await mgr.connect(1, ws1)
        await mgr.connect(1, ws2)
        mgr.disconnect(1, ws1)
        assert len(mgr.active_connections[1]) == 1

    def test_disconnect_unknown(self, mgr):
        mgr.disconnect(999, _mock_ws())  # Should not error

    @pytest.mark.asyncio
    async def test_disconnect_ws_not_in_list(self, mgr):
        ws1, ws2 = _mock_ws(), _mock_ws()
        await mgr.connect(1, ws1)
        mgr.disconnect(1, ws2)  # ws2 not in list
        assert len(mgr.active_connections[1]) == 1

class TestSendPersonalMessage:
    @pytest.mark.asyncio
    async def test_send_to_connected(self, mgr):
        ws = _mock_ws()
        await mgr.connect(1, ws)
        await mgr.send_personal_message({"type": "test"}, 1)
        ws.send_json.assert_called_once_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_send_to_disconnected(self, mgr):
        await mgr.send_personal_message({"type": "test"}, 999)  # No error

    @pytest.mark.asyncio
    async def test_send_error_handled(self, mgr):
        ws = _mock_ws()
        ws.send_json.side_effect = Exception("broken")
        await mgr.connect(1, ws)
        await mgr.send_personal_message({"msg": "x"}, 1)  # Should not raise

class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_all(self, mgr):
        ws1, ws2 = _mock_ws(), _mock_ws()
        await mgr.connect(1, ws1)
        await mgr.connect(2, ws2)
        await mgr.broadcast({"type": "event"})
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_cleans_dead(self, mgr):
        ws = _mock_ws()
        ws.send_text.side_effect = Exception("dead")
        await mgr.connect(1, ws)
        await mgr.broadcast({"type": "event"})
        assert 1 not in mgr.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_empty(self, mgr):
        await mgr.broadcast({"type": "event"})  # No error
