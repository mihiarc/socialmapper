# Isochrone Analysis: Understanding Accessibility

An **isochrone** is a polygon showing all areas reachable from a point within a given travel time. This tutorial teaches you how to create and use isochrones for accessibility analysis.

## What is an Isochrone?

Think of dropping a stone in water—the ripples show how far the impact spreads. An isochrone is similar: it shows how far you can travel from a location in a given time.

**Common uses:**
- How far can customers reach my store in 15 minutes?
- What neighborhoods are within walking distance of a park?
- Which areas have good hospital access?

## Creating Your First Isochrone

```python
from socialmapper import create_isochrone

# Create a 15-minute driving isochrone from downtown Seattle
isochrone = create_isochrone(
    location="Seattle, WA",
    travel_time=15,
    travel_mode="drive"
)

# Examine the result
print(f"Type: {isochrone['type']}")  # Feature
print(f"Geometry: {isochrone['geometry']['type']}")  # Polygon
print(f"Area: {isochrone['properties']['area_sq_km']:.1f} km²")
print(f"Backend used: {isochrone['properties']['backend']}")
```

### Using Coordinates

You can also specify exact coordinates:

```python
# Pike Place Market coordinates
isochrone = create_isochrone(
    location=(47.6097, -122.3425),
    travel_time=10,
    travel_mode="walk"
)
```

## Travel Modes Compared

SocialMapper supports three travel modes, each with different characteristics:

### Walking (5 km/h average)

```python
walk_isochrone = create_isochrone(
    location="Boston, MA",
    travel_time=15,
    travel_mode="walk"
)
print(f"Walking 15 min: {walk_isochrone['properties']['area_sq_km']:.2f} km²")
# Typically 0.5-2 km² depending on terrain
```

### Biking (15 km/h average)

```python
bike_isochrone = create_isochrone(
    location="Boston, MA",
    travel_time=15,
    travel_mode="bike"
)
print(f"Biking 15 min: {bike_isochrone['properties']['area_sq_km']:.2f} km²")
# Typically 3-10 km² depending on bike infrastructure
```

### Driving (varies by road type)

```python
drive_isochrone = create_isochrone(
    location="Boston, MA",
    travel_time=15,
    travel_mode="drive"
)
print(f"Driving 15 min: {drive_isochrone['properties']['area_sq_km']:.2f} km²")
# Typically 50-300 km² depending on traffic and highways
```

### Comparing All Modes

```python
from socialmapper import create_isochrone

location = "Denver, CO"
travel_time = 10

modes = ["walk", "bike", "drive"]
results = {}

for mode in modes:
    iso = create_isochrone(location, travel_time=travel_time, travel_mode=mode)
    results[mode] = iso['properties']['area_sq_km']

print(f"\nAccessibility from {location} in {travel_time} minutes:")
print(f"  Walking: {results['walk']:.1f} km²")
print(f"  Biking:  {results['bike']:.1f} km²")
print(f"  Driving: {results['drive']:.1f} km²")
print(f"\nDriving covers {results['drive']/results['walk']:.0f}x more area than walking")
```

## Choosing a Backend

SocialMapper supports multiple routing backends:

### Valhalla (Default, Recommended)

```python
# Fast, uses public API, no key required
isochrone = create_isochrone(
    location="Chicago, IL",
    travel_time=15,
    backend="valhalla"  # Default
)
```

**Pros:** Fast (1-2 seconds), free, no API key
**Cons:** Requires internet connection

### NetworkX (Offline)

```python
# Slower, but works offline
isochrone = create_isochrone(
    location="Chicago, IL",
    travel_time=15,
    backend="networkx"
)
```

**Pros:** Works offline, full control
**Cons:** Slower (5-15 seconds), downloads road network

### Other Backends

```python
# OpenRouteService (requires ORS_API_KEY)
isochrone = create_isochrone(location, backend="ors")

# GraphHopper (requires GRAPHHOPPER_API_KEY)
isochrone = create_isochrone(location, backend="graphhopper")

# Mapbox OSRM (requires MAPBOX_API_KEY)
isochrone = create_isochrone(location, backend="osrm")
```

### Checking Available Backends

```python
from socialmapper.isochrone.backends import list_available_backends, get_backend_info

# See which backends are ready to use
print("Available backends:", list_available_backends())

# Get detailed info
info = get_backend_info()
for name, details in info.items():
    status = "Ready" if details['available'] else "Needs setup"
    print(f"  {name}: {status}")
```

## Working with Isochrone Results

### Understanding the GeoJSON Structure

```python
isochrone = create_isochrone("Austin, TX", travel_time=20)

# The result is a GeoJSON Feature
print(isochrone.keys())
# dict_keys(['type', 'geometry', 'properties'])

# Geometry contains the polygon
geometry = isochrone['geometry']
print(f"Geometry type: {geometry['type']}")  # Polygon
print(f"Number of coordinates: {len(geometry['coordinates'][0])}")

# Properties contain metadata
props = isochrone['properties']
print(f"Location: {props['location']}")
print(f"Travel time: {props['travel_time']} min")
print(f"Travel mode: {props['travel_mode']}")
print(f"Area: {props['area_sq_km']:.2f} km²")
print(f"Backend: {props['backend']}")
```

