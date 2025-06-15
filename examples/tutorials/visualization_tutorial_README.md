# SocialMapper Visualization Tutorial

This tutorial demonstrates how to create professional static choropleth maps using SocialMapper's visualization module.

## Overview

The tutorial covers:

1. **Basic Choropleth Maps** - Simple demographic visualizations
2. **Custom Appearance** - Color schemes, classifications, and styling
3. **Distance & Accessibility Maps** - Travel analysis with POIs and isochrones
4. **Pipeline Integration** - Automated map generation from analysis outputs
5. **Advanced Techniques** - Multi-format export, missing data, transformations
6. **Best Practices** - Guidelines for publication-quality maps

## Running the Tutorial

### Prerequisites

Ensure you have SocialMapper installed with the visualization module:

```bash
pip install -e ".[dev]"
```

### Execute the Tutorial

Run the complete tutorial:

```bash
cd examples/tutorials
python visualization_tutorial.py
```

This will create various example maps in the `output/` directory.

### Run Individual Sections

You can also run specific tutorial sections:

```python
from visualization_tutorial import tutorial_basic_choropleth
tutorial_basic_choropleth()
```

## Tutorial Sections

### 1. Basic Choropleth Maps

Learn the fundamentals:
- Creating population maps
- Using convenience methods
- Basic map customization

**Output files:**
- `tutorial_basic_population.png` - Simple population map
- `tutorial_basic_income.png` - Median income visualization

### 2. Custom Appearance

Explore customization options:
- Color scheme selection (sequential, diverging)
- Classification methods (quantiles, natural breaks)
- Legend formatting
- Custom attributions

**Output files:**
- `tutorial_custom_colors.png` - Viridis color scheme with natural breaks
- `tutorial_custom_legend.png` - Currency-formatted legend
- `tutorial_diverging_colors.png` - Educational attainment with diverging colors

### 3. Distance & Accessibility

Visualize spatial relationships:
- Distance maps with POI markers
- Accessibility maps with isochrones
- Composite visualizations

**Output files:**
- `tutorial_distance_map.png` - Travel distance to libraries
- `tutorial_accessibility_map.png` - Population within walking distance
- `tutorial_composite_map.png` - Combined analysis with annotations

### 4. Pipeline Integration

Automate map creation:
- Batch processing multiple variables
- Automatic demographic column detection
- Integration with SocialMapper outputs

**Output files:**
- `pipeline_maps/distance_map.png`
- `pipeline_maps/b01003_001e_map.png` (population)
- `pipeline_maps/b19013_001e_map.png` (income)
- Additional demographic maps

### 5. Advanced Techniques

Special use cases:
- Multi-format export (PNG, PDF, SVG)
- Handling missing data
- Data transformations (log scale)

**Output files:**
- `tutorial_advanced_export.*` - Multiple format examples
- `tutorial_missing_data.png` - Visualization with missing values
- `tutorial_transformed_data.png` - Log-transformed population density

### 6. Best Practices

Professional map creation:
- Color scheme selection guidelines
- Classification method comparison
- Publication-ready formatting

**Output files:**
- `tutorial_bp_sequential.png` - Sequential color example
- `tutorial_bp_diverging.png` - Diverging color example
- `tutorial_bp_*.png` - Classification method comparisons
- `tutorial_publication_ready.pdf` - Journal-ready map

## Key Concepts

### Color Schemes

Choose appropriate color schemes for your data:

- **Sequential** (Blues, Greens, YlOrRd): For data that progresses from low to high
- **Diverging** (RdBu, BrBG): For data with a meaningful midpoint
- **Perceptually Uniform** (Viridis, Plasma): For accurate data representation

### Classification Methods

Select the right method for your data distribution:

- **Quantiles**: Equal number of features in each class
- **Fisher-Jenks**: Natural breaks that minimize within-class variance
- **Equal Interval**: Same numeric range for each class
- **Standard Deviation**: Highlight values above/below mean

### Map Elements

Professional maps include:
- Clear, informative title
- Properly formatted legend
- North arrow for orientation
- Scale bar for distance reference
- Data attribution
- Creation date

## Customization Examples

### Basic Usage

```python
from socialmapper.visualization import ChoroplethMap

# Simple demographic map
fig, ax = ChoroplethMap.create_demographic_map(
    gdf,
    'B01003_001E',
    title='Total Population'
)
```

### Advanced Configuration

```python
from socialmapper.visualization import MapConfig, ColorScheme

config = MapConfig(
    figsize=(14, 10),
    color_scheme=ColorScheme.PLASMA,
    n_classes=7,
    title="Custom Analysis",
    legend_config={
        'title': 'Values',
        'fmt': '{:.1f}',
        'loc': 'upper right'
    }
)

mapper = ChoroplethMap(config)
fig, ax = mapper.create_map(gdf, 'your_column')
```

## Tips for Success

1. **Start Simple**: Use convenience methods before diving into custom configurations
2. **Test Classifications**: Try different methods to find the best representation
3. **Consider Your Audience**: Use colorblind-friendly schemes for public maps
4. **Export Appropriately**: PNG for web (300 DPI), PDF for print
5. **Document Sources**: Always include data attribution

## Common Issues

### Memory Usage
Large GeoDataFrames may require geometry simplification:
```python
config = MapConfig(simplify_tolerance=0.01)
```

### Missing Dependencies
If you get import errors, ensure all dependencies are installed:
```bash
pip install matplotlib geopandas mapclassify
```

### Display Issues
If maps appear distorted, check your GeoDataFrame CRS:
```python
gdf = gdf.to_crs('EPSG:4326')  # Convert to WGS84
```

## Next Steps

After completing this tutorial:

1. Apply these techniques to your own SocialMapper analysis
2. Explore the full API in `socialmapper.visualization`
3. Customize the pipeline integration for your workflow
4. Share your maps and provide feedback!

## Additional Resources

- [SocialMapper Documentation](https://github.com/yourusername/socialmapper)
- [GeoPandas Plotting Guide](https://geopandas.org/en/stable/docs/user_guide/mapping.html)
- [Matplotlib Colormaps](https://matplotlib.org/stable/tutorials/colors/colormaps.html)
- [ColorBrewer](https://colorbrewer2.org/) - Color advice for maps