"""
Helper functions for the SocialMapper pipeline.

This module contains utility functions used across pipeline modules
for directory management and data conversion operations.
"""

import geopandas as gpd
from shapely.geometry import Point

from ..util import PathSecurityError, sanitize_path


def setup_directory(output_dir: str = "output") -> str:
    """
    Create and validate an output directory.

    Ensures the directory path is safe and creates it if it doesn't
    exist, with support for nested directory structures.

    Parameters
    ----------
    output_dir : str, optional
        Path to the output directory, by default "output".

    Returns
    -------
    str
        The sanitized output directory path.

    Raises
    ------
    PathSecurityError
        If the path contains unsafe components (e.g., path traversal
        attempts) or violates security constraints.

    Examples
    --------
    >>> output_path = setup_directory("results/analysis")
    >>> print(output_path)
    results/analysis

    >>> # Unsafe paths are rejected
    >>> setup_directory("../../../etc")  # doctest: +SKIP
    PathSecurityError: Invalid output directory
    """
    try:
        # Sanitize the output directory path
        safe_output_dir = sanitize_path(output_dir, allow_absolute=True)
        safe_output_dir.mkdir(parents=True, exist_ok=True)
        return str(safe_output_dir)
    except PathSecurityError as e:
        raise PathSecurityError(f"Invalid output directory: {e}") from e


def convert_poi_to_geodataframe(poi_data_list):
    """
    Convert POI dictionaries to a GeoPandas GeoDataFrame.

    Transforms a list of POI dictionaries containing location data
    into a GeoDataFrame with Point geometries and metadata.

    Parameters
    ----------
    poi_data_list : list of dict
        List of POI dictionaries containing location information.
        Each POI should have either 'lat'/'lon' keys or GeoJSON
        'geometry' with 'coordinates'.

    Returns
    -------
    gpd.GeoDataFrame or None
        GeoDataFrame with columns: 'name', 'id', 'type', 'geometry'.
        Returns None if input list is empty.

    Notes
    -----
    The function handles both standard lat/lon format and GeoJSON
    format for coordinates. The output uses EPSG:4326 (WGS84) CRS.

    Examples
    --------
    >>> pois = [{"lat": 45.5, "lon": -122.6, "name": "Portland"}]
    >>> gdf = convert_poi_to_geodataframe(pois)
    >>> print(gdf.columns.tolist())
    ['name', 'id', 'type', 'geometry']

    >>> # GeoJSON format also supported
    >>> geojson_poi = [{
    ...     "geometry": {"coordinates": [-122.6, 45.5]},
    ...     "name": "Portland"
    ... }]
    >>> gdf = convert_poi_to_geodataframe(geojson_poi)
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
