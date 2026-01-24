# Complete Workflow: Library Access Equity Study

This tutorial demonstrates a complete SocialMapper workflow by analyzing library accessibility and the demographics of populations served.

## Project Overview

**Research Question:** How equitable is library access in a city? Who has walkable access to public libraries?

**Workflow Steps:**
1. Create walking isochrone from downtown
2. Find all libraries in the area
3. Get census blocks in the reachable zone
4. Retrieve demographic data
5. Create choropleth showing population with library access
6. Generate summary statistics

## Setup

```python
import json
from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data,
    create_map
)
```

## Step 1: Define the Study Area

```python
# Study location: Portland, OR downtown
location = "Portland, OR"

# Create a 20-minute walking isochrone
# This represents areas with walkable access
walk_isochrone = create_isochrone(
    location=location,
    travel_time=20,
    travel_mode="walk"
)

print(f"Study Area: {location}")
print(f"Travel Mode: Walking")
print(f"Travel Time: 20 minutes")
print(f"Area Coverage: {walk_isochrone['properties']['area_sq_km']:.2f} km²")
```

## Step 2: Find Libraries

```python
# Query for public libraries
libraries = get_poi(
    location=location,
    categories=["education"],
    travel_time=20,  # Within 20-min walk
    limit=50
)

print(f"\nLibraries found: {len(libraries)}")
for lib in libraries:
    print(f"  - {lib['name']}: {lib['distance_km']:.2f} km from center")
```

## Step 3: Get Census Geography

```python
# Get census blocks within the walkable area
blocks = get_census_blocks(polygon=walk_isochrone)

print(f"\nCensus block groups in study area: {len(blocks)}")

# Show first few
for block in blocks[:3]:
    print(f"  GEOID: {block['geoid']}, Area: {block['area_sq_km']:.2f} km²")
```

## Step 4: Retrieve Demographics

```python
# Get demographic data for all blocks
geoids = [b['geoid'] for b in blocks]

census_result = get_census_data(
    location=geoids,
    variables=["population", "median_income", "median_age"]
)

print(f"\nCensus data retrieved:")
print(f"  Year: {census_result.query_info['year']}")
print(f"  Block groups: {len(census_result.data)}")
```

## Step 5: Analyze the Data

```python
# Combine census data with geographic data
for block in blocks:
    data = census_result.data.get(block['geoid'], {})
    block['population'] = data.get('population', 0) or 0
    block['median_income'] = data.get('median_income', 0) or 0
    block['median_age'] = data.get('median_age', 0) or 0

# Calculate totals and statistics
total_population = sum(b['population'] for b in blocks)
populations = [b['population'] for b in blocks if b['population'] > 0]
incomes = [b['median_income'] for b in blocks if b['median_income'] > 0]
ages = [b['median_age'] for b in blocks if b['median_age'] > 0]

print("\n" + "="*50)
print("STUDY RESULTS: Library Access Equity Analysis")
print("="*50)

print(f"\nGeographic Coverage:")
print(f"  Area with walkable library access: {walk_isochrone['properties']['area_sq_km']:.2f} km²")
print(f"  Census block groups: {len(blocks)}")
print(f"  Libraries available: {len(libraries)}")

print(f"\nPopulation with Library Access:")
print(f"  Total population: {total_population:,}")
print(f"  Average per block group: {total_population / len(blocks):,.0f}")

if incomes:
    print(f"\nEconomic Profile:")
    print(f"  Median income range: ${min(incomes):,} - ${max(incomes):,}")
    print(f"  Average median income: ${sum(incomes)/len(incomes):,.0f}")

if ages:
    print(f"\nAge Profile:")
    print(f"  Median age range: {min(ages):.1f} - {max(ages):.1f} years")
    print(f"  Average median age: {sum(ages)/len(ages):.1f} years")
```

## Step 6: Create Visualizations

### Population Map

```python
# Filter blocks with population data
blocks_with_pop = [b for b in blocks if b['population'] > 0]

# Create population choropleth
pop_map = create_map(
    data=blocks_with_pop,
    column="population",
    title="Population with Walkable Library Access",
    save_path="library_access_population.png"
)

print(f"\nPopulation map saved: {pop_map.file_path}")
```

### Income Map

```python
# Filter blocks with income data
blocks_with_income = [b for b in blocks if b['median_income'] > 0]

# Create income choropleth
income_map = create_map(
    data=blocks_with_income,
    column="median_income",
    title="Median Income in Library-Accessible Areas",
    save_path="library_access_income.png"
)

print(f"Income map saved: {income_map.file_path}")
```

## Step 7: Export Data

### Save as GeoJSON

```python
# Export for web mapping
geojson_result = create_map(
    data=blocks_with_pop,
    column="population",
    export_format="geojson"
)

with open("library_access.geojson", "w") as f:
    json.dump(geojson_result.geojson_data, f, indent=2)

print(f"GeoJSON exported: library_access.geojson")
```

### Save Summary Report

```python
# Create summary report
report = {
    "study": "Library Access Equity Analysis",
    "location": location,
    "travel_mode": "walk",
    "travel_time_minutes": 20,
    "coverage": {
        "area_sq_km": walk_isochrone['properties']['area_sq_km'],
        "block_groups": len(blocks),
        "libraries": len(libraries)
    },
    "demographics": {
        "total_population": total_population,
        "avg_median_income": sum(incomes)/len(incomes) if incomes else None,
        "avg_median_age": sum(ages)/len(ages) if ages else None
    },
    "libraries": [
        {"name": lib['name'], "distance_km": lib['distance_km']}
        for lib in libraries
    ]
}

with open("library_access_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"Report saved: library_access_report.json")
```

## Complete Script

Here's the full workflow as a single, runnable script:

