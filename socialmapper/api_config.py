"""Configuration objects for SocialMapper API functions."""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, Dict, Any
from .constants import (
    DEFAULT_TRAVEL_TIME, DEFAULT_TRAVEL_MODE, DEFAULT_CENSUS_YEAR,
    DEFAULT_POI_LIMIT, DEFAULT_EXPORT_FORMAT, DEFAULT_SEARCH_RADIUS_KM
)
from .validators import (
    validate_travel_time, validate_travel_mode, validate_export_format,
    validate_report_format
)


@dataclass
class IsochroneConfig:
    """
    Configuration for isochrone generation operations.

    Contains parameters for generating travel-time polygons including
    location specification, travel constraints, and transportation mode.

    Parameters
    ----------
    location : str or tuple of float
        Either a "City, State" string for geocoding or
        (latitude, longitude) tuple with coordinates.
    travel_time : int, default 15
        Travel time in minutes, must be between 1 and 120.
    travel_mode : {'drive', 'walk', 'bike'}, default 'drive'
        Transportation mode for travel time calculation.
    """

    location: Union[str, Tuple[float, float]]
    travel_time: int = DEFAULT_TRAVEL_TIME
    travel_mode: str = DEFAULT_TRAVEL_MODE

    def __post_init__(self):
        validate_travel_time(self.travel_time)
        validate_travel_mode(self.travel_mode)


@dataclass
class CensusConfig:
    """
    Configuration for census data retrieval operations.

    Contains parameters for fetching demographic data from the US Census
    Bureau's American Community Survey.

    Parameters
    ----------
    location : dict, list of str, or tuple of float
        Location specification:
        - dict: GeoJSON Feature/geometry from create_isochrone()
        - list: GEOID strings like ["060750201001", ...]
        - tuple: (latitude, longitude) for single point
    variables : list of str
        Census variables to retrieve. Can be common names or Census codes.
    year : int, default 2023
        Census year for ACS 5-year estimates.
    """

    location: Union[Dict, List[str], Tuple[float, float]]
    variables: List[str]
    year: int = DEFAULT_CENSUS_YEAR


@dataclass
class PoiConfig:
    """
    Configuration for points of interest search operations.

    Contains parameters for finding POIs near a location using OpenStreetMap
    data within either a radius or travel-time boundary.

    Parameters
    ----------
    location : str or tuple of float
        Either "City, State" string or (latitude, longitude) tuple.
    categories : list of str, optional
        POI categories to filter (e.g., ["restaurant", "school"]).
    travel_time : int, optional
        Travel time in minutes for isochrone boundary. If None, uses radius.
    limit : int, default 100
        Maximum number of POIs to return.
    validate_coords : bool, default True
        Whether to validate POI coordinates.
    """

    location: Union[str, Tuple[float, float]]
    categories: Optional[List[str]] = None
    travel_time: Optional[int] = None
    limit: int = DEFAULT_POI_LIMIT
    validate_coords: bool = True

    def __post_init__(self):
        if self.travel_time is not None:
            validate_travel_time(self.travel_time)


@dataclass
class MapConfig:
    """
    Configuration for choropleth map creation operations.

    Contains parameters for generating thematic maps from geographic data
    with support for multiple output formats.

    Parameters
    ----------
    data : list of dict, DataFrame, or GeoDataFrame
        Geographic data to visualize with 'geometry' field and data columns.
    column : str
        Name of the data column to use for choropleth coloring.
    title : str, optional
        Map title. If None, auto-generates from column name.
    save_path : str, optional
        File path for saving map. If None, returns map data.
    export_format : {'png', 'pdf', 'svg', 'geojson', 'shapefile'}, default 'png'
        Output format for the map.
    """

    data: Union[List[Dict], Any]  # pandas/geopandas types
    column: str
    title: Optional[str] = None
    save_path: Optional[str] = None
    export_format: str = DEFAULT_EXPORT_FORMAT

    def __post_init__(self):
        validate_export_format(self.export_format)


@dataclass
class MultipleAnalysisConfig:
    """Configuration for multiple location analysis."""

    locations: List[Union[str, Tuple[float, float]]]
    travel_time: int = 15
    travel_mode: str = "drive"
    variables: List[str] = None
    compare: bool = True

    def __post_init__(self):
        if self.variables is None:
            self.variables = ["population"]


@dataclass
class ReportConfig:
    """
    Configuration for analysis report generation.

    Contains parameters for creating formatted reports from SocialMapper
    analysis data in HTML or PDF format.

    Parameters
    ----------
    analysis_data : dict
        Analysis results from API functions containing isochrone, census,
        and POI data.
    format : {'html', 'pdf'}, default 'html'
        Output format for the report.
    template : str, default 'default'
        Report template name.
    include_maps : bool, default True
        Whether to include map visualizations in the report.
    """

    analysis_data: Dict[str, Any]
    format: str = "html"
    template: str = "default"
    include_maps: bool = True

    def __post_init__(self):
        validate_report_format(self.format)