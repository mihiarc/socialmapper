# Using Custom Locations

SocialMapper lets you analyze accessibility from your own locations beyond what's available in OpenStreetMap. This is useful for analyzing your organization's facilities, specific addresses, or any custom points of interest.

## CSV File Format

Create a CSV file with your locations. The basic format requires:
- `name` - Location name  
- `latitude` - Decimal latitude
- `longitude` - Decimal longitude

### Example CSV

```csv
name,latitude,longitude
Main Office,35.7796,-78.6382
Branch Office,35.8934,-78.8637
Community Center,35.7321,-78.5512
```

## Basic Usage

### Python API

```python
from socialmapper import run_socialmapper

# Analyze custom locations
results = run_socialmapper(
    custom_coords_path="my_locations.csv",
    travel_time=15,
    census_variables=["total_population", "median_household_income"]
)
```

### Command Line

```bash
socialmapper --custom-coords my_locations.csv --travel-time 15
```

## Working with Results

The results dictionary includes:
- `poi_data` - Your input locations with added geographic context
- `census_data` - Demographics for areas within travel time
- Output files in the `output/` directory

```python
# Check results
print(f"Analyzed {len(results['poi_data'])} locations")
print(f"Found {len(results['census_data'])} census block groups")
```

## Travel Time Options

Adjust the travel time to change the analysis area:

```python
# 5-minute walk
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=5
)

# 20-minute drive 
results = run_socialmapper(
    custom_coords_path="locations.csv", 
    travel_time=20
)
```

## Census Variables

Add more demographic variables to your analysis:

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=15,
    census_variables=[
        "total_population",
        "median_household_income",
        "median_age",
        "percent_poverty"
    ]
)
```

See [demographic variables](demographics.md) for the full list.

## Export Options

### Save Results as CSV

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=15,
    export_csv=True  # Default
)
# Results saved to output/csv/
```

### Generate Maps

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=15,
    export_maps=True
)
# Maps saved to output/maps/
```

## Tips and Best Practices

### Data Preparation
1. **Verify coordinates** - Ensure latitude/longitude are correct
2. **Use decimal degrees** - e.g., 35.7796, -78.6382
3. **Check coordinate order** - Latitude first, then longitude
4. **Name locations clearly** - Use descriptive names

### Performance
1. **Start small** - Test with a few locations first
2. **Use appropriate travel times** - Larger areas take longer
3. **Limit census variables** - Only request what you need

### Common Issues

**"File not found"**
- Check the file path
- Use absolute paths if needed

**"Invalid coordinates"**
- Verify latitude is between -90 and 90
- Verify longitude is between -180 and 180
- Check for swapped coordinates

**"No census data"**
- Ensure locations are in the United States
- Check coordinate accuracy

## Batch Analysis

To analyze multiple locations at once, simply include all locations in your CSV file:

```csv
name,latitude,longitude
Store 1,35.7796,-78.6382
Store 2,35.8934,-78.8637
Store 3,35.7321,-78.5512
Store 4,35.9102,-78.7234
```

SocialMapper will analyze all locations in a single run:

```python
# Analyze all locations at once
results = run_socialmapper(
    custom_coords_path="all_stores.csv",
    travel_time=15
)

print(f"Analyzed {len(results['poi_data'])} locations")
```

For separate analysis of each location:

```python
import pandas as pd

# Load locations
locations = pd.read_csv("stores.csv")

# Analyze each separately
for _, location in locations.iterrows():
    # Create single-location CSV or use data directly
    result = run_socialmapper(
        custom_coords_path=create_temp_csv(location),
        travel_time=15
    )
    print(f"{location['name']}: {sum(r['total_population'] for r in result['census_data']):,} people")
```

## Example Use Cases

### Facility Analysis
Analyze accessibility to your organization's locations:

```python
# Load facility locations
results = run_socialmapper(
    custom_coords_path="our_facilities.csv",
    travel_time=15,
    census_variables=["total_population", "median_income"]
)

# Review population reach
total_pop = sum(row.get("total_population", 0) for row in results["census_data"])
print(f"Total population within 15 minutes: {total_pop:,}")
```

### Site Comparison
Compare potential new locations:

```python
# Analyze each candidate site
for site_file in ["site_a.csv", "site_b.csv", "site_c.csv"]:
    results = run_socialmapper(
        custom_coords_path=site_file,
        travel_time=10,
        census_variables=["total_population"]
    )
    print(f"{site_file}: Population reach = {sum(r['total_population'] for r in results['census_data']):,}")
```

## Next Steps

- Learn about [travel time analysis](travel-time.md)
- Add more [demographic variables](demographics.md)
- [Export your results](exporting-results.md) in different formats