```python
#!/usr/bin/env python3
"""Library Access Equity Analysis - Complete Workflow"""

import json
from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data,
    create_map
)


def analyze_library_access(location: str, travel_time: int = 20):
    """
    Analyze library accessibility for a given location.

    Parameters
    ----------
    location : str
        City name (e.g., "Portland, OR")
    travel_time : int
        Walking time in minutes

    Returns
    -------
    dict
        Analysis results
    """
    print(f"\n{'='*60}")
    print(f"Library Access Equity Analysis: {location}")
    print(f"{'='*60}")

    # Step 1: Create walking isochrone
    print("\n[1/6] Creating walking isochrone...")
    isochrone = create_isochrone(
        location=location,
        travel_time=travel_time,
        travel_mode="walk"
    )
    print(f"      Area: {isochrone['properties']['area_sq_km']:.2f} km²")

    # Step 2: Find libraries
    print("\n[2/6] Finding libraries...")
    libraries = get_poi(
        location=location,
        categories=["education"],
        travel_time=travel_time,
        limit=50
    )
    print(f"      Found: {len(libraries)} libraries")

    # Step 3: Get census blocks
    print("\n[3/6] Getting census blocks...")
    blocks = get_census_blocks(polygon=isochrone)
    print(f"      Block groups: {len(blocks)}")

    # Step 4: Get demographics
    print("\n[4/6] Retrieving demographics...")
    geoids = [b['geoid'] for b in blocks]
    census_result = get_census_data(
        location=geoids,
        variables=["population", "median_income", "median_age"]
    )
    print(f"      Data retrieved for {len(census_result.data)} blocks")

    # Step 5: Process data
    print("\n[5/6] Processing data...")
    for block in blocks:
        data = census_result.data.get(block['geoid'], {})
        block['population'] = data.get('population', 0) or 0
        block['median_income'] = data.get('median_income', 0) or 0
        block['median_age'] = data.get('median_age', 0) or 0

    # Calculate statistics
    total_pop = sum(b['population'] for b in blocks)
    incomes = [b['median_income'] for b in blocks if b['median_income'] > 0]
    ages = [b['median_age'] for b in blocks if b['median_age'] > 0]

    # Step 6: Create maps
    print("\n[6/6] Creating visualizations...")
    blocks_valid = [b for b in blocks if b['population'] > 0]

    pop_map = create_map(
        data=blocks_valid,
        column="population",
        title=f"Population with Library Access - {location}",
        save_path=f"{location.replace(', ', '_').lower()}_library_pop.png"
    )
    print(f"      Saved: {pop_map.file_path}")

    # Summary
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Location: {location}")
    print(f"Travel time: {travel_time} minutes walking")
    print(f"Area covered: {isochrone['properties']['area_sq_km']:.2f} km²")
    print(f"Libraries: {len(libraries)}")
    print(f"Block groups: {len(blocks)}")
    print(f"Total population with access: {total_pop:,}")
    if incomes:
        print(f"Average median income: ${sum(incomes)/len(incomes):,.0f}")
    if ages:
        print(f"Average median age: {sum(ages)/len(ages):.1f} years")

    return {
        "location": location,
        "travel_time": travel_time,
        "isochrone": isochrone,
        "libraries": libraries,
        "blocks": blocks,
        "total_population": total_pop,
        "avg_income": sum(incomes)/len(incomes) if incomes else None,
        "avg_age": sum(ages)/len(ages) if ages else None
    }


if __name__ == "__main__":
    # Run analysis
    results = analyze_library_access("Portland, OR", travel_time=20)

    # Save results
    with open("analysis_results.json", "w") as f:
        json.dump({
            "location": results["location"],
            "travel_time": results["travel_time"],
            "total_population": results["total_population"],
            "avg_income": results["avg_income"],
            "avg_age": results["avg_age"],
            "libraries": [
                {"name": lib["name"], "distance_km": lib["distance_km"]}
                for lib in results["libraries"]
            ]
        }, f, indent=2)

    print("\nAnalysis complete!")
```

## Extending the Analysis

### Compare Multiple Cities

```python
cities = ["Portland, OR", "Seattle, WA", "San Francisco, CA"]

results = {}
for city in cities:
    result = analyze_library_access(city, travel_time=20)
    results[city] = {
        "population": result["total_population"],
        "libraries": len(result["libraries"]),
        "avg_income": result["avg_income"]
    }

# Compare
print("\n" + "="*60)
print("CITY COMPARISON")
print("="*60)
for city, data in results.items():
    print(f"\n{city}:")
    print(f"  Population with access: {data['population']:,}")
    print(f"  Libraries: {data['libraries']}")
    if data['avg_income']:
        print(f"  Avg income: ${data['avg_income']:,.0f}")
```

### Analyze Different Travel Modes

```python
location = "Boston, MA"
modes = ["walk", "bike", "drive"]

for mode in modes:
    iso = create_isochrone(location, travel_time=15, travel_mode=mode)
    libraries = get_poi(location, categories=["education"], travel_time=15, limit=100)
    blocks = get_census_blocks(polygon=iso)

    geoids = [b['geoid'] for b in blocks]
    census = get_census_data(geoids, variables=["population"])

    total_pop = sum(
        census.data.get(g, {}).get("population", 0) or 0
        for g in geoids
    )

    print(f"\n{mode.capitalize()} (15 min):")
    print(f"  Area: {iso['properties']['area_sq_km']:.1f} km²")
    print(f"  Libraries: {len(libraries)}")
    print(f"  Population reached: {total_pop:,}")
```

## Next Steps

- **[Food Desert Case Study](07-food-desert-case-study.md)** - Apply these techniques to food access analysis
- Try analyzing different amenities (hospitals, schools, parks)
- Compare urban vs. suburban accessibility
- Add temporal analysis (how has access changed over time?)
