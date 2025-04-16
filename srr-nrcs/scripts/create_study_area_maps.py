import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import contextily as ctx

def load_data() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Load and prepare the county boundaries and Walmart locations."""
    # Load county boundaries
    counties = gpd.read_file('county_boundaries.geojson')
    
    # Load Walmart locations
    walmarts = pd.read_csv('walmart_stores_bbox.csv')
    walmarts = gpd.GeoDataFrame(
        walmarts, 
        geometry=gpd.points_from_xy(walmarts.lon, walmarts.lat),
        crs="EPSG:4326"
    )
    
    return counties, walmarts

def create_overview_map(counties: gpd.GeoDataFrame, walmarts: gpd.GeoDataFrame, output_file: str = 'study_area_overview.png'):
    """Create an overview map of the study area with counties and Walmart locations."""
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Project to Web Mercator for basemap compatibility
    counties_proj = counties.to_crs(epsg=3857)
    walmarts_proj = walmarts.to_crs(epsg=3857)
    
    # Plot counties
    counties_proj.plot(ax=ax, alpha=0.5, edgecolor='black', facecolor='none', linewidth=1)
    
    # Plot Walmart locations
    walmarts_proj.plot(ax=ax, color='red', markersize=20, alpha=0.6, marker='o', label='Walmart')
    
    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.Stamen.TerrainBackground)
    
    # Customize the map
    ax.set_title('Study Area Overview: Counties and Walmart Locations', fontsize=16, pad=20)
    ax.legend(fontsize=12)
    
    # Add scale bar and north arrow (simplified)
    ax.text(0.02, 0.02, '↑N', transform=ax.transAxes, fontsize=14, fontweight='bold')
    
    # Save the map
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Overview map saved to {output_file}")

def create_density_map(counties: gpd.GeoDataFrame, walmarts: gpd.GeoDataFrame, output_file: str = 'walmart_density.png'):
    """Create a map showing Walmart density by county."""
    # Project to Web Mercator
    counties_proj = counties.to_crs(epsg=3857)
    walmarts_proj = walmarts.to_crs(epsg=3857)
    
    # Count Walmarts per county
    points_in_polygons = gpd.sjoin(walmarts_proj, counties_proj, how='right', predicate='within')
    walmart_counts = points_in_polygons.groupby('GEOID').size().fillna(0)
    counties_proj['walmart_count'] = counties_proj['GEOID'].map(walmart_counts)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot county density
    counties_proj.plot(
        column='walmart_count',
        ax=ax,
        legend=True,
        legend_kwds={'label': 'Number of Walmart Stores'},
        cmap='YlOrRd',
        missing_kwds={'color': 'lightgrey'}
    )
    
    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.Stamen.TerrainBackground)
    
    # Customize the map
    ax.set_title('Walmart Store Density by County', fontsize=16, pad=20)
    
    # Add county labels for those with stores
    for idx, row in counties_proj[counties_proj['walmart_count'] > 0].iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            text=f"{row['NAME']}\n({int(row['walmart_count'])})",
            xy=(centroid.x, centroid.y),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=8,
            color='black',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5)
        )
    
    # Save the map
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Density map saved to {output_file}")

def main():
    """Create all study area maps."""
    # Check if required files exist
    required_files = ['county_boundaries.geojson', 'walmart_stores_bbox.csv']
    for file in required_files:
        if not Path(file).exists():
            print(f"Error: Required file {file} not found!")
            return
    
    # Load data
    print("Loading data...")
    counties, walmarts = load_data()
    
    # Create maps
    print("\nCreating overview map...")
    create_overview_map(counties, walmarts)
    
    print("\nCreating density map...")
    create_density_map(counties, walmarts)
    
    print("\nAll maps created successfully!")

if __name__ == "__main__":
    main() 