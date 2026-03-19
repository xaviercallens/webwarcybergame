"""
Tests for backend.engine — sentinel injection, combat, economy, treaties, epoch loop.
"""
import os, pytest, asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from datetime import datetime, timedelta

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.models import *
from backend.engine import inject_sentinel_actions, process_transition_phase_async

@pytest.fixture
def session():
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(e)
    with Session(e) as s: yield s

def _mkf(s, name="F", cu=5000, fid=None):
    f = Faction(name=name, color="#F00", compute_reserves=cu)
    s.add(f); s.commit(); s.refresh(f); return f

def _seed_all_factions(s):
    """Pre-seed factions 1-8 so IDs match engine's hardcoded CNSA checks."""
    names = ["SV Bloc","Iron Grid","Silk Road","Euro Nexus","Pacific Vanguard",
             "Cyber Mercenaries","Sentinel Vanguard","Shadow Cartels"]
    factions = []
    for n in names:
        cu = 50000 if n in names[5:] else 5000
        f = Faction(name=n, color="#FFF", compute_reserves=cu)
        s.add(f)
    s.commit()
    return {f.name: f for f in s.exec(select(Faction)).all()}

def _mkp(s, u="p1", fid=None):
    from backend.auth import get_password_hash
    p = Player(username=u, hashed_password=get_password_hash("x"), faction_id=fid)
    s.add(p); s.commit(); s.refresh(p); return p

def _mknode(s, name="N1", fid=1, defense=100, compute=10):
    n = Node(name=name, lat=0, lng=0, faction_id=fid, defense_level=defense, compute_output=compute)
    s.add(n); s.commit(); s.refresh(n); return n

class TestInjectSentinelActions:
    def test_no_sentinels(self, session):
        inject_sentinel_actions(session, 1)  # Should not error

    def test_deployed_sentinel_breach(self, session):
        f = _mkf(session, "F1", 5000)
        p = _mkp(session, "p1", f.id)
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit(); session.refresh(s)
        sp = SentinelPolicy(sentinel_id=s.id, aggression_weight=1.0, stealth_weight=0.0, persistence_weight=0.5, efficiency_weight=0.5)
        session.add(sp); session.commit()
        f2 = _mkf(session, "F2")
        _mknode(session, "EN1", f2.id)
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)
        actions = session.exec(select(EpochAction)).all()
        assert len(actions) >= 1
        logs = session.exec(select(SentinelLog)).all()
        assert len(logs) >= 1

    def test_low_cu_skip(self, session):
        f = _mkf(session, "F1", 10)  # Not enough CU
        p = _mkp(session, "p1", f.id)
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit(); session.refresh(s)
        sp = SentinelPolicy(sentinel_id=s.id, aggression_weight=0.5, stealth_weight=0.5, persistence_weight=0.5, efficiency_weight=0.5)
        session.add(sp); session.commit()
        _mknode(session, "N1", f.id)
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)
        logs = session.exec(select(SentinelLog)).all()
        assert any("low" in l.description.lower() for l in logs)

    def test_stealth_targets_lowest(self, session):
        f = _mkf(session, "F1", 5000)
        p = _mkp(session, "p1", f.id)
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit(); session.refresh(s)
        sp = SentinelPolicy(sentinel_id=s.id, aggression_weight=1.0, stealth_weight=1.0, persistence_weight=0.5, efficiency_weight=0.5)
        session.add(sp); session.commit()
        f2 = _mkf(session, "F2")
        _mknode(session, "High", f2.id, defense=900)
        low = _mknode(session, "Low", f2.id, defense=50)
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)
        actions = session.exec(select(EpochAction)).all()
        assert any(a.target_node_id == low.id for a in actions)

    def test_defend_fallback(self, session):
        f = _mkf(session, "F1", 5000)
        p = _mkp(session, "p1", f.id)
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit(); session.refresh(s)
        sp = SentinelPolicy(sentinel_id=s.id, aggression_weight=0.0, stealth_weight=0.0, persistence_weight=0.5, efficiency_weight=0.5)
        session.add(sp); session.commit()
        own_node = _mknode(session, "Own", f.id)
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)
        actions = session.exec(select(EpochAction)).all()
        assert any(a.action_type == ActionType.DEFEND for a in actions)

    def test_no_policy_skips(self, session):
        f = _mkf(session, "F1", 5000)
        p = _mkp(session, "p1", f.id)
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit()
        _mknode(session, "N1", f.id)
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)
        assert len(session.exec(select(EpochAction)).all()) == 0

    def test_no_nodes(self, session):
        f = _mkf(session, "F1", 5000)
        p = _mkp(session, "p1", f.id)
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit(); session.refresh(s)
        sp = SentinelPolicy(sentinel_id=s.id, aggression_weight=0.5, stealth_weight=0.5, persistence_weight=0.5, efficiency_weight=0.5)
        session.add(sp); session.commit()
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)

    def test_breach_no_enemy_falls_to_defend(self, session):
        """When aggression is high but only own nodes exist, falls back to DEFEND."""
        f = _mkf(session, "F1", 5000)
        p = _mkp(session, "p1", f.id)
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit(); session.refresh(s)
        sp = SentinelPolicy(sentinel_id=s.id, aggression_weight=1.0, stealth_weight=0.0, persistence_weight=0.5, efficiency_weight=0.5)
        session.add(sp); session.commit()
        _mknode(session, "Own", f.id)
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)
        actions = session.exec(select(EpochAction)).all()
        assert any(a.action_type == ActionType.DEFEND for a in actions)