### Converting to Shapely

```python
from shapely.geometry import shape

isochrone = create_isochrone("Miami, FL", travel_time=15)

# Convert to Shapely geometry for spatial operations
polygon = shape(isochrone['geometry'])

# Now you can use Shapely operations
print(f"Perimeter: {polygon.length:.2f} degrees")
print(f"Centroid: {polygon.centroid}")
print(f"Bounds: {polygon.bounds}")
```

### Converting to GeoDataFrame

```python
import geopandas as gpd
from shapely.geometry import shape

isochrone = create_isochrone("Phoenix, AZ", travel_time=15)

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(
    [isochrone['properties']],
    geometry=[shape(isochrone['geometry'])],
    crs="EPSG:4326"
)

print(gdf)
```

## Practical Examples

### Example 1: Hospital Accessibility

Determine what areas are within 10 minutes of a healthcare facility:

```python
from socialmapper import create_isochrone, get_poi

# Find a healthcare facility
healthcare = get_poi("San Francisco, CA", categories=["healthcare"], limit=1)
facility = healthcare[0]

print(f"Analyzing access to: {facility['name']}")

# Create driving isochrone from facility location
isochrone = create_isochrone(
    location=(facility['lat'], facility['lon']),
    travel_time=10,
    travel_mode="drive"
)

print(f"Area with 10-min drive access: {isochrone['properties']['area_sq_km']:.1f} km²")
```

### Example 2: Commute Analysis

Compare commute coverage from two potential office locations:

```python
from socialmapper import create_isochrone

locations = {
    "Downtown": (40.7128, -74.0060),  # NYC Downtown
    "Midtown": (40.7549, -73.9840),   # NYC Midtown
}

print("30-minute commute coverage:\n")
for name, coords in locations.items():
    iso = create_isochrone(coords, travel_time=30, travel_mode="drive")
    print(f"{name}: {iso['properties']['area_sq_km']:.1f} km²")
```

### Example 3: Equity Analysis Setup

Find areas that lack walkable access to stores:

```python
from socialmapper import create_isochrone, get_poi, get_census_blocks

# Get shopping locations in an area
shopping = get_poi("Atlanta, GA", categories=["shopping"], limit=50)

print(f"Found {len(shopping)} shopping locations")

# For each store, create walking isochrone
# This shows areas WITH access
for store in shopping[:3]:
    iso = create_isochrone(
        location=(store['lat'], store['lon']),
        travel_time=15,
        travel_mode="walk"
    )
    print(f"{store['name']}: {iso['properties']['area_sq_km']:.2f} km² walkable")
```

## Multiple Isochrone Intervals

Create multiple time intervals for the same location:

```python
from socialmapper import create_isochrone

location = "Portland, OR"
intervals = [5, 10, 15, 20, 30]

print(f"Driving accessibility from {location}:\n")
for minutes in intervals:
    iso = create_isochrone(location, travel_time=minutes, travel_mode="drive")
    area = iso['properties']['area_sq_km']
    print(f"  {minutes:2d} min: {area:6.1f} km²")
```

## Saving Isochrones

### Save as GeoJSON

```python
import json
from socialmapper import create_isochrone

isochrone = create_isochrone("Los Angeles, CA", travel_time=20)

# Save as GeoJSON file
with open("la_isochrone.geojson", "w") as f:
    json.dump(isochrone, f, indent=2)
```

### Save as Shapefile

```python
import geopandas as gpd
from shapely.geometry import shape
from socialmapper import create_isochrone

isochrone = create_isochrone("Los Angeles, CA", travel_time=20)

# Convert to GeoDataFrame and save
gdf = gpd.GeoDataFrame(
    [isochrone['properties']],
    geometry=[shape(isochrone['geometry'])],
    crs="EPSG:4326"
)
gdf.to_file("la_isochrone.shp")
```

## Performance Tips

1. **Use Valhalla for speed** - Default backend, 10-100x faster than NetworkX

2. **Cache results** - Isochrones don't change often; save them locally

3. **Batch similar requests** - Group requests to the same region

4. **Use appropriate travel times** - Longer times = larger networks = slower processing

```python
# Fast: Valhalla backend
iso = create_isochrone(location, backend="valhalla")  # ~1-2 sec

# Slower: NetworkX (but works offline)
iso = create_isochrone(location, backend="networkx")  # ~5-15 sec
```

## Next Steps

Now that you understand isochrones:

- **[Points of Interest](03-points-of-interest.md)** - Find what's inside your isochrone
- **[Census Data](04-census-data.md)** - Get demographics for your isochrone
- **[Complete Workflow](06-complete-workflow.md)** - Combine everything
