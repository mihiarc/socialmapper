# Working with Census Data

This tutorial teaches you how to retrieve and analyze US Census demographic data for any geographic area.

## Overview

The US Census Bureau provides detailed demographic data at various geographic levels. SocialMapper makes it easy to:

- Get census block groups for any area
- Retrieve demographic variables (population, income, age, etc.)
- Combine census data with isochrones and POIs

## Prerequisites

You'll need a Census API key for production use:

1. Visit: https://api.census.gov/data/key_signup.html
2. Fill out the form (takes 30 seconds)
3. Set the environment variable:

```bash
export CENSUS_API_KEY=your_key_here
```

## Getting Census Block Groups

Census block groups are the smallest geographic unit for which detailed demographic data is available.

### From a Point Location

```python
from socialmapper import get_census_blocks

# Get census blocks around a location
blocks = get_census_blocks(
    location=(47.6062, -122.3321),  # Seattle
    radius_km=2
)

print(f"Found {len(blocks)} census block groups")
for block in blocks[:3]:
    print(f"  GEOID: {block['geoid']}")
    print(f"  Area: {block['area_sq_km']:.2f} km²")
```

### From a Polygon (Isochrone)

```python
from socialmapper import create_isochrone, get_census_blocks

# Create an isochrone
isochrone = create_isochrone("Portland, OR", travel_time=15)

# Get census blocks within the isochrone
blocks = get_census_blocks(polygon=isochrone)

print(f"Found {len(blocks)} census block groups in the isochrone")
```

### Understanding Block Group Results

Each census block group includes:

```python
block = blocks[0]

print(block.keys())
# dict_keys(['geoid', 'state_fips', 'county_fips', 'tract', 'block_group', 'geometry', 'area_sq_km'])

# GEOID: 12-character identifier
print(f"GEOID: {block['geoid']}")  # e.g., "410510001011"

# Geographic hierarchy
print(f"State FIPS: {block['state_fips']}")      # e.g., "41" (Oregon)
print(f"County FIPS: {block['county_fips']}")    # e.g., "051"
print(f"Tract: {block['tract']}")                 # e.g., "000101"
print(f"Block Group: {block['block_group']}")    # e.g., "1"

# Geometry is GeoJSON
print(f"Geometry type: {block['geometry']['type']}")  # Polygon
```

## Retrieving Census Data

### Basic Usage

```python
from socialmapper import get_census_data

# Get data for specific GEOIDs
result = get_census_data(
    location=["410510001011", "410510001012"],  # Oregon block groups
    variables=["population"]
)

print(f"Query type: {result.location_type}")  # "geoids"
print(f"Year: {result.query_info['year']}")

# Access the data
for geoid, data in result.data.items():
    print(f"{geoid}: Population = {data.get('population', 'N/A')}")
```

### Using Common Variable Names

SocialMapper translates common names to Census variable codes:

```python
result = get_census_data(
    location=["410510001011"],
    variables=["population", "median_income", "median_age"]
)

# These are translated to:
# population -> B01003_001E
# median_income -> B19013_001E
# median_age -> B01002_001E
```

### Available Variable Names

| Common Name | Census Code | Description |
|-------------|-------------|-------------|
| `population` | B01003_001E | Total population |
| `median_income` | B19013_001E | Median household income |
| `median_age` | B01002_001E | Median age |
| `total_households` | B11001_001E | Total households |
| `housing_units` | B25001_001E | Total housing units |
| `median_rent` | B25064_001E | Median gross rent |
| `median_home_value` | B25077_001E | Median home value |

You can also use raw Census variable codes directly:

```python
result = get_census_data(
    location=["410510001011"],
    variables=["B01003_001E", "B19013_001E"]  # Raw codes
)
```

## Three Ways to Query Census Data

### 1. By Polygon (Isochrone)

