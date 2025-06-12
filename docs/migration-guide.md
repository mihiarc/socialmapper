# Migration Guide: SocialMapper v0.5.x to v0.6.0

This guide helps you migrate from the old SocialMapper API to the new modern API introduced in v0.5.4.

## Overview

The new API provides:
- ✅ Better error handling with Result types
- ✅ Cleaner configuration with builder pattern
- ✅ Async support for better performance
- ✅ Type safety throughout
- ✅ Proper resource management with context managers

## Quick Migration Examples

### Basic Analysis

**Old API (Deprecated):**
```python
from socialmapper import run_socialmapper

result = run_socialmapper(
    geocode_area="San Francisco",
    state="CA",
    poi_type="amenity",
    poi_name="library",
    travel_time=15,
    census_variables=["total_population", "median_income"]
)
```

**New API (Recommended):**
```python
from socialmapper.api import quick_analysis

result = quick_analysis(
    location="San Francisco, CA",
    poi_search="amenity:library",
    travel_time=15,
    census_variables=["total_population", "median_income"]
)

if result.is_ok():
    analysis = result.unwrap()
    print(f"Found {analysis.poi_count} libraries")
```

### Custom POIs

**Old API:**
```python
result = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=20,
    census_variables=["total_population"],
    export_maps=True
)
```

**New API:**
```python
from socialmapper.api import analyze_custom_pois

result = analyze_custom_pois(
    "locations.csv",
    travel_time=20,
    census_variables=["total_population"],
    enable_maps=True
)
```

### Advanced Configuration

**Old API:**
```python
from socialmapper import run_socialmapper

result = run_socialmapper(
    geocode_area="Chicago",
    state="Illinois",
    poi_type="leisure",
    poi_name="park",
    travel_time=20,
    geographic_level="zcta",
    census_variables=["total_population", "median_income", "median_age"],
    export_csv=True,
    export_maps=True,
    export_isochrones=True,
    map_backend="matplotlib",
    output_dir="chicago_parks"
)
```

**New API:**
```python
from socialmapper.api import SocialMapperClient, SocialMapperBuilder, GeographicLevel

config = (SocialMapperBuilder()
    .with_location("Chicago", "Illinois")
    .with_osm_pois("leisure", "park")
    .with_travel_time(20)
    .with_geographic_level(GeographicLevel.ZCTA)
    .with_census_variables("total_population", "median_income", "median_age")
    .enable_map_export()
    .enable_isochrone_export()
    .with_output_directory("chicago_parks")
    .build()
)

with SocialMapperClient() as client:
    result = client.run_analysis(config)
    
    match result:
        case Ok(analysis):
            print(f"Success! Analyzed {analysis.census_units_analyzed} census units")
        case Err(error):
            print(f"Error: {error.message}")
```

### Using RunConfig

**Old API:**
```python
from socialmapper import run_socialmapper, RunConfig

config = RunConfig(
    custom_coords_path="pois.json",
    travel_time=15,
    census_variables=["total_population"],
    export_maps=True
)

result = run_socialmapper(config)
```

**New API:**
```python
from socialmapper.api import SocialMapperClient, SocialMapperBuilder

config = (SocialMapperBuilder()
    .with_custom_pois("pois.json")
    .with_travel_time(15)
    .with_census_variables("total_population")
    .enable_map_export()
    .build()
)

with SocialMapperClient() as client:
    result = client.run_analysis(config)
```

## Error Handling

### Old API
The old API raises exceptions that need to be caught:

```python
try:
    result = run_socialmapper(...)
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### New API
The new API returns Result types for explicit error handling:

```python
result = client.analyze(...)

# Option 1: Pattern matching (Python 3.10+)
match result:
    case Ok(analysis):
        print(f"Success: {analysis.poi_count} POIs")
    case Err(error):
        print(f"Failed: {error}")

# Option 2: Traditional if/else
if result.is_ok():
    analysis = result.unwrap()
    print(f"Success: {analysis.poi_count} POIs")
else:
    error = result.unwrap_err()
    print(f"Failed: {error}")
```

## Async Operations

The new API supports async operations for better performance:

```python
import asyncio
from socialmapper.api import AsyncSocialMapper

async def analyze_async():
    config = {...}  # Your configuration
    
    async with AsyncSocialMapper(config) as mapper:
        # Stream POIs as they're found
        async for poi in mapper.stream_pois():
            print(f"Found: {poi.name}")
        
        # Run full analysis
        result = await mapper.run_analysis()
        return result

# Run async function
result = asyncio.run(analyze_async())
```

## Parameter Mapping

| Old Parameter | New Method/Parameter |
|--------------|---------------------|
| `geocode_area` + `state` | `.with_location(city, state)` |
| `poi_type` + `poi_name` | `.with_osm_pois(type, name)` |
| `custom_coords_path` | `.with_custom_pois(path)` |
| `travel_time` | `.with_travel_time(minutes)` |
| `census_variables` | `.with_census_variables(*vars)` |
| `geographic_level` | `.with_geographic_level(level)` |
| `export_maps=True` | `.enable_map_export()` |
| `export_isochrones=True` | `.enable_isochrone_export()` |
| `export_csv=False` | `.disable_csv_export()` |
| `output_dir` | `.with_output_directory(path)` |
| `max_poi_count` | `.limit_pois(count)` |

## Deprecation Timeline

- **v0.5.4**: New API introduced, deprecation warnings added
- **v0.6.0**: `run_socialmapper` moved to legacy module
- **v0.7.0**: Old API completely removed

## Getting Help

If you encounter issues during migration:

1. Check the [API documentation](../api/index.md)
2. See [examples/modern_api_demo.py](../examples/modern_api_demo.py)
3. Report issues on [GitHub](https://github.com/mihiarc/socialmapper/issues)

## Benefits of Migrating

1. **Better Error Handling**: No more mysterious exceptions
2. **Type Safety**: Full IDE support with autocompletion
3. **Cleaner Code**: Intuitive builder pattern
4. **Better Performance**: Async support for I/O operations
5. **Future Proof**: Active development on new API only