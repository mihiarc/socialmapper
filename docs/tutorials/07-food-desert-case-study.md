# Case Study: Food Desert Analysis

This advanced tutorial applies SocialMapper to a real-world equity research problem: identifying food deserts and understanding who is affected.

## Background

A **food desert** is an area with limited access to affordable and nutritious food. The USDA defines food deserts using specific criteria:

- **Urban areas:** More than 1 mile to the nearest supermarket
- **Rural areas:** More than 10 miles to the nearest supermarket

This case study uses SocialMapper to:
1. Identify areas without walkable grocery access
2. Analyze the demographics of affected populations
3. Create visualizations highlighting at-risk communities

## Setup

```python
import json
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data,
    create_map
)
```

## Part 1: Map Grocery Store Coverage

### Step 1.1: Find All Grocery Stores

```python
# Study area: Detroit, MI (known for food access challenges)
study_location = "Detroit, MI"

# Find all grocery stores and supermarkets
grocery_stores = get_poi(
    location=study_location,
    categories=["shopping"],
    limit=200  # Get more to ensure coverage
)

print(f"Grocery stores in {study_location}: {len(grocery_stores)}")

# Show distribution
for store in grocery_stores[:10]:
    print(f"  {store['name']}: {store['distance_km']:.2f} km from center")
```

### Step 1.2: Create Walking Coverage Zones

For each grocery store, create a 15-minute walking isochrone (approximately 1 mile):

```python
# Create walking isochrones for each grocery store
coverage_polygons = []

print(f"\nCreating coverage zones for {len(grocery_stores)} stores...")

for i, store in enumerate(grocery_stores):
    try:
        iso = create_isochrone(
            location=(store['lat'], store['lon']),
            travel_time=15,  # 15-minute walk
            travel_mode="walk",
            backend="valhalla"  # Fast API
        )

        polygon = shape(iso['geometry'])
        coverage_polygons.append({
            'store': store['name'],
            'polygon': polygon,
            'area_km2': iso['properties']['area_sq_km']
        })

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(grocery_stores)} stores")

    except Exception as e:
        print(f"  Skipped {store['name']}: {e}")

print(f"\nGenerated {len(coverage_polygons)} coverage zones")
```

### Step 1.3: Merge Coverage Areas

```python
# Combine all coverage polygons into a single "served" area
served_polygons = [cp['polygon'] for cp in coverage_polygons]
served_area = unary_union(served_polygons)

total_served_area = served_area.area * 111 * 111  # Rough conversion to km²
print(f"Total area with grocery access: {total_served_area:.1f} km²")
```

## Part 2: Identify Underserved Areas

### Step 2.1: Get Study Area Boundary

```python
# Create a large isochrone to define our study area
# (30-minute drive from city center encompasses most of the city)
study_boundary = create_isochrone(
    location=study_location,
    travel_time=30,
    travel_mode="drive"
)

study_polygon = shape(study_boundary['geometry'])
study_area_km2 = study_boundary['properties']['area_sq_km']

print(f"Total study area: {study_area_km2:.1f} km²")
```

### Step 2.2: Identify Food Desert Areas

```python
# Food desert = study area - served area
food_desert_area = study_polygon.difference(served_area)

desert_area_km2 = food_desert_area.area * 111 * 111
coverage_percent = (1 - desert_area_km2 / study_area_km2) * 100

print(f"\nFood Access Analysis:")
print(f"  Study area: {study_area_km2:.1f} km²")
print(f"  Served area: {study_area_km2 - desert_area_km2:.1f} km²")
print(f"  Desert area: {desert_area_km2:.1f} km²")
print(f"  Coverage: {coverage_percent:.1f}%")
```

## Part 3: Demographic Analysis

### Step 3.1: Get Census Blocks

```python
# Get census blocks for the entire study area
all_blocks = get_census_blocks(polygon=study_boundary)

print(f"\nTotal census block groups: {len(all_blocks)}")
```

### Step 3.2: Classify Blocks by Access

