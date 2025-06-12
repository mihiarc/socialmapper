"""
Export module for the SocialMapper pipeline.

This module handles exporting pipeline outputs to various formats.
"""

import os
from typing import Any, Dict, List

import geopandas as gpd

from ..progress import get_progress_bar
from .helpers import convert_poi_to_geodataframe


def export_pipeline_outputs(
    census_data_gdf: gpd.GeoDataFrame,
    poi_data: Dict[str, Any],
    isochrone_gdf: gpd.GeoDataFrame,
    base_filename: str,
    travel_time: int,
    directories: Dict[str, str],
    export_csv: bool,
    export_maps: bool,
    use_interactive_maps: bool,
    census_codes: List[str],
    geographic_level: str = "block-group",
) -> Dict[str, Any]:
    """
    Export pipeline outputs (CSV, maps, etc.).

    Args:
        census_data_gdf: Census data GeoDataFrame
        poi_data: POI data dictionary
        isochrone_gdf: Isochrone GeoDataFrame
        base_filename: Base filename for outputs
        travel_time: Travel time in minutes
        directories: Dictionary of output directories
        export_csv: Whether to export CSV
        export_maps: Whether to export maps
        use_interactive_maps: Whether to use interactive maps
        census_codes: List of census codes
        geographic_level: Geographic unit type ('block-group' or 'zcta')

    Returns:
        Dictionary of result files and metadata
    """
    from ..export import export_census_data_to_csv
    from ..util import census_code_to_name
    from ..visualization import generate_maps_for_variables

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

    # Generate maps (optional)
    if export_maps:
        print("\n=== Generating Maps ===")

        # Get visualization variables
        if (
            hasattr(census_data_gdf, "attrs")
            and "variables_for_visualization" in census_data_gdf.attrs
        ):
            visualization_variables = census_data_gdf.attrs["variables_for_visualization"]
        else:
            visualization_variables = [var for var in census_codes if var != "NAME"]

        # Transform census variable codes to mapped names for the map generator
        variable_mapping = {code: census_code_to_name(code) for code in census_codes}
        mapped_variables = []
        for var in get_progress_bar(visualization_variables, desc="Processing variables"):
            mapped_name = variable_mapping.get(var, var)
            mapped_variables.append(mapped_name)

        # Print what we're mapping in user-friendly language
        readable_var_names = [name.replace("_", " ").title() for name in mapped_variables]
        print(f"Creating maps for: {', '.join(readable_var_names)}")

        # Prepare POI data for the map generator
        poi_data_for_map = None
        if poi_data and "pois" in poi_data and len(poi_data["pois"]) > 0:
            # Always use just the first POI for mapping
            first_poi = poi_data["pois"][0]
            poi_data_for_map = convert_poi_to_geodataframe([first_poi])
            print(f"Note: Only mapping the first POI: {first_poi.get('name', 'Unknown')}")

        # Determine which map backend to use
        use_plotly_maps = use_interactive_maps

        # Generate maps for each census variable
        map_files = generate_maps_for_variables(
            census_data_path=census_data_gdf,
            variables=mapped_variables,
            output_dir=directories["base"],
            basename=f"{base_filename}_{travel_time}min",
            isochrone_path=isochrone_gdf,
            poi_df=poi_data_for_map,
            use_panels=False,
            use_plotly=use_plotly_maps,
            geographic_level=geographic_level,
        )
        result_files["maps"] = map_files

        if use_interactive_maps:
            print("Interactive maps displayed in Streamlit")
        else:
            print(f"Generated {len(map_files)} static maps")
        export_count += 1
    else:
        if not export_maps:
            print("\n=== Processing Complete ===")
            print("✅ Census data processed successfully!")
            print(
                "📄 CSV export is the primary output - all intermediate files processed in memory for efficiency"
            )
            if export_csv:
                print("💾 Use export_maps=True to generate visualization maps")

    return result_files
