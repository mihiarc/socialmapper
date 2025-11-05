# Improved Error Messages - Implementation Summary

## Overview

This document summarizes the improvements made to SocialMapper's error handling and user experience, addressing Issue #85 and related concerns about cryptic error messages.

## Changes Made

### 1. Enhanced Exception Classes (`socialmapper/exceptions.py`)

#### New Base Exception Features
- All exceptions now support optional `help_text` parameter
- Automatic formatting of error messages with helpful guidance
- Consistent structure across all error types

#### New Specific Exception Classes

1. **MissingAPIKeyError** (extends ValidationError)
   - Triggered when Census API key is not found
   - Provides step-by-step instructions to obtain free API key
   - Links to documentation and key manager tool
   - Example usage in census.py and _census.py

2. **InvalidLocationError** (extends ValidationError)
   - Triggered when location cannot be geocoded
   - Provides formatting tips for location strings
   - Supports optional similar location suggestions
   - Example usage in _geocoding.py

3. **InvalidPOICategoryError** (extends ValidationError)
   - Triggered when invalid POI category is specified
   - Lists all valid category names
   - Shows example usage
   - Example usage in api.py

4. **NetworkError** (extends APIError)
   - Triggered for network connectivity issues
   - Provides troubleshooting steps
   - Distinguishes timeouts from connection errors
   - Example usage throughout API modules

5. **RateLimitError** (extends APIError)
   - Triggered when API rate limits are exceeded
   - Shows retry timing when available
   - Provides rate limiting best practices
   - Example usage in census.py and _osm.py

6. **InvalidAPIResponseError** (extends APIError)
   - Triggered for invalid or unexpected API responses
   - Context-aware help based on HTTP status codes
   - Specific guidance for 403, 404, 500+ errors
   - Example usage in census.py and _census.py

### 2. Updated Error Handling in Core Modules

#### Census API (`socialmapper/census.py`, `socialmapper/_census.py`)
- HTTP 403 errors now raise MissingAPIKeyError with setup instructions
- HTTP 429 errors now raise RateLimitError with retry guidance
- Timeout and connection errors now raise NetworkError with troubleshooting
- Other HTTP errors raise InvalidAPIResponseError with context

#### Geocoding (`socialmapper/_geocoding.py`)
- Failed geocoding attempts now raise InvalidLocationError with suggestions
- Network errors properly categorized (timeout vs connection)
- Provides helpful location formatting tips

#### POI/OpenStreetMap (`socialmapper/_osm.py`, `socialmapper/api.py`)
- Invalid POI categories raise InvalidPOICategoryError with valid list
- Overpass API failures raise appropriate network or rate limit errors
- Falls through multiple endpoints before raising final error

### 3. Updated Public API (`socialmapper/__init__.py`)

Exported new exception classes for user access:
- MissingAPIKeyError
- InvalidLocationError
- InvalidPOICategoryError
- NetworkError
- RateLimitError
- InvalidAPIResponseError

### 4. Comprehensive Test Coverage (`tests/test_exceptions.py`)

Added 11 new test cases covering:
- Exception inheritance hierarchy
- Error message content validation
- Help text presence and accuracy
- Context-specific guidance
- HTTP status code handling

All 25 tests pass successfully.

## Example Error Messages

### Missing API Key
```
Census API key not found

Quick Solutions:

1. Get a free Census API key (takes 2 minutes):
   - Visit: https://api.census.gov/data/key_signup.html
   - Check your email for the key
   - Set environment variable: export CENSUS_API_KEY='your_key'
   - Or add to .env file: CENSUS_API_KEY=your_key

2. Use the key manager (recommended):
   socialmapper-keys set census_api your_key_here

Documentation: https://mihiarc.github.io/socialmapper/setup
```

### Invalid Location
```
Could not find location: 'Portlnd, OR'

Location Tips:
- Try 'City, State' format (e.g., 'Portland, OR')
- Use full state names or 2-letter codes
- Include ZIP code for specific addresses
- Check spelling and state abbreviations

Did you mean one of these?
  - Portland, OR
  - Portland, ME
```

### Invalid POI Category
```
Invalid POI category: 'restraunt'

Valid POI categories:
  - education
  - food_and_drink
  - healthcare
  - recreation
  - services
  - shopping
  - transportation

Example: get_poi('Portland, OR', category='food_and_drink')
```

### Network Error
```
Network error connecting to Census API: Connection timeout

Troubleshooting:
- Check your internet connection
- Verify firewall/proxy settings
- The service may be temporarily down
- Try again in a few moments

Service status: Check if Census API is operational
```

### Rate Limit
```
Rate limit exceeded for Census API

Retry after: 60 seconds
Rate Limiting Tips:
- Add delays between requests
- Batch operations when possible
- Use caching to reduce API calls

Documentation: https://mihiarc.github.io/socialmapper/api-limits
```

## Benefits

1. **Reduced Onboarding Friction**: New users get clear guidance when they encounter errors
2. **Self-Service Problem Solving**: Error messages include actionable steps
3. **Better Developer Experience**: No need to search documentation for common issues
4. **Consistent Error Patterns**: All errors follow the same helpful format
5. **Backward Compatible**: Legacy exception aliases still work

## Files Modified

- `socialmapper/exceptions.py` - Enhanced exception classes
- `socialmapper/__init__.py` - Export new exceptions
- `socialmapper/census.py` - Census API error handling
- `socialmapper/_census.py` - Internal Census utilities
- `socialmapper/_geocoding.py` - Geocoding error handling
- `socialmapper/_osm.py` - OpenStreetMap/POI error handling
- `socialmapper/api.py` - POI category validation
- `tests/test_exceptions.py` - Comprehensive test coverage

## Testing

All tests pass:
- 25/25 exception tests pass
- 23/23 validator tests pass
- No regressions in existing functionality

## Next Steps

Potential future enhancements:
1. Add similar helpful errors for visualization operations
2. Implement fuzzy matching for location suggestions
3. Add telemetry to track which errors users encounter most
4. Create interactive troubleshooting wizard for common errors
5. Add localization support for error messages
