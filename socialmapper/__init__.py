"""SocialMapper: Simple spatial analysis API.

Core functions for all your spatial analysis needs:
- create_isochrone: Generate travel-time polygons
- get_census_blocks: Fetch census block groups for an area
- get_census_data: Get demographic data from US Census
- create_map: Generate choropleth map visualizations
- get_poi: Find points of interest near locations
- analyze_multiple_pois: Compare demographics across locations
- generate_report: Create analysis reports
- import_poi_csv: Import POIs from CSV files
- measure_isolation: Compute composite isolation scores
"""

# Import core API functions
from .api import (
    analyze_multiple_pois,
    create_isochrone,
    create_map,
    generate_report,
    get_census_blocks,
    get_census_data,
    get_poi,
    import_poi_csv,
    measure_isolation,
)

# Import result types
from .api_result_types import (
    CensusBlock,
    CensusDataResult,
    ClosureScenario,
    DiscoveredPOI,
    IsochroneResult,
    IsolationResult,
    MapResult,
    NearbyPOIResult,
    ReportResult,
    ServiceAccessDetail,
    ServiceBreakdown,
)

# Import exceptions
from .exceptions import (
    AnalysisError,
    APIError,
    # Legacy aliases
    ConfigurationError,
    DataError,
    DataProcessingError,
    ExternalAPIError,
    FileSystemError,
    # Helpful specific exceptions
    InvalidAPIResponseError,
    InvalidLocationError,
    InvalidPOICategoryError,
    MissingAPIKeyError,
    NetworkError,
    RateLimitError,
    SocialMapperError,
    ValidationError,
    VisualizationError,
)

# Version
__version__ = "1.1.2"

# Public API - core functions and exceptions (sorted alphabetically)
__all__ = [
    "APIError",
    "AnalysisError",
    "CensusBlock",
    "CensusDataResult",
    "ClosureScenario",
    "ConfigurationError",
    "DataError",
    "DataProcessingError",
    "DiscoveredPOI",
    "ExternalAPIError",
    "FileSystemError",
    "InvalidAPIResponseError",
    "InvalidLocationError",
    "InvalidPOICategoryError",
    "IsochroneResult",
    "IsolationResult",
    "MapResult",
    "MissingAPIKeyError",
    "NearbyPOIResult",
    "NetworkError",
    "RateLimitError",
    "ReportResult",
    "ServiceAccessDetail",
    "ServiceBreakdown",
    "SocialMapperError",
    "ValidationError",
    "VisualizationError",
    "analyze_multiple_pois",
    "create_isochrone",
    "create_map",
    "generate_report",
    "get_census_blocks",
    "get_census_data",
    "get_poi",
    "import_poi_csv",
    "measure_isolation",
]
