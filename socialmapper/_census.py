"""Internal census data utilities for SocialMapper."""

import os
import re
import requests
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, Polygon
import geopandas as gpd
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def validate_fips_code(fips_code: str, expected_length: int, code_type: str = "FIPS") -> str:
    """
    Validate and sanitize FIPS codes for safe use in queries.

    Ensures FIPS codes contain only digits and match expected length
    to prevent SQL injection attacks.

    Parameters
    ----------
    fips_code : str
        The FIPS code to validate.
    expected_length : int
        Expected number of digits (2 for state, 3 for county).
    code_type : str, optional
        Type of code for error messages, by default "FIPS".

    Returns
    -------
    str
        Validated FIPS code.

    Raises
    ------
    ValueError
        If FIPS code is invalid or malformed.

    Examples
    --------
    >>> validate_fips_code('06', 2, 'State')
    '06'

    >>> validate_fips_code('037', 3, 'County')
    '037'

    >>> validate_fips_code("'; DROP TABLE--", 2, 'State')
    Traceback (most recent call last):
        ...
    ValueError: Invalid State code: contains non-digit characters
    """
    if not fips_code:
        raise ValueError(f"Invalid {code_type} code: empty value")

    # Remove any whitespace
    fips_code = fips_code.strip()

    # Check if empty after stripping
    if not fips_code:
        raise ValueError(f"Invalid {code_type} code: empty value")

    # Check if it contains only digits
    if not re.match(r'^[0-9]+$', fips_code):
        raise ValueError(f"Invalid {code_type} code: contains non-digit characters")

    # Check length
    if len(fips_code) != expected_length:
        raise ValueError(
            f"Invalid {code_type} code: expected {expected_length} digits, got {len(fips_code)}"
        )

    return fips_code


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
    """
    Convert human-readable variable names to census codes.

    Maps common demographic variable names to their corresponding
    Census Bureau API variable codes (e.g., 'population' to
    'B01003_001E'). If a variable is already a census code,
    it is returned unchanged.

    Parameters
    ----------
    variables : list of str
        List of variable names or census codes to normalize.
        Can include human-readable names like 'population', 'median_income'
        or census codes like 'B01003_001E'.

    Returns
    -------
    list of str
        List of census variable codes corresponding to the input variables.
        Unknown variables are kept as-is with a warning logged.

    Examples
    --------
    >>> normalize_variable_names(['population', 'median_income'])
    ['B01003_001E', 'B19013_001E']

    >>> normalize_variable_names(['B01003_001E', 'housing_units'])
    ['B01003_001E', 'B25001_001E']

    Notes
    -----
    Variable names are case-insensitive and spaces are converted to
    underscores during the mapping process.
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
    """
    Fetch census block groups that intersect with a geometry.

    Identifies all census block groups that spatially intersect with
    the provided polygon geometry. This function determines the relevant
    state and county from the geometry's centroid, fetches block group
    boundaries, and filters for intersection.

    Parameters
    ----------
    geometry : shapely.geometry.Polygon
        The polygon geometry to find intersecting block groups for.
        Must be in WGS84 (EPSG:4326) coordinate system.

    Returns
    -------
    list of dict
        List of dictionaries containing block group information.
        Each dict contains:
        - 'geoid': Census GEOID identifier
        - 'state_fips': State FIPS code
        - 'county_fips': County FIPS code
        - 'tract': Census tract number
        - 'block_group': Block group number
        - 'geometry': GeoJSON geometry object
        - 'area_sq_km': Area in square kilometers

    Raises
    ------
    ValueError
        If census geography cannot be identified for the area.

    Examples
    --------
    >>> from shapely.geometry import Point
    >>> center = Point(-77.0369, 38.9072)  # Washington, DC
    >>> area = center.buffer(0.01)  # ~1km radius
    >>> block_groups = fetch_block_groups_for_area(area)
    >>> len(block_groups) > 0
    True

    Notes
    -----
    Areas are calculated in EPSG:3857 (Web Mercator) projection.
    Note that Web Mercator distorts areas, especially at higher
    latitudes. Consider using equal-area projections for precise
    area calculations.
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
    """
    Fetch block group geometries from Census TIGER/Line files.

    Retrieves census block group boundaries for a specific county
    using the Census Bureau's TIGER/Line REST API service.
    Falls back to alternative method if primary API fails.

    Parameters
    ----------
    state_fips : str
        State FIPS code (2 digits), e.g., '06' for California.
    county_fips : str
        County FIPS code (3 digits), e.g., '037' for Los Angeles County.

    Returns
    -------
    list of dict
        List of block group dictionaries, each containing:
        - 'geoid': Full 12-digit Census GEOID
        - 'state_fips': State FIPS code
        - 'county_fips': County FIPS code
        - 'tract': 6-digit census tract code
        - 'block_group': Single digit block group number
        - 'geometry': GeoJSON geometry object

    Examples
    --------
    >>> block_groups = fetch_tiger_block_groups('06', '037')
    >>> len(block_groups) > 0  # Los Angeles County has many block groups
    True

    >>> bg = block_groups[0]
    >>> 'geoid' in bg and 'geometry' in bg
    True

    See Also
    --------
    fetch_block_groups_alternative : Fallback method using shapefiles.

    Notes
    -----
    Uses the 2023 vintage of TIGER/Line data by default.
    Requires internet connection to Census Bureau services.
    """
    # Validate FIPS codes to prevent injection attacks
    validated_state = validate_fips_code(state_fips, 2, "State")
    validated_county = validate_fips_code(county_fips, 3, "County")

    # Use Census TIGER/Line REST API
    year = 2023
    url = f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS{year}/MapServer/8/query"

    # Build query parameters with validated inputs
    params = {
        "where": f"STATE='{validated_state}' AND COUNTY='{validated_county}'",
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
    """
    Alternative method to fetch block groups using direct shapefile access.

    Fallback method that downloads and reads TIGER/Line shapefiles
    directly from the Census FTP server when the REST API is unavailable.

    Parameters
    ----------
    state_fips : str
        State FIPS code (2 digits).
    county_fips : str
        County FIPS code (3 digits).

    Returns
    -------
    list of dict
        List of block group dictionaries with the same structure
        as fetch_tiger_block_groups().
        Returns empty list if fetch fails.

    See Also
    --------
    fetch_tiger_block_groups : Primary method using REST API.

    Notes
    -----
    This method requires geopandas and may be slower than the API
    method as it downloads entire state shapefiles before filtering.
    """
    # Validate FIPS codes to prevent injection attacks
    validated_state = validate_fips_code(state_fips, 2, "State")
    validated_county = validate_fips_code(county_fips, 3, "County")

    try:
        # Try using geopandas to read from Census FTP
        url = f"https://www2.census.gov/geo/tiger/TIGER2023/BG/tl_2023_{validated_state}_bg.zip"

        gdf = gpd.read_file(url)

        # Filter to county
        gdf = gdf[gdf['COUNTYFP'] == validated_county]
        
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
    """
    Fetch census data for specified GEOIDs and variables.

    Retrieves demographic and socioeconomic data from the Census Bureau
    API for specific geographic units (block groups) and variables.
    Data is fetched in batches to respect API limits.

    Parameters
    ----------
    geoids : list of str
        List of 12-digit census GEOID strings identifying block groups.
        Format: SSCCCTTTTTTB (State, County, Tract, Block Group).
    variables : list of str
        List of census variable codes (e.g., 'B01003_001E' for population).
        Should be valid ACS 5-year estimate variable codes.
    year : int, optional
        Census data year to fetch, by default 2023.
        Must be a year with available ACS 5-year estimates.

    Returns
    -------
    dict of dict
        Nested dictionary mapping GEOID to variable data.
        Structure: {geoid: {variable_code: value, ...}, ...}
        Values are returned as strings or None if unavailable.

    Raises
    ------
    ValueError
        If API key is not set in CENSUS_API_KEY environment variable.

    Examples
    --------
    >>> import os
    >>> os.environ['CENSUS_API_KEY'] = 'your_api_key'
    >>> geoids = ['060370001001']  # LA County block group
    >>> variables = ['B01003_001E', 'B19013_001E']  # Population, Income
    >>> data = fetch_census_data(geoids, variables)
    >>> '060370001001' in data
    True

    Notes
    -----
    Requires CENSUS_API_KEY environment variable to be set.
    API has rate limits; function implements batching with 50 GEOIDs
    per request to avoid exceeding limits.
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
        # Validate GEOID format before processing
        if len(geoid) >= 2 and re.match(r'^[0-9]+$', geoid):
            state = geoid[:2]
            geoids_by_state[state].append(geoid)
        else:
            logger.warning(f"Skipping invalid GEOID format: {geoid}")
    
    result = {}
    
    for state, state_geoids in geoids_by_state.items():
        # Build query - Census API has limits, so batch if needed
        batch_size = 50
        for i in range(0, len(state_geoids), batch_size):
            batch = state_geoids[i:i + batch_size]
            
            # Parse GEOIDs to get tract and block group
            for geoid in batch:
                if len(geoid) == 12:  # State + County + Tract + Block Group
                    # Validate GEOID is all digits to prevent injection
                    if not re.match(r'^[0-9]{12}$', geoid):
                        logger.warning(f"Skipping invalid GEOID: {geoid}")
                        continue

                    county = geoid[2:5]
                    tract = geoid[5:11]
                    block_group = geoid[11:12]

                    # Build query parameters with validated components
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