"""SocialMapper: Simple, direct API for spatial analysis.

Nine core functions for all your spatial analysis needs.
"""

import os
import json
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, shape
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)


def create_isochrone(
    location: Union[str, Tuple[float, float]],
    travel_time: int = 15,
    travel_mode: str = "drive"
) -> Dict[str, Any]:
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

    Returns
    -------
    dict
        GeoJSON Feature dict containing:
        - 'type': Always "Feature"
        - 'geometry': GeoJSON polygon of the isochrone
        - 'properties': Dict with location, travel_time,
          travel_mode, and area_sq_km

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
    # Import internal modules
    from ._geocoding import geocode_location
    from ._isochrone import generate_isochrone
    
    # Validate inputs
    if not 1 <= travel_time <= 120:
        raise ValueError(f"Travel time must be between 1 and 120 minutes, got {travel_time}")
    
    if travel_mode not in ["drive", "walk", "bike"]:
        raise ValueError(f"Travel mode must be 'drive', 'walk', or 'bike', got {travel_mode}")
    
    # Get coordinates
    if isinstance(location, str):
        coords = geocode_location(location)
        if not coords:
            raise ValueError(f"Could not geocode location: {location}")
        lat, lon = coords
        location_name = location
    else:
        lat, lon = location
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Invalid coordinates: {location}")
        location_name = f"{lat:.4f}, {lon:.4f}"
    
    # Generate isochrone
    polygon = generate_isochrone(lat, lon, travel_time, travel_mode)
    
    # Calculate area
    from shapely.ops import transform
    import pyproj
    
    # Project to equal area projection for accurate area calculation
    project = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
    projected_polygon = transform(project, polygon)
    area_sq_m = projected_polygon.area
    area_sq_km = area_sq_m / 1_000_000
    
    # Return GeoJSON
    return {
        "type": "Feature",
        "geometry": polygon.__geo_interface__,
        "properties": {
            "location": location_name,
            "travel_time": travel_time,
            "travel_mode": travel_mode,
            "area_sq_km": area_sq_km
        }
    }


def get_census_blocks(
    polygon: Optional[Dict] = None,
    location: Optional[Tuple[float, float]] = None,
    radius_km: float = 5
) -> List[Dict[str, Any]]:
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
    
    # Validate inputs
    if polygon is None and location is None:
        raise ValueError("Must provide either polygon or location")
    
    if polygon is not None and location is not None:
        raise ValueError("Provide either polygon or location, not both")
    
    # Get geometry
    if polygon:
        # Extract geometry from GeoJSON
        if "geometry" in polygon:
            geom = shape(polygon["geometry"])
        else:
            geom = shape(polygon)
    else:
        # Create circle from point
        from shapely.geometry import Point
        from shapely.ops import transform
        import pyproj
        
        lat, lon = location
        
        # Create point and buffer in meters
        point = Point(lon, lat)
        
        # Project to Web Mercator for accurate buffering
        project_to_mercator = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
        project_to_wgs84 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True).transform
        
        point_mercator = transform(project_to_mercator, point)
        buffer_mercator = point_mercator.buffer(radius_km * 1000)
        geom = transform(project_to_wgs84, buffer_mercator)
    
    # Fetch block groups
    return fetch_block_groups_for_area(geom)


def get_census_data(
    location: Union[Dict, List[str], Tuple[float, float]],
    variables: List[str],
    year: int = 2023
) -> Dict[str, Any]:
    """
    Get census demographic data for specified locations.

    Retrieves census data for various geographic units. Supports
    multiple input formats and automatically handles different
    census geographic levels (block groups, tracts, ZCTAs).

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
    dict
        Census data organized by location:
        - For polygon/GEOIDs: {geoid: {variable: value, ...}, ...}
        - For point: {variable: value, ...}

    Notes
    -----
    This function supports demographic-only analysis without POIs.
    It automatically determines the appropriate census geography
    level and can aggregate data across multiple census units.

    See Also
    --------
    get_census_blocks : Get census block group boundaries
    create_isochrone : Create travel-time polygons

    Examples
    --------
    >>> # From an isochrone
    >>> iso = create_isochrone("Denver, CO", travel_time=20)
    >>> data = get_census_data(iso, ["population", "median_income"])
    >>> len(data)  # Number of block groups
    35

    >>> # From specific GEOIDs
    >>> data = get_census_data(["060750201001"], ["B01003_001E"])
    >>> data["060750201001"]["B01003_001E"]
    2543

    >>> # From a point location
    >>> data = get_census_data((39.7392, -104.9903), ["population"])
    >>> data["population"]
    3421
    """
    from ._census import fetch_census_data, normalize_variable_names
    
    # Normalize variables
    var_codes = normalize_variable_names(variables)
    
    # Determine GEOIDs based on location type
    if isinstance(location, dict):
        # GeoJSON - get census blocks first
        blocks = get_census_blocks(polygon=location)
        geoids = [b["geoid"] for b in blocks]
        
    elif isinstance(location, list):
        # List of GEOIDs
        geoids = location
        
    elif isinstance(location, tuple):
        # Point - get single block group
        from ._geocoding import get_census_geography
        geo_info = get_census_geography(location[0], location[1])
        if not geo_info:
            raise ValueError(f"Could not identify census geography for point: {location}")
        geoids = [geo_info["geoid"]]
    else:
        raise ValueError("Location must be GeoJSON dict, list of GEOIDs, or (lat, lon) tuple")
    
    # Fetch census data
    data = fetch_census_data(geoids, var_codes, year)
    
    # Format return based on input type
    if isinstance(location, tuple):
        # Return single dict for point query
        return data.get(geoids[0], {}) if geoids else {}
    else:
        # Return dict keyed by GEOID
        return data


