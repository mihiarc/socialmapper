# Error Handling in SocialMapper

SocialMapper provides a comprehensive error handling system designed to give clear, actionable feedback to users when things go wrong.

## Overview

The error handling system in SocialMapper follows these principles:

1. **Clear Error Messages**: Every error provides a human-readable explanation
2. **Actionable Suggestions**: Errors include suggestions for how to fix the problem
3. **Rich Context**: Errors capture relevant context for debugging
4. **Error Chaining**: Original causes are preserved through the error chain
5. **Type Safety**: Custom exception hierarchy for different error categories

## Exception Hierarchy

```
SocialMapperError (base)
├── ConfigurationError
│   ├── MissingAPIKeyError
│   └── InvalidConfigurationError
├── ValidationError
│   ├── InvalidLocationError
│   ├── InvalidCensusVariableError
│   └── InvalidTravelTimeError
├── DataProcessingError
│   ├── NoDataFoundError
│   └── InsufficientDataError
├── ExternalAPIError
│   ├── CensusAPIError
│   ├── OSMAPIError
│   └── GeocodingError
├── FileSystemError
│   ├── FileNotFoundError
│   └── PermissionError
├── AnalysisError
│   ├── IsochroneGenerationError
│   └── NetworkAnalysisError
└── VisualizationError
    └── MapGenerationError
```

## Common Errors and Solutions

### 1. Invalid Location Format

**Error**: `InvalidLocationError`

**Example**:
```python
# Wrong
client.analyze(location="San Francisco")

# Correct
client.analyze(location="San Francisco, CA")
```

**Suggestions**:
- Use format: 'City, State' (e.g., 'San Francisco, CA')
- Or use format: 'County, State' (e.g., 'Wake County, North Carolina')

### 2. Missing Census API Key

**Error**: `MissingAPIKeyError`

**Solution**:
1. Get a free API key from https://api.census.gov/data/key_signup.html
2. Set as environment variable: `export CENSUS_API_KEY='your-key-here'`
3. Or pass directly: `.with_census_api_key('your-key')`

### 3. No POIs Found

**Error**: `NoDataFoundError`

**Common Causes**:
- POI type doesn't exist in the area
- Location name is misspelled
- Search area is too small

**Solutions**:
- Try different POI types: 'school', 'hospital', 'park'
- Use a larger area (county instead of city)
- Verify spelling of location names

### 4. Invalid Travel Time

**Error**: `InvalidTravelTimeError`

**Valid Range**: 1-120 minutes

**Example**:
```python
# Wrong
.with_travel_time(200)  # Too high

# Correct
.with_travel_time(30)   # Valid
```

### 5. Network/API Errors

**Error**: `OSMAPIError`, `CensusAPIError`

**Common Solutions**:
- Check internet connection
- Wait and retry (rate limiting)
- Verify API credentials
- Check service status

## Using Error Handling in Tutorials

The `tutorial_error_handler` provides user-friendly error messages for tutorials:

```python
from socialmapper import tutorial_error_handler

with tutorial_error_handler("My Tutorial"):
    # Tutorial code here
    result = run_analysis()
```

This will:
- Catch common errors
- Provide helpful suggestions
- Format errors nicely for learners
- Exit gracefully with appropriate messages

## Error Context and Debugging

Each error includes rich context:

```python
try:
    # Some operation
except SocialMapperError as e:
    print(f"Error: {e}")
    print(f"Category: {e.context.category}")
    print(f"Severity: {e.context.severity}")
    print(f"Operation: {e.context.operation}")
    print(f"Suggestions: {e.context.suggestions}")
    print(f"Details: {e.context.details}")
```

## Best Practices

### 1. Use Specific Exceptions

```python
# Good
raise InvalidLocationError(location)

# Avoid
raise ValueError("Bad location")
```

### 2. Add Context

```python
# Good
raise DataProcessingError(
    "Failed to process census data",
    geoids=geoids,
    variable=variable
).with_operation("census_integration")

# Avoid
raise Exception("Processing failed")
```

### 3. Chain Exceptions

```python
try:
    result = external_api_call()
except RequestException as e:
    raise OSMAPIError(
        "Failed to query OpenStreetMap",
        cause=e,  # Preserves original error
        query=query
    )
```

### 4. Provide Suggestions

```python
error = NoDataFoundError("libraries", location="Rural Town")
error.add_suggestion("Try searching for a larger area")
error.add_suggestion("Check if libraries exist in this region")
raise error
```

## Error Recovery Patterns

### 1. Retry on Transient Errors

```python
from socialmapper.util.error_handling import with_retries

@with_retries(max_attempts=3, exceptions=(OSMAPIError,))
def fetch_pois():
    return query_overpass(query)
```

### 2. Fallback Values

```python
from socialmapper.util.error_handling import with_fallback

@with_fallback([], NoDataFoundError)
def get_census_data():
    return fetch_census_data()
```

### 3. Batch Error Collection

```python
from socialmapper.util.error_handling import ErrorCollector

collector = ErrorCollector()

for location in locations:
    with collector.collect(location):
        process_location(location)

if collector.has_errors:
    print(f"Failed: {collector.error_count} locations")
```

## API Error Handling

The modern API uses the Result pattern:

```python
result = client.analyze(location="San Francisco, CA", 
                       poi_type="amenity",
                       poi_name="library")

match result:
    case Ok(analysis):
        print(f"Found {analysis.poi_count} POIs")
    case Err(error):
        print(f"Error: {error.message}")
        if error.type == ErrorType.VALIDATION:
            print("Check your input parameters")
```

## Logging Integration

Errors are automatically logged with appropriate levels:

```python
from socialmapper.util.error_handling import log_error

try:
    risky_operation()
except SocialMapperError as e:
    log_error(e, ErrorSeverity.ERROR)
```

## Testing Error Conditions

```python
import pytest
from socialmapper import InvalidLocationError

def test_location_validation():
    with pytest.raises(InvalidLocationError) as exc_info:
        validate_location("BadLocation")
    
    error = exc_info.value
    assert "City, State" in error.context.suggestions[0]
```

## Migration from Old Error Handling

If you're updating old code:

```python
# Old style
try:
    result = analyze()
except ValueError as e:
    print(f"Error: {e}")

# New style
try:
    result = analyze()
except SocialMapperError as e:
    print(format_error_for_user(e))
    for suggestion in e.context.suggestions:
        print(f"• {suggestion}")
```