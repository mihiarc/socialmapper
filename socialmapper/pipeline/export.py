"""Export module for the SocialMapper pipeline.

This module handles exporting pipeline outputs to various formats.
"""

import os
from typing import Any

import geopandas as gpd


def export_pipeline_outputs(
    census_data_gdf: gpd.GeoDataFrame,
    poi_data: dict[str, Any],
    isochrone_gdf: gpd.GeoDataFrame,
    base_filename: str,
    travel_time: int,
    directories: dict[str, str],
    export_csv: bool,
    census_codes: list[str],
    geographic_level: str = "block-group",
) -> dict[str, Any]:
    """Export pipeline outputs (CSV, maps, etc.).

    Args:
        census_data_gdf: Census data GeoDataFrame
        poi_data: POI data dictionary
        isochrone_gdf: Isochrone GeoDataFrame
        base_filename: Base filename for outputs
        travel_time: Travel time in minutes
        directories: Dictionary of output directories
        export_csv: Whether to export CSV
        census_codes: List of census codes
        geographic_level: Geographic unit type ('block-group' or 'zcta')

    Returns:
        Dictionary of result files and metadata
    """
    from ..export import export_census_data_to_csv

    result_files = {}
    export_count = 0

    # Export census data to CSV (optional)
    if export_csv:
        print("\n=== Exporting Census Data to CSV ===")

        csv_file = os.path.join(
            directories["csv"], f"{base_filename}_{travel_time}min_census_data.csv"
        )

        csv_output = export_census_data_to_csv(
            census_data=census_data_gdf,
            poi_data=poi_data,
            output_path=csv_file,
            base_filename=f"{base_filename}_{travel_time}min",
        )
        result_files["csv_data"] = csv_output
        print(f"Exported census data to CSV: {csv_output}")
        export_count += 1

    print("\n=== Processing Complete ===")
    print("✅ Census data processed successfully!")
    print(
        "📄 CSV export is the primary output - all intermediate files processed in memory for efficiency"
    )

    return result_files
