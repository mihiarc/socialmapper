# Testing the SRR-NRCS Project

This directory contains tests for the SRR-NRCS project. The tests are written using pytest.

## Setup

The tests are set up to run in a separate virtual environment from the main project. To set up the testing environment, run:

```bash
./setup_test_env.sh
```

This will:
1. Create a new virtual environment using uv
2. Install the package in development mode with testing dependencies
3. Run the tests

## Running Tests

To run all tests:

```bash
source .venv-test/bin/activate
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/core/test_config.py
```

To run a specific test function:

```bash
python -m pytest tests/core/test_config.py::TestConfig::test_get_path
```

To run tests with coverage report:

```bash
python -m pytest --cov=scripts tests/
```

## Test Structure

The tests are organized to mirror the project structure:

- `tests/conftest.py` - Contains shared pytest fixtures
- `tests/core/` - Tests for core functionality

## Testing Strategy

The tests are designed to:

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test how components work together
3. **Mock External Dependencies**: Use unittest.mock to mock external API calls

## Adding New Tests

When adding new functionality:

1. Create a test file that mirrors the module structure
2. Write tests before or alongside implementation
3. Use fixtures from conftest.py where possible
4. Use mocks for external dependencies

## Continuous Integration

The tests are automatically run when pushing to the repository. The workflow is defined in the `.github/workflows/tests.yml` file. 