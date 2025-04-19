import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import argparse
from typing import List, Dict, Set, Tuple
from scripts.core.config import Config
import matplotlib.pyplot as plt

def load_raw_locations(config: Config) -> pd.DataFrame:
    """
    Load the raw Walmart locations data.
    
    Args:
        config: Configuration object for path management
    """
    input_file = Path(config.get_path('data.output.analysis')) / 'walmart_stores_bbox.csv'
    return pd.read_csv(input_file)

def load_county_boundaries(config: Config) -> gpd.GeoDataFrame:
    """
    Load the county boundaries GeoJSON file.
    
    Args:
        config: Configuration object for path management
    """
    boundaries_file = Path(config.get_path('data.input.county_data')) / 'county_boundaries.geojson'
    return gpd.read_file(boundaries_file)

def filter_by_county_intersection(df: pd.DataFrame, counties: gpd.GeoDataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Filter Walmart locations to only those that intersect with the counties in our study area.
    
    Args:
        df: DataFrame containing Walmart locations with lat/lon coordinates
        counties: GeoDataFrame containing county boundaries
    
    Returns:
        Tuple containing (filtered DataFrame, count of locations filtered out)
    """
    # Create a GeoDataFrame from the Walmart locations
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.lon, df.lat),
        crs="EPSG:4326"
    )
    
    # Ensure both GeoDataFrames have the same CRS
    if counties.crs != gdf.crs:
        counties = counties.to_crs(gdf.crs)
    
    # Create a spatial index for faster intersection testing
    counties_sindex = counties.sindex
    
    # Function to check if a point is within any county
    def is_within_county(point):
        possible_matches_idx = list(counties_sindex.intersection(point.bounds))
        if not possible_matches_idx:
            return False
        possible_matches = counties.iloc[possible_matches_idx]
        return any(possible_matches.contains(point))
    
    # Apply filter to keep only points within counties
    within_county = gdf.geometry.apply(is_within_county)
    filtered_gdf = gdf[within_county]
    
    # Convert back to DataFrame (remove geometry column)
    filtered_df = pd.DataFrame(filtered_gdf.drop(columns='geometry'))
    
    # Return filtered DataFrame and count of filtered out locations
    return filtered_df, len(df) - len(filtered_df)

def extract_services_from_name(name: str) -> Set[str]:
    """Extract service types from the Walmart location name."""
    name = name.lower()
    services = set()
    
    # Define service keywords to look for
    service_keywords = {
        'supercenter': 'Supercenter',
        'neighborhood market': 'Neighborhood Market',
        'pharmacy': 'Pharmacy',
        'fuel': 'Fuel Station',
        'gas': 'Fuel Station',
        'grocery': 'Grocery',
        'vision': 'Vision Center',
        'auto': 'Auto Care',
        'care center': 'Auto Care',
        'money': 'Money Services'
    }
    
    # Special case: if name starts with "neighborhood" it's a Neighborhood Market
    if name.startswith('neighborhood'):
        services.add('Neighborhood Market')
    
    # Check for each service keyword in the name
    for keyword, service in service_keywords.items():
        if keyword in name:
            services.add(service)
    
    # If no specific services found, assume it's a general store
    if not services:
        services.add('General Store')
    
    return services

def are_same_location(lat1: float, lon1: float, lat2: float, lon2: float, threshold_km: float = 0.1) -> bool:
    """
    Check if two lat/lon pairs represent the same location within a threshold.
    Default threshold is 100 meters (0.1 km).
    """
    # Convert lat/lon difference to approximate distance in km
    # This is a simplified calculation that works well enough for small distances
    lat_diff_km = abs(lat1 - lat2) * 111  # 1 degree lat ≈ 111 km
    lon_diff_km = abs(lon1 - lon2) * 111 * np.cos(np.radians((lat1 + lat2) / 2))  # Adjust for latitude
    
    return (lat_diff_km**2 + lon_diff_km**2)**0.5 <= threshold_km

def consolidate_locations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Consolidate Walmart locations that are physically the same place.
    Returns a new DataFrame with consolidated locations and their services.
    """
    # Sort by latitude to optimize the comparison process
    df = df.sort_values('lat')
    
    # Initialize lists to store consolidated data
    consolidated_data = []
    processed_indices = set()
    
    for i in range(len(df)):
        if i in processed_indices:
            continue
            
        row = df.iloc[i]
        same_location_indices = {i}
        services = extract_services_from_name(row['name'])
        
        # Look for other locations within threshold distance
        for j in range(i + 1, len(df)):
            if j in processed_indices:
                continue
                
            other_row = df.iloc[j]
            
            # Break inner loop if we've moved too far in latitude
            if abs(other_row['lat'] - row['lat']) * 111 > 0.1:  # More than 100m in latitude
                break
            
            if are_same_location(row['lat'], row['lon'], 
                               other_row['lat'], other_row['lon']):
                same_location_indices.add(j)
                services.update(extract_services_from_name(other_row['name']))
        
        # Create consolidated record
        consolidated_record = row.to_dict()
        consolidated_record['services'] = '; '.join(sorted(services))
        consolidated_record['original_names'] = '; '.join(
            df.iloc[list(same_location_indices)]['name'].tolist()
        )
        consolidated_record['location_count'] = len(same_location_indices)
        
        consolidated_data.append(consolidated_record)
        processed_indices.update(same_location_indices)
    
    # Create new DataFrame with consolidated records
    result_df = pd.DataFrame(consolidated_data)
    
    # Reorder columns to put new fields in a logical place
    cols = ['name', 'original_names', 'services', 'location_count',
            'brand', 'state', 'city', 'address', 'postcode',
            'lat', 'lon', 'phone', 'website', 'opening_hours', 'type', 'id']
    
    return result_df[cols]

def main():
    # Initialize configuration
    config = Config()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process Walmart locations data')
    parser.add_argument('--filter-by-counties', action='store_true', 
                        help='Filter locations to only those within study area counties')
    args = parser.parse_args()
    
    # Load raw data
    print("Loading Walmart locations...")
    raw_df = load_raw_locations(config)
    print(f"Loaded {len(raw_df)} raw location records")
    
    # Filter by county boundaries if requested
    if args.filter_by_counties:
        print("\nFiltering locations by county boundaries...")
        counties = load_county_boundaries(config)
        raw_df, filtered_count = filter_by_county_intersection(raw_df, counties)
        print(f"Filtered out {filtered_count} locations outside study area counties")
        print(f"Kept {len(raw_df)} locations within study area counties")
    
    # Process and consolidate locations
    print("\nConsolidating locations...")
    consolidated_df = consolidate_locations(raw_df)
    print(f"Consolidated to {len(consolidated_df)} unique locations")
    
    # Get output directory from config
    output_dir = Path(config.get_path('data.output.analysis'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    output_suffix = "_county_filtered" if args.filter_by_counties else ""
    output_file = output_dir / f'walmart_locations_consolidated{output_suffix}.csv'
    consolidated_df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    # Print summary statistics
    print("\nSummary of consolidated locations:")
    print("\nLocations by state:")
    print(consolidated_df.groupby('state')['name'].count())
    
    print("\nService types found:")
    all_services = set()
    for services in consolidated_df['services'].str.split('; '):
        all_services.update(services)
    for service in sorted(all_services):
        count = consolidated_df[consolidated_df['services'].str.contains(service)].shape[0]
        print(f"{service}: {count}")

if __name__ == "__main__":
    main() 