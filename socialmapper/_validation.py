"""Simple coordinate validation for SocialMapper.

Replaces over-engineered coordinate_validation module with minimal validation.
"""

from typing import Any

from shapely.geometry import Point


def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """Validate latitude and longitude are in valid ranges.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees
    lon : float
        Longitude in decimal degrees

    Returns
    -------
    tuple[float, float]
        Validated (lat, lon) coordinates

    Raises
    ------
    ValueError
        If coordinates are out of valid range
    """
    if not isinstance(lat, (int, float)):
        raise ValueError(f"Latitude must be a number, got {type(lat)}")
    if not isinstance(lon, (int, float)):
        raise ValueError(f"Longitude must be a number, got {type(lon)}")

    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude {lat} must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude {lon} must be between -180 and 180")

    return float(lat), float(lon)


def validate_poi_coordinates(lat: float, lon: float) -> bool:
    """Validate POI coordinates (boolean return for backward compatibility).

    Parameters
    ----------
    lat : float
        Latitude value
    lon : float
        Longitude value

    Returns
    -------
    bool
        True if coordinates are valid, False otherwise
    """
    try:
        validate_coordinates(lat, lon)
        # Check for null island (0, 0) which is often an error
        if lat == 0 and lon == 0:
            return False
        return True
    except (TypeError, ValueError):
        return False


def validate_poi_data(pois: list[dict]) -> list[dict]:
    """Validate and standardize POI coordinate data.

    Parameters
    ----------
    pois : list[dict]
        List of POI dictionaries with coordinate fields

    Returns
    -------
    list[dict]
        List of valid POIs with standardized 'lat' and 'lon' fields

    Raises
    ------
    ValueError
        If no valid POIs found
    """
    valid_pois = []
    invalid_count = 0

    for poi in pois:
        try:
            # Try different coordinate formats
            lat, lon = None, None

            if "lat" in poi and "lon" in poi:
                lat, lon = poi["lat"], poi["lon"]
            elif "latitude" in poi and "longitude" in poi:
                lat, lon = poi["latitude"], poi["longitude"]
            elif "coordinates" in poi and isinstance(poi["coordinates"], list):
                if len(poi["coordinates"]) >= 2:
                    lon, lat = poi["coordinates"][0], poi["coordinates"][1]  # GeoJSON
            elif "geometry" in poi and isinstance(poi["geometry"], dict):
                coords = poi["geometry"].get("coordinates", [])
                if isinstance(coords, list) and len(coords) >= 2:
                    lon, lat = coords[0], coords[1]

            if lat is not None and lon is not None:
                # Validate coordinates
                lat, lon = validate_coordinates(lat, lon)
                # Standardize to lat/lon fields
                valid_poi = poi.copy()
                valid_poi["lat"] = lat
                valid_poi["lon"] = lon
                valid_pois.append(valid_poi)
            else:
                invalid_count += 1

        except (ValueError, TypeError, KeyError, IndexError):
            invalid_count += 1
            continue

    if not valid_pois:
        raise ValueError(f"No valid POI coordinates found among {len(pois)} POIs")

    if invalid_count > 0:
        print(
            f"⚠️  Warning: {invalid_count} out of {len(pois)} POIs have invalid coordinates"
        )

    return valid_pois


# Simple class to mimic the old Coordinate return type for backward compatibility
class ValidatedCoordinate:
    """Simple coordinate container for backward compatibility."""

    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def to_point(self) -> Point:
        """Convert to Shapely Point."""
        return Point(self.lon, self.lat)


def validate_coordinate_point(lat: float, lon: float, context: str = "unknown") -> ValidatedCoordinate | None:
    """Validate a single coordinate point.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees
    lon : float
        Longitude in decimal degrees
    context : str, optional
        Context for error reporting (unused, for backward compatibility)

    Returns
    -------
    ValidatedCoordinate or None
        ValidatedCoordinate if valid, None if invalid
    """
    try:
        lat, lon = validate_coordinates(lat, lon)
        return ValidatedCoordinate(lat, lon)
    except ValueError:
        return None


def prevalidate_for_pyproj(data: list[dict] | list[Point]) -> tuple[bool, list[str]]:
    """Pre-validate data before PyProj transformation.

    Parameters
    ----------
    data : list[dict] or list[Point]
        Input data to validate

    Returns
    -------
    tuple[bool, list[str]]
        (is_valid, list_of_errors)
    """
    errors = []

    try:
        if not data:
            errors.append("Empty data provided")
            return False, errors

        if isinstance(data, list):
            if isinstance(data[0], dict):
                # Validate POI data
                try:
                    validate_poi_data(data)
                except ValueError as e:
                    errors.append(str(e))
                    return False, errors
            elif isinstance(data[0], Point):
                # Validate Point objects
                for i, point in enumerate(data):
                    try:
                        validate_coordinates(point.y, point.x)
                    except ValueError as e:
                        errors.append(f"Point {i}: {e}")

        else:
            errors.append(f"Unsupported data type: {type(data)}")
            return False, errors

        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"Validation error: {e}")
        return False, errors