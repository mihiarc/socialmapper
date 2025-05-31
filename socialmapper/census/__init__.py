#!/usr/bin/env python3
"""
Modern streaming census module for SocialMapper.

This module provides:
- Pure streaming of census boundaries from Census APIs
- Optional lightweight caching of census data only
- No storage of geographic metadata
- Minimal memory footprint
- High performance with 99.9% storage reduction

The old DuckDB-based system has been replaced with a streaming architecture
that eliminates the 118.7 MB geographic metadata storage.
"""

# Import the new streaming system
from .streaming import (
    StreamingCensusManager,
    get_streaming_census_manager,
    get_block_groups_streaming,
    get_census_data_streaming
)

# Import neighbor functionality (unchanged)
from .neighbors import (
    get_neighbor_manager,
    get_neighboring_states,
    get_neighboring_counties,
    get_geography_from_point,
    get_counties_from_pois,
    initialize_all_neighbors
)

# Backward compatibility aliases
def get_census_database(cache_census_data: bool = False, cache_dir = None):
    """
    Backward compatibility function that returns a streaming census manager.
    
    Args:
        cache_census_data: Whether to cache census statistics
        cache_dir: Directory for optional census data cache
        
    Returns:
        StreamingCensusManager instance
    """
    return get_streaming_census_manager(cache_census_data, cache_dir)

def get_block_groups(state_fips, api_key=None):
    """Get block groups using streaming (backward compatibility)."""
    return get_block_groups_streaming(state_fips, api_key)

def get_census_data(geoids, variables, year=2021, dataset='acs/acs5', api_key=None, cache=False):
    """Get census data using streaming (backward compatibility)."""
    return get_census_data_streaming(geoids, variables, year, dataset, api_key, cache)

# Export main functions
__all__ = [
    # New streaming system
    'StreamingCensusManager',
    'get_streaming_census_manager',
    'get_block_groups_streaming',
    'get_census_data_streaming',
    
    # Neighbor functionality
    'get_neighbor_manager',
    'get_neighboring_states', 
    'get_neighboring_counties',
    'get_geography_from_point',
    'get_counties_from_pois',
    'initialize_all_neighbors',
    
    # Backward compatibility
    'get_census_database',
    'get_block_groups',
    'get_census_data'
]