```python
from socialmapper import create_isochrone, get_census_data

# Create an isochrone
isochrone = create_isochrone("Denver, CO", travel_time=15)

# Get census data for the entire isochrone area
result = get_census_data(
    location=isochrone,
    variables=["population", "median_income"]
)

print(f"Location type: {result.location_type}")  # "polygon"
print(f"Block groups analyzed: {len(result.data)}")
```

### 2. By GEOID List

```python
# Get data for specific GEOIDs
geoids = ["060750201001", "060750201002", "060750201003"]

result = get_census_data(
    location=geoids,
    variables=["population", "median_income"]
)

print(f"Location type: {result.location_type}")  # "geoids"
```

### 3. By Point Location

```python
# Get data for the block group containing a point
result = get_census_data(
    location=(37.7749, -122.4194),  # San Francisco
    variables=["population"]
)

print(f"Location type: {result.location_type}")  # "point"
```

## Aggregating Census Data

### Summing Population

```python
from socialmapper import create_isochrone, get_census_data

isochrone = create_isochrone("Chicago, IL", travel_time=20)
result = get_census_data(isochrone, variables=["population"])

# Sum population across all block groups
total_pop = sum(
    data.get("population", 0)
    for data in result.data.values()
    if data.get("population") is not None
)

print(f"Total population in 20-min drive: {total_pop:,}")
```

### Calculating Averages

```python
# Get median incomes
result = get_census_data(isochrone, variables=["median_income"])

# Calculate average median income
incomes = [
    data["median_income"]
    for data in result.data.values()
    if data.get("median_income") is not None
]

if incomes:
    avg_income = sum(incomes) / len(incomes)
    print(f"Average median income: ${avg_income:,.0f}")
```

### Weighted Average (Population-Weighted)

```python
result = get_census_data(
    isochrone,
    variables=["population", "median_income"]
)

# Calculate population-weighted average income
total_pop = 0
weighted_income = 0

for data in result.data.values():
    pop = data.get("population", 0)
    income = data.get("median_income")

    if pop and income:
        total_pop += pop
        weighted_income += pop * income

if total_pop > 0:
    avg_income = weighted_income / total_pop
    print(f"Population-weighted average income: ${avg_income:,.0f}")
```

## Practical Examples

### Example 1: Demographic Profile of an Area

```python
from socialmapper import create_isochrone, get_census_data

# Create area of interest
location = "Austin, TX"
isochrone = create_isochrone(location, travel_time=15)

# Get multiple variables
result = get_census_data(
    isochrone,
    variables=["population", "median_income", "median_age", "total_households"]
)

# Aggregate
stats = {
    "population": 0,
    "incomes": [],
    "ages": [],
    "households": 0
}

for data in result.data.values():
    if data.get("population"):
        stats["population"] += data["population"]
    if data.get("median_income"):
        stats["incomes"].append(data["median_income"])
    if data.get("median_age"):
        stats["ages"].append(data["median_age"])
    if data.get("total_households"):
        stats["households"] += data["total_households"]

print(f"Demographic Profile: {location} (15-min drive)")
print(f"  Total Population: {stats['population']:,}")
print(f"  Total Households: {stats['households']:,}")
if stats["incomes"]:
    print(f"  Median Income Range: ${min(stats['incomes']):,} - ${max(stats['incomes']):,}")
if stats["ages"]:
    print(f"  Median Age Range: {min(stats['ages']):.1f} - {max(stats['ages']):.1f}")
```

### Example 2: Compare Two Locations

```python
from socialmapper import create_isochrone, get_census_data

locations = ["Seattle, WA", "Portland, OR"]

for loc in locations:
    iso = create_isochrone(loc, travel_time=15)
    result = get_census_data(iso, variables=["population", "median_income"])

    total_pop = sum(
        d.get("population", 0) for d in result.data.values()
        if d.get("population")
    )

    incomes = [
        d["median_income"] for d in result.data.values()
        if d.get("median_income")
    ]

    print(f"\n{loc} (15-min drive):")
    print(f"  Population: {total_pop:,}")
    if incomes:
        print(f"  Avg Median Income: ${sum(incomes)/len(incomes):,.0f}")
```

