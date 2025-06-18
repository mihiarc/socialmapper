# Getting Started Tutorial (with Choropleth Maps)

This enhanced tutorial introduces SocialMapper's visualization capabilities, showing how to create professional choropleth maps alongside the standard demographic analysis.

## What You'll Learn

- How to search for Points of Interest (POIs) from OpenStreetMap
- How to generate travel time isochrones
- How to analyze census demographics within reachable areas
- **How to create choropleth maps to visualize demographic patterns**
- How to export results in multiple formats

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

This tutorial analyzes access to public libraries in Wake County, NC, demonstrating how residents can reach these important community resources within a 15-minute walk. We'll visualize the demographic characteristics of areas with good library access using choropleth maps.

## Step-by-Step Guide

### Step 1: Import Required Libraries

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder
from socialmapper.visualization.pipeline_integration import add_visualization_to_pipeline
```

The tutorial now uses:
- `SocialMapperClient`: Manages the analysis session
- `SocialMapperBuilder`: Helps construct analysis configurations
- `add_visualization_to_pipeline`: Creates choropleth maps from results

### Step 2: Define Search Parameters

```python
geocode_area = "Wake County"
state = "North Carolina"
poi_type = "amenity"  # OpenStreetMap category
poi_name = "library"  # Specific type within category
travel_time = 15      # minutes
```

### Step 3: Select Census Variables

```python
census_variables = [
    "total_population",
    "median_household_income",
    "median_age",
    "percent_poverty",
    "percent_no_vehicle"
]
```

!!! note "Variables for Visualization"
    When creating choropleth maps, choose variables that reveal spatial patterns. Income, poverty, and vehicle access are particularly relevant for understanding library accessibility.

### Step 4: Build and Run the Analysis

```python
with SocialMapperClient() as client:
    # Build configuration with map exports enabled
    config = (SocialMapperBuilder()
        .with_location(geocode_area, state)
        .with_osm_pois(poi_type, poi_name)
        .with_travel_time(travel_time)
        .with_census_variables(*census_variables)
        .with_exports(csv=True, isochrones=True)  # Enable both exports
        .build()
    )
    
    # Run analysis
    result = client.run_analysis(config)
```

!!! important "Enable Isochrone Export"
    Set `isochrones=True` in `.with_exports()` to save the intermediate data needed for creating choropleth maps.

### Step 5: Generate Choropleth Maps

After the analysis completes, create visualizations:

```python
# Find the generated data files
pipeline_data_dir = Path("output/pipeline_data")
census_data_path = list(pipeline_data_dir.glob("*census*.parquet"))[-1]
poi_data_path = list(pipeline_data_dir.glob("*pois*.parquet"))[-1]
isochrone_data_path = list(pipeline_data_dir.glob("*isochrones*.parquet"))[-1]

# Generate choropleth maps
map_paths = add_visualization_to_pipeline(
    census_data_path=census_data_path,
    output_dir="output/maps",
    poi_data_path=poi_data_path,
    isochrone_data_path=isochrone_data_path,
    demographic_columns=["total_population", "median_household_income", "percent_poverty"],
    create_demographic_maps=True,
    map_format="png",
    dpi=150
)
```

## Understanding the Output

### Generated Files

The enhanced tutorial creates multiple outputs:

1. **CSV Data** (`output/csv/`):
   - Detailed demographic data for each library
   - Aggregated statistics

2. **Intermediate Data** (`output/pipeline_data/`):
   - `*_pois.parquet`: Library locations
   - `*_isochrones.parquet`: 15-minute walk boundaries
   - `*_census.parquet`: Census data with geometries

3. **Choropleth Maps** (`output/maps/`):
   - `total_population_map.png`: Population density patterns
   - `median_household_income_map.png`: Income distribution
   - `percent_poverty_map.png`: Poverty concentration

### Interpreting Choropleth Maps

The choropleth maps reveal spatial patterns in library accessibility:

#### Population Density Map
- **Dark blue areas**: High population density with library access
- **Light blue areas**: Lower population density with library access
- **Gray areas**: Census blocks beyond 15-minute walk

#### Median Income Map
- **Dark green areas**: Higher income neighborhoods with library access
- **Light green areas**: Lower income neighborhoods with library access
- **Pattern analysis**: Are libraries equally accessible across income levels?

#### Travel Distance Map
- **Dark red areas**: Longer travel distance to nearest library
- **Yellow areas**: Moderate travel distance
- **Pattern analysis**: Geographic accessibility varies across the region

### Map Features

Each choropleth map includes:
- **Legend**: Shows data classification and color scheme
- **North arrow**: Indicates map orientation
- **Scale bar**: Shows distance reference
- **POI markers**: Library locations marked with symbols
- **Isochrone overlay**: 15-minute walk boundaries (if applicable)

## Customizing Visualizations

### Change Color Schemes

Modify the visualization configuration:

```python
from socialmapper.visualization import ColorScheme, MapConfig

# Create custom configuration
map_config = MapConfig(
    color_scheme=ColorScheme.BLUES,  # Use blue gradient
    title="Custom Library Access Map",
    figsize=(12, 10),
    show_legend=True,
    show_north_arrow=True,
    show_scale_bar=True
)
```

### Select Different Variables

Choose variables that reveal different patterns:

```python
demographic_columns = [
    "percent_seniors",      # Elderly population
    "percent_no_vehicle",   # Transportation barriers
    "percent_college",      # Education levels
]
```

### Adjust Classification Methods

Control how data is grouped into colors:

```python
from socialmapper.visualization import ClassificationScheme

config = MapConfig(
    classification_scheme=ClassificationScheme.QUANTILES,  # Equal count bins
    n_classes=7,  # More granular classification
)
```

## Common Visualization Issues

### No Maps Generated
- Ensure `isochrones=True` is set in `.with_exports()`
- Check that parquet files exist in `output/pipeline_data/`
- Verify census data was successfully fetched

### Poor Color Contrast
- Try different color schemes (VIRIDIS, PLASMA for continuous data)
- Adjust number of classes (3-7 typically work well)
- Use diverging colors (RDBU) for data with meaningful midpoint

### Large File Sizes
- Reduce DPI for web display (72-150 dpi)
- Use PNG for photos, SVG for scalable graphics
- Enable geometry simplification for large areas

## Complete Example

The full enhanced tutorial script is available at:
[`examples/tutorials/01_getting_started_with_maps.py`](https://github.com/mihiarc/socialmapper/blob/main/examples/tutorials/01_getting_started_with_maps.py)

## Next Steps

After completing this tutorial, explore:

1. **[Custom POIs Tutorial](custom-pois-tutorial.md)**: Analyze your own locations
2. **[Multi-Modal Analysis](travel-modes-tutorial.md)**: Compare walk, bike, and drive access
3. **[Address Geocoding](address-geocoding-tutorial.md)**: Work with specific addresses

## Key Takeaways

- Choropleth maps reveal spatial patterns invisible in tabular data
- SocialMapper integrates demographic analysis with professional visualization
- Maps help communicate findings to stakeholders and communities
- Visualization supports equity analysis by highlighting disparities
- The pipeline seamlessly combines data processing with map generation