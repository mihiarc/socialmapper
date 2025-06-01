#!/usr/bin/env python3
"""
Census data module for SocialMapper.

This module provides access to census data through a simple API that:
- Fetches data directly from Census API
- Stores data in memory only
- No persistent storage needed
"""

from .api import (
    get_block_groups,
    get_census_data,
    clear_cache,
    CensusAPI
)

__all__ = [
    'get_block_groups',
    'get_census_data',
    'clear_cache',
    'CensusAPI'
] 