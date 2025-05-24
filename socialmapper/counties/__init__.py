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


# Note: get_county_fips_from_point() function removed.
# Use the optimized neighbor system instead:
# from socialmapper.census import get_geography_from_point


# Note: get_neighboring_counties() function removed.
# Use the optimized neighbor system instead:
# from socialmapper.census import get_neighboring_counties


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


# Note: get_counties_from_pois() function removed.
# Use the optimized neighbor system instead:
# from socialmapper.census import get_counties_from_pois


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