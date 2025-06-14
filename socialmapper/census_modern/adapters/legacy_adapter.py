"""
Legacy compatibility adapters for the modernized census module.

These adapters provide backward compatibility with the old census APIs
while using the new modern implementation underneath.
"""

import warnings
from typing import List, Optional, Dict, Any
import pandas as pd
import geopandas as gpd

from ..domain.entities import CensusDataPoint
# Note: Legacy imports removed to avoid circular dependencies
# The modern system provides all functionality through CensusSystem


# Global instance for backward compatibility
_default_manager: Optional[CensusManager] = None


def _get_default_manager() -> CensusManager:
    """Get or create the default census manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = create_census_manager()
    return _default_manager


def _emit_deprecation_warning(old_function: str, new_usage: str):
    """Emit a deprecation warning for legacy functions."""
    warnings.warn(
        f"{old_function} is deprecated and will be removed in v0.6.0. "
        f"Use the modern API instead: {new_usage}",
        DeprecationWarning,
        stacklevel=3
    )


# Legacy streaming API compatibility
def get_streaming_census_manager(cache_census_data: bool = False, cache_dir: Optional[str] = None):
    """
    Legacy compatibility: Create a streaming census manager.
    
    This function maintains compatibility with the old streaming API.
    """
    _emit_deprecation_warning(
        "get_streaming_census_manager()",
        "from socialmapper.census_modern import create_census_manager; manager = create_census_manager()"
    )
    
    # Convert legacy parameters to new configuration
    config = CensusConfig(
        cache_enabled=cache_census_data,
        repository_path=cache_dir
    )
    
    return create_census_manager(config)


def get_block_groups_streaming(state_fips: List[str], api_key: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Legacy compatibility: Get block groups using streaming.
    
    Returns data in the old GeoDataFrame format for compatibility.
    """
    _emit_deprecation_warning(
        "get_block_groups_streaming()",
        "from socialmapper.census_modern import CensusManager; census = CensusManager(); units = census.get_block_groups(state_fips)"
    )
    
    # Use new manager but convert output to legacy format
    config = CensusConfig(census_api_key=api_key) if api_key else None
    manager = create_census_manager(config)
    
    units = manager.get_block_groups(state_fips)
    
    # Convert to legacy GeoDataFrame format
    data = []
    for unit in units:
        data.append({
            'GEOID': unit.geoid,
            'NAME': unit.name,
            'STATEFP': unit.state_fips,
            'COUNTYFP': unit.county_fips,
            'TRACTCE': unit.tract_code,
            'BLKGRPCE': unit.block_group_code,
            'geometry': None  # Would need actual geometry data
        })
    
    # Create GeoDataFrame for backward compatibility
    gdf = gpd.GeoDataFrame(data)
    return gdf


def get_census_data_streaming(
    geoids: List[str],
    variables: List[str],
    year: int = 2021,
    dataset: str = "acs/acs5",
    api_key: Optional[str] = None,
    cache: bool = False,
) -> pd.DataFrame:
    """
    Legacy compatibility: Get census data using streaming.
    
    Returns data in the old DataFrame format for compatibility.
    """
    _emit_deprecation_warning(
        "get_census_data_streaming()",
        "from socialmapper.census_modern import CensusManager; census = CensusManager(); data = census.get_census_data(geoids, variables)"
    )
    
    # Use new manager but convert output to legacy format
    config = CensusConfig(census_api_key=api_key, cache_enabled=cache) if api_key or cache else None
    manager = create_census_manager(config)
    
    data_points = manager.get_census_data(geoids, variables, year, dataset, cache)
    
    # Convert to legacy DataFrame format
    rows = []
    for point in data_points:
        rows.append({
            'GEOID': point.geoid,
            'variable_code': point.variable.code,
            'value': point.value,
            'year': point.year,
            'dataset': point.dataset,
            'NAME': point.variable.name
        })
    
    return pd.DataFrame(rows)


# Legacy simple API compatibility  
def get_block_groups(state: str, refresh: bool = False) -> gpd.GeoDataFrame:
    """
    Legacy compatibility: Get block groups for a state.
    
    Maintains compatibility with the old simple API.
    """
    _emit_deprecation_warning(
        "get_block_groups()",
        "from socialmapper.census_modern import CensusManager; census = CensusManager(); units = census.get_block_groups([state_fips])"
    )
    
    # Convert state name/abbreviation to FIPS if needed
    from socialmapper.states import normalize_state, StateFormat
    state_fips = normalize_state(state, to_format=StateFormat.FIPS)
    
    if not state_fips:
        raise ValueError(f"Could not resolve state: {state}")
    
    manager = _get_default_manager()
    units = manager.get_block_groups([state_fips], use_cache=not refresh)
    
    # Convert to legacy format
    return _convert_units_to_geodataframe(units)


