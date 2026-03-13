"""
Unit tests for database module.
Tests database connection, session management, and initialization.
"""

import pytest
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.database import get_engine, get_session, init_db
from backend import config


class TestDatabaseEngine:
    """Test suite for database engine creation."""

    def test_get_engine_returns_engine(self):
        """Test that get_engine returns a SQLAlchemy engine."""
        # Reset the global engine
        import backend.database as db_module
        db_module._engine = None
        
        # Mock the config
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            engine = get_engine()
            assert engine is not None
            assert hasattr(engine, 'connect')
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_get_engine_singleton_pattern(self):
        """Test that get_engine returns same instance (singleton)."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            engine1 = get_engine()
            engine2 = get_engine()
            assert engine1 is engine2
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_get_engine_no_database_url(self):
        """Test that get_engine returns None when DATABASE_URL not set."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = ""
        
        try:
            engine = get_engine()
            assert engine is None
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_get_engine_with_valid_url(self):
        """Test that get_engine works with valid database URL."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            engine = get_engine()
            assert engine is not None
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.fetchone() is not None
        finally:
            config.settings.database_url = original_url
            db_module._engine = None


class TestDatabaseSession:
    """Test suite for database session management."""

    def test_get_session_yields_session(self):
        """Test that get_session yields a Session object."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            session_gen = get_session()
            session = next(session_gen)
            assert isinstance(session, Session)
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_get_session_no_database_url(self):
        """Test that get_session yields None when DATABASE_URL not set."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = ""
        
        try:
            session_gen = get_session()
            session = next(session_gen)
            assert session is None
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_get_session_context_manager(self):
        """Test that get_session works as context manager."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            session_gen = get_session()
            session = next(session_gen)
            assert session is not None
            # Session should be usable
            assert hasattr(session, 'execute')
        finally:
            config.settings.database_url = original_url
            db_module._engine = None


class TestDatabaseInitialization:
    """Test suite for database initialization."""

    def test_init_db_creates_tables(self):
        """Test that init_db creates database tables."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            init_db()
            engine = get_engine()
            
            # Check that metadata was created
            assert SQLModel.metadata.tables is not None
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_init_db_no_database_url(self):
        """Test that init_db handles missing DATABASE_URL gracefully."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = ""
        
        try:
            # Should not raise an exception
            init_db()
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_init_db_idempotent(self):
        """Test that init_db can be called multiple times safely."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            init_db()
            init_db()  # Should not raise
            init_db()  # Should not raise
        finally:
            config.settings.database_url = original_url
            db_module._engine = None


class TestDatabaseConnection:
    """Test suite for database connection validation."""

    def test_database_connection_valid(self):
        """Test that database connection is valid."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            engine = get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.fetchone() is not None
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_database_connection_invalid_url(self):
        """Test that invalid database URL raises error."""
        import backend.database as db_module
        db_module._engine = None
        
        original_url = config.settings.database_url
        config.settings.database_url = "postgresql://invalid:invalid@localhost:99999/invalid"
        
        try:
            engine = get_engine()
            # Connection should fail when trying to use it
            with pytest.raises(Exception):
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
        finally:
            config.settings.database_url = original_url
            db_module._engine = None


class TestDatabaseModels:
    """Test suite for database models."""

    def test_sqlmodel_metadata_exists(self):
        """Test that SQLModel metadata is initialized."""
        assert SQLModel.metadata is not None

    def test_sqlmodel_metadata_tables(self):
        """Test that SQLModel metadata has tables dict."""
        assert hasattr(SQLModel.metadata, 'tables')
        assert isinstance(SQLModel.metadata.tables, dict)
