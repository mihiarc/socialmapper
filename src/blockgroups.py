#!/usr/bin/env python3
"""
Module to find census block groups that intersect with isochrones.
"""
import os
import sys
import argparse
import geopandas as gpd
from pathlib import Path
import pandas as pd
import requests
from shapely.geometry import shape
from typing import Dict, Any, List, Union, Optional

def get_census_block_groups(
    state_fips: List[str],
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Fetch census block group boundaries for specified states.
    
    Args:
        state_fips: List of state FIPS codes
        api_key: Census API key (optional if using cached data)
        
    Returns:
        GeoDataFrame with block group boundaries
    """
    # Check for cached block group data
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Try to load all states from cache
    cached_gdfs = []
    all_cached = True
    
    for state in state_fips:
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
    if not api_key:
        api_key = os.getenv('CENSUS_API_KEY')
        if not api_key:
            raise ValueError("Census API key not found. Please set the 'CENSUS_API_KEY' environment variable or provide it as an argument.")
    
    # We'll use the Census Bureau's TIGER/Line API to get block group geometries
    base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/8/query"
    
    all_block_groups = []
    
    for state in state_fips:
        print(f"Fetching block groups for state {state}...")
        
        params = {
            'where': f"STATE='{state}'",
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'geojson'
        }
        
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            gdf = gpd.GeoDataFrame.from_features(response.json()['features'], crs="EPSG:4326")
            
            # Save to cache
            cache_file = cache_dir / f"block_groups_{state}.geojson"
            gdf.to_file(cache_file, driver="GeoJSON")
            print(f"Saved block groups for state {state} to cache")
            
            all_block_groups.append(gdf)
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
    block_groups_gdf: gpd.GeoDataFrame
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
    # (This is optional and might be computationally intensive for large datasets)
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
        output_path: Optional path to save result GeoJSON
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
    
    # Save to file if output path is provided
    if output_path:
        result_gdf.to_file(output_path, driver="GeoJSON")
        print(f"Saved result to {output_path}")
    
    return result_gdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find census block groups intersecting with an isochrone")
    parser.add_argument("isochrone", help="Path to isochrone GeoJSON file")
    parser.add_argument("--states", required=True, nargs="+", help="State FIPS codes")
    parser.add_argument("--output", help="Output GeoJSON file path")
    parser.add_argument("--api-key", help="Census API key (optional if set as environment variable)")
    
    args = parser.parse_args()
    
    result = isochrone_to_block_groups(
        isochrone_path=args.isochrone,
        state_fips=args.states,
        output_path=args.output,
        api_key=args.api_key
    )
    
    # Print summary
    print(f"Found {len(result)} intersecting block groups") 