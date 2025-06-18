# Error Handling Improvements for SocialMapper

## Summary

Implemented a comprehensive error handling system for SocialMapper to address issues with vague type errors in tutorials. The new system provides clear, actionable error messages with helpful suggestions for users.

## Changes Made

### 1. Custom Exception Hierarchy (`socialmapper/exceptions.py`)
- Created base `SocialMapperError` class with rich context support
- Implemented specific exception types for different error categories:
  - Configuration errors (missing API keys, invalid config)
  - Validation errors (invalid locations, census variables, travel times)
  - Data processing errors (no data found, insufficient data)
  - External API errors (Census API, OpenStreetMap, geocoding)
  - File system errors (file not found, permissions)
  - Analysis errors (isochrone generation, network analysis)
  - Visualization errors (map generation)

### 2. Error Handling Utilities (`socialmapper/util/error_handling.py`)
- Context managers for error handling (`error_context`, `suppress_and_log`)
- Decorators for retry logic and fallbacks
- Error collection for batch operations
- Type and range validation helpers
- Structured logging integration

### 3. Tutorial Helper (`socialmapper/tutorial_helper.py`)
- `tutorial_error_handler` context manager for user-friendly error messages
- Specific handling for common tutorial errors
- Dependency checking utilities
- Configuration validation helpers

### 4. Pipeline Integration
- Updated `orchestrator.py` to use new error handling
- Added validation to `PipelineConfig` with proper error types
- Enhanced error context in all pipeline stages
- Better error propagation and chaining

### 5. Module Updates
- **extraction.py**: Better error handling for POI extraction
- **census.py**: Improved census API error handling
- **isochrone.py**: Enhanced isochrone generation errors
- **api/client.py**: Integrated custom exceptions with Result types
- **api/builder.py**: Immediate validation with specific error types

### 6. API Improvements
- Extended `ErrorType` enum with `CONFIGURATION` type
- Mapped custom exceptions to API error types
- Enhanced error context in Result types

## Key Features

### 1. Clear Error Messages
Every error now provides:
- Human-readable explanation
- Specific error category
- Contextual details
- Actionable suggestions

### 2. Error Chaining
- Original exceptions are preserved
- Full traceback available
- Context flows through error chain

### 3. User-Friendly Suggestions
```python
# Example error with suggestions:
InvalidLocationError: Invalid location format: 'San Francisco'

Suggestions:
  1. Use format: 'City, State' (e.g., 'San Francisco, CA')
  2. Or use format: 'City, State Code' (e.g., 'San Francisco, California')
```

### 4. Tutorial Support
Tutorials now handle errors gracefully:
```python
with tutorial_error_handler("Getting Started Tutorial"):
    # Tutorial code
    result = client.run_analysis(config)
```

## Benefits

1. **Better Developer Experience**: Clear errors help users fix issues quickly
2. **Reduced Support Burden**: Self-documenting errors with solutions
3. **Improved Debugging**: Rich context and error chaining
4. **Tutorial Robustness**: Tutorials fail gracefully with helpful messages
5. **Type Safety**: Specific exception types for different scenarios

## Usage Examples

### Basic Error Handling
```python
try:
    result = client.analyze(location="BadLocation")
except InvalidLocationError as e:
    print(f"Error: {e}")
    for suggestion in e.context.suggestions:
        print(f"• {suggestion}")
```

### With Context Manager
```python
with error_context("census data processing", location="San Francisco"):
    # Any errors here will have context added
    data = process_census_data()
```

### Retry Pattern
```python
@with_retries(max_attempts=3, exceptions=(OSMAPIError,))
def fetch_pois():
    return query_overpass(query)
```

## Documentation

- Created comprehensive error handling guide: `docs/error-handling.md`
- Updated tutorials to use new error handling
- Added test script: `test_error_handling.py`

## Next Steps

1. Update remaining modules to use new error handling
2. Add more specific error types as needed
3. Enhance error recovery strategies
4. Add telemetry for common errors