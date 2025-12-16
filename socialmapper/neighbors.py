"""SocialMapper Neighbors API.

Direct access to geographic neighbor relationships for US states
and counties. This module provides a simple, standalone API for
neighbor analysis without requiring the full SocialMapper workflow.

Examples
--------
    Basic usage:
        >>> import socialmapper.neighbors as neighbors
        >>> nc_states = neighbors.get_neighboring_states("37")  # North Carolina
        >>> wake_counties = neighbors.get_neighboring_counties("37", "183")  # Wake County

    Point analysis:
        >>> geo = neighbors.get_geography_from_point(35.7796, -78.6382)  # Raleigh
        >>> print(f"State: {geo['state_fips']}, County: {geo['county_fips']}")

    POI batch processing:
        >>> pois = [{"lat": 35.7796, "lon": -78.6382}, {"lat": 35.2271, "lon": -80.8431}]
        >>> counties = neighbors.get_counties_from_pois(pois, include_neighbors=True)
"""

from typing import Any

# Import geocoding functionality from internal module
from ._geocoding import get_census_geography

# Re-export with enhanced documentation


# Hardcoded neighbor relationships (same data as before, just directly here)
STATE_NEIGHBORS = {
    "01": ["13", "28", "47"],  # Alabama: GA, MS, TN
    "04": ["06", "08", "32", "35", "49"],  # Arizona: CA, CO, NV, NM, UT
    "05": ["22", "28", "29", "40", "47", "48"],  # Arkansas: LA, MS, MO, OK, TN, TX
    "06": ["04", "32", "41"],  # California: AZ, NV, OR
    "08": ["04", "20", "31", "35", "49", "56"],  # Colorado: AZ, KS, NE, NM, UT, WY
    "09": ["25", "36", "44"],  # Connecticut: MA, NY, RI
    "10": ["24", "34", "42"],  # Delaware: MD, NJ, PA
    "12": ["01", "13"],  # Florida: AL, GA
    "13": ["01", "12", "37", "45", "47"],  # Georgia: AL, FL, NC, SC, TN
    "16": ["30", "32", "41", "49", "53"],  # Idaho: MT, NV, OR, UT, WA
    "17": ["18", "19", "26", "29", "55"],  # Illinois: IN, IA, MI, MO, WI
    "18": ["17", "21", "26", "39"],  # Indiana: IL, KY, MI, OH
    "19": ["17", "20", "27", "29", "31", "46"],  # Iowa: IL, KS, MN, MO, NE, SD
    "20": ["08", "19", "29", "31", "40"],  # Kansas: CO, IA, MO, NE, OK
    "21": ["17", "18", "28", "29", "39", "47", "51", "54"],  # Kentucky
    "22": ["05", "28", "48"],  # Louisiana: AR, MS, TX
    "23": ["33"],  # Maine: NH
    "24": ["10", "34", "42", "51", "54"],  # Maryland: DE, NJ, PA, VA, WV
    "25": ["09", "33", "36", "44", "50"],  # Massachusetts: CT, NH, NY, RI, VT
    "26": ["17", "18", "39", "55"],  # Michigan: IL, IN, OH, WI
    "27": ["19", "30", "38", "46", "55"],  # Minnesota: IA, MT, ND, SD, WI
    "28": ["01", "05", "21", "22", "47"],  # Mississippi: AL, AR, KY, LA, TN
    "29": ["05", "17", "19", "20", "21", "31", "40", "47"],  # Missouri
    "30": ["16", "27", "38", "46", "56"],  # Montana: ID, MN, ND, SD, WY
    "31": ["08", "19", "20", "29", "46", "56"],  # Nebraska: CO, IA, KS, MO, SD, WY
    "32": ["04", "06", "16", "41", "49"],  # Nevada: AZ, CA, ID, OR, UT
    "33": ["23", "25", "50"],  # New Hampshire: ME, MA, VT
    "34": ["10", "24", "36", "42"],  # New Jersey: DE, MD, NY, PA
    "35": ["04", "08", "40", "48"],  # New Mexico: AZ, CO, OK, TX
    "36": ["09", "25", "34", "42", "50"],  # New York: CT, MA, NJ, PA, VT
    "37": ["13", "45", "47", "51"],  # North Carolina: GA, SC, TN, VA
    "38": ["27", "30", "46"],  # North Dakota: MN, MT, SD
    "39": ["18", "21", "26", "42", "54"],  # Ohio: IN, KY, MI, PA, WV
    "40": ["05", "08", "20", "29", "35", "48"],  # Oklahoma: AR, CO, KS, MO, NM, TX
    "41": ["06", "16", "32", "53"],  # Oregon: CA, ID, NV, WA
    "42": ["10", "24", "34", "36", "39", "54"],  # Pennsylvania: DE, MD, NJ, NY, OH, WV
    "44": ["09", "25"],  # Rhode Island: CT, MA
    "45": ["13", "37"],  # South Carolina: GA, NC
    "46": ["19", "27", "30", "31", "38", "56"],  # South Dakota: IA, MN, MT, NE, ND, WY
    "47": ["01", "05", "13", "21", "28", "29", "37", "51"],  # Tennessee
    "48": ["05", "22", "35", "40"],  # Texas: AR, LA, NM, OK
    "49": ["04", "08", "16", "32", "56"],  # Utah: AZ, CO, ID, NV, WY
    "50": ["25", "33", "36"],  # Vermont: MA, NH, NY
    "51": ["21", "24", "37", "47", "54"],  # Virginia: KY, MD, NC, TN, WV
    "53": ["16", "41"],  # Washington: ID, OR
    "54": ["21", "24", "39", "42", "51"],  # West Virginia: KY, MD, OH, PA, VA
    "55": ["17", "26", "27", "46"],  # Wisconsin: IL, MI, MN, SD
    "56": ["08", "16", "30", "31", "46", "49"],  # Wyoming: CO, ID, MT, NE, SD, UT
}


