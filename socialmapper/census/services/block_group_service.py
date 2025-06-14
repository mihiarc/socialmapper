"""
Block Group Service for SocialMapper.

Handles census block group operations including fetching boundaries,
batch processing, and TIGER/Line shapefile URL generation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
from tqdm import tqdm

from ..domain.entities import BlockGroupInfo, CountyInfo
from ..domain.interfaces import (
    CensusAPIClient, 
    CacheProvider, 
    ConfigurationProvider,
    RateLimiter
)

logger = logging.getLogger(__name__)


class BlockGroupService:
    """Service for managing census block group operations."""
    
    def __init__(
        self,
        config: ConfigurationProvider,
        api_client: CensusAPIClient,
        cache: Optional[CacheProvider] = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        self._config = config
        self._api_client = api_client
        self._cache = cache
        self._rate_limiter = rate_limiter
        
        # Configure geopandas for better performance if available
        self._use_arrow = self._check_arrow_support()
    
    def get_block_groups_for_county(
        self, 
        state_fips: str, 
        county_fips: str
    ) -> gpd.GeoDataFrame:
        """
        Fetch census block group boundaries for a specific county.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            
        Returns:
            GeoDataFrame with block group boundaries
        """
        # Normalize FIPS codes
        state_fips = state_fips.zfill(2)
        county_fips = county_fips.zfill(3)
        
        # Check cache first
        cache_key = f"block_groups_{state_fips}_{county_fips}"
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                logger.info(f"Loaded cached block groups for county {county_fips} in state {state_fips}")
                return cached_data
        
        # Fetch from Census API
        logger.info(f"Fetching block groups for county {county_fips} in state {state_fips}")
        
        # Use the Tracts_Blocks MapServer endpoint
        base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
        
        params = {
            "where": f"STATE='{state_fips}' AND COUNTY='{county_fips}'",
            "outFields": "STATE,COUNTY,TRACT,BLKGRP,GEOID",
            "returnGeometry": "true",
            "f": "geojson",
        }
        
        try:
            # Apply rate limiting
            if self._rate_limiter:
                self._rate_limiter.wait_if_needed("census")
            
            # Use requests directly since we're calling a different API
            import requests
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Parse the GeoJSON response
                data = response.json()
                block_groups = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")
                
                # Ensure proper formatting
                if "STATE" not in block_groups.columns or not all(block_groups["STATE"] == state_fips):
                    block_groups["STATE"] = state_fips
                if "COUNTY" not in block_groups.columns or not all(block_groups["COUNTY"] == county_fips):
                    block_groups["COUNTY"] = county_fips
                
                # Cache the result
                if self._cache:
                    self._cache.set(cache_key, block_groups)
                
                logger.info(f"Retrieved {len(block_groups)} block groups for county {county_fips}")
                return block_groups
            else:
                raise ValueError(f"Census API returned status code {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching block groups for county {county_fips}: {e}")
            raise ValueError(f"Could not fetch block groups: {str(e)}")
    
    def get_block_groups_for_counties(
        self, 
        counties: List[Tuple[str, str]]
    ) -> gpd.GeoDataFrame:
        """
        Fetch block groups for multiple counties and combine them.
        
        Args:
            counties: List of (state_fips, county_fips) tuples
            
        Returns:
            Combined GeoDataFrame with block groups for all counties
        """
        all_block_groups = []
        
        for state_fips, county_fips in tqdm(counties, desc="Fetching block groups by county", unit="county"):
            try:
                county_block_groups = self.get_block_groups_for_county(state_fips, county_fips)
                all_block_groups.append(county_block_groups)
            except Exception as e:
                logger.warning(f"Error fetching block groups for county {county_fips} in state {state_fips}: {e}")
        
        if not all_block_groups:
            raise ValueError("No block group data could be retrieved")
        
        # Combine all county block groups
        return pd.concat(all_block_groups, ignore_index=True)
    
    def get_block_groups_for_county_info(self, county: CountyInfo) -> gpd.GeoDataFrame:
        """
        Fetch block groups for a CountyInfo entity.
        
        Args:
            county: CountyInfo entity
            
        Returns:
            GeoDataFrame with block group boundaries
        """
        return self.get_block_groups_for_county(county.state_fips, county.county_fips)
    
    def get_block_group_urls(self, state_fips: str, year: int = 2022) -> Dict[str, str]:
        """
        Get the download URLs for block group shapefiles from the Census Bureau.
        
        Args:
            state_fips: State FIPS code
            year: Year for the TIGER/Line shapefiles
            
        Returns:
            Dictionary mapping state FIPS to download URLs
        """
        # Standardize the state FIPS
        state_fips = str(state_fips).zfill(2)
        
        # Base URL for Census Bureau TIGER/Line shapefiles
        base_url = f"https://www2.census.gov/geo/tiger/TIGER{year}/BG"
        
        # The URL pattern for block group shapefiles
        url = f"{base_url}/tl_{year}_{state_fips}_bg.zip"
        
        # Return a dictionary mapping state FIPS to the URL
        return {state_fips: url}
    
    def create_block_group_info_from_geoid(self, geoid: str) -> Optional[BlockGroupInfo]:
        """
        Create a BlockGroupInfo entity from a 12-digit GEOID.
        
        Args:
            geoid: 12-digit block group GEOID
            
        Returns:
            BlockGroupInfo entity or None if invalid
        """
        if not geoid or len(geoid) != 12 or not geoid.isdigit():
            return None
        
        try:
            return BlockGroupInfo(
                state_fips=geoid[:2],
                county_fips=geoid[2:5],
                tract=geoid[5:11],
                block_group=geoid[11:12],
                geoid=geoid
            )
        except ValueError:
            return None
    
    def validate_block_group_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Validate and clean block group GeoDataFrame.
        
        Args:
            gdf: Block group GeoDataFrame
            
        Returns:
            Cleaned GeoDataFrame
        """
        if gdf.empty:
            return gdf
        
        # Ensure required columns exist
        required_columns = ["STATE", "COUNTY", "TRACT", "BLKGRP"]
        missing_columns = [col for col in required_columns if col not in gdf.columns]
        
        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
        
        # Ensure GEOID column exists
        if "GEOID" not in gdf.columns:
            if all(col in gdf.columns for col in required_columns):
                gdf["GEOID"] = (
                    gdf["STATE"].astype(str).str.zfill(2) +
                    gdf["COUNTY"].astype(str).str.zfill(3) +
                    gdf["TRACT"].astype(str).str.zfill(6) +
                    gdf["BLKGRP"].astype(str)
                )
        
        # Remove invalid geometries
        if "geometry" in gdf.columns:
            valid_geom = gdf.geometry.notna() & gdf.geometry.is_valid
            if not valid_geom.all():
                logger.warning(f"Removing {(~valid_geom).sum()} invalid geometries")
                gdf = gdf[valid_geom].copy()
        
        return gdf
    
    def _check_arrow_support(self) -> bool:
        """Check if PyArrow is available for better performance."""
        try:
            import pyarrow
            import os
            os.environ["PYOGRIO_USE_ARROW"] = "1"
            return True
        except ImportError:
            return False 