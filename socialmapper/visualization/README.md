# SocialMapper Visualization Module

This module provides modern, professional static chloropleth map generation for SocialMapper outputs. It follows current best practices for creating publication-quality demographic and accessibility maps.

## Features

- **Professional Choropleth Maps**: Create high-quality static maps with customizable color schemes and classification methods
- **Multiple Map Types**: Support for demographic, distance, accessibility, and composite maps
- **Modern Design**: Follows 2023-2024 best practices for cartographic visualization
- **Full Customization**: Extensive configuration options for colors, legends, and map elements
- **Pipeline Integration**: Seamlessly integrates with SocialMapper's analysis pipeline

## Quick Start

```python
from socialmapper.visualization import ChoroplethMap

# Create a simple demographic map
fig, ax = ChoroplethMap.create_demographic_map(
    gdf,
    'B01003_001E',  # Total population
    title='Population Distribution'
)
fig.savefig('population_map.png', dpi=300)
```

## Map Types

### 1. Demographic Maps
Show distribution of census variables like population, income, or education levels.

```python
fig, ax = ChoroplethMap.create_demographic_map(
    gdf,
    'B19013_001E',  # Median household income
    title='Median Household Income by Block Group'
)
```

### 2. Distance Maps
Visualize travel distances from census units to points of interest.

```python
fig, ax = ChoroplethMap.create_distance_map(
    gdf,
    'travel_distance_km',
    poi_gdf=libraries_gdf,
    title='Distance to Nearest Library'
)
```

### 3. Accessibility Maps
Combine demographic data with isochrones to show population within travel time areas.

```python
fig, ax = ChoroplethMap.create_accessibility_map(
    gdf,
    'B01003_001E',
    poi_gdf=libraries_gdf,
    isochrone_gdf=walk_15min_gdf,
    title='Population within 15-minute Walk of Libraries'
)
```

## Configuration

### Color Schemes

The module supports various color schemes optimized for different data types:

- **Sequential**: `BLUES`, `REDS`, `GREENS`, `YLORBR`, `VIRIDIS`
- **Diverging**: `RDBU`, `BRBG`, `SPECTRAL`
- **Categorical**: `SET1`, `SET2`, `TAB10`

### Classification Methods

Choose from multiple classification schemes:

- `QUANTILES`: Equal number of features per class (default)
- `FISHER_JENKS`: Natural breaks for optimal class separation
- `EQUAL_INTERVAL`: Same numeric range per class
- `STD_MEAN`: Based on standard deviations from mean

### Custom Configuration

```python
from socialmapper.visualization import MapConfig, ColorScheme, ClassificationScheme

config = MapConfig(
    figsize=(14, 10),
    color_scheme=ColorScheme.PLASMA,
    classification_scheme=ClassificationScheme.FISHER_JENKS,
    n_classes=7,
    title="Custom Analysis Map",
    legend_config={
        'title': 'Value',
        'fmt': '{:.1f}',
        'loc': 'upper right'
    },
    attribution="Data: US Census Bureau | Analysis: Your Organization"
)

mapper = ChoroplethMap(config)
fig, ax = mapper.create_map(gdf, 'your_column')
```

## Pipeline Integration

The module integrates seamlessly with SocialMapper's analysis pipeline:

```python
from socialmapper.visualization.pipeline_integration import VisualizationPipeline

# Create visualization pipeline
viz_pipeline = VisualizationPipeline('output/maps')

# Generate multiple maps from census data
output_paths = viz_pipeline.create_maps_from_census_data(
    census_gdf,
    poi_gdf=poi_gdf,
    isochrone_gdf=isochrone_gdf,
    demographic_columns=['B01003_001E', 'B19013_001E'],
    create_distance_map=True,
    map_format='png'
)
```

## Map Elements

Each map includes professional cartographic elements:

- **Title**: Customizable font size and style
- **Legend**: Smart formatting with classification breaks
- **North Arrow**: Directional indicator
- **Scale Bar**: Distance reference
- **Attribution**: Data source and creation date

## Best Practices

1. **Color Selection**:
   - Use sequential schemes for continuous data
   - Use diverging schemes for data with meaningful midpoints
   - Avoid rainbow color schemes

2. **Classification**:
   - Use Fisher-Jenks for skewed demographic data
   - Use quantiles for normally distributed data
   - Use equal interval for comparing across maps

3. **Export**:
   - Use 300 DPI for print quality
   - Export as PNG for web, PDF for publications
   - Include attribution for data sources

## Examples

See `examples.py` for complete working examples including:
- Basic demographic mapping
- Distance analysis with POIs
- Custom configuration
- Accessibility analysis with isochrones
- Pipeline integration

## Requirements

- matplotlib >= 3.5.0
- geopandas >= 0.12.0
- mapclassify >= 2.4.0
- numpy >= 2.0.0
- pandas >= 1.5.0