```python
# Classify each block as "served" or "underserved"
served_blocks = []
underserved_blocks = []

for block in all_blocks:
    block_polygon = shape(block['geometry'])
    block_center = block_polygon.centroid

    # Check if block centroid is within served area
    if served_area.contains(block_center):
        block['access_status'] = 'served'
        served_blocks.append(block)
    else:
        block['access_status'] = 'underserved'
        underserved_blocks.append(block)

print(f"Block groups with access: {len(served_blocks)}")
print(f"Block groups without access: {len(underserved_blocks)}")
```

### Step 3.3: Get Demographics for Both Groups

```python
# Get demographics for served areas
served_geoids = [b['geoid'] for b in served_blocks]
served_census = get_census_data(
    location=served_geoids,
    variables=["population", "median_income"]
)

# Get demographics for underserved areas
underserved_geoids = [b['geoid'] for b in underserved_blocks]
underserved_census = get_census_data(
    location=underserved_geoids,
    variables=["population", "median_income"]
)

# Add data to blocks
for block in served_blocks:
    data = served_census.data.get(block['geoid'], {})
    block['population'] = data.get('population', 0) or 0
    block['median_income'] = data.get('median_income', 0) or 0

for block in underserved_blocks:
    data = underserved_census.data.get(block['geoid'], {})
    block['population'] = data.get('population', 0) or 0
    block['median_income'] = data.get('median_income', 0) or 0
```

### Step 3.4: Compare Demographics

```python
# Calculate statistics for served areas
served_pop = sum(b['population'] for b in served_blocks)
served_incomes = [b['median_income'] for b in served_blocks if b['median_income'] > 0]

# Calculate statistics for underserved areas
underserved_pop = sum(b['population'] for b in underserved_blocks)
underserved_incomes = [b['median_income'] for b in underserved_blocks if b['median_income'] > 0]

print("\n" + "="*60)
print("DEMOGRAPHIC COMPARISON")
print("="*60)

print("\nPopulation:")
print(f"  With grocery access: {served_pop:,}")
print(f"  Without grocery access: {underserved_pop:,}")
print(f"  Percent underserved: {underserved_pop/(served_pop+underserved_pop)*100:.1f}%")

if served_incomes and underserved_incomes:
    print("\nMedian Household Income:")
    print(f"  Served areas: ${sum(served_incomes)/len(served_incomes):,.0f}")
    print(f"  Underserved areas: ${sum(underserved_incomes)/len(underserved_incomes):,.0f}")

    income_gap = sum(served_incomes)/len(served_incomes) - sum(underserved_incomes)/len(underserved_incomes)
    print(f"  Income gap: ${income_gap:,.0f}")
```

## Part 4: Visualizations

### Map 1: Food Access Status

```python
# Combine all blocks for mapping
all_blocks_for_map = served_blocks + underserved_blocks

# Create numeric access status for coloring
for block in all_blocks_for_map:
    block['access_score'] = 1 if block['access_status'] == 'served' else 0

# Create access map
access_map = create_map(
    data=all_blocks_for_map,
    column="access_score",
    title="Food Access: Grocery Within 15-min Walk",
    save_path="detroit_food_access.png"
)

print(f"\nFood access map saved: {access_map.file_path}")
```

### Map 2: Population in Food Deserts

```python
# Map population in underserved areas
underserved_with_pop = [b for b in underserved_blocks if b['population'] > 0]

if underserved_with_pop:
    pop_map = create_map(
        data=underserved_with_pop,
        column="population",
        title="Population in Food Desert Areas",
        save_path="detroit_food_desert_population.png"
    )
    print(f"Population map saved: {pop_map.file_path}")
```

### Map 3: Income in Food Deserts

```python
# Map income in underserved areas
underserved_with_income = [b for b in underserved_blocks if b['median_income'] > 0]

if underserved_with_income:
    income_map = create_map(
        data=underserved_with_income,
        column="median_income",
        title="Median Income in Food Desert Areas",
        save_path="detroit_food_desert_income.png"
    )
    print(f"Income map saved: {income_map.file_path}")
```

## Part 5: Export Results

### Generate Summary Report

