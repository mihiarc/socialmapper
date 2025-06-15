"""Example usage of the visualization module."""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

from .chloropleth import ChoroplethMap, MapType
from .config import MapConfig, ColorScheme, ClassificationScheme
from .pipeline_integration import VisualizationPipeline


def create_sample_data():
    """Create sample data for demonstration."""
    # Create sample census block groups
    np.random.seed(42)
    n_blocks = 50
    
    # Generate random points
    lons = np.random.uniform(-78.7, -78.5, n_blocks)
    lats = np.random.uniform(35.7, 35.9, n_blocks)
    
    # Create GeoDataFrame
    data = {
        'census_block_group': [f'37183050{i:04d}' for i in range(n_blocks)],
        'B01003_001E': np.random.randint(500, 5000, n_blocks),  # Population
        'B19013_001E': np.random.randint(30000, 120000, n_blocks),  # Income
        'travel_distance_km': np.random.exponential(2.5, n_blocks),  # Distance
        'geometry': [Point(lon, lat).buffer(0.005) for lon, lat in zip(lons, lats)]
    }
    
    gdf = gpd.GeoDataFrame(data, crs='EPSG:4326')
    
    # Create sample POI
    poi_data = {
        'poi_name': ['Library A', 'Library B', 'Library C'],
        'geometry': [
            Point(-78.6, 35.8),
            Point(-78.65, 35.85),
            Point(-78.55, 35.75)
        ]
    }
    poi_gdf = gpd.GeoDataFrame(poi_data, crs='EPSG:4326')
    
    return gdf, poi_gdf


def example_basic_demographic_map():
    """Create a basic demographic choropleth map."""
    # Create sample data
    gdf, poi_gdf = create_sample_data()
    
    # Create map with default settings
    fig, ax = ChoroplethMap.create_demographic_map(
        gdf,
        'B01003_001E',
        title='Population Distribution by Census Block Group'
    )
    
    # Save map
    fig.savefig('population_map.png', dpi=300, bbox_inches='tight')
    print("Created population_map.png")


def example_distance_map_with_pois():
    """Create a distance map showing POI locations."""
    # Create sample data
    gdf, poi_gdf = create_sample_data()
    
    # Create distance map
    fig, ax = ChoroplethMap.create_distance_map(
        gdf,
        'travel_distance_km',
        poi_gdf=poi_gdf,
        title='Travel Distance to Nearest Library'
    )
    
    # Save map
    fig.savefig('distance_map.png', dpi=300, bbox_inches='tight')
    print("Created distance_map.png")


def example_custom_configuration():
    """Create a map with custom configuration."""
    # Create sample data
    gdf, poi_gdf = create_sample_data()
    
    # Custom configuration
    config = MapConfig(
        figsize=(14, 10),
        color_scheme=ColorScheme.PLASMA,
        classification_scheme=ClassificationScheme.QUANTILES,
        n_classes=7,
        edge_color='black',
        edge_width=0.3,
        title='Median Household Income',
        title_fontsize=20,
        legend_config={
            'title': 'Income ($)',
            'fmt': '${:,.0f}',
            'loc': 'upper right'
        },
        attribution='Data: US Census Bureau | Created with SocialMapper'
    )
    
    # Create map
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(
        gdf,
        'B19013_001E',
        map_type=MapType.DEMOGRAPHIC,
        poi_gdf=poi_gdf
    )
    
    # Save in multiple formats
    mapper.save('income_map.png', dpi=300)
    mapper.save('income_map.pdf', format='pdf')
    print("Created income_map.png and income_map.pdf")


def example_pipeline_integration():
    """Example of using the visualization pipeline."""
    # Create sample data
    gdf, poi_gdf = create_sample_data()
    
    # Save sample data
    output_dir = Path('sample_output')
    output_dir.mkdir(exist_ok=True)
    
    gdf.to_parquet(output_dir / 'census_data.parquet')
    poi_gdf.to_parquet(output_dir / 'poi_data.parquet')
    
    # Create visualization pipeline
    viz_pipeline = VisualizationPipeline(output_dir / 'maps')
    
    # Create multiple maps
    output_paths = viz_pipeline.create_maps_from_census_data(
        gdf,
        poi_gdf=poi_gdf,
        demographic_columns=['B01003_001E', 'B19013_001E'],
        create_distance_map=True,
        create_demographic_maps=True,
        map_format='png',
        dpi=300
    )
    
    print("Created maps:")
    for map_type, path in output_paths.items():
        print(f"  {map_type}: {path}")


def example_accessibility_map():
    """Create an accessibility map with isochrones."""
    # Create sample data
    gdf, poi_gdf = create_sample_data()
    
    # Create sample isochrone (15-minute walk radius)
    isochrone_data = {
        'poi_name': ['Library A'],
        'travel_time': [15],
        'geometry': [Point(-78.6, 35.8).buffer(0.02)]  # Simplified circle
    }
    isochrone_gdf = gpd.GeoDataFrame(isochrone_data, crs='EPSG:4326')
    
    # Create accessibility map
    fig, ax = ChoroplethMap.create_accessibility_map(
        gdf,
        'B01003_001E',
        poi_gdf=poi_gdf,
        isochrone_gdf=isochrone_gdf,
        title='Population within 15-minute Walk of Libraries'
    )
    
    # Save map
    fig.savefig('accessibility_map.png', dpi=300, bbox_inches='tight')
    print("Created accessibility_map.png")


if __name__ == '__main__':
    print("Running visualization examples...")
    
    # Run all examples
    example_basic_demographic_map()
    example_distance_map_with_pois()
    example_custom_configuration()
    example_accessibility_map()
    example_pipeline_integration()
    
    print("\nAll examples completed!")