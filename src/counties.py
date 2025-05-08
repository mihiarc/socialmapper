#!/usr/bin/env python3
"""
County management utilities for the SocialMapper project.

This module provides tools for working with US counties including:
- Converting between county FIPS codes, names, and other identifiers
- Getting neighboring counties
- Fetching block groups at the county level
"""
import os
import requests
import logging
import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from tqdm import tqdm

try:
    from stqdm import stqdm
    has_stqdm = True
except ImportError:
    from tqdm import tqdm as stqdm
    has_stqdm = False

# Import state utilities
from src.states import normalize_state, StateFormat

# Set up logging
logger = logging.getLogger(__name__)

# Import census utilities where available
try:
    import cenpy
    HAS_CENPY = True
except ImportError:
    HAS_CENPY = False
    logger.warning("cenpy not installed - advanced county operations may be limited")

# Configure geopandas to use PyOGRIO and PyArrow for better performance if available
USE_ARROW = False
try:
    import pyarrow
    USE_ARROW = True
    os.environ["PYOGRIO_USE_ARROW"] = "1"
except ImportError:
    pass


def get_county_fips_from_point(lat: float, lon: float, api_key: Optional[str] = None) -> Tuple[str, str]:
    """
    Determine the state and county FIPS codes for a given point.
    
    Args:
        lat: Latitude of the point
        lon: Longitude of the point
        api_key: Census API key (optional)
        
    Returns:
        Tuple of (state_fips, county_fips)
    """
    # Use Census Geocoder to determine the county
    url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {}).get("geographies", {}).get("Counties", [])
            
            if result and len(result) > 0:
                county_data = result[0]
                state_fips = county_data.get("STATE")
                county_fips = county_data.get("COUNTY")
                
                if state_fips and county_fips:
                    return state_fips, county_fips
    except Exception as e:
        logger.error(f"Error determining county from coordinates: {e}")
    
    # Fallback if geocoder fails
    logger.warning(f"Could not determine county for coordinates ({lat}, {lon})")
    return "", ""


def get_neighboring_counties(state_fips: str, county_fips: str) -> List[Tuple[str, str]]:
    """
    Get neighboring counties for a given county.
    
    Args:
        state_fips: State FIPS code
        county_fips: County FIPS code
        
    Returns:
        List of tuples with (state_fips, county_fips) for neighboring counties
    """
    # For now we'll use a spatial approach by getting counties and finding those that share boundaries
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # First, get all counties in the state
    state_counties_file = cache_dir / f"counties_{state_fips}.geojson"
    
    # Try to load from cache first
    state_counties = None
    if state_counties_file.exists():
        try:
            state_counties = gpd.read_file(
                state_counties_file,
                engine="pyogrio",
                use_arrow=USE_ARROW
            )
        except Exception as e:
            logger.warning(f"Could not load cached counties for state {state_fips}: {e}")
    
    # If not in cache, fetch from Census
    if state_counties is None:
        try:
            # Fetch counties using Census API via cenpy if available
            if HAS_CENPY:
                conn = cenpy.remote.APIConnection("TIGER")
                state_counties = conn.query(
                    layer="County", 
                    region=f"STATE:{state_fips}"
                )
                # Convert to GeoDataFrame
                state_counties = gpd.GeoDataFrame(
                    state_counties,
                    geometry=gpd.points_from_xy(
                        state_counties.INTPTLON, 
                        state_counties.INTPTLAT
                    ),
                    crs="EPSG:4326"
                )
                # Save to cache
                state_counties.to_file(state_counties_file, driver="GeoJSON")
            else:
                # Fall back to TIGER/Line REST API
                url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
                params = {
                    'where': f"STATE='{state_fips}'",
                    'outFields': 'STATE,COUNTY,NAME,GEOID',
                    'returnGeometry': 'true',
                    'f': 'geojson'
                }
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    state_counties = gpd.GeoDataFrame.from_features(
                        data['features'],
                        crs="EPSG:4326"
                    )
                    # Save to cache
                    state_counties.to_file(state_counties_file, driver="GeoJSON")
                else:
                    logger.warning(f"Failed to get counties for state {state_fips}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching counties for state {state_fips}: {e}")
            return []
    
    # Now find the target county
    target_county = state_counties[state_counties['COUNTY'] == county_fips]
    if len(target_county) == 0:
        logger.warning(f"Could not find county {county_fips} in state {state_fips}")
        return []
    
    # Get neighboring counties within the same state
    neighbors = []
    try:
        # Use spatial join to find counties that touch the target county
        target_geom = target_county.iloc[0].geometry
        for idx, county in state_counties.iterrows():
            if county['COUNTY'] != county_fips and county.geometry.touches(target_geom):
                neighbors.append((state_fips, county['COUNTY']))
    except Exception as e:
        logger.error(f"Error finding neighboring counties: {e}")
    
    # Add neighboring counties in adjacent states
    # This would require getting counties from neighboring states
    # For simplicity, this implementation only includes counties in the same state
    # A more complete implementation would expand to include counties in neighboring states
    
    return neighbors


