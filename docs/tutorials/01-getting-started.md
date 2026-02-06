# Getting Started with SocialMapper

This tutorial introduces SocialMapper and walks through your first spatial analysis in under 5 minutes.

## What is SocialMapper?

SocialMapper is a Python library that combines three powerful data sources into a unified API:

- **OpenStreetMap** - Points of interest (restaurants, schools, hospitals, etc.)
- **US Census Bureau** - Demographics (population, income, age, etc.)
- **Routing Engines** - Travel-time analysis (isochrones)

Instead of learning 4+ different libraries and spending hours on setup, you can start analyzing in minutes.

## Installation

```bash
pip install socialmapper
```

## Setup

### Get a Census API Key

For census data queries, you'll need a free Census API key:

1. Visit: https://api.census.gov/data/key_signup.html
2. Fill out the form (takes 30 seconds)
3. Set the environment variable:

```bash
export CENSUS_API_KEY=your_key_here
```

### Your First Analysis

```python
from socialmapper import create_isochrone, get_poi, get_census_data

# Step 1: Create an isochrone (travel-time polygon)
isochrone = create_isochrone(
    location="Seattle, WA",
    travel_time=15,      # 15 minutes
    travel_mode="drive"  # or "walk", "bike"
)

print(f"Area reachable in 15 min: {isochrone['properties']['area_sq_km']:.1f} km²")

# Step 2: Find points of interest
food_places = get_poi(
    location="Seattle, WA",
    categories=["food_and_drink"],
    limit=10
)

print(f"Found {len(food_places)} food & drink places nearby")
for place in food_places[:3]:
    print(f"  - {place['name']}: {place['distance_km']:.2f} km")

# Step 3: Get census demographics
census_result = get_census_data(
    location=isochrone,  # Use the isochrone polygon
    variables=["population", "median_income"]
)

# Summarize population
total_pop = sum(
    data.get("population", 0)
    for data in census_result.data.values()
    if data.get("population")
)
print(f"Total population in area: {total_pop:,}")
```

## The Five Core Functions

SocialMapper provides five main functions:

| Function | Purpose | Example Use |
|----------|---------|-------------|
| `create_isochrone()` | Generate travel-time polygons | "What area is reachable in 20 minutes?" |
| `get_poi()` | Find points of interest | "Where are the hospitals nearby?" |
| `get_census_blocks()` | Get census geography | "What census blocks are in this area?" |
| `get_census_data()` | Retrieve demographics | "What's the median income here?" |
| `create_map()` | Generate visualizations | "Show me a population map" |

## Next Steps

Now that you understand the basics:

1. **[Isochrone Analysis](02-isochrone-analysis.md)** - Deep dive into travel-time analysis
2. **[Points of Interest](03-points-of-interest.md)** - Master POI queries
3. **[Census Data](04-census-data.md)** - Work with demographics
4. **[Mapping & Visualization](05-mapping-visualization.md)** - Create beautiful maps
5. **[Complete Workflow](06-complete-workflow.md)** - Build a full analysis

## Quick Reference

```python
from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data,
    create_map,
    analyze_multiple_pois,
)
```

## Troubleshooting

### "Missing API Key" Error

Set your Census API key:
```bash
export CENSUS_API_KEY=your_key_here
```

### Slow Isochrone Generation

SocialMapper uses the Valhalla routing engine which is fast (1-2 seconds):
```python
iso = create_isochrone(location)  # ~1-2 seconds via Valhalla
```

### Rate Limiting

The Census API has rate limits. If you hit them:
- Add delays between requests
- Use batch queries where possible
- Cache results locally
