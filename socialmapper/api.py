"""SocialMapper: Simple, direct API for spatial analysis.

Five core functions for all your spatial analysis needs.
"""

import os
from typing import Optional, Union, List, Dict, Any, Tuple
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, shape
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)


def create_isochrone(
    location: Union[str, Tuple[float, float]], 
    travel_time: int = 15, 
    travel_mode: str = "drive"
) -> Dict[str, Any]:
    """Create a travel-time polygon from a location.
    
    Args:
        location: Either "City, State" string or (latitude, longitude) tuple
        travel_time: Travel time in minutes (1-120)
        travel_mode: Mode of travel ("drive", "walk", or "bike")
    
    Returns:
        GeoJSON-like dict with geometry and properties:
        {
            "type": "Feature",
            "geometry": {...},  # GeoJSON polygon
            "properties": {
                "location": "...",
                "travel_time": 15,
                "travel_mode": "drive",
                "area_sq_km": 25.3
            }
        }
    
    Example:
        >>> iso = create_isochrone("Portland, OR", travel_time=20)
        >>> iso = create_isochrone((45.5152, -122.6784), travel_time=15)
    """
    # Import internal modules
    from ._geocoding import geocode_location
    from ._isochrone import generate_isochrone
    
    # Validate inputs
    if not 1 <= travel_time <= 120:
        raise ValueError(f"Travel time must be between 1 and 120 minutes, got {travel_time}")
    
    if travel_mode not in ["drive", "walk", "bike"]:
        raise ValueError(f"Travel mode must be 'drive', 'walk', or 'bike', got {travel_mode}")
    
    # Get coordinates
    if isinstance(location, str):
        coords = geocode_location(location)
        if not coords:
            raise ValueError(f"Could not geocode location: {location}")
        lat, lon = coords
        location_name = location
    else:
        lat, lon = location
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Invalid coordinates: {location}")
        location_name = f"{lat:.4f}, {lon:.4f}"
    
    # Generate isochrone
    polygon = generate_isochrone(lat, lon, travel_time, travel_mode)
    
    # Calculate area
    from shapely.ops import transform
    import pyproj
    
    # Project to equal area projection for accurate area calculation
    project = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
    projected_polygon = transform(project, polygon)
    area_sq_m = projected_polygon.area
    area_sq_km = area_sq_m / 1_000_000
    
    # Return GeoJSON
    return {
        "type": "Feature",
        "geometry": polygon.__geo_interface__,
        "properties": {
            "location": location_name,
            "travel_time": travel_time,
            "travel_mode": travel_mode,
            "area_sq_km": area_sq_km
        }
    }


def get_census_blocks(
    polygon: Optional[Dict] = None,
    location: Optional[Tuple[float, float]] = None,
    radius_km: float = 5
) -> List[Dict[str, Any]]:
    """Get census block groups for an area.
    
    Args:
        polygon: GeoJSON dict from create_isochrone() or any GeoJSON polygon
        location: (latitude, longitude) tuple for point queries
        radius_km: Radius in kilometers if using location (default: 5)
    
    Returns:
        List of dicts with census block group information:
        [
            {
                "geoid": "060750201001",
                "state_fips": "06",
                "county_fips": "075",
                "tract": "020100",
                "block_group": "1",
                "geometry": {...},  # GeoJSON polygon
                "area_sq_km": 1.2
            },
            ...
        ]
    
    Example:
        >>> # From isochrone
        >>> iso = create_isochrone("San Francisco, CA", travel_time=15)
        >>> blocks = get_census_blocks(polygon=iso)
        
        >>> # From point and radius
        >>> blocks = get_census_blocks(location=(37.7749, -122.4194), radius_km=3)
    """
    from ._census import fetch_block_groups_for_area
    
    # Validate inputs
    if polygon is None and location is None:
        raise ValueError("Must provide either polygon or location")
    
    if polygon is not None and location is not None:
        raise ValueError("Provide either polygon or location, not both")
    
    # Get geometry
    if polygon:
        # Extract geometry from GeoJSON
        if "geometry" in polygon:
            geom = shape(polygon["geometry"])
        else:
            geom = shape(polygon)
    else:
        # Create circle from point
        from shapely.geometry import Point
        from shapely.ops import transform
        import pyproj
        
        lat, lon = location
        
        # Create point and buffer in meters
        point = Point(lon, lat)
        
        # Project to Web Mercator for accurate buffering
        project_to_mercator = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
        project_to_wgs84 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True).transform
        
        point_mercator = transform(project_to_mercator, point)
        buffer_mercator = point_mercator.buffer(radius_km * 1000)
        geom = transform(project_to_wgs84, buffer_mercator)
    
    # Fetch block groups
    return fetch_block_groups_for_area(geom)


