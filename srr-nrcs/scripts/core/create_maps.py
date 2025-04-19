"""
Create map visualizations for the NRCS Conservation Study Area Analysis.

This script creates two primary visualizations:
1. An overview map showing Walmart locations by store type across the study area
2. A density map showing the distribution of Walmart stores by county

The script reads processed county boundaries and Walmart location data from 
previous pipeline steps and outputs visualization maps in PNG format.

Dependencies:
    - geopandas: For spatial data operations
    - matplotlib: For creating visualizations
    - contextily: For adding basemaps
    - pyproj: For coordinate system transformations

Outputs:
    - study_area_overview.png: Map showing Walmart locations by type 
    - walmart_density.png: Map showing store distribution by county
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
import json
from pyproj import Transformer

def load_data():
    """
    Load county boundaries and consolidated Walmart locations from pipeline output files.
    
    Reads data from:
        - county_boundaries.geojson: County boundary geometries
        - walmart_locations_consolidated.csv: Processed Walmart location data
        - study_area_bbox.json: Bounding box for the study area
        
    Returns:
        tuple: Contains:
            - counties (gpd.GeoDataFrame): County boundaries
            - walmart_gdf (gpd.GeoDataFrame): Walmart locations with geometries
            - bbox (dict): Study area bounding box coordinates
    """
    # Load county boundaries
    counties = gpd.read_file('county_boundaries.geojson')
    
    # Load consolidated Walmart locations and convert to GeoDataFrame
    walmart_df = pd.read_csv('walmart_locations_consolidated.csv')
    walmart_gdf = gpd.GeoDataFrame(
        walmart_df, 
        geometry=gpd.points_from_xy(walmart_df.lon, walmart_df.lat),
        crs="EPSG:4326"  # WGS84 coordinate system
    )
    
    # Load expanded bounding box
    with open('study_area_bbox.json', 'r') as f:
        bbox = json.load(f)
    
    return counties, walmart_gdf, bbox

def create_overview_map(counties: gpd.GeoDataFrame, walmart_locations: gpd.GeoDataFrame, bbox: dict):
    """
    Create an overview map showing county boundaries and Walmart locations by store type.
    
    The map includes:
        - County boundaries with light fill
        - Basemap for geographic context
        - Walmart locations color-coded by service type (Supercenter, Neighborhood Market, General Store)
        
    Args:
        counties (gpd.GeoDataFrame): County boundary geometries
        walmart_locations (gpd.GeoDataFrame): Processed Walmart location data with point geometries
        bbox (dict): Dictionary containing west, east, north, south bounds of the study area
        
    Outputs:
        study_area_overview.png: Map visualization saved as PNG file
    """
    # Convert to Web Mercator (EPSG:3857) for basemap compatibility
    counties_web = counties.to_crs(epsg=3857)
    walmart_web = walmart_locations.to_crs(epsg=3857)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot counties with thicker boundaries
    counties_web.plot(
        ax=ax,
        alpha=0.2,
        edgecolor='black',
        linewidth=1.5,
        facecolor='lightgray'
    )
    
    # Convert bbox from WGS84 to Web Mercator coordinates and set map extent
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x1, y1 = transformer.transform(bbox['west'], bbox['south'])  # southwest corner
    x2, y2 = transformer.transform(bbox['east'], bbox['north'])  # northeast corner
    ax.set_xlim(x1, x2)
    ax.set_ylim(y1, y2)
    
    # Add CartoDB Positron basemap (light, neutral style)
    ctx.add_basemap(
        ax,
        source=ctx.providers.CartoDB.Positron,
        alpha=0.6
    )
    
    # Define color scheme for different Walmart store types
    color_map = {
        'Supercenter': '#e41a1c',     # Bright red
        'Neighborhood Market': '#4daf4a',  # Green
        'General Store': '#377eb8'     # Blue
    }
    
    # Plot each type of store with different colors
    for store_type, color in color_map.items():
        mask = walmart_web['services'].str.contains(store_type)
        if mask.any():
            walmart_web[mask].plot(
                ax=ax,
                color=color,
                markersize=80,
                alpha=0.7,
                label=store_type,
                marker='o',
                edgecolor='white',
                linewidth=0.5
            )
    
    # Add title and legend
    plt.title('Study Area Overview: Walmart Locations by Type', fontsize=16, pad=20)
    ax.legend(fontsize=10, loc='upper right', framealpha=0.9)
    
    # Save figure at high resolution
    plt.savefig('study_area_overview.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_density_map(counties: gpd.GeoDataFrame, walmart_locations: gpd.GeoDataFrame, bbox: dict):
    """
    Create a choropleth map showing Walmart store density by county.
    
    The map includes:
        - Counties colored by number of Walmart stores
        - County labels showing names and store counts
        - Basemap for geographic context
        
    Args:
        counties (gpd.GeoDataFrame): County boundary geometries
        walmart_locations (gpd.GeoDataFrame): Processed Walmart location data with point geometries
        bbox (dict): Dictionary containing west, east, north, south bounds of the study area
        
    Outputs:
        walmart_density.png: Density map visualization saved as PNG file
    """
    # Spatial join to count Walmart stores per county
    walmart_counts = gpd.sjoin(walmart_locations, counties, how='right', predicate='within')
    walmart_by_county = walmart_counts.groupby('GEOID').size().reset_index(name='walmart_count')
    
    # Merge counts back to counties for choropleth mapping
    counties_with_counts = counties.merge(walmart_by_county, on='GEOID', how='left')
    counties_with_counts['walmart_count'] = counties_with_counts['walmart_count'].fillna(0)
    
    # Convert to Web Mercator for basemap compatibility
    counties_web = counties_with_counts.to_crs(epsg=3857)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot density choropleth with Yellow-Orange-Red color scheme
    counties_web.plot(
        column='walmart_count',
        ax=ax,
        legend=True,
        legend_kwds={
            'label': 'Number of Walmart Stores',
            'orientation': 'horizontal',
            'pad': 0.05
        },
        missing_kwds={'color': 'lightgrey'},
        cmap='YlOrRd',  # Yellow to Orange to Red color gradient
        alpha=0.7,
        edgecolor='black',
        linewidth=0.5
    )
    
    # Convert bbox from WGS84 to Web Mercator coordinates and set map extent
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x1, y1 = transformer.transform(bbox['west'], bbox['south'])
    x2, y2 = transformer.transform(bbox['east'], bbox['north'])
    ax.set_xlim(x1, x2)
    ax.set_ylim(y1, y2)
    
    # Add CartoDB Positron basemap (light, neutral style)
    ctx.add_basemap(
        ax,
        source=ctx.providers.CartoDB.Positron,
        alpha=0.6
    )
    
    # Add county labels for those with at least one store
    for idx, row in counties_web[counties_web['walmart_count'] > 0].iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            text=f"{row['NAME']}\n({int(row['walmart_count'])})",
            xy=(centroid.x, centroid.y),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=8,
            color='black',
            bbox=dict(facecolor='white', edgecolor='black', alpha=0.7, pad=0.5)
        )
    
    # Add title
    plt.title('Walmart Store Distribution by County', fontsize=16, pad=20)
    
    # Save figure at high resolution
    plt.savefig('walmart_density.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """
    Main function to execute the map creation pipeline.
    
    Steps:
    1. Load county and Walmart data
    2. Create overview map showing Walmart locations by type
    3. Create density map showing store distribution by county
    4. Print statistics about the data
    """
    # Load data from previous pipeline outputs
    counties, walmart_locations, bbox = load_data()
    
    # Create visualization maps
    create_overview_map(counties, walmart_locations, bbox)
    create_density_map(counties, walmart_locations, bbox)
    
    # Print output status
    print("Maps have been created:")
    print("1. study_area_overview.png - Shows Walmart locations by type")
    print("2. walmart_density.png - Shows Walmart store distribution by county")
    
    # Print data statistics for verification
    print("\nWalmart location statistics:")
    print(f"Total locations: {len(walmart_locations)}")
    print("\nLocations by service type:")
    for service in walmart_locations['services'].unique():
        count = walmart_locations[walmart_locations['services'] == service].shape[0]
        print(f"{service}: {count}")

if __name__ == "__main__":
    main() 