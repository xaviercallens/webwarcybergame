#!/bin/bash
# Backend Test Runner Script
# Usage: ./run_tests.sh [option]

set -e

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Show usage
show_usage() {
    echo "Backend Test Runner"
    echo ""
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  all              Run all tests (default)"
    echo "  unit             Run unit tests only"
    echo "  integration      Run integration tests only"
    echo "  functional       Run functional tests only"
    echo "  coverage         Run tests with coverage report"
    echo "  quick            Run quick tests (no coverage)"
    echo "  watch            Run tests in watch mode"
    echo "  cli              Show CLI help"
    echo "  health           Check backend health"
    echo "  test-api         Test API endpoints"
    echo "  load             Run load test"
    echo "  help             Show this help message"
    echo ""
}

# Install dependencies
install_deps() {
    print_header "Installing Dependencies"
    uv sync --extra test
    print_success "Dependencies installed"
}

# Run all tests
run_all_tests() {
    print_header "Running All Tests"
    uv run pytest tests/ -v
}

# Run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"
    uv run pytest tests/test_api.py tests/test_config.py tests/test_database.py tests/test_main.py -v
}

# Run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"
    uv run pytest tests/test_integration.py -v
}

# Run functional tests
run_functional_tests() {
    print_header "Running Functional Tests"
    uv run pytest tests/test_functional.py -v
}

# Run tests with coverage
run_coverage() {
    print_header "Running Tests with Coverage"
    uv run pytest tests/ --cov=backend --cov-report=term-missing --cov-report=html
    print_success "Coverage report generated (htmlcov/index.html)"
}

# Run quick tests
run_quick() {
    print_header "Running Quick Tests"
    uv run pytest tests/ -q
}

# Run tests in watch mode
run_watch() {
    print_header "Running Tests in Watch Mode"
    print_info "Press Ctrl+C to stop"
    uv run pytest tests/ --looponfail
}

# Show CLI help
show_cli_help() {
    print_header "Backend CLI Help"
    uv run python cli.py --help
}

# Check backend health
check_health() {
    print_header "Checking Backend Health"
    uv run python cli.py health
}

# Test API endpoints
test_api() {
    print_header "Testing API Endpoints"
    uv run python cli.py test-all
}

# Run load test
run_load_test() {
    print_header "Running Load Test"
    uv run python cli.py load /api/health --requests 100
}

# Main script logic
case "${1:-all}" in
    all)
        install_deps
        run_all_tests
        ;;
    unit)
        install_deps
        run_unit_tests
        ;;
    integration)
        install_deps
        run_integration_tests
        ;;
    functional)
        install_deps
        run_functional_tests
        ;;
    coverage)
        install_deps
        run_coverage
        ;;
    quick)
        install_deps
        run_quick
        ;;
    watch)
        install_deps
        run_watch
        ;;
    cli)
        show_cli_help
        ;;
    health)
        check_health
        ;;
    test-api)
        test_api
        ;;
    load)
        run_load_test
        ;;
    help)
        show_usage
        ;;
    *)
        print_error "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac

print_success "Done!"
