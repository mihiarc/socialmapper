"""Result types for SocialMapper API operations.

This module provides Result, Ok, and Err types for functional error handling,
along with specific result types for POI discovery operations.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar('T')
E = TypeVar('E')


class Result(Generic[T, E]):
    """A Result type that can be either Ok or Err."""

    def __init__(self):
        raise NotImplementedError("Use Ok() or Err() to create Result instances")

    def is_ok(self) -> bool:
        """Check if this is an Ok result."""
        return isinstance(self, Ok)

    def is_err(self) -> bool:
        """Check if this is an Err result."""
        return isinstance(self, Err)

    def unwrap(self) -> T:
        """Get the value if Ok, raise if Err."""
        if isinstance(self, Ok):
            return self.value
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_err(self) -> E:
        """Get the error if Err, raise if Ok."""
        if isinstance(self, Err):
            return self.error
        raise ValueError(f"Called unwrap_err on Ok: {self.value}")


@dataclass
class Ok(Result[T, E]):
    """Successful result containing a value."""

    value: T

    def __init__(self, value: T):
        self.value = value


@dataclass
class Err(Result[T, E]):
    """Error result containing an error."""

    error: E

    def __init__(self, error: E):
        self.error = error


class ErrorType(str, Enum):
    """Types of errors that can occur in the API."""

    VALIDATION = "validation"
    API_ERROR = "api_error"
    NOT_FOUND = "not_found"
    NETWORK = "network"
    PARSING = "parsing"
    CONFIGURATION = "configuration"
    INTERNAL = "internal"


@dataclass
class Error:
    """Standard error information."""

    type: ErrorType
    message: str
    details: dict[str, Any] | None = None


class DiscoveredPOI(BaseModel):
    """Information about a discovered POI."""

    osm_id: int
    name: str | None = None
    category: str
    subcategory: str | None = None
    latitude: float
    longitude: float
    distance_meters: float
    travel_time_minutes: float | None = None
    tags: dict[str, Any] = Field(default_factory=dict)
    address: str | None = None


class NearbyPOIResult(BaseModel):
    """Result of nearby POI discovery."""

    origin: dict[str, float]  # {"latitude": ..., "longitude": ...}
    travel_time_minutes: int
    travel_mode: str
    discovered_pois: list[DiscoveredPOI]
    isochrone_area_sqkm: float | None = None
    categories_found: list[str] = Field(default_factory=list)
    total_pois: int = 0
    search_radius_meters: float | None = None


class NearbyPOIDiscoveryConfig(BaseModel):
    """Configuration for nearby POI discovery."""

    location: str | dict[str, float]  # Address or {"latitude": ..., "longitude": ...}
    travel_time: int = Field(ge=1, le=60)
    travel_mode: str = "drive"
    categories: list[str] | None = None
    max_results: int = 100
    include_details: bool = True
    output_format: str = "json"
    output_file: str | None = None


class CensusDataResult(BaseModel):
    """
    Result of census data query.

    Provides a consistent structure for census data regardless of the
    query method (polygon, GEOIDs, or point location).

    Attributes
    ----------
    data : dict[str, dict[str, Any]]
        Census data organized as {geoid: {variable: value, ...}}.
        Always uses this nested structure for consistency.
    location_type : {'polygon', 'geoids', 'point'}
        Type of location used in the query for context.
    query_info : dict[str, Any]
        Additional query metadata such as year, variable names,
        and any other relevant context. Default is empty dict.

    Examples
    --------
    >>> result = CensusDataResult(
    ...     data={"060750201001": {"population": 2543, "median_income": 85000}},
    ...     location_type="point",
    ...     query_info={"year": 2023, "variables": ["population", "median_income"]}
    ... )
    >>> result.data["060750201001"]["population"]
    2543
    """

    data: dict[str, dict[str, Any]]
    location_type: Literal["polygon", "geoids", "point"]
    query_info: dict[str, Any] = Field(default_factory=dict)


class MapResult(BaseModel):
    """
    Result of map creation operation.

    Provides a consistent return type for create_map() regardless of
    the export format or whether the map is saved to disk. This ensures
    predictable return types and better type safety for API users.

    Attributes
    ----------
    format : {'png', 'pdf', 'svg', 'geojson', 'shapefile'}
        The export format used for the map.
    image_data : bytes, optional
        Raw image bytes for PNG, PDF, or SVG formats. Only
        populated when save_path is None and format is an
        image format. Default is None.
    geojson_data : dict, optional
        GeoJSON FeatureCollection dict when format is 'geojson'
        and save_path is None. Default is None.
    file_path : Path, optional
        Absolute path to the saved file when save_path is
        provided. Default is None.
    metadata : dict[str, Any]
        Additional information about the map such as column name,
        title, number of features, etc. Default is empty dict.

    Examples
    --------
    >>> # Create image map, get bytes back
    >>> result = create_map(census_blocks, "population")
    >>> result.format
    'png'
    >>> len(result.image_data)
    45231

    >>> # Create GeoJSON map, get dict back
    >>> result = create_map(census_blocks, "population",
    ...                    export_format="geojson")
    >>> result.geojson_data['type']
    'FeatureCollection'

    >>> # Save to file, get path back
    >>> result = create_map(census_blocks, "population",
    ...                    save_path="output.png")
    >>> result.file_path
    PosixPath('/absolute/path/to/output.png')

    Notes
    -----
    Exactly one of image_data, geojson_data, or file_path will be
    populated based on the export_format and save_path parameters.
    Use the format field to determine which field contains data.
    """

    format: Literal["png", "pdf", "svg", "geojson", "shapefile"]
    image_data: bytes | None = None
    geojson_data: dict | None = None
    file_path: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IsochroneResult(BaseModel):
    """
    Result of isochrone creation for travel time analysis.

    An isochrone represents the area reachable from a location
    within a specified travel time and mode of transportation.

    Parameters
    ----------
    geometry : dict
        GeoJSON geometry object representing the isochrone boundary.
        Typically a Polygon or MultiPolygon feature.
    location : str
        Human-readable location identifier or address used as the
        origin point for the isochrone calculation.
    travel_time : int
        Travel time in minutes used to generate this isochrone.
        Must be between 1 and 120 minutes.
    travel_mode : str
        Mode of transportation used for calculation.
        Common values: "drive", "walk", "bike".
    area_sq_km : float
        Total area of the isochrone in square kilometers. Useful
        for comparing accessibility across different locations.

    Examples
    --------
    >>> result = IsochroneResult(
    ...     geometry={"type": "Polygon", "coordinates": [...]},
    ...     location="Portland, OR",
    ...     travel_time=15,
    ...     travel_mode="drive",
    ...     area_sq_km=125.4
    ... )
    >>> geojson = result.to_geojson()
    >>> geojson["type"]
    'Feature'
    """

    geometry: dict
    location: str
    travel_time: int
    travel_mode: str
    area_sq_km: float

    def to_geojson(self) -> dict:
        """
        Convert isochrone result to GeoJSON Feature format.

        Returns a GeoJSON Feature with the isochrone geometry and
        all metadata as properties, suitable for visualization in
        mapping libraries or export to GIS software.

        Returns
        -------
        dict
            GeoJSON Feature with geometry and properties containing
            location, travel_time, travel_mode, and area_sq_km.

        Examples
        --------
        >>> result = IsochroneResult(
        ...     geometry={"type": "Polygon", "coordinates": [...]},
        ...     location="Portland, OR",
        ...     travel_time=15,
        ...     travel_mode="drive",
        ...     area_sq_km=125.4
        ... )
        >>> feature = result.to_geojson()
        >>> feature["properties"]["travel_time"]
        15
        """
        return {
            "type": "Feature",
            "geometry": self.geometry,
            "properties": {
                "location": self.location,
                "travel_time": self.travel_time,
                "travel_mode": self.travel_mode,
                "area_sq_km": self.area_sq_km
            }
        }


class CensusBlock(BaseModel):
    """
    Census block group information with geographic boundaries.

    Represents a single Census block group with its geographic
    identifier components and spatial geometry. Block groups are
    statistical divisions used by the U.S. Census Bureau.

    Parameters
    ----------
    geoid : str
        Full 12-character GEOID uniquely identifying this block
        group. Format: SSCCCTTTTTTB where SS=state, CCC=county,
        TTTTTT=tract, B=block group.
    state_fips : str
        2-digit FIPS code identifying the state.
    county_fips : str
        3-digit FIPS code identifying the county within the state.
    tract : str
        6-character census tract identifier.
    block_group : str
        1-character block group identifier within the tract.
    geometry : dict
        GeoJSON geometry object representing the block group
        boundary, typically a Polygon or MultiPolygon.
    area_sq_km : float
        Total area of the block group in square kilometers.

    Examples
    --------
    >>> block = CensusBlock(
    ...     geoid="530330051001",
    ...     state_fips="53",
    ...     county_fips="033",
    ...     tract="005100",
    ...     block_group="1",
    ...     geometry={"type": "Polygon", "coordinates": [...]},
    ...     area_sq_km=2.34
    ... )
    >>> block.geoid
    '530330051001'
    """

    geoid: str
    state_fips: str
    county_fips: str
    tract: str
    block_group: str
    geometry: dict
    area_sq_km: float


class ReportResult(BaseModel):
    """
    Result of report generation with format-specific content.

    Contains the generated report in the requested format along
    with optional file path and metadata about the generation
    process.

    Parameters
    ----------
    format : {"html", "pdf"}
        Output format of the generated report. HTML returns string
        content, PDF returns binary bytes.
    content : str or bytes
        The report content. Type depends on format:
        - "html": str containing HTML markup
        - "pdf": bytes containing PDF binary data
    file_path : Path, optional
        Path where the report was saved, if applicable.
        None if report was not saved to disk.
    metadata : dict, optional
        Additional metadata about report generation including
        timestamp, template used, data sources, etc.
        Default is empty dict.

    Examples
    --------
    >>> report = ReportResult(
    ...     format="html",
    ...     content="<html><body>Report content</body></html>",
    ...     metadata={"generated_at": "2025-01-05T10:30:00"}
    ... )
    >>> report.format
    'html'

    >>> pdf_report = ReportResult(
    ...     format="pdf",
    ...     content=b"%PDF-1.4...",
    ...     file_path=Path("/reports/analysis.pdf"),
    ...     metadata={"pages": 5}
    ... )
    >>> isinstance(pdf_report.content, bytes)
    True
    """

    format: Literal["html", "pdf"]
    content: str | bytes
    file_path: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# API Request Validation Models
# ============================================================================


class IsochroneRequest(BaseModel):
    """
    Request parameters for isochrone creation.

    An isochrone represents all locations reachable within a
    specified travel time from a starting point using a specific
    mode of transportation. This model validates and structures
    the input parameters for isochrone generation.

    Parameters
    ----------
    location : str or tuple of float
        The starting location for the isochrone. Can be either:
        - A string address (e.g., "Portland, OR")
        - A tuple of (latitude, longitude) coordinates
    travel_time : int, default=15
        Maximum travel time in minutes from the origin point.
        Must be between 1 and 120 minutes inclusive.
    travel_mode : {'drive', 'walk', 'bike'}, default='drive'
        Mode of transportation for calculating travel times.
        Must be one of: 'drive', 'walk', or 'bike'.

    Examples
    --------
    >>> request = IsochroneRequest(
    ...     location="Portland, OR",
    ...     travel_time=20,
    ...     travel_mode="drive"
    ... )
    >>> request.travel_time
    20

    >>> request = IsochroneRequest(
    ...     location=(45.5152, -122.6784),
    ...     travel_time=30
    ... )
    >>> request.location
    (45.5152, -122.6784)
    """

    location: str | tuple[float, float]
    travel_time: int = Field(ge=1, le=120, default=15)
    travel_mode: Literal["drive", "walk", "bike"] = "drive"


class CensusBlocksRequest(BaseModel):
    """
    Request parameters for census blocks query.

    Census blocks are retrieved either within a polygon boundary
    or within a radius from a central point. These parameters are
    mutually exclusive - only one location method can be specified.

    Parameters
    ----------
    polygon : dict, optional
        GeoJSON Feature or geometry dict defining search boundary.
        If provided, all census blocks intersecting this polygon
        will be returned. Mutually exclusive with location.
    location : tuple of float, optional
        Center point as (latitude, longitude) for radial search.
        Must be provided if polygon is None. Mutually exclusive
        with polygon parameter.
    radius_km : float, default=5
        Search radius in kilometers from location point.
        Must be greater than 0 and less than or equal to 100 km.
        Only used when location is provided, ignored if polygon
        is specified.

    Raises
    ------
    ValueError
        If neither polygon nor location is provided.
    ValueError
        If both polygon and location are provided.

    Examples
    --------
    >>> request = CensusBlocksRequest(
    ...     location=(45.5152, -122.6784),
    ...     radius_km=10
    ... )
    >>> request.radius_km
    10

    >>> polygon = {"type": "Polygon", "coordinates": [...]}
    >>> request = CensusBlocksRequest(polygon=polygon)
    >>> request.polygon is not None
    True
    """

    polygon: dict | None = None
    location: tuple[float, float] | None = None
    radius_km: float = Field(gt=0, le=100, default=5)

    @model_validator(mode='after')
    def validate_exclusive_location(self):
        """
        Validate that exactly one location method is provided.

        Ensures that either polygon or location is specified,
        but not both and not neither.

        Returns
        -------
        self : CensusBlocksRequest
            The validated model instance.

        Raises
        ------
        ValueError
            If validation constraints are violated.
        """
        if self.polygon is None and self.location is None:
            raise ValueError("Must provide either polygon or location")
        if self.polygon is not None and self.location is not None:
            raise ValueError(
                "Provide either polygon or location, not both"
            )
        return self


class CensusDataRequest(BaseModel):
    """
    Request parameters for census data query.

    Fetches census demographic and economic data for one or more
    geographic areas. Supports multiple location specification
    methods including coordinates, GEOIDs, and polygon boundaries.

    Parameters
    ----------
    location : dict or list of str or tuple of float
        Location specification in one of three formats:
        - dict: GeoJSON Feature or geometry defining area
        - list of str: Census GEOIDs for specific block groups
        - tuple of float: (latitude, longitude) for point query
    variables : list of str
        Census variable codes to retrieve (e.g., ['B01001_001E']).
        Must contain at least one variable. See Census API
        documentation for available variable codes.
    year : int, default=2023
        Census data year to query. Must be between 2010 and 2023
        inclusive. Not all variables are available for all years.

    Examples
    --------
    >>> request = CensusDataRequest(
    ...     location=(45.5152, -122.6784),
    ...     variables=['B01001_001E', 'B19013_001E'],
    ...     year=2023
    ... )
    >>> len(request.variables)
    2

    >>> request = CensusDataRequest(
    ...     location=['410510100001', '410510100002'],
    ...     variables=['B01001_001E']
    ... )
    >>> isinstance(request.location, list)
    True
    """

    location: dict | list[str] | tuple[float, float]
    variables: list[str] = Field(min_length=1)
    year: int = Field(ge=2010, le=2023, default=2023)


class MapRequest(BaseModel):
    """
    Request parameters for map creation.

    Creates a choropleth or thematic map visualizing data across
    geographic areas. Supports multiple export formats and
    optional saving to disk.

    Parameters
    ----------
    column : str
        Name of the data column to visualize on the map.
        Must exist in the provided data.
    title : str, optional
        Title to display on the map. If None, a default title
        will be generated based on the column name.
    save_path : Path, optional
        Filesystem path where the map should be saved.
        If None, the map is returned in memory without saving.
    export_format : {'png', 'pdf', 'svg', 'geojson', 'shapefile'}
        Output format for the map. Default is 'png'.
        - 'png', 'pdf', 'svg': Raster/vector image formats
        - 'geojson': GeoJSON feature collection
        - 'shapefile': ESRI Shapefile (zipped)

    Examples
    --------
    >>> request = MapRequest(
    ...     column="total_population",
    ...     title="Population Density",
    ...     export_format="png"
    ... )
    >>> request.column
    'total_population'

    >>> from pathlib import Path
    >>> request = MapRequest(
    ...     column="median_income",
    ...     save_path=Path("/tmp/income_map.pdf"),
    ...     export_format="pdf"
    ... )
    >>> request.save_path.name
    'income_map.pdf'
    """

    column: str
    title: str | None = None
    save_path: Path | None = None
    export_format: Literal[
        "png", "pdf", "svg", "geojson", "shapefile"
    ] = "png"


class POIRequest(BaseModel):
    """
    Request parameters for Point of Interest (POI) query.

    Discovers points of interest (businesses, amenities, landmarks)
    near a location, optionally filtered by category and travel
    time accessibility.

    Parameters
    ----------
    location : str or tuple of float
        Location to search near. Can be either:
        - A string address (e.g., "Seattle, WA")
        - A tuple of (latitude, longitude) coordinates
    categories : list of str, optional
        OpenStreetMap amenity categories to filter by
        (e.g., ['restaurant', 'cafe', 'hospital']).
        If None, all POI categories are included.
    travel_time : int, optional
        Maximum travel time in minutes from the location.
        If provided, only POIs reachable within this time
        are returned. Must be between 1 and 120 minutes.
        If None, uses simple distance-based search.
    limit : int, default=100
        Maximum number of POIs to return. Must be between
        1 and 1000 inclusive. Results are sorted by distance.
    validate_coords : bool, default=True
        Whether to validate that coordinates are within valid
        latitude/longitude ranges. Disable for performance if
        coordinates are known to be valid.

    Examples
    --------
    >>> request = POIRequest(
    ...     location="Portland, OR",
    ...     categories=['restaurant', 'cafe'],
    ...     limit=50
    ... )
    >>> len(request.categories)
    2

    >>> request = POIRequest(
    ...     location=(47.6062, -122.3321),
    ...     travel_time=15,
    ...     limit=200
    ... )
    >>> request.travel_time
    15
    """

    location: str | tuple[float, float]
    categories: list[str] | None = None
    travel_time: int | None = Field(None, ge=1, le=120)
    limit: int = Field(default=100, ge=1, le=1000)
    validate_coords: bool = True
