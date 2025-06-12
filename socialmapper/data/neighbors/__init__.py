"""
Neighbor relationship management for SocialMapper.

This module provides functionality for managing and querying neighbor relationships
between geographic entities (states, counties, etc.).
"""

from .file_based import (
    FileNeighborManager,
    get_counties_from_pois,
    get_file_neighbor_manager,
    get_geography_from_point,
    get_neighboring_counties,
    get_neighboring_states,
)

__all__ = [
    "get_file_neighbor_manager",
    "get_neighboring_states",
    "get_neighboring_counties",
    "get_geography_from_point",
    "get_counties_from_pois",
    "FileNeighborManager",
]