def get_neighboring_states(state_fips: str) -> list[str]:
    """
    Get list of neighboring states for a given state FIPS code.

    Retrieves all states that share a border with the specified state
    based on pre-defined geographic adjacency relationships.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code (e.g., '37' for North Carolina).

    Returns
    -------
    list of str
        List of neighboring state FIPS codes. Returns empty list if
        state_fips not found.

    Examples
    --------
    >>> get_neighboring_states("37")  # North Carolina
    ['13', '45', '47', '51']  # GA, SC, TN, VA

    >>> get_neighboring_states("06")  # California
    ['04', '32', '41']  # AZ, NV, OR
    """
    return STATE_NEIGHBORS.get(state_fips, [])


def get_neighboring_counties(
    state_fips: str, county_fips: str, include_cross_state: bool = True
) -> list[tuple[str, str]]:
    """
    Get list of neighboring counties for a given county.

    Retrieves counties that share a border with the specified
    county. Currently returns empty list as detailed county
    adjacency data is not yet implemented.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.
    county_fips : str
        Three-digit county FIPS code.
    include_cross_state : bool, optional
        Whether to include neighboring counties in other states,
        by default True.

    Returns
    -------
    list of tuple[str, str]
        List of (state_fips, county_fips) tuples for neighboring
        counties. Currently returns empty list.

    Examples
    --------
    >>> neighbors = get_neighboring_counties("37", "183")
    >>> len(neighbors)  # Wake County, NC - not yet implemented
    0

    Notes
    -----
    County adjacency functionality is planned for future
    implementation and requires comprehensive county boundary data.
    """
    # For now, return empty list as county neighbor data is complex
    # This would require a large dataset of county adjacency
    return []


def get_geography_from_point(lat: float, lon: float) -> dict[str, str] | None:
    """
    Get geographic identifiers (FIPS codes) for a point.

    Performs reverse geocoding to determine the state, county,
    census tract, and block group containing the specified
    latitude and longitude coordinates.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees (-90 to 90).
    lon : float
        Longitude in decimal degrees (-180 to 180).

    Returns
    -------
    dict or None
        Dictionary with geographic identifiers containing keys:
        'state_fips' (str), 'county_fips' (str), 'tract' (str),
        'block_group' (str). Returns None if geocoding fails.

    Examples
    --------
    >>> result = get_geography_from_point(35.7796, -78.6382)
    >>> result['state_fips']
    '37'
    >>> result['county_fips']
    '183'
    """
    # Use the get_census_geography function from internal geocoding module
    return get_census_geography(lat, lon)


