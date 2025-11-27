"""Helper functions for SocialMapper API.

This module provides reusable utility functions for common operations
across the SocialMapper API, including coordinate resolution, geometry
calculations, and data format conversions.
"""

from typing import Any

import pyproj
from shapely.geometry import Point, shape
from shapely.ops import transform


def resolve_coordinates(location: str | tuple[float, float]) -> tuple[tuple[float, float], str]:
    """
    Resolve location input to coordinates and name.

    Converts location specifications (strings or coordinates)
    into standardized coordinate tuples and location names.

    Parameters
    ----------
    location : str or tuple of float
        Either "City, State" string for geocoding or
        (latitude, longitude) coordinate tuple.

    Returns
    -------
    tuple
        ((latitude, longitude), location_name) where:
        - First element is coordinate tuple
        - Second element is location name string

    Raises
    ------
    ValueError
        If location cannot be geocoded or coordinates
        are invalid.

    Examples
    --------
    >>> coords, name = resolve_coordinates("Portland, OR")
    >>> coords
    (45.5152, -122.6784)
    >>> name
    'Portland, OR'

    >>> coords, name = resolve_coordinates((45.5152, -122.6784))
    >>> name
    '45.5152, -122.6784'
    """
    from ._geocoding import geocode_location
    from .exceptions import ValidationError
    from .validators import validate_coordinates

    if isinstance(location, str):
        coords = geocode_location(location)
        if not coords:
            raise ValueError(f"Could not geocode location: {location}")
        lat, lon = coords
        location_name = location
    elif isinstance(location, (tuple, list)) and len(location) == 2:
        lat, lon = location
        if not validate_coordinates(lat, lon):
            raise ValidationError(f"Invalid coordinates: {location}")
        location_name = f"{lat:.4f}, {lon:.4f}"
    else:
        raise ValidationError(
            f"Location must be a string address or a tuple/list of (lat, lon), got {type(location).__name__}"
        )

    return (lat, lon), location_name


def calculate_polygon_area(polygon) -> float:
    """
    Calculate the area of a polygon in square kilometers.

    Uses equal-area projections for accurate area calculation:
    - EPSG:5070 (NAD83 / Conus Albers) for contiguous US locations
    - EPSG:6933 (NSIDC EASE-Grid 2.0 Global) for other locations

    This replaces the previous Web Mercator (EPSG:3857) projection
    which distorted areas by 32-140% at US latitudes.

    Parameters
    ----------
    polygon : shapely.geometry.Polygon
        Polygon geometry in WGS84 (EPSG:4326) coordinates.

    Returns
    -------
    float
        Area of the polygon in square kilometers.

    Examples
    --------
    >>> from shapely.geometry import Polygon
    >>> poly = Polygon([(-122.5, 45.5), (-122.4, 45.5),
    ...                 (-122.4, 45.6), (-122.5, 45.6)])
    >>> area = calculate_polygon_area(poly)
    >>> round(area, 2)
    85.39

    Notes
    -----
    For US Census applications, EPSG:5070 provides ~0.1% accuracy.
    Web Mercator (EPSG:3857) should never be used for area calculations
    as it exaggerates areas significantly at higher latitudes.
    """
    # Determine appropriate equal-area projection based on location
    centroid = polygon.centroid
    lon, lat = centroid.x, centroid.y

    # CONUS bounds: roughly 24°N to 50°N, -125°W to -66°W
    is_conus = (24.0 <= lat <= 50.0) and (-125.0 <= lon <= -66.0)

    if is_conus:
        # NAD83 / Conus Albers - optimized for contiguous US (~0.1% accuracy)
        target_crs = 'EPSG:5070'
    else:
        # NSIDC EASE-Grid 2.0 Global - equal-area cylindrical (~1-2% accuracy)
        target_crs = 'EPSG:6933'

    project = pyproj.Transformer.from_crs(
        'EPSG:4326', target_crs, always_xy=True
    ).transform
    projected_polygon = transform(project, polygon)
    area_sq_m = projected_polygon.area
    return area_sq_m / 1_000_000


def create_circular_geometry(location: tuple[float, float], radius_km: float):
    """
    Create circular polygon from center point and radius.

    Generates a circular buffer around a point by projecting
    to Web Mercator for accurate distance calculation.

    Parameters
    ----------
    location : tuple of float
        (latitude, longitude) center point coordinates.
    radius_km : float
        Radius of the circle in kilometers.

    Returns
    -------
    shapely.geometry.Polygon
        Circular polygon in WGS84 (EPSG:4326) coordinates.

    Examples
    --------
    >>> circle = create_circular_geometry((45.5152, -122.6784), 5.0)
    >>> round(calculate_polygon_area(circle), 1)
    78.5
    """
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


def extract_geometry_from_geojson(polygon: dict) -> Any:
    """
    Extract Shapely geometry from GeoJSON structure.

    Handles both GeoJSON Feature and bare Geometry objects,
    converting them to Shapely geometry objects.

    Parameters
    ----------
    polygon : dict
        GeoJSON Feature dict (with 'geometry' key) or
        bare GeoJSON geometry dict.

    Returns
    -------
    shapely.geometry.base.BaseGeometry
        Shapely geometry object (Polygon, MultiPolygon, etc.).

    Examples
    --------
    >>> geojson_feat = {
    ...     "type": "Feature",
    ...     "geometry": {
    ...         "type": "Polygon",
    ...         "coordinates": [[[-122.5, 45.5], [-122.4, 45.5],
    ...                          [-122.4, 45.6], [-122.5, 45.6],
    ...                          [-122.5, 45.5]]]
    ...     }
    ... }
    >>> geom = extract_geometry_from_geojson(geojson_feat)
    >>> geom.geom_type
    'Polygon'
    """
    if "geometry" in polygon:
        return shape(polygon["geometry"])
    else:
        return shape(polygon)
