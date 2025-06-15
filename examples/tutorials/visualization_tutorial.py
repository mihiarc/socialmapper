"""
SocialMapper Visualization Tutorial
===================================

This tutorial demonstrates how to create professional static choropleth maps
using SocialMapper's visualization module. We'll cover everything from basic
maps to advanced customization and pipeline integration.

Author: SocialMapper Team
Date: 2024
"""

import sys
from pathlib import Path

# Add the project root to Python path if running from examples directory
project_root = Path(__file__).parent.parent.parent
if project_root.exists():
    sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt

# Import SocialMapper visualization components
from socialmapper.visualization import ChoroplethMap, MapType, MapConfig, ColorScheme
from socialmapper.visualization.config import ClassificationScheme, LegendConfig
from socialmapper.visualization.pipeline_integration import VisualizationPipeline


# =============================================================================
# PART 1: Creating Sample Data
# =============================================================================

def create_sample_census_data():
    """
    Create sample census block group data for demonstration.
    In real usage, this would come from SocialMapper's analysis pipeline.
    """
    np.random.seed(42)
    
    # Create a grid of census block groups
    blocks = []
    data = []
    
    for i in range(5):
        for j in range(5):
            # Create a square polygon for each block group
            x, y = i * 0.1, j * 0.1
            polygon = Polygon([
                (x, y), (x + 0.08, y), 
                (x + 0.08, y + 0.08), (x, y + 0.08)
            ])
            blocks.append(polygon)
            
            # Generate sample demographic data
            block_id = f"37183050{i}{j}01"
            population = np.random.randint(500, 5000)
            income = np.random.randint(25000, 150000)
            
            # Distance increases from center
            center_x, center_y = 0.25, 0.25
            distance = np.sqrt((x + 0.04 - center_x)**2 + (y + 0.04 - center_y)**2) * 10
            
            data.append({
                'census_block_group': block_id,
                'B01003_001E': population,  # Total population
                'B19013_001E': income,      # Median household income
                'B25001_001E': np.random.randint(200, 2000),  # Housing units
                'B15003_022E': int(population * np.random.uniform(0.1, 0.4)),  # Bachelor's degree
                'travel_distance_km': distance + np.random.normal(0, 0.5),
                'travel_time_minutes': distance * 12 + np.random.normal(0, 2)
            })
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(data, geometry=blocks, crs='EPSG:4326')
    return gdf


def create_sample_poi_data():
    """Create sample Points of Interest (libraries)."""
    pois = [
        {'name': 'Central Library', 'x': 0.25, 'y': 0.25},
        {'name': 'North Branch', 'x': 0.25, 'y': 0.4},
        {'name': 'South Branch', 'x': 0.25, 'y': 0.1},
    ]
    
    geometry = [Point(poi['x'], poi['y']) for poi in pois]
    poi_gdf = gpd.GeoDataFrame(
        [{'poi_name': poi['name']} for poi in pois],
        geometry=geometry,
        crs='EPSG:4326'
    )
    return poi_gdf


def create_sample_isochrone_data():
    """Create sample 15-minute walk isochrones around POIs."""
    # Create circles around POIs to simulate isochrones
    center_points = [(0.25, 0.25), (0.25, 0.4), (0.25, 0.1)]
    isochrones = []
    
    for i, (x, y) in enumerate(center_points):
        # Create a circle with ~0.15 unit radius (roughly 15-min walk)
        circle = Point(x, y).buffer(0.15)
        isochrones.append(circle)
    
    isochrone_gdf = gpd.GeoDataFrame(
        [{'poi_id': i, 'travel_time': 15} for i in range(len(isochrones))],
        geometry=isochrones,
        crs='EPSG:4326'
    )
    return isochrone_gdf


# =============================================================================
# PART 2: Basic Choropleth Maps
# =============================================================================