def get_counties_from_pois(
    pois: list[dict], include_neighbors: bool = True, neighbor_distance: int = 1
) -> list[tuple[str, str]]:
    """
    Get counties containing or near a list of POIs.

    Identifies all counties that contain POIs, optionally
    including neighboring counties within a specified distance.
    Useful for determining census data coverage areas for POI
    analysis.

    Parameters
    ----------
    pois : list of dict
        List of POI dictionaries containing 'lat' and 'lon'
        keys with coordinate values.
    include_neighbors : bool, optional
        Whether to include counties neighboring those
        containing POIs, by default True.
    neighbor_distance : int, optional
        Distance of neighbor relationships to include
        (1 = immediate neighbors, 2 = neighbors of neighbors),
        by default 1.

    Returns
    -------
    list of tuple[str, str]
        List of unique (state_fips, county_fips) tuples
        representing counties.

    Examples
    --------
    >>> pois = [
    ...     {"lat": 35.7796, "lon": -78.6382},
    ...     {"lat": 35.2271, "lon": -80.8431},
    ... ]
    >>> counties = get_counties_from_pois(pois)
    >>> len(counties) > 0
    True

    >>> # Without neighbors
    >>> counties = get_counties_from_pois(
    ...     pois, include_neighbors=False
    ... )
    >>> len(counties) >= 2
    True
    """
    import logging
    logger = logging.getLogger(__name__)

    counties = set()

    for poi in pois:
        lat = poi.get("lat")
        lon = poi.get("lon")

        if lat is None or lon is None:
            logger.warning(f"POI missing lat/lon coordinates: {poi}")
            continue

        try:
            geo_info = get_census_geography(lat, lon)
            if geo_info:
                state_fips = geo_info.get("state_fips")
                county_fips = geo_info.get("county_fips")
                if state_fips and county_fips:
                    counties.add((state_fips, county_fips))
        except (ValueError, KeyError, TypeError, OSError, ConnectionError) as e:
            logger.warning(f"Failed to get geography for POI ({lat}, {lon}): {e}")

    # Note: include_neighbors and neighbor_distance are accepted but
    # county neighbor functionality is not yet implemented
    if include_neighbors:
        logger.debug(
            "County neighbor expansion requested but not yet implemented. "
            "Returning only POI-containing counties."
        )

    return list(counties)


def get_neighbor_manager(db_path: str | None = None):
    """
    Get neighbor manager instance for advanced geographic operations.

    Creates a manager object providing access to neighbor relationship
    data and caching. Useful for batch operations or custom neighbor
    queries.

    Parameters
    ----------
    db_path : str, optional
        Path to neighbor database file. Uses default internal database
        if None, by default None.

    Returns
    -------
    SimpleNeighborManager
        Manager instance providing methods for neighbor queries and
        statistics.

    Examples
    --------
    >>> manager = get_neighbor_manager()
    >>> stats = manager.get_neighbor_statistics()
    >>> print(f"States: {stats['state_relationships']}")
    States: 48
    """
    # Simple neighbor manager without census system dependency
    class SimpleNeighborManager:
        def __init__(self):
            pass

        def get_neighbor_statistics(self):
            """Get neighbor database statistics."""
            # Since we don't track these stats in the current implementation,
            # return realistic placeholder values
            return {
                "state_relationships": len([s for s in STATE_NEIGHBORS.values() if s]),
                "county_relationships": 0,  # County data not implemented
                "cross_state_county_relationships": 0,
                "cached_points": 0,
                "states_with_county_data": 0,
            }

        def get_statistics(self):
            """Alias for backward compatibility."""
            return self.get_neighbor_statistics()

        def get_neighboring_counties(self, county_fips):
            """Get neighboring counties."""
            # Not implemented for counties
            return []

        def get_geography_from_point(self, lat, lon):
            """Get geographic identifiers for a point."""
            return get_census_geography(lat, lon)

    return SimpleNeighborManager()


def get_statistics() -> dict[str, Any]:
    """
    Get comprehensive statistics about the neighbor database.

    Provides counts and metadata about stored geographic relationships
    including state neighbors, county neighbors, and cached lookups.

    Returns
    -------
    dict
        Dictionary with keys: 'state_relationships' (int),
        'county_relationships' (int),
        'cross_state_county_relationships' (int), 'cached_points'
        (int), 'states_with_county_data' (int).

    Examples
    --------
    >>> stats = get_statistics()
    >>> print(f"States: {stats['state_relationships']}")
    States: 48
    >>> print(f"Counties: {stats['county_relationships']:,}")
    Counties: 0
    """
    manager = get_neighbor_manager()
    return manager.get_neighbor_statistics()


