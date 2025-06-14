"""
Adapter layer for the modern census module.

This package contains adapters that provide backward compatibility
with legacy APIs and external system integrations.
"""

# Import all legacy adapter functions for backward compatibility
from .legacy_adapter import *

__all__ = [
    # Streaming API compatibility
    "get_streaming_census_manager",
    "get_block_groups_streaming", 
    "get_census_data_streaming",
    
    # Simple API compatibility
    "get_block_groups",
    "get_census_data",
    "clear_cache",
    
    # Neighbor API compatibility (stubs)
    "get_neighboring_states",
    "get_neighboring_counties",
] 