def get_census_data(
    state: str,
    variables: List[str],
    year: int = 2020,
    dataset: str = "acs5",
    refresh: bool = False,
) -> pd.DataFrame:
    """
    Legacy compatibility: Get census data for a state.
    
    Maintains compatibility with the old simple API.
    """
    _emit_deprecation_warning(
        "get_census_data()",
        "from socialmapper.census_modern import CensusManager; census = CensusManager(); data = census.get_census_data(geoids, variables)"
    )
    
    # Convert state to FIPS and get all block groups
    from socialmapper.states import normalize_state, StateFormat
    state_fips = normalize_state(state, to_format=StateFormat.FIPS)
    
    if not state_fips:
        raise ValueError(f"Could not resolve state: {state}")
    
    manager = _get_default_manager()
    
    # Get block groups for the state to get GEOIDs
    units = manager.get_block_groups([state_fips])
    geoids = [unit.geoid for unit in units]
    
    # Get census data
    dataset_formatted = f"acs/{dataset}" if not dataset.startswith("acs/") else dataset
    data_points = manager.get_census_data(
        geoids=geoids,
        variable_codes=variables,
        year=year,
        dataset=dataset_formatted,
        use_cache=not refresh
    )
    
    # Convert to legacy format with additional columns expected by old API
    rows = []
    for point in data_points:
        # Extract geographic components from GEOID
        geoid = point.geoid
        state_part = geoid[:2] if len(geoid) >= 2 else ""
        county_part = geoid[2:5] if len(geoid) >= 5 else ""
        tract_part = geoid[5:11] if len(geoid) >= 11 else ""
        bg_part = geoid[11:] if len(geoid) > 11 else ""
        
        row = {
            'GEO_ID': f"1500000US{geoid}",  # Legacy format
            'NAME': point.variable.name,
            'state': state_part,
            'county': county_part,
            'tract': tract_part,
            'block group': bg_part,
            point.variable.code: point.value
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df


def clear_cache(state: Optional[str] = None):
    """
    Legacy compatibility: Clear cached data.
    """
    _emit_deprecation_warning(
        "clear_cache()",
        "Cache clearing is handled automatically in the modern API"
    )
    
    # For backward compatibility, recreate the default manager
    global _default_manager
    _default_manager = None


def _convert_units_to_geodataframe(units) -> gpd.GeoDataFrame:
    """Convert GeographicUnit entities to legacy GeoDataFrame format."""
    data = []
    for unit in units:
        data.append({
            'GEOID': unit.geoid,
            'NAME': unit.name,
            'STATEFP': unit.state_fips,
            'COUNTYFP': unit.county_fips,
            'TRACTCE': unit.tract_code,
            'BLKGRPCE': unit.block_group_code,
            'geometry': None  # Legacy format included geometry
        })
    
    return gpd.GeoDataFrame(data)


# Legacy neighbor API would need similar adapters
def get_neighboring_states(state_fips: str) -> List[str]:
    """Legacy compatibility: Get neighboring states."""
    _emit_deprecation_warning(
        "get_neighboring_states()",
        "Use the dedicated neighbor service from socialmapper.geography"
    )
    
    # This would need to be implemented or delegated to the geography module
    # For now, return empty list
    return []


def get_neighboring_counties(county_fips: str) -> List[str]:
    """Legacy compatibility: Get neighboring counties."""
    _emit_deprecation_warning(
        "get_neighboring_counties()",
        "Use the dedicated neighbor service from socialmapper.geography"
    )
    
    # This would need to be implemented or delegated to the geography module
    return []


# Export all legacy functions for backward compatibility
__all__ = [
    # Streaming API
    "get_streaming_census_manager",
    "get_block_groups_streaming", 
    "get_census_data_streaming",
    
    # Simple API
    "get_block_groups",
    "get_census_data",
    "clear_cache",
    
    # Neighbor API (stubs)
    "get_neighboring_states",
    "get_neighboring_counties",
] 