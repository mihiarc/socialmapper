import os
import requests
import pandas as pd
import geopandas as gpd
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np
import matplotlib.patches as mpatches

# Load environment variables from .env file (if using)
load_dotenv()

# Census API key
API_KEY = os.getenv('CENSUS_API_KEY')  # Ensure 'CENSUS_API_KEY' is set in your environment

def fetch_census_blockgroup_data(state_code='20'):
    """
    Fetch Census block group data for the specified state.
    
    Args:
        state_code (str): State FIPS code (default: '20' for Kansas)
        
    Returns:
        pandas.DataFrame: Census block group data with population and demographics
    """
    if not API_KEY:
        raise ValueError("Census API key not found. Please set the 'CENSUS_API_KEY' environment variable.")
    
    # Define the API endpoint
    year = 2021  # ACS 5-Year Estimates year
    dataset = 'acs/acs5'
    base_url = f'https://api.census.gov/data/{year}/{dataset}'
    
    # Define the variables to retrieve
    # B01003_001E: Total population
    # B19013_001E: Median household income
    # B25044_003E: No vehicle available (owner-occupied)
    # B25044_010E: No vehicle available (renter-occupied)
    # B01001_001E: Total population by age and sex
    variables = [
        'B01003_001E',  # Total population
        'B19013_001E',  # Median household income
        'B25044_003E',  # No vehicle available (owner-occupied)
        'B25044_010E',  # No vehicle available (renter-occupied)
        'NAME'          # Block Group name
    ]
    
    print(f"Fetching Census data for state {state_code}...")
    
    # Define the parameters for this state
    params = {
        'get': ','.join(variables),
        'for': 'block group:*',
        'in': f'state:{state_code} county:* tract:*',
        'key': API_KEY
    }
    
    # Make the API request
    response = requests.get(base_url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        
        # Convert to DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Rename columns for clarity
        df.rename(columns={
            'B01003_001E': 'Total_Population',
            'B19013_001E': 'Median_Income',
            'B25044_003E': 'Owner_No_Vehicle',
            'B25044_010E': 'Renter_No_Vehicle',
            'NAME': 'Block_Group_Name',
            'state': 'State_FIPS',
            'county': 'County_FIPS',
            'tract': 'Tract_Code',
            'block group': 'Block_Group_Number'
        }, inplace=True)
        
        # Convert numeric columns, handle missing or non-numeric data
        for col in ['Total_Population', 'Median_Income', 'Owner_No_Vehicle', 'Renter_No_Vehicle']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Create a unique identifier for each Block Group
        df['Block_Group_ID'] = df['State_FIPS'] + df['County_FIPS'] + df['Tract_Code'] + df['Block_Group_Number']
        
        # Create a total no-vehicle household count
        df['Total_No_Vehicle'] = df['Owner_No_Vehicle'] + df['Renter_No_Vehicle']
        
        # Create output directory if it doesn't exist
        output_dir = Path('output/census')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        output_file = 'output/census/block_groups_data.csv'
        df.to_csv(output_file, index=False)
        print(f"Census data saved to '{output_file}'")
        
        return df
    else:
        print(f"Error fetching data: {response.status_code}")
        print(response.text)
        return None

def fetch_tiger_blockgroups(state_code='20', county_fips=None):
    """
    Fetch TIGER/Line block group geometries for the specified state and county.
    
    Args:
        state_code (str): State FIPS code (default: '20' for Kansas)
        county_fips (str, optional): County FIPS code, if None, fetches all counties
        
    Returns:
        geopandas.GeoDataFrame: Block group boundaries
    """
    print("Fetching TIGER/Line block group geometries...")
    
    # Base URL for Census TIGER/Line web service
    tiger_url = f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/10/query"
    
    # Define parameters
    county_filter = f" AND COUNTYFP = '{county_fips}'" if county_fips else ""
    where_clause = f"STATEFP = '{state_code}'{county_filter}"
    
    params = {
        'where': where_clause,
        'outFields': '*',
        'geometryPrecision': 6,
        'outSR': '4326',  # WGS84
        'f': 'geojson'
    }
    
    # Make the API request
    response = requests.get(tiger_url, params=params)
    
    if response.status_code == 200:
        # Parse the GeoJSON
        tiger_data = response.json()
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(tiger_data["features"], crs="EPSG:4326")
        
        # Create GEOID (unique identifier for block groups)
        gdf['GEOID'] = gdf['STATEFP'] + gdf['COUNTYFP'] + gdf['TRACTCE'] + gdf['BLKGRPCE']
        
        # Save to file
        output_dir = Path('output/census')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = f'output/census/tiger_blockgroups_{state_code}.geojson'
        gdf.to_file(output_file, driver='GeoJSON')
        print(f"Block group geometries saved to '{output_file}'")
        
        return gdf
    else:
        print(f"Error fetching TIGER geometries: {response.status_code}")
        print(response.text)
        return None

def join_census_with_geometries(census_df, tiger_gdf):
    """
    Join Census data with TIGER/Line geometries.
    
    Args:
        census_df (pandas.DataFrame): Census data
        tiger_gdf (geopandas.GeoDataFrame): TIGER/Line geometries
        
    Returns:
        geopandas.GeoDataFrame: Joined data with geometries
    """
    print("Joining Census data with geometries...")
    
    # Prepare the join key in Census data to match TIGER GEOID
    census_df['GEOID'] = census_df['Block_Group_ID']
    
    # Perform join
    joined_gdf = tiger_gdf.merge(census_df, on='GEOID', how='inner')
    
    # Save to file
    output_file = 'output/census/census_blockgroups_with_geometry.geojson'
    joined_gdf.to_file(output_file, driver='GeoJSON')
    print(f"Joined data saved to '{output_file}'")
    
    return joined_gdf

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

def intersect_with_isochrones(census_gdf, isochrones):
    """
    Intersect Census block groups with isochrones and calculate demographics.
    
    Args:
        census_gdf (geopandas.GeoDataFrame): Census block groups with demographics
        isochrones (dict): Dictionary of isochrones keyed by travel time
        
    Returns:
        dict: Dictionary of results by travel time
    """
    print("Intersecting Census block groups with isochrones...")
    
    results = {}
    summary_stats = {}
    
    # Ensure same CRS
    census_gdf = census_gdf.to_crs("EPSG:4326")
    
    # For each isochrone
    for minutes, iso_gdf in isochrones.items():
        iso_gdf = iso_gdf.to_crs("EPSG:4326")
        
        # Perform spatial intersection
        intersection = gpd.overlay(census_gdf, iso_gdf, how='intersection')
        
        if intersection.empty:
            print(f"No intersection found for {minutes}-minute isochrone")
            continue
        
        # Calculate area proportion for partial block groups
        census_gdf['total_area'] = census_gdf.geometry.area
        intersection['intersect_area'] = intersection.geometry.area
        intersection = intersection.merge(
            census_gdf[['GEOID', 'total_area']], 
            on='GEOID', 
            how='left'
        )
        intersection['area_proportion'] = intersection['intersect_area'] / intersection['total_area']
        
        # Apply area proportion to population and other counts
        for col in ['Total_Population', 'Owner_No_Vehicle', 'Renter_No_Vehicle', 'Total_No_Vehicle']:
            if col in intersection.columns:
                intersection[f'{col}_adjusted'] = intersection[col] * intersection['area_proportion']
        
        # Calculate summary statistics
        total_pop = intersection['Total_Population_adjusted'].sum()
        total_no_vehicle = intersection['Total_No_Vehicle_adjusted'].sum()
        median_income = intersection['Median_Income'].median()  # Use median of medians as approximation
        
        summary_stats[minutes] = {
            'total_block_groups': len(intersection),
            'total_population': total_pop,
            'total_no_vehicle_households': total_no_vehicle,
            'pct_no_vehicle': (total_no_vehicle / total_pop) * 100 if total_pop > 0 else 0,
            'median_household_income': median_income
        }
        
        # Save intersection to file
        output_file = f'output/census/isochrone_{minutes}min_census_intersection.geojson'
        intersection.to_file(output_file, driver='GeoJSON')
        print(f"Intersection for {minutes}-minute isochrone saved to '{output_file}'")
        
        results[minutes] = intersection
    
    # Save summary statistics to CSV
    summary_df = pd.DataFrame.from_dict(summary_stats, orient='index')
    summary_df.index.name = 'drive_time_minutes'
    summary_df.reset_index(inplace=True)
    summary_df.to_csv('output/census/isochrone_demographic_summary.csv', index=False)
    print("Summary statistics saved to 'output/census/isochrone_demographic_summary.csv'")
    
    return results, summary_stats

def create_demographic_maps(census_gdf, isochrones, walmart_lat, walmart_lon):
    """
    Create maps showing demographic data within isochrones.
    
    Args:
        census_gdf (geopandas.GeoDataFrame): Census block groups with demographics
        isochrones (dict): Dictionary of isochrones keyed by travel time
        walmart_lat (float): Walmart latitude
        walmart_lon (float): Walmart longitude
    """
    print("Creating demographic maps...")
    
    # Ensure output directory exists
    output_dir = Path('output/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to Web Mercator for basemap
    census_web = census_gdf.to_crs(epsg=3857)
    
    # Create maps for different demographic variables
    demographic_vars = {
        'Total_Population': 'Population',
        'Median_Income': 'Median Household Income ($)',
        'Total_No_Vehicle': 'Households without Vehicles'
    }
    
    for var, title in demographic_vars.items():
        print(f"Creating map for {title}...")
        
        # Skip if variable not in data
        if var not in census_web.columns:
            print(f"Variable {var} not found in Census data")
            continue
            
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(15, 12))
        
        # Plot demographic variable
        census_web.plot(
            column=var,
            ax=ax,
            legend=True,
            cmap='viridis',
            scheme='quantiles',
            k=5,
            alpha=0.7,
            edgecolor='white',
            linewidth=0.2,
            legend_kwds={
                'title': title,
                'fmt': '{:.0f}' if var != 'Median_Income' else '${:.0f}',
                'loc': 'lower right'
            }
        )
        
        # Define colors for isochrone boundaries
        cmap = plt.cm.YlOrRd
        colors = [cmap(0.2), cmap(0.4), cmap(0.6), cmap(0.8)]
        
        # Add isochrone boundaries
        patches = []
        for i, minutes in enumerate(sorted(isochrones.keys())):
            iso_web = isochrones[minutes].to_crs(epsg=3857)
            
            # Plot isochrone boundary
            iso_web.boundary.plot(
                ax=ax,
                color=colors[i],
                linewidth=2,
                alpha=0.8
            )
            
            # Create patch for legend
            patch = mpatches.Patch(color=colors[i], alpha=0.8, label=f'{minutes} min drive')
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
            zorder=5,
            label='Walmart'
        )
        
        # Add basemap
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.Positron,
            zoom=11
        )
        
        # Add isochrone legend
        iso_legend = ax.legend(
            handles=patches,
            title="Drive Time",
            loc='upper right',
            framealpha=0.9,
            fontsize=10
        )
        
        # Add second legend for Walmart
        walmart_patch = mpatches.Patch(color='red', marker='*', label='Walmart')
        ax.add_artist(iso_legend)
        
        # Add title
        plt.title(f'{title} and Walmart Drive Times', fontsize=16, pad=20)
        
        # Save map
        output_file = f'output/maps/walmart_drivetime_{var.lower()}_map.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Map saved to '{output_file}'")

