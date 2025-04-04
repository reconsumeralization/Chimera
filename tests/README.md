# Project Chimera Tests

This directory contains tests for Project Chimera, organized to mirror the structure of the `src` directory.

## Directory Structure

- `test_core/`: Tests for the `chimera_core` package
- `test_data/`: Tests for the `chimera_data` package
- `test_stdio_mcp/`: Tests for the `chimera_stdio_mcp` package
- `test_ui/`: Tests for the `chimera_ui` package
- `conftest.py`: Shared pytest fixtures and configuration

## Test Categories

### Unit Tests
Tests for individual functions and classes in isolation. These are the majority of the tests.

### Integration Tests
Tests for interactions between components within a package.

### End-to-End Tests
Tests for complete workflows across multiple packages.

## Running Tests

```bash
# Run all tests
pytest

# Run tests for a specific package
pytest tests/test_core

# Run tests with coverage
pytest --cov=src

# Run tests and generate a coverage report
pytest --cov=src --cov-report=html
```

## Writing Tests

### Guidelines

1. **Test organization**: Create test files that mirror the structure of the source code
2. **Test isolation**: Each test should be independent and not rely on the state from previous tests
3. **Mocking**: Use pytest fixtures and mocks to isolate tests from external dependencies
4. **Coverage**: Aim for high test coverage, especially for critical functionality
5. **Async testing**: Use pytest-asyncio for testing async functions

### Example Test

```python
import pytest
from src.chimera_core.services.some_service import SomeService

def test_some_functionality():
    # Arrange
    service = SomeService()
    
    # Act
    result = service.do_something()
    
    # Assert
    assert result == expected_value
```

## Test Data

Test data files should be placed in a `fixtures` directory within the relevant test package.

## CI Integration

These tests are run automatically in CI/CD pipelines on pull requests and before releases. 