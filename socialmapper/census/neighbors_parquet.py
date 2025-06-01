#!/usr/bin/env python3
"""
Parquet-based neighbor relationship management for SocialMapper.

This module provides optimized neighbor identification using Parquet files
to store pre-computed neighbor relationships. This replaces the DuckDB approach
with a more efficient, data-processing-friendly format that's better for large jobs.
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point

from socialmapper.progress import get_progress_bar
from socialmapper.util import get_census_api_key, rate_limiter

logger = logging.getLogger(__name__)

# Check if PyArrow is available for Parquet support
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    logger.warning("PyArrow not available - Parquet functionality disabled")

# Default paths for neighbor data files
def get_default_neighbor_data_path() -> Path:
    """Get the default path for neighbor data files."""
    # Try packaged data first
    package_data_path = Path(__file__).parent.parent / "data" / "neighbors"
    if package_data_path.exists():
        return package_data_path
    
    # Fall back to user directory for development/custom setups
    return Path.home() / ".socialmapper" / "neighbors"

DEFAULT_NEIGHBOR_DATA_PATH = get_default_neighbor_data_path()


class NeighborDataManager:
    """
    Manages pre-computed neighbor relationships using Parquet files.
    
    This approach provides:
    - Fast I/O with columnar storage
    - Easy integration with pandas/polars for large-scale processing
    - Smaller file sizes with compression
    - Better GitHub compatibility
    - Easier data inspection and debugging
    """
    
    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        """
        Initialize the neighbor data manager.
        
        Args:
            data_path: Path to the neighbor data directory. If None, uses default location.
        """
        self.data_path = Path(data_path) if data_path else DEFAULT_NEIGHBOR_DATA_PATH
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # File paths for different relationship types
        self.state_neighbors_path = self.data_path / "state_neighbors.parquet"
        self.county_neighbors_path = self.data_path / "county_neighbors.parquet"
        self.tract_neighbors_path = self.data_path / "tract_neighbors.parquet"
        self.block_group_neighbors_path = self.data_path / "block_group_neighbors.parquet"
        self.point_cache_path = self.data_path / "point_geography_cache.parquet"
        self.metadata_path = self.data_path / "metadata.parquet"
        
        # Cached DataFrames for performance
        self._state_neighbors_df = None
        self._county_neighbors_df = None
        self._point_cache_df = None
        self._metadata_df = None
        
        logger.info(f"Initialized neighbor data manager at {self.data_path}")
    
    def _load_state_neighbors(self) -> pd.DataFrame:
        """Load state neighbors DataFrame with caching."""
        if self._state_neighbors_df is None:
            if self.state_neighbors_path.exists():
                self._state_neighbors_df = pd.read_parquet(self.state_neighbors_path)
            else:
                # Create empty DataFrame with correct schema
                self._state_neighbors_df = pd.DataFrame({
                    'state_fips': pd.Series(dtype='string'),
                    'neighbor_state_fips': pd.Series(dtype='string'),
                    'relationship_type': pd.Series(dtype='string')
                })
        return self._state_neighbors_df
    
    def _load_county_neighbors(self) -> pd.DataFrame:
        """Load county neighbors DataFrame with caching."""
        if self._county_neighbors_df is None:
            if self.county_neighbors_path.exists():
                self._county_neighbors_df = pd.read_parquet(self.county_neighbors_path)
            else:
                # Create empty DataFrame with correct schema
                self._county_neighbors_df = pd.DataFrame({
                    'state_fips': pd.Series(dtype='string'),
                    'county_fips': pd.Series(dtype='string'),
                    'neighbor_state_fips': pd.Series(dtype='string'),
                    'neighbor_county_fips': pd.Series(dtype='string'),
                    'relationship_type': pd.Series(dtype='string'),
                    'shared_boundary_length': pd.Series(dtype='float64')
                })
        return self._county_neighbors_df
    
    def _load_point_cache(self) -> pd.DataFrame:
        """Load point geography cache DataFrame with caching."""
        if self._point_cache_df is None:
            if self.point_cache_path.exists():
                self._point_cache_df = pd.read_parquet(self.point_cache_path)
            else:
                # Create empty DataFrame with correct schema
                self._point_cache_df = pd.DataFrame({
                    'lat': pd.Series(dtype='float64'),
                    'lon': pd.Series(dtype='float64'),
                    'state_fips': pd.Series(dtype='string'),
                    'county_fips': pd.Series(dtype='string'),
                    'tract_geoid': pd.Series(dtype='string'),
                    'block_group_geoid': pd.Series(dtype='string'),
                    'cached_at': pd.Series(dtype='datetime64[ns]')
                })
        return self._point_cache_df
    
    def _load_metadata(self) -> pd.DataFrame:
        """Load metadata DataFrame with caching."""
        if self._metadata_df is None:
            if self.metadata_path.exists():
                self._metadata_df = pd.read_parquet(self.metadata_path)
            else:
                # Create empty DataFrame with correct schema
                self._metadata_df = pd.DataFrame({
                    'key': pd.Series(dtype='string'),
                    'value': pd.Series(dtype='string'),
                    'updated_at': pd.Series(dtype='datetime64[ns]')
                })
        return self._metadata_df
    
    def save_state_neighbors(self, df: pd.DataFrame):
        """Save state neighbors DataFrame to Parquet."""
        if not PARQUET_AVAILABLE:
            raise RuntimeError("PyArrow not available - cannot save Parquet files")
        
        # Ensure correct data types
        df = df.astype({
            'state_fips': 'string',
            'neighbor_state_fips': 'string',
            'relationship_type': 'string'
        })
        
        df.to_parquet(self.state_neighbors_path, compression='snappy', index=False)
        self._state_neighbors_df = df  # Update cache
        logger.info(f"Saved {len(df)} state neighbor relationships to {self.state_neighbors_path}")
    
    def save_county_neighbors(self, df: pd.DataFrame):
        """Save county neighbors DataFrame to Parquet."""
        if not PARQUET_AVAILABLE:
            raise RuntimeError("PyArrow not available - cannot save Parquet files")
        
        # Ensure correct data types
        df = df.astype({
            'state_fips': 'string',
            'county_fips': 'string',
            'neighbor_state_fips': 'string',
            'neighbor_county_fips': 'string',
            'relationship_type': 'string',
            'shared_boundary_length': 'float64'
        })
        
        df.to_parquet(self.county_neighbors_path, compression='snappy', index=False)
        self._county_neighbors_df = df  # Update cache
        logger.info(f"Saved {len(df)} county neighbor relationships to {self.county_neighbors_path}")
    
    def save_point_cache(self, df: pd.DataFrame):
        """Save point geography cache DataFrame to Parquet."""
        if not PARQUET_AVAILABLE:
            raise RuntimeError("PyArrow not available - cannot save Parquet files")
        
        # Ensure correct data types
        df = df.astype({
            'lat': 'float64',
            'lon': 'float64',
            'state_fips': 'string',
            'county_fips': 'string',
            'tract_geoid': 'string',
            'block_group_geoid': 'string'
        })
        
        # Add timestamp if not present
        if 'cached_at' not in df.columns:
            df['cached_at'] = pd.Timestamp.now()
        
        df.to_parquet(self.point_cache_path, compression='snappy', index=False)
        self._point_cache_df = df  # Update cache
        logger.info(f"Saved {len(df)} cached points to {self.point_cache_path}")
    
    def save_metadata(self, df: pd.DataFrame):
        """Save metadata DataFrame to Parquet."""
        if not PARQUET_AVAILABLE:
            raise RuntimeError("PyArrow not available - cannot save Parquet files")
        
        # Ensure correct data types
        df = df.astype({
            'key': 'string',
            'value': 'string'
        })
        
        # Add timestamp if not present
        if 'updated_at' not in df.columns:
            df['updated_at'] = pd.Timestamp.now()
        
        df.to_parquet(self.metadata_path, compression='snappy', index=False)
        self._metadata_df = df  # Update cache
        logger.info(f"Saved {len(df)} metadata entries to {self.metadata_path}")
    
    def get_file_sizes(self) -> Dict[str, float]:
        """Get file sizes in MB for all neighbor data files."""
        sizes = {}
        for name, path in [
            ('state_neighbors', self.state_neighbors_path),
            ('county_neighbors', self.county_neighbors_path),
            ('tract_neighbors', self.tract_neighbors_path),
            ('block_group_neighbors', self.block_group_neighbors_path),
            ('point_cache', self.point_cache_path),
            ('metadata', self.metadata_path)
        ]:
            if path.exists():
                sizes[name] = path.stat().st_size / (1024 * 1024)  # Convert to MB
            else:
                sizes[name] = 0.0
        
        sizes['total'] = sum(sizes.values())
        return sizes


class NeighborManager:
    """
    Manages pre-computed neighbor relationships using Parquet files.
    
    This class provides the same interface as the DuckDB version but with
    better performance for large-scale data processing.
    """
    
    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        """
        Initialize the neighbor manager.
        
        Args:
            data_path: Path to the neighbor data directory. If None, uses default location.
        """
        self.data_manager = NeighborDataManager(data_path)
    
    def initialize_state_neighbors(self, force_refresh: bool = False) -> int:
        """
        Initialize state neighbor relationships from known adjacencies.
        
        Args:
            force_refresh: Whether to refresh existing data
            
        Returns:
            Number of neighbor relationships created
        """
        # Check if already initialized
        if not force_refresh and self.data_manager.state_neighbors_path.exists():
            df = self.data_manager._load_state_neighbors()
            if len(df) > 0:
                return len(df)
        
        # State adjacency data
        STATE_NEIGHBORS = {
            '01': ['12', '13', '28', '47'],  # AL: FL, GA, MS, TN
            '02': [],  # AK: (no land borders)
            '04': ['06', '08', '35', '32', '49'],  # AZ: CA, CO, NM, NV, UT
            '05': ['22', '29', '28', '40', '47', '48'],  # AR: LA, MO, MS, OK, TN, TX
            '06': ['04', '32', '41'],  # CA: AZ, NV, OR
            '08': ['04', '20', '31', '35', '40', '49', '56'],  # CO: AZ, KS, NE, NM, OK, UT, WY
            '09': ['25', '36', '44'],  # CT: MA, NY, RI
            '10': ['24', '34', '42'],  # DE: MD, NJ, PA
            '12': ['01', '13'],  # FL: AL, GA
            '13': ['01', '12', '37', '45', '47'],  # GA: AL, FL, NC, SC, TN
            '15': [],  # HI: (no land borders)
            '16': ['30', '32', '41', '49', '53', '56'],  # ID: MT, NV, OR, UT, WA, WY
            '17': ['18', '19', '21', '29', '55'],  # IL: IN, IA, KY, MO, WI
            '18': ['17', '21', '26', '39'],  # IN: IL, KY, MI, OH
            '19': ['17', '27', '29', '31', '46', '55'],  # IA: IL, MN, MO, NE, SD, WI
            '20': ['08', '29', '31', '40'],  # KS: CO, MO, NE, OK
            '21': ['17', '18', '29', '39', '47', '51', '54'],  # KY: IL, IN, MO, OH, TN, VA, WV
            '22': ['05', '28', '48'],  # LA: AR, MS, TX
            '23': ['33'],  # ME: NH
            '24': ['10', '42', '51', '54', '11'],  # MD: DE, PA, VA, WV, DC
            '25': ['09', '33', '36', '44', '50'],  # MA: CT, NH, NY, RI, VT
            '26': ['18', '39', '55'],  # MI: IN, OH, WI
            '27': ['19', '38', '46', '55'],  # MN: IA, ND, SD, WI
            '28': ['01', '05', '22', '47'],  # MS: AL, AR, LA, TN
            '29': ['05', '17', '19', '20', '21', '31', '40', '47'],  # MO: AR, IL, IA, KS, KY, NE, OK, TN
            '30': ['16', '38', '46', '56'],  # MT: ID, ND, SD, WY
            '31': ['08', '19', '20', '29', '46', '56'],  # NE: CO, IA, KS, MO, SD, WY
            '32': ['04', '06', '16', '41', '49'],  # NV: AZ, CA, ID, OR, UT
            '33': ['23', '25', '50'],  # NH: ME, MA, VT
            '34': ['10', '36', '42'],  # NJ: DE, NY, PA
            '35': ['04', '08', '40', '48', '49'],  # NM: AZ, CO, OK, TX, UT
            '36': ['09', '25', '34', '42', '50'],  # NY: CT, MA, NJ, PA, VT
            '37': ['13', '45', '47', '51'],  # NC: GA, SC, TN, VA
            '38': ['27', '30', '46'],  # ND: MN, MT, SD
            '39': ['18', '21', '26', '42', '54'],  # OH: IN, KY, MI, PA, WV
            '40': ['05', '08', '20', '29', '35', '48'],  # OK: AR, CO, KS, MO, NM, TX
            '41': ['06', '16', '32', '53'],  # OR: CA, ID, NV, WA
            '42': ['10', '24', '34', '36', '39', '54'],  # PA: DE, MD, NJ, NY, OH, WV
            '44': ['09', '25'],  # RI: CT, MA
            '45': ['13', '37'],  # SC: GA, NC
            '46': ['19', '27', '30', '31', '38', '56'],  # SD: IA, MN, MT, NE, ND, WY
            '47': ['01', '05', '13', '21', '28', '29', '37', '51'],  # TN: AL, AR, GA, KY, MS, MO, NC, VA
            '48': ['05', '22', '35', '40'],  # TX: AR, LA, NM, OK
            '49': ['04', '08', '16', '35', '32', '56'],  # UT: AZ, CO, ID, NM, NV, WY
            '50': ['25', '33', '36'],  # VT: MA, NH, NY
            '51': ['21', '24', '37', '47', '54', '11'],  # VA: KY, MD, NC, TN, WV, DC
            '53': ['16', '41'],  # WA: ID, OR
            '54': ['21', '24', '39', '42', '51'],  # WV: KY, MD, OH, PA, VA
            '55': ['17', '19', '26', '27'],  # WI: IL, IA, MI, MN
            '56': ['08', '16', '30', '31', '46', '49'],  # WY: CO, ID, MT, NE, SD, UT
            '11': ['24', '51']  # DC: MD, VA
        }
        
        # Create DataFrame
        relationships = []
        for state_fips, neighbors in STATE_NEIGHBORS.items():
            for neighbor_fips in neighbors:
                relationships.append({
                    'state_fips': state_fips,
                    'neighbor_state_fips': neighbor_fips,
                    'relationship_type': 'adjacent'
                })
        
        df = pd.DataFrame(relationships)
        
        if len(df) > 0:
            self.data_manager.save_state_neighbors(df)
        
        count = len(df)
        
        # Update metadata
        metadata_df = pd.DataFrame([{
            'key': 'state_neighbors_initialized',
            'value': str(count),
            'updated_at': pd.Timestamp.now()
        }])
        self.data_manager.save_metadata(metadata_df)
        
        return count
    
    def get_neighboring_states(self, state_fips: str) -> List[str]:
        """
        Get neighboring states for a given state.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            List of neighboring state FIPS codes
        """
        df = self.data_manager._load_state_neighbors()
        neighbors = df[df['state_fips'] == state_fips]['neighbor_state_fips'].tolist()
        return sorted(neighbors)
    
    def get_neighboring_counties(
        self, 
        state_fips: str, 
        county_fips: str,
        include_cross_state: bool = True
    ) -> List[Tuple[str, str]]:
        """
        Get neighboring counties for a given county.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            include_cross_state: Whether to include cross-state neighbors
            
        Returns:
            List of (neighbor_state_fips, neighbor_county_fips) tuples
        """
        df = self.data_manager._load_county_neighbors()
        
        # Filter for the specific county
        county_neighbors = df[
            (df['state_fips'] == state_fips) & 
            (df['county_fips'] == county_fips)
        ]
        
        # Filter by cross-state preference
        if not include_cross_state:
            county_neighbors = county_neighbors[
                county_neighbors['neighbor_state_fips'] == state_fips
            ]
        
        # Return as list of tuples
        neighbors = [
            (row['neighbor_state_fips'], row['neighbor_county_fips'])
            for _, row in county_neighbors.iterrows()
        ]
        
        return sorted(neighbors)
    
    def get_geography_from_point(
        self, 
        lat: float, 
        lon: float,
        use_cache: bool = True,
        cache_result: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Get complete geographic identifiers for a point.
        
        Args:
            lat: Latitude
            lon: Longitude
            use_cache: Whether to use cached results
            cache_result: Whether to cache the result
            
        Returns:
            Dictionary with geographic identifiers
        """
        # Check cache first
        if use_cache:
            cache_df = self.data_manager._load_point_cache()
            cached = cache_df[
                (cache_df['lat'] == lat) & (cache_df['lon'] == lon)
            ]
            
            if len(cached) > 0:
                row = cached.iloc[0]
                # Convert pandas NA values to None
                return {
                    'state_fips': None if pd.isna(row['state_fips']) else str(row['state_fips']),
                    'county_fips': None if pd.isna(row['county_fips']) else str(row['county_fips']),
                    'tract_geoid': None if pd.isna(row['tract_geoid']) else str(row['tract_geoid']),
                    'block_group_geoid': None if pd.isna(row['block_group_geoid']) else str(row['block_group_geoid'])
                }
        
        # Geocode the point using Census Bureau API
        result = self._geocode_with_census_api(lat, lon)
        
        # Cache the result if requested and geocoding was successful
        if cache_result and result['state_fips'] is not None:
            cache_df = self.data_manager._load_point_cache()
            new_row = pd.DataFrame([{
                'lat': lat,
                'lon': lon,
                'state_fips': result['state_fips'],
                'county_fips': result['county_fips'],
                'tract_geoid': result['tract_geoid'],
                'block_group_geoid': result['block_group_geoid'],
                'cached_at': pd.Timestamp.now()
            }])
            
            updated_cache = pd.concat([cache_df, new_row], ignore_index=True)
            self.data_manager.save_point_cache(updated_cache)
        
        return result
    
    def _geocode_with_census_api(self, lat: float, lon: float) -> Dict[str, Optional[str]]:
        """
        Geocode a point using the Census Bureau's geocoding API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with geographic identifiers
        """
        try:
            # Use Census Bureau's geocoding API
            url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
            params = {
                'x': lon,
                'y': lat,
                'benchmark': 'Public_AR_Current',
                'vintage': 'Current_Current',
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if geocoding was successful
                if 'result' in data and 'geographies' in data['result']:
                    geographies = data['result']['geographies']
                    
                    # Extract FIPS codes from the response
                    state_fips = None
                    county_fips = None
                    tract_geoid = None
                    block_group_geoid = None
                    
                    # Get state and county from Counties layer
                    if 'Counties' in geographies and geographies['Counties']:
                        county_info = geographies['Counties'][0]
                        state_fips = county_info.get('STATE')
                        county_fips = county_info.get('COUNTY')
                    
                    # Get tract from Census Tracts layer
                    if 'Census Tracts' in geographies and geographies['Census Tracts']:
                        tract_info = geographies['Census Tracts'][0]
                        tract_geoid = tract_info.get('GEOID')
                    
                    # Get block group from Census Block Groups layer (if available)
                    if 'Census Block Groups' in geographies and geographies['Census Block Groups']:
                        bg_info = geographies['Census Block Groups'][0]
                        block_group_geoid = bg_info.get('GEOID')
                    # Fallback: derive block group from block if available
                    elif 'Census Blocks' in geographies and geographies['Census Blocks']:
                        block_info = geographies['Census Blocks'][0]
                        block_geoid = block_info.get('GEOID')
                        if block_geoid and len(block_geoid) >= 12:
                            # Block group is first 12 characters of block GEOID
                            block_group_geoid = block_geoid[:12]
                    
                    return {
                        'state_fips': state_fips,
                        'county_fips': county_fips,
                        'tract_geoid': tract_geoid,
                        'block_group_geoid': block_group_geoid
                    }
            
            # If geocoding failed, log the issue
            logger.warning(f"Geocoding failed for point ({lat}, {lon}): {response.status_code}")
            
        except Exception as e:
            logger.warning(f"Geocoding error for point ({lat}, {lon}): {e}")
        
        # Return None values if geocoding failed
        return {
            'state_fips': None,
            'county_fips': None,
            'tract_geoid': None,
            'block_group_geoid': None
        }
    
    def get_counties_from_pois(
        self, 
        pois: List[Dict],
        include_neighbors: bool = True,
        neighbor_distance: int = 1
    ) -> List[Tuple[str, str]]:
        """
        Get counties for POIs with optional neighbors.
        
        Args:
            pois: List of POI dictionaries with 'lat' and 'lon' keys
            include_neighbors: Whether to include neighboring counties
            neighbor_distance: How many levels of neighbors to include
            
        Returns:
            List of (state_fips, county_fips) tuples
        """
        counties = set()
        
        # Get counties for each POI
        for poi in pois:
            if 'lat' in poi and 'lon' in poi:
                geography = self.get_geography_from_point(poi['lat'], poi['lon'])
                
                # Explicitly check for valid FIPS codes (not None or empty)
                state_fips = geography.get('state_fips')
                county_fips = geography.get('county_fips')
                
                if state_fips is not None and county_fips is not None and state_fips != '' and county_fips != '':
                    counties.add((state_fips, county_fips))
        
        # Add neighbors if requested
        if include_neighbors:
            original_counties = counties.copy()
            for state_fips, county_fips in original_counties:
                neighbors = self.get_neighboring_counties(state_fips, county_fips)
                counties.update(neighbors)
        
        return sorted(list(counties))
    
    def get_neighbor_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the neighbor relationships.
        
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        # State neighbor statistics
        state_df = self.data_manager._load_state_neighbors()
        stats['state_relationships'] = len(state_df)
        
        # County neighbor statistics
        county_df = self.data_manager._load_county_neighbors()
        stats['county_relationships'] = len(county_df)
        
        # Cross-state county relationships
        cross_state_count = len(county_df[
            county_df['state_fips'] != county_df['neighbor_state_fips']
        ])
        stats['cross_state_county_relationships'] = cross_state_count
        
        # Point cache statistics
        cache_df = self.data_manager._load_point_cache()
        stats['cached_points'] = len(cache_df)
        
        # States with county data
        states_with_counties = county_df['state_fips'].nunique()
        stats['states_with_county_data'] = states_with_counties
        
        # File sizes
        file_sizes = self.data_manager.get_file_sizes()
        stats['total_size_mb'] = file_sizes['total']
        stats['file_sizes'] = file_sizes
        
        return stats


# Global instance
_neighbor_manager = None

def get_neighbor_manager(data_path: Optional[Union[str, Path]] = None) -> NeighborManager:
    """
    Get the global neighbor manager instance.
    
    Args:
        data_path: Optional path to neighbor data directory
        
    Returns:
        NeighborManager instance
    """
    global _neighbor_manager
    
    if _neighbor_manager is None or data_path is not None:
        _neighbor_manager = NeighborManager(data_path)
    
    return _neighbor_manager

def initialize_all_neighbors(force_refresh: bool = False) -> Dict[str, int]:
    """
    Initialize all neighbor relationships.
    
    Args:
        force_refresh: Whether to refresh existing data
        
    Returns:
        Dictionary with counts of relationships created
    """
    manager = get_neighbor_manager()
    
    results = {}
    
    # Initialize state neighbors
    results['state_neighbors'] = manager.initialize_state_neighbors(force_refresh)
    
    # County neighbors would be initialized separately (for package creation)
    # results['county_neighbors'] = manager.initialize_county_neighbors(force_refresh)
    
    return results

# Convenience functions for backward compatibility
def get_neighboring_states(state_fips: str) -> List[str]:
    """Get neighboring states for a given state."""
    return get_neighbor_manager().get_neighboring_states(state_fips)

def get_neighboring_counties(state_fips: str, county_fips: str, include_cross_state: bool = True) -> List[Tuple[str, str]]:
    """Get neighboring counties for a given county."""
    return get_neighbor_manager().get_neighboring_counties(state_fips, county_fips, include_cross_state)

def get_geography_from_point(lat: float, lon: float) -> Dict[str, Optional[str]]:
    """Get complete geographic identifiers for a point."""
    return get_neighbor_manager().get_geography_from_point(lat, lon)

def get_counties_from_pois(pois: List[Dict], include_neighbors: bool = True) -> List[Tuple[str, str]]:
    """Get counties for POIs with optional neighbors."""
    return get_neighbor_manager().get_counties_from_pois(pois, include_neighbors) 