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
__version__ = "1.0.0"

# Public API - core functions and exceptions
__all__ = [
    # Core functions
    "create_isochrone",
    "get_census_blocks",
    "get_census_data",
    "create_map",
    "get_poi",
    # Demo module for easy onboarding
    "demo",
    # Result types
    "MapResult",
    "CensusDataResult",
    "IsochroneResult",
    "CensusBlock",
    "DiscoveredPOI",
    "NearbyPOIResult",
    "ReportResult",
    # Request types
    "MapRequest",
    "CensusDataRequest",
    "CensusBlocksRequest",
    "IsochroneRequest",
    "POIRequest",
    # Core exceptions
    "SocialMapperError",
    "ValidationError",
    "APIError",
    "DataError",
    "AnalysisError",
    # Helpful specific exceptions
    "MissingAPIKeyError",
    "InvalidLocationError",
    "InvalidPOICategoryError",
    "NetworkError",
    "RateLimitError",
    "InvalidAPIResponseError",
    # Legacy aliases
    "ConfigurationError",
    "ExternalAPIError",
    "DataProcessingError",
    "FileSystemError",
    "VisualizationError",
]
