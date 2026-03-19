"""Tests for backend.seed_cnsa — CNSA faction seeding."""
import os, pytest
from unittest.mock import patch
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.models import Faction
from backend.seed_cnsa import run

@patch("backend.seed_cnsa.get_engine")
def test_adds_cnsa_factions(mock_engine):
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(e)
    mock_engine.return_value = e
    run()
    with Session(e) as s:
        factions = s.exec(select(Faction)).all()
        names = [f.name for f in factions]
        assert "Cyber Mercenaries" in names
        assert "Sentinel Vanguard" in names
        assert "Shadow Cartels" in names

@patch("backend.seed_cnsa.get_engine")
def test_skips_existing(mock_engine):
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(e)
    mock_engine.return_value = e
    run()
    run()  # Second run should skip all
    with Session(e) as s:
        assert len(s.exec(select(Faction)).all()) == 3  # No duplicates

@patch("backend.seed_cnsa.get_engine")
def test_correct_reserves(mock_engine):
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(e)
    mock_engine.return_value = e
    run()
    with Session(e) as s:
        for f in s.exec(select(Faction)).all():
            assert f.compute_reserves == 50000
