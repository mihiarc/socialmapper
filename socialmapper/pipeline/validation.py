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
    from ..util.coordinate_validation import validate_poi_coordinates as validate_coords

    print("\n=== Validating POI Coordinates ===")

    # Extract POIs from poi_data for validation
    pois_to_validate = poi_data["pois"] if isinstance(poi_data, dict) else poi_data

    # Validate coordinates - now returns ValidationResult directly
    validation_result = validate_coords(pois_to_validate)

    if validation_result.total_valid == 0:
        raise ValueError(
            f"No valid POI coordinates found. All {validation_result.total_input} POIs failed validation."
        )

    if validation_result.total_invalid > 0:
        print(
            f"⚠️  Coordinate Validation Warning: {validation_result.total_invalid} out of {validation_result.total_input} POIs have invalid coordinates"
        )
        print(
            f"   Valid POIs: {validation_result.total_valid} ({validation_result.success_rate:.1f}%)"
        )

        # Log invalid POIs for user review
        invalid_tracker = get_global_tracker()
        for invalid_poi in validation_result.invalid_coordinates:
            invalid_tracker.add_invalid_point(
                invalid_poi["data"],
                f"Coordinate validation failed: {invalid_poi['error']}",
                "coordinate_validation",
            )
