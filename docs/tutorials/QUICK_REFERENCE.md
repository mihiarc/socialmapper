# SocialMapper Quick Reference Guide

## 🚀 Essential Code Patterns

### Basic Setup

```python
# Import core functions
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    get_poi,
    create_map,
    geocode_address
)

# Set up environment (optional)
import os
os.environ['CENSUS_API_KEY'] = 'your-key-here'
```

---

## 📍 Location Formats

### Coordinates (Preferred)
```python
# Format: (latitude, longitude)
location = (35.7796, -78.6382)  # Raleigh, NC
```

### Common City Coordinates
```python
cities = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698),
    "Phoenix": (33.4484, -112.0740),
    "Philadelphia": (39.9526, -75.1652),
    "San Antonio": (29.4241, -98.4936),
    "San Diego": (32.7157, -117.1611),
    "Dallas": (32.7767, -96.7970),
    "San Jose": (37.3382, -121.8863),
    "Austin": (30.2672, -97.7431),
    "Jacksonville": (30.3322, -81.6557),
    "San Francisco": (37.7749, -122.4194),
    "Columbus": (39.9612, -82.9988),
    "Seattle": (47.6062, -122.3321),
    "Denver": (39.7392, -104.9903),
    "Boston": (42.3601, -71.0589),
    "Washington DC": (38.9072, -77.0369),
    "Miami": (25.7617, -80.1918),
    "Atlanta": (33.7490, -84.3880)
}
```

### Address Geocoding
```python
# Convert address to coordinates
coords = geocode_address("123 Main St, Raleigh, NC 27601")
if coords:
    lat, lon = coords
```

---

## 🗺️ Creating Isochrones

### Basic Isochrone
```python
iso = create_isochrone(
    location=(35.7796, -78.6382),
    travel_time=15,  # minutes
    travel_mode="drive"  # "walk", "bike", or "drive"
)
```

### Accessing Isochrone Properties
```python
# Get area
area = iso['properties']['area_sq_km']

# Get geometry
geometry = iso['geometry']

# Get bounds
bounds = iso['properties']['bbox']  # [min_lon, min_lat, max_lon, max_lat]
```

### Multiple Travel Times
```python
times = [5, 10, 15, 20]
isochrones = []

for time in times:
    iso = create_isochrone(location, travel_time=time, travel_mode="walk")
    isochrones.append(iso)
```

---

## 🏢 Finding POIs

### Basic POI Search
```python
# Find all restaurants
restaurants = get_poi(
    polygon=iso,
    poi_type="restaurant"
)

# Count results
print(f"Found {len(restaurants)} restaurants")
```

### Common POI Types
```python
poi_types = [
    "supermarket",      # Grocery stores
    "restaurant",       # All restaurants
    "fast_food",        # Fast food only
    "cafe",            # Coffee shops
    "pharmacy",        # Pharmacies
    "hospital",        # Hospitals
    "clinic",          # Medical clinics
    "school",          # Schools (all levels)
    "university",      # Higher education
    "park",            # Parks
    "library",         # Libraries
    "bank",            # Banks
    "atm",             # ATMs
    "fuel",            # Gas stations
    "police",          # Police stations
    "fire_station",    # Fire stations
    "post_office",     # Post offices
    "place_of_worship", # Religious sites
    "bus_stop",        # Bus stops
    "subway",          # Subway stations
]
```

### Processing POI Results
```python
# Extract POI details
for poi in restaurants[:5]:
    name = poi.get('name', 'Unknown')
    lat = poi['lat']
    lon = poi['lon']
    tags = poi.get('tags', {})

    print(f"{name}: ({lat:.4f}, {lon:.4f})")
```

---

## 📊 Census Data

### Get Census Blocks
```python
# Find blocks in isochrone
blocks = get_census_blocks(polygon=iso)

# Limit for performance
blocks = blocks[:20]  # First 20 blocks

# Extract GEOIDs
geoids = [block['geoid'] for block in blocks]
```