def tutorial_basic_choropleth():
    """
    Tutorial 1: Creating a basic choropleth map.
    
    This example shows the simplest way to create a choropleth map
    using SocialMapper's visualization module.
    """
    print("\n" + "="*60)
    print("TUTORIAL 1: Basic Choropleth Map")
    print("="*60)
    
    # Load sample data
    census_gdf = create_sample_census_data()
    
    # Method 1: Using the convenience method (recommended for beginners)
    fig, ax = ChoroplethMap.create_demographic_map(
        census_gdf,
        'B01003_001E',  # Total population column
        title='Population by Census Block Group'
    )
    
    # Save the map
    output_path = Path('output/tutorial_basic_population.png')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Created basic population map: {output_path}")
    
    # Method 2: Using the ChoroplethMap class directly (more control)
    mapper = ChoroplethMap()
    fig, ax = mapper.create_map(
        census_gdf,
        'B19013_001E',  # Median income column
        map_type=MapType.DEMOGRAPHIC
    )
    
    # Customize after creation
    ax.set_title('Median Household Income by Block Group', fontsize=16, pad=20)
    
    output_path = Path('output/tutorial_basic_income.png')
    mapper.save(output_path)
    plt.close(fig)
    
    print(f"✓ Created basic income map: {output_path}")


# =============================================================================
# PART 3: Customizing Map Appearance
# =============================================================================

def tutorial_custom_appearance():
    """
    Tutorial 2: Customizing map appearance.
    
    This example demonstrates how to customize colors, classification,
    and other visual elements of your maps.
    """
    print("\n" + "="*60)
    print("TUTORIAL 2: Customizing Map Appearance")
    print("="*60)
    
    census_gdf = create_sample_census_data()
    
    # Example 1: Custom color scheme and classification
    config = MapConfig(
        figsize=(12, 10),
        color_scheme=ColorScheme.VIRIDIS,  # Modern, colorblind-friendly
        classification_scheme=ClassificationScheme.FISHER_JENKS,  # Natural breaks
        n_classes=7,  # More classes for finer detail
        title="Population Distribution (Natural Breaks Classification)",
        title_fontsize=18,
        edge_color='black',
        edge_width=0.3
    )
    
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(census_gdf, 'B01003_001E')
    
    output_path = Path('output/tutorial_custom_colors.png')
    mapper.save(output_path)
    plt.close(fig)
    
    print(f"✓ Created custom color scheme map: {output_path}")
    
    # Example 2: Custom legend configuration
    legend_config = LegendConfig(
        title="Median Income ($)",
        loc="upper right",
        fmt="${:,.0f}",  # Format as currency
        fontsize=12,
        title_fontsize=14,
        frameon=True,
        shadow=True
    )
    
    config = MapConfig(
        color_scheme=ColorScheme.GREENS,  # Green for money
        classification_scheme=ClassificationScheme.QUANTILES,
        n_classes=5,
        title="Median Household Income Distribution",
        legend_config=legend_config,
        attribution="Data: US Census Bureau ACS 5-Year | Analysis: Your Organization"
    )
    
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(census_gdf, 'B19013_001E')
    
    output_path = Path('output/tutorial_custom_legend.png')
    mapper.save(output_path)
    plt.close(fig)
    
    print(f"✓ Created custom legend map: {output_path}")
    
    # Example 3: Highlighting patterns with diverging colors
    # Calculate percentage with bachelor's degree
    census_gdf['pct_bachelors'] = (
        census_gdf['B15003_022E'] / census_gdf['B01003_001E'] * 100
    )
    
    config = MapConfig(
        color_scheme=ColorScheme.RDBU,  # Red-Blue diverging
        classification_scheme=ClassificationScheme.STD_MEAN,  # Highlight above/below average
        n_classes=6,
        title="Educational Attainment: % with Bachelor's Degree",
        legend_config=LegendConfig(
            title="% Bachelor's",
            fmt="{:.1f}%"
        )
    )
    
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(census_gdf, 'pct_bachelors')
    
    output_path = Path('output/tutorial_diverging_colors.png')
    mapper.save(output_path)
    plt.close(fig)
    
    print(f"✓ Created diverging color map: {output_path}")


# =============================================================================
# PART 4: Distance and Accessibility Maps
# =============================================================================

