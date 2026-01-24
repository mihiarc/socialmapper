"""SocialMapper: Refactored API following SOLID principles.

This is a refactored version of the original api.py that follows SOLID principles
more closely by separating concerns, extracting validators, and using helper functions.
"""

import json
import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
from shapely.geometry import shape

from .api_result_types import CensusDataResult, MapResult
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
    backend: str = "auto",
) -> dict[str, Any]:
    """
    Create a travel-time polygon (isochrone) from a location.

    Generates an isochrone showing the area reachable within a specified
    travel time from a given location using a specific mode of transport.

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
    backend : str, optional
        Isochrone generation backend. Options:
        - 'auto': Automatically select best available (default)
        - 'valhalla': Use Valhalla API (fast, free)
        - 'ors': Use OpenRouteService (requires ORS_API_KEY)
        - 'osrm': Use Mapbox OSRM (requires MAPBOX_API_KEY)
        - 'graphhopper': Use GraphHopper (requires GRAPHHOPPER_API_KEY)
        - 'networkx': Use local NetworkX/OSMnx (slower but offline)

        Can also be set via SOCIALMAPPER_ROUTING_BACKEND environment
        variable.

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

    >>> # Use fast Valhalla backend explicitly
    >>> iso = create_isochrone("Raleigh, NC", backend="valhalla")
    >>> iso['properties']['backend']
    'valhalla'

    >>> # Use offline NetworkX backend
    >>> iso = create_isochrone((35.7796, -78.6382), backend="networkx")
    """
    from .validators import validate_travel_mode, validate_travel_time

    # Validate parameters
    validate_travel_time(travel_time)
    validate_travel_mode(travel_mode)

    # Resolve coordinates
    coords, location_name = resolve_coordinates(location)
    lat, lon = coords

    # Use the backend system for isochrone generation
    return _create_isochrone_with_backend(
        lat=lat,
        lon=lon,
        location_name=location_name,
        travel_time=travel_time,
        travel_mode=travel_mode,
        backend=backend,
    )


def _create_isochrone_with_backend(
    lat: float,
    lon: float,
    location_name: str,
    travel_time: int,
    travel_mode: str,
    backend: str,
) -> dict[str, Any]:
    """Create isochrone using the specified backend.

    Parameters
    ----------
    lat : float
        Latitude of the center point.
    lon : float
        Longitude of the center point.
    location_name : str
        Human-readable location name for metadata.
    travel_time : int
        Travel time in minutes.
    travel_mode : str
        Mode of transportation.
    backend : str
        Backend name ('auto', 'valhalla', 'networkx', etc.).

    Returns
    -------
    dict
        GeoJSON Feature dict.
    """
    from .isochrone.backends import get_backend

    # Get the backend (auto-selects if backend="auto")
    backend_instance = get_backend(backend)

    # Generate the isochrone
    result = backend_instance.create_isochrone(
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

    # Normalize variable names
    var_codes = normalize_variable_names(variables)

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
    export_format: str = "png"
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
    export_format : {'png', 'pdf', 'svg', 'geojson', 'shapefile'}, optional
        Output format for the map. Default is 'png'.

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
        return _create_image_map(gdf, column, title, save_path, export_format, metadata)
    elif export_format == "geojson":
        return _create_geojson_export(gdf, save_path, metadata)
    elif export_format == "shapefile":
        return _create_shapefile_export(gdf, save_path, metadata)


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
    metadata: dict[str, Any]
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

    Returns
    -------
    MapResult
        Structured result with image_data or file_path populated.
    """
    from ._visualization import generate_choropleth_map

    image_data = generate_choropleth_map(
        gdf, column, title, save_path, format=export_format
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


def get_poi(
    location: str | tuple[float, float],
    categories: list[str] | None = None,
    travel_time: int | None = None,
    limit: int = 100,
    validate_coords: bool = True
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
        If provided, finds POIs within isochrone.
        If None, uses 5km radius. Default is None.
    limit : int, optional
        Maximum number of POIs to return. Default is 100.
    validate_coords : bool, optional
        Whether to validate POI coordinates. Default is True.

    Returns
    -------
    list of dict
        POIs sorted by distance, each containing:
        - 'name': POI name
        - 'category': POI category
        - 'lat': Latitude
        - 'lon': Longitude
        - 'distance_km': Distance from origin
        - 'address': Address if available
        - 'tags': Additional OSM tags

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

    # Create search area
    search_area = _create_search_area(coords, travel_time)

    # Query POIs
    pois = query_pois(search_area, categories)

    # Validate and filter POIs if requested
    if validate_coords:
        pois = _validate_and_filter_pois(pois)

    # Calculate distances
    _calculate_poi_distances(pois, coords, validate_coords)

    # Sort by distance
    pois.sort(
        key=lambda x: x["distance_km"]
        if x["distance_km"] is not None else float('inf')
    )

    # Filter out invalid distances if validating
    if validate_coords:
        pois = [p for p in pois if p["distance_km"] != float('inf')]

    # Return limited results
    return pois[:limit]


def _create_search_area(coords: tuple[float, float], travel_time: int | None):
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

    Returns
    -------
    Polygon
        Shapely polygon defining search area.
    """
    lat, lon = coords

    if travel_time:
        iso = create_isochrone((lat, lon), travel_time=travel_time, travel_mode="drive")
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
                    f"Invalid coordinates for POI '{poi.get('name', 'Unknown')}': "
                    f"at null island (0, 0)"
                )
                continue
            valid_pois.append(poi)
        except (ValueError, TypeError, KeyError) as e:
            invalid_count += 1
            logger.warning(
                f"Invalid coordinates for POI '{poi.get('name', 'Unknown')}': "
                f"({poi.get('lat')}, {poi.get('lon')}) - {e}"
            )

    if invalid_count > 0:
        logger.info(f"Filtered out {invalid_count} POIs with invalid coordinates")

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
    for poi in pois:
        poi_coords = (poi["lat"], poi["lon"])
        try:
            poi["distance_km"] = geodesic(origin, poi_coords).kilometers
        except (ValueError, Exception) as e:
            logger.debug(f"Could not calculate distance for POI: {e}")
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

    # Analyze each location
    for loc in locations:
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

            location_result = {
                "location": (loc if isinstance(loc, str)
                             else f"{loc[0]:.4f}, {loc[1]:.4f}"),
                "isochrone": iso,
                "census_data": census_result.data,
                "aggregated": aggregated,
                "block_group_count": len(census_result.data)
            }
            results["locations"].append(location_result)

        except (SocialMapperError, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to analyze location {loc}: {e}")
            results["locations"].append({
                "location": (loc if isinstance(loc, str)
                             else f"{loc[0]:.4f}, {loc[1]:.4f}"),
                "error": str(e)
            })

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
        format,
        template,
        include_maps
    )


