"""Internal census data utilities for SocialMapper."""

import json
import logging
import re
from typing import Any

import requests
from shapely.geometry import Polygon, shape

from .constants import (
    CENSUS_API_TIMEOUT,
    CENSUS_BATCH_SIZE,
    HTTP_FORBIDDEN,
    HTTP_RATE_LIMITED,
)
from .performance.connection_pool import get_http_session

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
    'households_with_vehicle': 'B08201_001E',  # Total households (subtract no_vehicle)
    'households_no_vehicle': 'B08201_002E',  # Households with no vehicle available
    'median_home_value': 'B25077_001E',
    'median_rent': 'B25064_001E',
}


def normalize_variable_names(variables: list[str]) -> list[str]:
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


def fetch_block_groups_for_area(geometry: Polygon) -> list[dict[str, Any]]:
    """
    Fetch census block groups that intersect with a geometry.

    Identifies all census block groups that spatially intersect with
    the provided polygon geometry. This function samples multiple points
    around the geometry to identify ALL counties that may contain block
    groups, fetches boundaries from each county, and filters for intersection.

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
    Areas are calculated using equal-area projections:
    - EPSG:5070 (NAD83 / Conus Albers) for contiguous US locations
    - EPSG:6933 (NSIDC EASE-Grid 2.0 Global) for other locations
    This provides accurate area measurements within ~0.1-2%.

    This function samples the centroid plus points around the boundary
    to ensure coverage when the geometry spans multiple counties.
    """
    from ._geocoding import get_census_geography

    # Sample multiple points to identify ALL counties that intersect the geometry
    # This handles isochrones that span multiple counties
    sample_points = []

    # Always include centroid
    centroid = geometry.centroid
    sample_points.append((centroid.y, centroid.x))

    # Sample points around the boundary
    try:
        boundary = geometry.exterior
        # Sample at regular intervals along the boundary (8 points)
        for i in range(8):
            fraction = i / 8
            point = boundary.interpolate(fraction, normalized=True)
            sample_points.append((point.y, point.x))

        # Also sample from bounding box corners
        minx, miny, maxx, maxy = geometry.bounds
        sample_points.extend([
            (miny, minx),  # SW corner
            (miny, maxx),  # SE corner
            (maxy, minx),  # NW corner
            (maxy, maxx),  # NE corner
        ])
    except Exception as e:
        logger.warning(f"Could not sample boundary points: {e}")

    # Collect unique state/county combinations
    counties: set[tuple[str, str]] = set()
    for lat, lon in sample_points:
        try:
            geo_info = get_census_geography(lat, lon)
            if geo_info:
                counties.add((geo_info["state_fips"], geo_info["county_fips"]))
        except Exception as e:
            logger.debug(f"Could not get geography for ({lat:.4f}, {lon:.4f}): {e}")
            continue

    if not counties:
        logger.warning(
            f"Could not identify census geography for area at ({centroid.y:.4f}, {centroid.x:.4f}). "
            f"Possible reasons: "
            f"1) Location is outside the United States, "
            f"2) Census Geocoding API is unavailable (network issue), "
            f"3) Coordinates are in a territory without census data. "
            f"Try checking your internet connection or using US mainland coordinates."
        )
        return []

    logger.info(f"Identified {len(counties)} counties for census block query: {counties}")

    # Fetch block groups from ALL identified counties
    all_block_groups = []
    for state_fips, county_fips in counties:
        try:
            block_groups = fetch_tiger_block_groups(state_fips, county_fips)
            all_block_groups.extend(block_groups)
            logger.debug(f"Fetched {len(block_groups)} block groups from {state_fips}-{county_fips}")
        except Exception as e:
            logger.warning(f"Failed to fetch block groups for {state_fips}-{county_fips}: {e}")
            continue

    # Filter to those that intersect the geometry (with deduplication)
    seen_geoids: set[str] = set()
    result = []
    for bg in all_block_groups:
        geoid = bg.get("geoid", "")
        if geoid in seen_geoids:
            continue
        seen_geoids.add(geoid)

        bg_geom = shape(bg["geometry"])
        if geometry.intersects(bg_geom):
            # Calculate area using equal-area projection
            from shapely.ops import transform

            from .helpers import get_equal_area_transformer

            # Determine appropriate projection based on location
            bg_centroid = bg_geom.centroid
            lon, lat = bg_centroid.x, bg_centroid.y

            # Use helper to get appropriate equal-area transformer
            transformer = get_equal_area_transformer(lat, lon)
            bg_geom_projected = transform(transformer.transform, bg_geom)
            area_sq_m = bg_geom_projected.area
            area_sq_km = area_sq_m / 1_000_000

            bg["area_sq_km"] = area_sq_km
            result.append(bg)

    logger.info(f"Found {len(result)} block groups in area (from {len(counties)} counties)")
    return result


