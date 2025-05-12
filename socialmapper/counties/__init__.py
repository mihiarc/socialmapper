#!/usr/bin/env python3
"""
County management utilities for the SocialMapper project.

This module provides tools for working with US counties including:
- Converting between county FIPS codes, names, and other identifiers
- Getting neighboring counties
- Fetching block groups at the county level
"""
import os
import requests
import logging
import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from tqdm import tqdm
from socialmapper.progress import get_progress_bar
from functools import lru_cache
import concurrent.futures
import json
from rtree import index
import time
from shapely.geometry import Polygon

# Set up logging
logger = logging.getLogger(__name__)

# Check if we have pyogrio/arrow support for better performance
try:
    import pyogrio
    USE_ARROW = True
except ImportError:
    USE_ARROW = False


# Create a global cache for county spatial data
_COUNTY_SPATIAL_INDEX = None
_COUNTY_DATA = None

def _init_county_spatial_index(debug=False, use_mock_on_failure=True, use_bundled_data=True) -> Tuple[index.Index, gpd.GeoDataFrame]:
    """
    Initialize a spatial index for all US counties to enable fast point-in-polygon lookups.
    
    Args:
        debug: Enable debug mode with more logging
        use_mock_on_failure: Fall back to mock data if API calls fail
        use_bundled_data: Use the bundled county data instead of making API calls
        
    Returns:
        A tuple containing the spatial index and the county GeoDataFrame
    """
    global _COUNTY_SPATIAL_INDEX, _COUNTY_DATA
    
    if _COUNTY_SPATIAL_INDEX is not None and _COUNTY_DATA is not None:
        return _COUNTY_SPATIAL_INDEX, _COUNTY_DATA
    
    try:
        # First try to use bundled data if available and requested
        if use_bundled_data:
            try:
                # Load from bundled data
                data_path = Path(__file__).parent / "data" / "us_counties.parquet"
                
                if data_path.exists():
                    logger.debug(f"Loading county data from bundled package data")
                    counties_gdf = gpd.read_parquet(data_path)
                    
                    # Create spatial index for counties
                    spatial_idx = index.Index()
                    for idx, county in counties_gdf.iterrows():
                        spatial_idx.insert(idx, county.geometry.bounds)
                    
                    _COUNTY_SPATIAL_INDEX = spatial_idx
                    _COUNTY_DATA = counties_gdf
                    
                    logger.debug(f"Successfully loaded spatial index from bundled data with {len(counties_gdf)} counties")
                    return spatial_idx, counties_gdf
                else:
                    logger.warning("Bundled county data not found, falling back to API")
            except Exception as e:
                logger.warning(f"Error loading bundled county data: {e}")
                if debug:
                    logger.exception("Detailed error:")
        
        # If bundled data not available or not requested, use the API
        logger.debug("Initializing county spatial index from Census API")
        url = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query'
        
        params = {
            'where': "1=1",
            'outFields': '*',
            'outSR': '4326',
            'f': 'geojson'
        }
        
        # Make the request with increased timeout
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()  # Raise an error for bad responses
        
        if debug:
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
        
        # Try to parse the GeoJSON
        counties_gdf = gpd.GeoDataFrame.from_features(response.json())
        
        # Create spatial index for counties
        spatial_idx = index.Index()
        for idx, county in counties_gdf.iterrows():
            spatial_idx.insert(idx, county.geometry.bounds)
        
        _COUNTY_SPATIAL_INDEX = spatial_idx
        _COUNTY_DATA = counties_gdf
        
        logger.debug(f"Successfully initialized county spatial index with {len(counties_gdf)} counties")
        return spatial_idx, counties_gdf
        
    except Exception as e:
        logger.error(f"Failed to initialize county spatial index: {e}")
        if debug:
            logger.exception("Detailed error:")
        
        if use_mock_on_failure:
            # Create a minimal mock index with some sample counties
            logger.warning("Using mock county data as fallback")
            
            # Create a simple mock dataset with a few counties
            mock_counties = {
                'COUNTY': ['001', '003', '005', '007', '009'],
                'STATE': ['06', '06', '06', '06', '06'],  # California
                'NAME': ['Alameda', 'Alpine', 'Amador', 'Butte', 'Calaveras'],
                'geometry': [
                    Polygon([(-122.3, 37.5), (-122.3, 37.9), (-121.8, 37.9), (-121.8, 37.5)]),  # Alameda
                    Polygon([(-120.0, 38.3), (-120.0, 38.8), (-119.5, 38.8), (-119.5, 38.3)]),  # Alpine
                    Polygon([(-121.0, 38.3), (-121.0, 38.7), (-120.5, 38.7), (-120.5, 38.3)]),  # Amador
                    Polygon([(-122.0, 39.3), (-122.0, 40.1), (-121.0, 40.1), (-121.0, 39.3)]),  # Butte
                    Polygon([(-121.0, 37.8), (-121.0, 38.5), (-120.3, 38.5), (-120.3, 37.8)])   # Calaveras
                ]
            }
            
            # Create a GeoDataFrame
            mock_gdf = gpd.GeoDataFrame(mock_counties, crs="EPSG:4326")
            
            # Create a mock spatial index
            mock_idx = index.Index()
            for idx, county in mock_gdf.iterrows():
                mock_idx.insert(idx, county.geometry.bounds)
            
            _COUNTY_SPATIAL_INDEX = mock_idx
            _COUNTY_DATA = mock_gdf
            
            logger.debug("Initialized mock county spatial index")
            return mock_idx, mock_gdf
        else:
            raise