def create_map(
    data: Union[List[Dict], pd.DataFrame, gpd.GeoDataFrame],
    column: str,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    export_format: str = "png"
) -> Optional[Union[bytes, Dict]]:
    """
    Create a choropleth map visualization.

    Generates a thematic map where geographic areas are colored
    according to the values of a data variable.

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
        Path to save the map file. If None, returns data.
        Default is None.
    export_format : {'png', 'pdf', 'svg', 'geojson', 'shapefile'}, optional
        Output format for the map. Default is 'png'.

    Returns
    -------
    bytes, dict, or None
        - Image formats (png/pdf/svg): bytes if save_path is None
        - geojson: dict if save_path is None
        - shapefile: None (requires save_path)
        - All formats: None if save_path is provided

    Raises
    ------
    ValueError
        If column not found in data, invalid export format,
        or shapefile format without save_path.

    Examples
    --------
    >>> # Create map from census blocks
    >>> blocks = get_census_blocks(location=(40.7128, -74.0060),
    ...                           radius_km=2)
    >>> census = get_census_data([b["geoid"] for b in blocks],
    ...                         ["population"])
    >>> for block in blocks:
    ...     block["population"] = census.get(block["geoid"], {}).get(
    ...         "population", 0)
    >>> img_bytes = create_map(blocks, "population",
    ...                       title="Population by Block Group")

    >>> # Save as shapefile
    >>> create_map(blocks, "population",
    ...           save_path="output.shp",
    ...           export_format="shapefile")
    """
    from ._visualization import generate_choropleth_map
    
    # Convert to GeoDataFrame if needed
    if isinstance(data, list):
        # List of dicts
        import geopandas as gpd
        from shapely.geometry import shape
        
        geometries = []
        attributes = []
        
        for item in data:
            if "geometry" not in item:
                raise ValueError("Each item must have a 'geometry' field")
            
            geom = shape(item["geometry"]) if isinstance(item["geometry"], dict) else item["geometry"]
            geometries.append(geom)
            
            # Copy attributes except geometry
            attrs = {k: v for k, v in item.items() if k != "geometry"}
            attributes.append(attrs)
        
        gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs="EPSG:4326")
        
    elif isinstance(data, pd.DataFrame):
        # Convert DataFrame to GeoDataFrame
        if "geometry" not in data.columns:
            raise ValueError("DataFrame must have a 'geometry' column")
        gdf = gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:4326")
        
    elif isinstance(data, gpd.GeoDataFrame):
        gdf = data
        
    else:
        raise ValueError("Data must be a list of dicts, DataFrame, or GeoDataFrame")
    
    # Check column exists
    if column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found in data")

    # Validate export format
    valid_formats = ["png", "pdf", "svg", "geojson", "shapefile"]
    if export_format not in valid_formats:
        raise ValueError(f"Export format must be one of {valid_formats}, got '{export_format}'")

    # Handle different export formats
    if export_format in ["png", "pdf", "svg"]:
        # Image-based map visualization
        return generate_choropleth_map(gdf, column, title, save_path, format=export_format)

    elif export_format == "geojson":
        # Export as GeoJSON
        if save_path:
            from .io.writers import write_geojson
            write_geojson(gdf, Path(save_path))
            return None
        else:
            # Return GeoJSON dict
            return json.loads(gdf.to_json())

    elif export_format == "shapefile":
        # Export as Shapefile (requires save_path)
        if not save_path:
            raise ValueError("save_path is required for shapefile export")

        from pathlib import Path
        output_path = Path(save_path)
        # Ensure .shp extension
        if not output_path.suffix:
            output_path = output_path.with_suffix('.shp')

        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save shapefile
        gdf.to_file(output_path, driver='ESRI Shapefile')
        return None


