"""SocialMapper: Explore Community Connections.

An open-source Python toolkit that helps understand
community connections through mapping demographics and access to points of interest.
"""

# Load environment variables from .env file as early as possible
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

# Configure logging for the package (defaults to CRITICAL level)
try:
    from .util.logging_config import configure_logging

    configure_logging()
except ImportError:
    # Logging config not available - continue without it
    pass

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("socialmapper")
except PackageNotFoundError:
    # Package is not installed, use fallback
    __version__ = "0.5.4"  # fallback version from pyproject.toml

# Configure warnings for clean user experience
# This automatically handles known deprecation warnings from geospatial libraries
try:
    from .util.warnings_config import setup_production_environment

    setup_production_environment(verbose=False)
except ImportError:
    # Warnings config not available - continue without it
    pass

# Core module is deprecated - use api module instead

# Note: setup_directory removed from exports - use internal modules directly

# Import modern API (recommended)
try:
    from .api import (
        Err,
        Ok,
        Result,
        SocialMapperBuilder,
        SocialMapperClient,
        analyze_location,
        quick_analysis,
    )

    _MODERN_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Modern API not available: {e}")
    _MODERN_API_AVAILABLE = False

# Import modern census system
from .census import (
    CacheStrategy,
    CensusSystem,
    CensusSystemBuilder,
    RepositoryType,
    StateFormat,
    VariableFormat,
    get_census_system,
    get_legacy_adapter,
)

# Import neighbor functionality for direct access
try:
    from .census.infrastructure.geocoder import CensusGeocoder
    from .census.services.geography_service import GeographyService

    # Create a default geography service for neighbor operations
    def get_geography_from_point(lat: float, lon: float):
        """Get geographic identifiers for a point using modern system."""
        census_system = get_census_system()
        return census_system.get_geography_from_point(lat, lon)

    def get_counties_from_pois(pois, include_neighbors: bool = True):
        """Get counties for POIs using modern system."""
        census_system = get_census_system()
        return census_system.get_counties_from_pois(pois, include_neighbors)

    _NEIGHBOR_FUNCTIONS_AVAILABLE = True
except ImportError:
    _NEIGHBOR_FUNCTIONS_AVAILABLE = False

# Import visualization module
try:
    from .visualization import ChoroplethMap, ColorScheme, MapConfig, MapType

    _VISUALIZATION_AVAILABLE = True
except ImportError:
    _VISUALIZATION_AVAILABLE = False

# Import error handling components
from .exceptions import (
    SocialMapperError,
    ConfigurationError,
    ValidationError,
    DataProcessingError,
    ExternalAPIError,
    FileSystemError,
    AnalysisError,
    VisualizationError,
    # Specific errors
    MissingAPIKeyError,
    InvalidLocationError,
    InvalidCensusVariableError,
    InvalidTravelTimeError,
    NoDataFoundError,
    CensusAPIError,
    OSMAPIError,
    GeocodingError,
    IsochroneGenerationError,
    NetworkAnalysisError,
    MapGenerationError,
    # Helper functions
    format_error_for_user,
    handle_with_context,
)

# Import tutorial helpers
from .tutorial_helper import tutorial_error_handler

# Build __all__ based on available features
__all__ = [
    "CacheStrategy",
    "CensusSystem",
    "CensusSystemBuilder",
    "RepositoryType",
    "StateFormat",
    "VariableFormat",
    # Modern census system
    "get_census_system",
    "get_counties_from_pois",
    # Neighbor functions
    "get_geography_from_point",
    "get_legacy_adapter",
    # Error handling
    "SocialMapperError",
    "ConfigurationError", 
    "ValidationError",
    "DataProcessingError",
    "ExternalAPIError",
    "MissingAPIKeyError",
    "InvalidLocationError",
    "NoDataFoundError",
    "CensusAPIError",
    "OSMAPIError",
    "tutorial_error_handler",
]

# Add API items if available
if _MODERN_API_AVAILABLE:
    __all__.extend([
        "Err",
        "Ok",
        "Result",
        "SocialMapperBuilder",
        # Modern API (primary interface)
        "SocialMapperClient",
        "analyze_location",
        "quick_analysis",
    ])

# Add visualization items if available
if _VISUALIZATION_AVAILABLE:
    __all__.extend([
        "ChoroplethMap",
        "ColorScheme",
        "MapConfig",
        "MapType",
    ])
