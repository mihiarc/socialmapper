"""Input validation for SocialMapper API functions."""

from typing import Tuple, Union, List, Any


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude coordinates."""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def validate_travel_time(travel_time: int) -> None:
    """Validate travel time parameter."""
    if not 1 <= travel_time <= 120:
        raise ValueError(
            f"Travel time must be between 1 and 120 minutes, "
            f"got {travel_time}"
        )


def validate_travel_mode(travel_mode: str) -> None:
    """Validate travel mode parameter."""
    if travel_mode not in ["drive", "walk", "bike"]:
        raise ValueError(
            f"Travel mode must be 'drive', 'walk', or 'bike', "
            f"got {travel_mode}"
        )


def validate_export_format(export_format: str) -> None:
    """Validate map export format."""
    valid_formats = ["png", "pdf", "svg", "geojson", "shapefile"]
    if export_format not in valid_formats:
        raise ValueError(
            f"Export format must be one of {valid_formats}, "
            f"got '{export_format}'"
        )


def validate_location_input(
    polygon=None,
    location=None
) -> None:
    """Validate polygon/location input parameters."""
    if polygon is None and location is None:
        raise ValueError("Must provide either polygon or location")

    if polygon is not None and location is not None:
        raise ValueError("Provide either polygon or location, not both")