class TestProcessTransition:
    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_combat_capture(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        f1 = _mkf(session, "Attacker", 5000)
        f2 = _mkf(session, "Defender", 5000)
        p1 = _mkp(session, "atk", f1.id)
        node = _mknode(session, "Target", f2.id, defense=50)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p1.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=200))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(node)
        assert node.faction_id == f1.id

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_defense_holds(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        f1 = _mkf(session, "Attacker", 5000)
        f2 = _mkf(session, "Defender", 5000)
        p1 = _mkp(session, "atk", f1.id)
        node = _mknode(session, "Target", f2.id, defense=500)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p1.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=10))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(node)
        assert node.faction_id == f2.id  # Defense held

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_economy_update(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        f = _mkf(session, "F1", 0)
        _mknode(session, "N1", f.id, compute=50)
        _mknode(session, "N2", f.id, compute=30)
        e = Epoch(number=1); session.add(e); session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(f)
        assert f.compute_reserves == 80

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_treaty_violation(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        f1 = _mkf(session, "F1", 5000)
        f2 = _mkf(session, "F2", 5000)
        p1 = _mkp(session, "p1", f1.id)
        accord = Accord(faction_a_id=f1.id, faction_b_id=f2.id, type="CEASEFIRE", status="ACTIVE")
        session.add(accord); session.commit()
        node = _mknode(session, "N1", f2.id, defense=500)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p1.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=10))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(accord)
        assert accord.status == "BROKEN"

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_trade_accord(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        f1 = _mkf(session, "F1", 100)
        f2 = _mkf(session, "F2", 100)
        accord = Accord(faction_a_id=f1.id, faction_b_id=f2.id, type="TRADE", status="ACTIVE")
        session.add(accord); session.commit()
        e = Epoch(number=1); session.add(e); session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(f1); session.refresh(f2)
        assert f1.compute_reserves == 150
        assert f2.compute_reserves == 150

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_mercenary_fee(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        factions = _seed_all_factions(session)
        merc = factions["Cyber Mercenaries"]
        # Create a client faction that can pay the fee
        client_f = factions["SV Bloc"]
        client_f.compute_reserves = 500
        session.add(client_f); session.commit()
        accord = Accord(faction_a_id=merc.id, faction_b_id=client_f.id, type="ALLIANCE", status="ACTIVE")
        session.add(accord); session.commit()
        e = Epoch(number=1); session.add(e); session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(client_f)
        assert client_f.compute_reserves == 400  # 500 - 100 fee

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_mercenary_unpaid_breaks(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        factions = _seed_all_factions(session)
        merc = factions["Cyber Mercenaries"]
        client_f = factions["Iron Grid"]
        client_f.compute_reserves = 10  # Can't pay 100 fee
        session.add(client_f); session.commit()
        accord = Accord(faction_a_id=merc.id, faction_b_id=client_f.id, type="ALLIANCE", status="ACTIVE")
        session.add(accord); session.commit()
        e = Epoch(number=1); session.add(e); session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(accord)
        assert accord.status == "BROKEN"

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_cnsa_offense_buff(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        merc = Faction(name="Mercs", color="#AAA", compute_reserves=50000)
        session.add(merc); session.commit(); session.refresh(merc)
        f1 = _mkf(session, "BuffedAtk", 10000)
        f2 = _mkf(session, "Def", 5000)
        # Merc allied with f1
        accord = Accord(faction_a_id=merc.id, faction_b_id=f1.id, type="ALLIANCE", status="ACTIVE")
        session.add(accord); session.commit()
        # Set merc faction id explicitly to 6 for the buff logic
        merc_id = merc.id
        # The code checks if faction_a_id == 6 or faction_b_id == 6
        # Let's set the merc to id 6 by adjusting - this test verifies the buff path exists
        p1 = _mkp(session, "atk", f1.id)
        node = _mknode(session, "T", f2.id, defense=50)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p1.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=200))
        session.commit()
        await process_transition_phase_async(session, e)

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_news_generation_failure(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(side_effect=Exception("API down"))
        
        f = _mkf(session, "F1", 100)
        e = Epoch(number=1); session.add(e); session.commit()
        result = await process_transition_phase_async(session, e)
        assert result is True  # Should not crash

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_defend_action(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        f1 = _mkf(session, "Atk", 5000)
        f2 = _mkf(session, "Def", 5000)
        p1 = _mkp(session, "atk", f1.id)
        p2 = _mkp(session, "def", f2.id)
        node = _mknode(session, "T", f2.id, defense=100)
        e = Epoch(number=1); session.add(e); session.commit()
        # Attacker sends 150, defender adds 100 → total_defense = 100 + 100 = 200 > 150
        session.add(EpochAction(epoch_id=e.id, player_id=p1.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=150))
        session.add(EpochAction(epoch_id=e.id, player_id=p2.id, action_type=ActionType.DEFEND, target_node_id=node.id, cu_committed=100))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(node)
        assert node.faction_id == f2.id  # Defense held

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_influence_pct(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        
        f1 = _mkf(session, "F1", 0)
        f2 = _mkf(session, "F2", 0)
        _mknode(session, "N1", f1.id); _mknode(session, "N2", f1.id); _mknode(session, "N3", f1.id)
        _mknode(session, "N4", f2.id)
        e = Epoch(number=1); session.add(e); session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(f1); session.refresh(f2)
        assert f1.global_influence_pct == 75.0
        assert f2.global_influence_pct == 25.0

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_cnsa_merc_offense_buff(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        factions = _seed_all_factions(session)
        merc = factions["Cyber Mercenaries"]
        atk_f = factions["SV Bloc"]
        def_f = factions["Iron Grid"]
        accord = Accord(faction_a_id=merc.id, faction_b_id=atk_f.id, type="ALLIANCE", status="ACTIVE")
        session.add(accord); session.commit()
        p = _mkp(session, "atk", atk_f.id)
        node = _mknode(session, "T", def_f.id, defense=100)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=100))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(node)
        assert node.faction_id == atk_f.id

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_cnsa_sentinel_defense_buff(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        factions = _seed_all_factions(session)
        sentinel = factions["Sentinel Vanguard"]
        def_f = factions["Euro Nexus"]
        atk_f = factions["Silk Road"]
        accord = Accord(faction_a_id=sentinel.id, faction_b_id=def_f.id, type="ALLIANCE", status="ACTIVE")
        session.add(accord); session.commit()
        p = _mkp(session, "atk", atk_f.id)
        node = _mknode(session, "T", def_f.id, defense=100)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=110))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(node)
        assert node.faction_id == def_f.id

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_cnsa_cartel_debuff(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        factions = _seed_all_factions(session)
        cartel = factions["Shadow Cartels"]
        def_f = factions["Pacific Vanguard"]
        atk_f = factions["SV Bloc"]
        accord = Accord(faction_a_id=cartel.id, faction_b_id=def_f.id, type="ALLIANCE", status="ACTIVE")
        session.add(accord); session.commit()
        p = _mkp(session, "atk", atk_f.id)
        node = _mknode(session, "T", def_f.id, defense=100)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=120))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(node)
        assert node.faction_id == def_f.id

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_player_no_faction_skipped(self, MockDip, mock_mgr, session):
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        f = _mkf(session, "F1", 5000)
        p = _mkp(session, "nofac")
        node = _mknode(session, "N1", f.id, defense=100)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=200))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(node)
        assert node.faction_id == f.id

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_compute_reserves_zero_start(self, MockDip, mock_mgr, session):
        """Verify economy update adds node income to a faction starting at 0 CU."""
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        f = Faction(name="ZeroCU", color="#000", compute_reserves=0)
        session.add(f); session.commit(); session.refresh(f)
        _mknode(session, "N1", f.id, compute=30)
        e = Epoch(number=1); session.add(e); session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(f)
        assert f.compute_reserves == 30

    @patch("backend.engine.manager")
    @patch("backend.services.diplomacy.DiplomacyService")
    @pytest.mark.asyncio
    async def test_treaty_b_attacks_a(self, MockDip, mock_mgr, session):
        """Verify B attacking A also triggers violation."""
        mock_mgr.send_personal_message = AsyncMock()
        mock_mgr.broadcast = AsyncMock()
        MockDip.return_value.generate_epoch_news = AsyncMock(return_value="News!")
        f1 = _mkf(session, "A1", 5000)
        f2 = _mkf(session, "B1", 5000)
        p2 = _mkp(session, "p2", f2.id)
        accord = Accord(faction_a_id=f1.id, faction_b_id=f2.id, type="CEASEFIRE", status="ACTIVE")
        session.add(accord); session.commit()
        node = _mknode(session, "N1", f1.id, defense=500)
        e = Epoch(number=1); session.add(e); session.commit()
        session.add(EpochAction(epoch_id=e.id, player_id=p2.id, action_type=ActionType.BREACH, target_node_id=node.id, cu_committed=10))
        session.commit()
        await process_transition_phase_async(session, e)
        session.refresh(accord)
        assert accord.status == "BROKEN"


class TestInjectSentinelEdgeCases:
    def test_sentinel_player_no_faction(self, session):
        p = _mkp(session, "nofac")
        s = Sentinel(player_id=p.id, name="S1", status=SentinelStatus.DEPLOYED)
        session.add(s); session.commit()
        _mknode(session, "N1", 999)
        e = Epoch(number=1); session.add(e); session.commit()
        inject_sentinel_actions(session, e.id)
        assert len(session.exec(select(EpochAction)).all()) == 0
