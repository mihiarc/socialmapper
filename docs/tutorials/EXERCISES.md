# SocialMapper Exercise Compilation

## Complete Exercise Collection from All Tutorials

This document contains all exercises from the SocialMapper tutorial series, organized for easy reference and practice. Each exercise includes difficulty level, estimated time, skills practiced, and solutions.

---

## 🎯 Exercise Quick Reference

| Exercise | Tutorial | Difficulty | Time | Primary Skill |
|----------|----------|------------|------|---------------|
| 1.1 Your Neighborhood | 01 | 🟢 | 10 min | Basic workflow |
| 1.2 POI Comparison | 01 | 🟢 | 15 min | POI analysis |
| 1.3 Demographics | 01 | 🟢 | 15 min | Census data |
| 2.1 Mode Coverage | 02 | 🟢 | 10 min | Travel modes |
| 2.2 Time Sensitivity | 02 | 🟡 | 15 min | Parameter testing |
| 2.3 Multi-Modal | 02 | 🟡 | 15 min | Comparison |
| 3.1 Variable Explorer | 03 | 🟢 | 10 min | Census variables |
| 3.2 Demographic Profile | 03 | 🟡 | 20 min | Data aggregation |
| 3.3 Equity Analysis | 03 | 🔴 | 30 min | Statistical analysis |
| 4.1 CSV Creation | 04 | 🟢 | 10 min | Data preparation |
| 4.2 Batch Analysis | 04 | 🟡 | 20 min | Automation |
| 4.3 Category Compare | 04 | 🟡 | 20 min | Grouping |
| 5.1 Workflow Design | 05 | 🟡 | 15 min | Planning |
| 5.2 Metric Creation | 05 | 🔴 | 25 min | Indicators |
| 5.3 Full Pipeline | 05 | 🔴 | 30 min | Integration |
| 6.1 Overlap Detection | 06 | 🟡 | 20 min | Spatial analysis |
| 6.2 Gap Finding | 06 | 🔴 | 25 min | Coverage |
| 6.3 Site Selection | 06 | 🔴 | 30 min | Optimization |
| 7.1 ZCTA Basics | 07 | 🟢 | 15 min | Geography |
| 7.2 Scale Comparison | 07 | 🟡 | 20 min | MAUP |
| 7.3 Regional Pattern | 07 | 🔴 | 30 min | Spatial statistics |
| 8.1 Address Prep | 08 | 🟢 | 10 min | Cleaning |
| 8.2 Geocoding Pipeline | 08 | 🟡 | 20 min | Automation |
| 8.3 Error Handling | 08 | 🔴 | 25 min | Robustness |

**Legend:** 🟢 Beginner | 🟡 Intermediate | 🔴 Advanced

---

## 📚 Tutorial 01: Getting Started Exercises

### Exercise 1.1: Your Neighborhood Analysis 🟢

**From:** Tutorial 01 - Getting Started
**Time:** 10 minutes
**Skills:** Basic workflow, coordinate finding, visualization

**Challenge:**
Create a 15-minute walking isochrone from your home or workplace. Find and count the grocery stores within reach. Create a simple map showing the results.

**Hints:**
- Use Google Maps to find coordinates
- travel_mode should be "walk"
- POI category for grocery is "supermarket"

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import create_isochrone, get_poi, create_map

# Your location (example: downtown Seattle)
my_location = (47.6062, -122.3321)

# Create walking isochrone
iso = create_isochrone(
    location=my_location,
    travel_time=15,
    travel_mode="walk"
)

# Find grocery stores
groceries = get_poi(
    polygon=iso,
    poi_type="supermarket"
)

print(f"Found {len(groceries)} grocery stores within 15-min walk")

# Create map
map_obj = create_map(
    polygon=iso,
    pois=groceries,
    poi_type="supermarket"
)
map_obj.save("my_neighborhood.html")
```
</details>

---

### Exercise 1.2: POI Type Comparison 🟢

**From:** Tutorial 01 - Getting Started
**Time:** 15 minutes
**Skills:** POI analysis, data comparison, basic statistics

**Challenge:**
Compare the number of different POI types (grocery, pharmacy, restaurant) within a 10-minute drive from a location. Which type is most prevalent? Calculate the ratio of restaurants to grocery stores.

**Hints:**
- Create one isochrone, search for multiple POI types
- Store results in a dictionary
- Use len() to count POIs

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import create_isochrone, get_poi

location = (35.7796, -78.6382)  # Raleigh, NC

# Create driving isochrone
iso = create_isochrone(
    location=location,
    travel_time=10,
    travel_mode="drive"
)

# Search for different POI types
poi_types = ["supermarket", "pharmacy", "restaurant"]
results = {}

for poi_type in poi_types:
    pois = get_poi(polygon=iso, poi_type=poi_type)
    results[poi_type] = len(pois)
    print(f"{poi_type}: {results[poi_type]} found")

# Analysis
most_common = max(results, key=results.get)
print(f"\nMost prevalent: {most_common} ({results[most_common]} locations)")

# Restaurant to grocery ratio
if results["supermarket"] > 0:
    ratio = results["restaurant"] / results["supermarket"]
    print(f"Restaurant:Grocery ratio: {ratio:.2f}:1")
```
</details>

