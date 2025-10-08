# Quick Start Guide

Get up and running with SocialMapper in minutes! This guide will walk you through your first analysis using the simple, functional API.

## Prerequisites

- Python 3.11 or higher installed
- Internet connection for downloading data
- (Optional) Census API key for census data - get one free at https://api.census.gov/data/key_signup.html

## Installation

```bash
pip install socialmapper
```

## Your First Analysis

Let's analyze library accessibility in Raleigh, NC:

### Basic Python Script

Create a file `library_analysis.py`:

```python
from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data
)

# 1. Find libraries in the area
print("Finding libraries in Raleigh...")
libraries = get_poi(
    location=(35.7796, -78.6382),  # Downtown Raleigh, NC
    categories=["library"],
    limit=10
)
print(f"Found {len(libraries)} libraries")

# 2. Create a 15-minute driving isochrone for the first library
print("\nAnalyzing first library...")
library = libraries[0]
print(f"Library: {library['name']}")

isochrone = create_isochrone(
    location=(library['lat'], library['lon']),
    travel_time=15,
    travel_mode="drive"
)

print(f"Isochrone area: {isochrone['properties']['area_sq_km']:.2f} km²")

# 3. Get census blocks within the isochrone
blocks = get_census_blocks(polygon=isochrone)
print(f"Census blocks found: {len(blocks)}")

# 4. Get demographic data
geoids = [block['geoid'] for block in blocks]
demographics = get_census_data(
    location=geoids,
    variables=["population", "median_income", "median_age"]
)

# 5. Calculate totals
total_pop = sum(d.get('population', 0) for d in demographics.values())
avg_income = sum(
    d.get('median_income', 0) for d in demographics.values()
    if d.get('median_income', 0) > 0
) / len([d for d in demographics.values() if d.get('median_income', 0) > 0])

print(f"\n📊 Results:")
print(f"Population within 15 minutes: {total_pop:,}")
print(f"Average median income: ${avg_income:,.0f}")
```

Run it:
```bash
python library_analysis.py
```

## Understanding the Results

The analysis uses five simple functions:

1. **`get_poi()`** - Finds points of interest (libraries, schools, hospitals, etc.)
2. **`create_isochrone()`** - Creates a travel-time polygon (15-min drive area)
3. **`get_census_blocks()`** - Gets census block groups within the area
4. **`get_census_data()`** - Fetches demographic data for those blocks
5. **`create_map()`** - (Optional) Creates visualizations

Each function returns simple Python data structures (dicts, lists) that are easy to work with.

## Try Different Analyses

### Find Restaurants

```python
from socialmapper import get_poi

# Find restaurants within 5km
restaurants = get_poi(
    location=(35.7796, -78.6382),  # Raleigh, NC
    categories=["restaurant", "cafe"],
    limit=50
)

print(f"Found {len(restaurants)} restaurants")
for r in restaurants[:5]:
    print(f"  {r['name']}: {r['distance_km']:.2f} km away")
```

### Analyze Walking Distance

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data

# Create 10-minute walking isochrone
iso = create_isochrone(
    location=(35.7796, -78.6382),
    travel_time=10,
    travel_mode="walk"
)

# Get population data
blocks = get_census_blocks(polygon=iso)
geoids = [b['geoid'] for b in blocks]
data = get_census_data(geoids, ["population"])

total = sum(d.get('population', 0) for d in data.values())
print(f"Population within 10-min walk: {total:,}")
```

### Compare Multiple Locations

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data

# Compare two locations
locations = {
    "Downtown": (35.7796, -78.6382),
    "North Hills": (35.8321, -78.6414)
}

for name, coords in locations.items():
    iso = create_isochrone(coords, travel_time=15)
    blocks = get_census_blocks(polygon=iso)
    geoids = [b['geoid'] for b in blocks]
    data = get_census_data(geoids, ["population"])

    pop = sum(d.get('population', 0) for d in data.values())
    print(f"{name}: {pop:,} people within 15 minutes")
```

### Create a Visualization

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map
)

# Create isochrone
iso = create_isochrone((35.7796, -78.6382), travel_time=15)

# Get census data
blocks = get_census_blocks(polygon=iso)
geoids = [b['geoid'] for b in blocks]
census_data = get_census_data(geoids, ["population"])

# Add population to blocks
for block in blocks:
    geoid = block['geoid']
    block['population'] = census_data.get(geoid, {}).get('population', 0)

# Create map
create_map(
    data=blocks,
    column='population',
    title='Population within 15-minute drive',
    save_path='population_map.png'
)

print("Map saved to population_map.png")
```

## Common Patterns

### Sample for Performance

When working with many census blocks, sample for faster results:

```python
blocks = get_census_blocks(polygon=isochrone)

if len(blocks) > 50:
    # Sample first 50 blocks
    sample_blocks = blocks[:50]
    geoids = [b['geoid'] for b in sample_blocks]

    data = get_census_data(geoids, ["population"])
    sample_pop = sum(d.get('population', 0) for d in data.values())

    # Estimate total
    estimated_total = int(sample_pop * len(blocks) / len(sample_blocks))
    print(f"Estimated population: ~{estimated_total:,}")
```

### Error Handling

```python
from socialmapper import create_isochrone, ValidationError, APIError

try:
    iso = create_isochrone(
        location=(35.7796, -78.6382),
        travel_time=15,
        travel_mode="drive"
    )
    print(f"Created isochrone: {iso['properties']['area_sq_km']:.2f} km²")

except ValidationError as e:
    print(f"Invalid input: {e}")

except APIError as e:
    print(f"API error: {e}")
```

## Configuration

### Set Census API Key

Create a `.env` file in your project directory:

```bash
CENSUS_API_KEY=your-api-key-here
```

Get a free key at: https://api.census.gov/data/key_signup.html

Or set it in your code (not recommended for production):

```python
import os
os.environ['CENSUS_API_KEY'] = 'your-api-key-here'
```

### Configure Cache Location

```bash
SOCIALMAPPER_CACHE_DIR=/path/to/cache
```

## Next Steps

Now that you've completed your first analysis:

- 📖 [Read the API Reference](../api-reference.md) - Detailed documentation of all functions
- 📊 [View Census Variables](../reference/census-variables.md) - Available demographic data
- 💡 [See More Examples](https://github.com/mihiarc/socialmapper/tree/main/examples) - Advanced use cases
- 🗺️ [User Guide](../user-guide/index.md) - In-depth guides

## Need Help?

- **Documentation:** Browse the [User Guide](../user-guide/index.md)
- **Examples:** Check out [example scripts](https://github.com/mihiarc/socialmapper/tree/main/examples)
- **Issues:** Report problems on [GitHub](https://github.com/mihiarc/socialmapper/issues)

## What You Learned

✅ Import and use the five core functions
✅ Create travel-time isochrones
✅ Find points of interest
✅ Get census demographic data
✅ Combine spatial and demographic analysis
✅ Create visualizations
✅ Handle errors properly

Ready to explore more? Check out the [API Reference](../api-reference.md) for complete function documentation!
