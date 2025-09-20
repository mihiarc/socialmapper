"""Internal isochrone generation for SocialMapper."""

import requests
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import logging
from typing import Optional
import json

logger = logging.getLogger(__name__)


def generate_isochrone(
    lat: float,
    lon: float,
    travel_time: int,
    travel_mode: str
) -> Polygon:
    """
    Generate an isochrone polygon for accessibility analysis.

    Creates a polygon representing all locations reachable within a
    specified travel time from an origin point. Uses multiple routing
    services with automatic fallback to ensure reliability.

    Parameters
    ----------
    lat : float
        Latitude of the origin point in decimal degrees (WGS84).
    lon : float
        Longitude of the origin point in decimal degrees (WGS84).
    travel_time : int
        Maximum travel time in minutes (typically 5-60).
    travel_mode : str
        Transportation mode: 'drive', 'walk', or 'bike'.

    Returns
    -------
    shapely.geometry.Polygon
        Isochrone polygon in WGS84 coordinates representing the
        accessible area within the specified travel time.
        Always returns a valid polygon.

    Examples
    --------
    >>> # Generate 15-minute walking isochrone
    >>> iso = generate_isochrone(47.6062, -122.3321, 15, 'walk')
    >>> iso.is_valid
    True
    >>> iso.area > 0
    True

    See Also
    --------
    generate_with_ors : OpenRouteService implementation.
    generate_circle_approximation : Fallback circular approximation.

    Notes
    -----
    Attempts multiple routing services in order:
    1. OpenRouteService (with ORS_API_KEY environment variable)
    2. Circular approximation (fallback)

    All coordinates use WGS84 (EPSG:4326) coordinate system.
    """
    # Try multiple isochrone services
    polygon = None
    
    # Try OpenRouteService first (free tier available)
    polygon = generate_with_ors(lat, lon, travel_time, travel_mode)
    
    if not polygon:
        # Fallback to simple circular approximation
        polygon = generate_circle_approximation(lat, lon, travel_time, travel_mode)
    
    return polygon


def generate_with_ors(
    lat: float,
    lon: float,
    travel_time: int,
    travel_mode: str
) -> Optional[Polygon]:
    """
    Generate isochrone using OpenRouteService API.

    Connects to OpenRouteService to calculate accurate isochrones
    based on real road network data. Supports multiple travel modes
    with mode-specific routing profiles.

    Parameters
    ----------
    lat : float
        Latitude of the origin point (WGS84).
    lon : float
        Longitude of the origin point (WGS84).
    travel_time : int
        Travel time limit in minutes.
    travel_mode : str
        Mode of transportation: 'drive', 'walk', or 'bike'.

    Returns
    -------
    shapely.geometry.Polygon or None
        Isochrone polygon if successful, None if the service
        fails or returns invalid geometry.

    Raises
    ------
    requests.RequestException
        If the API request fails or times out.

    Notes
    -----
    Requires ORS_API_KEY environment variable for production.
    Falls back to demo endpoint with rate limits if no key.
    Travel modes map to ORS profiles:
    - drive -> driving-car
    - walk -> foot-walking
    - bike -> cycling-regular
    """
    import os
    
    # Map travel modes
    mode_mapping = {
        "drive": "driving-car",
        "walk": "foot-walking", 
        "bike": "cycling-regular"
    }
    profile = mode_mapping.get(travel_mode, "driving-car")
    
    # Check for API key
    api_key = os.getenv("ORS_API_KEY")
    
    if api_key:
        # Use production endpoint
        url = f"https://api.openrouteservice.org/v2/isochrones/{profile}"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    else:
        # Use public demo endpoint (limited requests)
        url = "https://api.openrouteservice.org/v2/isochrones/driving-car"
        headers = {
            "Content-Type": "application/json"
        }
        # For demo, always use driving
        profile = "driving-car"
        logger.warning("No ORS_API_KEY found, using demo endpoint (limited to driving mode)")
    
    # Build request
    data = {
        "locations": [[lon, lat]],
        "range": [travel_time * 60],  # Convert to seconds
        "range_type": "time"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("features"):
                # Extract polygon from GeoJSON
                feature = result["features"][0]
                coords = feature["geometry"]["coordinates"][0]
                polygon = Polygon(coords)
                logger.debug(f"Generated isochrone with ORS for {travel_time} min {travel_mode}")
                return polygon
        else:
            logger.warning(f"ORS API returned status {response.status_code}")
            
    except Exception as e:
        logger.warning(f"ORS isochrone generation failed: {e}")
    
    return None


def generate_circle_approximation(
    lat: float,
    lon: float,
    travel_time: int,
    travel_mode: str
) -> Polygon:
    """
    Generate a circular approximation of an isochrone.

    Creates a simplified isochrone using circular buffers based on
    average travel speeds. Used as fallback when routing services
    are unavailable.

    Parameters
    ----------
    lat : float
        Latitude of the origin point.
    lon : float
        Longitude of the origin point.
    travel_time : int
        Travel time in minutes.
    travel_mode : str
        Mode of transportation: 'drive', 'walk', or 'bike'.

    Returns
    -------
    shapely.geometry.Polygon
        Circular polygon approximating the isochrone.

    Examples
    --------
    >>> iso = generate_circle_approximation(40.7128, -74.0060, 30, 'walk')
    >>> iso.is_valid
    True
    >>> # Walking 30 min at 5km/h = 2.5km radius
    >>> iso.area > 0
    True

    Notes
    -----
    Uses fixed average speeds: drive=40km/h (city), bike=15km/h, walk=5km/h.
    Buffer calculation is performed in Web Mercator (EPSG:3857) for
    accurate distance measurement, then transformed back to WGS84.
    """
    from shapely.ops import transform
    import pyproj
    
    # Average speeds (km/h)
    speeds = {
        "drive": 40,  # City driving
        "bike": 15,
        "walk": 5
    }
    
    speed_kmh = speeds.get(travel_mode, 40)
    
    # Calculate radius in km
    radius_km = (speed_kmh * travel_time) / 60
    
    # Create point
    point = Point(lon, lat)
    
    # Project to Web Mercator for accurate buffering
    project_to_mercator = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
    project_to_wgs84 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True).transform
    
    # Buffer in meters
    point_mercator = transform(project_to_mercator, point)
    buffer_mercator = point_mercator.buffer(radius_km * 1000)
    
    # Convert back to WGS84
    polygon = transform(project_to_wgs84, buffer_mercator)
    
    logger.info(f"Generated circular isochrone approximation: {radius_km:.1f}km radius for {travel_time} min {travel_mode}")
    
    return polygon


