"""
Census API module for SocialMapper.

This module provides direct Census API access with in-memory data handling:
- Fetches data from Census API as needed
- Stores data in memory using pandas/geopandas
- No persistent storage
"""

import logging
from typing import List, Optional

import geopandas as gpd
import pandas as pd
import requests

from socialmapper.util import (
    get_census_api_key,
    normalize_census_variable,
)

from ..geography.states import StateFormat, normalize_state

logger = logging.getLogger(__name__)


class CensusAPI:
    """Census API handler with in-memory data management."""

    def __init__(self):
        """Initialize the Census API handler."""
        self._api_key = get_census_api_key()
        self._data_cache = {}  # Simple in-memory cache

    def get_block_groups(self, state: str, refresh: bool = False) -> gpd.GeoDataFrame:
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

        # Fetch from Census API - Block Groups are in Tracts_Blocks service, layer 1
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
        params = {
            "where": f"STATE = '{state_fips}'",
            "outFields": "*",
            "outSR": "4326",
            "f": "geojson",
            "returnGeometry": "true",
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        gdf = gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")

        # Cache in memory
        self._data_cache[cache_key] = gdf
        return gdf

    def get_census_data(
        self,
        state: str,
        variables: List[str],
        year: int = 2020,
        dataset: str = "acs5",
        refresh: bool = False,
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
        # For ACS data, the format is /data/YEAR/acs/acs5
        if dataset.startswith("acs"):
            url = f"{base_url}/{year}/acs/{dataset}"
        else:
            url = f"{base_url}/{year}/{dataset}"

        # Prepare variables - Census API returns NAME instead of GEO_ID
        get_vars = ["NAME"] + variables

        params = {
            "get": ",".join(get_vars),
            "for": "block group:*",
            "in": f"state:{state_fips} county:* tract:*",
            "key": self._api_key,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        # Convert to DataFrame
        data = response.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Create GEO_ID from components if not present
        if "GEO_ID" not in df.columns and all(col in df.columns for col in ["state", "county", "tract", "block group"]):
            df["GEO_ID"] = (
                "1500000US" +
                df["state"].str.zfill(2) +
                df["county"].str.zfill(3) +
                df["tract"].str.zfill(6) +
                df["block group"]
            )

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
            keys_to_remove = [key for key in self._data_cache if state_fips in key]
            for key in keys_to_remove:
                self._data_cache.pop(key)


# Create a default instance
census_api = CensusAPI()

# Export main functions
get_block_groups = census_api.get_block_groups
get_census_data = census_api.get_census_data
clear_cache = census_api.clear_cache
