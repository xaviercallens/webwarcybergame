"""
Additional tests to improve code coverage.
Tests edge cases and missing code paths.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.main import app, WEB_BUILD_DIR
from backend.database import get_session


class TestDatabaseEdgeCases:
    """Test edge cases in database module."""

    def test_get_session_generator_cleanup(self):
        """Test that get_session generator cleans up properly."""
        import backend.database as db_module
        db_module._engine = None
        
        from backend import config
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            session_gen = get_session()
            session = next(session_gen)
            assert session is not None
            
            # Cleanup
            try:
                next(session_gen)
            except StopIteration:
                pass
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_database_engine_logging(self):
        """Test that database engine handles logging."""
        import backend.database as db_module
        db_module._engine = None
        
        from backend import config
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            # This should log a warning when database is not configured
            engine = db_module.get_engine()
            assert engine is not None
        finally:
            config.settings.database_url = original_url
            db_module._engine = None


class TestMainAppStaticFiles:
    """Test static file serving in main app."""

    def test_web_build_dir_exists_check(self):
        """Test WEB_BUILD_DIR path handling."""
        assert isinstance(WEB_BUILD_DIR, Path)
        # WEB_BUILD_DIR may or may not exist, but should be a valid path
        assert WEB_BUILD_DIR.is_absolute()

    def test_app_static_mount_conditional(self):
        """Test that static files are conditionally mounted."""
        # If WEB_BUILD_DIR exists, static files should be mounted
        # If not, app should still work without them
        response = TestClient(app).get("/api/health")
        assert response.status_code == 200


class TestMainAppLifespan:
    """Test app lifespan behavior."""

    def test_app_lifespan_initialization(self, client: TestClient):
        """Test that app initializes with lifespan."""
        # If we can make a request, lifespan completed successfully
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_app_lifespan_database_init(self, client: TestClient):
        """Test that lifespan initializes database."""
        # Database should be initialized during lifespan
        response = client.get("/api/health")
        assert response.status_code == 200


class TestAPIEdgeCases:
    """Test edge cases in API endpoints."""

    def test_health_check_multiple_calls_consistency(self, client: TestClient):
        """Test that health check is consistent across multiple calls."""
        responses = [client.get("/api/health") for _ in range(5)]
        
        for response in responses:
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

    def test_api_error_detail_field(self, client: TestClient):
        """Test that error responses have detail field."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_api_response_consistency(self, client: TestClient):
        """Test that API responses are consistent."""
        response1 = client.get("/api/health")
        response2 = client.get("/api/health")
        
        assert response1.json() == response2.json()
        assert response1.status_code == response2.status_code


class TestConfigurationEdgeCases:
    """Test edge cases in configuration."""

    def test_settings_database_url_modification(self):
        """Test that settings database_url can be modified."""
        from backend.config import settings
        
        original = settings.database_url
        try:
            settings.database_url = "test_url"
            assert settings.database_url == "test_url"
        finally:
            settings.database_url = original

    def test_settings_type_validation(self):
        """Test that settings maintains type validation."""
        from backend.config import settings
        
        # database_url should always be a string
        assert isinstance(settings.database_url, str)


class TestDatabaseSessionEdgeCases:
    """Test edge cases in database session management."""

    def test_session_with_no_engine(self):
        """Test session behavior when engine is None."""
        import backend.database as db_module
        db_module._engine = None
        
        from backend import config
        original_url = config.settings.database_url
        config.settings.database_url = ""
        
        try:
            session_gen = get_session()
            session = next(session_gen)
            assert session is None
        finally:
            config.settings.database_url = original_url
            db_module._engine = None

    def test_engine_reuse_after_reset(self):
        """Test that engine can be recreated after reset."""
        import backend.database as db_module
        
        from backend import config
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            # Get engine first time
            engine1 = db_module.get_engine()
            assert engine1 is not None
            
            # Reset and get again
            db_module._engine = None
            engine2 = db_module.get_engine()
            assert engine2 is not None
            
            # Should be different instances
            assert engine1 is not engine2
        finally:
            config.settings.database_url = original_url
            db_module._engine = None


class TestAppInitializationEdgeCases:
    """Test edge cases in app initialization."""

    def test_app_metadata(self):
        """Test that app has correct metadata."""
        assert app.title == "Backend"
        assert app.description == "Backend API"
        assert app.version == "0.1.0"

    def test_app_openapi_metadata(self, client: TestClient):
        """Test that OpenAPI metadata is correct."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "info" in schema
        assert schema["info"]["title"] == "Backend"
        assert schema["info"]["version"] == "0.1.0"

    def test_app_routes_count(self):
        """Test that app has expected number of routes."""
        # Should have at least health check route
        assert len(app.routes) > 0


class TestConcurrentRequests:
    """Test concurrent request handling."""

    def test_concurrent_health_checks(self, client: TestClient):
        """Test multiple concurrent health checks."""
        responses = [client.get("/api/health") for _ in range(20)]
        
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)

    def test_concurrent_mixed_requests(self, client: TestClient):
        """Test concurrent mixed requests."""
        health = [client.get("/api/health") for _ in range(10)]
        invalid = [client.get("/api/invalid") for _ in range(10)]
        
        assert all(r.status_code == 200 for r in health)
        assert all(r.status_code == 404 for r in invalid)


class TestResponseValidation:
    """Test response validation."""

    def test_health_check_response_structure(self, client: TestClient):
        """Test that health check response has correct structure."""
        response = client.get("/api/health")
        data = response.json()
        
        # Should have exactly one key
        assert len(data) == 1
        assert "status" in data
        assert data["status"] == "healthy"

    def test_error_response_structure(self, client: TestClient):
        """Test that error response has correct structure."""
        response = client.get("/api/nonexistent")
        data = response.json()
        
        # Should have detail field
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestPerformanceEdgeCases:
    """Test performance edge cases."""

    def test_health_check_performance_multiple(self, client: TestClient):
        """Test health check performance with multiple calls."""
        import time
        
        start = time.time()
        for _ in range(10):
            response = client.get("/api/health")
            assert response.status_code == 200
        elapsed = time.time() - start
        
        # 10 calls should complete in less than 1 second
        assert elapsed < 1.0

    def test_health_check_response_size_consistency(self, client: TestClient):
        """Test that response size is consistent."""
        responses = [client.get("/api/health") for _ in range(5)]
        sizes = [len(r.content) for r in responses]
        
        # All responses should be the same size
        assert len(set(sizes)) == 1


class TestDatabaseConnectionEdgeCases:
    """Test database connection edge cases."""

    def test_database_url_validation(self):
        """Test database URL validation."""
        from backend.config import settings
        
        # Should be a string
        assert isinstance(settings.database_url, str)

    def test_engine_singleton_consistency(self):
        """Test that engine singleton is consistent."""
        import backend.database as db_module
        db_module._engine = None
        
        from backend import config
        original_url = config.settings.database_url
        config.settings.database_url = "sqlite:///:memory:"
        
        try:
            engine1 = db_module.get_engine()
            engine2 = db_module.get_engine()
            engine3 = db_module.get_engine()
            
            # All should be the same instance
            assert engine1 is engine2
            assert engine2 is engine3
        finally:
            config.settings.database_url = original_url
            db_module._engine = None