```python
report = {
    "study": "Food Desert Analysis",
    "location": study_location,
    "methodology": {
        "access_definition": "15-minute walk to grocery store",
        "grocery_categories": ["grocery", "supermarket"]
    },
    "findings": {
        "total_grocery_stores": len(grocery_stores),
        "study_area_km2": round(study_area_km2, 1),
        "served_area_km2": round(study_area_km2 - desert_area_km2, 1),
        "desert_area_km2": round(desert_area_km2, 1),
        "coverage_percent": round(coverage_percent, 1)
    },
    "demographics": {
        "served_population": served_pop,
        "underserved_population": underserved_pop,
        "percent_underserved": round(underserved_pop/(served_pop+underserved_pop)*100, 1),
        "avg_income_served": round(sum(served_incomes)/len(served_incomes)) if served_incomes else None,
        "avg_income_underserved": round(sum(underserved_incomes)/len(underserved_incomes)) if underserved_incomes else None
    }
}

with open("food_desert_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"\nReport saved: food_desert_report.json")
```

### Export GeoJSON for Web Mapping

```python
# Export underserved areas as GeoJSON
geojson_result = create_map(
    data=underserved_blocks,
    column="population",
    export_format="geojson"
)

with open("food_desert_areas.geojson", "w") as f:
    json.dump(geojson_result.geojson_data, f)

print(f"GeoJSON saved: food_desert_areas.geojson")
```

## Complete Analysis Script

```python
#!/usr/bin/env python3
"""
Food Desert Analysis - Complete Case Study

This script identifies food deserts and analyzes affected demographics.
"""

import json
from shapely.geometry import shape
from shapely.ops import unary_union
from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data,
    create_map
)


def analyze_food_access(location: str, walk_time: int = 15) -> dict:
    """
    Comprehensive food desert analysis for a location.

    Parameters
    ----------
    location : str
        City name (e.g., "Detroit, MI")
    walk_time : int
        Walking time to grocery store (minutes)

    Returns
    -------
    dict
        Complete analysis results
    """
    print(f"\n{'='*60}")
    print(f"FOOD DESERT ANALYSIS: {location}")
    print(f"{'='*60}")

    # Step 1: Find grocery stores
    print("\n[1/7] Finding grocery stores...")
    groceries = get_poi(
        location=location,
        categories=["shopping"],
        limit=200
    )
    print(f"      Found {len(groceries)} stores")

    # Step 2: Create coverage zones
    print("\n[2/7] Generating coverage zones...")
    coverage = []
    for i, store in enumerate(groceries):
        try:
            iso = create_isochrone(
                location=(store['lat'], store['lon']),
                travel_time=walk_time,
                travel_mode="walk"
            )
            coverage.append(shape(iso['geometry']))
        except Exception:
            pass

        if (i + 1) % 20 == 0:
            print(f"      Processed {i+1}/{len(groceries)}")

    print(f"      Generated {len(coverage)} coverage zones")

    # Step 3: Merge coverage
    print("\n[3/7] Merging coverage areas...")
    served_area = unary_union(coverage) if coverage else None

    # Step 4: Define study boundary
    print("\n[4/7] Defining study area...")
    boundary = create_isochrone(location, travel_time=30, travel_mode="drive")
    study_polygon = shape(boundary['geometry'])

    # Step 5: Get census blocks
    print("\n[5/7] Getting census blocks...")
    blocks = get_census_blocks(polygon=boundary)
    print(f"      Found {len(blocks)} block groups")

    # Step 6: Classify and get demographics
    print("\n[6/7] Analyzing demographics...")
    served_blocks = []
    underserved_blocks = []

    for block in blocks:
        block_center = shape(block['geometry']).centroid
        if served_area and served_area.contains(block_center):
            block['status'] = 'served'
            served_blocks.append(block)
        else:
            block['status'] = 'underserved'
            underserved_blocks.append(block)

    # Get demographics
    all_geoids = [b['geoid'] for b in blocks]
    census = get_census_data(all_geoids, variables=["population", "median_income"])

    for block in blocks:
        data = census.data.get(block['geoid'], {})
        block['population'] = data.get('population', 0) or 0
        block['median_income'] = data.get('median_income', 0) or 0

    # Step 7: Calculate statistics
    print("\n[7/7] Calculating statistics...")
    served_pop = sum(b['population'] for b in served_blocks)
    underserved_pop = sum(b['population'] for b in underserved_blocks)
    total_pop = served_pop + underserved_pop

    served_incomes = [b['median_income'] for b in served_blocks if b['median_income'] > 0]
    underserved_incomes = [b['median_income'] for b in underserved_blocks if b['median_income'] > 0]

    # Print results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"\nGrocery Stores: {len(groceries)}")
    print(f"Coverage Zones: {len(coverage)}")
    print(f"\nPopulation Analysis:")
    print(f"  Total: {total_pop:,}")
    print(f"  With access: {served_pop:,} ({served_pop/total_pop*100:.1f}%)")
    print(f"  Without access: {underserved_pop:,} ({underserved_pop/total_pop*100:.1f}%)")

    if served_incomes and underserved_incomes:
        print(f"\nIncome Comparison:")
        print(f"  Served areas: ${sum(served_incomes)/len(served_incomes):,.0f}")
        print(f"  Underserved: ${sum(underserved_incomes)/len(underserved_incomes):,.0f}")

    # Create visualizations
    print("\nCreating maps...")
    for block in blocks:
        block['access_score'] = 1 if block['status'] == 'served' else 0

    valid_blocks = [b for b in blocks if b['population'] > 0]
    if valid_blocks:
        access_map = create_map(
            data=valid_blocks,
            column="access_score",
            title=f"Food Access - {location}",
            save_path=f"{location.replace(', ', '_').lower()}_food_access.png"
        )
        print(f"  Saved: {access_map.file_path}")

    return {
        "location": location,
        "stores": len(groceries),
        "total_population": total_pop,
        "served_population": served_pop,
        "underserved_population": underserved_pop,
        "percent_underserved": round(underserved_pop/total_pop*100, 1) if total_pop else 0,
        "blocks": blocks
    }


if __name__ == "__main__":
    # Analyze Detroit
    results = analyze_food_access("Detroit, MI")

    # Save results
    summary = {k: v for k, v in results.items() if k != 'blocks'}
    with open("food_desert_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nAnalysis complete!")
```

