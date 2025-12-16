"""Input validation for SocialMapper API functions.

This module provides all validation functions for SocialMapper,
including coordinate validation, travel parameter validation,
and POI data validation.
"""

import logging

from shapely.geometry import Point

from .constants import (
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_TRAVEL_TIME,
    MIN_GEOJSON_COORDINATES,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    MIN_TRAVEL_TIME,
    VALID_EXPORT_FORMATS,
    VALID_REPORT_FORMATS,
    VALID_TRAVEL_MODES,
)
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


def _validate_coordinates_strict(lat: str | int | float, lon: str | int | float) -> tuple[float, float]:
    """Validate coordinate values (raises exception on invalid).

    Parameters
    ----------
    lat : str or int or float
        Latitude value.
    lon : str or int or float
        Longitude value.

    Returns
    -------
    tuple of (float, float)
        Tuple of validated (latitude, longitude) as floats.

    Raises
    ------
    ValidationError
        If coordinates are invalid.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Coordinates must be numeric: {e}") from None

    # Validate ranges
    if not MIN_LATITUDE <= lat <= MAX_LATITUDE:
        raise ValidationError(f"Invalid latitude: {lat}. Must be between -90 and 90")

    if not MIN_LONGITUDE <= lon <= MAX_LONGITUDE:
        raise ValidationError(f"Invalid longitude: {lon}. Must be between -180 and 180")

    return lat, lon


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude coordinates.

    Parameters
    ----------
    lat : float
        Latitude value to validate.
    lon : float
        Longitude value to validate.

    Returns
    -------
    bool
        True if coordinates are valid, False otherwise.
    """
    try:
        _validate_coordinates_strict(lat, lon)
        return True
    except ValidationError:
        return False


def validate_travel_time(travel_time: int) -> None:
    """
    Validate travel time parameter.

    Parameters
    ----------
    travel_time : int
        Travel time in minutes to validate.

    Raises
    ------
    ValueError
        If travel time is outside valid range.
    """
    if not MIN_TRAVEL_TIME <= travel_time <= MAX_TRAVEL_TIME:
        raise ValueError(
            f"Travel time must be between {MIN_TRAVEL_TIME} and {MAX_TRAVEL_TIME} minutes, "
            f"got {travel_time}"
        )


def validate_travel_mode(travel_mode: str) -> None:
    """
    Validate travel mode parameter.

    Parameters
    ----------
    travel_mode : str
        Travel mode to validate.

    Raises
    ------
    ValueError
        If travel mode is not supported.
    """
    if travel_mode not in VALID_TRAVEL_MODES:
        raise ValueError(
            f"Travel mode must be one of {VALID_TRAVEL_MODES}, "
            f"got '{travel_mode}'"
        )


def validate_export_format(export_format: str) -> None:
    """
    Validate map export format.

    Parameters
    ----------
    export_format : str
        Export format to validate.

    Raises
    ------
    ValueError
        If export format is not supported.
    """
    if export_format not in VALID_EXPORT_FORMATS:
        raise ValueError(
            f"Export format must be one of {VALID_EXPORT_FORMATS}, "
            f"got '{export_format}'"
        )


def validate_report_format(report_format: str) -> None:
    """
    Validate report format.

    Parameters
    ----------
    report_format : str
        Report format to validate.

    Raises
    ------
    ValueError
        If report format is not supported.
    """
    if report_format not in VALID_REPORT_FORMATS:
        raise ValueError(
            f"Report format must be one of {VALID_REPORT_FORMATS}, "
            f"got '{report_format}'"
        )