def tutorial_distance_accessibility():
    """
    Tutorial 3: Creating distance and accessibility maps.
    
    This example shows how to visualize travel distances and
    combine demographic data with accessibility analysis.
    """
    print("\n" + "="*60)
    print("TUTORIAL 3: Distance and Accessibility Maps")
    print("="*60)
    
    census_gdf = create_sample_census_data()
    poi_gdf = create_sample_poi_data()
    isochrone_gdf = create_sample_isochrone_data()
    
    # Example 1: Distance map with POI locations
    fig, ax = ChoroplethMap.create_distance_map(
        census_gdf,
        'travel_distance_km',
        poi_gdf=poi_gdf,
        title='Travel Distance to Nearest Library',
        legend_config=LegendConfig(
            title="Distance (km)",
            fmt="{:.1f}"
        )
    )
    
    output_path = Path('output/tutorial_distance_map.png')
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Created distance map: {output_path}")
    
    # Example 2: Accessibility map with isochrones
    fig, ax = ChoroplethMap.create_accessibility_map(
        census_gdf,
        'B01003_001E',  # Show population
        poi_gdf=poi_gdf,
        isochrone_gdf=isochrone_gdf,
        title='Population within 15-minute Walk of Libraries',
        alpha=0.7  # Make choropleth semi-transparent to see isochrones
    )
    
    output_path = Path('output/tutorial_accessibility_map.png')
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Created accessibility map: {output_path}")
    
    # Example 3: Custom composite map
    config = MapConfig(
        figsize=(14, 10),
        color_scheme=ColorScheme.YLORD,  # Yellow-Orange-Red for distance
        classification_scheme=ClassificationScheme.FISHER_JENKS,
        n_classes=6,
        title="Library Access Analysis: Distance and Population",
        alpha=0.8,
        edge_color='white',
        edge_width=0.5
    )
    
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(
        census_gdf,
        'travel_distance_km',
        map_type=MapType.COMPOSITE,
        poi_gdf=poi_gdf,
        isochrone_gdf=isochrone_gdf
    )
    
    # Add custom annotations
    for idx, poi in poi_gdf.iterrows():
        ax.annotate(
            poi['poi_name'],
            xy=(poi.geometry.x, poi.geometry.y),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7)
        )
    
    output_path = Path('output/tutorial_composite_map.png')
    mapper.save(output_path)
    plt.close(fig)
    
    print(f"✓ Created composite map: {output_path}")


# =============================================================================
# PART 5: Pipeline Integration
# =============================================================================

def tutorial_pipeline_integration():
    """
    Tutorial 4: Integrating with SocialMapper pipeline.
    
    This example demonstrates how to automatically generate multiple
    maps from SocialMapper's analysis output.
    """
    print("\n" + "="*60)
    print("TUTORIAL 4: Pipeline Integration")
    print("="*60)
    
    # Prepare sample data (in real use, this comes from SocialMapper analysis)
    census_gdf = create_sample_census_data()
    poi_gdf = create_sample_poi_data()
    isochrone_gdf = create_sample_isochrone_data()
    
    # Save sample data to simulate pipeline output
    temp_dir = Path('output/pipeline_data')
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    census_gdf.to_parquet(temp_dir / 'census_data.parquet')
    poi_gdf.to_parquet(temp_dir / 'poi_data.parquet')
    isochrone_gdf.to_parquet(temp_dir / 'isochrone_data.parquet')
    
    # Create visualization pipeline
    viz_pipeline = VisualizationPipeline(Path('output/pipeline_maps'))
    
    # Generate multiple maps automatically
    output_paths = viz_pipeline.create_maps_from_census_data(
        census_gdf,
        poi_gdf=poi_gdf,
        isochrone_gdf=isochrone_gdf,
        demographic_columns=['B01003_001E', 'B19013_001E', 'B25001_001E'],
        create_distance_map=True,
        create_demographic_maps=True,
        map_format='png',
        dpi=300
    )
    
    print("✓ Created pipeline maps:")
    for map_type, path in output_paths.items():
        print(f"  - {map_type}: {path}")
    
    # Close all figures
    plt.close('all')


# =============================================================================
# PART 6: Advanced Techniques
# =============================================================================

