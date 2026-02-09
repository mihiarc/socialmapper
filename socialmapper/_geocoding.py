"""Internal geocoding utilities for SocialMapper.

This module provides low-level geocoding functions used internally
by SocialMapper. For user-facing geocoding functionality with advanced
features like batch processing, quality validation, and multiple
providers, use the `socialmapper.geocoding` package instead.

Functions
---------
geocode_location : Simple address-to-coordinates geocoding
geocode_with_census : US Census geocoder fallback
get_census_geography : Reverse geocode to census geography IDs
"""

import json
import logging
import threading
import time

import requests

from .constants import (
    CENSUS_GEOCODER_GEOGRAPHIES_URL,
    CENSUS_GEOCODER_LOCATIONS_URL,
    GEOCODING_TIMEOUT,
    NOMINATIM_API_URL,
    USER_AGENT,
)
from .performance.bounded_cache import BoundedCache
from .performance.connection_pool import get_http_session

logger = logging.getLogger(__name__)

# In-memory cache for census geography lookups, keyed by rounded coords (bounded LRU)
_geocoding_cache: BoundedCache = BoundedCache(maxsize=1024)

# Nominatim rate limiting: minimum 1 second between requests (usage policy)
_nominatim_lock = threading.Lock()
_last_nominatim_call: float = 0.0


