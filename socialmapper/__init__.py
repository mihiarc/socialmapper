"""SocialMapper: Simple spatial analysis API.

Five core functions for all your spatial analysis needs:
- create_isochrone: Generate travel-time polygons
- get_census_blocks: Fetch census block groups for an area
- get_census_data: Get demographic data from US Census
- create_map: Generate choropleth map visualizations
- get_poi: Find points of interest near locations

New to SocialMapper? Try the demo module first:
    >>> from socialmapper import demo
    >>> demo.quick_start("Portland, OR")
"""

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import the 5 core API functions
# Import demo module for easy onboarding
from . import demo
from .api import (
    create_isochrone,
    create_map,
    get_census_blocks,
    get_census_data,
    get_poi,
)

# Import result types
from .api_result_types import (
    CensusBlock,
    CensusBlocksRequest,
    CensusDataRequest,
    CensusDataResult,
    DiscoveredPOI,
    IsochroneRequest,
    IsochroneResult,
    MapRequest,
    MapResult,
    NearbyPOIResult,
    POIRequest,
    ReportResult,
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
__version__ = "1.1.1"

# Public API - core functions and exceptions (sorted alphabetically)
__all__ = [
    "APIError",
    "AnalysisError",
    "CensusBlock",
    "CensusBlocksRequest",
    "CensusDataRequest",
    "CensusDataResult",
    "ConfigurationError",
    "DataError",
    "DataProcessingError",
    "DiscoveredPOI",
    "ExternalAPIError",
    "FileSystemError",
    "InvalidAPIResponseError",
    "InvalidLocationError",
    "InvalidPOICategoryError",
    "IsochroneRequest",
    "IsochroneResult",
    "MapRequest",
    "MapResult",
    "MissingAPIKeyError",
    "NearbyPOIResult",
    "NetworkError",
    "POIRequest",
    "RateLimitError",
    "ReportResult",
    "SocialMapperError",
    "ValidationError",
    "VisualizationError",
    "create_isochrone",
    "create_map",
    "demo",
    "get_census_blocks",
    "get_census_data",
    "get_poi",
]
