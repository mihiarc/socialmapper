"""Export module for the SocialMapper pipeline.

This module handles exporting pipeline outputs to various formats.
"""

from pathlib import Path
from typing import Any

import geopandas as gpd

from ..io import IOManager


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
    travel_mode: str | None = None,
    io_manager: IOManager | None = None,
) -> dict[str, Any]:
    """
    Export pipeline outputs to various file formats.

    Handles exporting census data to CSV and isochrones to GeoParquet
    format, with support for centralized file tracking via IOManager.

    Parameters
    ----------
    census_data_gdf : gpd.GeoDataFrame
        GeoDataFrame containing census data with geographic units.
    poi_data : dict
        Dictionary containing POI information for metadata.
    isochrone_gdf : gpd.GeoDataFrame
        GeoDataFrame containing isochrone polygons.
    base_filename : str
        Base name for output files (without extension).
    travel_time : int
        Travel time in minutes used in analysis.
    directories : dict of str
        Dictionary mapping output types to directory paths.
        Keys may include 'base', 'census_data', 'isochrones'.
    export_csv : bool
        Whether to export census data to CSV format.
    census_codes : list of str
        List of census variable codes included in the data.
    geographic_level : str, optional
        Geographic unit type: 'block-group' or 'zcta', by default
        'block-group'.
    travel_mode : str or None, optional
        Travel mode used (walk, bike, drive), by default None.
    io_manager : IOManager or None, optional
        IOManager instance for centralized file tracking, by default None.

    Returns
    -------
    dict
        Dictionary containing paths to exported files with keys:
        - 'csv_data': Path to exported CSV file (if export_csv=True)
        - 'isochrone_data': Path to exported GeoParquet file (if applicable)

    Notes
    -----
    Files are named with the pattern:
    {base_filename}_{travel_time}min_{travel_mode}_{type}.{ext}

    Examples
    --------
    >>> result_files = export_pipeline_outputs(
    ...     census_data, poi_data, isochrones,
    ...     "portland_analysis", 15,
    ...     {"base": "./output"}, True, ["B01003_001E"]
    ... )
    >>> print(result_files["csv_data"])
    ./output/portland_analysis_15min_census_data.csv
    """
    from ..export import export_census_data_to_csv

    result_files = {}
    export_count = 0

    # Export census data to CSV (optional)
    if export_csv:
        print("\n=== Exporting Census Data to CSV ===")

        if io_manager:
            # Use IOManager for centralized file tracking
            # First prepare the data for CSV export
            from ..export.preparation import prepare_census_data

            # Prepare census data with POI information
            prepared_df = prepare_census_data(census_data_gdf, poi_data)

            output_file = io_manager.save_file(
                content=prepared_df,
                category="census_data",
                file_type="csv",
                base_name=base_filename,
                travel_mode=travel_mode,
                travel_time=travel_time,
                suffix="census_data",
                metadata={"census_codes": census_codes, "geographic_level": geographic_level},
            )
            result_files["csv_data"] = str(output_file.path)
            print(f"Exported census data to CSV: {output_file.path}")
        else:
            # Legacy path handling
            mode_suffix = f"_{travel_mode}" if travel_mode else ""
            csv_file = Path(directories.get("census_data", directories["base"])) / f"{base_filename}_{travel_time}min{mode_suffix}_census_data.csv"

            csv_output = export_census_data_to_csv(
                census_data=census_data_gdf,
                poi_data=poi_data,
                output_path=csv_file,
                base_filename=f"{base_filename}_{travel_time}min",
            )
            result_files["csv_data"] = csv_output
            print(f"Exported census data to CSV: {csv_output}")

        export_count += 1

    # Export isochrones to GeoParquet (optional)
    if "isochrones" in directories and isochrone_gdf is not None and not isochrone_gdf.empty:
        print("\n=== Exporting Isochrones to GeoParquet ===")

        try:
            if io_manager:
                # Use IOManager for centralized file tracking
                output_file = io_manager.save_file(
                    content=isochrone_gdf,
                    category="isochrones",
                    file_type="isochrone",
                    base_name=base_filename,
                    travel_mode=travel_mode,
                    travel_time=travel_time,
                    metadata={"poi_count": len(poi_data.get("pois", []))},
                )
                result_files["isochrone_data"] = str(output_file.path)
                print(f"Exported isochrones to GeoParquet: {output_file.path}")
            else:
                # Legacy path handling
                mode_suffix = f"_{travel_mode}" if travel_mode else ""
                isochrone_file = Path(directories["isochrones"]) / f"{base_filename}_{travel_time}min{mode_suffix}_isochrones.geoparquet"

                # Save isochrone GeoDataFrame to GeoParquet format
                isochrone_gdf.to_parquet(isochrone_file, compression="snappy", index=False)
                result_files["isochrone_data"] = isochrone_file
                print(f"Exported isochrones to GeoParquet: {isochrone_file}")

            export_count += 1
        except Exception as e:
            print(f"⚠️ Warning: Failed to export isochrones: {e}")

    print("\n=== Processing Complete ===")
    print("✅ Census data processed successfully!")
    if export_count > 0:
        print(
            f"📄 Exported {export_count} file(s) - all intermediate data processed in memory for efficiency"
        )

    return result_files
