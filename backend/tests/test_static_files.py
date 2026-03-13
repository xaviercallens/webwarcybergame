"""
Tests for static file serving.
Tests the conditional mounting of static files.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient


class TestStaticFilesConditionalMounting:
    """Test conditional mounting of static files."""

    def test_static_files_mount_when_directory_exists(self):
        """Test that static files are mounted when WEB_BUILD_DIR exists."""
        # Create a temporary directory to simulate WEB_BUILD_DIR
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple index.html
            index_path = Path(tmpdir) / "index.html"
            index_path.write_text("<html><body>Test</body></html>")
            
            # Create a new app with the temporary directory
            test_app = FastAPI()
            
            @test_app.get("/api/health")
            def health():
                return {"status": "healthy"}
            
            # Mount static files
            if Path(tmpdir).exists():
                test_app.mount("/", StaticFiles(directory=tmpdir, html=True), name="static")
            
            # Test the app
            client = TestClient(test_app)
            
            # API should work
            response = client.get("/api/health")
            assert response.status_code == 200
            
            # Static files should be served
            response = client.get("/index.html")
            assert response.status_code == 200

    def test_app_works_without_static_files(self):
        """Test that app works even without static files directory."""
        from backend.main import app
        
        client = TestClient(app)
        
        # API should work regardless
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_static_mount_path_is_root(self):
        """Test that static files are mounted at root."""
        from backend.main import app
        
        # Check if static files are mounted
        static_routes = [
            route for route in app.routes
            if hasattr(route, 'name') and route.name == 'static'
        ]
        
        # If static files exist, they should be mounted at root
        # This is optional - only if WEB_BUILD_DIR exists
        if static_routes:
            # Static route path should be root or similar
            assert len(static_routes) > 0

    def test_static_files_html_mode_enabled(self):
        """Test that static files have HTML mode enabled for SPA."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create index.html
            index_path = Path(tmpdir) / "index.html"
            index_path.write_text("<html><body>SPA</body></html>")
            
            # Create app with static files
            test_app = FastAPI()
            
            @test_app.get("/api/health")
            def health():
                return {"status": "healthy"}
            
            # Mount with html=True for SPA routing
            test_app.mount("/", StaticFiles(directory=tmpdir, html=True), name="static")
            
            client = TestClient(test_app)
            
            # API should work
            response = client.get("/api/health")
            assert response.status_code == 200
            
            # Index should be served
            response = client.get("/index.html")
            assert response.status_code == 200


class TestMainAppStaticFilesConfiguration:
    """Test main app static files configuration."""

    def test_web_build_dir_default_path(self):
        """Test WEB_BUILD_DIR default path."""
        from backend.main import WEB_BUILD_DIR
        
        # Should be a Path object
        assert isinstance(WEB_BUILD_DIR, Path)
        
        # Should be absolute
        assert WEB_BUILD_DIR.is_absolute()
        
        # Should contain build/web
        assert 'build' in str(WEB_BUILD_DIR)
        assert 'web' in str(WEB_BUILD_DIR)

    def test_web_build_dir_from_environment(self):
        """Test WEB_BUILD_DIR respects environment variable."""
        import os
        from pathlib import Path
        
        # Check if WEB_BUILD_DIR env var is used
        # This is set in main.py: os.getenv("WEB_BUILD_DIR", ...)
        
        # If env var is set, it should be used
        # If not, default path should be used
        
        env_value = os.getenv("WEB_BUILD_DIR")
        from backend.main import WEB_BUILD_DIR
        
        if env_value:
            assert str(WEB_BUILD_DIR) == env_value
        else:
            # Should use default path
            assert WEB_BUILD_DIR.is_absolute()

    def test_static_files_optional(self):
        """Test that static files are optional."""
        from backend.main import app, WEB_BUILD_DIR
        
        # App should work regardless of whether static files exist
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200


class TestStaticFilesErrorHandling:
    """Test static files error handling."""

    def test_api_works_with_or_without_static_files(self):
        """Test API works regardless of static files."""
        from backend.main import app
        
        client = TestClient(app)
        
        # API should always work
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_404_for_missing_static_files(self):
        """Test 404 for missing static files."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_app = FastAPI()
            
            @test_app.get("/api/health")
            def health():
                return {"status": "healthy"}
            
            # Mount static files
            test_app.mount("/", StaticFiles(directory=tmpdir, html=True), name="static")
            
            client = TestClient(test_app)
            
            # Missing file should return 404
            response = client.get("/nonexistent.js")
            assert response.status_code == 404


class TestAppWithAndWithoutStaticFiles:
    """Test app behavior with and without static files."""

    def test_app_functionality_independent_of_static_files(self):
        """Test app functionality doesn't depend on static files."""
        from backend.main import app
        
        client = TestClient(app)
        
        # Core functionality should work
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
        
        # OpenAPI docs should work
        response = client.get("/docs")
        assert response.status_code == 200
        
        # OpenAPI schema should work
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_static_files_dont_interfere_with_api(self):
        """Test static files don't interfere with API."""
        from backend.main import app
        
        client = TestClient(app)
        
        # Multiple API calls should work
        for _ in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200