def tutorial_advanced_techniques():
    """
    Tutorial 5: Advanced visualization techniques.
    
    This example covers advanced customization and special use cases.
    """
    print("\n" + "="*60)
    print("TUTORIAL 5: Advanced Techniques")
    print("="*60)
    
    census_gdf = create_sample_census_data()
    
    # Example 1: Multi-format export
    config = MapConfig(
        figsize=(12, 8),
        color_scheme=ColorScheme.PLASMA,
        title="Multi-Format Export Example"
    )
    
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(census_gdf, 'B01003_001E')
    
    # Save in multiple formats
    formats = {
        'png': 300,   # High DPI for print
        'pdf': None,  # Vector format
        'svg': None   # Scalable vector
    }
    
    for fmt, dpi in formats.items():
        output_path = Path(f'output/tutorial_advanced_export.{fmt}')
        mapper.save(output_path, format=fmt, dpi=dpi)
        print(f"✓ Exported as {fmt}: {output_path}")
    
    plt.close(fig)
    
    # Example 2: Handling missing data
    # Add some missing values
    census_gdf_missing = census_gdf.copy()
    census_gdf_missing.loc[0:5, 'B19013_001E'] = np.nan
    
    config = MapConfig(
        color_scheme=ColorScheme.BLUES,
        missing_color='lightgray',  # Color for missing data
        title="Handling Missing Data",
        legend_config=LegendConfig(
            title="Median Income ($)",
            fmt="${:,.0f}"
        )
    )
    
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(census_gdf_missing, 'B19013_001E')
    
    # Add note about missing data
    ax.text(
        0.02, 0.98,
        "Gray areas indicate missing data",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
    )
    
    output_path = Path('output/tutorial_missing_data.png')
    mapper.save(output_path)
    plt.close(fig)
    
    print(f"✓ Created missing data map: {output_path}")
    
    # Example 3: Custom data transformation
    # Calculate population density (people per unit area)
    census_gdf['area'] = census_gdf.geometry.area
    census_gdf['pop_density'] = census_gdf['B01003_001E'] / census_gdf['area']
    
    # Log transform for better visualization of skewed data
    census_gdf['log_pop_density'] = np.log10(census_gdf['pop_density'] + 1)
    
    config = MapConfig(
        color_scheme=ColorScheme.INFERNO,
        classification_scheme=ClassificationScheme.QUANTILES,
        n_classes=8,
        title="Population Density (Log Scale)",
        legend_config=LegendConfig(
            title="Log₁₀(Density)",
            fmt="{:.2f}"
        )
    )
    
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(census_gdf, 'log_pop_density')
    
    output_path = Path('output/tutorial_transformed_data.png')
    mapper.save(output_path)
    plt.close(fig)
    
    print(f"✓ Created transformed data map: {output_path}")


# =============================================================================
# PART 7: Best Practices and Tips
# =============================================================================

