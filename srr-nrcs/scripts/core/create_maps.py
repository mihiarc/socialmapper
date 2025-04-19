import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
import json
from pyproj import Transformer

def load_data():
    """Load county boundaries and consolidated Walmart locations."""
    # Load county boundaries
    counties = gpd.read_file('county_boundaries.geojson')
    
    # Load consolidated Walmart locations and convert to GeoDataFrame
    walmart_df = pd.read_csv('walmart_locations_consolidated.csv')
    walmart_gdf = gpd.GeoDataFrame(
        walmart_df, 
        geometry=gpd.points_from_xy(walmart_df.lon, walmart_df.lat),
        crs="EPSG:4326"
    )
    
    # Load expanded bounding box
    with open('study_area_bbox.json', 'r') as f:
        bbox = json.load(f)
    
    return counties, walmart_gdf, bbox

def create_overview_map(counties: gpd.GeoDataFrame, walmart_locations: gpd.GeoDataFrame, bbox: dict):
    """Create an overview map showing county boundaries and Walmart locations."""
    # Convert to Web Mercator for basemap
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
    
    # Convert bbox to Web Mercator and set map extent
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x1, y1 = transformer.transform(bbox['west'], bbox['south'])
    x2, y2 = transformer.transform(bbox['east'], bbox['north'])
    ax.set_xlim(x1, x2)
    ax.set_ylim(y1, y2)
    
    # Add basemap
    ctx.add_basemap(
        ax,
        source=ctx.providers.CartoDB.Positron,
        alpha=0.6
    )
    
    # Plot Walmart locations with service-based colors
    # Create a color map for different types of stores
    color_map = {
        'Supercenter': '#e41a1c',  # Bright red
        'Neighborhood Market': '#4daf4a',  # Green
        'General Store': '#377eb8'  # Blue
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
    
    # Save figure
    plt.savefig('study_area_overview.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_density_map(counties: gpd.GeoDataFrame, walmart_locations: gpd.GeoDataFrame, bbox: dict):
    """Create a choropleth map showing Walmart store density by county."""
    # Spatial join to count Walmart stores per county
    walmart_counts = gpd.sjoin(walmart_locations, counties, how='right', predicate='within')
    walmart_by_county = walmart_counts.groupby('GEOID').size().reset_index(name='walmart_count')
    
    # Merge counts back to counties
    counties_with_counts = counties.merge(walmart_by_county, on='GEOID', how='left')
    counties_with_counts['walmart_count'] = counties_with_counts['walmart_count'].fillna(0)
    
    # Convert to Web Mercator for basemap
    counties_web = counties_with_counts.to_crs(epsg=3857)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot density with improved color scheme
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
        cmap='YlOrRd',
        alpha=0.7,
        edgecolor='black',
        linewidth=0.5
    )
    
    # Convert bbox to Web Mercator and set map extent
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x1, y1 = transformer.transform(bbox['west'], bbox['south'])
    x2, y2 = transformer.transform(bbox['east'], bbox['north'])
    ax.set_xlim(x1, x2)
    ax.set_ylim(y1, y2)
    
    # Add basemap
    ctx.add_basemap(
        ax,
        source=ctx.providers.CartoDB.Positron,
        alpha=0.6
    )
    
    # Add county labels for those with stores
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
    
    # Save figure
    plt.savefig('walmart_density.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Load data
    counties, walmart_locations, bbox = load_data()
    
    # Create maps
    create_overview_map(counties, walmart_locations, bbox)
    create_density_map(counties, walmart_locations, bbox)
    
    print("Maps have been created:")
    print("1. study_area_overview.png - Shows Walmart locations by type")
    print("2. walmart_density.png - Shows Walmart store distribution by county")
    
    # Print some statistics about the data
    print("\nWalmart location statistics:")
    print(f"Total locations: {len(walmart_locations)}")
    print("\nLocations by service type:")
    for service in walmart_locations['services'].unique():
        count = walmart_locations[walmart_locations['services'] == service].shape[0]
        print(f"{service}: {count}")

if __name__ == "__main__":
    main() 