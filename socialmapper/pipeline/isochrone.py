"""
Isochrone generation module for the SocialMapper pipeline.

This module handles generation of travel time areas (isochrones) for POIs.
"""

from typing import Any, Dict, List

import geopandas as gpd


def generate_isochrones(
    poi_data: Dict[str, Any], travel_time: int, state_abbreviations: List[str]
) -> gpd.GeoDataFrame:
    """
    Generate isochrones for the POI data.

    Args:
        poi_data: POI data dictionary
        travel_time: Travel time in minutes
        state_abbreviations: List of state abbreviations

    Returns:
        GeoDataFrame containing isochrones
    """
    from ..isochrone import create_isochrones_from_poi_list

    print(f"\n=== Generating {travel_time}-Minute Isochrones ===")

    # Generate isochrones - the function handles its own progress tracking
    isochrone_gdf = create_isochrones_from_poi_list(
        poi_data=poi_data, travel_time_limit=travel_time, combine_results=True, use_parquet=True
    )

    # If the function returned a file path, load the GeoDataFrame from it
    if isinstance(isochrone_gdf, str):
        try:
            isochrone_gdf = gpd.read_parquet(isochrone_gdf)
        except Exception as e:
            print(f"Warning: Error loading isochrones from parquet: {e}")
            # Alternative method using pyarrow
            try:
                import pyarrow.parquet as pq

                table = pq.read_table(isochrone_gdf)
                isochrone_gdf = gpd.GeoDataFrame.from_arrow(table)
            except Exception as e2:
                print(f"Critical error loading isochrones: {e2}")
                raise ValueError("Failed to load isochrone data")

    if isochrone_gdf is None or isochrone_gdf.empty:
        raise ValueError(
            "Failed to generate isochrones. This could be due to network issues or invalid POI locations."
        )

    print(f"Generated isochrones for {len(isochrone_gdf)} locations")
    return isochrone_gdf
