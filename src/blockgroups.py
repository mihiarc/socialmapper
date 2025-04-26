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
from typing import List, Optional, Tuple

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

def get_census_block_groups(
    state_fips: List[str],
    api_key: Optional[str] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None
) -> gpd.GeoDataFrame:
    """
    Fetch census block group boundaries for specified states.
    
    Args:
        state_fips: List of state FIPS codes or abbreviations
        api_key: Census API key (optional if using cached data)
        bbox: Optional bounding box (min_x, min_y, max_x, max_y) to filter block groups
            This can significantly improve performance when only a small area is needed
        
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
                # Use PyOGRIO with PyArrow for faster reading
                if bbox:
                    # Use spatial filtering when a bbox is provided
                    cached_gdfs.append(gpd.read_file(
                        cache_file, 
                        engine="pyogrio",
                        use_arrow=USE_ARROW,
                        bbox=bbox
                    ))
                else:
                    cached_gdfs.append(gpd.read_file(
                        cache_file, 
                        engine="pyogrio", 
                        use_arrow=USE_ARROW
                    ))
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
    api_key = api_key or os.getenv('CENSUS_API_KEY')

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
        
        # Add spatial filtering to the API request if a bbox is provided
        if bbox:
            params['geometry'] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params['geometryType'] = "esriGeometryEnvelope"
            params['spatialRel'] = "esriSpatialRelIntersects"
            print(f"Using bounding box filter: {bbox}")
        
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
                gdf.to_file(cache_file, driver="GeoJSON", engine="pyogrio", use_arrow=USE_ARROW)
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
        isochrone_path: Path to the isochrone GeoJSON or GeoParquet file
        
    Returns:
        GeoDataFrame containing the isochrone
    """
    try:
        if isochrone_path.endswith('.parquet'):
            isochrone_gdf = gpd.read_parquet(isochrone_path)
        else:
            isochrone_gdf = gpd.read_file(isochrone_path, engine="pyogrio", use_arrow=USE_ARROW)
            
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
        print(f"Coordinate indexing reduced block groups from {len(block_groups_gdf)} to {len(filtered_block_groups)}")
        block_groups_gdf = filtered_block_groups
    
    # Set predicate based on selection mode
    predicate = "within" if selection_mode == "contain" else "intersects"
    
    # Find which block groups intersect with or are contained within the isochrone
    intersection = gpd.sjoin(block_groups_gdf, isochrone_gdf, how="inner", predicate=predicate)
    
    # Process geometries based on selection mode
    processed_geometries = []
    
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
    isochrone_path: str,
    state_fips: List[str],
    output_path: Optional[str] = None,
    api_key: Optional[str] = None,
    selection_mode: str = "intersect",
    use_parquet: bool = True
) -> gpd.GeoDataFrame:
    """
    Main function to find census block groups intersecting with an isochrone.
    
    Args:
        isochrone_path: Path to isochrone GeoJSON or GeoParquet file
        state_fips: List of state FIPS codes to fetch block groups for
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
    isochrone_gdf = load_isochrone(isochrone_path)
    
    # Get the bounding box of the isochrone to optimize data fetching
    bbox = tuple(isochrone_gdf.total_bounds)
    
    # Get block groups for requested states with spatial filtering using the isochrone bbox
    block_groups_gdf = get_census_block_groups(state_fips, api_key, bbox)
    
    # Find intersecting block groups
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
            
        if use_parquet and USE_ARROW and not output_path.endswith('.geojson'):
            # Default to parquet if extension isn't explicitly geojson
            if not output_path.endswith('.parquet'):
                output_path = f"{output_path}.parquet"
            result_gdf.to_parquet(output_path)
        else:
            if not output_path.endswith('.geojson'):
                output_path = f"{output_path}.geojson"
            result_gdf.to_file(output_path, driver="GeoJSON", engine="pyogrio", use_arrow=USE_ARROW)
            
        print(f"Saved {len(result_gdf)} block groups to {output_path}")
        
    return result_gdf

def extract_state_from_isochrone(isochrone_path: str) -> List[str]:
    """
    Try to extract state information from the isochrone file
    based on POI names or metadata.
    
    Args:
        isochrone_path: Path to isochrone file
        
    Returns:
        List of state FIPS codes or abbreviations (empty if none found)
    """
    # This is a simple heuristic and may need to be expanded
    isochrone_gdf = load_isochrone(isochrone_path)
    
    if 'state' in isochrone_gdf.columns:
        states = isochrone_gdf['state'].unique().tolist()
        if states:
            return states
    
    return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find census block groups that intersect with isochrones"
    )
    parser.add_argument(
        "isochrone_path",
        help="Path to isochrone GeoJSON or GeoParquet file"
    )
    parser.add_argument(
        "--state-fips",
        nargs="+",
        help="State FIPS codes or abbreviations"
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
    
    # If state FIPS not provided, try to extract from isochrone
    state_fips = args.state_fips
    if not state_fips:
        state_fips = extract_state_from_isochrone(args.isochrone_path)
        if not state_fips:
            parser.error("No state FIPS codes provided or extracted. Please specify --state-fips.")
    
    # Run the main function
    isochrone_to_block_groups(
        isochrone_path=args.isochrone_path,
        state_fips=state_fips,
        output_path=args.output_path,
        api_key=args.api_key,
        selection_mode=args.selection_mode,
        use_parquet=not args.no_parquet
    ) 