---

### Exercise 1.3: Basic Demographics 🟢

**From:** Tutorial 01 - Getting Started
**Time:** 15 minutes
**Skills:** Census data retrieval, aggregation, interpretation

**Challenge:**
Get the total population and median household income for a 5-minute driving area. Calculate the average income weighted by population.

**Hints:**
- Use get_census_blocks() first
- Then get_census_data() with specific variables
- Weight income by block population

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data
)

location = (40.7128, -74.0060)  # New York City

# Create isochrone
iso = create_isochrone(
    location=location,
    travel_time=5,
    travel_mode="drive"
)

# Get census blocks
blocks = get_census_blocks(polygon=iso)[:20]  # Limit for speed

# Get demographic data
data = get_census_data(
    location=[b['geoid'] for b in blocks],
    variables=["population", "median_household_income"]
)

# Calculate totals
total_pop = sum(d['population'] for d in data.values())
print(f"Total population: {total_pop:,}")

# Calculate weighted average income
weighted_income = sum(
    d['population'] * d['median_household_income']
    for d in data.values()
    if d['median_household_income'] is not None
)
total_pop_with_income = sum(
    d['population']
    for d in data.values()
    if d['median_household_income'] is not None
)

if total_pop_with_income > 0:
    avg_income = weighted_income / total_pop_with_income
    print(f"Weighted average income: ${avg_income:,.0f}")
```
</details>

---

## 🚗 Tutorial 02: Travel Modes Exercises

### Exercise 2.1: Mode Coverage Comparison 🟢

**From:** Tutorial 02 - Travel Modes
**Time:** 10 minutes
**Skills:** Mode comparison, area calculation

**Challenge:**
Calculate the area covered by each travel mode (walk, bike, drive) for a 10-minute journey. What percentage of the driving area can be reached by walking?

**Hints:**
- Each isochrone has area_sq_km in properties
- Calculate percentage: (walk_area / drive_area) * 100

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import create_isochrone

location = (37.7749, -122.4194)  # San Francisco
modes = ["walk", "bike", "drive"]
areas = {}

for mode in modes:
    iso = create_isochrone(
        location=location,
        travel_time=10,
        travel_mode=mode
    )
    areas[mode] = iso['properties']['area_sq_km']
    print(f"{mode}: {areas[mode]:.2f} km²")

# Calculate percentages
walk_percent = (areas["walk"] / areas["drive"]) * 100
bike_percent = (areas["bike"] / areas["drive"]) * 100

print(f"\nWalking covers {walk_percent:.1f}% of driving area")
print(f"Biking covers {bike_percent:.1f}% of driving area")
```
</details>

---

### Exercise 2.2: Time Sensitivity Analysis 🟡

**From:** Tutorial 02 - Travel Modes
**Time:** 15 minutes
**Skills:** Parameter testing, data visualization, trend analysis

**Challenge:**
For walking mode, create isochrones for 5, 10, 15, 20, and 25 minutes. Plot how the area grows with time. Is the relationship linear?

**Hints:**
- Use a loop with range(5, 30, 5)
- Store results in lists
- Area doesn't grow linearly due to network constraints

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import create_isochrone
import matplotlib.pyplot as plt

location = (35.7796, -78.6382)  # Raleigh
times = range(5, 30, 5)
areas = []

for time in times:
    iso = create_isochrone(
        location=location,
        travel_time=time,
        travel_mode="walk"
    )
    area = iso['properties']['area_sq_km']
    areas.append(area)
    print(f"{time} min: {area:.2f} km²")

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(times, areas, 'bo-', linewidth=2, markersize=8)
plt.xlabel('Travel Time (minutes)')
plt.ylabel('Area (km²)')
plt.title('Walking Area vs. Time')
plt.grid(True, alpha=0.3)

# Add trend information
for i in range(1, len(areas)):
    growth_rate = (areas[i] - areas[i-1]) / areas[i-1] * 100
    print(f"{list(times)[i-1]} to {list(times)[i]} min: +{growth_rate:.1f}%")

plt.show()

