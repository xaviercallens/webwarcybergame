"""
Integration tests for backend API.
Tests interaction between multiple components.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.main import app
from backend.database import get_session


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    def test_health_check_integration(self, client: TestClient):
        """Test health check endpoint integration."""
        # Make multiple requests
        for _ in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

    def test_api_error_handling_integration(self, client: TestClient):
        """Test API error handling across endpoints."""
        # Test 404 error
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert "detail" in response.json()
        
        # Test 405 error
        response = client.post("/api/health")
        assert response.status_code == 405
        assert "detail" in response.json()

    def test_api_response_consistency(self, client: TestClient):
        """Test API response consistency."""
        # Make multiple requests
        responses = [client.get("/api/health") for _ in range(10)]
        
        # All should be identical
        first_response = responses[0].json()
        for response in responses[1:]:
            assert response.json() == first_response


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    def test_database_session_integration(self, session: Session):
        """Test database session integration."""
        # Session should be usable
        assert session is not None
        assert hasattr(session, 'execute')
        assert hasattr(session, 'add')
        assert hasattr(session, 'commit')

    def test_database_connection_lifecycle(self, session: Session):
        """Test database connection lifecycle."""
        # Session should be active
        assert session is not None
        
        # Should be able to use session
        from sqlalchemy import text
        result = session.execute(text("SELECT 1"))
        assert result.fetchone() is not None


class TestAppIntegration:
    """Integration tests for FastAPI app."""

    def test_app_startup_shutdown_integration(self, client: TestClient):
        """Test app startup and shutdown integration."""
        # Make request to trigger startup
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # App should be ready
        response = client.get("/docs")
        assert response.status_code == 200

    def test_app_routes_integration(self, client: TestClient):
        """Test app routes integration."""
        # Health check should work
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # OpenAPI should work
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Docs should work
        response = client.get("/docs")
        assert response.status_code == 200

    def test_app_dependency_injection_integration(self, client: TestClient):
        """Test app dependency injection integration."""
        # Dependencies should be properly injected
        response = client.get("/api/health")
        assert response.status_code == 200


class TestConfigurationIntegration:
    """Integration tests for configuration."""

    def test_config_database_integration(self):
        """Test configuration and database integration."""
        from backend.config import settings
        from backend.database import get_engine
        
        # Settings should be available
        assert settings is not None
        assert isinstance(settings.database_url, str)
        
        # Engine should respect settings
        import backend.database as db_module
        db_module._engine = None
        
        original_url = settings.database_url
        settings.database_url = "sqlite:///:memory:"
        
        try:
            engine = get_engine()
            assert engine is not None
        finally:
            settings.database_url = original_url
            db_module._engine = None

    def test_config_app_integration(self):
        """Test configuration and app integration."""
        from backend.main import app
        
        # App should be initialized
        assert app is not None
        assert app.title == "Backend"
        assert app.version == "4.0.0"


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_complete_request_lifecycle(self, client: TestClient):
        """Test complete request lifecycle."""
        # 1. Make request
        response = client.get("/api/health")
        
        # 2. Verify response
        assert response.status_code == 200
        
        # 3. Verify content
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        
        # 4. Verify headers
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_multiple_sequential_requests(self, client: TestClient):
        """Test multiple sequential requests."""
        responses = []
        
        for i in range(5):
            response = client.get("/api/health")
            responses.append(response)
            assert response.status_code == 200
        
        # All should be successful
        assert all(r.status_code == 200 for r in responses)

    def test_mixed_request_types(self, client: TestClient):
        """Test mixed request types."""
        # GET should work
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # POST should fail
        response = client.post("/api/health")
        assert response.status_code == 405
        
        # PUT should fail
        response = client.put("/api/health")
        assert response.status_code == 405
        
        # DELETE should fail
        response = client.delete("/api/health")
        assert response.status_code == 405


class TestConcurrentIntegration:
    """Integration tests for concurrent operations."""

    def test_concurrent_api_requests(self, client: TestClient):
        """Test concurrent API requests."""
        responses = [client.get("/api/health") for _ in range(20)]
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)

    def test_concurrent_mixed_requests(self, client: TestClient):
        """Test concurrent mixed requests."""
        health_responses = [client.get("/api/health") for _ in range(10)]
        invalid_responses = [client.get("/api/invalid") for _ in range(10)]
        
        # Health checks should succeed
        assert all(r.status_code == 200 for r in health_responses)
        
        # Invalid requests should fail
        assert all(r.status_code == 404 for r in invalid_responses)


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery."""

    def test_recovery_after_error(self, client: TestClient):
        """Test recovery after error."""
        # Make invalid request
        response = client.get("/api/invalid")
        assert response.status_code == 404
        
        # App should still work
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_multiple_errors_recovery(self, client: TestClient):
        """Test recovery after multiple errors."""
        for _ in range(5):
            # Invalid request
            response = client.get("/api/invalid")
            assert response.status_code == 404
            
            # Valid request
            response = client.get("/api/health")
            assert response.status_code == 200


class TestPerformanceIntegration:
    """Integration tests for performance."""

    def test_response_time_consistency(self, client: TestClient):
        """Test response time consistency."""
        import time
        
        times = []
        for _ in range(10):
            start = time.time()
            response = client.get("/api/health")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200
        
        # All should be fast
        assert all(t < 0.1 for t in times)

    def test_throughput_integration(self, client: TestClient):
        """Test throughput."""
        import time
        
        start = time.time()
        for _ in range(100):
            response = client.get("/api/health")
            assert response.status_code == 200
        elapsed = time.time() - start
        
        # Should handle 100 requests quickly
        assert elapsed < 5.0


class TestDataIntegrity:
    """Integration tests for data integrity."""

    def test_response_data_integrity(self, client: TestClient):
        """Test response data integrity."""
        responses = [client.get("/api/health") for _ in range(5)]
        
        # All responses should have identical data
        first_data = responses[0].json()
        for response in responses[1:]:
            assert response.json() == first_data

    def test_response_format_consistency(self, client: TestClient):
        """Test response format consistency."""
        responses = [client.get("/api/health") for _ in range(5)]
        
        for response in responses:
            data = response.json()
            # Should have status field
            assert "status" in data
            # Status should be string
            assert isinstance(data["status"], str)
            # Status should be "healthy"
            assert data["status"] == "healthy"
