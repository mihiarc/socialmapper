"""SocialMapper: Refactored API following SOLID principles.

This is a refactored version of the original api.py that follows SOLID principles
more closely by separating concerns, extracting validators, and using helper functions.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .api_result_types import (
    CensusDataResult,
    ClosureScenario,
    IsolationResult,
    MapResult,
    ServiceAccessDetail,
    ServiceBreakdown,
)

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd
from .constants import (
    CENSUS_MAX_YEAR,
    CENSUS_MIN_YEAR,
    FULL_BLOCK_GROUP_GEOID_LENGTH,
    ISOLATION_CATEGORY_DELAY,
    ISOLATION_CENSUS_DELAY,
    ISOLATION_ISOCHRONE_DELAY,
    ISOLATION_POI_LIMIT,
    VALHALLA_MATRIX_BATCH_SIZE,
)
from .exceptions import SocialMapperError
from .helpers import (
    create_circular_geometry,
    extract_geometry_from_geojson,
    resolve_coordinates,
)
from .validators import validate_export_format, validate_location_input

logger = logging.getLogger(__name__)


def create_isochrone(
    location: str | tuple[float, float],
    travel_time: int = 15,
    travel_mode: str = "drive",
) -> dict[str, Any]:
    """
    Create a travel-time polygon (isochrone) from a location.

    Generates an isochrone showing the area reachable within a specified
    travel time from a given location using a specific mode of transport.
    Uses the Valhalla routing engine (free, no API key required).

    Parameters
    ----------
    location : str or tuple of float
        Either a "City, State" string for geocoding or a
        (latitude, longitude) tuple with coordinates.
    travel_time : int, optional
        Travel time in minutes. Must be between 1 and 120.
        Default is 15.
    travel_mode : {'drive', 'walk', 'bike'}, optional
        Mode of transportation. Default is 'drive'.

    Returns
    -------
    dict
        GeoJSON Feature dict containing:
        - 'type': Always "Feature"
        - 'geometry': GeoJSON polygon of the isochrone
        - 'properties': Dict with location, travel_time,
          travel_mode, area_sq_km, and backend

    Raises
    ------
    ValueError
        If travel_time is not between 1-120, travel_mode is invalid,
        or location cannot be geocoded.

    Examples
    --------
    >>> iso = create_isochrone("Portland, OR", travel_time=20)
    >>> iso['properties']['travel_time']
    20

    >>> iso = create_isochrone((45.5152, -122.6784), travel_time=15)
    >>> iso['properties']['travel_mode']
    'drive'
    """
    from .validators import validate_travel_mode, validate_travel_time

    # Validate parameters
    validate_travel_time(travel_time)
    validate_travel_mode(travel_mode)

    # Resolve coordinates
    coords, location_name = resolve_coordinates(location)
    lat, lon = coords

    # Generate isochrone via Valhalla
    from .isochrone.backends import get_backend

    backend = get_backend()
    result = backend.create_isochrone(
        lat=lat,
        lon=lon,
        travel_time=travel_time,
        travel_mode=travel_mode,
    )

    # Build GeoJSON Feature response
    properties = {
        "location": location_name,
        "travel_time": result.travel_time,
        "travel_mode": result.travel_mode,
        "area_sq_km": result.area_sq_km,
        "backend": result.backend,
    }

    # Include backend-specific metadata if available
    if result.metadata:
        properties["metadata"] = result.metadata

    return {
        "type": "Feature",
        "geometry": result.geometry,
        "properties": properties,
    }


def get_census_blocks(
    polygon: dict | None = None,
    location: tuple[float, float] | None = None,
    radius_km: float = 5
) -> list[dict[str, Any]]:
    """
    Get census block groups for a geographic area.

    Retrieves census block group boundaries that intersect with
    either a polygon or a circular area around a point.

    Parameters
    ----------
    polygon : dict, optional
        GeoJSON Feature or geometry dict, typically from
        create_isochrone(). Either polygon or location must
        be provided.
    location : tuple of float, optional
        (latitude, longitude) coordinates for center point.
        Creates circular area with radius_km.
    radius_km : float, optional
        Radius in kilometers when using location parameter.
        Default is 5.

    Returns
    -------
    list of dict
        List of census block groups, each containing:
        - 'geoid': 12-digit census block group ID
        - 'state_fips': 2-digit state FIPS code
        - 'county_fips': 3-digit county FIPS code
        - 'tract': 6-digit census tract code
        - 'block_group': 1-digit block group number
        - 'geometry': GeoJSON polygon geometry
        - 'area_sq_km': Area in square kilometers

    Raises
    ------
    ValueError
        If neither polygon nor location is provided, or if
        both are provided.

    Examples
    --------
    >>> # Using an isochrone polygon
    >>> iso = create_isochrone("San Francisco, CA", travel_time=15)
    >>> blocks = get_census_blocks(polygon=iso)
    >>> len(blocks)
    42

    >>> # Using a point and radius
    >>> blocks = get_census_blocks(location=(37.7749, -122.4194),
    ...                           radius_km=3)
    >>> blocks[0]['geoid']
    '060750201001'
    """
    from ._census import fetch_block_groups_for_area

    validate_location_input(polygon, location)

    if polygon:
        geom = extract_geometry_from_geojson(polygon)
    else:
        geom = create_circular_geometry(location, radius_km)

    return fetch_block_groups_for_area(geom)


def get_census_data(
    location: dict | list[str] | tuple[float, float],
    variables: list[str],
    year: int = 2023
) -> CensusDataResult:
    """
    Get census demographic data for specified locations.

    Retrieves census data for various geographic units. Supports
    multiple input formats and automatically handles different census
    geographic levels (block groups, tracts, ZCTAs). Returns a
    consistent structure regardless of location type.

    Parameters
    ----------
    location : dict, list of str, or tuple of float
        Location specification:
        - dict: GeoJSON Feature/geometry from create_isochrone()
        - list: GEOID strings like ["060750201001", ...]
        - tuple: (latitude, longitude) for single point
    variables : list of str
        Census variables to retrieve. Can be:
        - Common names: ["population", "median_income", "median_age"]
        - Census codes: ["B01003_001E", "B19013_001E", "B01002_001E"]
    year : int, optional
        Census year for ACS 5-year estimates. Default is 2023.

    Returns
    -------
    CensusDataResult
        Structured result containing:
        - data: Census data as {geoid: {variable: value, ...}}
          Always uses nested dict structure for consistency.
        - location_type: Type of location query (polygon, geoids, point)
        - query_info: Metadata including year and variables requested

    Examples
    --------
    >>> # From an isochrone
    >>> iso = create_isochrone("Denver, CO", travel_time=20)
    >>> result = get_census_data(iso, ["population", "median_income"])
    >>> len(result.data)  # Number of block groups
    35
    >>> result.location_type
    'polygon'

    >>> # From specific GEOIDs
    >>> result = get_census_data(["060750201001"], ["B01003_001E"])
    >>> result.data["060750201001"]["B01003_001E"]
    2543
    >>> result.location_type
    'geoids'

    >>> # From a point location
    >>> result = get_census_data((37.7749, -122.4194), ["population"])
    >>> geoid = list(result.data.keys())[0]
    >>> result.data[geoid]["population"]
    1842
    >>> result.location_type
    'point'
    """
    from ._census import fetch_census_data, normalize_variable_names
    from .exceptions import ValidationError

    # Validate inputs
    if not isinstance(year, int) or not (CENSUS_MIN_YEAR <= year <= CENSUS_MAX_YEAR):
        raise ValidationError(
            f"Census year must be an integer between {CENSUS_MIN_YEAR} and {CENSUS_MAX_YEAR}, got {year!r}"
        )
    if not variables or not isinstance(variables, list):
        raise ValidationError(
            "Census variables must be a non-empty list of variable names"
        )

    # Normalize variable names (may expand compound variables)
    var_codes, compounds = normalize_variable_names(variables)

    # Determine location type
    if isinstance(location, dict):
        location_type = "polygon"
    elif isinstance(location, list):
        location_type = "geoids"
    elif isinstance(location, tuple):
        location_type = "point"
    else:
        raise ValueError(
            "Location must be GeoJSON dict, list of GEOIDs, or (lat, lon) tuple"
        )

    # Resolve location to GEOIDs
    geoids = _resolve_geoids_from_location(location)

    # Fetch census data
    data = fetch_census_data(geoids, var_codes, year)

    # Post-process: compute compound variables (e.g. poverty = sum of two codes)
    if compounds:
        for geoid_data in data.values():
            for friendly_name, components in compounds.items():
                values = [geoid_data.get(c) for c in components]
                if all(v is not None for v in values):
                    geoid_data[friendly_name] = sum(values)
                else:
                    geoid_data[friendly_name] = None
                # Remove component codes from output
                for c in components:
                    geoid_data.pop(c, None)

    # Return consistent structure - always {geoid: {variable: value}}
    return CensusDataResult(
        data=data,
        location_type=location_type,
        query_info={
            "year": year,
            "variables": variables,
            "variable_codes": var_codes,
            "geoid_count": len(geoids)
        }
    )


def _resolve_geoids_from_location(location) -> list[str]:
    """
    Convert location specification to census GEOIDs.

    Resolves various location formats into a list of census
    geographic identifiers (GEOIDs).

    Parameters
    ----------
    location : dict, list, or tuple
        Location as GeoJSON dict, list of GEOIDs, or
        (lat, lon) coordinate tuple.

    Returns
    -------
    list of str
        List of 12-digit census block group GEOIDs.

    Raises
    ------
    ValueError
        If location format is invalid or census geography
        cannot be determined.
    """
    if isinstance(location, dict):
        blocks = get_census_blocks(polygon=location)
        return [b["geoid"] for b in blocks]
    elif isinstance(location, list):
        invalid = [g for g in location if not (isinstance(g, str) and len(g) == FULL_BLOCK_GROUP_GEOID_LENGTH and g.isdigit())]
        if invalid:
            from .exceptions import ValidationError
            raise ValidationError(
                f"GEOIDs must be 12-digit numeric strings, got invalid: {invalid[:5]}"
            )
        return location
    elif isinstance(location, tuple):
        from ._geocoding import get_census_geography
        geo_info = get_census_geography(location[0], location[1])
        if not geo_info:
            raise ValueError(
                f"Could not identify census geography for point: {location}"
            )
        return [geo_info["geoid"]]
    else:
        raise ValueError(
            "Location must be GeoJSON dict, list of GEOIDs, or (lat, lon) tuple"
        )


def create_map(
    data: list[dict] | pd.DataFrame | gpd.GeoDataFrame,
    column: str,
    title: str | None = None,
    save_path: str | None = None,
    export_format: str = "png",
    basemap: str | None = "CartoDB.Voyager",
    cmap: str | None = None,
    overlay_boundary: dict | gpd.GeoDataFrame | None = None,
    overlay_points: list[dict] | None = None,
    show_stats: bool = False,
    stats_dict: dict | None = None,
) -> MapResult:
    """
    Create a choropleth map visualization.

    Generates a thematic map where geographic areas are colored
    according to the values of a data variable. Always returns
    a MapResult object for consistent return types regardless of
    format or save behavior.

    Parameters
    ----------
    data : list of dict, DataFrame, or GeoDataFrame
        Geographic data to visualize:
        - list: Dicts with 'geometry' key and data columns
        - DataFrame: Must have a 'geometry' column
        - GeoDataFrame: GeoPandas GeoDataFrame
    column : str
        Name of the data column to visualize on the map.
    title : str, optional
        Title to display on the map. Default is None.
    save_path : str, optional
        Path to save the map file. If provided, the result will
        include the absolute path. Default is None.
    export_format : {'png', 'pdf', 'svg', 'geojson', 'shapefile', 'html'}, optional
        Output format for the map. Use 'html' for interactive Leaflet
        maps (requires ``socialmapper[interactive]``). Default is 'png'.
    basemap : str, optional
        Basemap provider name for image formats. Options include:
        - 'CartoDB.Voyager' (default): Clean, light basemap
        - 'CartoDB.Positron': Minimal, grayscale basemap
        - 'CartoDB.DarkMatter': Dark theme basemap
        - None: No basemap (plain white background)
    cmap : str, optional
        Matplotlib colormap name. If None, auto-selects based on data:
        - Sequential numeric: 'YlGnBu'
        - Diverging numeric: 'RdBu_r'
        - Categorical: 'Set3'
    overlay_boundary : dict or GeoDataFrame, optional
        Boundary geometry to overlay (e.g., isochrone). Can be:
        - GeoJSON dict (Feature or geometry)
        - GeoDataFrame with boundary geometry
        Displayed as dashed red line on image formats.
    overlay_points : list of dict, optional
        List of point markers to overlay. Each dict must have:
        - 'lat': Latitude
        - 'lon': Longitude
        - 'name' (optional): Label for the point
        Only applies to image formats (png, pdf, svg).
    show_stats : bool, optional
        Whether to display a statistics box. Default is False.
        Only applies to image formats.
    stats_dict : dict, optional
        Custom statistics to display. If None and show_stats is True,
        basic statistics are calculated from the data column.

    Returns
    -------
    MapResult
        Structured result containing:
        - format: The export format used
        - image_data: Raw bytes for image formats (if not saved)
        - geojson_data: GeoJSON dict (if format is geojson and
          not saved)
        - file_path: Absolute path to saved file (if saved)
        - metadata: Additional info like column name, title, etc.

    Raises
    ------
    ValueError
        If column not found in data, invalid export format,
        or shapefile format without save_path.

    Examples
    --------
    >>> # Create map from census blocks - get image bytes
    >>> blocks = get_census_blocks(location=(40.7128, -74.0060),
    ...                           radius_km=2)
    >>> result = get_census_data([b["geoid"] for b in blocks],
    ...                         ["population"])
    >>> for block in blocks:
    ...     block["population"] = result.data.get(
    ...         block["geoid"], {}).get("population", 0)
    >>> map_result = create_map(blocks, "population",
    ...                        title="Population by Block Group")
    >>> map_result.format
    'png'
    >>> len(map_result.image_data)
    45231

    >>> # Create map with basemap and overlays
    >>> iso = create_isochrone("Portland, OR", travel_time=15)
    >>> map_result = create_map(
    ...     blocks, "population",
    ...     title="Population within 15-min drive",
    ...     basemap="CartoDB.Positron",
    ...     overlay_boundary=iso,
    ...     overlay_points=[{'lat': 45.5, 'lon': -122.6, 'name': 'Origin'}],
    ...     show_stats=True
    ... )

    >>> # Create GeoJSON map
    >>> map_result = create_map(blocks, "population",
    ...                        export_format="geojson")
    >>> map_result.geojson_data['type']
    'FeatureCollection'

    >>> # Save as shapefile - get file path
    >>> map_result = create_map(blocks, "population",
    ...                        save_path="output.shp",
    ...                        export_format="shapefile")
    >>> map_result.file_path
    PosixPath('/absolute/path/to/output.shp')
    """
    # Validate export format
    validate_export_format(export_format)

    # Convert data to GeoDataFrame
    gdf = _convert_data_to_geodataframe(data)

    # Check column exists
    if column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found in data")

    # Prepare metadata
    metadata = {
        "column": column,
        "title": title,
        "num_features": len(gdf),
        "column_type": str(gdf[column].dtype)
    }

    # Generate map based on format
    if export_format in ["png", "pdf", "svg"]:
        return _create_image_map(
            gdf, column, title, save_path, export_format, metadata,
            basemap=basemap, cmap=cmap, overlay_boundary=overlay_boundary,
            overlay_points=overlay_points, show_stats=show_stats,
            stats_dict=stats_dict
        )
    elif export_format == "html":
        return _create_html_map(
            gdf, column, title, save_path, metadata,
            basemap=basemap, overlay_boundary=overlay_boundary,
            overlay_points=overlay_points, show_stats=show_stats,
            stats_dict=stats_dict
        )
    elif export_format == "geojson":
        return _create_geojson_export(gdf, save_path, metadata)
    elif export_format == "shapefile":
        return _create_shapefile_export(gdf, save_path, metadata)
    else:
        raise ValueError(f"Unsupported export format: {export_format}")


def _convert_data_to_geodataframe(data) -> gpd.GeoDataFrame:
    """
    Convert input data to GeoPandas GeoDataFrame.

    Standardizes various geographic data formats into a
    GeoDataFrame for consistent processing.

    Parameters
    ----------
    data : list, DataFrame, or GeoDataFrame
        Geographic data in various formats.

    Returns
    -------
    GeoDataFrame
        Standardized geographic data with EPSG:4326 CRS.

    Raises
    ------
    ValueError
        If data format is invalid or missing required fields.
    """
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import shape

    if isinstance(data, list):
        geometries = []
        attributes = []

        for item in data:
            if "geometry" not in item:
                raise ValueError("Each item must have a 'geometry' field")

            if isinstance(item["geometry"], dict):
                geom = shape(item["geometry"])
            else:
                geom = item["geometry"]
            geometries.append(geom)

            attrs = {k: v for k, v in item.items() if k != "geometry"}
            attributes.append(attrs)

        return gpd.GeoDataFrame(attributes, geometry=geometries, crs="EPSG:4326")

    elif isinstance(data, pd.DataFrame):
        if "geometry" not in data.columns:
            raise ValueError("DataFrame must have a 'geometry' column")
        return gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:4326")

    elif isinstance(data, gpd.GeoDataFrame):
        if data.crs is None:
            return data.set_crs("EPSG:4326")
        return data

    else:
        raise ValueError(
            "Data must be a list of dicts, DataFrame, or GeoDataFrame"
        )


def _create_image_map(
    gdf: gpd.GeoDataFrame,
    column: str,
    title: str | None,
    save_path: str | None,
    export_format: str,
    metadata: dict[str, Any],
    basemap: str | None = "CartoDB.Voyager",
    cmap: str | None = None,
    overlay_boundary: dict | gpd.GeoDataFrame | None = None,
    overlay_points: list[dict] | None = None,
    show_stats: bool = False,
    stats_dict: dict | None = None,
) -> MapResult:
    """
    Generate image-format choropleth map.

    Creates a visual map in PNG, PDF, or SVG format and returns
    a MapResult object.

    Parameters
    ----------
    gdf : GeoDataFrame
        Geographic data to visualize.
    column : str
        Column name to visualize.
    title : str, optional
        Map title.
    save_path : str, optional
        File path for saving.
    export_format : str
        Image format (png, pdf, svg).
    metadata : dict
        Metadata about the map.
    basemap : str, optional
        Basemap provider name. Default is 'CartoDB.Voyager'.
    cmap : str, optional
        Matplotlib colormap name.
    overlay_boundary : dict or GeoDataFrame, optional
        Boundary geometry to overlay.
    overlay_points : list of dict, optional
        Point markers to overlay.
    show_stats : bool, optional
        Whether to display statistics box.
    stats_dict : dict, optional
        Custom statistics to display.

    Returns
    -------
    MapResult
        Structured result with image_data or file_path populated.
    """
    import geopandas as gpd
    from shapely.geometry import shape

    from ._visualization import generate_choropleth_map

    # Convert overlay_boundary dict to GeoDataFrame if needed
    overlay_boundary_gdf = None
    if overlay_boundary is not None:
        if isinstance(overlay_boundary, gpd.GeoDataFrame):
            overlay_boundary_gdf = overlay_boundary
        elif isinstance(overlay_boundary, dict):
            # Convert GeoJSON dict to GeoDataFrame
            geom = shape(overlay_boundary.get('geometry', overlay_boundary))
            overlay_boundary_gdf = gpd.GeoDataFrame(
                {'geometry': [geom]}, crs="EPSG:4326"
            )

    image_data = generate_choropleth_map(
        gdf, column, title, save_path, output_format=export_format,
        basemap=basemap, cmap=cmap, overlay_boundary=overlay_boundary_gdf,
        overlay_points=overlay_points, show_stats=show_stats,
        stats_dict=stats_dict
    )

    # If saved to file, image_data will be None
    if save_path:
        return MapResult(
            format=export_format,
            file_path=Path(save_path).resolve(),
            metadata=metadata
        )
    else:
        return MapResult(
            format=export_format,
            image_data=image_data,
            metadata=metadata
        )


def _create_html_map(
    gdf: gpd.GeoDataFrame,
    column: str,
    title: str | None,
    save_path: str | None,
    metadata: dict[str, Any],
    basemap: str | None = "CartoDB.Voyager",
    overlay_boundary: dict | gpd.GeoDataFrame | None = None,
    overlay_points: list[dict] | None = None,
    show_stats: bool = False,
    stats_dict: dict | None = None,
) -> MapResult:
    """Generate an interactive HTML map using folium.

    Parameters
    ----------
    gdf : GeoDataFrame
        Geographic data to visualize.
    column : str
        Column name to visualize.
    title : str, optional
        Map title.
    save_path : str, optional
        File path for saving HTML.
    metadata : dict
        Metadata about the map.
    basemap : str, optional
        Basemap provider name.
    overlay_boundary : dict or GeoDataFrame, optional
        Boundary geometry to overlay.
    overlay_points : list of dict, optional
        Point markers to overlay.
    show_stats : bool, optional
        Whether to display statistics panel.
    stats_dict : dict, optional
        Custom statistics to display.

    Returns
    -------
    MapResult
        Structured result with html_content or file_path populated.
    """
    import geopandas as gpd
    from shapely.geometry import shape

    from ._interactive import generate_interactive_map

    # Convert overlay_boundary dict to GeoDataFrame if needed
    overlay_boundary_gdf = None
    if overlay_boundary is not None:
        if isinstance(overlay_boundary, gpd.GeoDataFrame):
            overlay_boundary_gdf = overlay_boundary
        elif isinstance(overlay_boundary, dict):
            geom = shape(overlay_boundary.get('geometry', overlay_boundary))
            overlay_boundary_gdf = gpd.GeoDataFrame(
                {'geometry': [geom]}, crs="EPSG:4326"
            )

    html_content = generate_interactive_map(
        gdf, column, title, save_path,
        basemap=basemap, overlay_boundary=overlay_boundary_gdf,
        overlay_points=overlay_points, show_stats=show_stats,
        stats_dict=stats_dict,
    )

    if save_path:
        return MapResult(
            format="html",
            file_path=Path(save_path).resolve(),
            metadata=metadata,
        )
    else:
        return MapResult(
            format="html",
            html_content=html_content,
            metadata=metadata,
        )


def _create_geojson_export(
    gdf: gpd.GeoDataFrame,
    save_path: str | None,
    metadata: dict[str, Any]
) -> MapResult:
    """
    Export GeoDataFrame to GeoJSON format.

    Converts geographic data to GeoJSON for web mapping and
    returns a MapResult object.

    Parameters
    ----------
    gdf : GeoDataFrame
        Geographic data to export.
    save_path : str, optional
        File path for saving, if None returns dict.
    metadata : dict
        Metadata about the map.

    Returns
    -------
    MapResult
        Structured result with geojson_data or file_path populated.
    """
    geojson_data = json.loads(gdf.to_json())

    if save_path:
        from .io.writers import write_geojson
        output_path = Path(save_path).resolve()
        write_geojson(gdf, output_path)
        return MapResult(
            format="geojson",
            file_path=output_path,
            metadata=metadata
        )
    else:
        return MapResult(
            format="geojson",
            geojson_data=geojson_data,
            metadata=metadata
        )


def _create_shapefile_export(
    gdf: gpd.GeoDataFrame,
    save_path: str | None,
    metadata: dict[str, Any]
) -> MapResult:
    """
    Export GeoDataFrame to ESRI Shapefile.

    Creates shapefile for GIS software compatibility and returns
    a MapResult object with the file path.

    Parameters
    ----------
    gdf : GeoDataFrame
        Geographic data to export.
    save_path : str
        Required file path for shapefile output.
    metadata : dict
        Metadata about the map.

    Returns
    -------
    MapResult
        Structured result with file_path populated.

    Raises
    ------
    ValueError
        If save_path is not provided.
    """
    if not save_path:
        raise ValueError("save_path is required for shapefile export")

    output_path = Path(save_path)
    if not output_path.suffix:
        output_path = output_path.with_suffix('.shp')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver='ESRI Shapefile')

    return MapResult(
        format="shapefile",
        file_path=output_path.resolve(),
        metadata=metadata
    )


def _filter_pois_by_polygon(
    pois: list[dict[str, Any]], polygon
) -> list[dict[str, Any]]:
    """Filter POIs to only those contained within a polygon.

    Parameters
    ----------
    pois : list of dict
        POI dicts with ``lat`` and ``lon`` keys.
    polygon : shapely.geometry.Polygon
        Search area boundary.

    Returns
    -------
    list of dict
        POIs whose coordinates fall inside *polygon*.
    """
    from shapely.geometry import Point

    kept = []
    for poi in pois:
        if polygon.contains(Point(poi["lon"], poi["lat"])):
            kept.append(poi)
    if len(kept) < len(pois):
        logger.debug(
            "Spatial filter removed %d POIs outside polygon",
            len(pois) - len(kept),
        )
    return kept


def _calculate_travel_times(
    pois: list[dict[str, Any]],
    origin: tuple[float, float],
    travel_mode: str = "drive",
) -> None:
    """Compute actual travel time/distance from origin to each POI via Valhalla matrix API.

    Updates each POI dict in-place with ``travel_time_minutes`` and
    ``travel_distance_km`` fields.

    Parameters
    ----------
    pois : list of dict
        POI dicts with ``lat`` and ``lon`` keys.
    origin : tuple of float
        ``(latitude, longitude)`` of the origin point.
    travel_mode : str
        One of ``'drive'``, ``'walk'``, ``'bike'``.
    """
    import time

    if not pois:
        return

    from .isochrone.backends import get_backend

    backend = get_backend()
    router = backend.get_router()
    profile = {"drive": "auto", "walk": "pedestrian", "bike": "bicycle"}[travel_mode]

    # routingpy uses (lon, lat) format
    origin_loc = [origin[1], origin[0]]
    poi_locs = [[p["lon"], p["lat"]] for p in pois]

    BATCH_SIZE = VALHALLA_MATRIX_BATCH_SIZE
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds between batches / initial retry delay

    for batch_start in range(0, len(pois), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(pois))
        batch_locs = [origin_loc] + poi_locs[batch_start:batch_end]
        destinations = list(range(1, len(batch_locs)))

        # Pause between batches to respect rate limits on public Valhalla
        if batch_start > 0:
            time.sleep(BASE_DELAY)

        success = False
        for attempt in range(MAX_RETRIES):
            try:
                result = router.matrix(
                    locations=batch_locs,
                    profile=profile,
                    sources=[0],
                    destinations=destinations,
                )

                for i, poi_idx in enumerate(range(batch_start, batch_end)):
                    duration = result.durations[0][i]
                    distance = result.distances[0][i] if result.distances else None
                    if duration is not None:
                        pois[poi_idx]["travel_time_minutes"] = round(duration / 60, 1)
                    else:
                        pois[poi_idx]["travel_time_minutes"] = None
                    if distance is not None:
                        pois[poi_idx]["travel_distance_km"] = round(distance / 1000, 2)
                    else:
                        pois[poi_idx]["travel_distance_km"] = None

                success = True
                break

            except Exception as exc:
                exc_str = str(exc)
                is_rate_limit = "429" in exc_str or "content-type" in exc_str.lower()
                if is_rate_limit and attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** (attempt + 1))
                    logger.info(
                        "Rate limited on batch %d-%d (attempt %d/%d), "
                        "retrying in %.1fs",
                        batch_start, batch_end, attempt + 1, MAX_RETRIES, delay,
                    )
                    time.sleep(delay)
                    continue

                logger.warning(
                    "Valhalla matrix call failed for batch %d-%d "
                    "after %d attempt(s), falling back to no travel data: %s",
                    batch_start, batch_end, attempt + 1, exc,
                )
                break

        if not success:
            for poi_idx in range(batch_start, batch_end):
                pois[poi_idx]["travel_time_minutes"] = None
                pois[poi_idx]["travel_distance_km"] = None


def get_poi(
    location: str | tuple[float, float],
    categories: list[str] | None = None,
    travel_time: int | None = None,
    travel_mode: str = "drive",
    limit: int = 100,
    validate_coords: bool = True,
    *,
    _search_polygon=None,
) -> list[dict[str, Any]]:
    """
    Get points of interest near a location.

    Retrieves POIs from OpenStreetMap within a specified area,
    either defined by travel time or radius.

    Parameters
    ----------
    location : str or tuple of float
        Either "City, State" string or (latitude, longitude) tuple.
    categories : list of str, optional
        POI categories to filter. Options include:
        - Food: "restaurant", "cafe", "bar", "fast_food"
        - Education: "school", "university", "library"
        - Health: "hospital", "clinic", "pharmacy"
        - Recreation: "park", "playground", "sports"
        - Shopping: "grocery", "supermarket", "convenience"
        - Finance: "bank", "atm"
        Default is None (all categories).
    travel_time : int, optional
        Travel time in minutes for boundary (uses driving).
        If provided, finds POIs within isochrone and computes
        actual travel time/distance via Valhalla matrix API.
        Results are sorted by ``travel_time_minutes``.
        If None, uses 5km radius and sorts by geodesic
        ``distance_km``. Default is None.
    travel_mode : {'drive', 'walk', 'bike'}, optional
        Mode of transportation used when *travel_time* is given.
        Default is 'drive'.
    limit : int, optional
        Maximum number of POIs to return. Default is 100.
    validate_coords : bool, optional
        Whether to validate POI coordinates. Default is True.

    Returns
    -------
    list of dict
        POIs sorted by distance/travel time, each containing:
        - 'name': POI name
        - 'category': POI category
        - 'lat': Latitude
        - 'lon': Longitude
        - 'distance_km': Geodesic (straight-line) distance from origin
        - 'address': Address string or None
        - 'tags': Additional OSM tags
        When *travel_time* is provided, each dict also includes:
        - 'travel_time_minutes': Actual routed travel time
        - 'travel_distance_km': Actual routed distance

    Examples
    --------
    >>> # POIs within 5km radius
    >>> pois = get_poi("Seattle, WA",
    ...               categories=["restaurant", "cafe"])
    >>> len(pois)
    75

    >>> # POIs within 15-minute drive
    >>> pois = get_poi((47.6062, -122.3321), travel_time=15)
    >>> pois[0]['distance_km']
    0.542
    """
    from ._osm import query_pois
    from .poi_categorization import POI_CATEGORY_MAPPING
    from .validators import validate_travel_time

    # Validate categories if provided
    if categories:
        for category in categories:
            if category not in POI_CATEGORY_MAPPING:
                from .exceptions import InvalidPOICategoryError
                raise InvalidPOICategoryError(
                    category,
                    list(POI_CATEGORY_MAPPING.keys())
                )

    # Validate travel time if provided
    if travel_time is not None:
        validate_travel_time(travel_time)

    # Resolve coordinates
    coords, _ = resolve_coordinates(location)
    lat, lon = coords

    # Use precomputed search polygon if provided, otherwise compute
    if _search_polygon is not None:
        search_area = _search_polygon
    else:
        search_area = _create_search_area(coords, travel_time, travel_mode)

    # Query POIs
    pois = query_pois(search_area, categories)

    # Post-query spatial containment filter (safety net)
    pois = _filter_pois_by_polygon(pois, search_area)

    # Validate and filter POIs if requested
    if validate_coords:
        pois = _validate_and_filter_pois(pois)

    # Always compute geodesic distance
    _calculate_poi_distances(pois, coords, validate_coords)

    # Filter out invalid distances if validating
    if validate_coords:
        pois = [p for p in pois if p["distance_km"] != float('inf')]

    if travel_time is not None:
        # Compute actual travel times and sort by them
        _calculate_travel_times(pois, coords, travel_mode)
        pois.sort(
            key=lambda x: x["travel_time_minutes"]
            if x["travel_time_minutes"] is not None else float('inf')
        )
    else:
        # Sort by geodesic distance
        pois.sort(
            key=lambda x: x["distance_km"]
            if x["distance_km"] is not None else float('inf')
        )

    # Return limited results
    return pois[:limit]


def _create_search_area(
    coords: tuple[float, float],
    travel_time: int | None,
    travel_mode: str = "drive",
):
    """
    Generate geographic search boundary.

    Creates either an isochrone or circular search area
    for POI queries.

    Parameters
    ----------
    coords : tuple of float
        (latitude, longitude) center point.
    travel_time : int, optional
        Travel time in minutes for isochrone boundary.
    travel_mode : str, optional
        Mode of transportation for isochrone. Default is 'drive'.

    Returns
    -------
    Polygon
        Shapely polygon defining search area.
    """
    from shapely.geometry import shape

    lat, lon = coords

    if travel_time is not None:
        iso = create_isochrone((lat, lon), travel_time=travel_time, travel_mode=travel_mode)
        return shape(iso["geometry"])
    else:
        from .constants import DEFAULT_SEARCH_RADIUS_KM
        return create_circular_geometry(coords, DEFAULT_SEARCH_RADIUS_KM)


def _validate_and_filter_pois(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Validate and filter POI data.

    Removes POIs with invalid or missing coordinates.

    Parameters
    ----------
    pois : list of dict
        Raw POI data from OSM query.

    Returns
    -------
    list of dict
        POIs with valid coordinates only.
    """
    from .validators import _validate_coordinates_strict

    valid_pois = []
    invalid_count = 0

    for poi in pois:
        try:
            lat, lon = _validate_coordinates_strict(poi["lat"], poi["lon"])
            # Skip null island (0, 0) which is often an error
            if lat == 0 and lon == 0:
                invalid_count += 1
                logger.warning(
                    "Invalid coordinates for POI '%s': at null island (0, 0)",
                    poi.get("name", "Unknown"),
                )
                continue
            valid_pois.append(poi)
        except (ValueError, TypeError, KeyError) as e:
            invalid_count += 1
            logger.warning(
                "Invalid coordinates for POI '%s': (%s, %s) - %s",
                poi.get("name", "Unknown"), poi.get("lat"), poi.get("lon"), e,
            )

    if invalid_count > 0:
        logger.info("Filtered out %d POIs with invalid coordinates", invalid_count)

    return valid_pois