def validate_location_input(
    polygon=None,
    location=None
) -> None:
    """
    Validate mutually exclusive location parameters.

    Ensures exactly one of polygon or location is provided,
    preventing ambiguous input specifications.

    Parameters
    ----------
    polygon : dict, optional
        GeoJSON polygon specification. Default is None.
    location : tuple, optional
        Coordinate tuple specification. Default is None.

    Raises
    ------
    ValueError
        If neither parameter is provided or both are provided.

    Examples
    --------
    >>> validate_location_input(polygon={"type": "Polygon"})
    >>> # No exception raised

    >>> validate_location_input()  # doctest: +SKIP
    ValueError: Must provide either polygon or location
    """
    if polygon is None and location is None:
        raise ValueError("Must provide either polygon or location")

    if polygon is not None and location is not None:
        raise ValueError("Provide either polygon or location, not both")


def validate_poi_data(pois: list[dict]) -> list[dict]:
    """Validate and standardize POI coordinate data.

    Parameters
    ----------
    pois : list of dict
        List of POI dictionaries with coordinate fields.

    Returns
    -------
    list of dict
        List of valid POIs with standardized 'lat' and 'lon' fields.

    Raises
    ------
    ValueError
        If no valid POIs found.

    Examples
    --------
    >>> pois = [{"lat": 35.7796, "lon": -78.6382}]
    >>> validated = validate_poi_data(pois)
    >>> len(validated)
    1
    """
    valid_pois = []
    invalid_count = 0

    for poi in pois:
        try:
            lat, lon = None, None

            if "lat" in poi and "lon" in poi:
                lat, lon = poi["lat"], poi["lon"]
            elif "latitude" in poi and "longitude" in poi:
                lat, lon = poi["latitude"], poi["longitude"]
            elif "coordinates" in poi and isinstance(poi["coordinates"], list):
                if len(poi["coordinates"]) >= MIN_GEOJSON_COORDINATES:
                    lon, lat = poi["coordinates"][0], poi["coordinates"][1]
            elif "geometry" in poi and isinstance(poi["geometry"], dict):
                coords = poi["geometry"].get("coordinates", [])
                if isinstance(coords, list) and len(coords) >= MIN_GEOJSON_COORDINATES:
                    lon, lat = coords[0], coords[1]

            if lat is not None and lon is not None:
                lat, lon = _validate_coordinates_strict(lat, lon)
                valid_poi = poi.copy()
                valid_poi["lat"] = lat
                valid_poi["lon"] = lon
                valid_pois.append(valid_poi)
            else:
                invalid_count += 1

        except (ValidationError, ValueError, TypeError, KeyError, IndexError):
            invalid_count += 1
            continue

    if not valid_pois:
        raise ValueError(f"No valid POI coordinates found among {len(pois)} POIs")

    if invalid_count > 0:
        logger.warning(
            f"{invalid_count} out of {len(pois)} POIs have invalid coordinates"
        )

    return valid_pois


def prevalidate_for_pyproj(data: list[dict] | list[Point]) -> tuple[bool, list[str]]:
    """Pre-validate data before PyProj transformation.

    Parameters
    ----------
    data : list of dict or list of Point
        Input data to validate.

    Returns
    -------
    tuple of (bool, list of str)
        Tuple of (is_valid, list_of_errors).

    Examples
    --------
    >>> data = [{"lat": 35.7796, "lon": -78.6382}]
    >>> is_valid, errors = prevalidate_for_pyproj(data)
    >>> is_valid
    True
    """
    errors = []

    try:
        if not data:
            errors.append("Empty data provided")
            return False, errors

        if isinstance(data, list):
            if not isinstance(data[0], dict | Point):
                errors.append(f"Unsupported data type in list: {type(data[0])}")
                return False, errors

            if isinstance(data[0], dict):
                try:
                    validate_poi_data(data)
                except ValueError as e:
                    errors.append(str(e))
                    return False, errors
            elif isinstance(data[0], Point):
                for i, point in enumerate(data):
                    try:
                        _validate_coordinates_strict(point.y, point.x)
                    except ValidationError as e:
                        errors.append(f"Point {i}: {e}")

        else:
            errors.append(f"Unsupported data type: {type(data)}")
            return False, errors

        return len(errors) == 0, errors

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        errors.append(f"Validation error: {e}")
        return False, errors
