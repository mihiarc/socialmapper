"""Helper functions for SocialMapper API.

This module provides reusable utility functions for common operations
across the SocialMapper API, including coordinate resolution, geometry
calculations, and data format conversions.
"""

from typing import Tuple, Union, Dict, Any
from shapely.geometry import Point, shape
from shapely.ops import transform
import pyproj


def resolve_coordinates(location: Union[str, Tuple[float, float]]) -> Tuple[Tuple[float, float], str]:
    """Resolve location to coordinates and name."""
    from ._geocoding import geocode_location
    from .validators import validate_coordinates

    if isinstance(location, str):
        coords = geocode_location(location)
        if not coords:
            raise ValueError(f"Could not geocode location: {location}")
        lat, lon = coords
        location_name = location
    else:
        lat, lon = location
        if not validate_coordinates(lat, lon):
            raise ValueError(f"Invalid coordinates: {location}")
        location_name = f"{lat:.4f}, {lon:.4f}"

    return (lat, lon), location_name


def calculate_polygon_area(polygon) -> float:
    """Calculate area of polygon in square kilometers."""
    project = pyproj.Transformer.from_crs(
        'EPSG:4326', 'EPSG:3857', always_xy=True
    ).transform
    projected_polygon = transform(project, polygon)
    area_sq_m = projected_polygon.area
    return area_sq_m / 1_000_000


def create_circular_geometry(location: Tuple[float, float], radius_km: float):
    """Create circular geometry from point and radius."""
    lat, lon = location
    point = Point(lon, lat)

    project_to_mercator = pyproj.Transformer.from_crs(
        'EPSG:4326', 'EPSG:3857', always_xy=True
    ).transform
    project_to_wgs84 = pyproj.Transformer.from_crs(
        'EPSG:3857', 'EPSG:4326', always_xy=True
    ).transform

    point_mercator = transform(project_to_mercator, point)
    buffer_mercator = point_mercator.buffer(radius_km * 1000)
    return transform(project_to_wgs84, buffer_mercator)


def extract_geometry_from_geojson(polygon: Dict) -> Any:
    """Extract geometry from GeoJSON feature or geometry."""
    if "geometry" in polygon:
        return shape(polygon["geometry"])
    else:
        return shape(polygon)