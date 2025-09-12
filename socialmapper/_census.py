"""Internal census data utilities for SocialMapper."""

import os
import requests
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, Polygon
import geopandas as gpd
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# Variable name mappings
VARIABLE_MAPPING = {
    'population': 'B01003_001E',
    'total_population': 'B01003_001E',
    'median_income': 'B19013_001E',
    'median_household_income': 'B19013_001E',
    'median_age': 'B01002_001E',
    'housing_units': 'B25001_001E',
    'total_housing_units': 'B25001_001E',
    'occupied_housing': 'B25003_001E',
    'owner_occupied': 'B25003_002E',
    'renter_occupied': 'B25003_003E',
    'white_population': 'B02001_002E',
    'black_population': 'B02001_003E',
    'asian_population': 'B02001_005E',
    'hispanic_population': 'B03002_012E',
    'poverty': 'B17001_002E',
    'poverty_population': 'B17001_002E',
    'bachelors_degree': 'B15003_022E',
    'high_school': 'B15003_017E',
    'households_with_vehicle': 'B08201_002E',
    'households_no_vehicle': 'B08201_002E',
    'median_home_value': 'B25077_001E',
    'median_rent': 'B25064_001E',
}


def normalize_variable_names(variables: List[str]) -> List[str]:
    """Convert human-readable variable names to census codes.
    
    Args:
        variables: List of variable names or codes
    
    Returns:
        List of census variable codes
    """
    normalized = []
    
    for var in variables:
        # Check if already a census code (has underscore and starts with letter)
        if '_' in var and var[0].isalpha() and var[0].isupper():
            normalized.append(var)
        else:
            # Try to map from human-readable name
            mapped = VARIABLE_MAPPING.get(var.lower().replace(' ', '_'))
            if mapped:
                normalized.append(mapped)
            else:
                logger.warning(f"Unknown variable '{var}', keeping as-is")
                normalized.append(var)
    
    return normalized


def fetch_block_groups_for_area(geometry: Polygon) -> List[Dict[str, Any]]:
    """Fetch census block groups that intersect with a geometry.
    
    Args:
        geometry: Shapely Polygon to find block groups for
    
    Returns:
        List of dicts with block group information
    """
    # Get bounds
    bounds = geometry.bounds  # (minx, miny, maxx, maxy)
    
    # Identify states that might be in this area
    from ._geocoding import get_census_geography
    
    # Sample the centroid to get state/county
    centroid = geometry.centroid
    geo_info = get_census_geography(centroid.y, centroid.x)
    
    if not geo_info:
        logger.error("Could not identify census geography for area")
        return []
    
    state_fips = geo_info["state_fips"]
    county_fips = geo_info["county_fips"]
    
    # Fetch block groups for the county
    block_groups = fetch_tiger_block_groups(state_fips, county_fips)
    
    # Filter to those that intersect the geometry
    result = []
    for bg in block_groups:
        bg_geom = shape(bg["geometry"])
        if geometry.intersects(bg_geom):
            # Calculate area
            import pyproj
            from shapely.ops import transform
            
            project = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
            bg_geom_projected = transform(project, bg_geom)
            area_sq_m = bg_geom_projected.area
            area_sq_km = area_sq_m / 1_000_000
            
            bg["area_sq_km"] = area_sq_km
            result.append(bg)
    
    logger.info(f"Found {len(result)} block groups in area")
    return result


