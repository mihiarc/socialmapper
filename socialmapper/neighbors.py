"""
SocialMapper Neighbors API

Direct access to geographic neighbor relationships for US states and counties.
This module provides a simple, standalone API for neighbor analysis without
requiring the full SocialMapper workflow.

Examples:
    Basic usage:
        >>> import socialmapper.neighbors as neighbors
        >>> nc_states = neighbors.get_neighboring_states('37')  # North Carolina
        >>> wake_counties = neighbors.get_neighboring_counties('37', '183')  # Wake County
    
    Point analysis:
        >>> geo = neighbors.get_geography_from_point(35.7796, -78.6382)  # Raleigh
        >>> print(f"State: {geo['state_fips']}, County: {geo['county_fips']}")
    
    POI batch processing:
        >>> pois = [{'lat': 35.7796, 'lon': -78.6382}, {'lat': 35.2271, 'lon': -80.8431}]
        >>> counties = neighbors.get_counties_from_pois(pois, include_neighbors=True)
"""

from typing import List, Tuple, Dict, Optional, Any

# Import all neighbor functionality from the census module
from .census import (
    get_neighboring_states as _get_neighboring_states,
    get_neighboring_counties as _get_neighboring_counties,
    get_geography_from_point as _get_geography_from_point,
    get_counties_from_pois as _get_counties_from_pois,
    get_neighbor_manager as _get_neighbor_manager
)

# Re-export with enhanced documentation

def get_neighboring_states(state_fips: str) -> List[str]:
    """
    Get neighboring states for a given state.
    
    Args:
        state_fips: Two-digit state FIPS code (e.g., '37' for North Carolina)
        
    Returns:
        List of neighboring state FIPS codes
        
    Examples:
        >>> get_neighboring_states('37')  # North Carolina
        ['13', '45', '47', '51']  # GA, SC, TN, VA
        
        >>> get_neighboring_states('06')  # California  
        ['04', '32', '41']  # AZ, NV, OR
    """
    return _get_neighboring_states(state_fips)


def get_neighboring_counties(
    state_fips: str, 
    county_fips: str, 
    include_cross_state: bool = True
) -> List[Tuple[str, str]]:
    """
    Get neighboring counties for a given county.
    
    Args:
        state_fips: Two-digit state FIPS code
        county_fips: Three-digit county FIPS code
        include_cross_state: Whether to include neighbors in other states
        
    Returns:
        List of (state_fips, county_fips) tuples for neighboring counties
        
    Examples:
        >>> get_neighboring_counties('37', '183')  # Wake County, NC
        [('37', '037'), ('37', '063'), ('37', '069'), ...]
        
        >>> get_neighboring_counties('06', '037')  # Los Angeles County, CA
        [('06', '059'), ('06', '065'), ('06', '071'), ...]
    """
    return _get_neighboring_counties(state_fips, county_fips, include_cross_state)


def get_geography_from_point(lat: float, lon: float) -> Dict[str, Optional[str]]:
    """
    Get geographic identifiers for a point (latitude, longitude).
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        Dictionary with geographic identifiers:
        - state_fips: Two-digit state FIPS code
        - county_fips: Three-digit county FIPS code  
        - tract_geoid: 11-digit census tract GEOID
        - block_group_geoid: 12-digit block group GEOID
        
    Examples:
        >>> get_geography_from_point(35.7796, -78.6382)  # Raleigh, NC
        {'state_fips': '37', 'county_fips': '183', 'tract_geoid': '37183050100', ...}
        
        >>> get_geography_from_point(34.0522, -118.2437)  # Los Angeles, CA
        {'state_fips': '06', 'county_fips': '037', 'tract_geoid': '06037207400', ...}
    """
    return _get_geography_from_point(lat, lon)


