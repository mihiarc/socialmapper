"""
POI validation module for the SocialMapper pipeline.

This module handles validation of POI coordinates and data integrity.
"""

from typing import Any, Dict

from ..util.invalid_data_tracker import get_global_tracker


def validate_poi_coordinates(poi_data: Dict[str, Any]) -> None:
    """
    Validate POI coordinates using Pydantic validation.

    Args:
        poi_data: POI data dictionary

    Raises:
        ValueError: If no valid coordinates are found
    """
    from ..util.coordinate_validation import validate_poi_coordinates as validate_coords

    print("\n=== Validating POI Coordinates ===")

    # Extract POIs from poi_data for validation
    pois_to_validate = poi_data["pois"] if isinstance(poi_data, dict) else poi_data

    # Validate coordinates
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
