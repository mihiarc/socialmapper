# Quick Start Guide

Get up and running with SocialMapper in minutes! This guide will walk you through your first analysis.

## Prerequisites

- Python 3.11 or higher installed
- Internet connection for downloading data
- (Optional) Census API key for enhanced data

## Installation

```bash
pip install socialmapper
```

## Your First Analysis

Let's analyze library accessibility in a community:

### 1. Basic Command Line Usage

```bash
socialmapper analyze --state "North Carolina" --county "Wake County" \
  --place-type "library" --travel-time 15
```

### 2. Python Script

Create a file `my_first_analysis.py`:

```python
from socialmapper import run_socialmapper

# Analyze library accessibility
results = run_socialmapper(
    state="North Carolina",
    county="Wake County",
    place_type="library",
    travel_time=15,
    census_variables=["total_population", "median_household_income"],
    export_csv=True
)

# Display results
print(f"Found {len(results['poi_data'])} libraries")
print(f"Analyzed {len(results['census_data'])} census block groups")
```

Run it:
```bash
python my_first_analysis.py
```

## Understanding the Results

After running the analysis, you'll get:

1. **POI Data** - Information about each library found
2. **Census Data** - Demographics of areas within travel time
3. **CSV Files** - Detailed data exported to `output/csv/`
4. **Maps** (optional) - Visualizations in `output/maps/`

## Next Steps

### Try Different POI Types

```python
# Schools
results = run_socialmapper(
    state="California",
    county="Los Angeles County",
    place_type="school",
    travel_time=10
)

# Healthcare facilities
results = run_socialmapper(
    state="Texas",
    county="Harris County",
    place_type="hospital",
    travel_time=20
)
```

### Use Custom Locations

Create a CSV file `my_locations.csv`:
```csv
name,latitude,longitude
Community Center,35.7796,-78.6382
City Park,35.7821,-78.6589
```

Then analyze:
```python
results = run_socialmapper(
    custom_coords_path="my_locations.csv",
    travel_time=15,
    census_variables=["total_population"]
)
```

### Add More Census Variables

```python
# Detailed demographic analysis
census_vars = [
    "total_population",
    "median_age",
    "median_household_income",
    "percent_poverty",
    "percent_without_vehicle"
]

results = run_socialmapper(
    state="New York",
    county="New York County",
    place_type="park",
    travel_time=10,
    census_variables=census_vars
)
```

## Common Patterns

### Batch Analysis
```python
# Analyze multiple POI types
poi_types = ['library', 'school', 'hospital', 'park']

for poi_type in poi_types:
    print(f"\nAnalyzing {poi_type}s...")
    results = run_socialmapper(
        state="Washington",
        county="King County",
        place_type=poi_type,
        travel_time=15
    )
    print(f"Found {len(results['poi_data'])} {poi_type}s")
```

### Different Travel Times
```python
# Compare accessibility at different time intervals
for minutes in [5, 10, 15, 20, 30]:
    results = run_socialmapper(
        state="Colorado",
        county="Denver County",
        place_type="grocery_store",
        travel_time=minutes
    )
    total_pop = sum(r['total_population'] for r in results['census_data'])
    print(f"{minutes} minutes: {total_pop:,} people")
```

## Troubleshooting

### No Results Found?
- Check spelling of state/county names
- Try a different POI type
- Ensure internet connection is active

### Slow Performance?
- First runs build caches (normal)
- Reduce number of census variables
- Use smaller geographic areas

### Memory Issues?
- Process one county at a time
- Limit census variables
- Close other applications

## Learn More

- **[Examples Directory](https://github.com/mihiarc/socialmapper/tree/main/examples)** - Complete working examples
- **[API Reference](../api-reference.md)** - Detailed function reference
- **[Command Line Guide](../user-guide/cli-usage.md)** - All CLI options
- **[User Guide](../user-guide/index.md)** - Understanding the features

Ready for more? Check out our [tutorials](https://github.com/mihiarc/socialmapper/tree/main/examples/tutorials) for step-by-step guides!