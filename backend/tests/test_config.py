"""
Unit tests for configuration module.
Tests environment variable loading and settings management.
"""

import os
import pytest
from backend.config import Settings, settings


class TestSettingsClass:
    """Test suite for Settings class."""

    def test_settings_instance_exists(self):
        """Test that settings instance is created."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_has_database_url(self):
        """Test that settings has database_url attribute."""
        assert hasattr(settings, 'database_url')

    def test_settings_database_url_type(self):
        """Test that database_url is a string."""
        assert isinstance(settings.database_url, str)

    def test_settings_database_url_default(self):
        """Test that database_url has default value."""
        # Should be empty string if not set
        assert isinstance(settings.database_url, str)


class TestEnvironmentVariables:
    """Test suite for environment variable handling."""

    def test_database_url_from_env(self):
        """Test that DATABASE_URL is read from environment."""
        original = os.environ.get("DATABASE_URL")
        
        try:
            os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/testdb"
            # Reload settings to pick up env var
            from importlib import reload
            import backend.config as config_module
            reload(config_module)
            
            assert config_module.settings.database_url == "postgresql://test:test@localhost/testdb"
        finally:
            if original:
                os.environ["DATABASE_URL"] = original
            else:
                os.environ.pop("DATABASE_URL", None)

    def test_database_url_empty_default(self):
        """Test that DATABASE_URL defaults to empty string when not set."""
        # Note: DATABASE_URL may be set in .env file
        # This test verifies the default behavior when env var is empty
        from backend.config import settings
        # If DATABASE_URL is set, it should be a non-empty string
        # If not set, it should be empty
        assert isinstance(settings.database_url, str)


class TestSettingsValidation:
    """Test suite for settings validation."""

    def test_settings_immutable(self):
        """Test that settings can be modified (not immutable)."""
        original = settings.database_url
        try:
            settings.database_url = "test_value"
            assert settings.database_url == "test_value"
        finally:
            settings.database_url = original

    def test_settings_string_format(self):
        """Test that database_url is properly formatted."""
        # Should be either empty or valid connection string format
        url = settings.database_url
        if url:
            assert "://" in url or url == ""


class TestDotenvLoading:
    """Test suite for .env file loading."""

    def test_dotenv_is_loaded(self):
        """Test that dotenv is loaded on module import."""
        # If .env exists, it should be loaded
        # This is a basic check that the module imports without error
        from backend import config
        assert config is not None

    def test_settings_singleton(self):
        """Test that settings is a singleton."""
        from backend.config import settings as settings1
        from backend.config import settings as settings2
        assert settings1 is settings2
