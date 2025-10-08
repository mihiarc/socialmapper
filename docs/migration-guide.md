# Best Practices Guide

This guide covers best practices for using the SocialMapper API effectively.

## API Overview

SocialMapper provides a simple, functional API with five core functions:

```python
from socialmapper import (
    create_isochrone,       # Create travel-time polygons
    get_census_blocks,      # Get census block groups
    get_census_data,        # Fetch demographic data
    create_map,             # Create visualizations
    get_poi                 # Find points of interest
)
```

## Error Handling

### Use Specific Exception Types

```python
from socialmapper import (
    create_isochrone,
    ValidationError,
    APIError,
    DataError
)

try:
    iso = create_isochrone(location, travel_time, travel_mode)
    blocks = get_census_blocks(polygon=iso)
    data = get_census_data([b['geoid'] for b in blocks], variables)

except ValidationError as e:
    # Handle invalid input parameters
    print(f"Invalid input: {e}")

except APIError as e:
    # Handle external API errors (Census API, OSM, etc.)
    print(f"API error: {e}")

except DataError as e:
    # Handle data processing errors
    print(f"Data error: {e}")
```

### Catch All SocialMapper Errors

```python
from socialmapper import SocialMapperError

try:
    # Your analysis code
    iso = create_isochrone(...)

except SocialMapperError as e:
    # Handle any SocialMapper-specific error
    print(f"Analysis failed: {e}")

except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {e}")
```

## Performance Optimization

### 1. Sample Large Result Sets

When working with many census blocks, sample for faster analysis:

```python
blocks = get_census_blocks(polygon=isochrone)

# Sample strategy for large result sets
if len(blocks) > 50:
    # Take first 50 blocks as sample
    sample_blocks = blocks[:50]
    geoids = [b['geoid'] for b in sample_blocks]

    # Get data for sample
    census_data = get_census_data(geoids, ["population", "median_income"])

    # Calculate sample statistics
    sample_pop = sum(d.get('population', 0) for d in census_data.values())

    # Extrapolate to full area
    estimated_total_pop = int(sample_pop * len(blocks) / len(sample_blocks))

    print(f"Estimated total population: ~{estimated_total_pop:,}")
else:
    # Small enough to analyze completely
    geoids = [b['geoid'] for b in blocks]
    census_data = get_census_data(geoids, ["population", "median_income"])
    total_pop = sum(d.get('population', 0) for d in census_data.values())
    print(f"Total population: {total_pop:,}")
```

### 2. Reuse Isochrones

Cache isochrone results when analyzing the same location multiple times:

```python
# Create isochrone once
isochrone = create_isochrone(
    location=(35.7796, -78.6382),
    travel_time=15,
    travel_mode="drive"
)

# Use for multiple analyses
blocks = get_census_blocks(polygon=isochrone)
pois = get_poi(location=(35.7796, -78.6382), travel_time=15)

# Both use the same 15-minute travel time boundary
```

### 3. Batch Census Requests

Request all variables in one call:

```python
# ✅ Good - single request
data = get_census_data(
    geoids,
    variables=["population", "median_income", "median_age", "percent_poverty"]
)

# ❌ Avoid - multiple requests
pop_data = get_census_data(geoids, ["population"])
income_data = get_census_data(geoids, ["median_income"])
age_data = get_census_data(geoids, ["median_age"])
```

### 4. Filter POIs Early

Use categories to limit POI queries:

```python
# ✅ Good - targeted search
hospitals = get_poi(
    location=(35.7796, -78.6382),
    categories=["hospital", "clinic"],
    limit=20
)

# ❌ Avoid - get everything then filter
all_pois = get_poi(location=(35.7796, -78.6382), limit=1000)
hospitals = [p for p in all_pois if p['category'] in ['hospital', 'clinic']]
```

## Data Aggregation Patterns

### Population-Weighted Averages

```python
census_data = get_census_data(geoids, ["population", "median_income"])

# Calculate population-weighted average income
total_pop = 0
weighted_income_sum = 0

for data in census_data.values():
    pop = data.get('population', 0)
    income = data.get('median_income', 0)

    if pop > 0 and income > 0:
        total_pop += pop
        weighted_income_sum += pop * income

weighted_avg_income = weighted_income_sum / total_pop if total_pop > 0 else 0

print(f"Population-weighted average income: ${weighted_avg_income:,.0f}")
```

### Aggregating Multiple Metrics

```python
from collections import defaultdict

census_data = get_census_data(
    geoids,
    variables=["population", "median_income", "median_age"]
)

# Calculate aggregated statistics
stats = defaultdict(list)

for data in census_data.values():
    if data.get('population', 0) > 0:
        stats['population'].append(data['population'])
    if data.get('median_income', 0) > 0:
        stats['median_income'].append(data['median_income'])
    if data.get('median_age', 0) > 0:
        stats['median_age'].append(data['median_age'])

# Calculate summary statistics
summary = {}
for key, values in stats.items():
    if values:
        summary[key] = {
            'total': sum(values) if key == 'population' else None,
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'median': sorted(values)[len(values) // 2]
        }

print("Summary Statistics:")
for key, stat in summary.items():
    print(f"\n{key.replace('_', ' ').title()}:")
    for metric, value in stat.items():
        if value is not None:
            print(f"  {metric}: {value:,.0f}")
```

## Working with GeoJSON

### Save Results

