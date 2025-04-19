import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
import matplotlib.patches as mpatches
import numpy as np
import requests
import io
import zipfile

def download_zcta_shapefile():
    """
    Download and extract ZIP Code Tabulation Area (ZCTA) shapefile from Census Bureau.
    Returns:
        str: Path to the extracted shapefile directory
    """
    print("Downloading ZIP Code Tabulation Areas (ZCTA) shapefile...")
    
    # Create directory for ZIP code data
    zcta_dir = Path('data/zipcode_shapefile')
    zcta_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if files already exist
    if (zcta_dir / 'tl_2021_us_zcta520.shp').exists():
        print("ZCTA shapefile already exists, skipping download.")
        return zcta_dir
    
    # URL for 2021 ZCTA shapefile
    zcta_url = "https://www2.census.gov/geo/tiger/TIGER2021/ZCTA520/tl_2021_us_zcta520.zip"
    
    # Download the file
    print(f"Downloading from {zcta_url}...")
    response = requests.get(zcta_url, stream=True)
    
    if response.status_code == 200:
        # Save the zip file
        zip_path = zcta_dir / "zcta.zip"
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(zcta_dir)
        
        # Remove the zip file
        zip_path.unlink()
        
        print("ZCTA shapefile downloaded and extracted successfully.")
        return zcta_dir
    else:
        print(f"Failed to download ZCTA shapefile: {response.status_code}")
        return None

def load_zcta_shapefile(state_fips='20'):
    """
    Load ZIP Code Tabulation Areas (ZCTA) shapefile for the specified state.
    
    Args:
        state_fips (str): State FIPS code (default: '20' for Kansas)
        
    Returns:
        geopandas.GeoDataFrame: ZCTA boundaries for the state
    """
    print(f"Loading ZCTA shapefile for state {state_fips}...")
    
    # Path to ZCTA shapefile
    zcta_dir = Path('data/zipcode_shapefile')
    zcta_file = zcta_dir / 'tl_2021_us_zcta520.shp'
    
    # Check if directory exists
    if not zcta_dir.exists():
        zcta_dir = download_zcta_shapefile()
        if zcta_dir is None:
            return None
    
    # Check if file exists
    if not zcta_file.exists():
        print(f"ZCTA shapefile not found at {zcta_file}")
        zcta_dir = download_zcta_shapefile()
        if zcta_dir is None:
            return None
    
    # Load the shapefile
    zcta_gdf = gpd.read_file(zcta_file)
    
    # Filter for the specified state
    # ZCTA shapefile doesn't have a state field, so we need to join with a state-to-zip mapping
    # For now, we'll use a simplified approach based on ZIP code prefixes for Kansas
    
    # Kansas ZIP codes generally start with 66, 67, or 68
    # This is a simplification and might include some ZIPs from neighboring states
    # For a more accurate approach, a proper state-to-zip mapping would be needed
    if state_fips == '20':  # Kansas
        zcta_gdf['ZIP'] = zcta_gdf['ZCTA5CE20'].astype(str)
        kansas_prefixes = ['66', '67', '68']
        mask = zcta_gdf['ZIP'].str.startswith(tuple(kansas_prefixes))
        zcta_gdf = zcta_gdf[mask].copy()
    
    print(f"Loaded {len(zcta_gdf)} ZCTAs for the specified state.")
    
    # Save filtered ZCTA to file
    output_dir = Path('output/zipcode')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = f'output/zipcode/zcta_{state_fips}.geojson'
    zcta_gdf.to_file(output_file, driver='GeoJSON')
    print(f"Filtered ZCTAs saved to '{output_file}'")
    
    return zcta_gdf

def load_isochrones():
    """
    Load isochrones from GeoJSON files.
    
    Returns:
        dict: Dictionary of isochrones keyed by travel time
    """
    isochrones = {}
    isochrone_dir = Path('output/isochrones')
    
    # Check if directory exists
    if not isochrone_dir.exists():
        print("Isochrone directory not found. Please run walmart_isochrone_generator.py first.")
        return None
    
    # Look for isochrone files
    for file in isochrone_dir.glob('walmart_dodge_city_*min_isochrone.geojson'):
        # Extract minutes from filename
        filename = file.name
        minutes = int(filename.split('_')[3].replace('min', ''))
        
        # Load GeoJSON
        gdf = gpd.read_file(file)
        isochrones[minutes] = gdf
        print(f"Loaded {minutes}-minute isochrone")
    
    return isochrones