def tutorial_best_practices():
    """
    Tutorial 6: Best practices for creating effective maps.
    
    This section provides guidance on making professional,
    publication-ready maps.
    """
    print("\n" + "="*60)
    print("TUTORIAL 6: Best Practices")
    print("="*60)
    
    census_gdf = create_sample_census_data()
    
    # Best Practice 1: Choose appropriate color schemes
    print("\nBest Practice 1: Color Scheme Selection")
    print("-" * 40)
    
    # Sequential data (e.g., population counts)
    sequential_config = MapConfig(
        color_scheme=ColorScheme.BLUES,
        title="Sequential: Population Count",
        figsize=(8, 6)
    )
    
    # Diverging data (e.g., change over time)
    census_gdf['pop_change'] = np.random.normal(0, 20, len(census_gdf))
    diverging_config = MapConfig(
        color_scheme=ColorScheme.RDBU,
        classification_scheme=ClassificationScheme.STD_MEAN,
        title="Diverging: Population Change (%)",
        figsize=(8, 6)
    )
    
    # Create both maps
    fig1, ax1 = ChoroplethMap(sequential_config).create_map(
        census_gdf, 'B01003_001E'
    )
    fig2, ax2 = ChoroplethMap(diverging_config).create_map(
        census_gdf, 'pop_change'
    )
    
    fig1.savefig('output/tutorial_bp_sequential.png', dpi=300, bbox_inches='tight')
    fig2.savefig('output/tutorial_bp_diverging.png', dpi=300, bbox_inches='tight')
    plt.close(fig1)
    plt.close(fig2)
    
    print("✓ Created color scheme examples")
    
    # Best Practice 2: Classification method selection
    print("\nBest Practice 2: Classification Methods")
    print("-" * 40)
    
    classification_examples = [
        (ClassificationScheme.QUANTILES, "Quantiles: Equal-count bins"),
        (ClassificationScheme.FISHER_JENKS, "Natural Breaks: Minimize variance"),
        (ClassificationScheme.EQUAL_INTERVAL, "Equal Interval: Same range"),
    ]
    
    for scheme, description in classification_examples:
        config = MapConfig(
            classification_scheme=scheme,
            n_classes=5,
            title=description,
            figsize=(8, 6)
        )
        
        fig, ax = ChoroplethMap(config).create_map(census_gdf, 'B19013_001E')
        
        output_name = f"output/tutorial_bp_{scheme.value}.png"
        fig.savefig(output_name, dpi=300, bbox_inches='tight')
        plt.close(fig)
    
    print("✓ Created classification examples")
    
    # Best Practice 3: Publication-ready maps
    print("\nBest Practice 3: Publication-Ready Maps")
    print("-" * 40)
    
    publication_config = MapConfig(
        figsize=(10, 8),  # Standard journal size
        dpi=300,  # High resolution
        color_scheme=ColorScheme.VIRIDIS,  # Colorblind-friendly
        classification_scheme=ClassificationScheme.FISHER_JENKS,
        n_classes=5,
        title="Median Household Income by Census Block Group",
        title_fontsize=14,
        title_fontweight='normal',  # Not bold for journals
        edge_color='#333333',  # Dark gray instead of black
        edge_width=0.25,  # Thin lines
        legend_config=LegendConfig(
            title="Income (USD)",
            fmt="${:,.0f}",
            fontsize=10,
            title_fontsize=11
        ),
        attribution="Source: U.S. Census Bureau, ACS 5-Year Estimates (2022)",
        attribution_fontsize=8,
        scale_bar=True,
        north_arrow=True
    )
    
    mapper = ChoroplethMap(publication_config)
    fig, ax = mapper.create_map(census_gdf, 'B19013_001E')
    
    # Save as PDF for publication
    output_path = Path('output/tutorial_publication_ready.pdf')
    mapper.save(output_path, format='pdf')
    
    print(f"✓ Created publication-ready map: {output_path}")
    
    plt.close('all')


# =============================================================================
# MAIN: Run All Tutorials
# =============================================================================

def main():
    """Run all tutorial sections."""
    print("\n" + "="*60)
    print("SocialMapper Visualization Tutorial")
    print("="*60)
    print("\nThis tutorial will create various example maps in the 'output' directory.")
    print("Each section demonstrates different features and best practices.")
    
    # Create output directory
    Path('output').mkdir(exist_ok=True)
    
    # Run all tutorial sections
    tutorials = [
        ("Basic Choropleth Maps", tutorial_basic_choropleth),
        ("Custom Appearance", tutorial_custom_appearance),
        ("Distance & Accessibility", tutorial_distance_accessibility),
        ("Pipeline Integration", tutorial_pipeline_integration),
        ("Advanced Techniques", tutorial_advanced_techniques),
        ("Best Practices", tutorial_best_practices)
    ]
    
    for name, func in tutorials:
        try:
            func()
        except Exception as e:
            print(f"\n⚠️  Error in {name}: {e}")
            continue
    
    print("\n" + "="*60)
    print("Tutorial Complete!")
    print("="*60)
    print(f"\nAll example maps have been saved to: {Path('output').absolute()}")
    print("\nNext steps:")
    print("1. Review the generated maps in the output directory")
    print("2. Examine the code for each example")
    print("3. Adapt the examples for your own data")
    print("4. See the module documentation for more options")


if __name__ == '__main__':
    main()