"""SocialMapper: Backend Toolkit for Spatial Analysis.

An open-source Python backend toolkit for spatial analysis, demographic mapping,
and geospatial data processing. Provides APIs and services for community mapping.
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
    __version__ = "0.9.0"  # fallback version from pyproject.toml

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

# Import simple API (recommended, new in v0.9.0)
try:
    from .simple_api import (
        SocialMapper,
        AnalysisResult,
        POIResult,
        SocialMapperError as SimpleError,
        ValidationError as SimpleValidationError,
        AnalysisError as SimpleAnalysisError,
        APIError as SimpleAPIError,
        quick_analysis,
        analyze_libraries,
        analyze_schools,
        analyze_hospitals, 
        analyze_parks,
        discover_food_access,
        discover_healthcare_access,
        compare_locations,
        analyze_custom_pois,
    )
    _SIMPLE_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Simple API not available: {e}")
    _SIMPLE_API_AVAILABLE = False

# Import legacy complex API (deprecated)
import warnings
try:
    from .api import (
        Err,
        Ok,
        Result,
        SocialMapperBuilder,
        SocialMapperClient,
        analyze_location as legacy_analyze_location,
    )
    
    # Add deprecation warning for complex API usage
    _original_client_init = SocialMapperClient.__init__
    def _deprecated_client_init(self, *args, **kwargs):
        warnings.warn(
            "SocialMapperClient is deprecated. Use the simpler 'SocialMapper' class instead:\n"
            "  from socialmapper import SocialMapper\n"
            "  mapper = SocialMapper()\n" 
            "  result = mapper.analyze_location('City, State', poi_types=['library'])",
            DeprecationWarning,
            stacklevel=2
        )
        return _original_client_init(self, *args, **kwargs)
    SocialMapperClient.__init__ = _deprecated_client_init

    _LEGACY_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Legacy API not available: {e}")
    _LEGACY_API_AVAILABLE = False

# Import modern census system
from .census import (
    CacheStrategy,
    CensusSystem,
    CensusSystemBuilder,
    RepositoryType,
    StateFormat,
    VariableFormat,
    get_census_system,
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

# Import backend configuration
from .config.feature_flags import (
    BackendConfig,
    get_api_base_url,
    get_backend_config,
    get_runtime_config,
)

# Import error handling components
from .exceptions import (
    AnalysisError,
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
    # Specific errors
    MissingAPIKeyError,
    NetworkAnalysisError,
    NoDataFoundError,
    OSMAPIError,
    SocialMapperError,
    ValidationError,
    VisualizationError,
    # Helper functions
    format_error_for_user,
    handle_with_context,
)

# Import tutorial helpers
from .tutorial_helper import tutorial_error_handler

# Import NLP module if available
try:
    from .nlp import (
        EntityExtractor,
        EntityType,
        IntentClassifier,
        NLQueryProcessor,
        QueryIntent,
        QueryTranslator,
    )
    _NLP_AVAILABLE = True
except ImportError:
    _NLP_AVAILABLE = False

# Build __all__ based on available features
__all__ = [
    # Tutorial helpers
    "tutorial_error_handler",
]

# Add simple API items (recommended)
if _SIMPLE_API_AVAILABLE:
    __all__.extend(
        [
            # Simple API (primary interface)
            "SocialMapper",
            "AnalysisResult", 
            "POIResult",
            "quick_analysis",
            "analyze_libraries",
            "analyze_schools", 
            "analyze_hospitals",
            "analyze_parks",
            "discover_food_access",
            "discover_healthcare_access",
            "compare_locations",
            "analyze_custom_pois",
            # Simple API exceptions
            "SimpleError",
            "SimpleValidationError",
            "SimpleAnalysisError",
            "SimpleAPIError",
        ]
    )

# Add legacy API items (deprecated)
if _LEGACY_API_AVAILABLE:
    __all__.extend(
        [
            # Legacy complex API (deprecated)
            "SocialMapperClient",
            "SocialMapperBuilder", 
            "Err",
            "Ok",
            "Result",
            "legacy_analyze_location",
        ]
    )

# Add core infrastructure
__all__.extend([
    # Backend configuration
    "BackendConfig",
    "get_api_base_url",
    "get_backend_config", 
    "get_runtime_config",
    # Census system
    "CensusSystem",
    "CensusSystemBuilder",
    "get_census_system",
    "CacheStrategy",
    "RepositoryType",
    "StateFormat",
    "VariableFormat",
    # Geography functions
    "get_geography_from_point",
    "get_counties_from_pois",
    # Error handling (legacy)
    "SocialMapperError",
    "ValidationError",
    "CensusAPIError",
    "ConfigurationError",
    "DataProcessingError",
    "ExternalAPIError",
    "InvalidLocationError",
    "MissingAPIKeyError",
    "NoDataFoundError", 
    "OSMAPIError",
])

# Add visualization items if available
if _VISUALIZATION_AVAILABLE:
    __all__.extend(
        [
            "ChoroplethMap",
            "ColorScheme",
            "MapConfig",
            "MapType",
        ]
    )

# Add NLP items if available
if _NLP_AVAILABLE:
    __all__.extend(
        [
            "EntityExtractor",
            "EntityType",
            "IntentClassifier",
            "NLQueryProcessor",
            "QueryIntent",
            "QueryTranslator",
        ]
    )
