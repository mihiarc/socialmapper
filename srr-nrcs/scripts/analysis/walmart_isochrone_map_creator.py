import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import contextily as ctx
from shapely.geometry import Point
from pathlib import Path

def load_isochrones(output_dir='output/isochrones'):
    """
    Load all isochrone files into a dictionary.
    
    Args:
        output_dir (str): Directory containing isochrone files
        
    Returns:
        dict: Dictionary of isochrones keyed by travel time
    """
    print("Loading isochrones...")
    
    isochrones = {}
    isochrone_dir = Path(output_dir)
    
    # Check if directory exists
    if not isochrone_dir.exists():
        print("Isochrone directory not found.")
        return None
    
    # Look for isochrone files
    for file in isochrone_dir.glob('walmart_dodge_city_*min_isochrone.geojson'):
        # Extract minutes from filename
        filename = file.name
        minutes = int(filename.split('_')[3].replace('min', ''))
        
        # Load GeoJSON
        try:
            gdf = gpd.read_file(file)
            isochrones[minutes] = gdf
            print(f"Loaded {minutes}-minute isochrone from {file}")
        except Exception as e:
            print(f"Error loading {file}: {str(e)}")
    
    if not isochrones:
        print("No isochrone files found.")
        return None
        
    print(f"Loaded {len(isochrones)} isochrones: {sorted(isochrones.keys())}")
    return isochrones

def load_walmart_location():
    """Load the Walmart location in Dodge City, KS from the CSV file."""
    print("Loading Walmart location data...")
    
    # Load Walmart locations
    walmart_df = pd.read_csv('output/walmart_locations/walmart_locations_consolidated_county_filtered.csv')
    
    # Filter to get only the Walmart in Dodge City, KS
    dodge_city_walmart = walmart_df[(walmart_df['city'] == 'Dodge City') & (walmart_df['state'] == 'KS')]
    
    if dodge_city_walmart.empty:
        raise ValueError("Dodge City Walmart not found in the dataset")
    
    # Extract store information
    store_info = dodge_city_walmart.iloc[0]
    lat, lon = store_info['lat'], store_info['lon']
    name = store_info['name']
    address = f"{store_info['address']}, {store_info['city']}, {store_info['state']} {store_info['postcode']}"
    
    print(f"Found Walmart at: {address}")
    print(f"Coordinates: ({lat}, {lon})")
    
    return lat, lon, name, address

