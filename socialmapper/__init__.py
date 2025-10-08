"""SocialMapper: Simple spatial analysis API.

Five core functions for all your spatial analysis needs:
- create_isochrone: Generate travel-time polygons
- get_census_blocks: Fetch census block groups for an area
- get_census_data: Get demographic data from US Census
- create_map: Generate choropleth map visualizations
- get_poi: Find points of interest near locations
"""

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import the 5 core API functions
from .api import (
    create_isochrone,
    create_map,
    get_census_blocks,
    get_census_data,
    get_poi,
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
    SocialMapperError,
    ValidationError,
    VisualizationError,
)

# Version
__version__ = "0.9.0"

# Public API - core functions and exceptions
__all__ = [
    # Core functions
    "create_isochrone",
    "get_census_blocks",
    "get_census_data",
    "create_map",
    "get_poi",
    # Core exceptions
    "SocialMapperError",
    "ValidationError",
    "APIError",
    "DataError",
    "AnalysisError",
    # Legacy aliases
    "ConfigurationError",
    "ExternalAPIError",
    "DataProcessingError",
    "FileSystemError",
    "VisualizationError",
]