def fetch_tiger_block_groups(state_fips: str, county_fips: str) -> list[dict[str, Any]]:
    """
    Fetch block group geometries from Census TIGER/Line shapefiles.

    Retrieves census block group boundaries for a specific county by
    downloading TIGER/Line shapefiles directly from the Census Bureau FTP server.

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
        Returns empty list if fetch fails.

    Examples
    --------
    >>> block_groups = fetch_tiger_block_groups('06', '037')
    >>> len(block_groups) > 0  # Los Angeles County has many block groups
    True

    >>> bg = block_groups[0]
    >>> 'geoid' in bg and 'geometry' in bg
    True

    Notes
    -----
    Uses the 2023 vintage of TIGER/Line data by default.
    Requires internet connection to Census Bureau FTP server.
    Downloads entire state shapefile and filters to county.
    """
    # Validate FIPS codes to prevent injection attacks
    validated_state = validate_fips_code(state_fips, 2, "State")
    validated_county = validate_fips_code(county_fips, 3, "County")

    try:
        # Use TIGERweb Tracts_Blocks query service (efficient, no large downloads)
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"

        params = {
            "where": f"STATE='{validated_state}' AND COUNTY='{validated_county}'",
            "outFields": "GEOID,STATE,COUNTY,TRACT,BLKGRP",
            "outSR": "4326",
            "f": "geojson"
        }

        logger.debug(f"Querying block groups for state {state_fips}, county {county_fips}")
        session = get_http_session()
        response = session.get(url, params=params, timeout=CENSUS_API_TIMEOUT)
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

    except requests.Timeout as e:
        from .exceptions import NetworkError
        logger.warning(
            f"Request timeout accessing TIGERweb service for state {state_fips}, county {county_fips}"
        )
        raise NetworkError(
            "TIGERweb (Census Geography)",
            "Request timed out"
        ) from e
    except requests.RequestException as e:
        from .exceptions import NetworkError
        logger.warning(
            f"Network error accessing TIGERweb service for state {state_fips}, county {county_fips}: {e}"
        )
        raise NetworkError(
            "TIGERweb (Census Geography)",
            str(e)
        ) from e
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse block groups for {state_fips}-{county_fips}: {e}")
        from .exceptions import DataError
        raise DataError(f"Failed to parse census block groups response: {e}") from e


