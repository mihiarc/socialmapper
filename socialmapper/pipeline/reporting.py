"""
Reporting module for the SocialMapper pipeline.

This module handles generation of final reports and summaries.
"""

from typing import Any, Dict

from ..progress import get_progress_tracker
from ..util.invalid_data_tracker import get_global_tracker


def generate_final_report(
    poi_data: Dict[str, Any],
    sampled_pois: bool,
    result_files: Dict[str, Any],
    base_filename: str,
    travel_time: int,
) -> Dict[str, Any]:
    """
    Generate final pipeline report and summary.

    Args:
        poi_data: POI data dictionary
        sampled_pois: Whether POIs were sampled
        result_files: Dictionary of result files
        base_filename: Base filename
        travel_time: Travel time in minutes

    Returns:
        Final result dictionary
    """
    # Print processing summary
    tracker = get_progress_tracker()
    tracker.print_summary()

    # Generate invalid data report if any issues were found
    invalid_tracker = get_global_tracker()
    invalid_summary = invalid_tracker.get_summary()
    if (
        invalid_summary["total_invalid_points"] > 0
        or invalid_summary["total_invalid_clusters"] > 0
        or invalid_summary["total_processing_errors"] > 0
    ):

        print("\n=== Invalid Data Report ===")
        invalid_tracker.print_summary()

        # Save detailed invalid data report
        try:
            report_files = invalid_tracker.save_invalid_data_report(
                filename_prefix=f"{base_filename}_{travel_time}min_invalid_data"
            )
            print(f"📋 Detailed invalid data report saved to: {', '.join(report_files)}")
            result_files["invalid_data_reports"] = report_files
        except Exception as e:
            print(f"⚠️  Warning: Could not save invalid data report: {e}")

    # Build final result dictionary
    result = {"poi_data": poi_data, "interactive_maps_available": True}  # Always true for Plotly

    # Add CSV path if applicable
    if "csv_data" in result_files:
        result["csv_data"] = result_files["csv_data"]

    # Add maps if applicable
    if "maps" in result_files:
        result["maps"] = result_files["maps"]
    else:
        result["maps"] = []

    # Add sampling information if POIs were sampled
    if sampled_pois:
        result["sampled_pois"] = True
        result["original_poi_count"] = poi_data.get("metadata", {}).get("original_count", 0)
        result["sampled_poi_count"] = len(poi_data.get("pois", []))

    # Add invalid data reports if any were generated
    if "invalid_data_reports" in result_files:
        result["invalid_data_reports"] = result_files["invalid_data_reports"]
        result["invalid_data_summary"] = invalid_summary

    return result
