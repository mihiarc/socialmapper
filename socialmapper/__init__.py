"""SocialMapper: Backend Toolkit for Spatial Analysis.

An open-source Python backend toolkit for spatial analysis, demographic mapping,
and geospatial data processing. Clean, Pythonic API for community mapping.
"""

# Load environment variables from .env file as early as possible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

# Configure logging and warnings for clean user experience
try:
    from .util.logging_config import configure_logging
    configure_logging()
except ImportError:
    pass

try:
    from .util.warnings_config import setup_production_environment
    setup_production_environment(verbose=False)
except ImportError:
    pass

# Version information
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("socialmapper")
except PackageNotFoundError:
    __version__ = "1.0.0"  # Major version for API consolidation

# Main API - Simple, Pythonic interface
from .api import (
    AnalysisError,
    AnalysisResult,
    APIError,
    POIResult,
    SocialMapper,
    SocialMapperError,
    ValidationError,
    analyze_custom_pois,
    analyze_hospitals,
    analyze_libraries,
    analyze_parks,
    analyze_schools,
    compare_locations,
    discover_food_access,
    discover_healthcare_access,
    quick_analysis,
)

# Census system infrastructure
from .census import (
    CacheStrategy,
    CensusSystem,
    CensusSystemBuilder,
    RepositoryType,
    StateFormat,
    VariableFormat,
    get_census_system,
)

# Geography utilities
try:
    from .census.infrastructure.geocoder import CensusGeocoder
    from .census.services.geography_service import GeographyService

    def get_geography_from_point(lat: float, lon: float):
        """Get geographic identifiers for a point."""
        census_system = get_census_system()
        return census_system.get_geography_from_point(lat, lon)

    def get_counties_from_pois(pois, include_neighbors: bool = True):
        """Get counties for POIs."""
        census_system = get_census_system()
        return census_system.get_counties_from_pois(pois, include_neighbors)

except ImportError:
    pass

# Visualization (optional)
try:
    from .visualization import ChoroplethMap, ColorScheme, MapConfig, MapType
    _VISUALIZATION_AVAILABLE = True
except ImportError:
    _VISUALIZATION_AVAILABLE = False

# Backend configuration
from .config.feature_flags import (
    BackendConfig,
    get_api_base_url,
    get_backend_config,
    get_runtime_config,
)

# Error handling infrastructure
from .exceptions import (
    AnalysisError as LegacyAnalysisError,
)
from .exceptions import (
    CensusAPIError,
    ConfigurationError,
    DataProcessingError,
    ExternalAPIError,
    FileSystemError,
    GeocodingError,
    InvalidCensusVariableError,
    InvalidLocationError,
    InvalidTravelTimeError,
    IsochroneGenerationError,
    MapGenerationError,
    MissingAPIKeyError,
    NetworkAnalysisError,
    NoDataFoundError,
    OSMAPIError,
    VisualizationError,
    format_error_for_user,
    handle_with_context,
)
from .exceptions import (
    SocialMapperError as LegacySocialMapperError,
)
from .exceptions import (
    ValidationError as LegacyValidationError,
)

# Tutorial helpers
from .tutorial_helper import tutorial_error_handler


# Public API
__all__ = [
    # Core API
    "SocialMapper",
    "AnalysisResult",
    "POIResult",
    # Exceptions
    "SocialMapperError",
    "ValidationError",
    "AnalysisError",
    "APIError",
    # Convenience functions
    "quick_analysis",
    "analyze_libraries",
    "analyze_schools",
    "analyze_hospitals",
    "analyze_parks",
    "discover_food_access",
    "discover_healthcare_access",
    "compare_locations",
    "analyze_custom_pois",
    # Census system
    "CensusSystem",
    "CensusSystemBuilder",
    "get_census_system",
    "CacheStrategy",
    "RepositoryType",
    "StateFormat",
    "VariableFormat",
    # Geography utilities
    "get_geography_from_point",
    "get_counties_from_pois",
    # Configuration
    "BackendConfig",
    "get_api_base_url",
    "get_backend_config",
    "get_runtime_config",
    # Legacy error handling
    "LegacyAnalysisError",
    "CensusAPIError",
    "ConfigurationError",
    "DataProcessingError",
    "ExternalAPIError",
    "InvalidLocationError",
    "MissingAPIKeyError",
    "NoDataFoundError",
    "OSMAPIError",
    # Tutorial helpers
    "tutorial_error_handler",
]

# Add optional components
if _VISUALIZATION_AVAILABLE:
    __all__.extend([
        "ChoroplethMap",
        "ColorScheme",
        "MapConfig",
        "MapType",
    ])