# Check linearity
print("\nRelationship is non-linear - growth rate decreases with time")
print("This reflects real-world network constraints and barriers")
```
</details>

---

### Exercise 2.3: Multi-Modal Accessibility Score 🟡

**From:** Tutorial 02 - Travel Modes
**Time:** 15 minutes
**Skills:** Composite metrics, normalization, scoring

**Challenge:**
Create an accessibility score that combines all three modes. Weight walking at 40%, biking at 35%, and driving at 25% to emphasize sustainable transport. Apply to 3 different locations.

**Hints:**
- Normalize areas to 0-1 scale
- Apply weights and sum
- Compare locations

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import create_isochrone

# Define locations
locations = {
    "Downtown": (35.7796, -78.6382),
    "Suburb": (35.8974, -78.6382),
    "Rural": (36.0396, -78.8986)
}

# Weights favoring sustainable transport
weights = {"walk": 0.40, "bike": 0.35, "drive": 0.25}

def calculate_accessibility_score(location):
    areas = {}
    for mode in ["walk", "bike", "drive"]:
        iso = create_isochrone(
            location=location,
            travel_time=15,
            travel_mode=mode
        )
        areas[mode] = iso['properties']['area_sq_km']

    # Normalize to 0-1 scale (using drive as max)
    max_area = areas["drive"]
    normalized = {mode: area/max_area for mode, area in areas.items()}

    # Calculate weighted score
    score = sum(normalized[mode] * weights[mode] for mode in weights)

    return score, areas

# Compare locations
results = {}
for name, coords in locations.items():
    score, areas = calculate_accessibility_score(coords)
    results[name] = score
    print(f"\n{name}:")
    print(f"  Areas: Walk={areas['walk']:.1f}, Bike={areas['bike']:.1f}, Drive={areas['drive']:.1f} km²")
    print(f"  Accessibility Score: {score:.3f}")

# Rank locations
ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)
print("\nRanking by Sustainable Accessibility:")
for i, (name, score) in enumerate(ranked, 1):
    print(f"{i}. {name}: {score:.3f}")
```
</details>

---

## 📊 Tutorial 03: Census Demographics Exercises

### Exercise 3.1: Variable Explorer 🟢

**From:** Tutorial 03 - Census Demographics
**Time:** 10 minutes
**Skills:** Census variables, data exploration

**Challenge:**
Retrieve 5 different census variables for your area. Print them in a formatted table showing min, max, mean, and median values across block groups.

**Hints:**
- Use variables like "population", "median_age", "housing_units"
- Calculate statistics across all block groups
- Format output for readability

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data
)
import statistics

location = (33.4484, -112.0740)  # Phoenix

# Create isochrone
iso = create_isochrone(location, travel_time=10, travel_mode="drive")

# Get census blocks
blocks = get_census_blocks(polygon=iso)[:15]  # Limit for speed

# Get multiple variables
variables = [
    "population",
    "median_age",
    "median_household_income",
    "housing_units",
    "percent_poverty"
]

data = get_census_data(
    location=[b['geoid'] for b in blocks],
    variables=variables
)

# Calculate statistics for each variable
print(f"{'Variable':<25} {'Min':>10} {'Max':>10} {'Mean':>10} {'Median':>10}")
print("-" * 70)

for var in variables:
    values = [d[var] for d in data.values() if d[var] is not None]

    if values:
        min_val = min(values)
        max_val = max(values)
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)

        # Format based on variable type
        if "income" in var or "population" in var or "housing" in var:
            print(f"{var:<25} {min_val:>10,.0f} {max_val:>10,.0f} {mean_val:>10,.0f} {median_val:>10,.0f}")
        else:
            print(f"{var:<25} {min_val:>10.1f} {max_val:>10.1f} {mean_val:>10.1f} {median_val:>10.1f}")