### Example 3: Income Inequality Analysis

```python
from socialmapper import create_isochrone, get_census_data
import statistics

isochrone = create_isochrone("San Francisco, CA", travel_time=20)
result = get_census_data(isochrone, variables=["median_income", "population"])

# Extract income data with populations
income_data = []
for data in result.data.values():
    if data.get("median_income") and data.get("population"):
        income_data.append({
            "income": data["median_income"],
            "pop": data["population"]
        })

if income_data:
    incomes = [d["income"] for d in income_data]

    print("Income Distribution Analysis:")
    print(f"  Minimum: ${min(incomes):,}")
    print(f"  Maximum: ${max(incomes):,}")
    print(f"  Mean: ${statistics.mean(incomes):,.0f}")
    print(f"  Median: ${statistics.median(incomes):,.0f}")
    print(f"  Std Dev: ${statistics.stdev(incomes):,.0f}")

    # Income ratio (max/min)
    ratio = max(incomes) / min(incomes)
    print(f"  Income Ratio (max/min): {ratio:.1f}x")
```

## Working with Different Years

```python
# Default is 2023 ACS 5-year estimates
result_2023 = get_census_data(location, variables=["population"])

# Use a different year
result_2022 = get_census_data(location, variables=["population"], year=2022)
result_2021 = get_census_data(location, variables=["population"], year=2021)
```

## Understanding the CensusDataResult

```python
result = get_census_data(isochrone, variables=["population", "median_income"])

# Result structure
print(type(result))  # CensusDataResult

# Data is a dict: {geoid: {variable: value}}
print(result.data)
# {'410510001011': {'population': 1234, 'median_income': 65000}, ...}

# Location type tells you how the query was made
print(result.location_type)  # 'polygon', 'geoids', or 'point'

# Query info provides metadata
print(result.query_info)
# {'year': 2023, 'variables': ['population', 'median_income'], ...}
```

## Handling Missing Data

Census data sometimes has missing values:

```python
result = get_census_data(location, variables=["median_income"])

# Check for missing data
for geoid, data in result.data.items():
    income = data.get("median_income")
    if income is None:
        print(f"Missing income data for {geoid}")
    elif income < 0:
        print(f"Suppressed data for {geoid} (too few samples)")
    else:
        print(f"{geoid}: ${income:,}")
```

## Best Practices

### 1. Batch Your Requests

```python
# Good: One request with multiple variables
result = get_census_data(location, variables=["population", "median_income", "median_age"])

# Avoid: Multiple requests
pop = get_census_data(location, variables=["population"])
income = get_census_data(location, variables=["median_income"])
age = get_census_data(location, variables=["median_age"])
```

### 2. Cache Results

```python
import json

# Fetch data
result = get_census_data(isochrone, variables=["population"])

# Save to file
with open("census_cache.json", "w") as f:
    json.dump(result.data, f)

# Load from cache
with open("census_cache.json", "r") as f:
    cached_data = json.load(f)
```

### 3. Handle Rate Limits

```python
import time

locations = ["Seattle, WA", "Portland, OR", "San Francisco, CA"]

for loc in locations:
    iso = create_isochrone(loc, travel_time=15)
    result = get_census_data(iso, variables=["population"])
    print(f"{loc}: {sum(d.get('population', 0) for d in result.data.values()):,}")

    time.sleep(1)  # Rate limit protection
```

## Next Steps

Now that you can work with census data:

- **[Mapping & Visualization](05-mapping-visualization.md)** - Create choropleth maps
- **[Complete Workflow](06-complete-workflow.md)** - Full analysis examples
- **[Food Desert Case Study](07-food-desert-case-study.md)** - Real-world application
