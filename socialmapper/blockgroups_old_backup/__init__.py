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
from typing import List, Optional, Dict, Union
import json
# Import the new progress bar utility
from socialmapper.progress import get_progress_bar
from tqdm import tqdm

from socialmapper.states import normalize_state, StateFormat, state_fips_to_name
from socialmapper.counties import (
    get_counties_from_pois,
    get_block_groups_for_counties,
    get_block_group_urls
)
from socialmapper.util import get_census_api_key

# Set PyOGRIO as the default IO engine
gpd.options.io_engine = "pyogrio"

# Enable PyArrow for GeoPandas operations if available
try:
    import pyarrow
    USE_ARROW = True
    os.environ["PYOGRIO_USE_ARROW"] = "1"  # Set environment variable for pyogrio
    print("PyArrow is available and enabled for optimized I/O")
except ImportError:
    USE_ARROW = False
    print("PyArrow not available. Install it for better performance.")

# Remove duplicate imports - we now use socialmapper.counties directly
# try:
#     from src.counties import (
#         get_counties_from_pois,
#         get_block_groups_for_counties
#     )
#     HAS_COUNTY_UTILS = True
# except ImportError:
#     HAS_COUNTY_UTILS = False

# Set flag indicating that county utilities are available
HAS_COUNTY_UTILS = True