def intersect_isochrones_with_zipcodes(isochrones, zipcodes_gdf):
    """
    Intersect isochrones with ZIP code boundaries and calculate areas.
    
    Args:
        isochrones (dict): Dictionary of isochrones keyed by travel time
        zipcodes_gdf (geopandas.GeoDataFrame): ZIP code boundaries
        
    Returns:
        dict: Dictionary of results by travel time
    """
    print("Intersecting isochrones with ZIP codes...")
    
    results = {}
    intersection_data = []
    
    # Ensure same CRS
    zipcodes_gdf = zipcodes_gdf.to_crs("EPSG:4326")
    
    # Calculate total area for each ZIP code
    zipcodes_gdf['total_area'] = zipcodes_gdf.geometry.area
    
    # For each isochrone
    for minutes, iso_gdf in isochrones.items():
        iso_gdf = iso_gdf.to_crs("EPSG:4326")
        
        # Perform spatial intersection
        intersection = gpd.overlay(zipcodes_gdf, iso_gdf, how='intersection')
        
        if intersection.empty:
            print(f"No intersection found for {minutes}-minute isochrone")
            continue
        
        # Calculate intersection area
        intersection['intersect_area'] = intersection.geometry.area
        
        # Calculate area proportion
        intersection = intersection.merge(
            zipcodes_gdf[['ZCTA5CE20', 'total_area']], 
            on='ZCTA5CE20', 
            how='left'
        )
        intersection['area_proportion'] = intersection['intersect_area'] / intersection['total_area']
        
        # Add drive time column
        intersection['drive_time_minutes'] = minutes
        
        # Extract relevant columns
        result_df = intersection[['ZCTA5CE20', 'drive_time_minutes', 
                                  'total_area', 'intersect_area', 'area_proportion']]
        
        # Add to results
        results[minutes] = intersection
        intersection_data.append(result_df)
        
        # Save intersection to GeoJSON
        output_file = f'output/zipcode/isochrone_{minutes}min_zipcode_intersection.geojson'
        intersection.to_file(output_file, driver='GeoJSON')
        print(f"Intersection for {minutes}-minute isochrone saved to '{output_file}'")
    
    # Combine all results into a single DataFrame
    if intersection_data:
        all_intersections = pd.concat(intersection_data, ignore_index=True)
        all_intersections.rename(columns={'ZCTA5CE20': 'zipcode'}, inplace=True)
        
        # Create a wide-format table with each drive time as a column
        pivot_df = all_intersections.pivot(
            index='zipcode',
            columns='drive_time_minutes',
            values='area_proportion'
        ).reset_index()
        
        # Rename columns for clarity
        time_columns = [col for col in pivot_df.columns if col != 'zipcode']
        column_mapping = {col: f'pct_area_within_{col}min' for col in time_columns}
        pivot_df.rename(columns=column_mapping, inplace=True)
        
        # Fill NAs with 0 (ZIP codes not within that drive time)
        pivot_df.fillna(0, inplace=True)
        
        # Save to CSV
        output_file = 'output/zipcode/zipcode_drivetime_coverage.csv'
        pivot_df.to_csv(output_file, index=False)
        print(f"ZIP code drive time coverage saved to '{output_file}'")
        
        # Also save the detailed version
        detailed_output = 'output/zipcode/zipcode_drivetime_detail.csv'
        all_intersections.to_csv(detailed_output, index=False)
        print(f"Detailed ZIP code intersections saved to '{detailed_output}'")
        
        return results, pivot_df
    else:
        print("No intersections found")
        return None, None

