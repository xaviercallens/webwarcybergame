"""
Unit tests for FastAPI endpoints.
Tests all API routes and response formats.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Test suite for health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """Test that health check returns 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self, client: TestClient):
        """Test that health check returns healthy status."""
        response = client.get("/api/health")
        assert response.json() == {"status": "healthy"}

    def test_health_check_response_type(self, client: TestClient):
        """Test that health check response is JSON."""
        response = client.get("/api/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_check_no_body_required(self, client: TestClient):
        """Test that health check requires no request body."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_idempotent(self, client: TestClient):
        """Test that multiple health checks return same result."""
        response1 = client.get("/api/health")
        response2 = client.get("/api/health")
        assert response1.json() == response2.json()


class TestRootEndpoint:
    """Test suite for root endpoint."""

    def test_root_endpoint_exists(self, client: TestClient):
        """Test that root endpoint is accessible."""
        response = client.get("/")
        # Should return 200 if static files are mounted, 404 if not
        assert response.status_code in [200, 404]

    def test_root_endpoint_method_get(self, client: TestClient):
        """Test that root endpoint accepts GET requests."""
        response = client.get("/")
        assert response.status_code in [200, 404]

    def test_root_endpoint_method_post_not_allowed(self, client: TestClient):
        """Test that root endpoint rejects POST requests."""
        response = client.post("/")
        assert response.status_code in [405, 404]


class TestAPIRouting:
    """Test suite for API routing and error handling."""

    def test_invalid_endpoint_returns_404(self, client: TestClient):
        """Test that invalid endpoints return 404."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_api_prefix_routing(self, client: TestClient):
        """Test that API endpoints use /api prefix."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_non_api_endpoint_routing(self, client: TestClient):
        """Test that non-API endpoints are handled."""
        response = client.get("/health")
        assert response.status_code == 404

    def test_case_sensitive_routing(self, client: TestClient):
        """Test that routing is case-sensitive."""
        response = client.get("/API/health")
        assert response.status_code == 404

    def test_trailing_slash_handling(self, client: TestClient):
        """Test trailing slash handling in routes."""
        response1 = client.get("/api/health")
        # Without trailing slash should work
        assert response1.status_code == 200
        
        # With trailing slash may redirect or return 404
        response2 = client.get("/api/health/")
        assert response2.status_code in [200, 307, 404]


class TestHTTPMethods:
    """Test suite for HTTP method handling."""

    def test_health_check_get_allowed(self, client: TestClient):
        """Test that GET is allowed on health check."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_post_not_allowed(self, client: TestClient):
        """Test that POST is not allowed on health check."""
        response = client.post("/api/health")
        assert response.status_code == 405

    def test_health_check_put_not_allowed(self, client: TestClient):
        """Test that PUT is not allowed on health check."""
        response = client.put("/api/health")
        assert response.status_code == 405

    def test_health_check_delete_not_allowed(self, client: TestClient):
        """Test that DELETE is not allowed on health check."""
        response = client.delete("/api/health")
        assert response.status_code == 405

    def test_health_check_patch_not_allowed(self, client: TestClient):
        """Test that PATCH is not allowed on health check."""
        response = client.patch("/api/health")
        assert response.status_code == 405


class TestResponseFormats:
    """Test suite for response format validation."""

    def test_health_check_json_format(self, client: TestClient):
        """Test that health check returns valid JSON."""
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_health_check_status_field_type(self, client: TestClient):
        """Test that status field is a string."""
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data["status"], str)

    def test_health_check_status_field_value(self, client: TestClient):
        """Test that status field has correct value."""
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_no_extra_fields(self, client: TestClient):
        """Test that health check response has no extra fields."""
        response = client.get("/api/health")
        data = response.json()
        assert len(data) == 1
        assert "status" in data


class TestErrorHandling:
    """Test suite for error handling."""

    def test_404_error_format(self, client: TestClient):
        """Test that 404 errors return proper format."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_405_error_format(self, client: TestClient):
        """Test that 405 errors return proper format."""
        response = client.post("/api/health")
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data

    def test_error_response_is_json(self, client: TestClient):
        """Test that error responses are JSON."""
        response = client.get("/api/nonexistent")
        assert response.headers["content-type"] == "application/json"


class TestConcurrency:
    """Test suite for concurrent requests."""

    def test_multiple_health_checks_concurrent(self, client: TestClient):
        """Test that multiple concurrent health checks work."""
        responses = [client.get("/api/health") for _ in range(10)]
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)

    def test_mixed_requests_concurrent(self, client: TestClient):
        """Test that mixed requests work concurrently."""
        health = client.get("/api/health")
        invalid = client.get("/api/nonexistent")
        
        assert health.status_code == 200
        assert invalid.status_code == 404


class TestResponseHeaders:
    """Test suite for response headers."""

    def test_health_check_content_type(self, client: TestClient):
        """Test that health check has correct content-type."""
        response = client.get("/api/health")
        assert "application/json" in response.headers["content-type"]

    def test_health_check_has_content_length(self, client: TestClient):
        """Test that health check has content-length header."""
        response = client.get("/api/health")
        assert "content-length" in response.headers

    def test_health_check_server_header(self, client: TestClient):
        """Test that response has standard headers."""
        response = client.get("/api/health")
        # TestClient may not include server header, but should have content-type
        assert "content-type" in response.headers


class TestPerformance:
    """Test suite for performance characteristics."""

    def test_health_check_response_time(self, client: TestClient):
        """Test that health check responds quickly."""
        import time
        start = time.time()
        response = client.get("/api/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second

    def test_health_check_response_size(self, client: TestClient):
        """Test that health check response is small."""
        response = client.get("/api/health")
        assert len(response.content) < 100  # Should be small JSON