def _create_mock_county_spatial_index():
    """
    Create a simple mock spatial index with a few sample counties.
    Used as a fallback when the API fails and for testing.
    
    Returns:
        Tuple containing (spatial_index, county_gdf)
    """
    global _COUNTY_SPATIAL_INDEX, _COUNTY_DATA
    
    logger.debug("Creating mock county spatial index")
    # Create a simple index with a few counties
    idx = index.Index()
    
    # Generate some mock county data
    counties = [
        # Illinois counties (Chicago area)
        {'STATE': '17', 'COUNTY': '031', 'NAME': 'Cook', 'bounds': [-88.2, 41.6, -87.5, 42.1]},
        {'STATE': '17', 'COUNTY': '043', 'NAME': 'DuPage', 'bounds': [-88.3, 41.7, -87.9, 42.0]},
        {'STATE': '17', 'COUNTY': '197', 'NAME': 'Will', 'bounds': [-88.2, 41.2, -87.5, 41.7]},
        
        # California counties (SF area)
        {'STATE': '06', 'COUNTY': '075', 'NAME': 'San Francisco', 'bounds': [-122.6, 37.7, -122.3, 37.9]},
        {'STATE': '06', 'COUNTY': '081', 'NAME': 'San Mateo', 'bounds': [-122.5, 37.1, -122.0, 37.7]},
        {'STATE': '06', 'COUNTY': '085', 'NAME': 'Santa Clara', 'bounds': [-122.2, 37.0, -121.2, 37.5]},
        
        # Some other states to cover the USA
        {'STATE': '36', 'COUNTY': '061', 'NAME': 'New York', 'bounds': [-74.1, 40.5, -73.7, 40.9]},
        {'STATE': '48', 'COUNTY': '201', 'NAME': 'Harris', 'bounds': [-95.8, 29.5, -94.9, 30.1]},
        {'STATE': '53', 'COUNTY': '033', 'NAME': 'King', 'bounds': [-122.5, 47.1, -121.2, 47.8]},
    ]
    
    # Create GeoDataFrame with mock counties
    geometries = []
    
    for i, county in enumerate(counties):
        minx, miny, maxx, maxy = county['bounds']
        # Add to spatial index
        idx.insert(i, (minx, miny, maxx, maxy), obj=(county['STATE'], county['COUNTY']))
        
        # Create polygon for the county
        geometry = Polygon([
            (minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)
        ])
        geometries.append(geometry)
    
    # Create GeoDataFrame
    county_gdf = gpd.GeoDataFrame(
        counties,
        geometry=geometries,
        crs="EPSG:4326"
    )
    
    _COUNTY_SPATIAL_INDEX = idx
    _COUNTY_DATA = county_gdf
    
    return idx, county_gdf


