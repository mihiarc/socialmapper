"""Isochrone generation module for the SocialMapper pipeline.

This module handles generation of travel time areas (isochrones) for POIs.
"""

from typing import Any

import geopandas as gpd

from ..exceptions import (
    DataProcessingError,
    IsochroneGenerationError,
    NetworkAnalysisError,
)
from ..isochrone import TravelMode
from ..util.error_handling import error_context


def generate_isochrones(
    poi_data: dict[str, Any],
    travel_time: int,
    state_abbreviations: list[str],
    travel_mode: TravelMode | None = None,
) -> gpd.GeoDataFrame:
    """
    Generate travel-time polygons (isochrones) for POI locations.

    Creates isochrones representing areas reachable within a specified
    travel time from points of interest using the specified travel mode.

    Parameters
    ----------
    poi_data : dict
        Dictionary containing POI information with 'pois' key containing
        list of POIs with location data.
    travel_time : int
        Travel time limit in minutes for generating isochrones.
    state_abbreviations : list of str
        List of state abbreviations for network data download.
    travel_mode : TravelMode or None, optional
        Mode of travel (WALK, BIKE, or DRIVE). If None, defaults to DRIVE.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame containing isochrone polygons with geometry and
        attributes for each POI location.

    Raises
    ------
    NetworkAnalysisError
        If the network data is insufficient for the specified travel mode.
    IsochroneGenerationError
        If isochrone generation fails for any reason.
    DataProcessingError
        If the result format is unexpected or loading from file fails.

    Examples
    --------
    >>> poi_data = {"pois": [{"lat": 45.5, "lon": -122.6, "name": "Portland"}]}
    >>> isochrones = generate_isochrones(poi_data, 15, ["OR"])
    >>> print(f"Generated {len(isochrones)} isochrones")
    Generated 1 isochrones

    >>> # Using walk mode
    >>> isochrones = generate_isochrones(
    ...     poi_data, 10, ["OR"], travel_mode=TravelMode.WALK
    ... )
    """
    from ..isochrone import create_isochrones_from_poi_list

    if travel_mode is None:
        travel_mode = TravelMode.DRIVE

    print(f"\n=== Generating {travel_time}-Minute Isochrones ({travel_mode.value} mode) ===")

    # Generate isochrones - the function handles its own progress tracking
    try:
        with error_context("isochrone generation", travel_time=travel_time, mode=travel_mode.value):
            isochrone_result = create_isochrones_from_poi_list(
                poi_data=poi_data,
                travel_time_limit=travel_time,
                combine_results=True,
                save_individual_files=False,  # We want the GeoDataFrame directly
                use_parquet=True,
                travel_mode=travel_mode,
            )
    except Exception as e:
        # Check for common network-related errors
        error_msg = str(e).lower()
        if "network" in error_msg or "graph" in error_msg:
            raise NetworkAnalysisError(
                f"Failed to analyze {travel_mode.value} network",
                network_type=travel_mode.value,
                cause=e,
            ).add_suggestion("The area may lack sufficient road/path data for this travel mode")
        else:
            raise IsochroneGenerationError(travel_mode=travel_mode.value, cause=e)

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
                raise DataProcessingError(
                    "Failed to load isochrone data from file", file_path=isochrone_result, cause=e2
                ).with_operation("isochrone_file_loading")
    elif isinstance(isochrone_result, list):
        # If it's a list of GeoDataFrames, combine them
        if all(isinstance(gdf, gpd.GeoDataFrame) for gdf in isochrone_result):
            import pandas as pd

            isochrone_gdf = gpd.GeoDataFrame(pd.concat(isochrone_result, ignore_index=True))
        else:
            raise DataProcessingError(
                "Unexpected isochrone result format",
                result_type="list",
                content_type=type(isochrone_result[0]).__name__ if isochrone_result else "empty",
            ).with_operation("isochrone_processing")
    else:
        raise DataProcessingError(
            "Unexpected isochrone result type", result_type=type(isochrone_result).__name__
        ).with_operation("isochrone_processing")

    if isochrone_gdf is None or isochrone_gdf.empty:
        raise (
            IsochroneGenerationError(travel_mode=travel_mode.value)
            .add_suggestion("Check that POI locations are valid and accessible")
            .add_suggestion("Verify internet connection for downloading network data")
        )

    print(f"Generated isochrones for {len(isochrone_gdf)} locations")
    return isochrone_gdf