def get_poi(
    location: Union[str, Tuple[float, float]],
    categories: Optional[List[str]] = None,
    travel_time: Optional[int] = None,
    limit: int = 100,
    validate_coords: bool = True
) -> List[Dict[str, Any]]:
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

    >>> # All POIs with validation disabled
    >>> pois = get_poi((37.7749, -122.4194),
    ...               limit=50, validate_coords=False)
    """
    from ._geocoding import geocode_location
    from ._osm import query_pois
    
    # Get coordinates
    if isinstance(location, str):
        coords = geocode_location(location)
        if not coords:
            raise ValueError(f"Could not geocode location: {location}")
        lat, lon = coords
    else:
        lat, lon = location
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Invalid coordinates: {location}")
    
    # Determine search area
    if travel_time:
        # Create isochrone boundary
        iso = create_isochrone((lat, lon), travel_time=travel_time, travel_mode="drive")
        search_area = shape(iso["geometry"])
    else:
        # Use 5km radius
        from shapely.geometry import Point
        from shapely.ops import transform
        import pyproj
        
        point = Point(lon, lat)
        
        # Project to Web Mercator for accurate buffering
        project_to_mercator = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
        project_to_wgs84 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True).transform
        
        point_mercator = transform(project_to_mercator, point)
        buffer_mercator = point_mercator.buffer(5000)  # 5km
        search_area = transform(project_to_wgs84, buffer_mercator)
    
    # Query POIs
    pois = query_pois(search_area, categories)

    # Validate coordinates if requested
    if validate_coords and pois:
        from ._validation import validate_poi_coordinates_batch

        valid_pois = []
        invalid_count = 0

        for poi in pois:
            if validate_poi_coordinates_batch(poi["lat"], poi["lon"]):
                valid_pois.append(poi)
            else:
                invalid_count += 1
                logger.warning(f"Invalid coordinates for POI '{poi.get('name', 'Unknown')}': ({poi['lat']}, {poi['lon']})")

        if invalid_count > 0:
            logger.info(f"Filtered out {invalid_count} POIs with invalid coordinates")

        pois = valid_pois

    # Calculate distances from origin
    origin = (lat, lon)
    for poi in pois:
        poi_coords = (poi["lat"], poi["lon"])
        try:
            poi["distance_km"] = geodesic(origin, poi_coords).kilometers
        except (ValueError, Exception) as e:
            # If distance calculation fails (e.g., invalid coords), use a large value
            logger.debug(f"Could not calculate distance for POI: {e}")
            poi["distance_km"] = float('inf')

    # Sort by distance and limit (inf values will be at the end)
    pois.sort(key=lambda x: x["distance_km"])

    # Filter out POIs with infinite distance
    pois = [p for p in pois if p["distance_km"] != float('inf')]

    return pois[:limit]


def analyze_multiple_pois(
    locations: List[Union[str, Tuple[float, float]]],
    travel_time: int = 15,
    travel_mode: str = "drive",
    variables: List[str] = None,
    compare: bool = True
) -> Dict[str, Any]:
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

    >>> # Analyze specific coordinates
    >>> results = analyze_multiple_pois(
    ...     [(45.5152, -122.6784), (47.6062, -122.3321)],
    ...     travel_time=15
    ... )
    >>> len(results['locations'])
    2
    """
    if variables is None:
        variables = ["population"]

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
            # Create isochrone
            iso = create_isochrone(loc, travel_time, travel_mode)

            # Get census data
            census_data = get_census_data(iso, variables)

            # Aggregate statistics
            aggregated = {}
            for var in variables:
                values = [data.get(var, 0) for data in census_data.values() if data.get(var) is not None]
                if values:
                    aggregated[var] = {
                        "total": sum(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }

            location_result = {
                "location": loc if isinstance(loc, str) else f"{loc[0]:.4f}, {loc[1]:.4f}",
                "isochrone": iso,
                "census_data": census_data,
                "aggregated": aggregated,
                "block_group_count": len(census_data)
            }

            results["locations"].append(location_result)

        except Exception as e:
            logger.error(f"Failed to analyze location {loc}: {e}")
            results["locations"].append({
                "location": loc if isinstance(loc, str) else f"{loc[0]:.4f}, {loc[1]:.4f}",
                "error": str(e)
            })

    # Add comparison if requested
    if compare and len(results["locations"]) > 1:
        comparison = {}

        for var in variables:
            var_comparison = []
            for loc_result in results["locations"]:
                if "aggregated" in loc_result and var in loc_result["aggregated"]:
                    var_comparison.append({
                        "location": loc_result["location"],
                        **loc_result["aggregated"][var]
                    })

            if var_comparison:
                # Sort by total
                var_comparison.sort(key=lambda x: x.get("total", 0), reverse=True)
                comparison[var] = {
                    "ranked": var_comparison,
                    "highest": var_comparison[0]["location"] if var_comparison else None,
                    "lowest": var_comparison[-1]["location"] if var_comparison else None
                }

        results["comparison"] = comparison

    return results


def import_poi_csv(
    csv_path: str,
    name_field: str = "name",
    lat_field: str = "latitude",
    lon_field: str = "longitude",
    type_field: str = "type"
) -> List[Dict[str, Any]]:
    """
    Import points of interest from a CSV file.

    Parses CSV files with flexible column mapping to extract
    POI data in a standardized format.

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
        POIs in standard format, each containing:
        - 'name': POI name
        - 'lat': Latitude coordinate
        - 'lon': Longitude coordinate
        - 'type': POI category/type
        - 'tags': Dict of additional columns

    Raises
    ------
    FileNotFoundError
        If CSV file does not exist.
    ValueError
        If required columns not found or no valid POIs.

    Examples
    --------
    >>> # Import with standard column names
    >>> pois = import_poi_csv("locations.csv")
    >>> len(pois)
    42

    >>> # Import with custom column names
    >>> pois = import_poi_csv(
    ...     "businesses.csv",
    ...     name_field="business_name",
    ...     lat_field="lat",
    ...     lon_field="lng"
    ... )
    >>> pois[0]['name']
    'Coffee Shop'
    """
    from ._csv_import import parse_csv_pois

    return parse_csv_pois(csv_path, name_field, lat_field, lon_field, type_field)


def generate_report(
    analysis_data: Dict[str, Any],
    format: str = "html",
    template: str = "default",
    include_maps: bool = True
) -> Union[str, bytes]:
    """
    Generate a formatted report from analysis results.

    Creates professional reports from SocialMapper analysis
    data in HTML or PDF format.

    Parameters
    ----------
    analysis_data : dict
        Analysis results from API functions. Can include:
        - 'isochrone': From create_isochrone()
        - 'census_data': From get_census_data()
        - 'pois': From get_poi()
        - 'metadata': Additional information
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

    Raises
    ------
    ValueError
        If format is not 'html' or 'pdf'.

    Examples
    --------
    >>> # Generate report from isochrone analysis
    >>> iso = create_isochrone("Boston, MA", travel_time=15)
    >>> census = get_census_data(iso,
    ...                         ["population", "median_income"])
    >>> report_html = generate_report({
    ...     "isochrone": iso,
    ...     "census_data": census
    ... })

    >>> # Generate PDF report
    >>> report_pdf = generate_report(
    ...     analysis_data,
    ...     format="pdf",
    ...     include_maps=False
    ... )
    """
    from ._reporting import create_analysis_report

    return create_analysis_report(analysis_data, format, template, include_maps)


def run_pipeline(
    config: Dict[str, Any],
    stages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the full SocialMapper pipeline with custom configuration.

    Provides access to the complete pipeline functionality including
    batch processing, advanced validation, and comprehensive reporting.

    Parameters
    ----------
    config : dict
        Pipeline configuration with keys:
        - 'geocode_area': Location string or None
        - 'poi_type': POI type to search for
        - 'poi_name': POI name pattern
        - 'travel_time': Travel time in minutes (default: 15)
        - 'travel_mode': "drive", "walk", or "bike"
        - 'census_variables': List of census variables
        - 'output_dir': Output directory (default: "output")
        - 'export_csv': Whether to export CSV (default: True)
        - 'create_maps': Whether to create maps (default: True)
    stages : list of str, optional
        Specific stages to run. Options:
        ["setup", "extract", "validate", "isochrone",
         "census", "export", "maps", "report"]
        If None, runs all stages. Default is None.

    Returns
    -------
    dict
        Pipeline results containing:
        - 'poi_data': Extracted POI data
        - 'census_data': Census analysis results
        - 'maps': Generated map files
        - 'csv_data': Exported CSV path
        - 'reports': Generated reports

    See Also
    --------
    create_isochrone : Create travel-time polygons
    get_census_data : Get census demographic data
    get_poi : Get points of interest

    Examples
    --------
    >>> # Run full pipeline for schools
    >>> results = run_pipeline({
    ...     "geocode_area": "Chicago, IL",
    ...     "poi_type": "school",
    ...     "poi_name": "elementary",
    ...     "travel_time": 20,
    ...     "census_variables": ["population", "median_income"]
    ... })
    >>> results['poi_data']['metadata']['source']
    'OpenStreetMap'

    >>> # Run specific stages only
    >>> results = run_pipeline(
    ...     config,
    ...     stages=["setup", "extract", "validate"]
    ... )
    """
    from .pipeline.orchestrator import PipelineConfig, PipelineOrchestrator

    # Create pipeline config
    pipeline_config = PipelineConfig(**config)

    # Create and run orchestrator
    orchestrator = PipelineOrchestrator(pipeline_config)

    # Run specific stages or all
    if stages:
        return orchestrator.run_stages(stages)
    else:
        return orchestrator.run()