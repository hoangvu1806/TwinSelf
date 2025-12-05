# Testing Guide

TwinSelf uses two types of tests to ensure quality:

## Unit Tests (Fast, Mocked)

**Purpose:** Test API logic without real services  
**Speed:** ~10 seconds  
**When:** Every commit (CI/CD)

```bash
# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=twinself --cov-report=term-missing
```

**What's tested:**
- ✅ API endpoint logic
- ✅ Request/response validation
- ✅ Error handling
- ✅ Data models

**What's mocked:**
- Chatbot (DigitalTwinChatbot)
- MLflow client
- Gemini evaluation model

## Integration Tests (Slow, Real Services)

**Purpose:** Test entire system with real services  
**Speed:** ~2-3 minutes  
**When:** Before deployment to production

### Prerequisites

1. Start MLflow server:
```bash
mlflow server --host 127.0.0.1 --port 5000
```

2. Start MLOps server:
```bash
python mlops_server.py
```

### Run Integration Tests

**Option 1: Manual**
```bash
pytest tests/test_integration.py -v -m integration
```

**Option 2: Automated (Windows)**
```powershell
.\scripts\run_integration_tests.ps1
```

**What's tested:**
- ✅ Real chatbot responses
- ✅ MLflow connection and logging
- ✅ Qdrant vector search
- ✅ End-to-end conversation flow
- ✅ User feedback storage

## Test Structure

```
tests/
├── test_api.py              # Unit tests for API endpoints
├── test_chatbot.py          # Unit tests for chatbot core
├── test_version_manager.py  # Unit tests for versioning
└── test_integration.py      # Integration tests (requires services)
```

## CI/CD Pipeline

GitHub Actions automatically runs unit tests on every push:

```yaml
# .github/workflows/ci.yml
- Python 3.11 on Windows
- Mock all external services
- Generate coverage report
- Upload to Codecov
```

**View CI status:** Check GitHub Actions tab

## Best Practices

### For Development
1. Run unit tests frequently: `pytest tests/ -v`
2. Check coverage: `pytest tests/ --cov=twinself`
3. Fix failing tests before committing

### Before Deployment
1. Run integration tests: `pytest tests/test_integration.py -v`
2. Verify all services are working
3. Check MLflow logs for errors
4. Test with real user scenarios

### Writing New Tests

**Unit Test Example:**
```python
def test_new_endpoint(client):
    """Test new endpoint with mocked services"""
    response = client.post("/new-endpoint", json={"data": "test"})
    assert response.status_code == 200
```

**Integration Test Example:**
```python
@pytest.mark.integration
def test_new_feature(check_services):
    """Test new feature with real services"""
    response = requests.post(
        "http://localhost:8001/new-endpoint",
        json={"data": "test"}
    )
    assert response.status_code == 200
```

## Troubleshooting

### Unit Tests Slow?
- Check if services are mocked properly
- Ensure `TestClient` is used (not real HTTP requests)

### Integration Tests Fail?
- Verify MLflow is running: `curl http://localhost:5000/health`
- Verify MLOps server is running: `curl http://localhost:8001/health`
- Check server logs for errors
- Wait for chatbot initialization (~30s)

### Coverage Too Low?
- Add tests for uncovered code
- Focus on critical paths first
- Aim for >80% coverage

## Quick Reference

```bash
# Unit tests only (fast)
pytest tests/ -v -m "not integration"

# Integration tests only (slow)
pytest tests/ -v -m integration

# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=twinself --cov-report=html

# Stop on first failure
pytest tests/ -x

# Verbose output
pytest tests/ -vv
```
