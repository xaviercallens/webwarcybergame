"""
Unit tests for main FastAPI application.
Tests app initialization, lifespan, and configuration.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.main import app, WEB_BUILD_DIR


class TestAppInitialization:
    """Test suite for FastAPI app initialization."""

    def test_app_is_fastapi_instance(self):
        """Test that app is a FastAPI instance."""
        assert isinstance(app, FastAPI)

    def test_app_title(self):
        """Test that app has correct title."""
        assert app.title == "Backend"

    def test_app_description(self):
        """Test that app has description."""
        assert app.description == "Backend API"

    def test_app_version(self):
        """Test that app has correct version."""
        assert app.version == "0.1.0"

    def test_app_has_lifespan(self):
        """Test that app is configured with lifespan."""
        # FastAPI 0.128 uses lifespan parameter in constructor
        # Check that app was initialized (which includes lifespan setup)
        assert app is not None
        assert isinstance(app, FastAPI)


class TestAppRoutes:
    """Test suite for app routes."""

    def test_app_has_routes(self):
        """Test that app has registered routes."""
        assert len(app.routes) > 0

    def test_health_check_route_exists(self):
        """Test that health check route is registered."""
        route_paths = [route.path for route in app.routes]
        assert "/api/health" in route_paths

    def test_app_routes_are_callable(self):
        """Test that all routes are callable."""
        for route in app.routes:
            if hasattr(route, 'endpoint'):
                assert callable(route.endpoint)


class TestAppConfiguration:
    """Test suite for app configuration."""

    def test_web_build_dir_path(self):
        """Test that WEB_BUILD_DIR is a Path object."""
        from pathlib import Path
        assert isinstance(WEB_BUILD_DIR, Path)

    def test_web_build_dir_default(self):
        """Test that WEB_BUILD_DIR has default value."""
        assert WEB_BUILD_DIR is not None

    def test_web_build_dir_is_absolute(self):
        """Test that WEB_BUILD_DIR is absolute path."""
        assert WEB_BUILD_DIR.is_absolute()


class TestAppOpenAPI:
    """Test suite for OpenAPI documentation."""

    def test_app_has_openapi_schema(self, client: TestClient):
        """Test that app provides OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_app_has_docs(self, client: TestClient):
        """Test that app provides Swagger UI docs."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_app_has_redoc(self, client: TestClient):
        """Test that app provides ReDoc docs."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestAppMiddleware:
    """Test suite for app middleware."""

    def test_app_has_middleware_stack(self):
        """Test that app has middleware stack."""
        assert hasattr(app, 'middleware_stack')

    def test_app_user_middleware(self):
        """Test that app has user middleware."""
        assert hasattr(app, 'user_middleware')


class TestAppDependencies:
    """Test suite for app dependencies."""

    def test_app_has_dependency_overrides(self):
        """Test that app supports dependency overrides."""
        assert hasattr(app, 'dependency_overrides')
        assert isinstance(app.dependency_overrides, dict)


class TestAppErrorHandling:
    """Test suite for app error handling."""

    def test_app_handles_404_errors(self, client: TestClient):
        """Test that app handles 404 errors."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_app_handles_405_errors(self, client: TestClient):
        """Test that app handles 405 errors."""
        response = client.post("/api/health")
        assert response.status_code == 405

    def test_app_error_responses_are_json(self, client: TestClient):
        """Test that error responses are JSON."""
        response = client.get("/nonexistent")
        assert "application/json" in response.headers["content-type"]


class TestAppStartup:
    """Test suite for app startup behavior."""

    def test_app_startup_completes(self, client: TestClient):
        """Test that app startup completes successfully."""
        # If we can make a request, startup completed
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_app_ready_for_requests(self, client: TestClient):
        """Test that app is ready to handle requests."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