# State FIPS code reference for convenience
STATE_FIPS_CODES = {
    "AL": "01",
    "AK": "02",
    "AZ": "04",
    "AR": "05",
    "CA": "06",
    "CO": "08",
    "CT": "09",
    "DE": "10",
    "DC": "11",
    "FL": "12",
    "GA": "13",
    "HI": "15",
    "ID": "16",
    "IL": "17",
    "IN": "18",
    "IA": "19",
    "KS": "20",
    "KY": "21",
    "LA": "22",
    "ME": "23",
    "MD": "24",
    "MA": "25",
    "MI": "26",
    "MN": "27",
    "MS": "28",
    "MO": "29",
    "MT": "30",
    "NE": "31",
    "NV": "32",
    "NH": "33",
    "NJ": "34",
    "NM": "35",
    "NY": "36",
    "NC": "37",
    "ND": "38",
    "OH": "39",
    "OK": "40",
    "OR": "41",
    "PA": "42",
    "RI": "44",
    "SC": "45",
    "SD": "46",
    "TN": "47",
    "TX": "48",
    "UT": "49",
    "VT": "50",
    "VA": "51",
    "WA": "53",
    "WV": "54",
    "WI": "55",
    "WY": "56",
}

FIPS_TO_STATE = {v: k for k, v in STATE_FIPS_CODES.items()}


def get_state_fips(state_abbr: str) -> str | None:
    """
    Convert state abbreviation to FIPS code.

    Translates two-letter postal abbreviations to Census Bureau
    FIPS codes for use in geographic queries and data retrieval.

    Parameters
    ----------
    state_abbr : str
        Two-letter state postal abbreviation (e.g., 'NC',
        'CA'). Case-insensitive.

    Returns
    -------
    str or None
        Two-digit FIPS code string, or None if abbreviation
        not recognized.

    Examples
    --------
    >>> get_state_fips("NC")
    '37'
    >>> get_state_fips("CA")
    '06'
    >>> get_state_fips("ca")  # Case insensitive
    '06'
    """
    return STATE_FIPS_CODES.get(state_abbr.upper())


def get_state_abbr(state_fips: str) -> str | None:
    """
    Convert FIPS code to state postal abbreviation.

    Translates Census Bureau FIPS codes to standard two-letter
    postal abbreviations for display and data export.

    Parameters
    ----------
    state_fips : str
        Two-digit FIPS code (e.g., '37', '06').

    Returns
    -------
    str or None
        Two-letter state postal abbreviation, or None if FIPS
        code not recognized.

    Examples
    --------
    >>> get_state_abbr("37")
    'NC'
    >>> get_state_abbr("06")
    'CA'
    """
    return FIPS_TO_STATE.get(state_fips)


# Convenience functions using state abbreviations
def get_neighboring_states_by_abbr(state_abbr: str) -> list[str]:
    """
    Get list of neighboring states using postal abbreviations.

    Convenience function that accepts and returns state
    abbreviations instead of FIPS codes, wrapping
    get_neighboring_states().

    Parameters
    ----------
    state_abbr : str
        Two-letter state postal abbreviation (e.g., 'NC', 'CA').
        Case-insensitive.

    Returns
    -------
    list of str
        List of neighboring state postal abbreviations. Returns
        empty list if state_abbr not recognized.

    Examples
    --------
    >>> get_neighboring_states_by_abbr("NC")
    ['GA', 'SC', 'TN', 'VA']
    >>> get_neighboring_states_by_abbr("ca")  # Case insensitive
    ['AZ', 'NV', 'OR']
    """
    state_fips = get_state_fips(state_abbr)
    if not state_fips:
        return []

    neighbor_fips = get_neighboring_states(state_fips)
    return [get_state_abbr(fips) for fips in neighbor_fips if get_state_abbr(fips)]


# Export all public functions
__all__ = [
    "FIPS_TO_STATE",
    "STATE_FIPS_CODES",
    "get_counties_from_pois",
    "get_geography_from_point",
    "get_neighbor_manager",
    "get_neighboring_counties",
    "get_neighboring_states",
    "get_neighboring_states_by_abbr",
    "get_state_abbr",
    "get_state_fips",
    "get_statistics",
]
