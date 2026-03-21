"""
Command-line interface for backend testing and interaction.
Provides tools to test and interact with the backend API.
"""

import json
import time
import argparse
from typing import Optional, Dict, Any

import httpx


class BackendCLI:
    """CLI for backend interaction and testing."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize CLI with base URL."""
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)

    def health_check(self) -> Dict[str, Any]:
        """Check backend health."""
        try:
            response = self.client.get("/api/health")
            return {
                "status": "success",
                "code": response.status_code,
                "data": response.json(),
                "time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Test a specific endpoint."""
        try:
            if method == "GET":
                response = self.client.get(endpoint)
            elif method == "POST":
                response = self.client.post(endpoint, json=data)
            elif method == "PUT":
                response = self.client.put(endpoint, json=data)
            elif method == "DELETE":
                response = self.client.delete(endpoint)
            else:
                return {"status": "error", "error": f"Unknown method: {method}"}
            
            return {
                "status": "success",
                "code": response.status_code,
                "data": response.json() if response.text else None,
                "headers": dict(response.headers),
                "time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def load_test(self, endpoint: str, num_requests: int = 100, 
                 concurrent: bool = False) -> Dict[str, Any]:
        """Load test an endpoint."""
        times = []
        errors = 0
        
        try:
            start = time.time()
            
            for _ in range(num_requests):
                try:
                    response = self.client.get(endpoint)
                    times.append(response.elapsed.total_seconds())
                    if response.status_code != 200:
                        errors += 1
                except Exception:
                    errors += 1
            
            total_time = time.time() - start
            
            return {
                "status": "success",
                "requests": num_requests,
                "errors": errors,
                "success_rate": (num_requests - errors) / num_requests * 100,
                "total_time": total_time,
                "avg_time": sum(times) / len(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "throughput": num_requests / total_time
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all available endpoints."""
        endpoints = [
            ("/api/health", "GET"),
            ("/openapi.json", "GET"),
            ("/docs", "GET"),
            ("/redoc", "GET"),
        ]
        
        results = {}
        for endpoint, method in endpoints:
            results[endpoint] = self.test_endpoint(endpoint, method)
        
        return results

    def get_api_schema(self) -> Dict[str, Any]:
        """Get API schema."""
        try:
            response = self.client.get("/openapi.json")
            return {
                "status": "success",
                "schema": response.json()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def list_endpoints(self) -> Dict[str, Any]:
        """List all available endpoints."""
        try:
            response = self.client.get("/openapi.json")
            schema = response.json()
            
            endpoints = []
            for path, methods in schema.get("paths", {}).items():
                for method in methods.keys():
                    if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        endpoints.append({
                            "path": path,
                            "method": method.upper()
                        })
            
            return {
                "status": "success",
                "endpoints": endpoints
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def benchmark(self, endpoint: str, num_requests: int = 100) -> Dict[str, Any]:
        """Benchmark an endpoint."""
        return self.load_test(endpoint, num_requests)

    def close(self):
        """Close the client."""
        self.client.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CyberWar Backend CLI - Test and interact with the backend"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Health check command
    subparsers.add_parser("health", help="Check backend health")
    
    # Test endpoint command
    test_parser = subparsers.add_parser("test", help="Test an endpoint")
    test_parser.add_argument("endpoint", help="Endpoint to test")
    test_parser.add_argument("--method", default="GET", help="HTTP method")
    test_parser.add_argument("--data", help="JSON data for POST/PUT")
    
    # Load test command
    load_parser = subparsers.add_parser("load", help="Load test an endpoint")
    load_parser.add_argument("endpoint", help="Endpoint to test")
    load_parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    
    # Test all endpoints command
    subparsers.add_parser("test-all", help="Test all endpoints")
    
    # Get schema command
    subparsers.add_parser("schema", help="Get API schema")
    
    # List endpoints command
    subparsers.add_parser("list", help="List all endpoints")
    
    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Benchmark an endpoint")
    bench_parser.add_argument("endpoint", help="Endpoint to benchmark")
    bench_parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = BackendCLI(args.url)
    
    try:
        if args.command == "health":
            result = cli.health_check()
            print(json.dumps(result, indent=2))
        
        elif args.command == "test":
            data = None
            if args.data:
                data = json.loads(args.data)
            result = cli.test_endpoint(args.endpoint, args.method, data)
            print(json.dumps(result, indent=2))
        
        elif args.command == "load":
            result = cli.load_test(args.endpoint, args.requests)
            print(json.dumps(result, indent=2))
        
        elif args.command == "test-all":
            result = cli.test_all_endpoints()
            print(json.dumps(result, indent=2))
        
        elif args.command == "schema":
            result = cli.get_api_schema()
            print(json.dumps(result, indent=2))
        
        elif args.command == "list":
            result = cli.list_endpoints()
            print(json.dumps(result, indent=2))
        
        elif args.command == "benchmark":
            result = cli.benchmark(args.endpoint, args.requests)
            print(json.dumps(result, indent=2))
    
    finally:
        cli.close()


if __name__ == "__main__":
    main()