@lru_cache(maxsize=1024)
def get_county_fips_from_point(lat: float, lon: float, api_key: Optional[str] = None) -> Tuple[str, str]:
    """
    Determine the state and county FIPS codes for a given point.
    Uses a spatial index for fast lookups when available.
    
    Args:
        lat: Latitude of the point
        lon: Longitude of the point
        api_key: Census API key (optional)
        
    Returns:
        Tuple of (state_fips, county_fips)
    """
    # Try using our spatial index first - much faster than API calls
    try:
        idx, county_gdf = _init_county_spatial_index()
        point = gpd.points_from_xy([lon], [lat], crs="EPSG:4326")
        
        # Find potential counties using the spatial index (bounding box intersection)
        bbox_hits = list(idx.intersection((lon, lat, lon, lat)))
        
        if bbox_hits:
            # Get the geometries for the potential counties
            candidate_counties = county_gdf.iloc[bbox_hits]
            
            # Do precise point-in-polygon check
            for _, county in candidate_counties.iterrows():
                if county.geometry.contains(point[0]):
                    return county['STATE'], county['COUNTY']
                    
            # If point is not in any polygon (could be on water or boundary), 
            # use nearest county
            nearest_idx = candidate_counties.distance(point[0]).idxmin()
            nearest_county = county_gdf.loc[nearest_idx]
            return nearest_county['STATE'], nearest_county['COUNTY']
            
    except Exception as e:
        logger.warning(f"Spatial index lookup failed for ({lat}, {lon}): {e}")
    
    # Fall back to Census Geocoder API if spatial indexing fails
    url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {}).get("geographies", {}).get("Counties", [])
            
            if result and len(result) > 0:
                county_data = result[0]
                state_fips = county_data.get("STATE")
                county_fips = county_data.get("COUNTY")
                
                if state_fips and county_fips:
                    return state_fips, county_fips
    except Exception as e:
        logger.error(f"Error determining county from coordinates: {e}")
    
    # Fallback if everything fails
    logger.warning(f"Could not determine county for coordinates ({lat}, {lon})")
    return "", ""