```
</details>

---

### Exercise 3.2: Demographic Profile Builder 🟡

**From:** Tutorial 03 - Census Demographics
**Time:** 20 minutes
**Skills:** Data aggregation, profile creation, reporting

**Challenge:**
Create a comprehensive demographic profile comparing areas within 10-minute walk vs. 10-minute drive. Include population, age distribution, income, and housing characteristics. Format as a report.

**Hints:**
- Get data for both isochrones
- Calculate percentages and ratios
- Create formatted comparison

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data
)

def create_demographic_profile(location, travel_time, travel_mode):
    """Create demographic profile for an area."""

    # Create isochrone
    iso = create_isochrone(
        location=location,
        travel_time=travel_time,
        travel_mode=travel_mode
    )

    # Get census blocks
    blocks = get_census_blocks(polygon=iso)[:20]

    # Get comprehensive demographics
    variables = [
        "population",
        "median_age",
        "median_household_income",
        "housing_units",
        "percent_poverty",
        "percent_minority"
    ]

    data = get_census_data(
        location=[b['geoid'] for b in blocks],
        variables=variables
    )

    # Aggregate statistics
    profile = {
        "total_population": sum(d['population'] for d in data.values()),
        "total_housing": sum(d['housing_units'] for d in data.values() if d['housing_units']),
        "avg_age": sum(d['population'] * d['median_age'] for d in data.values() if d['median_age']) /
                   sum(d['population'] for d in data.values() if d['median_age']),
        "avg_income": sum(d['population'] * d['median_household_income'] for d in data.values() if d['median_household_income']) /
                      sum(d['population'] for d in data.values() if d['median_household_income']),
        "poverty_rate": sum(d['population'] * d['percent_poverty'] for d in data.values() if d['percent_poverty']) /
                        sum(d['population'] for d in data.values() if d['percent_poverty']),
        "area_sq_km": iso['properties']['area_sq_km']
    }

    profile["population_density"] = profile["total_population"] / profile["area_sq_km"]

    return profile

# Location (Austin, TX)
location = (30.2672, -97.7431)

# Create profiles
walk_profile = create_demographic_profile(location, 10, "walk")
drive_profile = create_demographic_profile(location, 10, "drive")

# Generate report
print("=" * 60)
print("DEMOGRAPHIC COMPARISON REPORT")
print("10-Minute Walk vs. Drive Access from Downtown Austin")
print("=" * 60)

print("\n📊 POPULATION & DENSITY")
print(f"{'Metric':<30} {'Walk':>12} {'Drive':>12} {'Ratio':>8}")
print("-" * 60)
print(f"{'Total Population':<30} {walk_profile['total_population']:>12,} {drive_profile['total_population']:>12,} {drive_profile['total_population']/walk_profile['total_population']:>8.1f}x")
print(f"{'Area (km²)':<30} {walk_profile['area_sq_km']:>12.1f} {drive_profile['area_sq_km']:>12.1f} {drive_profile['area_sq_km']/walk_profile['area_sq_km']:>8.1f}x")
print(f"{'Density (per km²)':<30} {walk_profile['population_density']:>12,.0f} {drive_profile['population_density']:>12,.0f} {walk_profile['population_density']/drive_profile['population_density']:>8.1f}x")

print("\n💰 ECONOMIC INDICATORS")
print(f"{'Median Income':<30} ${walk_profile['avg_income']:>11,.0f} ${drive_profile['avg_income']:>11,.0f}")
print(f"{'Poverty Rate':<30} {walk_profile['poverty_rate']:>11.1f}% {drive_profile['poverty_rate']:>11.1f}%")

print("\n🏘️ HOUSING")
print(f"{'Total Housing Units':<30} {walk_profile['total_housing']:>12,} {drive_profile['total_housing']:>12,}")
print(f"{'Average Household Size':<30} {walk_profile['total_population']/walk_profile['total_housing']:>12.1f} {drive_profile['total_population']/drive_profile['total_housing']:>12.1f}")

print("\n📈 KEY INSIGHTS")
print(f"• Walking area is {walk_profile['population_density']/drive_profile['population_density']:.1f}x more dense")
print(f"• Driving reaches {drive_profile['total_population']/walk_profile['total_population']:.1f}x more people")
print(f"• Income difference: ${abs(walk_profile['avg_income']-drive_profile['avg_income']):,.0f}")
```
</details>

---

### Exercise 3.3: Equity Analysis 🔴

**From:** Tutorial 03 - Census Demographics
**Time:** 30 minutes
**Skills:** Statistical analysis, equity metrics, visualization

**Challenge:**
Develop an equity index that measures disparate access to resources. Compare access to healthcare (hospitals/clinics) for high-income vs. low-income block groups. Calculate and visualize the disparity ratio.

**Hints:**
- Split block groups by median income
- Count POIs accessible to each group
- Calculate per-capita access rates

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    get_poi
)
import matplotlib.pyplot as plt
import numpy as np