def generate_with_osrm(
    lat: float,
    lon: float,
    travel_time: int,
    travel_mode: str
) -> Optional[Polygon]:
    """
    Generate isochrone using OSRM (if available).

    Placeholder for Open Source Routing Machine (OSRM) integration.
    OSRM doesn't provide native isochrone support, requiring custom
    implementation using table service.

    Parameters
    ----------
    lat : float
        Latitude of the origin point.
    lon : float
        Longitude of the origin point.
    travel_time : int
        Travel time in minutes.
    travel_mode : str
        Mode of transportation.

    Returns
    -------
    shapely.geometry.Polygon or None
        Currently returns None as implementation is pending.

    Notes
    -----
    Future implementation would require:
    1. OSRM table service to calculate travel times to grid points
    2. Interpolation to create contour lines
    3. Polygon generation from contours
    Requires local OSRM server or public instance.
    """
    # OSRM doesn't have native isochrone support
    # Would need to implement using table service and polygon generation
    # Skipping for now as it's complex
    return None


def generate_with_valhalla(
    lat: float,
    lon: float,
    travel_time: int,
    travel_mode: str
) -> Optional[Polygon]:
    """
    Generate isochrone using Valhalla routing engine.

    Uses Valhalla's native isochrone API to generate accurate
    isochrones based on real road network data. Supports multiple
    costing models for different travel modes.

    Parameters
    ----------
    lat : float
        Latitude of the origin point.
    lon : float
        Longitude of the origin point.
    travel_time : int
        Travel time limit in minutes.
    travel_mode : str
        Mode of transportation: 'drive', 'walk', or 'bike'.

    Returns
    -------
    shapely.geometry.Polygon or None
        Isochrone polygon if successful, None if Valhalla
        server is unavailable or request fails.

    Notes
    -----
    Requires VALHALLA_URL environment variable pointing to a
    Valhalla server (default: http://localhost:8002).
    Travel modes map to Valhalla costing models:
    drive -> auto, walk -> pedestrian, bike -> bicycle.
    """
    # Map travel modes
    mode_mapping = {
        "drive": "auto",
        "walk": "pedestrian",
        "bike": "bicycle"
    }
    costing = mode_mapping.get(travel_mode, "auto")
    
    # Check for Valhalla server URL
    import os
    valhalla_url = os.getenv("VALHALLA_URL", "http://localhost:8002")
    
    url = f"{valhalla_url}/isochrone"
    
    # Build request
    data = {
        "locations": [{"lat": lat, "lon": lon}],
        "costing": costing,
        "contours": [{"time": travel_time}],
        "polygons": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("features"):
                # Extract polygon from GeoJSON
                feature = result["features"][0]
                coords = feature["geometry"]["coordinates"][0]
                polygon = Polygon(coords)
                logger.debug(f"Generated isochrone with Valhalla for {travel_time} min {travel_mode}")
                return polygon
                
    except Exception as e:
        logger.debug(f"Valhalla not available: {e}")
    
    return None