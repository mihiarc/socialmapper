# Census API Reliability Guide

This guide explains how to use SocialMapper's enhanced Census API integration for reliable data fetching.

## Overview

The enhanced Census API client provides enterprise-grade reliability features:

- **Circuit Breaker Pattern**: Prevents cascading failures
- **Request Deduplication**: Eliminates duplicate concurrent requests
- **Connection Pooling**: Improves performance with persistent connections
- **Adaptive Rate Limiting**: Automatically adjusts to API response patterns
- **Comprehensive Metrics**: Monitor API performance and reliability
- **Multiple Caching Strategies**: Memory, file, and hybrid caching options

## Quick Start

### Basic Usage

```python
from socialmapper.census.infrastructure import create_census_api_client

# Create enhanced client with sensible defaults
client = create_census_api_client()

# Fetch census data
data = client.get_census_data(
    variables=["B01003_001E"],  # Total population
    geography="state:*",
    year=2022,
    dataset="acs/acs5"
)
```

### Using with SocialMapper

The enhanced client is automatically used when you analyze with SocialMapper:

```python
from socialmapper import SocialMapperBuilder

analysis = (
    SocialMapperBuilder()
    .location("Raleigh, NC")
    .poi_type("amenity")
    .poi_name("library")
    .travel_time(15)
    .build()
    .analyze()
)
```

## Reliability Features

### Circuit Breaker

The circuit breaker prevents your application from repeatedly calling a failing service:

```python
# Circuit breaker states:
# - CLOSED: Normal operation
# - OPEN: Blocking requests after failures
# - HALF_OPEN: Testing if service recovered

# Configuration
from socialmapper.census.infrastructure import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Try recovery after 60 seconds
    success_threshold=2,      # Need 2 successes to close
)
```

### Request Deduplication

Prevents duplicate API calls when multiple parts of your code request the same data:

```python
# Multiple concurrent requests for same data
# Only one actual API call is made
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor() as executor:
    # These will deduplicate to a single API call
    future1 = executor.submit(client.get_census_data, ...)
    future2 = executor.submit(client.get_census_data, ...)
    future3 = executor.submit(client.get_census_data, ...)
```

### Connection Pooling

The enhanced client maintains a pool of HTTP connections for better performance:

```python
# Configured automatically with:
# - 10 connection pools
# - 10 connections per pool
# - Non-blocking when pool is full
```

### Adaptive Rate Limiting

Automatically adjusts request rate based on API responses:

```python
# Starts at 60 requests/minute
# Reduces on 429 errors
# Increases when API responds quickly
# Configurable min/max bounds (10-120 req/min)
```

## Caching Strategies

### Memory Cache

Fast in-memory cache with LRU eviction:

```python
client = create_census_api_client(
    cache_type="memory",
    cache_max_size=1000  # Max entries
)
```

### File Cache

Persistent cache that survives restarts:

```python
client = create_census_api_client(
    cache_type="file",
    cache_dir=".census_cache",
    cache_ttl_seconds=3600  # 1 hour TTL
)
```

### Hybrid Cache

Best of both worlds - memory for speed, file for persistence:

```python
client = create_census_api_client(
    cache_type="hybrid",
    memory_size=100,        # Hot cache in memory
    cache_dir=".census_cache"
)
```

## Batch Processing

Process large numbers of geographic units efficiently:

```python
# Fetch data for multiple block groups in batches
geoids = ["371830528021", "371830528022", ...]  # Many block groups

data = client.get_census_data_batch(
    geoids=geoids,
    variables=["B01003_001E", "B19013_001E"],
    year=2022,
    dataset="acs/acs5",
    batch_size=50  # Process 50 at a time
)
```

## Monitoring and Metrics

### Real-time Metrics

```python
# Get comprehensive metrics
metrics = client.get_metrics_summary()

print(f"Total Requests: {metrics['requests']['total']}")
print(f"Success Rate: {metrics['requests']['success_rate']}")
print(f"Cache Hit Rate: {metrics['cache']['hit_rate']}")
print(f"Circuit Breaker: {metrics['circuit_breaker']['state']}")
```

### Performance Monitoring

```python
# Get recent performance metrics
recent = client.get_metrics_summary()["recent_metrics"]

print(f"Recent errors (last 5 min): {recent['recent_errors']}")
print(f"Recent avg response time: {recent['recent_average_response_time']}")
```

## Configuration Options

### Complete System Setup

```python
from socialmapper.census.infrastructure import create_census_system

# Create complete census system with all components
system = create_census_system(
    enhanced=True,
    cache_type="hybrid",
    rate_limit_requests_per_minute=60,
    adaptive_rate_limiting=True,
    max_retries=3,
    api_timeout_seconds=30,
)

client = system["client"]
cache = system["cache"]
rate_limiter = system["rate_limiter"]
config = system["config"]
```

### Environment Variables

```bash
# Required
export CENSUS_API_KEY="your-api-key"

# Optional
export CENSUS_CACHE_ENABLED=true
export CENSUS_RATE_LIMIT=60
export LOG_LEVEL=INFO
```

## Error Handling

The enhanced client provides detailed error information:

```python
try:
    data = client.get_census_data(...)
except CensusAPIError as e:
    print(f"API Error: {e}")
    
    # Check if circuit breaker is open
    if "Circuit breaker is open" in str(e):
        # Wait before retrying
        pass
except CensusAPIRateLimitError as e:
    print(f"Rate limited: {e}")
    # Client handles waiting automatically
```

## Best Practices

1. **Always use the enhanced client** for production applications
2. **Enable caching** to reduce API calls and improve performance
3. **Monitor metrics** to understand API usage patterns
4. **Use batch processing** for large datasets
5. **Handle circuit breaker states** gracefully in your UI
6. **Set appropriate timeouts** based on your use case

## Example: Raleigh, NC Analysis

```python
import os
from socialmapper.census.infrastructure import create_census_api_client

# Ensure API key is set
if not os.getenv("CENSUS_API_KEY"):
    print("Please set CENSUS_API_KEY environment variable")
    exit(1)

# Create enhanced client
client = create_census_api_client(enhanced=True)

# Fetch data for Wake County, NC (Raleigh)
data = client.get_census_data(
    variables=[
        "B01003_001E",  # Total population
        "B19013_001E",  # Median household income
        "B25001_001E",  # Total housing units
    ],
    geography="block group:*",
    year=2022,
    dataset="acs/acs5",
    **{"in": "state:37 county:183"}  # Wake County
)

print(f"Fetched data for {len(data)-1} block groups")

# Check metrics
metrics = client.get_metrics_summary()
print(f"Cache hit rate: {metrics['cache']['hit_rate']}")
```

## Troubleshooting

### Circuit Breaker Opens Frequently

- Check API key validity
- Verify network connectivity
- Review error logs for specific issues
- Consider increasing failure threshold

### Low Cache Hit Rate

- Ensure cache is enabled
- Check cache TTL settings
- Verify cache directory permissions (file cache)
- Consider increasing cache size

### Rate Limiting Issues

- Reduce request rate
- Enable adaptive rate limiting
- Check current API limits
- Consider request batching

### Timeout Errors

- Increase timeout setting
- Check network latency
- Consider smaller batch sizes
- Enable retry logic