def get_census_data(
    location: Union[Dict, List[str], Tuple[float, float]],
    variables: List[str],
    year: int = 2023
) -> Dict[str, Any]:
    """Get census data for location(s).
    
    Args:
        location: Can be:
            - GeoJSON dict (from create_isochrone or get_census_blocks)
            - List of GEOID strings ["060750201001", ...]
            - (latitude, longitude) tuple for single point
        variables: List of variable names or codes:
            - Names: ["population", "median_income", "median_age"]
            - Codes: ["B01003_001E", "B19013_001E", "B01002_001E"]
        year: Census year (default: 2023 for most recent ACS 5-year)
    
    Returns:
        Dict with census data:
        - For GeoJSON/GEOIDs: {"geoid": {"variable": value, ...}, ...}
        - For point: {"variable": value, ...}
    
    Example:
        >>> # From isochrone
        >>> iso = create_isochrone("Denver, CO", travel_time=20)
        >>> data = get_census_data(iso, ["population", "median_income"])
        
        >>> # From GEOIDs
        >>> data = get_census_data(["060750201001"], ["B01003_001E"])
        
        >>> # From point
        >>> data = get_census_data((39.7392, -104.9903), ["population"])
    """
    from ._census import fetch_census_data, normalize_variable_names
    
    # Normalize variables
    var_codes = normalize_variable_names(variables)
    
    # Determine GEOIDs based on location type
    if isinstance(location, dict):
        # GeoJSON - get census blocks first
        blocks = get_census_blocks(polygon=location)
        geoids = [b["geoid"] for b in blocks]
        
    elif isinstance(location, list):
        # List of GEOIDs
        geoids = location
        
    elif isinstance(location, tuple):
        # Point - get single block group
        from ._geocoding import get_census_geography
        geo_info = get_census_geography(location[0], location[1])
        if not geo_info:
            raise ValueError(f"Could not identify census geography for point: {location}")
        geoids = [geo_info["geoid"]]
    else:
        raise ValueError("Location must be GeoJSON dict, list of GEOIDs, or (lat, lon) tuple")
    
    # Fetch census data
    data = fetch_census_data(geoids, var_codes, year)
    
    # Format return based on input type
    if isinstance(location, tuple):
        # Return single dict for point query
        return data.get(geoids[0], {}) if geoids else {}
    else:
        # Return dict keyed by GEOID
        return data


