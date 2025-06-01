"""
Census API module for SocialMapper.

This module provides direct Census API access with in-memory data handling:
- Fetches data from Census API as needed
- Stores data in memory using pandas/geopandas
- No persistent storage
"""

import logging
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point, Polygon, MultiPolygon

from socialmapper.utils.helpers import (
    normalize_census_variable,
    get_census_api_key,
    get_readable_census_variables,
    CENSUS_VARIABLE_MAPPING
)
from ..geography.states import (
    normalize_state,
    normalize_state_list,
    StateFormat
)

logger = logging.getLogger(__name__)

class CensusAPI:
    """Census API handler with in-memory data management."""
    
    def __init__(self):
        """Initialize the Census API handler."""
        self._api_key = get_census_api_key()
        self._data_cache = {}  # Simple in-memory cache
    
    def get_block_groups(
        self,
        state: str,
        refresh: bool = False
    ) -> gpd.GeoDataFrame:
        """
        Get block groups for a state.
        
        Args:
            state: State identifier (name, abbreviation, or FIPS)
            refresh: Force refresh from API
            
        Returns:
            GeoDataFrame with block groups
        """
        state_fips = normalize_state(state, to_format=StateFormat.FIPS)
        cache_key = f"bg_{state_fips}"
        
        if not refresh and cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        # Fetch from Census API
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/10/query"
        params = {
            'where': f"STATE = '{state_fips}'",
            'outFields': '*',
            'outSR': '4326',
            'f': 'geojson'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        gdf = gpd.GeoDataFrame.from_features(
            response.json()['features'],
            crs="EPSG:4326"
        )
        
        # Cache in memory
        self._data_cache[cache_key] = gdf
        return gdf
    
    def get_census_data(
        self,
        state: str,
        variables: List[str],
        year: int = 2020,
        dataset: str = 'acs5',
        refresh: bool = False
    ) -> pd.DataFrame:
        """
        Get census data for a state.
        
        Args:
            state: State identifier
            variables: Census variable codes
            year: Census year
            dataset: Census dataset (e.g., 'acs5')
            refresh: Force refresh from API
            
        Returns:
            DataFrame with census data
        """
        state_fips = normalize_state(state, to_format=StateFormat.FIPS)
        cache_key = f"data_{state_fips}_{year}_{dataset}"
        
        if not refresh and cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        # Normalize variables
        variables = [normalize_census_variable(var) for var in variables]
        
        # Build API URL
        base_url = "https://api.census.gov/data"
        url = f"{base_url}/{year}/{dataset}"
        
        # Prepare variables
        get_vars = ['GEO_ID'] + variables
        
        params = {
            'get': ','.join(get_vars),
            'for': 'block group:*',
            'in': f'state:{state_fips}',
            'key': self._api_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Convert to DataFrame
        data = response.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Cache in memory
        self._data_cache[cache_key] = df
        return df
    
    def clear_cache(self, state: Optional[str] = None):
        """
        Clear cached data.
        
        Args:
            state: State to clear. If None, clears all data.
        """
        if state is None:
            self._data_cache.clear()
        else:
            state_fips = normalize_state(state, to_format=StateFormat.FIPS)
            keys_to_remove = [
                key for key in self._data_cache
                if state_fips in key
            ]
            for key in keys_to_remove:
                self._data_cache.pop(key)

# Create a default instance
census_api = CensusAPI()

# Export main functions
get_block_groups = census_api.get_block_groups
get_census_data = census_api.get_census_data
clear_cache = census_api.clear_cache 