def analyze_healthcare_equity(location, travel_time=15):
    """Analyze healthcare access equity by income."""

    # Create isochrone
    iso = create_isochrone(
        location=location,
        travel_time=travel_time,
        travel_mode="drive"
    )

    # Get census blocks and demographics
    blocks = get_census_blocks(polygon=iso)[:30]

    data = get_census_data(
        location=[b['geoid'] for b in blocks],
        variables=["population", "median_household_income"]
    )

    # Calculate income threshold (median)
    incomes = [d['median_household_income'] for d in data.values()
               if d['median_household_income'] is not None]
    income_threshold = np.median(incomes)

    # Split blocks by income
    low_income_blocks = []
    high_income_blocks = []

    for geoid, demo in data.items():
        if demo['median_household_income'] is None:
            continue

        block = next(b for b in blocks if b['geoid'] == geoid)

        if demo['median_household_income'] < income_threshold:
            low_income_blocks.append(block)
        else:
            high_income_blocks.append(block)

    # Analyze healthcare access for each group
    def get_healthcare_access(blocks_subset):
        total_pop = 0
        total_facilities = 0

        for block in blocks_subset:
            # Create small isochrone from block centroid
            centroid = block['centroid']
            iso_small = create_isochrone(
                location=(centroid['lat'], centroid['lon']),
                travel_time=10,
                travel_mode="drive"
            )

            # Find healthcare facilities
            hospitals = get_poi(polygon=iso_small, poi_type="hospital")
            clinics = get_poi(polygon=iso_small, poi_type="clinic")

            facilities = len(hospitals) + len(clinics)
            population = data[block['geoid']]['population']

            total_facilities += facilities
            total_pop += population

        # Calculate per-capita rate
        if total_pop > 0:
            return total_facilities / total_pop * 10000  # Per 10,000 people
        return 0

    # Calculate access rates
    low_income_rate = get_healthcare_access(low_income_blocks)
    high_income_rate = get_healthcare_access(high_income_blocks)

    # Calculate equity metrics
    disparity_ratio = high_income_rate / low_income_rate if low_income_rate > 0 else 0
    equity_gap = high_income_rate - low_income_rate

    # Visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart of access rates
    groups = ['Low Income\n(<${:,.0f})'.format(income_threshold),
              'High Income\n(>${:,.0f})'.format(income_threshold)]
    rates = [low_income_rate, high_income_rate]
    colors = ['#d73027', '#4575b4']

    bars = ax1.bar(groups, rates, color=colors, alpha=0.8)
    ax1.set_ylabel('Healthcare Facilities per 10,000 People')
    ax1.set_title('Healthcare Access by Income Group')
    ax1.grid(True, alpha=0.3)

    # Add value labels
    for bar, rate in zip(bars, rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{rate:.2f}', ha='center', fontweight='bold')

    # Equity metrics display
    metrics_text = f"""
    Equity Analysis Results

    Disparity Ratio: {disparity_ratio:.2f}x
    (High-income areas have {disparity_ratio:.2f}x better access)

    Absolute Gap: {equity_gap:.2f} facilities/10k

    Low Income Blocks: {len(low_income_blocks)}
    High Income Blocks: {len(high_income_blocks)}

    Equity Index: {1/disparity_ratio:.2f}
    (1.0 = perfect equity, <1.0 = inequity)
    """

    ax2.text(0.1, 0.5, metrics_text, transform=ax2.transAxes,
             fontsize=12, verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax2.axis('off')

    plt.suptitle(f'Healthcare Access Equity Analysis\n{travel_time}-minute drive radius',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

    return {
        'disparity_ratio': disparity_ratio,
        'low_income_rate': low_income_rate,
        'high_income_rate': high_income_rate,
        'equity_index': 1/disparity_ratio if disparity_ratio > 0 else 0
    }

# Run analysis
location = (39.7392, -104.9903)  # Denver
results = analyze_healthcare_equity(location)

print("\n🏥 HEALTHCARE EQUITY ANALYSIS COMPLETE")
print(f"Equity Index: {results['equity_index']:.2f}")
print("Interpretation: " +
      ("Equitable access" if results['equity_index'] > 0.8 else "Significant inequity detected"))
```
</details>

---

## 📍 Tutorial 04: Custom POIs Exercises

### Exercise 4.1: CSV Data Preparation 🟢

**From:** Tutorial 04 - Custom POIs
**Time:** 10 minutes
**Skills:** Data preparation, CSV formatting, validation

**Challenge:**
Create a CSV file with 5 local libraries including name, address, latitude, and longitude. Load and validate the data, checking for missing values and coordinate validity.

**Hints:**
- Use online tools to find coordinates
- Check latitude is -90 to 90, longitude -180 to 180
- Handle missing values gracefully

<details>
<summary>💡 Solution</summary>

```python
import csv
import pandas as pd

# Create sample library data
libraries_data = [
    ["name", "address", "latitude", "longitude", "branch_type"],
    ["Central Library", "123 Main St", 35.7796, -78.6382, "Main"],
    ["North Branch", "456 Oak Ave", 35.8127, -78.6435, "Branch"],
    ["South Branch", "789 Pine Rd", 35.7465, -78.6320, "Branch"],
    ["East Branch", "321 Elm St", 35.7799, -78.5950, "Branch"],
    ["West Branch", "654 Maple Dr", 35.7793, -78.6814, "Branch"]
]

# Save to CSV
csv_filename = "libraries.csv"
with open(csv_filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(libraries_data)

print(f"Created {csv_filename}")

# Load and validate
def validate_poi_data(filename):
    """Validate POI CSV data."""

    df = pd.read_csv(filename)
    print(f"\n📋 Data Summary:")
    print(f"Total POIs: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")

    # Check for missing values
    print(f"\n🔍 Missing Values:")
    print(df.isnull().sum())

    # Validate coordinates
    print(f"\n📍 Coordinate Validation:")
    invalid_coords = []

    for idx, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']

        # Check valid ranges
        if not (-90 <= lat <= 90):
            invalid_coords.append(f"Row {idx}: Invalid latitude {lat}")
        if not (-180 <= lon <= 180):
            invalid_coords.append(f"Row {idx}: Invalid longitude {lon}")

    if invalid_coords:
        print("❌ Invalid coordinates found:")
        for error in invalid_coords:
            print(f"  {error}")
    else:
        print("✅ All coordinates valid")

    # Show data preview
    print(f"\n📊 Data Preview:")
    print(df.head())

    return df

# Validate the data
df_libraries = validate_poi_data(csv_filename)

# Process POIs
from socialmapper import create_isochrone

for idx, row in df_libraries.iterrows():
    location = (row['latitude'], row['longitude'])
    iso = create_isochrone(location, travel_time=5, travel_mode="walk")
    area = iso['properties']['area_sq_km']
    print(f"{row['name']}: {area:.2f} km² walking coverage")
```
</details>

---

### Exercise 4.2: Batch POI Analysis 🟡

**From:** Tutorial 04 - Custom POIs
**Time:** 20 minutes
**Skills:** Batch processing, progress tracking, error handling

**Challenge:**
Process a list of 10 POIs, creating isochrones for each. Track processing time, handle errors gracefully, and create a summary report showing total population served by all locations combined.

**Hints:**
- Use try/except for error handling
- Track time with time.time()
- Union polygons for total coverage

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data
)
import time
import json

# Sample POI data (community centers)
pois = [
    {"name": "Downtown Center", "lat": 35.7796, "lon": -78.6382},
    {"name": "North Center", "lat": 35.8127, "lon": -78.6435},
    {"name": "South Center", "lat": 35.7465, "lon": -78.6320},
    {"name": "East Center", "lat": 35.7799, "lon": -78.5950},
    {"name": "West Center", "lat": 35.7793, "lon": -78.6814},
    {"name": "Northeast Center", "lat": 35.8458, "lon": -78.5953},
    {"name": "Northwest Center", "lat": 35.8455, "lon": -78.6817},
    {"name": "Southeast Center", "lat": 35.7134, "lon": -78.5956},
    {"name": "Southwest Center", "lat": 35.7131, "lon": -78.6811},
    {"name": "Central Center", "lat": 35.7796, "lon": -78.6150}
]

def process_poi_batch(poi_list, travel_time=10, travel_mode="drive"):
    """Process batch of POIs with error handling and reporting."""

    results = []
    errors = []
    start_time = time.time()

    print(f"🚀 Processing {len(poi_list)} POIs...")
    print("-" * 50)

    for i, poi in enumerate(poi_list, 1):
        poi_start = time.time()

        try:
            print(f"[{i}/{len(poi_list)}] Processing {poi['name']}...", end=" ")

            # Create isochrone
            location = (poi['lat'], poi['lon'])
            iso = create_isochrone(
                location=location,
                travel_time=travel_time,
                travel_mode=travel_mode
            )

            # Get population
            blocks = get_census_blocks(polygon=iso)[:10]  # Limit for speed

            if blocks:
                data = get_census_data(
                    location=[b['geoid'] for b in blocks],
                    variables=["population"]
                )
                total_pop = sum(d['population'] for d in data.values())
            else:
                total_pop = 0

            # Store results
            result = {
                'name': poi['name'],
                'location': location,
                'area_sq_km': iso['properties']['area_sq_km'],
                'population': total_pop,
                'processing_time': time.time() - poi_start,
                'polygon': iso
            }
            results.append(result)

            print(f"✅ {result['area_sq_km']:.1f} km², {total_pop:,} people ({result['processing_time']:.1f}s)")

        except Exception as e:
            error_info = {
                'name': poi['name'],
                'error': str(e),
                'processing_time': time.time() - poi_start
            }
            errors.append(error_info)
            print(f"❌ Error: {e} ({error_info['processing_time']:.1f}s)")

    # Generate summary report
    total_time = time.time() - start_time

    print("\n" + "=" * 50)
    print("📊 BATCH PROCESSING REPORT")
    print("=" * 50)

    print(f"\n⏱️  Performance:")
    print(f"  Total Time: {total_time:.1f} seconds")
    print(f"  Average Time: {total_time/len(poi_list):.1f} seconds per POI")
    print(f"  Success Rate: {len(results)}/{len(poi_list)} ({len(results)/len(poi_list)*100:.0f}%)")

    if results:
        total_area = sum(r['area_sq_km'] for r in results)
        total_population = sum(r['population'] for r in results)
        avg_area = total_area / len(results)
        avg_population = total_population / len(results)

        print(f"\n📈 Coverage Statistics:")
        print(f"  Total Area: {total_area:.1f} km²")
        print(f"  Average Area: {avg_area:.1f} km²")
        print(f"  Total Population: {total_population:,}")
        print(f"  Average Population: {avg_population:,.0f}")

        # Find best and worst locations
        best_pop = max(results, key=lambda x: x['population'])
        worst_pop = min(results, key=lambda x: x['population'])
        best_area = max(results, key=lambda x: x['area_sq_km'])

        print(f"\n🏆 Top Performers:")
        print(f"  Highest Population: {best_pop['name']} ({best_pop['population']:,})")
        print(f"  Largest Area: {best_area['name']} ({best_area['area_sq_km']:.1f} km²)")
        print(f"  Lowest Population: {worst_pop['name']} ({worst_pop['population']:,})")

    if errors:
        print(f"\n⚠️  Errors ({len(errors)}):")
        for error in errors:
            print(f"  {error['name']}: {error['error']}")

    # Save results to file
    output_file = "batch_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_pois': len(poi_list),
                'successful': len(results),
                'failed': len(errors),
                'total_time': total_time,
                'total_population': sum(r['population'] for r in results),
                'total_area': sum(r['area_sq_km'] for r in results)
            },
            'results': [
                {k: v for k, v in r.items() if k != 'polygon'}
                for r in results
            ],
            'errors': errors
        }, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")

    return results, errors

# Run batch analysis
results, errors = process_poi_batch(pois)
```
</details>

---

### Exercise 4.3: POI Category Comparison 🟡

**From:** Tutorial 04 - Custom POIs
**Time:** 20 minutes
**Skills:** Category analysis, grouping, comparative visualization

**Challenge:**
Create POI lists for three categories (e.g., schools, parks, health facilities). Compare the average area served and population reached by each category. Visualize the differences.

**Hints:**
- Group POIs by category
- Calculate averages per category
- Create comparison charts

<details>
<summary>💡 Solution</summary>

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    get_poi
)
import matplotlib.pyplot as plt
import numpy as np

# Define POI categories to analyze
poi_categories = {
    "Schools": ["school", "university"],
    "Parks": ["park", "playground"],
    "Healthcare": ["hospital", "clinic", "pharmacy"]
}

def analyze_poi_categories(center_location, search_radius=5000):
    """Analyze and compare different POI categories."""

    # Create search area
    search_iso = create_isochrone(
        location=center_location,
        travel_time=20,
        travel_mode="drive"
    )

    category_results = {}

    for category_name, poi_types in poi_categories.items():
        print(f"\n📍 Analyzing {category_name}...")

        all_pois = []
        # Collect POIs of all types in category
        for poi_type in poi_types:
            pois = get_poi(polygon=search_iso, poi_type=poi_type)
            all_pois.extend(pois)

        if not all_pois:
            print(f"  No {category_name} found")
            continue

        print(f"  Found {len(all_pois)} locations")

        # Analyze each POI (limit to first 5 for speed)
        areas = []
        populations = []

        for poi in all_pois[:5]:
            try:
                # Create 10-minute walk isochrone
                iso = create_isochrone(
                    location=(poi['lat'], poi['lon']),
                    travel_time=10,
                    travel_mode="walk"
                )

                # Get population
                blocks = get_census_blocks(polygon=iso)[:5]
                if blocks:
                    data = get_census_data(
                        location=[b['geoid'] for b in blocks],
                        variables=["population"]
                    )
                    pop = sum(d['population'] for d in data.values())
                else:
                    pop = 0

                areas.append(iso['properties']['area_sq_km'])
                populations.append(pop)

            except Exception as e:
                print(f"  Error processing POI: {e}")
                continue

        if areas:
            category_results[category_name] = {
                'count': len(all_pois),
                'analyzed': len(areas),
                'avg_area': np.mean(areas),
                'std_area': np.std(areas),
                'avg_population': np.mean(populations),
                'std_population': np.std(populations),
                'total_area': sum(areas),
                'total_population': sum(populations)
            }

    # Visualize results
    if category_results:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        categories = list(category_results.keys())
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        # 1. Average area per POI
        avg_areas = [category_results[c]['avg_area'] for c in categories]
        std_areas = [category_results[c]['std_area'] for c in categories]

        bars1 = ax1.bar(categories, avg_areas, yerr=std_areas,
                       capsize=5, color=colors, alpha=0.7)
        ax1.set_ylabel('Area (km²)')
        ax1.set_title('Average Walking Coverage per POI')
        ax1.grid(True, alpha=0.3)

        # Add value labels
        for bar, val in zip(bars1, avg_areas):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.2f}', ha='center', va='bottom')

        # 2. Average population per POI
        avg_pops = [category_results[c]['avg_population'] for c in categories]
        std_pops = [category_results[c]['std_population'] for c in categories]

        bars2 = ax2.bar(categories, avg_pops, yerr=std_pops,
                       capsize=5, color=colors, alpha=0.7)
        ax2.set_ylabel('Population')
        ax2.set_title('Average Population Served per POI')
        ax2.grid(True, alpha=0.3)

        for bar, val in zip(bars2, avg_pops):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:,.0f}', ha='center', va='bottom')

        # 3. POI counts
        counts = [category_results[c]['count'] for c in categories]

        bars3 = ax3.bar(categories, counts, color=colors, alpha=0.7)
        ax3.set_ylabel('Number of POIs')
        ax3.set_title('POI Density by Category')
        ax3.grid(True, alpha=0.3)

        for bar, val in zip(bars3, counts):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val}', ha='center', va='bottom')

        # 4. Efficiency metric (population per km²)
        efficiency = [category_results[c]['avg_population'] / category_results[c]['avg_area']
                     for c in categories]

        bars4 = ax4.bar(categories, efficiency, color=colors, alpha=0.7)
        ax4.set_ylabel('People per km²')
        ax4.set_title('Service Efficiency (Population Density)')
        ax4.grid(True, alpha=0.3)

        for bar, val in zip(bars4, efficiency):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:,.0f}', ha='center', va='bottom')

        plt.suptitle('POI Category Comparison Analysis\n10-minute walking access',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()

        # Print summary report
        print("\n" + "=" * 60)
        print("POI CATEGORY COMPARISON SUMMARY")
        print("=" * 60)

        for category, stats in category_results.items():
            print(f"\n{category}:")
            print(f"  Total POIs found: {stats['count']}")
            print(f"  POIs analyzed: {stats['analyzed']}")
            print(f"  Avg area per POI: {stats['avg_area']:.2f} km²")
            print(f"  Avg population per POI: {stats['avg_population']:,.0f}")
            print(f"  Service efficiency: {stats['avg_population']/stats['avg_area']:,.0f} people/km²")

        # Identify best category for each metric
        best_coverage = max(categories, key=lambda c: category_results[c]['avg_area'])
        best_population = max(categories, key=lambda c: category_results[c]['avg_population'])
        best_efficiency = max(categories,
                            key=lambda c: category_results[c]['avg_population']/category_results[c]['avg_area'])
        most_numerous = max(categories, key=lambda c: category_results[c]['count'])

        print("\n🏆 Category Leaders:")
        print(f"  Most numerous: {most_numerous} ({category_results[most_numerous]['count']} POIs)")
        print(f"  Best coverage: {best_coverage} ({category_results[best_coverage]['avg_area']:.2f} km²/POI)")
        print(f"  Most people served: {best_population} ({category_results[best_population]['avg_population']:,.0f}/POI)")
        print(f"  Most efficient: {best_efficiency}")

    return category_results

# Run analysis for Raleigh, NC
location = (35.7796, -78.6382)
results = analyze_poi_categories(location)
```
</details>

---

## 🔧 Additional Exercises (Tutorials 5-8)

### Exercise 5.1: Workflow Design 🟡
**From:** Tutorial 05
**Time:** 15 minutes
**Challenge:** Design a workflow that finds the best location for a new community center by evaluating 5 candidate sites based on population served, existing facility gaps, and demographic need.

### Exercise 5.2: Custom Metric Creation 🔴
**From:** Tutorial 05
**Time:** 25 minutes
**Challenge:** Create an "Accessibility Index" that combines distance to essential services (grocery, pharmacy, healthcare) with demographic vulnerability (age, income, car ownership).

### Exercise 6.1: Service Overlap Detection 🟡
**From:** Tutorial 06
**Time:** 20 minutes
**Challenge:** Identify areas served by multiple libraries within 15-minute walk. Calculate the percentage of population with access to 0, 1, 2, or 3+ libraries.

### Exercise 6.2: Coverage Gap Analysis 🔴
**From:** Tutorial 06
**Time:** 25 minutes
**Challenge:** Find "transit deserts" - populated areas more than 15 minutes walk from any bus stop. Prioritize gaps by population density and demographic need.

### Exercise 7.1: ZCTA Regional Analysis 🟢
**From:** Tutorial 07
**Time:** 15 minutes
**Challenge:** Compare demographics between 3 adjacent ZIP codes. Which has the highest population density? The highest median income?

### Exercise 8.1: Batch Geocoding Pipeline 🟡
**From:** Tutorial 08
**Time:** 20 minutes
**Challenge:** Build a robust geocoding pipeline that processes a list of addresses, handles failures with fallback geocoders, and reports success rates.

---

## 📈 Progress Tracking

### Skill Development Checklist

#### Foundation Skills
- [ ] Create basic isochrone
- [ ] Search for POIs
- [ ] Retrieve census data
- [ ] Create simple maps
- [ ] Compare travel modes

#### Intermediate Skills
- [ ] Import custom data
- [ ] Batch process locations
- [ ] Calculate demographics
- [ ] Build workflows
- [ ] Handle errors gracefully

#### Advanced Skills
- [ ] Develop equity metrics
- [ ] Statistical analysis
- [ ] Optimize performance
- [ ] Create visualizations
- [ ] Build production pipelines

### Recommended Practice Schedule

**Week 1:** Complete exercises 1.1-2.3 (Basics)
**Week 2:** Complete exercises 3.1-4.3 (Data)
**Week 3:** Complete exercises 5.1-6.3 (Integration)
**Week 4:** Complete exercises 7.1-8.3 (Advanced)

---

## 🎯 Challenge Projects

### Beginner Challenge: Neighborhood Audit
Create a comprehensive accessibility report for your neighborhood including:
- Walking access to essential services
- Demographic profile
- Service gaps identification
- Improvement recommendations

### Intermediate Challenge: Equity Dashboard
Build an interactive dashboard showing:
- Transit equity scores by area
- Healthcare accessibility gaps
- Food desert identification
- Demographic overlays

### Advanced Challenge: Site Optimization
Develop an algorithm that:
- Evaluates 20+ potential sites
- Optimizes for multiple objectives
- Accounts for existing facilities
- Produces implementation plan

---

*Keep practicing! Each exercise builds critical skills for real-world accessibility analysis.* 🚀✨