def get_block_groups_for_county(
    state_fips: str, 
    county_fips: str,
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Fetch census block group boundaries for a specific county.
    
    Args:
        state_fips: State FIPS code
        county_fips: County FIPS code
        api_key: Census API key (optional)
        
    Returns:
        GeoDataFrame with block group boundaries
    """
    # Check for cached block group data
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    cache_file = cache_dir / f"block_groups_{state_fips}_{county_fips}.geojson"
    
    # Try to load from cache first
    if cache_file.exists():
        try:
            block_groups = gpd.read_file(
                cache_file,
                engine="pyogrio",
                use_arrow=USE_ARROW
            )
            tqdm.write(f"Loaded cached block groups for county {county_fips} in state {state_fips}")
            return block_groups
        except Exception as e:
            tqdm.write(f"Error loading cache: {e}")
    
    # If not in cache, fetch from Census API
    tqdm.write(f"Fetching block groups for county {county_fips} in state {state_fips}")
    
    # Use the Tracts_Blocks MapServer endpoint
    base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
    
    params = {
        'where': f"STATE='{state_fips}' AND COUNTY='{county_fips}'",
        'outFields': 'STATE,COUNTY,TRACT,BLKGRP,GEOID',
        'returnGeometry': 'true',
        'f': 'geojson'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=60)
        
        if response.status_code == 200:
            # Parse the GeoJSON response
            data = response.json()
            block_groups = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
            
            # Ensure proper formatting
            if 'STATE' not in block_groups.columns or not all(block_groups['STATE'] == state_fips):
                block_groups['STATE'] = state_fips
            if 'COUNTY' not in block_groups.columns or not all(block_groups['COUNTY'] == county_fips):
                block_groups['COUNTY'] = county_fips
            
            # Save to cache
            block_groups.to_file(cache_file, driver="GeoJSON", engine="pyogrio", use_arrow=USE_ARROW)
            
            tqdm.write(f"Retrieved {len(block_groups)} block groups for county {county_fips}")
            return block_groups
        else:
            raise ValueError(f"Census API returned status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching block groups for county {county_fips}: {e}")
        raise ValueError(f"Could not fetch block groups: {str(e)}")


def get_block_groups_for_counties(
    counties: List[Tuple[str, str]],
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Fetch block groups for multiple counties and combine them.
    
    Args:
        counties: List of (state_fips, county_fips) tuples
        api_key: Census API key (optional)
        
    Returns:
        Combined GeoDataFrame with block groups for all counties
    """
    all_block_groups = []
    
    for state_fips, county_fips in stqdm(counties, desc="Fetching block groups by county", unit="county"):
        try:
            county_block_groups = get_block_groups_for_county(state_fips, county_fips, api_key)
            all_block_groups.append(county_block_groups)
        except Exception as e:
            tqdm.write(f"Error fetching block groups for county {county_fips} in state {state_fips}: {e}")
    
    if not all_block_groups:
        raise ValueError("No block group data could be retrieved")
    
    # Combine all county block groups
    return pd.concat(all_block_groups, ignore_index=True)


def get_counties_from_pois(
    poi_data: Dict, 
    include_neighbors: bool = True,
    api_key: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Determine counties for a list of POIs and optionally include neighboring counties.
    
    Args:
        poi_data: Dictionary with 'pois' key containing list of POIs
        include_neighbors: Whether to include neighboring counties
        api_key: Census API key (optional)
        
    Returns:
        List of (state_fips, county_fips) tuples for all relevant counties
    """
    pois = poi_data.get('pois', [])
    if not pois:
        raise ValueError("No POIs found in input data")
    
    counties_set = set()
    
    for poi in stqdm(pois, desc="Determining counties for POIs", unit="POI"):
        lat = poi.get('lat')
        lon = poi.get('lon')
        
        if lat is None or lon is None:
            logger.warning(f"POI missing coordinates: {poi.get('id', 'unknown')}")
            continue
        
        # Get state and county FIPS for this POI
        state_fips, county_fips = get_county_fips_from_point(lat, lon, api_key)
        
        if state_fips and county_fips:
            counties_set.add((state_fips, county_fips))
            
            # Add neighboring counties if requested
            if include_neighbors:
                neighbors = get_neighboring_counties(state_fips, county_fips)
                counties_set.update(neighbors)
    
    return list(counties_set) 