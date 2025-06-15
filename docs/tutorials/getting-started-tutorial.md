# Getting Started Tutorial

This tutorial introduces the fundamental concepts of SocialMapper through a practical example analyzing library accessibility in Wake County, North Carolina.

## What You'll Learn

- How to search for Points of Interest (POIs) from OpenStreetMap
- How to generate travel time isochrones
- How to analyze census demographics within reachable areas
- How to export and interpret results

## Prerequisites

Before starting this tutorial, ensure you have:

1. **SocialMapper installed**:
   ```bash
   pip install socialmapper
   ```

2. **Census API key** (optional but recommended):
   ```bash
   export CENSUS_API_KEY="your-key-here"
   ```
   
   !!! tip "Getting a Census API Key"
       You can obtain a free API key from the [U.S. Census Bureau](https://api.census.gov/data/key_signup.html). While optional, having a key prevents rate limiting.

## Tutorial Overview

This tutorial analyzes access to public libraries in Wake County, NC, demonstrating how residents can reach these important community resources within a 15-minute walk.

## Step-by-Step Guide

### Step 1: Import Required Libraries

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder
```

The tutorial uses SocialMapper's modern API with two key components:
- `SocialMapperClient`: Manages the analysis session
- `SocialMapperBuilder`: Helps construct analysis configurations

### Step 2: Define Search Parameters

```python
geocode_area = "Wake County"
state = "North Carolina"
poi_type = "amenity"  # OpenStreetMap category
poi_name = "library"  # Specific type within category
travel_time = 15      # minutes
```

**Key parameters explained:**
- **geocode_area**: The geographic area to analyze (county, city, or specific address)
- **state**: Helps disambiguate location names
- **poi_type/poi_name**: OpenStreetMap tags for finding specific place types
- **travel_time**: Maximum walking time in minutes

!!! info "OpenStreetMap Tags"
    Common POI combinations include:
    - `amenity=school` for schools
    - `amenity=hospital` for hospitals
    - `leisure=park` for parks
    - `shop=supermarket` for grocery stores

### Step 3: Select Census Variables

```python
census_variables = [
    "total_population",
    "median_household_income",
    "median_age"
]
```

These variables help understand the demographics of people who can access the libraries. SocialMapper supports many census variables including income, age, race, education, and housing characteristics.

### Step 4: Build and Run the Analysis

```python
with SocialMapperClient() as client:
    # Build configuration using fluent interface
    config = (SocialMapperBuilder()
        .with_location(geocode_area, state)
        .with_osm_pois(poi_type, poi_name)
        .with_travel_time(travel_time)
        .with_census_variables(*census_variables)
        .with_exports(csv=True, isochrones=False)
        .build()
    )
    
    # Run analysis
    result = client.run_analysis(config)
```

The builder pattern makes it easy to configure analyses:
- `.with_location()`: Sets the geographic area
- `.with_osm_pois()`: Configures POI search
- `.with_travel_time()`: Sets travel time limit
- `.with_census_variables()`: Selects demographic data
- `.with_exports()`: Controls output formats

### Step 5: Handle Results

```python
if result.is_err():
    error = result.unwrap_err()
    print(f"Error: {error.message}")
else:
    analysis_result = result.unwrap()
    print(f"Found {analysis_result.poi_count} libraries")
    print(f"Analyzed {analysis_result.census_units_analyzed} block groups")
```

SocialMapper uses Result types for robust error handling. The analysis returns:
- **poi_count**: Number of libraries found
- **census_units_analyzed**: Number of census block groups within reach
- **files_generated**: Dictionary of output file paths

## Understanding the Output

The tutorial generates a CSV file in the `output/csv/` directory containing:

1. **POI Information**: Name, address, and coordinates of each library
2. **Demographics**: Population characteristics within walking distance
3. **Aggregated Statistics**: Summary metrics across all reachable areas

### Sample Output Structure

The CSV output contains detailed data that can be hard to read in raw format. Here's how to create a beautiful, readable table using SocialMapper's built-in Rich console:

```python
import pandas as pd
from socialmapper.ui.rich_console import console, print_table

# Read the generated CSV file
df = pd.read_csv('output/csv/wake_county_north_carolina_library_analysis.csv')

# Select key columns and format for display
display_data = []
for _, row in df.iterrows():
    display_data.append({
        'Library': row['poi_name'],
        'Population Served': f"{int(row['total_population']):,}",
        'Median Income': f"${int(row['median_household_income']):,}",
        'Median Age': f"{row['median_age']:.1f}"
    })

# Display using Rich table
print_table(display_data, title="Library Accessibility Analysis")
```

This produces a beautiful, formatted table:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Library                               ┃ Population Served ┃ Median Income  ┃ Median Age ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Wake County Public Library - Main     │ 15,420           │ $65,000        │ 34.5       │
│ Eva H. Perry Regional Library         │ 12,300           │ $58,000        │ 36.2       │
│ Green Road Library                    │ 18,750           │ $72,500        │ 32.1       │
│ Apex Library                          │ 22,100           │ $85,000        │ 35.8       │
└───────────────────────────────────────┴──────────────────┴────────────────┴────────────┘
```

For even simpler usage with direct DataFrame printing:
```python
from socialmapper.ui.rich_console import console

# Create a Rich table directly from DataFrame
from rich.table import Table

table = Table(title="Library Accessibility Summary")
table.add_column("Library Name", style="cyan", no_wrap=True)
table.add_column("Pop. Reach", justify="right", style="green")
table.add_column("Income", justify="right", style="yellow")

for _, row in df.head(5).iterrows():
    table.add_row(
        row['poi_name'][:30],  # Truncate long names
        f"{int(row['total_population']):,}",
        f"${int(row['median_household_income']):,}"
    )

console.print(table)
```

## Customizing the Analysis

### Try Different POI Types

Replace the library search with other community resources:

```python
# Parks
poi_type = "leisure"
poi_name = "park"

# Schools
poi_type = "amenity"
poi_name = "school"

# Healthcare
poi_type = "amenity"
poi_name = "hospital"
```

### Adjust Travel Parameters

```python
# Shorter walk (5 minutes)
travel_time = 5

# Longer walk (30 minutes)
travel_time = 30

# Different travel mode (requires mode support)
travel_mode = "drive"  # or "bike"
```

### Add More Census Variables

```python
census_variables = [
    "total_population",
    "median_household_income",
    "median_age",
    "percent_poverty",
    "percent_no_vehicle",
    "percent_seniors"
]
```

### Enable Map Generation

```python
.with_exports(csv=True, isochrones=True)  # Creates visual maps
```

## Common Issues and Solutions

### No POIs Found
- Verify the location name is correct
- Try a larger geographic area
- Check POI type/name combination

### Census Data Missing
- Ensure Census API key is set
- Some rural areas may have limited data
- Try different census variables

### Slow Performance
- First run downloads street network data (cached for future use)
- Reduce travel time for faster analysis
- Use smaller geographic areas

## Next Steps

After completing this tutorial, explore:

1. **[Custom POIs Tutorial](custom-pois-tutorial.md)**: Use your own location data
2. **[Travel Modes Tutorial](travel-modes-tutorial.md)**: Compare walk, bike, and drive access
3. **[ZCTA Analysis Tutorial](zcta-analysis-tutorial.md)**: Analyze by ZIP code

## Full Code

The complete tutorial script is available at:
```
examples/tutorials/01_getting_started.py
```

## Key Takeaways

- SocialMapper makes it easy to analyze community accessibility
- The builder pattern provides a clean API for configuration
- Results include both geographic and demographic insights
- Caching speeds up repeated analyses
- Error handling helps diagnose issues