def get_counties_from_pois(
    pois: List[Dict], 
    include_neighbors: bool = True,
    neighbor_distance: int = 1
) -> List[Tuple[str, str]]:
    """
    Get counties for a list of Points of Interest (POIs).
    
    Args:
        pois: List of POI dictionaries with 'lat' and 'lon' keys
        include_neighbors: Whether to include neighboring counties
        neighbor_distance: Distance of neighbors to include (1 = immediate neighbors)
        
    Returns:
        List of unique (state_fips, county_fips) tuples
        
    Examples:
        >>> pois = [
        ...     {'lat': 35.7796, 'lon': -78.6382, 'name': 'Raleigh'},
        ...     {'lat': 35.2271, 'lon': -80.8431, 'name': 'Charlotte'}
        ... ]
        >>> counties = get_counties_from_pois(pois)
        [('37', '183'), ('37', '119'), ...]  # Wake, Mecklenburg, and neighbors
        
        >>> # Without neighbors
        >>> counties = get_counties_from_pois(pois, include_neighbors=False)
        [('37', '183'), ('37', '119')]  # Just Wake and Mecklenburg
    """
    # Get the manager and call the method with all parameters
    manager = _get_neighbor_manager()
    return manager.get_counties_from_pois(pois, include_neighbors, neighbor_distance)


def get_neighbor_manager(db_path: Optional[str] = None):
    """
    Get the neighbor manager instance for advanced operations.
    
    Args:
        db_path: Optional path to neighbor database file
        
    Returns:
        NeighborManager instance for advanced operations
        
    Examples:
        >>> manager = get_neighbor_manager()
        >>> stats = manager.get_neighbor_statistics()
        >>> print(f"Database has {stats['county_relationships']} county relationships")
    """
    return _get_neighbor_manager(db_path)


def get_statistics() -> Dict[str, Any]:
    """
    Get statistics about the neighbor database.
    
    Returns:
        Dictionary with database statistics:
        - state_relationships: Number of state neighbor relationships
        - county_relationships: Number of county neighbor relationships
        - cross_state_county_relationships: Number of cross-state county relationships
        - cached_points: Number of cached point lookups
        - states_with_county_data: Number of states with county data
        
    Examples:
        >>> stats = get_statistics()
        >>> print(f"Database contains {stats['county_relationships']:,} county relationships")
        Database contains 18,560 county relationships
    """
    manager = _get_neighbor_manager()
    return manager.get_neighbor_statistics()


# State FIPS code reference for convenience
STATE_FIPS_CODES = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08',
    'CT': '09', 'DE': '10', 'DC': '11', 'FL': '12', 'GA': '13', 'HI': '15',
    'ID': '16', 'IL': '17', 'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21',
    'LA': '22', 'ME': '23', 'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27',
    'MS': '28', 'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33',
    'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
    'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46',
    'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53',
    'WV': '54', 'WI': '55', 'WY': '56'
}

FIPS_TO_STATE = {v: k for k, v in STATE_FIPS_CODES.items()}


def get_state_fips(state_abbr: str) -> Optional[str]:
    """
    Convert state abbreviation to FIPS code.
    
    Args:
        state_abbr: Two-letter state abbreviation (e.g., 'NC', 'CA')
        
    Returns:
        Two-digit FIPS code or None if not found
        
    Examples:
        >>> get_state_fips('NC')
        '37'
        >>> get_state_fips('CA')
        '06'
    """
    return STATE_FIPS_CODES.get(state_abbr.upper())


def get_state_abbr(state_fips: str) -> Optional[str]:
    """
    Convert FIPS code to state abbreviation.
    
    Args:
        state_fips: Two-digit FIPS code (e.g., '37', '06')
        
    Returns:
        Two-letter state abbreviation or None if not found
        
    Examples:
        >>> get_state_abbr('37')
        'NC'
        >>> get_state_abbr('06')
        'CA'
    """
    return FIPS_TO_STATE.get(state_fips)


# Convenience functions using state abbreviations
def get_neighboring_states_by_abbr(state_abbr: str) -> List[str]:
    """
    Get neighboring states using state abbreviation.
    
    Args:
        state_abbr: Two-letter state abbreviation
        
    Returns:
        List of neighboring state abbreviations
        
    Examples:
        >>> get_neighboring_states_by_abbr('NC')
        ['GA', 'SC', 'TN', 'VA']
    """
    state_fips = get_state_fips(state_abbr)
    if not state_fips:
        return []
    
    neighbor_fips = get_neighboring_states(state_fips)
    return [get_state_abbr(fips) for fips in neighbor_fips if get_state_abbr(fips)]


# Export all public functions
__all__ = [
    'get_neighboring_states',
    'get_neighboring_counties', 
    'get_geography_from_point',
    'get_counties_from_pois',
    'get_neighbor_manager',
    'get_statistics',
    'get_state_fips',
    'get_state_abbr',
    'get_neighboring_states_by_abbr',
    'STATE_FIPS_CODES',
    'FIPS_TO_STATE'
] 