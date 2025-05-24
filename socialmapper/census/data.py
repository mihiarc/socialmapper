#!/usr/bin/env python3
"""
Census data retrieval and management for the optimized census module.

This module handles:
- Fetching census data from the Census API
- Caching data in DuckDB
- Creating data views for analysis
- High-performance data operations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import geopandas as gpd
import requests
import httpx

from socialmapper.progress import get_progress_bar
from socialmapper.util import (
    normalize_census_variable,
    get_census_api_key,
    get_readable_census_variables,
    CENSUS_VARIABLE_MAPPING,
    rate_limiter,
    AsyncRateLimitedClient
)
from socialmapper.states import state_fips_to_name

from . import get_census_database, CensusDatabase

logger = logging.getLogger(__name__)


class CensusDataManager:
    """
    Manages census data retrieval, caching, and views.
    """
    
    def __init__(self, db: CensusDatabase):
        self.db = db
    
    def get_or_fetch_census_data(
        self,
        geoids: List[str],
        variables: List[str],
        year: int = 2021,
        dataset: str = 'acs/acs5',
        api_key: Optional[str] = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Get census data for specified GEOIDs, fetching from API if not cached.
        
        Args:
            geoids: List of block group GEOIDs
            variables: List of census variable codes
            year: Census year
            dataset: Census dataset
            api_key: Census API key
            force_refresh: Whether to force refresh from API
            
        Returns:
            DataFrame with census data
        """
        # Normalize variables
        normalized_vars = [normalize_census_variable(var) for var in variables]
        
        # Check what data we have cached
        cached_data = self._get_cached_data(geoids, normalized_vars, year, dataset)
        
        # Determine what we need to fetch
        if force_refresh or cached_data.empty:
            missing_geoids = geoids
            missing_vars = normalized_vars
        else:
            # Find missing combinations
            missing_geoids, missing_vars = self._find_missing_data(
                geoids, normalized_vars, year, dataset, cached_data
            )
        
        # Fetch missing data if needed
        if missing_geoids and missing_vars:
            new_data = self._fetch_census_data_from_api(
                missing_geoids, missing_vars, year, dataset, api_key
            )
            if not new_data.empty:
                self._store_census_data(new_data, year, dataset)
        
        # Return all requested data
        return self._get_cached_data(geoids, normalized_vars, year, dataset)
    
    def _get_cached_data(
        self,
        geoids: List[str],
        variables: List[str],
        year: int,
        dataset: str
    ) -> pd.DataFrame:
        """Get cached census data from database."""
        if not geoids or not variables:
            return pd.DataFrame()
        
        geoid_placeholders = ','.join(['?' for _ in geoids])
        var_placeholders = ','.join(['?' for _ in variables])
        
        query = f"""
            SELECT 
                GEOID,
                variable_code,
                variable_name,
                value,
                margin_of_error,
                year,
                dataset
            FROM census_data 
            WHERE GEOID IN ({geoid_placeholders})
                AND variable_code IN ({var_placeholders})
                AND year = ?
                AND dataset = ?
        """
        
        params = geoids + variables + [year, dataset]
        return self.db.conn.execute(query, params).df()
    
    def _find_missing_data(
        self,
        geoids: List[str],
        variables: List[str],
        year: int,
        dataset: str,
        cached_data: pd.DataFrame
    ) -> tuple[List[str], List[str]]:
        """Find missing GEOID/variable combinations."""
        if cached_data.empty:
            return geoids, variables
        
        # Get cached combinations
        cached_combinations = set(
            zip(cached_data['GEOID'], cached_data['variable_code'])
        )
        
        # Find missing combinations
        missing_geoids = set()
        missing_vars = set()
        
        for geoid in geoids:
            for var in variables:
                if (geoid, var) not in cached_combinations:
                    missing_geoids.add(geoid)
                    missing_vars.add(var)
        
        return list(missing_geoids), list(missing_vars)
    
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
        state_geoids = self._group_geoids_by_state(geoids)
        
        all_data = []
        
        for state_fips, state_geoids_list in state_geoids.items():
            state_name = state_fips_to_name(state_fips) or state_fips
            get_progress_bar().write(f"Fetching census data for {state_name} ({len(state_geoids_list)} block groups)")
            
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
        
        # Transform to long format for storage
        return self._transform_to_long_format(combined_data, variables, year, dataset)
    
    def _group_geoids_by_state(self, geoids: List[str]) -> Dict[str, List[str]]:
        """Group GEOIDs by state FIPS code."""
        state_geoids = {}
        for geoid in geoids:
            if len(geoid) >= 2:
                state_fips = geoid[:2]
                if state_fips not in state_geoids:
                    state_geoids[state_fips] = []
                state_geoids[state_fips].append(geoid)
        return state_geoids
    
    def _fetch_state_census_data(
        self,
        state_fips: str,
        variables: List[str],
        year: int,
        dataset: str,
        api_key: str
    ) -> pd.DataFrame:
        """Fetch census data for a single state."""
        # Ensure NAME is included
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
        """Transform wide format census data to long format for storage."""
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
                        'margin_of_error': None,  # Could be enhanced to fetch MOE
                        'year': year,
                        'dataset': dataset
                    }
                    records.append(record)
        
        return pd.DataFrame(records)
    
    def _store_census_data(self, data: pd.DataFrame, year: int, dataset: str):
        """Store census data in the database."""
        if data.empty:
            return
        
        # Insert records (replace if exists)
        records = data.to_dict('records')
        
        # Use executemany for better performance and handle conflicts properly
        self.db.conn.executemany("""
            INSERT INTO census_data 
            (GEOID, variable_code, variable_name, value, margin_of_error, year, dataset)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (GEOID, variable_code, year, dataset) 
            DO UPDATE SET 
                variable_name = excluded.variable_name,
                value = excluded.value,
                margin_of_error = excluded.margin_of_error
        """, [
            (record['GEOID'], record['variable_code'], record['variable_name'], 
             record['value'], record['margin_of_error'], record['year'], record['dataset'])
            for record in records
        ])
    
    def create_census_view(
        self,
        geoids: List[str],
        variables: List[str],
        year: int = 2021,
        dataset: str = 'acs/acs5'
    ) -> str:
        """
        Create a DuckDB view for census data analysis.
        
        Args:
            geoids: List of block group GEOIDs
            variables: List of census variable codes
            year: Census year
            dataset: Census dataset
            
        Returns:
            Name of the created view
        """
        view_name = f"census_view_{year}_{dataset.replace('/', '_')}"
        
        # Normalize variables
        normalized_vars = [normalize_census_variable(var) for var in variables]
        
        # Create pivot query for wide format
        var_cases = []
        for var in normalized_vars:
            var_cases.append(f"MAX(CASE WHEN variable_code = '{var}' THEN value END) AS {var}")
        
        geoid_placeholders = ','.join([f"'{geoid}'" for geoid in geoids])
        var_placeholders = ','.join([f"'{var}'" for var in normalized_vars])
        
        query = f"""
            CREATE OR REPLACE VIEW {view_name} AS
            SELECT 
                gu.GEOID,
                gu.STATEFP,
                gu.COUNTYFP,
                gu.TRACTCE,
                gu.BLKGRPCE,
                gu.NAME,
                gu.ALAND,
                gu.AWATER,
                {', '.join(var_cases)}
            FROM geographic_units gu
            LEFT JOIN census_data cd ON gu.GEOID = cd.GEOID
            WHERE gu.GEOID IN ({geoid_placeholders})
                AND gu.unit_type = 'block_group'
                AND (cd.variable_code IN ({var_placeholders}) OR cd.variable_code IS NULL)
                AND (cd.year = {year} OR cd.year IS NULL)
                AND (cd.dataset = '{dataset}' OR cd.dataset IS NULL)
            GROUP BY gu.GEOID, gu.STATEFP, gu.COUNTYFP, gu.TRACTCE, 
                     gu.BLKGRPCE, gu.NAME, gu.ALAND, gu.AWATER
        """
        
        self.db.conn.execute(query)
        return view_name
    
    def get_view_as_geodataframe(self, view_name: str) -> gpd.GeoDataFrame:
        """
        Get a DuckDB view as a GeoDataFrame.
        
        Args:
            view_name: Name of the view
            
        Returns:
            GeoDataFrame with the view data
        """
        df = self.db.conn.execute(f"SELECT * FROM {view_name}").df()
        
        if df.empty:
            return gpd.GeoDataFrame()
        
        # Since we're not storing geometries in the view (streaming approach),
        # we need to get the block groups with geometries separately
        from socialmapper.census import get_census_database
        
        # Get the GEOIDs from the view
        geoids = df['GEOID'].tolist()
        
        # Stream the block groups with geometries
        db = get_census_database()
        state_fips = list(set(df['STATEFP'].tolist()))
        block_groups_gdf = db.get_or_stream_block_groups(state_fips)
        
        # Filter to only the GEOIDs we need
        block_groups_gdf = block_groups_gdf[block_groups_gdf['GEOID'].isin(geoids)]
        
        # Merge the census data with the geometries
        result_gdf = block_groups_gdf.merge(df, on='GEOID', how='inner', suffixes=('', '_census'))
        
        # Add compatibility columns
        result_gdf['STATE'] = result_gdf['STATEFP']
        result_gdf['COUNTY'] = result_gdf['COUNTYFP']
        result_gdf['TRACT'] = result_gdf['TRACTCE']
        result_gdf['BLKGRP'] = result_gdf['BLKGRPCE']
        
        return result_gdf


# Note: Async functions have been integrated into CensusDataManager.
# Use CensusDataManager.get_or_fetch_census_data() for optimized data fetching.


# Note: Backward compatibility functions have been removed.
# Users should migrate to the new CensusDataManager API. 