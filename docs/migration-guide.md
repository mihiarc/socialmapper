# Migration Guide: From run_socialmapper to Modern API

This guide helps you migrate from the deprecated `run_socialmapper` function to the modern SocialMapper API.

## Why Migrate?

The new API provides:
- **Better error handling** with Result types instead of exceptions
- **Type safety** with full type hints
- **Resource management** with context managers
- **Cleaner configuration** with the builder pattern
- **Progress tracking** and async support
- **Improved testability** with dependency injection

## Quick Migration Examples

### Basic POI Analysis

**Old way:**
```python
from socialmapper import run_socialmapper

results = run_socialmapper(
    geocode_area="San Francisco",
    state="CA",
    poi_type="amenity",
    poi_name="library",
    travel_time=15,
    census_variables=["total_population", "median_income"]
)
```

**New way:**
```python
from socialmapper import SocialMapperClient

with SocialMapperClient() as client:
    result = client.analyze(
        location="San Francisco, CA",
        poi_type="amenity",
        poi_name="library",
        travel_time=15,
        census_variables=["total_population", "median_income"]
    )
    
    if result.is_ok():
        analysis = result.unwrap()
        # Use analysis.poi_count, analysis.files_generated, etc.
```

### Custom Coordinates

**Old way:**
```python
results = run_socialmapper(
    custom_coords_path="my_locations.csv",
    travel_time=20,
    census_variables=["total_population"],
    export_csv=True,
    export_isochrones=True
)
```

**New way:**
```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_custom_pois("my_locations.csv")
        .with_travel_time(20)
        .with_census_variables("total_population")
        .with_exports(csv=True, isochrones=True)
        .build()
    )
    
    result = client.run_analysis(config)
```

### With API Key and Custom Output

**Old way:**
```python
results = run_socialmapper(
    geocode_area="Chicago",
    state="IL",
    poi_type="leisure",
    poi_name="park",
    travel_time=30,
    geographic_level="zcta",
    census_variables=["total_population", "median_age"],
    api_key="your-api-key",
    output_dir="parks_analysis"
)
```

**New way:**
```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_location("Chicago", "IL")
        .with_osm_pois("leisure", "park")
        .with_travel_time(30)
        .with_geographic_level("zcta")
        .with_census_variables("total_population", "median_age")
        .with_census_api_key("your-api-key")
        .with_output_directory("parks_analysis")
        .build()
    )
    
    result = client.run_analysis(config)
```

## Key Differences

### 1. Error Handling

**Old way:** Exceptions are raised
```python
try:
    results = run_socialmapper(...)
except Exception as e:
    print(f"Error: {e}")
```

**New way:** Result types with explicit error handling
```python
result = client.analyze(...)
if result.is_err():
    error = result.unwrap_err()
    print(f"Error type: {error.type.name}")
    print(f"Message: {error.message}")
```

### 2. Configuration

**Old way:** Many function parameters
```python
run_socialmapper(
    geocode_area="...",
    state="...",
    poi_type="...",
    poi_name="...",
    travel_time=15,
    # ... many more parameters
)
```

**New way:** Fluent builder pattern
```python
config = (SocialMapperBuilder()
    .with_location("City", "State")
    .with_osm_pois("type", "name")
    .with_travel_time(15)
    # ... chain as needed
    .build()
)
```

### 3. Return Values

**Old way:** Dictionary with various keys
```python
results = run_socialmapper(...)
pois = results.get("poi_data", {}).get("pois", [])
census = results.get("census_data", [])
```

**New way:** Structured result object
```python
if result.is_ok():
    analysis = result.unwrap()
    print(f"POIs found: {analysis.poi_count}")
    print(f"Census units: {analysis.census_units_analyzed}")
    for file_type, path in analysis.files_generated.items():
        print(f"{file_type}: {path}")
```

### 4. Client Configuration

**New way only:** Configure client behavior
```python
from socialmapper import SocialMapperClient, ClientConfig

config = ClientConfig(
    api_key="your-census-api-key",
    rate_limit=5,  # requests per second
    timeout=600,   # seconds
    retry_attempts=3
)

with SocialMapperClient(config) as client:
    # Use client with custom configuration
```

## Advanced Features

### Progress Tracking

```python
def on_progress(percent: float):
    print(f"Progress: {percent:.1f}%")

result = client.run_analysis(config, on_progress=on_progress)
```

### Batch Processing

```python
configs = [config1, config2, config3]

with client.batch_analyses(configs) as batch:
    results = batch.run_all()
    for i, result in enumerate(results):
        if result.is_ok():
            print(f"Analysis {i+1} completed")
```

### Custom Cache Strategy

```python
class MyCache:
    def get(self, key: str):
        # Your cache implementation
        pass
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        # Your cache implementation
        pass

config = ClientConfig(cache_strategy=MyCache())
```

## Common Patterns

### 1. Simple Analysis

```python
# Most common use case
with SocialMapperClient() as client:
    result = client.analyze(
        location="Portland, OR",
        poi_type="amenity",
        poi_name="library"
    )
```

### 2. Full Configuration

```python
# When you need full control
with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_location("Austin", "TX")
        .with_osm_pois("amenity", "school", {"operator": "Austin ISD"})
        .with_travel_time(20)
        .with_census_variables(
            "total_population",
            "median_household_income",
            "percent_poverty",
            "percent_without_vehicle"
        )
        .with_geographic_level("block-group")
        .with_exports(csv=True, isochrones=True)
        .with_output_directory("school_analysis")
        .build()
    )
    
    result = client.run_analysis(config)
```

### 3. Error Recovery

```python
with SocialMapperClient() as client:
    locations = ["San Francisco, CA", "Invalid City, XX", "Seattle, WA"]
    
    for location in locations:
        result = client.analyze(location, "amenity", "hospital")
        
        match result:
            case Ok(analysis):
                print(f"{location}: {analysis.poi_count} hospitals")
            case Err(error) if error.type == ErrorType.GEOCODING:
                print(f"{location}: Could not geocode location")
            case Err(error):
                print(f"{location}: {error.message}")
```

## Need Help?

- Check the [API Reference](api-reference.md) for detailed documentation
- See [examples/](../examples/) for working code samples
- Report issues at https://github.com/anthropics/socialmapper/issues