## Extending the Analysis

### Compare Multiple Cities

```python
cities = ["Detroit, MI", "Atlanta, GA", "Chicago, IL"]

comparisons = []
for city in cities:
    result = analyze_food_access(city)
    comparisons.append({
        "city": city,
        "underserved_percent": result["percent_underserved"],
        "underserved_pop": result["underserved_population"]
    })

# Rank by food desert severity
comparisons.sort(key=lambda x: x["underserved_percent"], reverse=True)

print("\nFood Desert Severity Ranking:")
for i, c in enumerate(comparisons, 1):
    print(f"{i}. {c['city']}: {c['underserved_percent']}% underserved ({c['underserved_pop']:,} people)")
```

### Analyze by Income Level

```python
# Identify low-income food deserts (double burden)
low_income_deserts = [
    b for b in underserved_blocks
    if b['median_income'] > 0 and b['median_income'] < 35000
]

pop_in_low_income_deserts = sum(b['population'] for b in low_income_deserts)
print(f"\nLow-income food deserts:")
print(f"  Block groups: {len(low_income_deserts)}")
print(f"  Population affected: {pop_in_low_income_deserts:,}")
```

## Conclusion

This case study demonstrated how SocialMapper can be used for equity research:

1. **Spatial Analysis** - Identified areas with and without grocery access
2. **Demographic Integration** - Connected geography to population data
3. **Equity Insights** - Revealed who is most affected by food deserts
4. **Visualization** - Created maps to communicate findings

The same methodology can be applied to analyze access to:
- Healthcare facilities
- Public transportation
- Schools and childcare
- Parks and recreation
- Banking services

## Next Steps

- Apply this analysis to your city
- Combine with income and demographic filters
- Create interactive web maps with the GeoJSON exports
- Develop policy recommendations based on findings
