"""Tests for backend.cli — BackendCLI all methods and main()."""
import os, pytest, json
from unittest.mock import patch, MagicMock
from io import StringIO

os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.cli import BackendCLI, main

class TestBackendCLI:
    def _mock_client(self):
        cli = BackendCLI("http://test:8000")
        cli.client = MagicMock()
        return cli

    def test_health_success(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code = 200; resp.json.return_value = {"status": "healthy"}
        resp.elapsed.total_seconds.return_value = 0.01
        cli.client.get.return_value = resp
        r = cli.health_check()
        assert r["status"] == "success" and r["data"]["status"] == "healthy"

    def test_health_error(self):
        cli = self._mock_client()
        cli.client.get.side_effect = Exception("conn refused")
        r = cli.health_check()
        assert r["status"] == "error"

    def test_test_endpoint_get(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code=200; resp.json.return_value={}; resp.text="{}"; resp.headers={}
        resp.elapsed.total_seconds.return_value = 0.01
        cli.client.get.return_value = resp
        r = cli.test_endpoint("/api/health")
        assert r["status"] == "success"

    def test_test_endpoint_post(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code=200; resp.json.return_value={}; resp.text="{}"; resp.headers={}
        resp.elapsed.total_seconds.return_value = 0.01
        cli.client.post.return_value = resp
        r = cli.test_endpoint("/api/test", "POST", {"key": "val"})
        assert r["status"] == "success"

    def test_test_endpoint_put(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code=200; resp.json.return_value={}; resp.text="{}"; resp.headers={}
        resp.elapsed.total_seconds.return_value = 0.01
        cli.client.put.return_value = resp
        r = cli.test_endpoint("/x", "PUT", {})
        assert r["status"] == "success"

    def test_test_endpoint_delete(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code=200; resp.json.return_value={}; resp.text="{}"; resp.headers={}
        resp.elapsed.total_seconds.return_value = 0.01
        cli.client.delete.return_value = resp
        r = cli.test_endpoint("/x", "DELETE")
        assert r["status"] == "success"

    def test_test_endpoint_unknown_method(self):
        cli = self._mock_client()
        r = cli.test_endpoint("/x", "PATCH")
        assert r["status"] == "error"

    def test_test_endpoint_exception(self):
        cli = self._mock_client()
        cli.client.get.side_effect = Exception("err")
        assert cli.test_endpoint("/x")["status"] == "error"

    def test_load_test(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code=200
        resp.elapsed.total_seconds.return_value = 0.01
        cli.client.get.return_value = resp
        r = cli.load_test("/api/health", 5)
        assert r["requests"] == 5 and r["errors"] == 0 and r["success_rate"] == 100.0

    def test_load_test_errors(self):
        cli = self._mock_client()
        cli.client.get.side_effect = Exception("err")
        r = cli.load_test("/api/health", 3)
        assert r["errors"] == 3

    def test_test_all_endpoints(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code=200; resp.json.return_value={}; resp.text="{}"; resp.headers={}
        resp.elapsed.total_seconds.return_value = 0.01
        cli.client.get.return_value = resp
        r = cli.test_all_endpoints()
        assert "/api/health" in r

    def test_get_api_schema(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.json.return_value = {"openapi": "3.0.0"}
        cli.client.get.return_value = resp
        r = cli.get_api_schema()
        assert r["status"] == "success"

    def test_get_api_schema_error(self):
        cli = self._mock_client()
        cli.client.get.side_effect = Exception("err")
        assert cli.get_api_schema()["status"] == "error"

    def test_list_endpoints(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.json.return_value = {"paths": {"/api/health": {"get": {}}}}
        cli.client.get.return_value = resp
        r = cli.list_endpoints()
        assert len(r["endpoints"]) == 1

    def test_list_endpoints_error(self):
        cli = self._mock_client()
        cli.client.get.side_effect = Exception("err")
        assert cli.list_endpoints()["status"] == "error"

    def test_benchmark(self):
        cli = self._mock_client()
        resp = MagicMock(); resp.status_code=200; resp.elapsed.total_seconds.return_value=0.01
        cli.client.get.return_value = resp
        r = cli.benchmark("/api/health", 5)
        assert r["requests"] == 5

    def test_close(self):
        cli = self._mock_client()
        cli.close()
        cli.client.close.assert_called_once()


class TestMain:
    @patch("backend.cli.BackendCLI")
    def test_health_cmd(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.health_check.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "health"]):
            main()
        inst.health_check.assert_called_once()

    @patch("backend.cli.BackendCLI")
    def test_test_cmd(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.test_endpoint.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "test", "/api/health"]):
            main()
        inst.test_endpoint.assert_called_once()

    @patch("backend.cli.BackendCLI")
    def test_load_cmd(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.load_test.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "load", "/api/health", "--requests", "5"]):
            main()

    @patch("backend.cli.BackendCLI")
    def test_test_all_cmd(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.test_all_endpoints.return_value = {}
        with patch("sys.argv", ["cli", "test-all"]):
            main()

    @patch("backend.cli.BackendCLI")
    def test_schema_cmd(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.get_api_schema.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "schema"]):
            main()

    @patch("backend.cli.BackendCLI")
    def test_list_cmd(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.list_endpoints.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "list"]):
            main()

    @patch("backend.cli.BackendCLI")
    def test_benchmark_cmd(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.benchmark.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "benchmark", "/api/health"]):
            main()

    @patch("backend.cli.BackendCLI")
    def test_no_cmd(self, MockCLI):
        with patch("sys.argv", ["cli"]):
            main()  # Should print help, not crash

    @patch("backend.cli.BackendCLI")
    def test_test_with_data(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.test_endpoint.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "test", "/api/x", "--method", "POST", "--data", '{"k":"v"}']):
            main()

    @patch("backend.cli.BackendCLI")
    def test_custom_url(self, MockCLI):
        inst = MagicMock(); MockCLI.return_value = inst
        inst.health_check.return_value = {"status": "success"}
        with patch("sys.argv", ["cli", "--url", "http://custom:9000", "health"]):
            main()
        MockCLI.assert_called_with("http://custom:9000")
