"""Internal validation utilities for SocialMapper."""

import logging

logger = logging.getLogger(__name__)


def validate_poi_coordinates_batch(lat: float, lon: float) -> bool:
    """Validate POI coordinates.

    Args:
        lat: Latitude value
        lon: Longitude value

    Returns:
        True if coordinates are valid, False otherwise
    """
    try:
        # Check if coordinates are within valid ranges
        if not -90 <= lat <= 90:
            return False
        if not -180 <= lon <= 180:
            return False

        # Check for null island (0, 0) which is often an error
        if lat == 0 and lon == 0:
            logger.debug("Coordinates at null island (0, 0) - likely invalid")
            return False

        return True
    except (TypeError, ValueError):
        return False