### Common Census Variables
```python
# Basic demographics
basic_vars = [
    "population",              # Total population
    "median_age",             # Median age
    "median_household_income", # Median HH income
    "housing_units",          # Total housing units
]

# Detailed demographics
detailed_vars = [
    "percent_poverty",        # % below poverty line
    "percent_minority",       # % minority population
    "percent_over_65",        # % age 65+
    "percent_under_18",       # % under 18
    "unemployment_rate",      # Unemployment rate
    "median_home_value",      # Median home value
    "percent_renter",         # % renter occupied
    "percent_no_vehicle",     # % without vehicle
]

# Get data
data = get_census_data(
    location=geoids,
    variables=basic_vars
)
```

### Aggregating Census Data
```python
# Calculate totals
total_pop = sum(d['population'] for d in data.values())

# Weighted average
weighted_income = sum(
    d['population'] * d['median_household_income']
    for d in data.values()
    if d['median_household_income']
) / sum(
    d['population']
    for d in data.values()
    if d['median_household_income']
)
```

---

## 🗺️ Creating Maps

### Basic Map
```python
# Simple isochrone map
map_obj = create_map(polygon=iso)
map_obj.save("my_map.html")
```

### Map with POIs
```python
# Add POIs to map
map_obj = create_map(
    polygon=iso,
    pois=restaurants,
    poi_type="restaurant"
)
```

### Choropleth Map
```python
# Create demographic choropleth
map_obj = create_map(
    polygon=iso,
    census_blocks=blocks,
    census_data=data,
    variable="median_household_income"
)
```

---

## 🔄 Common Workflows

### Complete Analysis Pipeline
```python
def analyze_location(coords, travel_time=15, travel_mode="drive"):
    """Complete accessibility analysis for a location."""

    # 1. Create isochrone
    iso = create_isochrone(coords, travel_time, travel_mode)

    # 2. Find POIs
    grocery = get_poi(iso, "supermarket")
    pharmacy = get_poi(iso, "pharmacy")

    # 3. Get demographics
    blocks = get_census_blocks(iso)[:20]
    data = get_census_data(
        [b['geoid'] for b in blocks],
        ["population", "median_household_income"]
    )

    # 4. Calculate metrics
    total_pop = sum(d['population'] for d in data.values())
    area = iso['properties']['area_sq_km']

    # 5. Return results
    return {
        'area_sq_km': area,
        'population': total_pop,
        'grocery_stores': len(grocery),
        'pharmacies': len(pharmacy),
        'pop_density': total_pop / area if area > 0 else 0
    }
```

### Multi-Location Comparison
```python
def compare_locations(location_list):
    """Compare accessibility across multiple locations."""

    results = []
    for name, coords in location_list:
        analysis = analyze_location(coords)
        analysis['name'] = name
        results.append(analysis)

    # Sort by population reached
    results.sort(key=lambda x: x['population'], reverse=True)

    return results
```

### Equity Analysis
```python
def calculate_equity_score(location):
    """Calculate accessibility equity score."""

    # Get area demographics
    iso = create_isochrone(location, 15, "walk")
    blocks = get_census_blocks(iso)[:30]

    data = get_census_data(
        [b['geoid'] for b in blocks],
        ["population", "percent_poverty", "percent_no_vehicle"]
    )

    # Find essential services
    grocery = get_poi(iso, "supermarket")
    pharmacy = get_poi(iso, "pharmacy")

    # Calculate metrics
    vulnerable_pop = sum(
        d['population'] * (d['percent_poverty'] + d['percent_no_vehicle']) / 200
        for d in data.values()
    )

    services_per_capita = (len(grocery) + len(pharmacy)) / sum(
        d['population'] for d in data.values()
    ) * 10000

    return {
        'vulnerable_population': vulnerable_pop,
        'services_per_10k': services_per_capita,
        'equity_score': services_per_capita * (1 + vulnerable_pop/100)
    }
```

---

## 🐛 Error Handling

### Robust Isochrone Creation
```python
def safe_create_isochrone(location, travel_time, travel_mode):
    """Create isochrone with error handling."""

    try:
        iso = create_isochrone(location, travel_time, travel_mode)
        if iso and 'geometry' in iso:
            return iso
        else:
            print(f"Invalid isochrone returned for {location}")
            return None
    except Exception as e:
        print(f"Error creating isochrone: {e}")
        return None
```

### Handle Missing Census Data
```python
def safe_get_census_value(data, geoid, variable, default=0):
    """Safely get census value with default."""

    if geoid in data and variable in data[geoid]:
        value = data[geoid][variable]
        return value if value is not None else default
    return default
```

