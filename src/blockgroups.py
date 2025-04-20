#!/usr/bin/env python3
"""
Module to find census block groups that intersect with isochrones.
"""
import os
import argparse
import geopandas as gpd
from pathlib import Path
import pandas as pd
import requests
from shapely.geometry import shape
from typing import List, Optional

def get_census_block_groups(
    state_fips: List[str],
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Fetch census block group boundaries for specified states.
    
    Args:
        state_fips: List of state FIPS codes or abbreviations
        api_key: Census API key (optional if using cached data)
        
    Returns:
        GeoDataFrame with block group boundaries
    """
    # Map of state abbreviations to FIPS codes
    state_abbr_to_fips = {
        'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 'CT': '09',
        'DE': '10', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18',
        'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24', 'MA': '25',
        'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32',
        'NH': '33', 'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
        'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47',
        'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55',
        'WY': '56', 'DC': '11'
    }
    
    # Convert any state abbreviations to FIPS codes
    normalized_state_fips = []
    for state in state_fips:
        if state in state_abbr_to_fips:
            normalized_state_fips.append(state_abbr_to_fips[state])
        else:
            # Assume it's already a FIPS code
            normalized_state_fips.append(state)
    
    # Check for cached block group data
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Try to load all states from cache
    cached_gdfs = []
    all_cached = True
    
    for state in normalized_state_fips:
        cache_file = cache_dir / f"block_groups_{state}.geojson"
        if cache_file.exists():
            try:
                cached_gdfs.append(gpd.read_file(cache_file))
                print(f"Loaded cached block groups for state {state}")
            except Exception as e:
                print(f"Error loading cache for state {state}: {e}")
                all_cached = False
                break
        else:
            all_cached = False
            break
    
    # If all states were cached, return combined data
    if all_cached and cached_gdfs:
        return pd.concat(cached_gdfs, ignore_index=True)
    
    # If not all states were cached or there was an error, fetch from Census API
    api_key = os.getenv('CENSUS_API_KEY')

    if api_key:
        print("Using Census API key from environment variable")
    else:
        print("No Census API key found in environment variables.")
    
    # We'll use the Census Bureau's TIGER/Line API to get block group geometries
    base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/8/query"
    
    all_block_groups = []
    
    for state in normalized_state_fips:
        print(f"Fetching block groups for state {state}...")
        
        params = {
            'where': f"STATE='{state}'",
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'geojson'
        }
        
        # Add the API key to the request parameters
        if api_key:
            params['token'] = api_key
        
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            response_json = response.json()
            
            # Check if the response has features with geometry
            if 'features' in response_json and response_json['features']:
                gdf = gpd.GeoDataFrame.from_features(response_json['features'], crs="EPSG:4326")
                gdf['STATE'] = state
                
                # Save to cache
                cache_file = cache_dir / f"block_groups_{state}.geojson"
                gdf.to_file(cache_file, driver="GeoJSON")
                print(f"Saved block groups for state {state} to cache")
                
                all_block_groups.append(gdf)
            else:
                print(f"Error: No block group features found for state {state}")
        else:
            print(f"Error fetching block groups for state {state}: {response.status_code}")
            print(response.text)
    
    if not all_block_groups:
        raise ValueError("No block group data could be retrieved.")
    
    return pd.concat(all_block_groups, ignore_index=True)

def load_isochrone(isochrone_path: str) -> gpd.GeoDataFrame:
    """
    Load an isochrone file.
    
    Args:
        isochrone_path: Path to the isochrone GeoJSON file
        
    Returns:
        GeoDataFrame containing the isochrone
    """
    try:
        isochrone_gdf = gpd.read_file(isochrone_path)
        if isochrone_gdf.crs is None:
            isochrone_gdf.set_crs("EPSG:4326", inplace=True)
        return isochrone_gdf
    except Exception as e:
        raise ValueError(f"Error loading isochrone file: {e}")

def find_intersecting_block_groups(
    isochrone_gdf: gpd.GeoDataFrame,
    block_groups_gdf: gpd.GeoDataFrame,
    predicate: str = "intersects"
) -> gpd.GeoDataFrame:
    """
    Find census block groups that intersect with the isochrone.
    
    Args:
        isochrone_gdf: GeoDataFrame containing the isochrone
        block_groups_gdf: GeoDataFrame containing block group boundaries
        
    Returns:
        GeoDataFrame with intersecting block groups
    """
    # Make sure CRS match
    if isochrone_gdf.crs != block_groups_gdf.crs:
        block_groups_gdf = block_groups_gdf.to_crs(isochrone_gdf.crs)
    
    # Find which block groups intersect with the isochrone
    intersection = gpd.sjoin(block_groups_gdf, isochrone_gdf, how="inner", predicate="intersects")
    
    # For partially intersecting block groups, we can calculate the intersection geometry
    intersected_geometries = []
    
    for idx, row in intersection.iterrows():
        block_geom = row.geometry
        isochrone_geom = isochrone_gdf.loc[isochrone_gdf.index == row.index_right, "geometry"].iloc[0]
        intersection_geom = block_geom.intersection(isochrone_geom)
        intersected_geometries.append({
            "GEOID": row.GEOID if "GEOID" in row else row.BLKGRP,
            "STATE": row.STATE,
            "COUNTY": row.COUNTY,
            "TRACT": row.TRACT,
            "BLKGRP": row.BLKGRP if "BLKGRP" in row else row.GEOID[-1],
            "geometry": intersection_geom,
            "poi_id": row.poi_id,
            "poi_name": row.poi_name,
            "travel_time_minutes": row.travel_time_minutes,
            "intersection_area_pct": intersection_geom.area / block_geom.area * 100
        })
    
    # Create new GeoDataFrame with intersected geometries
    result_gdf = gpd.GeoDataFrame(intersected_geometries, crs=isochrone_gdf.crs)
    
    return result_gdf

def isochrone_to_block_groups(
    isochrone_path: str,
    state_fips: List[str],
    output_path: Optional[str] = None,
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Main function to find census block groups intersecting with an isochrone.
    
    Args:
        isochrone_path: Path to isochrone GeoJSON file
        state_fips: List of state FIPS codes to fetch block groups for
        output_path: Path to save result GeoJSON (defaults to output/blockgroups/[filename].geojson)
        api_key: Census API key (optional if using cached data)
        
    Returns:
        GeoDataFrame with intersecting block groups
    """
    # Load the isochrone
    isochrone_gdf = load_isochrone(isochrone_path)
    
    # Get block groups for requested states
    block_groups_gdf = get_census_block_groups(state_fips, api_key)
    
    # Find intersecting block groups
    result_gdf = find_intersecting_block_groups(isochrone_gdf, block_groups_gdf)
    
    # Generate default output path if none provided
    if output_path is None:
        # Extract filename from isochrone path without extension
        isochrone_name = Path(isochrone_path).stem
        output_path = Path(f"output/blockgroups/{isochrone_name}_blockgroups.geojson")
    else:
        output_path = Path(output_path)
    
    # Ensure output directory exists
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    result_gdf.to_file(output_path, driver="GeoJSON")
    print(f"Saved result to {output_path}")
    
    return result_gdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find census block groups intersecting with an isochrone")
    parser.add_argument("isochrone", help="Path to isochrone GeoJSON file")
    parser.add_argument("--states", required=True, nargs="+", help="State FIPS codes or abbreviations")
    parser.add_argument("--output", help="Output GeoJSON file path")
    parser.add_argument("--api-key", help="Census API key (optional if set as environment variable)")
    parser.add_argument("--predicate", help="Predicate for spatial join. Default is intersects. Other options are contains, within, and crosses.")
    
    args = parser.parse_args()
    
    result = isochrone_to_block_groups(
        isochrone_path=args.isochrone,
        state_fips=args.states,
        output_path=args.output,
        api_key=args.api_key
    )
    
    # Print summary
    print(f"Found {len(result)} intersecting block groups") 