def create_zipcode_map(zipcodes_gdf, isochrones, walmart_lat, walmart_lon):
    """
    Create a map showing ZIP codes and isochrones.
    
    Args:
        zipcodes_gdf (geopandas.GeoDataFrame): ZIP code boundaries
        isochrones (dict): Dictionary of isochrones keyed by travel time
        walmart_lat (float): Walmart latitude
        walmart_lon (float): Walmart longitude
    """
    print("Creating ZIP code map...")
    
    # Ensure output directory exists
    output_dir = Path('output/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to Web Mercator for basemap
    zipcodes_web = zipcodes_gdf.to_crs(epsg=3857)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Plot ZIP codes
    zipcodes_web.plot(
        ax=ax,
        edgecolor='black',
        linewidth=0.5,
        facecolor='none',
        alpha=0.6
    )
    
    # Add ZIP code labels
    for idx, row in zipcodes_web.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            text=row['ZCTA5CE20'],
            xy=(centroid.x, centroid.y),
            xytext=(0, 0),
            textcoords="offset points",
            fontsize=8,
            ha='center',
            color='black'
        )
    
    # Define colors for isochrones
    cmap = plt.cm.YlOrRd
    colors = [cmap(0.2), cmap(0.4), cmap(0.6), cmap(0.8)]
    
    # Add isochrones
    patches = []
    for i, minutes in enumerate(sorted(isochrones.keys())):
        iso_web = isochrones[minutes].to_crs(epsg=3857)
        
        # Plot with transparency
        iso_web.plot(
            ax=ax,
            color=colors[i],
            alpha=0.3,
            edgecolor=colors[i],
            linewidth=1.5
        )
        
        # Create patch for legend
        patch = mpatches.Patch(color=colors[i], alpha=0.3, label=f'{minutes} min drive')
        patches.append(patch)
    
    # Add Walmart location
    walmart_point = gpd.GeoDataFrame(
        geometry=[gpd.points_from_xy([walmart_lon], [walmart_lat], crs=4326)[0]],
        crs=4326
    ).to_crs(epsg=3857)
    
    walmart_point.plot(
        ax=ax,
        color='red',
        markersize=150,
        marker='*',
        edgecolor='white',
        linewidth=1.5,
        zorder=5
    )
    
    # Add basemap
    ctx.add_basemap(
        ax,
        source=ctx.providers.CartoDB.Positron,
        zoom=9
    )
    
    # Add legend
    ax.legend(
        handles=patches,
        title="Drive Time Zones",
        loc='upper right',
        framealpha=0.9,
        fontsize=10
    )
    
    # Set extent to show all ZIP codes
    bounds = zipcodes_web.geometry.total_bounds
    buffer_x = (bounds[2] - bounds[0]) * 0.05
    buffer_y = (bounds[3] - bounds[1]) * 0.05
    ax.set_xlim(bounds[0] - buffer_x, bounds[2] + buffer_x)
    ax.set_ylim(bounds[1] - buffer_y, bounds[3] + buffer_y)
    
    # Add title
    plt.title('ZIP Codes with Walmart Drive Time Zones', fontsize=16, pad=20)
    
    # Save map
    output_file = 'output/maps/walmart_zipcode_drivetime_map.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Map saved to '{output_file}'")
    return output_file

def main():
    """Main function to analyze ZIP code areas with Walmart isochrones."""
    print("Starting Walmart ZIP code analysis...")
    
    # Step 1: Load ZIP Code Tabulation Areas (ZCTA)
    zipcodes_gdf = load_zcta_shapefile(state_fips='20')  # Kansas
    
    if zipcodes_gdf is not None:
        # Step 2: Load isochrones
        isochrones = load_isochrones()
        
        if isochrones:
            # Step 3: Intersect isochrones with ZIP codes
            results, summary_df = intersect_isochrones_with_zipcodes(isochrones, zipcodes_gdf)
            
            if results:
                # Step 4: Create ZIP code map
                # Load Walmart location
                walmart_df = pd.read_csv('output/walmart_locations/walmart_locations_consolidated_county_filtered.csv')
                dodge_city_walmart = walmart_df[(walmart_df['city'] == 'Dodge City') & (walmart_df['state'] == 'KS')]
                
                if not dodge_city_walmart.empty:
                    lat, lon = dodge_city_walmart.iloc[0]['lat'], dodge_city_walmart.iloc[0]['lon']
                    create_zipcode_map(zipcodes_gdf, isochrones, lat, lon)
                
                # Step 5: Print summary
                print("\nZIP Code Coverage Summary:")
                for minutes in sorted(results.keys()):
                    coverage = results[minutes]
                    zips_count = len(coverage['ZCTA5CE20'].unique())
                    full_coverage = coverage[coverage['area_proportion'] > 0.99]
                    full_zips_count = len(full_coverage['ZCTA5CE20'].unique())
                    
                    print(f"\n{minutes}-minute drive time zone:")
                    print(f"  Total ZIP codes intersected: {zips_count}")
                    print(f"  ZIP codes with >99% coverage: {full_zips_count}")
                    if zips_count > 0:
                        print(f"  ZIP codes: {', '.join(coverage['ZCTA5CE20'].unique())}")
    
    print("Walmart ZIP code analysis complete!")

if __name__ == "__main__":
    main() 