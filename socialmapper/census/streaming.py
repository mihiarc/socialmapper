#!/usr/bin/env python3
"""
Pure streaming census system - no persistent storage of geographic metadata.

This module provides:
- On-demand streaming of block groups from Census APIs
- Optional lightweight caching of census data only
- No storage of geographic metadata (GEOID, names, etc.)
- Minimal memory footprint
"""

import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import warnings

import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point, Polygon, MultiPolygon

from socialmapper.progress import get_progress_bar
from socialmapper.util import (
    normalize_census_variable,
    get_census_api_key,
    get_readable_census_variables,
    CENSUS_VARIABLE_MAPPING,
    rate_limiter
)
from socialmapper.states import (
    normalize_state,
    normalize_state_list,
    StateFormat,
    state_fips_to_name
)

logger = logging.getLogger(__name__)


class StreamingCensusManager:
    """
    Pure streaming census manager with no persistent geographic metadata storage.
    
    This class provides:
    - On-demand streaming of boundaries from Census APIs
    - Optional lightweight caching of census data (statistics only)
    - No storage of geographic metadata
    - Minimal storage footprint
    """
    
    def __init__(self, cache_census_data: bool = False, cache_dir: Optional[Path] = None):
        """
        Initialize the streaming census manager.
        
        Args:
            cache_census_data: Whether to cache census statistics (not geographic metadata)
            cache_dir: Directory for optional census data cache (Parquet files)
        """
        self.cache_census_data = cache_census_data
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".socialmapper" / "census_cache"
        
        if self.cache_census_data:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None
    
    def get_block_groups(
        self, 
        state_fips: List[str], 
        api_key: Optional[str] = None
    ) -> gpd.GeoDataFrame:
        """
        Stream block groups for specified states directly from Census APIs.
        
        Args:
            state_fips: List of state FIPS codes
            api_key: Census API key
            
        Returns:
            GeoDataFrame with block groups (streamed, not cached)
        """
        # Normalize state FIPS codes
        normalized_fips = []
        for state in state_fips:
            fips = normalize_state(state, to_format=StateFormat.FIPS)
            if fips:
                normalized_fips.append(fips)
            else:
                logger.warning(f"Could not normalize state identifier: {state}")
        
        if not normalized_fips:
            raise ValueError("No valid state identifiers provided")
        
        # Stream boundaries for all requested states
        all_gdfs = []
        
        for fips in normalized_fips:
            try:
                gdf = self._stream_block_groups_from_api(fips, api_key)
                if gdf is not None and not gdf.empty:
                    all_gdfs.append(gdf)
            except Exception as e:
                logger.error(f"Failed to stream block groups for state {fips}: {e}")
                continue
        
        if not all_gdfs:
            raise ValueError(f"No block groups found for states: {normalized_fips}")
        
        # Combine all state data
        combined_gdf = pd.concat(all_gdfs, ignore_index=True)
        
        # Add computed columns for backward compatibility
        if 'STATEFP' in combined_gdf.columns:
            combined_gdf['STATE'] = combined_gdf['STATEFP']
        if 'COUNTYFP' in combined_gdf.columns:
            combined_gdf['COUNTY'] = combined_gdf['COUNTYFP']
        if 'TRACTCE' in combined_gdf.columns:
            combined_gdf['TRACT'] = combined_gdf['TRACTCE']
        if 'BLKGRPCE' in combined_gdf.columns:
            combined_gdf['BLKGRP'] = combined_gdf['BLKGRPCE']
        
        return combined_gdf
    
    def _stream_block_groups_from_api(self, state_fips: str, api_key: Optional[str] = None) -> Optional[gpd.GeoDataFrame]:
        """Stream block groups from Census API."""
        if not api_key:
            api_key = get_census_api_key()
            if not api_key:
                raise ValueError("Census API key required for streaming boundary data")
        
        state_name = state_fips_to_name(state_fips) or state_fips
        
        # Try multiple approaches in order of preference
        gdf = None
        
        # Method 1: Census Cartographic Boundary Files (preferred)
        try:
            gdf = self._fetch_from_cartographic_files(state_fips)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.error(f"Cartographic files failed: {e}, trying TIGER API")
        
        # Method 2: TIGER/Web API with GeoJSON format (fallback)
        try:
            gdf = self._fetch_from_tiger_geojson(state_fips)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.error(f"TIGER GeoJSON API failed: {e}, trying ESRI JSON")
        
        # Method 3: TIGER/Web API with ESRI JSON format (last resort)
        try:
            gdf = self._fetch_from_tiger_esri_json(state_fips)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.error(f"All streaming methods failed for state {state_fips}: {e}")
        
        return None
    
    def _fetch_from_cartographic_files(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """Fetch block groups from Census Cartographic Boundary Files."""
        url = f"https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_{state_fips}_bg_500k.zip"
        
        rate_limiter.wait_if_needed("census")
        
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            import warnings
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')
            response = requests.get(url, timeout=60, verify=False)
            response.raise_for_status()
            warnings.resetwarnings()
        
        # Save to temporary file and extract
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            tmp_zip.write(response.content)
            tmp_zip_path = tmp_zip.name
        
        try:
            # Extract and read the shapefile
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                
                # Find the .shp file
                shp_files = list(Path(tmp_dir).glob("*.shp"))
                if not shp_files:
                    return None
                
                # Load as GeoDataFrame
                gdf = gpd.read_file(shp_files[0])
                
                # Ensure GEOID is properly formatted if missing
                if gdf is not None and not gdf.empty and 'GEOID' not in gdf.columns:
                    if all(col in gdf.columns for col in ['STATEFP', 'COUNTYFP', 'TRACTCE', 'BLKGRPCE']):
                        gdf['GEOID'] = (
                            gdf['STATEFP'].astype(str).str.zfill(2) +
                            gdf['COUNTYFP'].astype(str).str.zfill(3) +
                            gdf['TRACTCE'].astype(str).str.zfill(6) +
                            gdf['BLKGRPCE'].astype(str)
                        )
                
                return gdf
        finally:
            # Clean up temporary ZIP file
            Path(tmp_zip_path).unlink()
    
    def _fetch_from_tiger_geojson(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """Fetch block groups from TIGER/Web API using GeoJSON format."""
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
        
        params = {
            'where': f"STATE='{state_fips}'",
            'outFields': 'STATE,COUNTY,TRACT,BLKGRP,GEOID,ALAND,AWATER',
            'returnGeometry': 'true',
            'f': 'geojson'
        }
        
        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        if 'features' not in data or not data['features']:
            return None
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
        
        # Standardize column names to match shapefile format
        column_mapping = {
            'STATE': 'STATEFP',
            'COUNTY': 'COUNTYFP', 
            'TRACT': 'TRACTCE',
            'BLKGRP': 'BLKGRPCE'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in gdf.columns and new_col not in gdf.columns:
                gdf[new_col] = gdf[old_col]
        
        # Ensure GEOID is properly formatted
        if 'GEOID' not in gdf.columns:
            gdf['GEOID'] = (
                gdf['STATEFP'].astype(str).str.zfill(2) +
                gdf['COUNTYFP'].astype(str).str.zfill(3) +
                gdf['TRACTCE'].astype(str).str.zfill(6) +
                gdf['BLKGRPCE'].astype(str)
            )
        
        return gdf
    
    def _fetch_from_tiger_esri_json(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """Fetch block groups from TIGER/Web API using ESRI JSON format."""
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
        
        params = {
            'where': f"STATE='{state_fips}'",
            'outFields': 'STATE,COUNTY,TRACT,BLKGRP,GEOID,ALAND,AWATER',
            'returnGeometry': 'true',
            'f': 'json'
        }
        
        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        if 'features' not in data or not data['features']:
            return None
        
        # Convert ESRI JSON to GeoDataFrame (simplified version)
        features = []
        for feature in data['features']:
            attributes = feature.get('attributes', {})
            # Note: This is a simplified version - full ESRI JSON conversion would be more complex
            features.append(attributes)
        
        if not features:
            return None
        
        # Create basic DataFrame (without geometries for now)
        df = pd.DataFrame(features)
        
        # This would need proper ESRI JSON geometry conversion
        # For now, return None to fall back to other methods
        return None
    
    def get_census_data(
        self,
        geoids: List[str],
        variables: List[str],
        year: int = 2021,
        dataset: str = 'acs/acs5',
        api_key: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get census data for specified GEOIDs, with optional caching.
        
        Args:
            geoids: List of block group GEOIDs
            variables: List of census variable codes
            year: Census year
            dataset: Census dataset
            api_key: Census API key
            
        Returns:
            DataFrame with census data
        """
        # Check cache if enabled
        if self.cache_census_data:
            cached_data = self._get_cached_census_data(geoids, variables, year, dataset)
            if not cached_data.empty:
                return cached_data
        
        # Fetch from API
        data = self._fetch_census_data_from_api(geoids, variables, year, dataset, api_key)
        
        # Cache if enabled
        if self.cache_census_data and not data.empty:
            self._cache_census_data(data, year, dataset)
        
        return data
    
    def _get_cached_census_data(self, geoids: List[str], variables: List[str], year: int, dataset: str) -> pd.DataFrame:
        """Get cached census data from Parquet files."""
        cache_file = self.cache_dir / f"census_{year}_{dataset.replace('/', '_')}.parquet"
        
        if not cache_file.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(cache_file)
            # Filter to requested data
            df = df[
                (df['GEOID'].isin(geoids)) & 
                (df['variable_code'].isin(variables))
            ]
            return df
        except Exception as e:
            logger.warning(f"Error reading census cache: {e}")
            return pd.DataFrame()
    
    def _cache_census_data(self, data: pd.DataFrame, year: int, dataset: str):
        """Cache census data to Parquet files."""
        cache_file = self.cache_dir / f"census_{year}_{dataset.replace('/', '_')}.parquet"
        
        try:
            # Append to existing cache or create new
            if cache_file.exists():
                existing = pd.read_parquet(cache_file)
                combined = pd.concat([existing, data], ignore_index=True)
                combined = combined.drop_duplicates(subset=['GEOID', 'variable_code'])
            else:
                combined = data
            
            combined.to_parquet(cache_file, compression='snappy')
            # Removed noisy logging: get_progress_bar().write(f"Cached {len(data)} census records to {cache_file}")
            
        except Exception as e:
            logger.warning(f"Error caching census data: {e}")
    
    def _fetch_census_data_from_api(
        self,
        geoids: List[str],
        variables: List[str],
        year: int,
        dataset: str,
        api_key: Optional[str] = None
    ) -> pd.DataFrame:
        """Fetch census data from the Census API."""
        if not api_key:
            api_key = get_census_api_key()
            if not api_key:
                raise ValueError("Census API key required for fetching census data")
        
        # Group GEOIDs by state for efficient API calls
        state_geoids = {}
        for geoid in geoids:
            if len(geoid) >= 2:
                state_fips = geoid[:2]
                if state_fips not in state_geoids:
                    state_geoids[state_fips] = []
                state_geoids[state_fips].append(geoid)
        
        all_data = []
        
        for state_fips, state_geoids_list in state_geoids.items():
            state_name = state_fips_to_name(state_fips) or state_fips
            
            try:
                state_data = self._fetch_state_census_data(
                    state_fips, variables, year, dataset, api_key
                )
                
                if not state_data.empty:
                    # Filter to only the GEOIDs we need
                    state_data = state_data[state_data['GEOID'].isin(state_geoids_list)]
                    all_data.append(state_data)
                    
            except Exception as e:
                logger.error(f"Failed to fetch census data for state {state_fips}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        # Combine all state data
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Transform to long format
        return self._transform_to_long_format(combined_data, variables, year, dataset)
    
    def _fetch_state_census_data(
        self,
        state_fips: str,
        variables: List[str],
        year: int,
        dataset: str,
        api_key: str
    ) -> pd.DataFrame:
        """Fetch census data for a single state."""
        api_variables = variables.copy()
        if 'NAME' not in api_variables:
            api_variables.append('NAME')
        
        base_url = f'https://api.census.gov/data/{year}/{dataset}'
        
        params = {
            'get': ','.join(api_variables),
            'for': 'block group:*',
            'in': f'state:{state_fips} county:* tract:*',
            'key': api_key
        }
        
        try:
            rate_limiter.wait_if_needed("census")
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data or len(data) < 2:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Create GEOID
            df['GEOID'] = (
                df['state'].str.zfill(2) + 
                df['county'].str.zfill(3) + 
                df['tract'].str.zfill(6) + 
                df['block group']
            )
            
            return df
            
        except Exception as e:
            logger.error(f"API request failed for state {state_fips}: {e}")
            raise
    
    def _transform_to_long_format(
        self,
        data: pd.DataFrame,
        variables: List[str],
        year: int,
        dataset: str
    ) -> pd.DataFrame:
        """Transform wide format census data to long format."""
        records = []
        
        for _, row in data.iterrows():
            geoid = row['GEOID']
            
            for var in variables:
                if var in row:
                    # Get variable name from mapping
                    var_name = None
                    for name, code in CENSUS_VARIABLE_MAPPING.items():
                        if code == var:
                            var_name = name.replace('_', ' ').title()
                            break
                    
                    record = {
                        'GEOID': geoid,
                        'variable_code': var,
                        'variable_name': var_name or var,
                        'value': pd.to_numeric(row[var], errors='coerce'),
                        'margin_of_error': None,
                        'year': year,
                        'dataset': dataset
                    }
                    records.append(record)
        
        return pd.DataFrame(records)


# Global streaming manager instance
_streaming_manager = None

def get_streaming_census_manager(
    cache_census_data: bool = False,
    cache_dir: Optional[Path] = None
) -> StreamingCensusManager:
    """
    Get the global streaming census manager instance.
    
    Args:
        cache_census_data: Whether to cache census statistics
        cache_dir: Directory for optional census data cache
        
    Returns:
        StreamingCensusManager instance
    """
    global _streaming_manager
    
    if _streaming_manager is None:
        _streaming_manager = StreamingCensusManager(cache_census_data, cache_dir)
    
    return _streaming_manager


# Convenience functions for backward compatibility
def get_block_groups_streaming(state_fips: List[str], api_key: Optional[str] = None) -> gpd.GeoDataFrame:
    """Get block groups using pure streaming (no storage)."""
    manager = get_streaming_census_manager()
    return manager.get_block_groups(state_fips, api_key)

def get_census_data_streaming(
    geoids: List[str],
    variables: List[str],
    year: int = 2021,
    dataset: str = 'acs/acs5',
    api_key: Optional[str] = None,
    cache: bool = False
) -> pd.DataFrame:
    """Get census data using streaming with optional caching."""
    manager = get_streaming_census_manager(cache_census_data=cache)
    return manager.get_census_data(geoids, variables, year, dataset, api_key)