def create_isochrone_map(isochrones, lat, lon, store_name, address, county_name='Ford County'):
    """Create a map visualization of the isochrones."""
    print("Creating isochrone map...")
    
    # First, let's save individual isochrones to check they're loading properly
    output_dir = Path('output/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check each isochrone's shape
    for minutes, iso in isochrones.items():
        print(f"Isochrone {minutes} min details:")
        print(f"  Shape: {iso.shape}")
        print(f"  Bounds: {iso.total_bounds}")
        # Check geometry type 
        print(f"  Geometry type: {iso.geometry.iloc[0].geom_type}")
        # Save individual isochrone for debugging
        fig, ax = plt.subplots(figsize=(10, 8))
        iso.plot(ax=ax, color='red')
        plt.title(f"{minutes}-minute isochrone")
        plt.savefig(f"output/maps/debug_{minutes}min_isochrone.png")
        plt.close()
        print(f"  Saved debug map to output/maps/debug_{minutes}min_isochrone.png")
    
    # Create figure and axis for main map
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Define completely different visual styles for each isochrone
    # Larger isochrones should be more transparent
    styles = {
        15: {'color': '#FF0000', 'alpha': 0.8, 'edgecolor': 'black', 'linewidth': 2.0, 'zorder': 10},  # Red, most visible
        30: {'color': '#FF9900', 'alpha': 0.7, 'edgecolor': 'black', 'linewidth': 1.5, 'zorder': 9},   # Orange
        45: {'color': '#FFCC00', 'alpha': 0.6, 'edgecolor': 'black', 'linewidth': 1.0, 'zorder': 8},   # Yellow
        60: {'color': '#8BB0DD', 'alpha': 0.4, 'edgecolor': 'black', 'linewidth': 0.8, 'zorder': 7}    # Light blue, least visible
    }
    
    # Plot isochrones from largest to smallest (REVERSE order)
    # This ensures smaller isochrones are drawn on top of larger ones
    sorted_times = sorted(isochrones.keys(), reverse=True)
    patches = []
    
    print(f"Plotting isochrones in reverse order: {sorted_times}")
    
    # First pass: Draw only the large isochrones with fill
    for minutes in sorted_times:
        if minutes > 15:  # Only plot the larger isochrones first
            print(f"First pass: Plotting {minutes}-minute isochrone")
            
            # Convert to web mercator
            iso_web = isochrones[minutes].to_crs(epsg=3857)
            
            # Plot with appropriate style from dictionary
            style = styles[minutes]
            iso_web.plot(
                ax=ax,
                color=style['color'],
                alpha=style['alpha'],
                edgecolor=style['edgecolor'],
                linewidth=style['linewidth'],
                zorder=style['zorder']
            )
    
    # Second pass: Draw the small isochrones (especially 15-min)
    for minutes in sorted(isochrones.keys()):
        if minutes <= 15:  # Only plot the smallest isochrones in second pass
            print(f"Second pass: Plotting {minutes}-minute isochrone")
            
            # Convert to web mercator
            iso_web = isochrones[minutes].to_crs(epsg=3857)
            
            # Plot with appropriate style from dictionary
            style = styles[minutes]
            iso_web.plot(
                ax=ax,
                color=style['color'],
                alpha=style['alpha'],
                edgecolor=style['edgecolor'],
                linewidth=style['linewidth'],
                zorder=style['zorder']
            )
    
    # Create legend patches
    for minutes in sorted(isochrones.keys()):
        style = styles[minutes]
        patch = mpatches.Patch(
            color=style['color'],
            alpha=style['alpha'],
            edgecolor=style['edgecolor'],
            linewidth=style['linewidth'],
            label=f'{minutes} min'
        )
        patches.append(patch)
    
    # Add Walmart location as a point - make it very prominent
    walmart_point = gpd.GeoDataFrame(
        geometry=[Point(lon, lat)],
        crs='EPSG:4326'
    ).to_crs(epsg=3857)
    
    walmart_point.plot(
        ax=ax,
        color='white',
        markersize=250,
        marker='*',
        edgecolor='black',
        linewidth=2.5,
        zorder=100  # Make sure it's on top
    )
    
    # Add store information
    center_point = walmart_point.geometry.iloc[0]
    ax.annotate(
        f"Walmart Supercenter\n{address}",
        xy=(center_point.x, center_point.y),
        xytext=(40, 20),
        textcoords="offset points",
        fontsize=12,
        color='black',
        bbox=dict(facecolor='white', edgecolor='black', alpha=0.9, pad=1.5),
        zorder=101
    )
    
    # Set extent based on the largest isochrone with extra buffer
    if sorted_times:
        # Use the largest isochrone as the extent
        largest_iso = isochrones[max(sorted_times)].to_crs(epsg=3857)
        bounds = largest_iso.geometry.total_bounds
        
        # Add a much larger buffer (50%) to ensure all isochrones are visible
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        buffer_x = width * 0.5
        buffer_y = height * 0.5
        
        ax.set_xlim(bounds[0] - buffer_x, bounds[2] + buffer_x)
        ax.set_ylim(bounds[1] - buffer_y, bounds[3] + buffer_y)
    
    # Try to add OpenStreetMap basemap but make it optional
    try:
        print("Attempting to add basemap from OpenStreetMap...")
        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik,
            zoom=10  # Force a specific zoom level
        )
        print("Successfully added basemap")
    except Exception as e:
        print(f"Warning: Could not add basemap: {str(e)}")
        print("Continuing without basemap")
        # Add light gray background to make it easier to see the isochrones
        ax.set_facecolor('#f0f0f0')
        # Add gridlines for better orientation
        ax.grid(color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    
    # Add legend with improved styling
    ax.legend(
        handles=patches,
        title="Drive Time Zones",
        loc='lower right',
        framealpha=1.0,
        fontsize=12,
        title_fontsize=14
    )
    
    # Add title
    plt.title(f'Dodge City Walmart Drive Time Zones', fontsize=16, pad=20)
    
    # Save map
    output_file = 'output/maps/walmart_dodge_city_isochrones.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save a map without basemap for debugging
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Replot each isochrone in the debug map
    for minutes in sorted_times:
        iso_web = isochrones[minutes].to_crs(epsg=3857)
        style = styles[minutes]
        
        iso_web.plot(
            ax=ax,
            color=style['color'],
            alpha=style['alpha'] + 0.2,  # Make slightly more visible for debug map
            edgecolor=style['edgecolor'],
            linewidth=style['linewidth'],
            zorder=style['zorder']
        )
    
    # Add Walmart location
    walmart_point.plot(
        ax=ax,
        color='white',
        markersize=250,
        marker='*',
        edgecolor='black',
        linewidth=2.5,
        zorder=100
    )
    
    plt.title('Isochrones Without Basemap (Debug)')
    plt.savefig('output/maps/debug_isochrones_no_basemap.png')
    plt.close()
    
    print(f"Main map saved to {output_file}")
    print(f"Debug map without basemap saved to output/maps/debug_isochrones_no_basemap.png")
    return output_file

def main():
    """Main function to create isochrone map."""
    print("Starting Walmart isochrone map creation...")
    
    # Load isochrones
    isochrones = load_isochrones()
    
    if not isochrones:
        print("No isochrones found. Please run the isochrone generator first.")
        return
    
    # Load Walmart location
    lat, lon, store_name, address = load_walmart_location()
    
    # Create isochrone map
    create_isochrone_map(isochrones, lat, lon, store_name, address)
    
    print("Walmart isochrone map creation complete!")

if __name__ == "__main__":
    main() 