def geocode_location(address: str) -> tuple[float, float]:
    """
    Geocode an address string to coordinates.

    Converts human-readable addresses to geographic coordinates using
    OpenStreetMap's Nominatim service as primary provider, with US Census
    geocoder as fallback. Focuses on US addresses for optimal accuracy.

    Parameters
    ----------
    address : str
        Address string to geocode. Can be partial ("City, State")
        or full street address ("123 Main St, City, State ZIP").

    Returns
    -------
    tuple of float
        Tuple containing (latitude, longitude) in decimal degrees.

    Raises
    ------
    InvalidLocationError
        If geocoding fails for all providers.
    requests.RequestException
        If network request fails with timeout or connection error.

    Examples
    --------
    >>> coords = geocode_location("Seattle, WA")
    >>> coords is not None
    True
    >>> lat, lon = coords
    >>> 47.5 < lat < 47.7 and -122.4 < lon < -122.2
    True

    >>> geocode_location("1600 Pennsylvania Ave, Washington, DC")
    (38.8976, -77.0365)  # Approximate coordinates

    See Also
    --------
    geocode_with_census : Direct Census geocoder implementation.

    Notes
    -----
    Includes rate limiting and proper User-Agent headers to respect
    service providers' usage policies. Results are logged at debug level.
    """
    # Try Nominatim first (no API key needed)
    session = get_http_session()
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "us"  # Focus on US addresses
    }
    headers = {
        "User-Agent": USER_AGENT
    }

    # Enforce Nominatim rate limit (1 request per second)
    global _last_nominatim_call
    with _nominatim_lock:
        elapsed = time.monotonic() - _last_nominatim_call
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        _last_nominatim_call = time.monotonic()

    try:
        response = session.get(
            NOMINATIM_API_URL, params=params, headers=headers, timeout=GEOCODING_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        if data:
            result = data[0]
            lat = float(result["lat"])
            lon = float(result["lon"])
            logger.debug("Geocoded '%s' to (%s, %s)", address, lat, lon)
            return (lat, lon)

    except requests.Timeout:
        logger.warning("Nominatim geocoding timed out for '%s'", address)
        # Try fallback before giving up
    except requests.RequestException as e:
        logger.warning("Nominatim geocoding network error for '%s': %s", address, e)
        # Try fallback before giving up
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("Nominatim geocoding failed to parse response for '%s': %s", address, e)
        # Try fallback before giving up

    # Fallback to Census geocoder
    result = geocode_with_census(address)

    # If both failed, raise helpful error
    if result is None:
        from .exceptions import InvalidLocationError
        raise InvalidLocationError(
            address,
            suggestions=[
                "Portland, OR",
                "Seattle, WA",
                "New York, NY",
                "Los Angeles, CA"
            ]
        )

    return result


def geocode_with_census(address: str) -> tuple[float, float] | None:
    """
    Geocode using US Census geocoder as fallback.

    Uses the US Census Bureau's geocoding service for address resolution.
    This service is specifically designed for US addresses and provides
    high accuracy for street-level addresses within the United States.

    Parameters
    ----------
    address : str
        US address string to geocode. Should be a complete US address
        for best results.

    Returns
    -------
    tuple of float or None
        Tuple containing (latitude, longitude) in decimal degrees,
        or None if geocoding fails or address is not found.

    Examples
    --------
    >>> coords = geocode_with_census("350 Fifth Avenue, New York, NY 10118")
    >>> coords is not None
    True

    >>> geocode_with_census("Invalid Address XYZ")
    None

    Notes
    -----
    Only works for addresses within the United States and territories.
    Does not require an API key but has rate limiting.
    Returns the most accurate match from the Census geocoding database.
    """
    session = get_http_session()
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }

    try:
        response = session.get(
            CENSUS_GEOCODER_LOCATIONS_URL, params=params, timeout=GEOCODING_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        if data.get("result") and data["result"].get("addressMatches"):
            match = data["result"]["addressMatches"][0]
            coords = match["coordinates"]
            lat = coords["y"]
            lon = coords["x"]
            logger.debug("Census geocoded '%s' to (%s, %s)", address, lat, lon)
            return (lat, lon)

    except requests.Timeout:
        logger.warning("Census geocoding timed out for '%s'", address)
    except requests.RequestException as e:
        logger.warning("Census geocoding network error for '%s': %s", address, e)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("Census geocoding failed to parse response for '%s': %s", address, e)

    return None


def get_census_geography(lat: float, lon: float) -> dict[str, str] | None:
    """
    Get census geographic identifiers for a point.

    Performs reverse geocoding to identify the census geographic units
    (state, county, tract, block group) that contain a given coordinate point.
    Uses the US Census Bureau's geography API for accurate boundary matching.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees (WGS84).
    lon : float
        Longitude in decimal degrees (WGS84).

    Returns
    -------
    dict of str or None
        Dictionary containing census geography identifiers:
        - 'state_fips': 2-digit state FIPS code
        - 'county_fips': 3-digit county FIPS code
        - 'tract': 6-digit census tract code
        - 'block_group': 1-digit block group number
        - 'geoid': 12-digit combined GEOID
        Returns None if the point cannot be matched to census geography.

    Examples
    --------
    >>> geo = get_census_geography(38.9072, -77.0369)  # Washington, DC
    >>> geo is not None
    True
    >>> 'state_fips' in geo and 'county_fips' in geo
    True
    >>> len(geo['geoid']) == 12
    True

    Notes
    -----
    Uses the 2020 Census block boundaries for geographic matching.
    Only works for coordinates within the United States and territories.
    """
    # Check cache first (round to 4 decimal places ~11m precision)
    cache_key = f"{round(lat, 4)}:{round(lon, 4)}"
    cached = _geocoding_cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache hit for census geography (%.4f, %.4f)", lat, lon)
        # Sentinel empty dict means "no result" (distinguish from never-cached)
        return cached if cached != {} else None

    from .constants import DEFAULT_HTTP_TIMEOUT

    session = get_http_session()
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "2020 Census Blocks",
        "format": "json"
    }

    try:
        response = session.get(
            CENSUS_GEOCODER_GEOGRAPHIES_URL, params=params, timeout=DEFAULT_HTTP_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        if data.get("result") and data["result"].get("geographies"):
            blocks = data["result"]["geographies"].get("2020 Census Blocks", [])
            if blocks:
                block = blocks[0]

                # Extract components
                state_fips = block.get("STATE", "")
                county_fips = block.get("COUNTY", "")
                tract = block.get("TRACT", "")
                block_group = block.get("BLKGRP", "")

                # Create GEOID (state + county + tract + block group)
                geoid = f"{state_fips}{county_fips}{tract}{block_group}"

                result = {
                    "state_fips": state_fips,
                    "county_fips": county_fips,
                    "tract": tract,
                    "block_group": block_group,
                    "geoid": geoid
                }

                # Cache the result
                _geocoding_cache.set(cache_key, result)

                return result

        # No geography data returned
        logger.warning(
            "Census Geocoding API returned no geography data for (%s, %s). "
            "The location may be outside the US or in a territory without census block data.",
            lat, lon,
        )

    except requests.Timeout as e:
        from .exceptions import NetworkError
        logger.warning("Census Geocoding API request timed out for (%s, %s)", lat, lon)
        raise NetworkError(
            "Census Geocoding API",
            "Request timed out"
        ) from e
    except requests.RequestException as e:
        from .exceptions import NetworkError
        logger.warning("Network error accessing Census Geocoding API for (%s, %s): %s", lat, lon, e)
        raise NetworkError(
            "Census Geocoding API",
            str(e)
        ) from e
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        from .exceptions import DataError
        logger.error("Failed to parse census geography response for (%s, %s): %s", lat, lon, e)
        raise DataError(f"Failed to parse census geography response: {e}") from e

    # Cache the negative result (empty dict as sentinel)
    _geocoding_cache.set(cache_key, {})

    return None