def fetch_tiger_block_groups(state_fips: str, county_fips: str) -> List[Dict[str, Any]]:
    """Fetch block group geometries from Census TIGER/Line files.
    
    Args:
        state_fips: State FIPS code (2 digits)
        county_fips: County FIPS code (3 digits)
    
    Returns:
        List of block group dicts with geometry
    """
    # Use Census TIGER/Line REST API
    year = 2023
    url = f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS{year}/MapServer/8/query"
    
    # Build query parameters
    params = {
        "where": f"STATE='{state_fips}' AND COUNTY='{county_fips}'",
        "outFields": "GEOID,STATE,COUNTY,TRACT,BLKGRP",
        "outSR": "4326",
        "f": "geojson"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        features = data.get("features", [])
        
        result = []
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            
            if geom and props.get("GEOID"):
                result.append({
                    "geoid": props["GEOID"],
                    "state_fips": props.get("STATE", ""),
                    "county_fips": props.get("COUNTY", ""),
                    "tract": props.get("TRACT", ""),
                    "block_group": props.get("BLKGRP", ""),
                    "geometry": geom
                })
        
        logger.debug(f"Fetched {len(result)} block groups for {state_fips}-{county_fips}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch block groups: {e}")
        
    # Fallback: try alternative method
    return fetch_block_groups_alternative(state_fips, county_fips)


def fetch_block_groups_alternative(state_fips: str, county_fips: str) -> List[Dict[str, Any]]:
    """Alternative method to fetch block groups using direct shapefile access."""
    try:
        # Try using geopandas to read from Census FTP
        url = f"https://www2.census.gov/geo/tiger/TIGER2023/BG/tl_2023_{state_fips}_bg.zip"
        
        gdf = gpd.read_file(url)
        
        # Filter to county
        gdf = gdf[gdf['COUNTYFP'] == county_fips]
        
        result = []
        for _, row in gdf.iterrows():
            result.append({
                "geoid": row['GEOID'],
                "state_fips": row['STATEFP'],
                "county_fips": row['COUNTYFP'],
                "tract": row['TRACTCE'],
                "block_group": row['BLKGRPCE'],
                "geometry": row['geometry'].__geo_interface__
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Alternative block group fetch failed: {e}")
        return []


def fetch_census_data(
    geoids: List[str],
    variables: List[str],
    year: int = 2023
) -> Dict[str, Dict[str, Any]]:
    """Fetch census data for specified GEOIDs and variables.
    
    Args:
        geoids: List of census GEOID strings
        variables: List of census variable codes
        year: Census year
    
    Returns:
        Dict mapping GEOID to variable data
    """
    if not geoids or not variables:
        return {}
    
    # Census API base URL
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    
    # Get API key from environment
    api_key = os.getenv("CENSUS_API_KEY")
    
    # Group GEOIDs by state (first 2 digits)
    from collections import defaultdict
    geoids_by_state = defaultdict(list)
    for geoid in geoids:
        if len(geoid) >= 2:
            state = geoid[:2]
            geoids_by_state[state].append(geoid)
    
    result = {}
    
    for state, state_geoids in geoids_by_state.items():
        # Build query - Census API has limits, so batch if needed
        batch_size = 50
        for i in range(0, len(state_geoids), batch_size):
            batch = state_geoids[i:i + batch_size]
            
            # Parse GEOIDs to get tract and block group
            for geoid in batch:
                if len(geoid) == 12:  # State + County + Tract + Block Group
                    county = geoid[2:5]
                    tract = geoid[5:11]
                    block_group = geoid[11:12]
                    
                    # Build query parameters
                    params = {
                        "get": ",".join(["NAME"] + variables),
                        "for": f"block group:{block_group}",
                        "in": f"state:{state} county:{county} tract:{tract}"
                    }
                    
                    if api_key:
                        params["key"] = api_key
                    
                    try:
                        response = requests.get(base_url, params=params, timeout=10)
                        response.raise_for_status()
                        
                        data = response.json()
                        if len(data) > 1:  # First row is headers
                            headers = data[0]
                            values = data[1]
                            
                            # Build result dict for this GEOID
                            geoid_data = {}
                            for j, header in enumerate(headers):
                                if header in variables:
                                    try:
                                        geoid_data[header] = float(values[j]) if values[j] else None
                                    except (ValueError, TypeError):
                                        geoid_data[header] = values[j]
                            
                            # Map back to human-readable names too
                            reverse_mapping = {v: k for k, v in VARIABLE_MAPPING.items()}
                            for var_code, value in geoid_data.items():
                                if var_code in reverse_mapping:
                                    geoid_data[reverse_mapping[var_code]] = value
                            
                            result[geoid] = geoid_data
                            
                    except Exception as e:
                        logger.warning(f"Failed to fetch census data for {geoid}: {e}")
    
    logger.info(f"Fetched census data for {len(result)}/{len(geoids)} GEOIDs")
    return result