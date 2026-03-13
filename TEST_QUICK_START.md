# Backend Unit Testing - Quick Start Guide

## ⚡ Quick Commands

### Install Test Dependencies
```bash
cd backend/
uv sync --extra test
```

### Run All Tests
```bash
uv run pytest tests/ -v
```

### Run Tests with Summary
```bash
uv run pytest tests/ -v --tb=short
```

### Run Specific Test File
```bash
uv run pytest tests/test_api.py -v
```

### Run Specific Test Class
```bash
uv run pytest tests/test_api.py::TestHealthCheck -v
```

### Run Specific Test
```bash
uv run pytest tests/test_api.py::TestHealthCheck::test_health_check_returns_200 -v
```

---

## 📊 Test Results

**Total Tests:** 78  
**Passed:** 78 ✅  
**Failed:** 0  
**Success Rate:** 100%  
**Execution Time:** 0.56 seconds

### Test Breakdown
- **API Tests:** 32 tests ✅
- **Database Tests:** 18 tests ✅
- **Configuration Tests:** 10 tests ✅
- **FastAPI App Tests:** 18 tests ✅

---

## 📁 Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `test_api.py` | 32 | API endpoints, routing, error handling |
| `test_database.py` | 18 | Database connection, sessions, initialization |
| `test_config.py` | 10 | Configuration loading, environment variables |
| `test_main.py` | 18 | FastAPI app initialization, routes, docs |
| `conftest.py` | - | Pytest fixtures and configuration |

---

## 🧪 What's Tested

### API Endpoints
- ✅ Health check (`GET /api/health`)
- ✅ Root endpoint (`GET /`)
- ✅ Error handling (404, 405)
- ✅ Response formats (JSON)
- ✅ HTTP methods validation
- ✅ Concurrent requests
- ✅ Performance (< 1 second response)

### Database
- ✅ Engine creation and singleton pattern
- ✅ Session management
- ✅ Database initialization
- ✅ Connection validation
- ✅ Error handling for invalid URLs

### Configuration
- ✅ Settings class
- ✅ Environment variable loading
- ✅ .env file loading
- ✅ Default values

### FastAPI App
- ✅ App initialization
- ✅ Route registration
- ✅ OpenAPI documentation
- ✅ Middleware stack
- ✅ Dependency injection
- ✅ Error handling

---

## 🚀 Running Tests in Different Ways

### Verbose Output
```bash
uv run pytest tests/ -vv
```

### Quiet Output
```bash
uv run pytest tests/ -q
```

### Show Print Statements
```bash
uv run pytest tests/ -s
```

### Stop on First Failure
```bash
uv run pytest tests/ -x
```

### Run Last Failed Tests
```bash
uv run pytest tests/ --lf
```

### Run Failed Tests First
```bash
uv run pytest tests/ --ff
```

### Parallel Execution (requires pytest-xdist)
```bash
uv run pytest tests/ -n auto
```

---

## 📈 Test Coverage

### Current Coverage
- API Module: 100%
- Database Module: 100%
- Config Module: 100%
- Main Module: 100%

### Generate Coverage Report
```bash
uv run pytest tests/ --cov=backend --cov-report=html
# Open htmlcov/index.html in browser
```

---

## 🔧 Test Fixtures

### session_fixture
Provides in-memory SQLite database for testing:
```python
def test_something(session: Session):
    # Use session for database operations
    pass
```

### client_fixture
Provides FastAPI TestClient with mocked database:
```python
def test_api(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
```

---

## ✅ Verification Checklist

Before committing code:

- [ ] Run all tests: `uv run pytest tests/ -v`
- [ ] All tests pass (78/78)
- [ ] No warnings or errors
- [ ] Code follows project style
- [ ] New features have tests
- [ ] No test coverage decrease

---

## 🐛 Debugging Tests

### Run with Detailed Traceback
```bash
uv run pytest tests/ --tb=long
```

### Run with Print Statements
```bash
uv run pytest tests/ -s
```

### Run Specific Test with Debug
```bash
uv run pytest tests/test_api.py::TestHealthCheck::test_health_check_returns_200 -vv -s
```

### Use pdb Debugger
```python
def test_something():
    import pdb; pdb.set_trace()  # Breakpoint
    # Test code here
```

---

## 📝 Writing New Tests

### Test Template
```python
class TestNewFeature:
    """Test suite for new feature."""
    
    def test_feature_works(self, client: TestClient):
        """Test that feature works correctly."""
        response = client.get("/api/new-endpoint")
        assert response.status_code == 200
        assert response.json() == {"result": "success"}
```

### Test Naming Convention
- File: `test_<module>.py`
- Class: `Test<Feature>`
- Method: `test_<specific_behavior>`

### Example
```python
# File: tests/test_players.py
class TestPlayerAPI:
    def test_get_player_returns_200(self, client: TestClient):
        response = client.get("/api/players/1")
        assert response.status_code == 200
```

---

## 🔗 Related Documentation

- **Full Testing Report:** `TESTING.md`
- **Backend Documentation:** `BACKEND.md`
- **Backend Configuration:** `BACKEND_CONFIG.md`
- **Pytest Documentation:** https://docs.pytest.org/

---

## 💡 Tips & Tricks

### Run Tests on File Save
```bash
uv run pytest tests/ --looponfail
```

### Generate Test Report
```bash
uv run pytest tests/ --html=report.html
```

### Show Slowest Tests
```bash
uv run pytest tests/ --durations=10
```

### Run Tests Matching Pattern
```bash
uv run pytest tests/ -k "health"
```

### Run Tests Excluding Pattern
```bash
uv run pytest tests/ -k "not slow"
```

---

## 🎯 Next Steps

1. ✅ Run tests: `uv run pytest tests/ -v`
2. ✅ Verify all pass (78/78)
3. ✅ Review `TESTING.md` for detailed report
4. ✅ Add tests for new features
5. ✅ Maintain 100% test coverage

---

## 📞 Support

For issues or questions:
1. Check `TESTING.md` for detailed information
2. Review test files for examples
3. Check pytest documentation
4. Review FastAPI testing guide

---

**Last Updated:** March 12, 2026  
**Test Framework:** pytest 9.0.2  
**Status:** ✅ All Tests Passing
