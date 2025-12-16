"""Helper functions for SocialMapper API.

This module provides reusable utility functions for common operations
across the SocialMapper API, including coordinate resolution, geometry
calculations, and data format conversions.
"""

from typing import Any

import pyproj
from shapely.geometry import Point, shape
from shapely.ops import transform

from .constants import (
    CONUS_MAX_LAT,
    CONUS_MAX_LON,
    CONUS_MIN_LAT,
    CONUS_MIN_LON,
    COORDINATE_PAIR_LENGTH,
    CRS_CONUS_ALBERS,
    CRS_GLOBAL_EQUAL_AREA,
    CRS_WGS84,
)


def is_conus(lat: float, lon: float) -> bool:
    """
    Check if coordinates are within the contiguous United States (CONUS).

    Used to determine the appropriate equal-area projection for
    accurate area and distance calculations.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees.
    lon : float
        Longitude in decimal degrees.

    Returns
    -------
    bool
        True if coordinates are within CONUS bounds.

    Examples
    --------
    >>> is_conus(45.5152, -122.6784)  # Portland, OR
    True
    >>> is_conus(21.3069, -157.8583)  # Honolulu, HI
    False
    >>> is_conus(51.5074, -0.1278)  # London, UK
    False
    """
    return (CONUS_MIN_LAT <= lat <= CONUS_MAX_LAT) and (CONUS_MIN_LON <= lon <= CONUS_MAX_LON)


def get_equal_area_crs(lat: float, lon: float) -> str:
    """
    Get the appropriate equal-area CRS for a location.

    Returns EPSG:5070 (NAD83 / Conus Albers) for locations within
    the contiguous United States, which provides ~0.1% accuracy.
    Returns EPSG:6933 (NSIDC EASE-Grid 2.0 Global) for all other
    locations, which provides ~1-2% accuracy globally.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees.
    lon : float
        Longitude in decimal degrees.

    Returns
    -------
    str
        EPSG code string for the appropriate CRS.

    Examples
    --------
    >>> get_equal_area_crs(45.5152, -122.6784)  # Portland, OR
    'EPSG:5070'
    >>> get_equal_area_crs(21.3069, -157.8583)  # Honolulu, HI
    'EPSG:6933'
    """
    if is_conus(lat, lon):
        return CRS_CONUS_ALBERS
    return CRS_GLOBAL_EQUAL_AREA


def get_equal_area_transformer(
    lat: float, lon: float, inverse: bool = False
) -> pyproj.Transformer:
    """
    Get a PyProj transformer for equal-area projections.

    Creates a transformer between WGS84 (EPSG:4326) and the
    appropriate equal-area CRS for the given location.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees (used to select CRS).
    lon : float
        Longitude in decimal degrees (used to select CRS).
    inverse : bool, optional
        If True, creates transformer from equal-area back to WGS84.
        Default is False (WGS84 to equal-area).

    Returns
    -------
    pyproj.Transformer
        Configured transformer for coordinate conversions.

    Examples
    --------
    >>> transformer = get_equal_area_transformer(45.5152, -122.6784)
    >>> x, y = transformer.transform(-122.6784, 45.5152)  # Note: x=lon, y=lat

    >>> inverse_transformer = get_equal_area_transformer(
    ...     45.5152, -122.6784, inverse=True
    ... )
    """
    target_crs = get_equal_area_crs(lat, lon)
    if inverse:
        return pyproj.Transformer.from_crs(target_crs, CRS_WGS84, always_xy=True)
    return pyproj.Transformer.from_crs(CRS_WGS84, target_crs, always_xy=True)


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
    elif isinstance(location, tuple | list) and len(location) == COORDINATE_PAIR_LENGTH:
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

    # Get transformer for appropriate equal-area CRS
    transformer = get_equal_area_transformer(lat, lon)
    projected_polygon = transform(transformer.transform, polygon)
    area_sq_m = projected_polygon.area
    return area_sq_m / 1_000_000


def create_circular_geometry(location: tuple[float, float], radius_km: float):
    """
    Create circular polygon from center point and radius.

    Generates a circular buffer around a point using equal-area
    projections for accurate distance-based buffers:
    - EPSG:5070 (NAD83 / Conus Albers) for contiguous US locations
    - EPSG:6933 (NSIDC EASE-Grid 2.0 Global) for other locations

    This replaces the previous Web Mercator (EPSG:3857) projection
    which distorted distances by ~40% at 45 degrees latitude.

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

    Notes
    -----
    For US Census applications, EPSG:5070 provides accurate distance
    calculations (~0.1% accuracy). Web Mercator (EPSG:3857) should
    never be used for distance-based operations as it exaggerates
    distances significantly at higher latitudes.
    """
    lat, lon = location
    point = Point(lon, lat)

    # Get transformers for appropriate equal-area CRS
    project_to_equal_area = get_equal_area_transformer(lat, lon)
    project_to_wgs84 = get_equal_area_transformer(lat, lon, inverse=True)

    point_projected = transform(project_to_equal_area.transform, point)
    buffer_projected = point_projected.buffer(radius_km * 1000)
    return transform(project_to_wgs84.transform, buffer_projected)


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
