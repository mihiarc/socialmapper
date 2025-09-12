"""Internal geocoding utilities for SocialMapper."""

import requests
from typing import Optional, Tuple, Dict
import logging
from time import sleep

logger = logging.getLogger(__name__)


def geocode_location(address: str) -> Optional[Tuple[float, float]]:
    """Geocode an address string to coordinates.
    
    Args:
        address: Address string like "City, State" or full address
    
    Returns:
        Tuple of (latitude, longitude) or None if failed
    """
    # Try Nominatim first (no API key needed)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "us"  # Focus on US addresses
    }
    headers = {
        "User-Agent": "SocialMapper/2.0 (https://github.com/socialmapper)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data:
            result = data[0]
            lat = float(result["lat"])
            lon = float(result["lon"])
            logger.debug(f"Geocoded '{address}' to ({lat}, {lon})")
            return (lat, lon)
            
    except Exception as e:
        logger.warning(f"Nominatim geocoding failed for '{address}': {e}")
    
    # Fallback to Census geocoder
    return geocode_with_census(address)


def geocode_with_census(address: str) -> Optional[Tuple[float, float]]:
    """Geocode using US Census geocoder as fallback.
    
    Args:
        address: Address string
    
    Returns:
        Tuple of (latitude, longitude) or None if failed
    """
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("result") and data["result"].get("addressMatches"):
            match = data["result"]["addressMatches"][0]
            coords = match["coordinates"]
            lat = coords["y"]
            lon = coords["x"]
            logger.debug(f"Census geocoded '{address}' to ({lat}, {lon})")
            return (lat, lon)
            
    except Exception as e:
        logger.error(f"Census geocoding failed for '{address}': {e}")
    
    return None


def get_census_geography(lat: float, lon: float) -> Optional[Dict[str, str]]:
    """Get census geographic identifiers for a point.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dict with state_fips, county_fips, tract, block_group, and geoid
    """
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "2020 Census Blocks",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("result") and data["result"].get("geographies"):
            blocks = data["result"]["geographies"].get("2020 Census Blocks", [])
            if blocks:
                block = blocks[0]
                
                # Extract components
                state_fips = block.get("STATE", "")
                county_fips = block.get("COUNTY", "")
                tract = block.get("TRACT", "")
                block_group = block.get("BLKGRP", "")
                
                # Create GEOID (state + county + tract + block group)
                geoid = f"{state_fips}{county_fips}{tract}{block_group}"
                
                return {
                    "state_fips": state_fips,
                    "county_fips": county_fips,
                    "tract": tract,
                    "block_group": block_group,
                    "geoid": geoid
                }
                
    except Exception as e:
        logger.error(f"Failed to get census geography for ({lat}, {lon}): {e}")
    
    return None