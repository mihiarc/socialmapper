"""
POI validation module for the SocialMapper pipeline.

This module handles validation of POI coordinates and data integrity,
ensuring that location data is valid before processing.
"""

from typing import Any

from ..util.invalid_data_tracker import get_global_tracker


def validate_poi_coordinates(poi_data: dict[str, Any]) -> None:
    """
    Validate POI coordinate data for geographic validity.

    Performs validation on POI latitude and longitude coordinates
    to ensure they fall within valid geographic ranges and are
    properly formatted.

    Parameters
    ----------
    poi_data : dict
        Dictionary containing POI information with 'pois' key
        containing list of POIs with lat/lon coordinates.

    Raises
    ------
    ValueError
        If no valid coordinates are found among the input POIs.

    Notes
    -----
    Invalid POIs are tracked globally for user review rather than
    causing immediate failure, allowing partial processing of valid data.

    Examples
    --------
    >>> poi_data = {"pois": [{"lat": 45.5, "lon": -122.6}]}
    >>> validate_poi_coordinates(poi_data)
    === Validating POI Coordinates ===

    >>> # Invalid coordinates raise error
    >>> bad_data = {"pois": [{"lat": 200, "lon": 500}]}
    >>> validate_poi_coordinates(bad_data)  # doctest: +SKIP
    ValueError: No valid POI coordinates found.
    """
    from .._validation import validate_poi_data

    print("\n=== Validating POI Coordinates ===")

    # Extract POIs from poi_data for validation
    pois_to_validate = poi_data["pois"] if isinstance(poi_data, dict) else poi_data

    # Validate coordinates
    try:
        valid_pois = validate_poi_data(pois_to_validate)

        # Update poi_data with validated POIs
        if isinstance(poi_data, dict):
            poi_data["pois"] = valid_pois

        invalid_count = len(pois_to_validate) - len(valid_pois)
        if invalid_count > 0:
            # Log invalid POIs for user review
            invalid_tracker = get_global_tracker()
            for poi in pois_to_validate:
                if poi not in valid_pois:
                    invalid_tracker.add_invalid_point(
                        poi,
                        "Coordinate validation failed",
                        "coordinate_validation",
                    )

    except ValueError as e:
        raise ValueError(f"No valid POI coordinates found: {e}")
