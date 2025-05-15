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
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from tqdm import tqdm
from socialmapper.progress import get_progress_bar
from socialmapper.states import normalize_state, StateFormat, state_fips_to_name
from socialmapper.util import get_census_api_key

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
            # # Fetch counties using Census API via cenpy if available
            # # This section is commented out to prioritize the TIGERweb REST API
            # # due to issues with cenpy product shortcodes for direct TIGER access.
            # if HAS_CENPY:
            #     logger.info(f"Attempting to fetch counties for state {state_fips} using cenpy.")
            #     # It's better to use a specific vintage or product that includes TIGER data
            #     # For example, using ACS product which has an associated TIGER map service
            #     # conn = cenpy.products.ACS(year=2022) # Or other recent year
            #     # state_counties_gdf = conn._api.mapservice.query(
            #     #     layer_idx=conn._layer_lookup['county'], # Use the correct layer index for counties
            #     #     where=f"STATE = '{state_fips}'",
            #     #     return_geometry=True
            #     # )
            #     # # Ensure it's a GeoDataFrame, cenpy might return a DataFrame
            #     # if not isinstance(state_counties_gdf, gpd.GeoDataFrame):
            #     #     state_counties = gpd.GeoDataFrame(state_counties_gdf, geometry='geometry', crs="EPSG:4326") # Adjust geometry column if needed
            #     # else:
            #     #     state_counties = state_counties_gdf

            #     # The original approach causing issues:
            #     conn = cenpy.remote.APIConnection("TIGER") # This shortcode might be problematic
            #     state_counties_df = conn.query(
            #         layer="County", 
            #         region=f"STATE:{state_fips}"
            #     )
            #     # Convert to GeoDataFrame - This part was missing and might be needed if the above worked
            #     # state_counties = gpd.GeoDataFrame(
            #     #     state_counties_df,
            #     #     geometry=gpd.points_from_xy( # Assuming INTPTLON/LAT are present, which they might not be for "TIGER"
            #     #         state_counties_df.INTPTLON, 
            #     #         state_counties_df.INTPTLAT
            #     #     ),
            #     #     crs="EPSG:4326" 
            #     # )
            #     # # Save to cache
            #     # if state_counties is not None and not state_counties.empty:
            #     #    state_counties.to_file(state_counties_file, driver="GeoJSON")
            #     # else:
            #     #    logger.warning(f"cenpy query for state {state_fips} returned no county data.")
            #     #    state_counties = None # Ensure it's None to trigger fallback

            # if state_counties is None: # If cenpy failed or didn't run
            # Fall back to TIGER/Line REST API (Now primary method)
            logger.info(f"Fetching counties for state {state_fips} using TIGERweb REST API.")
            url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
            params = {
                'where': f"STATE='{state_fips}'",
                'outFields': 'STATE,COUNTY,NAME,GEOID,BASENAME', # Added BASENAME for consistency
                'returnGeometry': 'true',
                'f': 'geojson'
            }
            response = requests.get(url, params=params, timeout=60) # Added timeout
            if response.status_code == 200:
                data = response.json()
                if 'features' in data and data['features']:
                    state_counties = gpd.GeoDataFrame.from_features(
                        data['features'],
                        crs="EPSG:4326"
                    )
                    # Save to cache
                    state_counties.to_file(state_counties_file, driver="GeoJSON")
                else:
                    logger.warning(f"TIGERweb API returned no features for state {state_fips}.")
                    return [] # Return empty if no features
            else:
                logger.warning(f"Failed to get counties for state {state_fips} via TIGERweb API (Status: {response.status_code}). Response: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching counties for state {state_fips}: {e}")
            return [] # Return empty on any exception during fetch
    
    if state_counties is None or state_counties.empty:
        logger.warning(f"No county data could be loaded or fetched for state {state_fips}.")
        return []

    # Ensure 'COUNTY' column exists and is of string type for matching
    if 'COUNTY' not in state_counties.columns:
        if 'COUNTYFP' in state_counties.columns: # Common alternative name
            state_counties = state_counties.rename(columns={'COUNTYFP': 'COUNTY'})
        elif 'GEOID' in state_counties.columns and len(state_counties['GEOID'].iloc[0]) >= 5:
             # Extract from GEOID if it's like SSSCC (StateFIPS + CountyFIPS)
            state_counties['COUNTY'] = state_counties['GEOID'].str[2:5]
        else:
            logger.error(f"COUNTY column missing and could not be derived in fetched data for state {state_fips}.")
            return []
    state_counties['COUNTY'] = state_counties['COUNTY'].astype(str).str.zfill(3)
    
    # Now find the target county
    target_county_gdf = state_counties[state_counties['COUNTY'] == county_fips] # Renamed for clarity
    if len(target_county_gdf) == 0:
        logger.warning(f"Could not find county {county_fips} in state {state_fips}")
        return []
    
    # Get neighboring counties within the same state
    neighbors = []
    try:
        # Use spatial join to find counties that touch the target county
        target_geom = target_county_gdf.iloc[0].geometry # Use the GeoDataFrame
        # Ensure geometries are valid
        if not target_geom.is_valid:
            logger.debug(f"Target county {county_fips} in state {state_fips} has invalid geometry. Attempting to buffer by 0.")
            target_geom = target_geom.buffer(0)
            if not target_geom.is_valid:
                logger.error(f"Target county {county_fips} in state {state_fips} geometry still invalid after buffer(0). Cannot find neighbors.")
                return []

        for idx, county_row in state_counties.iterrows(): # Renamed for clarity
            if county_row['COUNTY'] != county_fips:
                county_geom = county_row.geometry
                if not county_geom.is_valid:
                    logger.debug(f"Neighbor candidate county {county_row['BASENAME']} ({county_row['COUNTY']}) in state {state_fips} has invalid geometry. Attempting to buffer by 0.")
                    county_geom = county_geom.buffer(0)
                
                if county_geom.is_valid and county_geom.touches(target_geom):
                    neighbors.append((state_fips, county_row['COUNTY']))
                elif county_geom.is_valid and county_geom.intersects(target_geom) and not county_geom.overlaps(target_geom):
                    # Adding intersects as well, as 'touches' can be very strict
                    # and might miss some legitimate neighbors due to minor geometry imperfections.
                    # We exclude overlaps to avoid issues if the target geometry is somehow duplicated or contained.
                    logger.info(f"Adding county {county_row['BASENAME']} ({county_row['COUNTY']}) as neighbor to {county_fips} based on intersection (not just touches).")
                    neighbors.append((state_fips, county_row['COUNTY']))

    except Exception as e:
        logger.error(f"Error finding neighboring counties spatially for {state_fips}-{county_fips}: {e}")
    
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
    if api_key is None:
        api_key = get_census_api_key()
    
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
    
    for state_fips, county_fips in get_progress_bar(counties, desc="Fetching block groups by county", unit="county"):
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
    
    for poi in get_progress_bar(pois, desc="Determining counties for POIs", unit="POI"):
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


def get_block_group_urls(state_fips: str, year: int = 2022) -> Dict[str, str]:
    """
    Get the download URLs for block group shapefiles from the Census Bureau.
    
    Args:
        state_fips: State FIPS code
        year: Year for the TIGER/Line shapefiles
        
    Returns:
        Dictionary mapping state FIPS to download URLs
    """
    # Standardize the state FIPS
    state_fips = str(state_fips).zfill(2)
    
    # Base URL for Census Bureau TIGER/Line shapefiles
    base_url = f"https://www2.census.gov/geo/tiger/TIGER{year}/BG"
    
    # The URL pattern for block group shapefiles
    url = f"{base_url}/tl_{year}_{state_fips}_bg.zip"
    
    # Return a dictionary mapping state FIPS to the URL
    return {state_fips: url} 