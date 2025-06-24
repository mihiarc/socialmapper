# SocialMapper Testing Infrastructure

This directory contains a comprehensive testing suite for SocialMapper, implementing modern Python testing practices for 2025.

## Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── README.md               # This file
├── unit/                   # Fast, isolated unit tests
│   ├── __init__.py
│   ├── test_api_client.py          # API client and Result types
│   ├── test_census_service.py      # Census data services
│   ├── test_coordinate_validation.py # Property-based validation tests
│   └── test_export_formats.py     # Snapshot tests for outputs
├── integration/            # Slower integration tests
│   ├── __init__.py
│   └── test_pipeline_end_to_end.py # Full pipeline testing
└── fixtures/               # Test data and fixtures
```

## Testing Technologies

### Core Testing Framework
- **pytest** - Modern test runner with extensive plugin ecosystem
- **pytest-asyncio** - Support for async/await testing
- **pytest-mock** - Enhanced mocking capabilities
- **pytest-benchmark** - Performance testing and regression detection

### Advanced Testing Techniques
- **Hypothesis** - Property-based testing for edge case discovery
- **Syrupy** - Snapshot testing for output consistency
- **mutmut** - Mutation testing for test quality assessment
- **respx** - HTTP mocking for API testing
- **Faker** - Realistic test data generation

## Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests with external dependencies
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.api` - Tests for new API components
- `@pytest.mark.async` - Tests using async/await
- `@pytest.mark.performance` - Performance and benchmark tests
- `@pytest.mark.external` - Tests requiring external APIs (disabled by default)

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run only unit tests
uv run pytest -m unit

# Run tests excluding slow ones
uv run pytest -m "not slow"

# Run specific test file
uv run pytest tests/unit/test_coordinate_validation.py

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=socialmapper
```

### Property-Based Testing

```bash
# Run property-based tests with more examples
uv run pytest tests/unit/test_coordinate_validation.py --hypothesis-show-statistics

# Run with specific Hypothesis settings
uv run pytest --hypothesis-max-examples=1000
```

### Snapshot Testing

```bash
# Update snapshots after intentional changes
uv run pytest --snapshot-update

# Review snapshot changes
uv run pytest tests/unit/test_export_formats.py -v
```

### Performance Testing

```bash
# Run benchmark tests
uv run pytest -m benchmark

# Run benchmarks with comparison
uv run pytest --benchmark-compare
```

### Mutation Testing

```bash
# Run mutation testing (requires all tests to pass first)
mutmut run

# View mutation testing results
mutmut browse

# Test specific mutants
mutmut run --paths-to-mutate socialmapper/util/coordinate_validation.py
```

## Test Fixtures

### Core Fixtures (from conftest.py)

- `temp_dir` - Temporary directory for file operations
- `sample_coordinates` - Seattle coordinates for testing
- `sample_addresses` - List of test addresses
- `sample_poi_data` - Mock POI data
- `sample_census_data` - Mock census demographics
- `sample_geodataframe` - GeoPandas test data
- `mock_osm_response` - OpenStreetMap API response
- `mock_census_response` - Census API response
- `mock_geocoding_response` - Geocoding API response

### Specialized Fixtures

- `large_dataset` - For performance testing
- `async_sample_data` - For async testing
- `hypothesis_settings` - Property-based test configuration

## Writing New Tests

### Unit Tests

```python
import pytest
from socialmapper.module import function_to_test

@pytest.mark.unit
def test_function_behavior(sample_data_fixture):
    """Test function with clear description."""
    result = function_to_test(sample_data_fixture)
    assert result == expected_value
```

### Property-Based Tests

```python
from hypothesis import given, strategies as st

@given(st.floats(min_value=-90.0, max_value=90.0))
def test_coordinate_validation(latitude):
    """Test coordinate validation with random inputs."""
    result = validate_coordinate(latitude, 0.0)
    assert result.is_valid
```

### Snapshot Tests

```python
@pytest.mark.unit
def test_output_format(snapshot, input_data):
    """Test output format remains consistent."""
    result = process_data(input_data)
    assert result == snapshot
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

### Integration Tests

```python
@pytest.mark.integration
def test_full_pipeline(mock_external_apis, temp_dir):
    """Test complete pipeline integration."""
    config = {"output_dir": str(temp_dir)}
    result = run_pipeline(config)
    assert result["status"] == "completed"
```

## Continuous Integration

Tests are configured to run automatically with:

- **Fast feedback**: Unit tests run on every commit
- **Comprehensive testing**: Integration tests run on pull requests
- **Performance monitoring**: Benchmark tests track performance regressions
- **Quality assurance**: Mutation testing ensures test effectiveness

## Best Practices

### Test Organization
- Keep tests close to the code they test
- Use descriptive test names that explain the behavior being tested
- Group related tests in classes
- Use fixtures to reduce duplication

### Test Quality
- Test both happy path and error conditions
- Use property-based testing for complex validation logic
- Mock external dependencies to ensure test isolation
- Verify not just that code works, but that it fails correctly

### Performance
- Keep unit tests fast (< 1 second each)
- Use integration tests for slower end-to-end scenarios
- Monitor performance with benchmark tests
- Use appropriate test markers to control test execution

### Maintenance
- Update snapshots when outputs intentionally change
- Run mutation testing periodically to verify test quality
- Keep test dependencies up to date
- Review and clean up obsolete tests

## Test Data Security

- Never commit real API keys or sensitive data
- Use mock data that resembles real data structure
- Environment variables in tests use "test_" prefixes
- All external API calls are mocked by default

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root with `uv run pytest`
2. **Fixture Not Found**: Check that fixtures are properly defined in `conftest.py`
3. **Snapshot Failures**: Use `--snapshot-update` after intentional changes
4. **Async Test Failures**: Ensure proper `@pytest.mark.asyncio` decoration
5. **External API Tests**: Check that external test environment variables are set

### Debug Mode

```bash
# Run tests with debugging
uv run pytest --pdb

# Run with detailed output
uv run pytest -vv --tb=long

# Run single test with debugging
uv run pytest tests/unit/test_file.py::test_function --pdb
```

This testing infrastructure ensures SocialMapper maintains high code quality, catches regressions early, and provides confidence for refactoring and new feature development.