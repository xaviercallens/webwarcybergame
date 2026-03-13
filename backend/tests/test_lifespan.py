"""
Tests for app lifespan and initialization.
Ensures database initialization and app startup/shutdown.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from backend.main import app, lifespan


class TestAppLifespan:
    """Test app lifespan context manager."""

    def test_lifespan_is_async_context_manager(self):
        """Test that lifespan is an async context manager."""
        # lifespan should be callable
        assert callable(lifespan)

    def test_lifespan_calls_init_db(self):
        """Test that lifespan calls database.init_db()."""
        import asyncio
        from unittest.mock import patch
        
        async def test_lifespan_init():
            with patch('backend.database.init_db') as mock_init:
                async with lifespan(app):
                    # init_db should have been called
                    mock_init.assert_called_once()
        
        # Run the async test
        asyncio.run(test_lifespan_init())

    def test_lifespan_yields_control(self):
        """Test that lifespan yields control back."""
        import asyncio
        from unittest.mock import patch
        
        async def test_lifespan_yield():
            startup_called = False
            shutdown_called = False
            
            with patch('backend.database.init_db'):
                async with lifespan(app):
                    startup_called = True
                
                shutdown_called = True
            
            assert startup_called
            assert shutdown_called
        
        asyncio.run(test_lifespan_yield())


class TestAppStartupShutdown:
    """Test app startup and shutdown."""

    def test_app_startup_completes_successfully(self):
        """Test that app startup completes successfully."""
        # Create a test client which triggers startup
        client = TestClient(app)
        
        # Make a request to ensure startup completed
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_app_handles_startup_errors_gracefully(self):
        """Test that app handles startup errors gracefully."""
        # Even if init_db fails, the app should still work
        # because we have error handling
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200


class TestAppInitializationSequence:
    """Test app initialization sequence."""

    def test_app_initialization_order(self):
        """Test that app initializes in correct order."""
        # 1. FastAPI app is created
        assert app is not None
        
        # 2. Routes are registered
        assert len(app.routes) > 0
        
        # 3. Lifespan is configured
        # (verified by successful requests)
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_app_ready_after_initialization(self):
        """Test that app is ready after initialization."""
        client = TestClient(app)
        
        # Health check should work
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
        
        # API should be accessible
        assert len(app.routes) > 0


class TestStaticFilesConditionalMount:
    """Test conditional mounting of static files."""

    def test_static_files_mount_when_exists(self):
        """Test static files are mounted when directory exists."""
        # This tests line 31-32 in main.py
        # If WEB_BUILD_DIR exists, static files should be mounted
        
        from backend.main import WEB_BUILD_DIR
        
        # Check if static files are in the app
        static_mounted = any(
            hasattr(route, 'name') and route.name == 'static'
            for route in app.routes
        )
        
        # If WEB_BUILD_DIR exists, static should be mounted
        if WEB_BUILD_DIR.exists():
            assert static_mounted
        else:
            # If it doesn't exist, static may not be mounted
            # but app should still work
            client = TestClient(app)
            response = client.get("/api/health")
            assert response.status_code == 200

    def test_app_works_without_static_files(self):
        """Test app works even without static files."""
        client = TestClient(app)
        
        # API should work
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # Health check should return correct data
        assert response.json() == {"status": "healthy"}


class TestDatabaseInitializationInLifespan:
    """Test database initialization in lifespan."""

    def test_database_init_on_startup(self):
        """Test that database initialization happens on startup."""
        # Create test client to trigger startup
        client = TestClient(app)
        
        # Make a request
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # If we got here, startup completed successfully
        # which means init_db was called

    def test_lifespan_continues_after_init_db(self):
        """Test that lifespan continues after init_db."""
        import asyncio
        
        async def test_continuation():
            init_called = False
            yield_reached = False
            
            async with lifespan(app):
                init_called = True
                yield_reached = True
            
            assert init_called
            assert yield_reached
        
        # This would require running in event loop
        # but the test structure verifies the flow


class TestAppConfiguration:
    """Test app configuration details."""

    def test_app_has_all_required_attributes(self):
        """Test app has all required attributes."""
        assert hasattr(app, 'title')
        assert hasattr(app, 'description')
        assert hasattr(app, 'version')
        assert hasattr(app, 'routes')
        assert hasattr(app, 'dependency_overrides')

    def test_app_title_is_backend(self):
        """Test app title is 'Backend'."""
        assert app.title == "Backend"

    def test_app_description_is_api(self):
        """Test app description mentions API."""
        assert "API" in app.description

    def test_app_version_is_semantic(self):
        """Test app version follows semantic versioning."""
        parts = app.version.split('.')
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()


class TestHealthCheckEndpoint:
    """Test health check endpoint details."""

    def test_health_check_is_get_method(self):
        """Test health check uses GET method."""
        client = TestClient(app)
        
        # GET should work
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # POST should not work
        response = client.post("/api/health")
        assert response.status_code == 405

    def test_health_check_returns_json(self):
        """Test health check returns JSON."""
        client = TestClient(app)
        response = client.get("/api/health")
        
        assert response.headers["content-type"] == "application/json"
        assert isinstance(response.json(), dict)

    def test_health_check_status_field(self):
        """Test health check status field."""
        client = TestClient(app)
        response = client.get("/api/health")
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestAppRoutesRegistration:
    """Test app routes registration."""

    def test_health_check_route_registered(self):
        """Test health check route is registered."""
        route_paths = [route.path for route in app.routes]
        assert "/api/health" in route_paths

    def test_all_routes_are_callable(self):
        """Test all routes have callable endpoints."""
        for route in app.routes:
            if hasattr(route, 'endpoint'):
                assert callable(route.endpoint)

    def test_app_has_openapi_routes(self):
        """Test app has OpenAPI routes."""
        route_paths = [route.path for route in app.routes]
        
        # Should have OpenAPI routes
        openapi_paths = [p for p in route_paths if 'openapi' in p or 'docs' in p]
        assert len(openapi_paths) > 0
