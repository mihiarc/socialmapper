"""
SocialMapper: Explore Community Connections.

An open-source Python toolkit that helps understand
community connections through mapping demographics and access to points of interest.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("socialmapper")
except PackageNotFoundError:
    # Package is not installed
    try:
        from . import _version

        __version__ = _version.__version__
    except (ImportError, AttributeError):
        __version__ = "0.3.0-alpha"  # fallback

# Configure warnings for clean user experience
# This automatically handles known deprecation warnings from geospatial libraries
try:
    from .util.warnings_config import setup_production_environment

    setup_production_environment(verbose=False)
except ImportError:
    # Warnings config not available - continue without it
    pass

# Import main functionality (deprecated - use api module instead)
from .core import run_socialmapper

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
except ImportError:
    _MODERN_API_AVAILABLE = False

# Import modern census system instead of old one
from .census_modern import (
    get_census_system,
    get_legacy_adapter,
    CensusSystem,
    CensusSystemBuilder,
    StateFormat,
    VariableFormat,
    CacheStrategy,
    RepositoryType
)

# Import neighbor functionality for direct access
try:
    from .census_modern.infrastructure.geocoder import CensusGeocoder
    from .census_modern.services.geography_service import GeographyService
    
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

# Build __all__ based on available features
__all__ = [
    "run_socialmapper",  # Deprecated - use SocialMapperClient instead
    # Modern census system
    "get_census_system",
    "get_legacy_adapter", 
    "CensusSystem",
    "CensusSystemBuilder",
    "StateFormat",
    "VariableFormat",
    "CacheStrategy",
    "RepositoryType",
    # Neighbor functions
    "get_geography_from_point",
    "get_counties_from_pois",
]

# Add modern API if available
if _MODERN_API_AVAILABLE:
    __all__.extend(
        [
            # Modern API (recommended)
            "SocialMapperClient",
            "SocialMapperBuilder",
            "quick_analysis",
            "analyze_location",
            "Result",
            "Ok",
            "Err",
        ]
    )
