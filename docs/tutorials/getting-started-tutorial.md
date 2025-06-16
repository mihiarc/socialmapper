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
        .with_exports(csv=True, isochrones=False, maps=True)
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
- `.with_exports()`: Controls output formats (CSV data, isochrone boundaries, choropleth maps)

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

The tutorial generates multiple outputs:

### 1. CSV Data File
Located in `output/csv/`, containing:
- **POI Information**: Name, address, and coordinates of each library
- **Demographics**: Population characteristics within walking distance
- **Aggregated Statistics**: Summary metrics across all reachable areas

### 2. Choropleth Maps
Located in `output/maps/`, visualizing:
- **Demographic Maps**: Population density, income distribution, age patterns
- **Distance Map**: Travel distance to nearest library by census block group
- **Accessibility Map**: Combined view showing demographics within isochrones

Each map includes:
- Color-coded census block groups showing data intensity
- Library locations marked with symbols
- Legend explaining the color scale
- Scale bar and north arrow for reference

### Sample Output Structure

The CSV file contains detailed demographic data for each library. Let's first look at the raw output:

```python
import pandas as pd

# Read the generated CSV file
df = pd.read_csv('output/csv/wake_county_north_carolina_library_analysis.csv')

# Show raw data
print(df.head())
```

Raw output (hard to read):
```
                              poi_name     poi_lat     poi_lon  total_population  median_household_income  median_age  percent_poverty  ...
0     Wake County Public Library - Main  35.779623  -78.638245             15420                    65000        34.5             12.3  ...
1          Eva H. Perry Regional Library  35.723412  -78.856732             12300                    58000        36.2             15.7  ...
2                    Green Road Library  35.903234  -78.567891             18750                    72500        32.1              8.9  ...
3                         Apex Library  35.732156  -78.850234             22100                    85000        35.8              5.2  ...
```

### Creating a Readable Table

Now let's transform this into a clean, readable table using the `tabulate` package:

```python
from tabulate import tabulate

# Select and format key columns for display
display_df = pd.DataFrame({
    'Library': df['poi_name'],
    'Population Served': df['total_population'].astype(int).map('{:,}'.format),
    'Median Income': df['median_household_income'].astype(int).map('${:,}'.format),
    'Median Age': df['median_age'].round(1)
})

# Display using tabulate with GitHub-flavored markdown style
print(tabulate(display_df, headers='keys', tablefmt='github', showindex=False))
```

Clean, formatted table:
```
| Library                           | Population Served | Median Income | Median Age |
|-----------------------------------|-------------------|---------------|------------|
| Wake County Public Library - Main | 15,420           | $65,000       | 34.5       |
| Eva H. Perry Regional Library     | 12,300           | $58,000       | 36.2       |
| Green Road Library                | 18,750           | $72,500       | 32.1       |
| Apex Library                      | 22,100           | $85,000       | 35.8       |
```

### Quick Summary Statistics

You can also use pandas to calculate summary statistics and display them in a clean table:

```python
# Calculate summary statistics using pandas
summary_stats = pd.DataFrame({
    'Metric': [
        'Total Libraries',
        'Total Population Reach',
        'Average Population per Library',
        'Average Median Income',
        'Lowest Income Area',
        'Highest Income Area',
        'Average Age'
    ],
    'Value': [
        f"{len(df)}",
        f"{df['total_population'].sum():,}",
        f"{df['total_population'].mean():,.0f}",
        f"${df['median_household_income'].mean():,.0f}",
        f"${df['median_household_income'].min():,}",
        f"${df['median_household_income'].max():,}",
        f"{df['median_age'].mean():.1f} years"
    ]
})

print("\nSummary Statistics:")
print(tabulate(summary_stats, headers='keys', tablefmt='simple', showindex=False))
```

Output:
```
Summary Statistics:
Metric                           Value
-------------------------------  -------------
Total Libraries                  12
Total Population Reach           198,470
Average Population per Library   16,539
Average Median Income            $68,750
Lowest Income Area               $45,000
Highest Income Area              $95,000
Average Age                      34.8 years
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

### Export Options

```python
# Default (CSV + maps)
.with_exports(csv=True, isochrones=False, maps=True)

# All outputs
.with_exports(csv=True, isochrones=True, maps=True)

# Data only (no visualizations)
.with_exports(csv=True, isochrones=False, maps=False)
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
[`examples/tutorials/01_getting_started.py`](https://github.com/mihiarc/socialmapper/blob/main/examples/tutorials/01_getting_started.py)

## Key Takeaways

- SocialMapper makes it easy to analyze community accessibility
- The builder pattern provides a clean API for configuration
- Results include both geographic and demographic insights
- Caching speeds up repeated analyses
- Error handling helps diagnose issues