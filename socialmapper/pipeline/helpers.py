"""
Helper functions for the SocialMapper pipeline.

This module contains utility functions used across pipeline modules.
"""

import geopandas as gpd
from shapely.geometry import Point

from ..util import PathSecurityError, sanitize_path


def setup_directory(output_dir: str = "output") -> str:
    """
    Create a single output directory.

    Args:
        output_dir: Path to the output directory

    Returns:
        The output directory path

    Raises:
        PathSecurityError: If the path is invalid or unsafe
    """
    try:
        # Sanitize the output directory path
        safe_output_dir = sanitize_path(output_dir, allow_absolute=True)
        safe_output_dir.mkdir(parents=True, exist_ok=True)
        return str(safe_output_dir)
    except PathSecurityError as e:
        raise PathSecurityError(f"Invalid output directory: {e}")


def convert_poi_to_geodataframe(poi_data_list):
    """
    Convert a list of POI dictionaries to a GeoDataFrame.

    Args:
        poi_data_list: List of POI dictionaries

    Returns:
        GeoDataFrame containing POI data
    """
    if not poi_data_list:
        return None

    # Extract coordinates and create Point geometries
    geometries = []
    names = []
    ids = []
    types = []

    for poi in poi_data_list:
        if "lat" in poi and "lon" in poi:
            lat = poi["lat"]
            lon = poi["lon"]
        elif "geometry" in poi and "coordinates" in poi["geometry"]:
            # GeoJSON format
            coords = poi["geometry"]["coordinates"]
            lon, lat = coords[0], coords[1]
        else:
            continue

        geometries.append(Point(lon, lat))
        names.append(poi.get("name", poi.get("tags", {}).get("name", poi.get("id", "Unknown"))))
        ids.append(poi.get("id", ""))

        # Check for type directly in the POI data first, then fallback to tags
        if "type" in poi:
            types.append(poi.get("type"))
        else:
            types.append(poi.get("tags", {}).get("amenity", "Unknown"))

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(
        {"name": names, "id": ids, "type": types, "geometry": geometries}, crs="EPSG:4326"
    )  # WGS84 is standard for GPS coordinates

    return gdf
