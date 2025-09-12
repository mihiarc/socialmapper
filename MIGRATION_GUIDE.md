# SocialMapper v1.x to v2.0 Migration Guide

## Overview

SocialMapper v2.0 is a complete redesign that simplifies the API to just 5 core functions. This guide will help you migrate your existing code.

## Breaking Changes

### 1. No More Client Class

**v1.x (Old)**
```python
from socialmapper.api import SocialMapper

# Create client
mapper = SocialMapper(api_key="your-census-key")

# Use client methods
result = mapper.create_isochrone(location, travel_time=15)
```

**v2.0 (New)**
```python
from socialmapper import create_isochrone

# Direct function call - API key from environment
iso = create_isochrone("Seattle, WA", travel_time=15)
```

### 2. Changed Return Types

**v1.x (Old)**
- Custom result classes (`AnalysisResult`, `POIResult`)
- Complex nested structures
- Required `.unwrap()` for results

**v2.0 (New)**
- Simple Python dictionaries and lists
- GeoJSON-compatible formats
- Direct access to data

### 3. Simplified Imports

**v1.x (Old)**
```python
from socialmapper.api import SocialMapper
from socialmapper.pipeline import NearbyPOIDiscoveryConfig
from socialmapper.visualization import ChoroplethMap, MapConfig
from socialmapper.census import CensusClient
```

**v2.0 (New)**
```python
# All functions available from top level
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
    get_poi
)
```

## Function-by-Function Migration

### Isochrone Generation

**v1.x**
```python
mapper = SocialMapper()
result = mapper.analyze(
    location="Portland, OR",
    travel_time=15,
    mode="drive"
)
isochrone = result.isochrone
```

**v2.0**
```python
isochrone = create_isochrone(
    "Portland, OR",
    travel_time=15,
    travel_mode="drive"
)
```

### POI Discovery

**v1.x**
```python
from socialmapper.pipeline import NearbyPOIDiscoveryConfig

config = NearbyPOIDiscoveryConfig(
    origin="Seattle, WA",
    travel_time=20,
    poi_categories=["restaurant", "cafe"],
    max_pois_per_category=10
)
stage = NearbyPOIDiscoveryStage(config)
result = stage.execute()
pois = result.unwrap().pois_by_category
```

**v2.0**
```python
pois = get_poi(
    "Seattle, WA",
    categories=["restaurant", "cafe"],
    travel_time=20,
    limit=100
)
```

### Census Data

**v1.x**
```python
from socialmapper.census import CensusClient

client = CensusClient(api_key="...")
data = client.get_data(
    variables=["B01003_001E"],
    geographic_units=geoids,
    year=2023
)
```

**v2.0**
```python
# API key from CENSUS_API_KEY environment variable
data = get_census_data(
    location=geoids,  # or coordinates, or GeoJSON
    variables=["population"],  # human-readable names supported
    year=2023
)
```

### Map Creation

**v1.x**
```python
from socialmapper.visualization import ChoroplethMap, MapConfig

config = MapConfig(
    figsize=(12, 8),
    color_scheme="YlOrRd",
    show_legend=True
)
map_creator = ChoroplethMap(config)
fig, ax = map_creator.create_map(
    gdf=data,
    column="population",
    map_type=MapType.DEMOGRAPHIC
)
```

**v2.0**
```python
# Much simpler - returns PNG bytes or saves to file
create_map(
    data=blocks,  # List of dicts or GeoDataFrame
    column="population",
    title="Population Map",
    save_path="map.png"  # Optional
)
```

### Census Blocks

**v1.x**
```python
# Complex process involving multiple steps
from socialmapper.census import get_block_groups_for_polygon

blocks = get_block_groups_for_polygon(polygon_gdf)
```

**v2.0**
```python
# Simple function call
blocks = get_census_blocks(
    polygon=isochrone,  # From create_isochrone()
    # OR
    location=(lat, lon),
    radius_km=5
)
```

## Environment Variables

Both versions use environment variables for API keys:

```bash
# Set in your .env file or shell
export CENSUS_API_KEY="your-census-api-key"
export ORS_API_KEY="your-openrouteservice-key"  # Optional
```

## Common Migration Patterns

### Pattern 1: Simple Analysis

**v1.x**
```python
mapper = SocialMapper(api_key=census_key)
result = mapper.analyze(
    location="Denver, CO",
    travel_time=15,
    include_demographics=True,
    include_pois=True
)
if result.success:
    data = result.data
```

**v2.0**
```python
# Create isochrone
iso = create_isochrone("Denver, CO", travel_time=15)

# Get census data for the area
census = get_census_data(iso, ["population", "median_income"])

# Get POIs in the area
pois = get_poi("Denver, CO", travel_time=15)
```

### Pattern 2: Batch Processing

**v1.x**
```python
mapper = SocialMapper()
results = []
for city in cities:
    result = mapper.analyze(city, travel_time=20)
    results.append(result)
```

**v2.0**
```python
results = []
for city in cities:
    iso = create_isochrone(city, travel_time=20)
    results.append(iso)
```

## Removed Features

The following features from v1.x are not available in v2.0:

1. **NLP Interface** - Natural language query processing
2. **Pipeline Orchestration** - Complex multi-stage pipelines
3. **Result Types** - Custom result classes with validation
4. **API Builder** - Programmatic API construction
5. **Advanced Error Handling** - Detailed error hierarchies

If you need these features, consider:
- Staying on v1.x
- Implementing custom wrappers around v2.0 functions
- Opening an issue to discuss adding specific functionality

## Quick Start Example

Here's a complete example showing the new API in action:

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
    get_poi
)

# 1. Create a 15-minute drive-time area
iso = create_isochrone("San Francisco, CA", travel_time=15)
print(f"Area covered: {iso['properties']['area_sq_km']:.1f} sq km")

# 2. Find restaurants in the area
restaurants = get_poi(
    "San Francisco, CA",
    categories=["restaurant"],
    travel_time=15,
    limit=20
)
print(f"Found {len(restaurants)} restaurants")

# 3. Get census blocks
blocks = get_census_blocks(polygon=iso)
print(f"Found {len(blocks)} census blocks")

# 4. Get demographic data
census = get_census_data(
    [b["geoid"] for b in blocks],
    ["population", "median_income"]
)

# 5. Add census data to blocks and create map
for block in blocks:
    block_data = census.get(block["geoid"], {})
    block["population"] = block_data.get("population", 0)

create_map(
    blocks,
    column="population",
    title="Population within 15-min drive",
    save_path="sf_population.png"
)
```

## Getting Help

- **Documentation**: See `example_new_api.py` for comprehensive examples
- **Issues**: Report problems at https://github.com/mihiarc/socialmapper/issues
- **Discussion**: Use GitHub Discussions for questions

## Rollback Option

If you need to rollback to v1.x:

```bash
pip install socialmapper==1.0.0
```

The v1.x branch will receive security updates through 2024.