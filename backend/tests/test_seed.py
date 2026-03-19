"""Tests for backend.seed — FACTIONS_DATA, generate_nodes_for_faction, seed_database."""
import os, pytest, random
from unittest.mock import patch, MagicMock
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.seed import FACTIONS_DATA, generate_nodes_for_faction, seed_database
from backend.models import Faction, Node, NodeClass

@pytest.fixture
def session():
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(e)
    with Session(e) as s: yield s

class TestFactionsData:
    def test_count(self):
        assert len(FACTIONS_DATA) == 8
    def test_cnsa_count(self):
        assert sum(1 for d in FACTIONS_DATA if d.get("is_cnsa")) == 3
    def test_keys(self):
        for d in FACTIONS_DATA:
            assert "name" in d and "color" in d and "base_lat" in d

class TestGenerateNodes:
    def test_correct_count(self):
        f = Faction(id=1, name="Test", color="#000")
        nodes = generate_nodes_for_faction(f, 37.0, -122.0, count=20)
        assert len(nodes) == 20
    def test_tier_distribution(self):
        random.seed(42)
        f = Faction(id=1, name="Test", color="#000")
        nodes = generate_nodes_for_faction(f, 37.0, -122.0, count=1000)
        t1 = sum(1 for n in nodes if n.node_class == NodeClass.TIER_1)
        t3 = sum(1 for n in nodes if n.node_class == NodeClass.TIER_3)
        assert 500 < t1 < 700  # ~60%
        assert 70 < t3 < 130   # ~10%
    def test_lat_lng_clamped(self):
        f = Faction(id=1, name="Test", color="#000")
        nodes = generate_nodes_for_faction(f, 85.0, 175.0, count=50)
        for n in nodes:
            assert -90 <= n.lat <= 90
            assert -180 <= n.lng <= 180
    def test_naming_convention(self):
        f = Faction(id=1, name="Silicon Valley Bloc", color="#000")
        nodes = generate_nodes_for_faction(f, 37.0, -122.0, count=5)
        for n in nodes:
            assert n.name.startswith("SIL-N")
    def test_defense_ranges(self):
        random.seed(42)
        f = Faction(id=1, name="Test", color="#000")
        nodes = generate_nodes_for_faction(f, 0, 0, count=100)
        for n in nodes:
            assert 50 <= n.defense_level <= 1000
            assert 5 <= n.compute_output <= 100

class TestSeedDatabase:
    @patch("backend.seed.get_engine")
    def test_seed_creates_factions_and_nodes(self, mock_engine):
        e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(e)
        mock_engine.return_value = e
        seed_database(total_nodes=30)
        with Session(e) as s:
            factions = s.exec(select(Faction)).all()
            nodes = s.exec(select(Node)).all()
            assert len(factions) == 8
            assert len(nodes) == 30

    @patch("backend.seed.get_engine")
    def test_reseed_replaces_nodes(self, mock_engine):
        e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(e)
        mock_engine.return_value = e
        seed_database(total_nodes=20)
        seed_database(total_nodes=10)
        with Session(e) as s:
            assert len(s.exec(select(Node)).all()) == 10

    @patch("backend.seed.get_engine")
    def test_node_distribution(self, mock_engine):
        e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(e)
        mock_engine.return_value = e
        seed_database(total_nodes=25)
        with Session(e) as s:
            nodes = s.exec(select(Node)).all()
            assert len(nodes) == 25