def main():
    """Main function to analyze Census data with Walmart isochrones."""
    print("Starting Walmart Census data analysis...")
    
    # Step 1: Fetch Census data
    census_df = fetch_census_blockgroup_data(state_code='20')  # Kansas
    
    # Step 2: Fetch TIGER/Line geometries
    # Optionally filter for Ford County (FIPS: '057')
    tiger_gdf = fetch_tiger_blockgroups(state_code='20', county_fips='057')
    
    # Step 3: Join Census data with geometries
    if census_df is not None and tiger_gdf is not None:
        census_gdf = join_census_with_geometries(census_df, tiger_gdf)
        
        # Step 4: Load isochrones
        isochrones = load_isochrones()
        
        if isochrones:
            # Step 5: Intersect with isochrones
            results, summary = intersect_with_isochrones(census_gdf, isochrones)
            
            # Step 6: Create demographic maps
            # Load Walmart location
            walmart_df = pd.read_csv('output/walmart_locations/walmart_locations_consolidated_county_filtered.csv')
            dodge_city_walmart = walmart_df[(walmart_df['city'] == 'Dodge City') & (walmart_df['state'] == 'KS')]
            
            if not dodge_city_walmart.empty:
                lat, lon = dodge_city_walmart.iloc[0]['lat'], dodge_city_walmart.iloc[0]['lon']
                create_demographic_maps(census_gdf, isochrones, lat, lon)
            
            # Print summary
            print("\nDemographic Summary by Drive Time:")
            for minutes, stats in summary.items():
                print(f"\n{minutes}-minute drive time zone:")
                print(f"  Total Population: {stats['total_population']:.0f}")
                print(f"  Households without Vehicles: {stats['total_no_vehicle_households']:.0f}")
                print(f"  Percent of Households without Vehicles: {stats['pct_no_vehicle']:.1f}%")
                print(f"  Median Household Income: ${stats['median_household_income']:.0f}")
    
    print("Walmart Census data analysis complete!")

if __name__ == "__main__":
    main() 