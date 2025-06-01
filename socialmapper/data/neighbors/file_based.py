#!/usr/bin/env python3
"""
File-based neighbor relationship management for SocialMapper - DuckDB replacement.

This module provides neighbor identification using JSON and Parquet files
instead of DuckDB, eliminating database locking issues while maintaining
fast lookups for neighbor relationships.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import pandas as pd
import geopandas as gpd
from datetime import datetime
import requests

from ...core.environment import get_progress_bar
from ...utils.helpers import rate_limiter

logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_NEIGHBORS_DIR = Path.home() / ".socialmapper" / "cache" / "neighbors"

class FileNeighborManager:
    """
    File-based neighbor management system using optimal formats for each data type.
    
    File Format Rationale:
    - State neighbors: JSON (small, hierarchical, human-readable)
    - County neighbors: Parquet (large, tabular, performance-critical)  
    - Point cache: Parquet (growing, mixed types, query performance)
    """
    
    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the file-based neighbor manager.
        
        Args:
            cache_dir: Directory for neighbor cache files
        """
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_NEIGHBORS_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON for small, hierarchical state neighbor data
        self.state_neighbors_file = self.cache_dir / "state_neighbors.json"
        
        # Parquet for large, tabular county neighbor data
        self.county_neighbors_file = self.cache_dir / "county_neighbors.parquet"
        
        # Parquet for growing, mixed-type point cache
        self.point_cache_file = self.cache_dir / "point_geography_cache.parquet"
        
        # JSON for lightweight metadata
        self.metadata_file = self.cache_dir / "neighbors_metadata.json"
        
        logger.info(f"Initialized file-based neighbor manager at {self.cache_dir}")
    
    def get_neighboring_states(self, state_fips: str) -> List[str]:
        """
        Get neighboring states for a given state.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            List of neighboring state FIPS codes
        """
        state_neighbors = self._load_state_neighbors()
        return state_neighbors.get(state_fips, [])
    
    def get_neighboring_counties(self, state_fips: str, county_fips: str) -> List[Tuple[str, str]]:
        """
        Get neighboring counties for a given county.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            
        Returns:
            List of (state_fips, county_fips) tuples for neighboring counties
        """
        try:
            if not self.county_neighbors_file.exists():
                logger.warning("County neighbors file not found")
                return []
            
            df = pd.read_parquet(self.county_neighbors_file)
            
            # Filter for the specific county
            neighbors = df[
                (df['state_fips'] == state_fips) & 
                (df['county_fips'] == county_fips)
            ]
            
            # Return list of neighbor tuples
            return list(zip(neighbors['neighbor_state_fips'], neighbors['neighbor_county_fips']))
            
        except Exception as e:
            logger.error(f"Error getting neighboring counties: {e}")
            return []
    
    def get_geography_from_point(self, lat: float, lon: float, use_cache: bool = True, cache_result: bool = True) -> Optional[Dict[str, str]]:
        """
        Get geographic identifiers for a point using cached data with Census API fallback.
        
        Args:
            lat: Latitude
            lon: Longitude
            use_cache: Whether to check cache first
            cache_result: Whether to cache the API result
            
        Returns:
            Dictionary with geographic identifiers or None
        """
        # Check cache first if requested
        if use_cache:
            try:
                if self.point_cache_file.exists():
                    df = pd.read_parquet(self.point_cache_file)
                    
                    # Find closest cached point (simple approach)
                    df['distance'] = ((df['lat'] - lat) ** 2 + (df['lon'] - lon) ** 2) ** 0.5
                    closest = df.loc[df['distance'].idxmin()]
                    
                    # Return if close enough (within ~1km)
                    if closest['distance'] < 0.01:  # Roughly 1km
                        logger.debug(f"Found cached geography for point ({lat}, {lon})")
                        return {
                            'state_fips': closest['state_fips'],
                            'county_fips': closest['county_fips'],
                            'tract_geoid': closest.get('tract_geoid'),
                            'block_group_geoid': closest.get('block_group_geoid')
                        }
            except Exception as e:
                logger.warning(f"Error checking cache for point ({lat}, {lon}): {e}")
        
        # No cached result found, use Census API fallback
        logger.info(f"Geocoding point ({lat}, {lon}) using Census API")
        geo_info = self._geocode_point_with_census_api(lat, lon)
        
        # Cache the result if requested and successful
        if cache_result and geo_info and geo_info.get('state_fips'):
            self.cache_point_geography(lat, lon, geo_info)
        
        return geo_info
    
    def _geocode_point_with_census_api(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """
        Geocode a point using Census API to get geographic identifiers.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with geographic identifiers or None
        """
        try:
            # Use Census Geocoding API
            url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
            params = {
                'x': lon,
                'y': lat,
                'benchmark': 'Public_AR_Current',
                'vintage': 'Current_Current',
                'format': 'json'
            }
            
            rate_limiter.wait_if_needed("census")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'result' not in data or 'geographies' not in data['result']:
                logger.warning(f"No geography data found for point ({lat}, {lon})")
                return None
            
            geographies = data['result']['geographies']
            
            # Extract identifiers
            state_fips = None
            county_fips = None
            tract_geoid = None
            block_group_geoid = None
            
            # Get state
            if 'States' in geographies and geographies['States']:
                state_fips = geographies['States'][0].get('STATE')
            
            # Get county
            if 'Counties' in geographies and geographies['Counties']:
                county_fips = geographies['Counties'][0].get('COUNTY')
            
            # Get tract
            if 'Census Tracts' in geographies and geographies['Census Tracts']:
                tract_geoid = geographies['Census Tracts'][0].get('GEOID')
            
            # Get block group from 2020 Census Blocks data
            if '2020 Census Blocks' in geographies and geographies['2020 Census Blocks']:
                block_data = geographies['2020 Census Blocks'][0]
                
                # Extract components to build block group GEOID
                block_state = block_data.get('STATE')
                block_county = block_data.get('COUNTY') 
                block_tract = block_data.get('TRACT')
                block_group = block_data.get('BLKGRP')
                
                # Construct block group GEOID: STATE(2) + COUNTY(3) + TRACT(6) + BLKGRP(1) = 12 digits
                if all([block_state, block_county, block_tract, block_group]):
                    block_group_geoid = f"{block_state.zfill(2)}{block_county.zfill(3)}{block_tract.zfill(6)}{block_group}"
            
            result = {
                'state_fips': state_fips,
                'county_fips': county_fips,
                'tract_geoid': tract_geoid,
                'block_group_geoid': block_group_geoid
            }
            
            logger.debug(f"Geocoded ({lat}, {lon}): State {state_fips}, County {county_fips}, BG {block_group_geoid}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to geocode point ({lat}, {lon}) using Census API: {e}")
            return None
    
    def cache_point_geography(self, lat: float, lon: float, geo_info: Dict[str, str]):
        """
        Cache geographic information for a point.
        
        Args:
            lat: Latitude
            lon: Longitude
            geo_info: Geographic identifiers
        """
        try:
            # Load existing cache or create new
            if self.point_cache_file.exists():
                df = pd.read_parquet(self.point_cache_file)
            else:
                df = pd.DataFrame()
            
            # Add new point
            new_row = {
                'lat': lat,
                'lon': lon,
                'state_fips': geo_info.get('state_fips'),
                'county_fips': geo_info.get('county_fips'),
                'tract_geoid': geo_info.get('tract_geoid'),
                'block_group_geoid': geo_info.get('block_group_geoid'),
                'cached_at': datetime.now().isoformat()
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save back to file
            df.to_parquet(self.point_cache_file)
            
        except Exception as e:
            logger.error(f"Error caching point geography: {e}")
    
    def _load_state_neighbors(self) -> Dict[str, List[str]]:
        """Load state neighbor relationships from JSON file."""
        if not self.state_neighbors_file.exists():
            # Create default state neighbors data
            state_neighbors = self._get_default_state_neighbors()
            self._save_state_neighbors(state_neighbors)
            return state_neighbors
        
        try:
            with open(self.state_neighbors_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state neighbors: {e}")
            return {}
    
    def _save_state_neighbors(self, state_neighbors: Dict[str, List[str]]):
        """Save state neighbor relationships to JSON file."""
        try:
            with open(self.state_neighbors_file, 'w') as f:
                json.dump(state_neighbors, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state neighbors: {e}")
    
    def _get_default_state_neighbors(self) -> Dict[str, List[str]]:
        """Get default state neighbor relationships."""
        # This is a subset of US state adjacencies - in production you'd want the complete set
        return {
            "01": ["13", "28", "47"],  # Alabama: Georgia, Mississippi, Tennessee
            "02": [],  # Alaska: No land borders
            "04": ["06", "32", "35", "49"],  # Arizona: California, Nevada, New Mexico, Utah
            "05": ["22", "28", "35", "40", "47", "48"],  # Arkansas: Louisiana, Mississippi, New Mexico, Oklahoma, Tennessee, Texas
            "06": ["04", "32", "41"],  # California: Arizona, Nevada, Oregon
            "08": ["20", "31", "35", "49", "56"],  # Colorado: Kansas, Nebraska, New Mexico, Utah, Wyoming
            "09": ["25", "36", "44"],  # Connecticut: Massachusetts, New York, Rhode Island
            "10": ["24", "34", "42"],  # Delaware: Maryland, New Jersey, Pennsylvania
            "11": ["24", "51"],  # District of Columbia: Maryland, Virginia
            "12": ["01", "13"],  # Florida: Alabama, Georgia
            "13": ["01", "12", "37", "45", "47"],  # Georgia: Alabama, Florida, North Carolina, South Carolina, Tennessee
            "15": [],  # Hawaii: No land borders
            "16": ["30", "32", "41", "49", "53"],  # Idaho: Montana, Nevada, Oregon, Utah, Washington
            "17": ["18", "19", "21", "26", "29", "55"],  # Illinois: Indiana, Iowa, Kentucky, Michigan, Missouri, Wisconsin
            "18": ["17", "21", "26", "39"],  # Indiana: Illinois, Kentucky, Michigan, Ohio
            "19": ["17", "20", "26", "29", "31", "46"],  # Iowa: Illinois, Kansas, Michigan, Missouri, Nebraska, South Dakota
            "20": ["08", "19", "29", "31", "40"],  # Kansas: Colorado, Iowa, Missouri, Nebraska, Oklahoma
            "21": ["17", "18", "26", "39", "47", "54"],  # Kentucky: Illinois, Indiana, Michigan, Ohio, Tennessee, West Virginia
            "22": ["05", "28", "48"],  # Louisiana: Arkansas, Mississippi, Texas
            "23": ["33"],  # Maine: New Hampshire
            "24": ["10", "11", "34", "42", "51", "54"],  # Maryland: Delaware, DC, New Jersey, Pennsylvania, Virginia, West Virginia
            "25": ["09", "33", "36", "44", "50"],  # Massachusetts: Connecticut, New Hampshire, New York, Rhode Island, Vermont
            "26": ["17", "18", "19", "21", "39", "55"],  # Michigan: Illinois, Indiana, Iowa, Kentucky, Ohio, Wisconsin
            "27": ["19", "30", "38", "46", "55"],  # Minnesota: Iowa, Montana, North Dakota, South Dakota, Wisconsin
            "28": ["01", "05", "22", "47"],  # Mississippi: Alabama, Arkansas, Louisiana, Tennessee
            "29": ["05", "17", "19", "20", "31", "40", "47"],  # Missouri: Arkansas, Illinois, Iowa, Kansas, Nebraska, Oklahoma, Tennessee
            "30": ["16", "27", "38", "46", "56"],  # Montana: Idaho, Minnesota, North Dakota, South Dakota, Wyoming
            "31": ["08", "19", "20", "29", "46", "56"],  # Nebraska: Colorado, Iowa, Kansas, Missouri, South Dakota, Wyoming
            "32": ["04", "06", "16", "41", "49"],  # Nevada: Arizona, California, Idaho, Oregon, Utah
            "33": ["23", "25", "50"],  # New Hampshire: Maine, Massachusetts, Vermont
            "34": ["10", "24", "36", "42"],  # New Jersey: Delaware, Maryland, New York, Pennsylvania
            "35": ["04", "05", "08", "40", "48", "49"],  # New Mexico: Arizona, Arkansas, Colorado, Oklahoma, Texas, Utah
            "36": ["09", "25", "34", "42", "50"],  # New York: Connecticut, Massachusetts, New Jersey, Pennsylvania, Vermont
            "37": ["13", "45", "47", "51"],  # North Carolina: Georgia, South Carolina, Tennessee, Virginia
            "38": ["27", "30", "46"],  # North Dakota: Minnesota, Montana, South Dakota
            "39": ["18", "21", "26", "42", "54"],  # Ohio: Indiana, Kentucky, Michigan, Pennsylvania, West Virginia
            "40": ["05", "20", "29", "35", "48"],  # Oklahoma: Arkansas, Kansas, Missouri, New Mexico, Texas
            "41": ["06", "16", "32", "53"],  # Oregon: California, Idaho, Nevada, Washington
            "42": ["10", "24", "34", "36", "39", "54"],  # Pennsylvania: Delaware, Maryland, New Jersey, New York, Ohio, West Virginia
            "44": ["09", "25"],  # Rhode Island: Connecticut, Massachusetts
            "45": ["13", "37"],  # South Carolina: Georgia, North Carolina
            "46": ["19", "27", "30", "31", "38", "56"],  # South Dakota: Iowa, Minnesota, Montana, Nebraska, North Dakota, Wyoming
            "47": ["01", "05", "13", "21", "28", "29", "37", "51"],  # Tennessee: Alabama, Arkansas, Georgia, Kentucky, Mississippi, Missouri, North Carolina, Virginia
            "48": ["05", "22", "35", "40"],  # Texas: Arkansas, Louisiana, New Mexico, Oklahoma
            "49": ["04", "08", "16", "32", "35", "56"],  # Utah: Arizona, Colorado, Idaho, Nevada, New Mexico, Wyoming
            "50": ["25", "33", "36"],  # Vermont: Massachusetts, New Hampshire, New York
            "51": ["11", "21", "24", "37", "47", "54"],  # Virginia: DC, Kentucky, Maryland, North Carolina, Tennessee, West Virginia
            "53": ["16", "41"],  # Washington: Idaho, Oregon
            "54": ["21", "24", "39", "42", "51"],  # West Virginia: Kentucky, Maryland, Ohio, Pennsylvania, Virginia
            "55": ["17", "19", "26", "27"],  # Wisconsin: Illinois, Iowa, Michigan, Minnesota
            "56": ["08", "16", "30", "31", "46", "49"]   # Wyoming: Colorado, Idaho, Montana, Nebraska, South Dakota, Utah
        }
    
    def get_counties_from_pois(self, 
                              pois: List[Dict[str, Any]], 
                              include_neighbors: bool = False,
                              neighbor_distance: int = 1) -> List[Tuple[str, str]]:
        """
        Get counties for POIs, optionally including neighboring counties.
        
        Args:
            pois: List of POI dictionaries with lat/lon
            include_neighbors: Whether to include neighboring counties
            neighbor_distance: How many neighbor levels to include
            
        Returns:
            List of (state_fips, county_fips) tuples
        """
        counties = set()
        
        for poi in pois:
            lat = poi.get('lat')
            lon = poi.get('lon')
            
            if lat is None or lon is None:
                continue
            
            # Get geography for this point
            geo_info = self.get_geography_from_point(lat, lon)
            
            if geo_info and geo_info.get('state_fips') and geo_info.get('county_fips'):
                state_fips = geo_info['state_fips']
                county_fips = geo_info['county_fips']
                counties.add((state_fips, county_fips))
                
                # Add neighboring counties if requested
                if include_neighbors:
                    neighbors = self.get_neighboring_counties(state_fips, county_fips)
                    counties.update(neighbors)
                    
                    # Add additional neighbor levels if requested
                    if neighbor_distance > 1:
                        for level in range(2, neighbor_distance + 1):
                            next_level_neighbors = set()
                            for neighbor_state, neighbor_county in neighbors:
                                next_neighbors = self.get_neighboring_counties(neighbor_state, neighbor_county)
                                next_level_neighbors.update(next_neighbors)
                            counties.update(next_level_neighbors)
                            neighbors = next_level_neighbors
        
        return list(counties)
    
    def get_neighbor_statistics(self) -> Dict[str, int]:
        """Get statistics about cached neighbor data."""
        stats = {
            'state_neighbors': 0,
            'county_neighbors': 0,
            'cached_points': 0
        }
        
        try:
            # State neighbors
            state_neighbors = self._load_state_neighbors()
            stats['state_neighbors'] = sum(len(neighbors) for neighbors in state_neighbors.values())
            
            # County neighbors
            if self.county_neighbors_file.exists():
                df = pd.read_parquet(self.county_neighbors_file)
                stats['county_neighbors'] = len(df)
            
            # Cached points
            if self.point_cache_file.exists():
                df = pd.read_parquet(self.point_cache_file)
                stats['cached_points'] = len(df)
                
        except Exception as e:
            logger.error(f"Error getting neighbor statistics: {e}")
        
        return stats


# Backward compatibility functions
def get_file_neighbor_manager(cache_dir: Optional[Union[str, Path]] = None) -> FileNeighborManager:
    """Get the global file-based neighbor manager instance."""
    global _file_neighbor_manager
    
    if '_file_neighbor_manager' not in globals() or _file_neighbor_manager is None:
        _file_neighbor_manager = FileNeighborManager(cache_dir)
    
    return _file_neighbor_manager

def get_neighboring_states(state_fips: str) -> List[str]:
    """Get neighboring states for a given state (file-based version)."""
    manager = get_file_neighbor_manager()
    return manager.get_neighboring_states(state_fips)

def get_neighboring_counties(state_fips: str, county_fips: str) -> List[Tuple[str, str]]:
    """Get neighboring counties for a given county (file-based version)."""
    manager = get_file_neighbor_manager()
    return manager.get_neighboring_counties(state_fips, county_fips)

def get_geography_from_point(lat: float, lon: float) -> Optional[Dict[str, str]]:
    """Get geographic identifiers for a point (file-based version)."""
    manager = get_file_neighbor_manager()
    return manager.get_geography_from_point(lat, lon)

def get_counties_from_pois(pois: List[Dict[str, Any]], 
                          include_neighbors: bool = False,
                          neighbor_distance: int = 1) -> List[Tuple[str, str]]:
    """Get counties for POIs (file-based version)."""
    manager = get_file_neighbor_manager()
    return manager.get_counties_from_pois(pois, include_neighbors, neighbor_distance)

# Global instance
_file_neighbor_manager = None 