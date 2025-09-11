"""Simplified census data integration for the SocialMapper pipeline."""

import logging
from typing import Any, Tuple, List
import geopandas as gpd
import pandas as pd

from ..census_simple import (
    get_census_data_for_isochrone,
    normalize_variables,
    CensusClient,
    get_demographics_for_isochrone
)
from ..distance import add_travel_distances
from ..progress import get_progress_bar

logger = logging.getLogger(__name__)


def integrate_census_with_isochrone(
    isochrone_gdf: gpd.GeoDataFrame,
    census_variables: List[str],
    api_key: str = None,
    poi_data: dict = None,
    travel_time: int = 15
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, List[str]]:
    """Integrate census data with an isochrone - simple and direct.
    
    Args:
        isochrone_gdf: The isochrone polygon(s)
        census_variables: List of census variables (names or codes)
        api_key: Census API key (optional)
        poi_data: POI data for distance calculations
        travel_time: Travel time in minutes
        
    Returns:
        Tuple of (block_groups_gdf, census_data_gdf, census_codes)
    """
    print("\n=== Integrating Census Data ===")
    
    # Normalize variables to census codes
    census_codes = normalize_variables(census_variables)
    print(f"Requesting census data for: {', '.join(census_variables)}")
    
    # Get census data for the isochrone area
    with get_progress_bar(total=1, desc="🏛️ Fetching Census Data", unit="query") as pbar:
        census_data = get_census_data_for_isochrone(
            isochrone_gdf, 
            census_codes,
            api_key=api_key
        )
        pbar.update(1)
    
    if census_data.empty:
        raise ValueError("No census data found for the isochrone area")
    
    print(f"Found {len(census_data)} census block groups")
    
    # census_data already has block group geometries merged
    geographic_units_gdf = census_data[['GEOID', 'geometry']].copy()
    
    # Add travel distances if POI data is provided
    if poi_data and 'pois' in poi_data:
        print("Calculating travel distances to POIs...")
        units_with_distances = add_travel_distances(
            block_groups_gdf=geographic_units_gdf,
            poi_data=poi_data,
            travel_time=travel_time
        )
        
        # Merge distances back with census data
        census_data_gdf = census_data.merge(
            units_with_distances[['GEOID', 'min_travel_time_minutes', 'nearest_poi_meters']],
            on='GEOID',
            how='left'
        )
    else:
        census_data_gdf = census_data
    
    print(f"Census integration complete: {len(census_data_gdf)} block groups with data")
    
    return geographic_units_gdf, census_data_gdf, census_codes


def get_demographic_summary(
    isochrone_gdf: gpd.GeoDataFrame,
    api_key: str = None
) -> dict:
    """Get a quick demographic summary for an isochrone area.
    
    Args:
        isochrone_gdf: The isochrone polygon(s)
        api_key: Census API key (optional)
        
    Returns:
        Dict with demographic statistics
    """
    return get_demographics_for_isochrone(isochrone_gdf, api_key)