# Cache neighbor relationships
@lru_cache(maxsize=256)
def get_neighboring_counties(state_fips: str, county_fips: str) -> List[Tuple[str, str]]:
    """
    Get neighboring counties for a given county.
    
    Args:
        state_fips: State FIPS code
        county_fips: County FIPS code
        
    Returns:
        List of tuples with (state_fips, county_fips) for neighboring counties
    """
    # For now we'll use a spatial approach by getting counties and finding those that share boundaries
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Cached neighbors file
    neighbors_cache_file = cache_dir / f"neighbors_{state_fips}_{county_fips}.json"
    if neighbors_cache_file.exists():
        try:
            with open(neighbors_cache_file, 'r') as f:
                neighbors_data = json.load(f)
                return [(str(n[0]), str(n[1])) for n in neighbors_data]
        except Exception as e:
            logger.warning(f"Could not load cached neighbors for {state_fips}_{county_fips}: {e}")
    
    # First, get all counties in the state
    state_counties_file = cache_dir / f"counties_{state_fips}.geojson"
    
    # Try to load from cache first
    state_counties = None
    if state_counties_file.exists():
        try:
            state_counties = gpd.read_file(
                state_counties_file,
                engine="pyogrio",
                use_arrow=USE_ARROW
            )
        except Exception as e:
            logger.warning(f"Could not load cached counties for state {state_fips}: {e}")
    
    # If not in cache, fetch from Census
    if state_counties is None:
        try:
            logger.debug(f"Fetching counties for state {state_fips} using TIGERweb REST API.")
            url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
            params = {
                'where': f"STATE='{state_fips}'",
                'outFields': 'STATE,COUNTY,NAME,GEOID,BASENAME',
                'returnGeometry': 'true',
                'f': 'geojson'
            }
            response = requests.get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if 'features' in data and data['features']:
                    state_counties = gpd.GeoDataFrame.from_features(
                        data['features'],
                        crs="EPSG:4326"
                    )
                    # Save to cache
                    state_counties.to_file(state_counties_file, driver="GeoJSON")
                else:
                    logger.warning(f"TIGERweb API returned no features for state {state_fips}.")
                    return []
            else:
                logger.warning(f"Failed to get counties for state {state_fips} via TIGERweb API (Status: {response.status_code}). Response: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching counties for state {state_fips}: {e}")
            return []
    
    if state_counties is None or state_counties.empty:
        logger.warning(f"No county data could be loaded or fetched for state {state_fips}.")
        return []

    # Ensure 'COUNTY' column exists and is of string type for matching
    if 'COUNTY' not in state_counties.columns:
        if 'COUNTYFP' in state_counties.columns:
            state_counties = state_counties.rename(columns={'COUNTYFP': 'COUNTY'})
        elif 'GEOID' in state_counties.columns and len(state_counties['GEOID'].iloc[0]) >= 5:
            state_counties['COUNTY'] = state_counties['GEOID'].str[2:5]
        else:
            logger.error(f"COUNTY column missing and could not be derived in fetched data for state {state_fips}.")
            return []
    state_counties['COUNTY'] = state_counties['COUNTY'].astype(str).str.zfill(3)
    
    # Now find the target county
    target_county_gdf = state_counties[state_counties['COUNTY'] == county_fips]
    if len(target_county_gdf) == 0:
        logger.warning(f"Could not find county {county_fips} in state {state_fips}")
        return []
    
    # Get neighboring counties within the same state
    neighbors = []
    try:
        # Use spatial join to find counties that touch the target county
        target_geom = target_county_gdf.iloc[0].geometry
        # Ensure geometries are valid
        if not target_geom.is_valid:
            logger.warning(f"Target county {county_fips} in state {state_fips} has invalid geometry. Attempting to buffer by 0.")
            target_geom = target_geom.buffer(0)
            if not target_geom.is_valid:
                logger.error(f"Target county {county_fips} in state {state_fips} geometry still invalid after buffer(0). Cannot find neighbors.")
                return []

        for idx, county_row in state_counties.iterrows():
            if county_row['COUNTY'] != county_fips:
                county_geom = county_row.geometry
                if not county_geom.is_valid:
                    logger.warning(f"Neighbor candidate county {county_row['BASENAME']} ({county_row['COUNTY']}) in state {state_fips} has invalid geometry. Attempting to buffer by 0.")
                    county_geom = county_geom.buffer(0)
                
                if county_geom.is_valid and county_geom.touches(target_geom):
                    neighbors.append((state_fips, county_row['COUNTY']))
                elif county_geom.is_valid and county_geom.intersects(target_geom) and not county_geom.overlaps(target_geom):
                    logger.debug(f"Adding county {county_row['BASENAME']} ({county_row['COUNTY']}) as neighbor to {county_fips} based on intersection (not just touches).")
                    neighbors.append((state_fips, county_row['COUNTY']))

    except Exception as e:
        logger.error(f"Error finding neighboring counties spatially for {state_fips}-{county_fips}: {e}")
    
    # Cache the neighbors for future use
    try:
        with open(neighbors_cache_file, 'w') as f:
            json.dump(neighbors, f)
    except Exception as e:
        logger.warning(f"Could not cache neighbors for {state_fips}_{county_fips}: {e}")
    
    return neighbors