def fetch_census_data(
    geoids: list[str],
    variables: list[str],
    year: int = 2023
) -> dict[str, dict[str, Any]]:
    """
    Fetch census data for specified GEOIDs and variables.

    Retrieves demographic and socioeconomic data from the Census Bureau
    API for specific geographic units (block groups) and variables.
    Uses efficient batching by grouping GEOIDs by tract and fetching
    all block groups per tract in a single API call.

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
    Uses efficient batching: groups GEOIDs by tract and fetches all
    block groups per tract using wildcard queries. This reduces API
    calls from N (one per GEOID) to T (one per unique tract).
    """
    if not geoids or not variables:
        return {}

    # Census API base URL
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"

    # Get API key from environment variable
    import os
    api_key = os.environ.get("CENSUS_API_KEY")

    # Build reverse mapping for human-readable names (computed once)
    from collections import defaultdict
    reverse_mapping = defaultdict(list)
    for name, code in VARIABLE_MAPPING.items():
        reverse_mapping[code].append(name)

    # Group GEOIDs by tract (state + county + tract = first 11 digits)
    # This allows us to use wildcard queries to fetch all block groups per tract
    geoids_by_tract: dict[str, set[str]] = defaultdict(set)
    requested_geoids = set()

    for geoid in geoids:
        # Validate GEOID format: must be 12 digits
        if not re.match(r'^[0-9]{12}$', geoid):
            logger.warning(f"Skipping invalid GEOID format: {geoid}")
            continue

        tract_key = geoid[:11]  # State (2) + County (3) + Tract (6)
        geoids_by_tract[tract_key].add(geoid)
        requested_geoids.add(geoid)

    result = {}
    total_api_calls = 0

    # Process tracts in batches to respect rate limits
    tract_keys = list(geoids_by_tract.keys())

    for batch_start in range(0, len(tract_keys), CENSUS_BATCH_SIZE):
        batch_tracts = tract_keys[batch_start:batch_start + CENSUS_BATCH_SIZE]

        for tract_key in batch_tracts:
            state = tract_key[:2]
            county = tract_key[2:5]
            tract = tract_key[5:11]
            target_geoids = geoids_by_tract[tract_key]

            # Use wildcard to fetch ALL block groups in this tract at once
            params = {
                "get": ",".join(["NAME", *variables]),
                "for": "block group:*",  # Wildcard: get all block groups in tract
                "in": f"state:{state} county:{county} tract:{tract}"
            }

            if api_key:
                params["key"] = api_key

            try:
                session = get_http_session()
                response = session.get(base_url, params=params, timeout=CENSUS_API_TIMEOUT)
                response.raise_for_status()
                total_api_calls += 1

                data = response.json()
                if len(data) > 1:  # First row is headers
                    headers = data[0]

                    # Find column indices for reconstructing GEOID
                    state_idx = headers.index("state") if "state" in headers else None
                    county_idx = headers.index("county") if "county" in headers else None
                    tract_idx = headers.index("tract") if "tract" in headers else None
                    bg_idx = headers.index("block group") if "block group" in headers else None

                    # Process each row (skip header row)
                    for row in data[1:]:
                        # Reconstruct GEOID from response columns
                        if all(idx is not None for idx in [state_idx, county_idx, tract_idx, bg_idx]):
                            row_geoid = (
                                f"{row[state_idx]}{row[county_idx]}"
                                f"{row[tract_idx]}{row[bg_idx]}"
                            )
                        else:
                            # Fallback: construct from known tract + block group position
                            row_geoid = f"{tract_key}{row[-1]}"

                        # Only include if this GEOID was in our request
                        if row_geoid not in target_geoids:
                            continue

                        # Build result dict for this GEOID
                        geoid_data = {}
                        for j, header in enumerate(headers):
                            if header in variables:
                                try:
                                    geoid_data[header] = float(row[j]) if row[j] else None
                                except (ValueError, TypeError):
                                    geoid_data[header] = row[j]

                        # Map census codes to human-readable names
                        for var_code, value in list(geoid_data.items()):
                            if var_code in reverse_mapping:
                                for alias in reverse_mapping[var_code]:
                                    geoid_data[alias] = value

                        result[row_geoid] = geoid_data

            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == HTTP_FORBIDDEN:
                    from .exceptions import MissingAPIKeyError
                    logger.error(f"Census API authentication failed for tract {tract_key}")
                    raise MissingAPIKeyError("Census") from e
                elif e.response is not None and e.response.status_code == HTTP_RATE_LIMITED:
                    from .exceptions import RateLimitError
                    logger.warning(f"Census API rate limit exceeded for tract {tract_key}")
                    raise RateLimitError("Census API") from e
                else:
                    from .exceptions import InvalidAPIResponseError
                    status = e.response.status_code if e.response else None
                    raise InvalidAPIResponseError(
                        "Census API",
                        status_code=status,
                        details=str(e)
                    ) from e
            except requests.Timeout as e:
                from .exceptions import NetworkError
                logger.warning(f"Census API request timed out for tract {tract_key}")
                raise NetworkError("Census API", "Request timed out") from e
            except requests.RequestException as e:
                from .exceptions import NetworkError
                logger.warning(f"Network error fetching census data for tract {tract_key}: {e}")
                raise NetworkError("Census API", str(e)) from e
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse census data for tract {tract_key}: {e}")
                from .exceptions import DataError
                raise DataError(f"Failed to parse census API response: {e}") from e

        # Add small delay between batches to respect rate limits
        if batch_start + CENSUS_BATCH_SIZE < len(tract_keys):
            import time

            from .constants import CENSUS_BATCH_DELAY
            time.sleep(CENSUS_BATCH_DELAY)

    logger.info(
        f"Fetched census data for {len(result)}/{len(requested_geoids)} GEOIDs "
        f"using {total_api_calls} API calls (grouped by {len(geoids_by_tract)} tracts)"
    )
    return result
