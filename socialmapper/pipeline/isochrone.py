"""Isochrone generation module for the SocialMapper pipeline.

This module handles generation of travel time areas (isochrones) for POIs.
"""

from typing import Any

import geopandas as gpd

from ..isochrone import TravelMode


def generate_isochrones(
    poi_data: dict[str, Any],
    travel_time: int,
    state_abbreviations: list[str],
    travel_mode: TravelMode | None = None,
) -> gpd.GeoDataFrame:
    """Generate isochrones for the POI data.

    Args:
        poi_data: POI data dictionary
        travel_time: Travel time in minutes
        state_abbreviations: List of state abbreviations
        travel_mode: Mode of travel (walk, bike, drive)

    Returns:
        GeoDataFrame containing isochrones
    """
    from ..isochrone import create_isochrones_from_poi_list

    if travel_mode is None:
        travel_mode = TravelMode.DRIVE

    print(f"\n=== Generating {travel_time}-Minute Isochrones ({travel_mode.value} mode) ===")

    # Generate isochrones - the function handles its own progress tracking
    isochrone_result = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        combine_results=True,
        save_individual_files=False,  # We want the GeoDataFrame directly
        use_parquet=True,
        travel_mode=travel_mode,
    )

    # Handle different return types
    if isinstance(isochrone_result, gpd.GeoDataFrame):
        isochrone_gdf = isochrone_result
    elif isinstance(isochrone_result, str):
        # If it's a file path, load the GeoDataFrame from it
        try:
            isochrone_gdf = gpd.read_parquet(isochrone_result)
        except Exception as e:
            print(f"Warning: Error loading isochrones from parquet: {e}")
            # Alternative method using pyarrow
            try:
                import pyarrow.parquet as pq

                table = pq.read_table(isochrone_result)
                isochrone_gdf = gpd.GeoDataFrame.from_arrow(table)
            except Exception as e2:
                print(f"Critical error loading isochrones: {e2}")
                raise ValueError("Failed to load isochrone data") from e2
    elif isinstance(isochrone_result, list):
        # If it's a list of GeoDataFrames, combine them
        if all(isinstance(gdf, gpd.GeoDataFrame) for gdf in isochrone_result):
            import pandas as pd
            isochrone_gdf = gpd.GeoDataFrame(pd.concat(isochrone_result, ignore_index=True))
        else:
            raise ValueError(f"Unexpected list content in isochrone result: {type(isochrone_result[0]) if isochrone_result else 'empty list'}")
    else:
        raise ValueError(f"Unexpected return type from create_isochrones_from_poi_list: {type(isochrone_result)}")

    if isochrone_gdf is None or isochrone_gdf.empty:
        raise ValueError(
            "Failed to generate isochrones. This could be due to network issues or invalid POI locations."
        )

    print(f"Generated isochrones for {len(isochrone_gdf)} locations")
    return isochrone_gdf