def create_map(
    data: Union[List[Dict], pd.DataFrame, gpd.GeoDataFrame],
    column: str,
    title: Optional[str] = None,
    save_path: Optional[str] = None
) -> Optional[bytes]:
    """Create a choropleth map visualization.
    
    Args:
        data: Data to visualize, can be:
            - List of dicts with 'geometry' and data columns
            - pandas DataFrame with geometry column
            - GeoDataFrame
        column: Name of the data column to visualize
        title: Optional map title
        save_path: Optional path to save map (e.g., "map.png")
    
    Returns:
        PNG image as bytes if save_path is None, otherwise None
    
    Example:
        >>> # Get data
        >>> blocks = get_census_blocks(location=(40.7128, -74.0060), radius_km=2)
        >>> census = get_census_data([b["geoid"] for b in blocks], ["population"])
        
        >>> # Add census data to blocks
        >>> for block in blocks:
        >>>     block["population"] = census.get(block["geoid"], {}).get("population", 0)
        
        >>> # Create map
        >>> create_map(blocks, "population", title="Population by Block Group")
        
        >>> # Save to file
        >>> create_map(blocks, "population", save_path="population_map.png")
    """
    from ._visualization import generate_choropleth_map
    
    # Convert to GeoDataFrame if needed
    if isinstance(data, list):
        # List of dicts
        import geopandas as gpd
        from shapely.geometry import shape
        
        geometries = []
        attributes = []
        
        for item in data:
            if "geometry" not in item:
                raise ValueError("Each item must have a 'geometry' field")
            
            geom = shape(item["geometry"]) if isinstance(item["geometry"], dict) else item["geometry"]
            geometries.append(geom)
            
            # Copy attributes except geometry
            attrs = {k: v for k, v in item.items() if k != "geometry"}
            attributes.append(attrs)
        
        gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs="EPSG:4326")
        
    elif isinstance(data, pd.DataFrame):
        # Convert DataFrame to GeoDataFrame
        if "geometry" not in data.columns:
            raise ValueError("DataFrame must have a 'geometry' column")
        gdf = gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:4326")
        
    elif isinstance(data, gpd.GeoDataFrame):
        gdf = data
        
    else:
        raise ValueError("Data must be a list of dicts, DataFrame, or GeoDataFrame")
    
    # Check column exists
    if column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    # Generate map
    return generate_choropleth_map(gdf, column, title, save_path)


def get_poi(
    location: Union[str, Tuple[float, float]],
    categories: Optional[List[str]] = None,
    travel_time: Optional[int] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get points of interest near a location.
    
    Args:
        location: Either "City, State" string or (latitude, longitude) tuple
        categories: Optional list of POI categories to filter:
            - "restaurant", "cafe", "bar", "fast_food"
            - "school", "university", "library"
            - "hospital", "clinic", "pharmacy"
            - "park", "playground", "sports"
            - "grocery", "supermarket", "convenience"
            - "bank", "atm"
            - None for all categories
        travel_time: Optional travel time in minutes to create boundary (uses driving)
            - If provided, finds POIs within travel-time isochrone
            - If None, finds POIs within 5km radius
        limit: Maximum number of POIs to return (default: 100)
    
    Returns:
        List of POI dicts sorted by distance:
        [
            {
                "name": "Golden Gate Park",
                "category": "park",
                "lat": 37.7694,
                "lon": -122.4862,
                "distance_km": 1.2,
                "address": "...",  # if available
                "tags": {...}  # additional OSM tags
            },
            ...
        ]
    
    Example:
        >>> # POIs within 5km of location
        >>> pois = get_poi("Seattle, WA", categories=["restaurant", "cafe"])
        
        >>> # POIs within 15-minute drive
        >>> pois = get_poi((47.6062, -122.3321), travel_time=15)
        
        >>> # All POIs near coordinates
        >>> pois = get_poi((37.7749, -122.4194), limit=50)
    """
    from ._geocoding import geocode_location
    from ._osm import query_pois
    
    # Get coordinates
    if isinstance(location, str):
        coords = geocode_location(location)
        if not coords:
            raise ValueError(f"Could not geocode location: {location}")
        lat, lon = coords
    else:
        lat, lon = location
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Invalid coordinates: {location}")
    
    # Determine search area
    if travel_time:
        # Create isochrone boundary
        iso = create_isochrone((lat, lon), travel_time=travel_time, travel_mode="drive")
        search_area = shape(iso["geometry"])
    else:
        # Use 5km radius
        from shapely.geometry import Point
        from shapely.ops import transform
        import pyproj
        
        point = Point(lon, lat)
        
        # Project to Web Mercator for accurate buffering
        project_to_mercator = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
        project_to_wgs84 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True).transform
        
        point_mercator = transform(project_to_mercator, point)
        buffer_mercator = point_mercator.buffer(5000)  # 5km
        search_area = transform(project_to_wgs84, buffer_mercator)
    
    # Query POIs
    pois = query_pois(search_area, categories)
    
    # Calculate distances from origin
    origin = (lat, lon)
    for poi in pois:
        poi_coords = (poi["lat"], poi["lon"])
        poi["distance_km"] = geodesic(origin, poi_coords).kilometers
    
    # Sort by distance and limit
    pois.sort(key=lambda x: x["distance_km"])
    
    return pois[:limit]