def _calculate_poi_distances(
    pois: list[dict[str, Any]],
    origin: tuple[float, float],
    validate_coords: bool
):
    """
    Calculate geodesic distances from origin to POIs.

    Computes the straight-line distance in kilometers from
    a central point to each POI.

    Parameters
    ----------
    pois : list of dict
        POI data with 'lat' and 'lon' fields.
    origin : tuple of float
        (latitude, longitude) of origin point.
    validate_coords : bool
        If True, marks invalid distances as infinity.

    Returns
    -------
    None
        Updates pois in-place with 'distance_km' field.
    """
    from geopy.distance import geodesic

    for poi in pois:
        poi_coords = (poi["lat"], poi["lon"])
        try:
            poi["distance_km"] = geodesic(origin, poi_coords).kilometers
        except (ValueError, TypeError) as e:
            logger.debug("Could not calculate distance for POI: %s", e)
            if validate_coords:
                poi["distance_km"] = float('inf')
            else:
                poi["distance_km"] = None


def analyze_multiple_pois(
    locations: list[str | tuple[float, float]],
    travel_time: int = 15,
    travel_mode: str = "drive",
    variables: list[str] | None = None,
    compare: bool = True
) -> dict[str, Any]:
    """
    Analyze multiple locations and optionally compare them.

    Performs demographic analysis for multiple locations using
    isochrones and census data, with optional comparison.

    Parameters
    ----------
    locations : list of str or tuple of float
        List of locations to analyze. Each can be:
        - "City, State" string for geocoding
        - (latitude, longitude) tuple
    travel_time : int, optional
        Travel time in minutes for isochrones. Default is 15.
    travel_mode : {'drive', 'walk', 'bike'}, optional
        Mode of transportation. Default is 'drive'.
    variables : list of str, optional
        Census variables to analyze. Default is ["population"].
    compare : bool, optional
        Whether to include comparative analysis. Default is True.

    Returns
    -------
    dict
        Analysis results containing:
        - 'locations': List of individual location analyses
        - 'comparison': Comparative metrics (if compare=True)
        - 'metadata': Analysis parameters

    Examples
    --------
    >>> # Analyze three cities
    >>> results = analyze_multiple_pois(
    ...     ["Portland, OR", "Seattle, WA", "San Francisco, CA"],
    ...     travel_time=20,
    ...     variables=["population", "median_income"]
    ... )
    >>> results['comparison']['population']['highest']
    'San Francisco, CA'
    """
    # Default variables if not provided
    if variables is None:
        variables = ["population"]

    # Build results structure
    results = {
        "locations": [],
        "metadata": {
            "travel_time": travel_time,
            "travel_mode": travel_mode,
            "variables": variables
        }
    }

    # Analyze each location in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _analyze_single_location(loc):
        try:
            iso = create_isochrone(loc, travel_time, travel_mode)
            census_result = get_census_data(iso, variables)

            aggregated = {}
            for var in variables:
                values = [
                    data.get(var, 0) for data in census_result.data.values()
                    if data.get(var) is not None
                ]
                if values:
                    aggregated[var] = {
                        "total": sum(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }

            return {
                "location": (loc if isinstance(loc, str)
                             else f"{loc[0]:.4f}, {loc[1]:.4f}"),
                "isochrone": iso,
                "census_data": census_result.data,
                "aggregated": aggregated,
                "block_group_count": len(census_result.data)
            }

        except (SocialMapperError, ValueError, KeyError, TypeError) as e:
            logger.error("Failed to analyze location %s: %s", loc, e)
            return {
                "location": (loc if isinstance(loc, str)
                             else f"{loc[0]:.4f}, {loc[1]:.4f}"),
                "error": str(e)
            }

    max_workers = min(4, len(locations))
    if max_workers > 1:
        # Parallel execution for multiple locations
        future_to_idx = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for idx, loc in enumerate(locations):
                future = executor.submit(_analyze_single_location, loc)
                future_to_idx[future] = idx

            # Collect results in original order
            indexed_results = {}
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                indexed_results[idx] = future.result()

        for idx in range(len(locations)):
            results["locations"].append(indexed_results[idx])
    else:
        # Single location - no need for thread pool
        results["locations"].append(_analyze_single_location(locations[0]))

    # Add comparison if requested and multiple locations
    if compare and len(results["locations"]) > 1:
        results["comparison"] = _create_comparison_analysis(results["locations"], variables)

    return results


def _create_comparison_analysis(locations: list[dict], variables: list[str]) -> dict:
    """
    Generate comparative metrics across multiple locations.

    Creates rankings and identifies highest/lowest values
    for each demographic variable across locations.

    Parameters
    ----------
    locations : list of dict
        Location analysis results with aggregated data.
    variables : list of str
        Census variables to compare.

    Returns
    -------
    dict
        Comparative analysis with rankings and extremes.
    """
    comparison = {}

    for var in variables:
        var_comparison = [
            {"location": loc_result["location"], **loc_result["aggregated"][var]}
            for loc_result in locations
            if "aggregated" in loc_result and var in loc_result["aggregated"]
        ]

        if var_comparison:
            var_comparison.sort(key=lambda x: x.get("total", 0), reverse=True)
            comparison[var] = {
                "ranked": var_comparison,
                "highest": var_comparison[0]["location"] if var_comparison else None,
                "lowest": var_comparison[-1]["location"] if var_comparison else None
            }

    return comparison


def import_poi_csv(
    csv_path: str,
    name_field: str = "name",
    lat_field: str = "latitude",
    lon_field: str = "longitude",
    type_field: str = "type"
) -> list[dict[str, Any]]:
    """
    Import points of interest from a CSV file.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file to import.
    name_field : str, optional
        Column name for POI names. Default is "name".
    lat_field : str, optional
        Column name for latitude. Default is "latitude".
    lon_field : str, optional
        Column name for longitude. Default is "longitude".
    type_field : str, optional
        Column name for POI type. Default is "type".

    Returns
    -------
    list of dict
        POIs in standard format.

    Examples
    --------
    >>> pois = import_poi_csv("locations.csv")
    >>> len(pois)
    42
    """
    from ._csv_import import parse_csv_pois

    return parse_csv_pois(csv_path, name_field, lat_field, lon_field, type_field)


def generate_report(
    analysis_data: dict[str, Any],
    format: str = "html",
    template: str = "default",
    include_maps: bool = True
) -> str | bytes:
    """
    Generate a formatted report from analysis results.

    Parameters
    ----------
    analysis_data : dict
        Analysis results from API functions.
    format : {'html', 'pdf'}, optional
        Output format. Default is 'html'.
    template : str, optional
        Report template name. Default is 'default'.
    include_maps : bool, optional
        Whether to include map visualizations. Default is True.

    Returns
    -------
    str or bytes
        - HTML format: HTML string
        - PDF format: PDF bytes

    Examples
    --------
    >>> iso = create_isochrone("Boston, MA", travel_time=15)
    >>> census = get_census_data(iso, ["population"])
    >>> report_html = generate_report({
    ...     "isochrone": iso,
    ...     "census_data": census
    ... })
    """
    from ._reporting import create_analysis_report
    from .validators import validate_report_format

    # Validate format
    validate_report_format(format)

    # Generate report
    return create_analysis_report(
        analysis_data,
        output_format=format,
        template=template,
        include_maps=include_maps,
    )


def _extract_access_detail(
    pois: list[dict[str, Any]], index: int, category: str
) -> ServiceAccessDetail:
    """Extract a ServiceAccessDetail from the POI list at a given index.

    Parameters
    ----------
    pois : list of dict
        Sorted list of POI dicts (by travel_time_minutes).
    index : int
        Index into the list to extract.
    category : str
        Service category label.

    Returns
    -------
    ServiceAccessDetail
        Populated detail for the POI at *index*, or an empty detail
        if *index* is out of range.
    """
    if index < 0 or index >= len(pois):
        return ServiceAccessDetail(category=category)
    poi = pois[index]
    return ServiceAccessDetail(
        name=poi.get("name"),
        category=category,
        travel_time_minutes=poi.get("travel_time_minutes"),
        travel_distance_km=poi.get("travel_distance_km"),
        lat=poi.get("lat"),
        lon=poi.get("lon"),
        address=poi.get("address"),
    )


def _filter_by_keywords(
    pois: list[dict[str, Any]], keywords: list[str]
) -> list[dict[str, Any]]:
    """Filter POIs whose name contains any keyword (case-insensitive).

    Parameters
    ----------
    pois : list of dict
        POI dicts with optional ``name`` key.
    keywords : list of str
        Substrings to match against POI names.

    Returns
    -------
    list of dict
        POIs whose name matched at least one keyword.
    """
    lowered_keywords = [kw.lower() for kw in keywords]
    kept: list[dict[str, Any]] = []
    for poi in pois:
        name = (poi.get("name") or "").lower()
        if not name:
            continue
        if any(kw in name for kw in lowered_keywords):
            kept.append(poi)
    return kept


def measure_isolation(
    location: str | tuple[float, float],
    service_categories: list[str] | None = None,
    travel_mode: str = "drive",
    max_search_time: int = 60,
    include_census: bool = True,
    grocery_keywords: list[str] | None = None,
) -> IsolationResult:
    """Compute a composite isolation score for a location.

    The isolation score equals the **maximum** nearest-service travel
    time across all requested categories -- the minimum driving time
    that guarantees access to every essential service.

    Parameters
    ----------
    location : str or tuple of float
        Either ``"City, State"`` for geocoding or ``(lat, lon)`` tuple.
    service_categories : list of str, optional
        POI categories to measure. Default is
        ``["shopping", "education", "healthcare"]``.
    travel_mode : {'drive', 'walk', 'bike'}, optional
        Mode of transportation. Default is ``'drive'``.
    max_search_time : int, optional
        Maximum isochrone search radius in minutes (1-120).
        Default is 60.
    include_census : bool, optional
        If True, overlay census demographics on the adaptive
        isochrone. Default is True.
    grocery_keywords : list of str, optional
        When provided, POIs in the ``shopping`` category are filtered
        to those whose name contains any of these keywords
        (case-insensitive). Useful for isolating grocery stores from
        general shopping results.

    Returns
    -------
    IsolationResult
        Composite result with per-category breakdowns, closure
        scenarios, adaptive isochrone, and optional census data.

    Examples
    --------
    >>> result = measure_isolation("Liberal, KS")
    >>> result.isolation_score_minutes  # max of nearest times
    7.7
    >>> result.binding_constraint
    'healthcare'
    """
    import math
    import time

    from .validators import validate_travel_mode, validate_travel_time

    # --- Step 1: Validate inputs ----------------------------------------
    if service_categories is None:
        service_categories = ["shopping", "education", "healthcare"]

    validate_travel_time(max_search_time)
    validate_travel_mode(travel_mode)

    # Validate each category is known
    from .exceptions import InvalidPOICategoryError
    from .poi_categorization import POI_CATEGORY_MAPPING

    for cat in service_categories:
        if cat not in POI_CATEGORY_MAPPING:
            raise InvalidPOICategoryError(cat, list(POI_CATEGORY_MAPPING.keys()))

    # --- Step 2: Resolve location ----------------------------------------
    coords, location_name = resolve_coordinates(location)

    logger.info(
        "measure_isolation: %s (%s) — categories=%s, max_search=%d min",
        location_name, coords, service_categories, max_search_time,
    )

    # --- Step 3: Search isochrone ----------------------------------------
    from shapely.geometry import shape

    search_iso = create_isochrone(coords, travel_time=max_search_time, travel_mode=travel_mode)
    search_polygon = shape(search_iso["geometry"])

    # --- Step 4: Per-category POI queries --------------------------------
    category_pois: dict[str, list[dict[str, Any]]] = {}

    for idx, category in enumerate(service_categories):
        # Rate-limit: 8-second delay between categories (skip first)
        if idx > 0:
            logger.info("Waiting %d s before querying category '%s'…", ISOLATION_CATEGORY_DELAY, category)
            time.sleep(ISOLATION_CATEGORY_DELAY)

        try:
            pois = get_poi(
                coords,
                categories=[category],
                travel_time=max_search_time,
                travel_mode=travel_mode,
                limit=ISOLATION_POI_LIMIT,
                _search_polygon=search_polygon,
            )
        except Exception as exc:
            logger.warning(
                "POI query failed for category '%s': %s", category, exc
            )
            pois = []

        # Apply grocery_keywords filter to shopping category
        if category == "shopping" and grocery_keywords and pois:
            pois = _filter_by_keywords(pois, grocery_keywords)

        category_pois[category] = pois
        logger.info(
            "  %s: %d POIs found (nearest=%.1f min)",
            category,
            len(pois),
            pois[0]["travel_time_minutes"] if pois and pois[0].get("travel_time_minutes") is not None else float("nan"),
        )

    # --- Step 5: Compute isolation score ---------------------------------
    breakdowns: list[ServiceBreakdown] = []
    nearest_times: list[float] = []

    for category in service_categories:
        pois = category_pois[category]
        nearest = _extract_access_detail(pois, 0, category)
        second_nearest = _extract_access_detail(pois, 1, category) if len(pois) > 1 else None

        breakdown = ServiceBreakdown(
            category=category,
            nearest=nearest,
            second_nearest=second_nearest,
            poi_count=len(pois),
        )
        breakdowns.append(breakdown)

        if nearest.travel_time_minutes is not None:
            nearest_times.append(nearest.travel_time_minutes)

    # Isolation score = max of nearest times
    isolation_score: float | None = None
    binding_constraint: str | None = None

    if nearest_times:
        isolation_score = max(nearest_times)
        # Find binding category
        for bd in breakdowns:
            if (
                bd.nearest.travel_time_minutes is not None
                and bd.nearest.travel_time_minutes == isolation_score
            ):
                bd.is_binding = True
                binding_constraint = bd.category
                break

    # --- Step 6: Closure scenarios ----------------------------------------
    closure_scenarios: list[ClosureScenario] = []
    second_nearest_times: list[float] = []

    for bd in breakdowns:
        original_time = bd.nearest.travel_time_minutes
        if bd.second_nearest is not None:
            new_time = bd.second_nearest.travel_time_minutes
        else:
            new_time = None

        increase: float | None = None
        access_lost = False

        if original_time is not None and new_time is not None:
            increase = round(new_time - original_time, 1)
            second_nearest_times.append(new_time)
        elif original_time is not None and new_time is None:
            # Only 1 POI — closure means total loss
            access_lost = True if bd.poi_count == 1 else False

        closure_scenarios.append(ClosureScenario(
            category=bd.category,
            original_time_minutes=original_time,
            new_time_minutes=new_time,
            time_increase_minutes=increase,
            access_lost=access_lost,
        ))

    closure_isolation_score: float | None = None
    if second_nearest_times:
        closure_isolation_score = max(second_nearest_times)

    # --- Step 7: Adaptive isochrone --------------------------------------
    adaptive_iso: dict | None = None

    if isolation_score is not None:
        adaptive_time = math.ceil(isolation_score)
        # Clamp to valid range
        adaptive_time = max(1, min(adaptive_time, 120))
        if adaptive_time == max_search_time:
            adaptive_iso = search_iso
        else:
            logger.info(
                "Waiting %d s before adaptive isochrone (%d min)…", ISOLATION_ISOCHRONE_DELAY, adaptive_time
            )
            time.sleep(ISOLATION_ISOCHRONE_DELAY)
            try:
                adaptive_iso = create_isochrone(
                    coords, travel_time=adaptive_time, travel_mode=travel_mode
                )
            except Exception as exc:
                logger.warning("Adaptive isochrone failed: %s", exc)

    # --- Step 8: Census overlay ------------------------------------------
    census_data = None
    population_affected: int | None = None

    if include_census and adaptive_iso is not None:
        logger.info("Waiting %d s before census data query…", ISOLATION_CENSUS_DELAY)
        time.sleep(ISOLATION_CENSUS_DELAY)
        try:
            census_data = get_census_data(
                adaptive_iso,
                variables=["population", "median_income", "poverty"],
            )
            # Sum population across all block groups
            total_pop = 0
            for bg_data in census_data.data.values():
                pop = bg_data.get("population")
                if pop is not None:
                    total_pop += int(pop)
            population_affected = total_pop
        except Exception as exc:
            logger.warning("Census data query failed: %s", exc)

    # --- Build result ----------------------------------------------------
    return IsolationResult(
        location_name=location_name,
        coordinates=coords,
        isolation_score_minutes=isolation_score,
        binding_constraint=binding_constraint,
        service_breakdown=breakdowns,
        closure_scenarios=closure_scenarios,
        closure_isolation_score_minutes=closure_isolation_score,
        adaptive_isochrone=adaptive_iso,
        census_data=census_data,
        population_affected=population_affected,
        metadata={
            "service_categories": service_categories,
            "travel_mode": travel_mode,
            "max_search_time": max_search_time,
            "grocery_keywords": grocery_keywords,
        },
    )


