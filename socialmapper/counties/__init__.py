#!/usr/bin/env python3
"""
County management utilities for the SocialMapper project.

This module provides tools for working with US counties including:
- Converting between county FIPS codes, names, and other identifiers
- Getting neighboring counties
- Fetching block groups at the county level

Note: This module now uses the modern census system internally for better architecture
and maintainability while preserving the same API.
"""

# Import everything from the modern census system
from ..census import get_census_system

# Create a default system instance
_census_system = None

def _get_census_system():
    """Get the census system instance."""
    global _census_system
    if _census_system is None:
        _census_system = get_census_system()
    return _census_system

# Note: Geographic lookup functions are now available through the modern census system:
# census_system.get_geography_from_point() and census_system.get_counties_from_pois()


def get_block_groups_for_county(state_fips, county_fips, api_key=None):
    """
    Fetch census block group boundaries for a specific county.
    
    Args:
        state_fips: State FIPS code
        county_fips: County FIPS code
        api_key: Census API key (optional, uses system configuration)
        
    Returns:
        GeoDataFrame with block group boundaries
    """
    return _get_census_system().get_block_groups_for_county(state_fips, county_fips)


def get_block_groups_for_counties(counties, api_key=None):
    """
    Fetch block groups for multiple counties and combine them.
    
    Args:
        counties: List of (state_fips, county_fips) tuples
        api_key: Census API key (optional, uses system configuration)
        
    Returns:
        Combined GeoDataFrame with block groups for all counties
    """
    return _get_census_system().get_block_groups_for_counties(counties)


def get_block_group_urls(state_fips, year=2022):
    """
    Get the download URLs for block group shapefiles from the Census Bureau.
    
    Args:
        state_fips: State FIPS code
        year: Year for the TIGER/Line shapefiles
        
    Returns:
        Dictionary mapping state FIPS to download URLs
    """
    return _get_census_system().get_block_group_urls(state_fips, year)

# Export all functions
__all__ = [
    "get_block_groups_for_county",
    "get_block_groups_for_counties", 
    "get_block_group_urls",
]