def get_block_groups_for_county(
    state_fips: str, 
    county_fips: str,
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Fetch census block group boundaries for a specific county.
    
    Args:
        state_fips: State FIPS code
        county_fips: County FIPS code
        api_key: Census API key (optional)
        
    Returns:
        GeoDataFrame with block group boundaries
    """
    # Check for cached block group data
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    cache_file = cache_dir / f"block_groups_{state_fips}_{county_fips}.geojson"
    
    # Try to load from cache first
    if cache_file.exists():
        try:
            block_groups = gpd.read_file(
                cache_file,
                engine="pyogrio",
                use_arrow=USE_ARROW
            )
            tqdm.write(f"Loaded cached block groups for county {county_fips} in state {state_fips}")
            return block_groups
        except Exception as e:
            tqdm.write(f"Error loading cache: {e}")
    
    # If not in cache, fetch from Census API
    tqdm.write(f"Fetching block groups for county {county_fips} in state {state_fips}")
    
    # Use the Tracts_Blocks MapServer endpoint
    base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
    
    params = {
        'where': f"STATE='{state_fips}' AND COUNTY='{county_fips}'",
        'outFields': 'STATE,COUNTY,TRACT,BLKGRP,GEOID',
        'returnGeometry': 'true',
        'f': 'geojson'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=60)
        
        if response.status_code == 200:
            # Parse the GeoJSON response
            data = response.json()
            block_groups = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
            
            # Ensure proper formatting
            if 'STATE' not in block_groups.columns or not all(block_groups['STATE'] == state_fips):
                block_groups['STATE'] = state_fips
            if 'COUNTY' not in block_groups.columns or not all(block_groups['COUNTY'] == county_fips):
                block_groups['COUNTY'] = county_fips
            
            # Save to cache
            block_groups.to_file(cache_file, driver="GeoJSON", engine="pyogrio", use_arrow=USE_ARROW)
            
            tqdm.write(f"Retrieved {len(block_groups)} block groups for county {county_fips}")
            return block_groups
        else:
            raise ValueError(f"Census API returned status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching block groups for county {county_fips}: {e}")
        raise ValueError(f"Could not fetch block groups: {str(e)}")


def get_block_groups_for_counties(
    counties: List[Tuple[str, str]],
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Fetch block groups for multiple counties and combine them.
    
    Args:
        counties: List of (state_fips, county_fips) tuples
        api_key: Census API key (optional)
        
    Returns:
        Combined GeoDataFrame with block groups for all counties
    """
    all_block_groups = []
    
    # Use ThreadPoolExecutor to fetch block groups in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all county fetch tasks
        future_to_county = {
            executor.submit(get_block_groups_for_county, state_fips, county_fips, api_key): 
            (state_fips, county_fips) for state_fips, county_fips in counties
        }
        
        # Process results as they complete
        for future in get_progress_bar(
            concurrent.futures.as_completed(future_to_county), 
            total=len(counties),
            desc="Fetching block groups by county", 
            unit="county"
        ):
            state_fips, county_fips = future_to_county[future]
            try:
                county_block_groups = future.result()
                all_block_groups.append(county_block_groups)
            except Exception as e:
                tqdm.write(f"Error fetching block groups for county {county_fips} in state {state_fips}: {e}")
    
    if not all_block_groups:
        raise ValueError("No block group data could be retrieved")
    
    # Combine all county block groups
    return pd.concat(all_block_groups, ignore_index=True)


def _process_poi_batch(poi_batch, include_neighbors=True, api_key=None):
    """
    Process a batch of POIs to determine their counties.
    
    Args:
        poi_batch: List of POI dictionaries
        include_neighbors: Whether to include neighboring counties
        api_key: Census API key (optional)
        
    Returns:
        Set of (state_fips, county_fips) tuples
    """
    counties_set = set()
    
    for poi in poi_batch:
        lat = poi.get('lat')
        lon = poi.get('lon')
        
        if lat is None or lon is None:
            logger.warning(f"POI missing coordinates: {poi.get('id', 'unknown')}")
            continue
        
        # Get state and county FIPS for this POI
        state_fips, county_fips = get_county_fips_from_point(lat, lon, api_key)
        
        if state_fips and county_fips:
            counties_set.add((state_fips, county_fips))
            
            # Add neighboring counties if requested
            if include_neighbors:
                neighbors = get_neighboring_counties(state_fips, county_fips)
                counties_set.update(neighbors)
    
    return counties_set


def get_counties_from_pois(
    poi_data: Dict, 
    include_neighbors: bool = True,
    api_key: Optional[str] = None,
    max_workers: int = 8,
    batch_size: int = 100
) -> List[Tuple[str, str]]:
    """
    Determine counties for a list of POIs and optionally include neighboring counties.
    Uses parallel processing for faster results with large POI sets.
    
    Args:
        poi_data: Dictionary with 'pois' key containing list of POIs
        include_neighbors: Whether to include neighboring counties
        api_key: Census API key (optional)
        max_workers: Maximum number of worker processes/threads
        batch_size: Number of POIs to process in each batch
        
    Returns:
        List of (state_fips, county_fips) tuples for all relevant counties
    """
    # Initialize the spatial index if not already done
    try:
        _init_county_spatial_index()
        logger.debug("County spatial index initialized for efficient lookups")
    except Exception as e:
        logger.warning(f"Could not initialize county spatial index: {e}")
        logger.warning("Falling back to standard API lookups which may be slower")
    
    pois = poi_data.get('pois', [])
    if not pois:
        raise ValueError("No POIs found in input data")
    
    logger.debug(f"Processing {len(pois)} POIs to determine counties")
    start_time = time.time()
    
    # For very small POI sets, don't use multiprocessing overhead
    if len(pois) < 20:
        logger.debug("Small POI set detected, using single-threaded processing")
        counties_set = _process_poi_batch(pois, include_neighbors, api_key)
        return list(counties_set)
    
    # Split POIs into batches
    poi_batches = []
    for i in range(0, len(pois), batch_size):
        poi_batches.append(pois[i:i+batch_size])
    
    logger.debug(f"Split {len(pois)} POIs into {len(poi_batches)} batches of size ~{batch_size}")
    
    all_counties = set()
    
    # Use ThreadPoolExecutor for I/O bound operations like API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batches for processing
        future_to_batch = {
            executor.submit(_process_poi_batch, batch, include_neighbors, api_key): 
            i for i, batch in enumerate(poi_batches)
        }
        
        # Process results as they complete
        for future in get_progress_bar(
            concurrent.futures.as_completed(future_to_batch), 
            total=len(poi_batches),
            desc=f"Processing POI batches ({len(pois)} POIs in {len(poi_batches)} batches)", 
            unit="batch"
        ):
            batch_idx = future_to_batch[future]
            try:
                batch_counties = future.result()
                
                # Update the global set with counties from this batch
                all_counties.update(batch_counties)
                
                # Log progress periodically
                if batch_idx % 5 == 0 or batch_idx == len(poi_batches) - 1:
                    tqdm.write(f"Processed batch {batch_idx+1}/{len(poi_batches)} - Found {len(all_counties)} unique counties so far")
            except Exception as e:
                tqdm.write(f"Error processing batch {batch_idx}: {e}")
    
    elapsed = time.time() - start_time
    logger.debug(f"County determination complete. Found {len(all_counties)} counties in {elapsed:.2f} seconds")
    
    return list(all_counties)


def get_block_group_urls(state_fips: str, year: int = 2022) -> Dict[str, str]:
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