```python
import json

# Create isochrone
iso = create_isochrone((35.7796, -78.6382), travel_time=15)

# Save as GeoJSON file
with open('isochrone.geojson', 'w') as f:
    json.dump(iso, f, indent=2)

# Load and use
with open('isochrone.geojson', 'r') as f:
    loaded_iso = json.load(f)
    blocks = get_census_blocks(polygon=loaded_iso)
```

### Use with Web Mapping Libraries

```python
# The GeoJSON output works directly with Leaflet, Mapbox, etc.
iso = create_isochrone(location, travel_time=15)

# For Leaflet:
# L.geoJSON(iso).addTo(map);

# For Mapbox GL JS:
# map.addSource('isochrone', { type: 'geojson', data: iso });
```

## Multi-Location Analysis

### Parallel Analysis Pattern

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data

def analyze_location(name, coords, travel_time=15):
    """Analyze a single location."""
    iso = create_isochrone(coords, travel_time=travel_time)
    blocks = get_census_blocks(polygon=iso)

    if not blocks:
        return {'name': name, 'population': 0}

    geoids = [b['geoid'] for b in blocks]
    census_data = get_census_data(geoids, ["population"])

    total_pop = sum(d.get('population', 0) for d in census_data.values())

    return {
        'name': name,
        'coordinates': coords,
        'area_km2': iso['properties']['area_sq_km'],
        'population': total_pop,
        'block_count': len(blocks)
    }

# Analyze multiple locations
locations = {
    "Downtown Raleigh": (35.7796, -78.6382),
    "North Hills": (35.8321, -78.6414),
    "Cary": (35.7915, -78.7811)
}

results = []
for name, coords in locations.items():
    try:
        result = analyze_location(name, coords, travel_time=15)
        results.append(result)
        print(f"✓ {name}: {result['population']:,} people")
    except Exception as e:
        print(f"✗ {name}: {e}")

# Find best location
if results:
    best = max(results, key=lambda x: x['population'])
    print(f"\nBest population reach: {best['name']} ({best['population']:,} people)")
```

### Comparison Analysis

```python
def compare_travel_modes(location, travel_time=15):
    """Compare accessibility by different travel modes."""
    modes = ["drive", "walk", "bike"]
    results = {}

    for mode in modes:
        try:
            iso = create_isochrone(location, travel_time, mode)
            blocks = get_census_blocks(polygon=iso)

            geoids = [b['geoid'] for b in blocks[:30]]  # Sample for speed
            census_data = get_census_data(geoids, ["population"])

            sample_pop = sum(d.get('population', 0) for d in census_data.values())
            estimated_pop = int(sample_pop * len(blocks) / min(len(geoids), 30))

            results[mode] = {
                'area_km2': iso['properties']['area_sq_km'],
                'population': estimated_pop
            }
        except Exception as e:
            print(f"Error for {mode}: {e}")

    return results

# Compare modes
location = (35.7796, -78.6382)  # Raleigh, NC
comparison = compare_travel_modes(location, travel_time=10)

print(f"\n10-minute accessibility comparison:")
for mode, data in comparison.items():
    print(f"  {mode:8} → {data['area_km2']:6.2f} km², ~{data['population']:,} people")
```

## Validation and Data Quality

### Validate Inputs

```python
def validate_coordinates(lat, lon):
    """Validate coordinate ranges."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
    return True

def validate_travel_time(time):
    """Validate travel time."""
    if not (1 <= time <= 120):
        raise ValueError(f"Travel time must be between 1 and 120 minutes, got {time}")
    return True

# Use in your code
lat, lon = 35.7796, -78.6382
travel_time = 15

validate_coordinates(lat, lon)
validate_travel_time(travel_time)

iso = create_isochrone((lat, lon), travel_time=travel_time)
```

### Handle Missing Data

```python
census_data = get_census_data(geoids, ["population", "median_income", "median_age"])

# Handle missing or zero values
for geoid, data in census_data.items():
    pop = data.get('population', 0) or 0
    income = data.get('median_income', None)
    age = data.get('median_age', None)

    # Only use non-null, non-zero values
    if pop > 0:
        print(f"Block {geoid}: {pop} people")

        if income and income > 0:
            print(f"  Median income: ${income:,}")
        else:
            print(f"  Median income: [No data]")
```

## Testing

### Unit Testing Example

```python
import unittest
from socialmapper import create_isochrone, ValidationError

class TestIsochrones(unittest.TestCase):

    def test_valid_isochrone(self):
        """Test creating a valid isochrone."""
        iso = create_isochrone(
            location=(35.7796, -78.6382),
            travel_time=15,
            travel_mode="drive"
        )

        self.assertEqual(iso['type'], 'Feature')
        self.assertIn('geometry', iso)
        self.assertIn('properties', iso)
        self.assertEqual(iso['properties']['travel_time'], 15)
        self.assertGreater(iso['properties']['area_sq_km'], 0)

    def test_invalid_travel_time(self):
        """Test that invalid travel time raises error."""
        with self.assertRaises(ValidationError):
            create_isochrone(
                location=(35.7796, -78.6382),
                travel_time=150  # Too long
            )

    def test_invalid_travel_mode(self):
        """Test that invalid travel mode raises error."""
        with self.assertRaises(ValidationError):
            create_isochrone(
                location=(35.7796, -78.6382),
                travel_time=15,
                travel_mode="teleport"  # Invalid
            )

if __name__ == '__main__':
    unittest.main()
```

## See Also

- [API Reference](api-reference.md) - Complete function documentation
- [Census Variables](reference/census-variables.md) - Available demographic data
- [Examples](https://github.com/mihiarc/socialmapper/tree/main/examples) - Code examples
- [User Guide](user-guide/index.md) - In-depth guides
