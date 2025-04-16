import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
import json

def create_dodge_city_walmart_map():
    """
    Creates a map centered on the Walmart in Dodge City, KS, showing the entire Ford County.
    Uses OpenStreetMap as the basemap.
    """
    print("Creating map of Dodge City, KS Walmart...")
    
    # Load county boundaries
    counties = gpd.read_file('data/county_boundaries.geojson')
    
    # Filter to get only Ford County, KS
    ford_county = counties[counties['NAME'] == 'Ford County']
    if ford_county.empty:
        print("Error: Ford County not found in county boundaries data")
        return
    
    # Load Walmart locations
    walmart_df = pd.read_csv('output/walmart_locations/walmart_locations_consolidated_county_filtered.csv')
    
    # Filter to get only the Walmart in Dodge City, KS
    dodge_city_walmart = walmart_df[(walmart_df['city'] == 'Dodge City') & (walmart_df['state'] == 'KS')]
    if dodge_city_walmart.empty:
        print("Error: Dodge City Walmart not found in Walmart locations data")
        return
    
    # Create GeoDataFrame for Walmart location
    walmart_gdf = gpd.GeoDataFrame(
        dodge_city_walmart, 
        geometry=gpd.points_from_xy(dodge_city_walmart.lon, dodge_city_walmart.lat),
        crs="EPSG:4326"
    )
    
    # Convert to Web Mercator for basemap
    ford_county_web = ford_county.to_crs(epsg=3857)
    walmart_web = walmart_gdf.to_crs(epsg=3857)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot county boundary with thicker line
    ford_county_web.plot(
        ax=ax,
        alpha=0.2,
        edgecolor='black',
        linewidth=2,
        facecolor='lightgray'
    )
    
    # Plot Walmart location
    walmart_web.plot(
        ax=ax,
        color='red',
        markersize=150,
        marker='*',
        edgecolor='white',
        linewidth=1,
        label='Walmart Supercenter'
    )
    
    # Set extent to show the entire county
    # Adding a small buffer (5%) to make sure the entire county is visible
    bounds = ford_county_web.geometry.total_bounds
    buffer_x = (bounds[2] - bounds[0]) * 0.05
    buffer_y = (bounds[3] - bounds[1]) * 0.05
    ax.set_xlim(bounds[0] - buffer_x, bounds[2] + buffer_x)
    ax.set_ylim(bounds[1] - buffer_y, bounds[3] + buffer_y)
    
    # Add OpenStreetMap basemap
    ctx.add_basemap(
        ax,
        source=ctx.providers.OpenStreetMap.Mapnik,
        zoom=11
    )
    
    # Add store information as annotation
    store_info = dodge_city_walmart.iloc[0]
    store_addr = f"{store_info['address']}, {store_info['city']}, {store_info['state']} {store_info['postcode']}"
    ax.annotate(
        f"Walmart Supercenter\n{store_addr}\nPhone: {store_info['phone']}",
        xy=(walmart_web.geometry.iloc[0].x, walmart_web.geometry.iloc[0].y),
        xytext=(40, 20),
        textcoords="offset points",
        fontsize=10,
        color='black',
        bbox=dict(facecolor='white', edgecolor='black', alpha=0.8, pad=1)
    )
    
    # Add title and legend
    plt.title('Dodge City Walmart and Ford County, KS', fontsize=16, pad=20)
    ax.legend(fontsize=12, loc='upper right')
    
    # Add county name
    county_centroid = ford_county_web.geometry.iloc[0].centroid
    ax.annotate(
        'FORD COUNTY',
        xy=(county_centroid.x, county_centroid.y),
        xytext=(0, 0),
        textcoords="offset points",
        fontsize=14,
        color='darkblue',
        alpha=0.7,
        ha='center',
        weight='bold'
    )
    
    # Create output directory if it doesn't exist
    output_dir = Path('output/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the map
    output_file = 'output/maps/dodge_city_walmart_map.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Map saved to {output_file}")

if __name__ == "__main__":
    create_dodge_city_walmart_map() 