### Batch Processing with Progress
```python
def batch_process_with_progress(items, process_func):
    """Process items with progress reporting."""

    results = []
    errors = []

    for i, item in enumerate(items, 1):
        print(f"Processing {i}/{len(items)}: {item['name']}")

        try:
            result = process_func(item)
            results.append(result)
        except Exception as e:
            errors.append({'item': item, 'error': str(e)})
            print(f"  Error: {e}")

    print(f"\nCompleted: {len(results)}/{len(items)} successful")
    return results, errors
```

---

## ⚡ Performance Tips

### Optimize Census Calls
```python
# ❌ Slow: Individual calls
for geoid in geoids:
    data = get_census_data([geoid], variables)

# ✅ Fast: Batch call
data = get_census_data(geoids, variables)
```

### Limit Data for Testing
```python
# Reduce travel time
iso = create_isochrone(location, travel_time=5)  # 5 min instead of 15

# Limit census blocks
blocks = get_census_blocks(iso)[:10]  # First 10 only

# Sample POIs
pois = get_poi(iso, "restaurant")[:5]  # First 5 only
```

### Cache Patterns
```python
# Simple caching
cache = {}

def cached_isochrone(location, travel_time, travel_mode):
    key = f"{location}_{travel_time}_{travel_mode}"

    if key not in cache:
        cache[key] = create_isochrone(location, travel_time, travel_mode)

    return cache[key]
```

---

## 📝 Data Export

### Export to CSV
```python
import csv

def export_analysis_csv(results, filename):
    """Export analysis results to CSV."""

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
```

### Export to GeoJSON
```python
import json

def export_geojson(isochrones, filename):
    """Export isochrones as GeoJSON."""

    features = []
    for iso in isochrones:
        features.append({
            "type": "Feature",
            "properties": iso['properties'],
            "geometry": iso['geometry']
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(filename, 'w') as f:
        json.dump(geojson, f, indent=2)
```

### Export to DataFrame
```python
import pandas as pd

def results_to_dataframe(results):
    """Convert results to pandas DataFrame."""

    df = pd.DataFrame(results)
    return df
```

---

## 🔍 Debugging Tips

### Check Isochrone Validity
```python
def validate_isochrone(iso):
    """Check if isochrone is valid."""

    checks = {
        'has_geometry': 'geometry' in iso,
        'has_properties': 'properties' in iso,
        'has_area': 'area_sq_km' in iso.get('properties', {}),
        'area_positive': iso.get('properties', {}).get('area_sq_km', 0) > 0
    }

    for check, passed in checks.items():
        print(f"{check}: {'✅' if passed else '❌'}")

    return all(checks.values())
```

### Debug Census Data
```python
def debug_census_data(data):
    """Print census data summary."""

    print(f"Total blocks: {len(data)}")
    print(f"Sample GEOID: {list(data.keys())[0] if data else 'None'}")

    if data:
        first = list(data.values())[0]
        print(f"Variables available: {list(first.keys())}")
        print(f"Sample values: {first}")
```

### Monitor API Calls
```python
import time

def timed_api_call(func, *args, **kwargs):
    """Time an API call."""

    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start

    print(f"{func.__name__} took {elapsed:.2f} seconds")
    return result
```

---

## 🎯 Common Calculations

### Population Density
```python
density = total_population / area_sq_km
```

### Per Capita Metrics
```python
grocery_per_10k = (num_grocery / total_population) * 10000
```

### Accessibility Ratio
```python
walk_drive_ratio = walk_area / drive_area
```

### Coverage Percentage
```python
coverage_pct = (covered_population / total_population) * 100
```

### Average Distance
```python
avg_distance = sum(distances) / len(distances)
```

### Weighted Average
```python
weighted_avg = sum(value * weight for value, weight in zip(values, weights)) / sum(weights)
```

---

## 📚 Additional Resources

- **Census API Documentation**: https://www.census.gov/data/developers/
- **OpenStreetMap POI Tags**: https://wiki.openstreetmap.org/wiki/Map_features
- **Coordinate Finder**: https://www.latlong.net/
- **GeoJSON Viewer**: https://geojson.io/

---

*Keep this guide handy for quick reference during your analysis!* 🚀