def get_census_block_groups(
    state_fips: List[str],
    api_key: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """
    Fetch census block group boundaries for specified states.
    
    Args:
        state_fips: List of state FIPS codes or abbreviations
        api_key: Census API key (optional if using cached data)
        
    Returns:
        GeoDataFrame with block group boundaries
    """
    # Convert any state identifiers to FIPS codes using the centralized state module
    normalized_state_fips = []
    for state in state_fips:
        # Convert to FIPS code
        fips = normalize_state(state, to_format=StateFormat.FIPS)
        if fips:
            normalized_state_fips.append(fips)
        else:
            # If not found, keep as is
            normalized_state_fips.append(state)
    
    # Check for cached block group data
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Try to load all states from cache
    cached_gdfs = []
    all_cached = True
    
    for state in get_progress_bar(normalized_state_fips, desc="Checking cached block groups", unit="state"):
        cache_file = cache_dir / f"block_groups_{state}.geojson"
        if cache_file.exists():
            try:
                # Use PyOGRIO with PyArrow for faster reading
                cached_gdfs.append(gpd.read_file(
                    cache_file, 
                    engine="pyogrio", 
                    use_arrow=USE_ARROW
                ))
                tqdm.write(f"Loaded cached block groups for state {state}")
            except Exception as e:
                tqdm.write(f"Error loading cache for state {state}: {e}")
                all_cached = False
                break
        else:
            all_cached = False
            break
    
    # If all states were cached, return combined data
    if all_cached and cached_gdfs:
        return pd.concat(cached_gdfs, ignore_index=True)
    
    # If not all states were cached or there was an error, fetch from Census API
    if api_key is None:
        api_key = get_census_api_key()

    tqdm.write("Fetching block groups from Census TIGER API")
    
    # Use the Tracts_Blocks MapServer endpoint
    base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
    
    all_block_groups = []
    
    for state in get_progress_bar(normalized_state_fips, desc="Fetching block groups by state", unit="state"):
        tqdm.write(f"Fetching block groups for state {state}...")
        state_block_groups = []
        
        # Use the simple approach that works: for large states, fetch data in smaller batches
        # This avoids timeouts and "Request Rejected" errors that occur with large queries
        batch_size = 1000
        start_index = 0
        more_records = True
        
        # Fields needed for block group identification and analysis
        required_fields = 'STATE,COUNTY,TRACT,BLKGRP,GEOID'
        
        batch_count = 0
        with get_progress_bar(desc=f"Fetching batches for state {state}", unit="batch") as batch_pbar:
            while more_records:
                # Simple query that fetches records in batches
                params = {
                    'where': f"STATE='{state}'",
                    'outFields': required_fields,
                    'returnGeometry': 'true',
                    'resultRecordCount': batch_size,
                    'resultOffset': start_index,
                    'f': 'geojson'
                }
                
                try:
                    # Only log the first batch and then every 5th batch to reduce verbosity
                    if batch_count == 0 or batch_count % 5 == 0:
                        tqdm.write(f"  Fetching batch starting at index {start_index}...")
                    
                    response = requests.get(base_url, params=params, timeout=60)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'json' in content_type.lower():
                            try:
                                response_json = response.json()
                                
                                if 'features' in response_json and response_json['features']:
                                    feature_count = len(response_json['features'])
                                    
                                    # Only log the first batch and then every 5th batch
                                    if batch_count == 0 or batch_count % 5 == 0:
                                        tqdm.write(f"  Retrieved {feature_count} block groups in this batch")
                                    
                                    # Create GeoDataFrame from features
                                    batch_gdf = gpd.GeoDataFrame.from_features(response_json['features'], crs="EPSG:4326")
                                    
                                    # Verify STATE column is correct
                                    if 'STATE' not in batch_gdf.columns or not all(batch_gdf['STATE'] == state):
                                        batch_gdf['STATE'] = state
                                    
                                    state_block_groups.append(batch_gdf)
                                    
                                    # Check if we need to fetch more records
                                    more_records = feature_count == batch_size and 'exceededTransferLimit' in response_json.get('properties', {})
                                    
                                    # Update start index for next batch
                                    start_index += feature_count
                                    batch_count += 1
                                    batch_pbar.update(1)
                                else:
                                    more_records = False
                                    if 'error' in response_json:
                                        tqdm.write(f"  API error: {response_json['error']}")
                            except json.JSONDecodeError as e:
                                tqdm.write(f"  Error parsing JSON: {e}")
                                more_records = False
                        else:
                            tqdm.write(f"  Error: Received non-JSON response: {content_type}")
                            more_records = False
                    else:
                        tqdm.write(f"  Error fetching data: HTTP {response.status_code}")
                        more_records = False
                except Exception as e:
                    tqdm.write(f"  Exception during API request: {e}")
                    more_records = False
        
        # If we got some data, combine it and save to cache
        if state_block_groups:
            state_gdf = pd.concat(state_block_groups, ignore_index=True)
            tqdm.write(f"Total block groups retrieved for {state}: {len(state_gdf)}")
            
            # Save to cache
            cache_file = cache_dir / f"block_groups_{state}.geojson"
            state_gdf.to_file(cache_file, driver="GeoJSON", engine="pyogrio", use_arrow=USE_ARROW)
            tqdm.write(f"Saved block groups for state {state} to cache")
            
            all_block_groups.append(state_gdf)
           
    if not all_block_groups:
        raise ValueError("No block group data could be retrieved. Please check your network connection or try again later.")
    
    return pd.concat(all_block_groups, ignore_index=True)

def load_isochrone(isochrone_path: Union[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    """
    Load an isochrone file or use directly provided GeoDataFrame.
    
    Args:
        isochrone_path: Path to the isochrone GeoJSON/GeoParquet file OR a GeoDataFrame
        
    Returns:
        GeoDataFrame containing the isochrone
    """
    try:
        # If already a GeoDataFrame, return it directly
        if isinstance(isochrone_path, gpd.GeoDataFrame):
            isochrone_gdf = isochrone_path
        elif isinstance(isochrone_path, str):
            # Load from file path
            if isochrone_path.endswith('.parquet'):
                isochrone_gdf = gpd.read_parquet(isochrone_path)
            else:
                isochrone_gdf = gpd.read_file(isochrone_path, engine="pyogrio", use_arrow=USE_ARROW)
        else:
            raise ValueError(f"Unsupported isochrone input type: {type(isochrone_path)}. Expected string path or GeoDataFrame.")
            
        if isochrone_gdf.crs is None:
            isochrone_gdf.set_crs("EPSG:4326", inplace=True)
        return isochrone_gdf
    except Exception as e:
        raise ValueError(f"Error loading isochrone file: {e}")

def find_intersecting_block_groups(
    isochrone_gdf: gpd.GeoDataFrame,
    block_groups_gdf: gpd.GeoDataFrame,
    selection_mode: str = "intersect"
) -> gpd.GeoDataFrame:
    """
    Find census block groups that intersect with the isochrone.
    
    Args:
        isochrone_gdf: GeoDataFrame containing the isochrone
        block_groups_gdf: GeoDataFrame containing block group boundaries
        selection_mode: Method to select and process block groups
            - "clip": Clip block groups to isochrone boundary (original behavior)
            - "intersect": Keep full geometry of any intersecting block group
            - "contain": Only include block groups fully contained within isochrone
        
    Returns:
        GeoDataFrame with selected block groups
    """
    # Make sure CRS match
    if isochrone_gdf.crs != block_groups_gdf.crs:
        block_groups_gdf = block_groups_gdf.to_crs(isochrone_gdf.crs)
    
    # Use coordinate indexing to pre-filter block groups by bounding box
    # This improves performance by reducing the number of geometries for spatial join
    bounds = isochrone_gdf.total_bounds
    filtered_block_groups = block_groups_gdf.cx[
        bounds[0]:bounds[2], 
        bounds[1]:bounds[3]
    ]
    
    # If filtering reduced the dataset substantially, use the filtered version
    if len(filtered_block_groups) < len(block_groups_gdf) * 0.9:  # If we've filtered out at least 10%
        tqdm.write(f"Coordinate indexing reduced block groups from {len(block_groups_gdf)} to {len(filtered_block_groups)}")
        block_groups_gdf = filtered_block_groups
    
    # Set predicate based on selection mode
    predicate = "within" if selection_mode == "contain" else "intersects"
    
    # Find which block groups intersect with or are contained within the isochrone
    intersection = gpd.sjoin(block_groups_gdf, isochrone_gdf, how="inner", predicate=predicate)
    
    # Process geometries based on selection mode
    processed_geometries = []
    
    tqdm.write(f"Processing {len(intersection)} intersecting block groups...")
    
    # Skip progress bar for nearly instant operations
    for idx, row in intersection.iterrows():
        block_geom = row.geometry
        isochrone_geom = isochrone_gdf.loc[isochrone_gdf.index == row.index_right, "geometry"].iloc[0]
        
        # Determine geometry based on selection mode
        if selection_mode == "clip":
            # Original behavior - clip to isochrone boundary
            final_geom = block_geom.intersection(isochrone_geom)
        else:
            # For "intersect" or "contain", keep the original geometry
            final_geom = block_geom
        
        # Calculate intersection percentage
        intersection_geom = block_geom.intersection(isochrone_geom)
        intersection_pct = intersection_geom.area / block_geom.area * 100
        
        # Get GEOID parts ensuring proper formatting
        state = str(row['STATE']).zfill(2)
        county = str(row['COUNTY']).zfill(3)
        tract = str(row['TRACT']).zfill(6)
        blkgrp = str(row['BLKGRP'] if 'BLKGRP' in row else '1')
        
        # Create properly formatted 12-digit GEOID
        geoid = state + county + tract + blkgrp
        
        processed_geometries.append({
            "GEOID": geoid,
            "STATE": row['STATE'],
            "COUNTY": row['COUNTY'],
            "TRACT": row['TRACT'],
            "BLKGRP": row['BLKGRP'] if 'BLKGRP' in row else geoid[-1],
            "geometry": final_geom,
            "poi_id": row['poi_id'] if 'poi_id' in row else None,
            "poi_name": row['poi_name'] if 'poi_name' in row else None,
            "travel_time_minutes": row['travel_time_minutes'] if 'travel_time_minutes' in row else None,
            "intersection_area_pct": intersection_pct
        })
    
    # Create new GeoDataFrame with processed geometries
    result_gdf = gpd.GeoDataFrame(processed_geometries, crs=isochrone_gdf.crs)
    
    return result_gdf

def isochrone_to_block_groups(
    isochrone_path: Union[str, gpd.GeoDataFrame],
    state_fips: List[str],
    output_path: Optional[str] = None,
    api_key: Optional[str] = None,
    selection_mode: str = "intersect",
    use_parquet: bool = True
) -> gpd.GeoDataFrame:
    """
    Main function to find census block groups intersecting with an isochrone.
    
    Args:
        isochrone_path: Path to isochrone GeoJSON/GeoParquet file OR a GeoDataFrame
        state_fips: List of state FIPS codes or abbreviations (required)
        output_path: Path to save result GeoJSON (defaults to output/blockgroups/[filename].geojson)
        api_key: Census API key (optional if using cached data)
        selection_mode: Method to select and process block groups
            - "clip": Clip block groups to isochrone boundary (original behavior)
            - "intersect": Keep full geometry of any intersecting block group
            - "contain": Only include block groups fully contained within isochrone
        use_parquet: Whether to use GeoParquet instead of GeoJSON format when saving
        
    Returns:
        GeoDataFrame with selected block groups
    """
    # Load the isochrone
    tqdm.write("Loading isochrone...")
    isochrone_gdf = load_isochrone(isochrone_path)
    
    # Validate state_fips
    if not state_fips:
        raise ValueError("state_fips parameter is required. Please provide a list of state abbreviations or FIPS codes.")
    
    # Get block groups for requested states
    tqdm.write(f"Fetching block groups for state(s): {', '.join(state_fips)}")
    block_groups_gdf = get_census_block_groups(state_fips, api_key)
    
    # Find intersecting block groups
    tqdm.write(f"Finding block groups that {selection_mode} with isochrone...")
    result_gdf = find_intersecting_block_groups(
        isochrone_gdf,
        block_groups_gdf,
        selection_mode
    )
    
    # Save result if output path is provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        tqdm.write(f"Saving {len(result_gdf)} block groups...")
        if use_parquet and USE_ARROW and not output_path.endswith('.geojson'):
            # Default to parquet if extension isn't explicitly geojson
            if not output_path.endswith('.parquet'):
                output_path = f"{output_path}.parquet"
            result_gdf.to_parquet(output_path)
        else:
            if not output_path.endswith('.geojson'):
                output_path = f"{output_path}.geojson"
            result_gdf.to_file(output_path, driver="GeoJSON", engine="pyogrio", use_arrow=USE_ARROW)
            
        tqdm.write(f"Saved {len(result_gdf)} block groups to {output_path}")
        
    return result_gdf

def isochrone_to_block_groups_by_county(
    isochrone_path: Union[str, gpd.GeoDataFrame],
    poi_data: Dict,
    output_path: Optional[str] = None,
    api_key: Optional[str] = None,
    selection_mode: str = "intersect"
) -> gpd.GeoDataFrame:
    """
    Find census block groups that intersect with an isochrone using county-based optimization.
    
    This function uses counties containing the POIs rather than entire states, which can be
    significantly faster, especially when dealing with large states or metropolitan areas
    that span multiple states.
    
    Args:
        isochrone_path: Path to isochrone GeoJSON/GeoParquet file OR a GeoDataFrame
        poi_data: Dictionary with POI data including coordinates
        output_path: Path to save result (no longer used - kept for backwards compatibility)
        api_key: Census API key (optional if using cached data)
        selection_mode: Method to select and process block groups
            - "clip": Clip block groups to isochrone boundary
            - "intersect": Keep full geometry of any intersecting block group
            - "contain": Only include block groups fully contained within isochrone
        
    Returns:
        GeoDataFrame with selected block groups
    """
    if not HAS_COUNTY_UTILS:
        raise ImportError("County utilities are not available. Make sure src/counties.py is present.")
    
    # Load the isochrone
    tqdm.write("Loading isochrone...")
    isochrone_gdf = load_isochrone(isochrone_path)
    
    # Get counties containing the POIs and their neighbors
    tqdm.write("Determining counties for POIs...")
    counties = get_counties_from_pois(poi_data, include_neighbors=True, api_key=api_key)
    
    if not counties:
        raise ValueError(
            "Could not determine counties for the POIs. Falling back to state-based method "
            "may be necessary. Check that POIs have valid coordinates."
        )
    
    tqdm.write(f"Found {len(counties)} relevant counties")
    
    # Get block groups for all relevant counties
    tqdm.write(f"Fetching block groups for {len(counties)} counties...")
    block_groups_gdf = get_block_groups_for_counties(counties, api_key)
    
    # Find intersecting block groups
    tqdm.write(f"Finding block groups that {selection_mode} with isochrone...")
    result_gdf = find_intersecting_block_groups(
        isochrone_gdf,
        block_groups_gdf,
        selection_mode
    )
    
    # File output functionality completely removed
    
    return result_gdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find census block groups that intersect with isochrones"
    )
    parser.add_argument(
        "isochrone_path",
        help="Path to isochrone GeoJSON or GeoParquet file"
    )
    parser.add_argument(
        "--poi-file",
        required=True,
        help="Path to POI JSON file containing coordinates"
    )
    parser.add_argument(
        "--output-path",
        help="Path to save result GeoJSON or GeoParquet"
    )
    parser.add_argument(
        "--api-key",
        help="Census API key (optional if using cached data or set as environment variable)"
    )
    parser.add_argument(
        "--selection-mode",
        choices=["clip", "intersect", "contain"],
        default="intersect",
        help="Method to select and process block groups"
    )
    parser.add_argument(
        "--no-parquet",
        action="store_true",
        help="Do not use GeoParquet format (use GeoJSON instead)"
    )
    
    args = parser.parse_args()
    
    # Load the POI data
    with open(args.poi_file, 'r') as f:
        poi_data = json.load(f)
    
    # Run the main function with POI data
    isochrone_to_block_groups_by_county(
        isochrone_path=args.isochrone_path,
        poi_data=poi_data,
        output_path=args.output_path,
        api_key=args.api_key,
        selection_mode=args.selection_mode
    ) 