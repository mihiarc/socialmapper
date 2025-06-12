"""
SocialMapper: Explore Community Connections.

An open-source Python toolkit that helps understand 
community connections through mapping demographics and access to points of interest.
"""

from importlib.metadata import version, PackageNotFoundError

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
        SocialMapperClient,
        SocialMapperBuilder,
        quick_analysis,
        analyze_location,
        Result,
        Ok,
        Err,
    )
    _MODERN_API_AVAILABLE = True
except ImportError:
    _MODERN_API_AVAILABLE = False

# Import neighbor functionality for direct access
try:
    from .census import (
        get_neighboring_states,
        get_neighboring_counties,
        get_geography_from_point,
        get_counties_from_pois,
        get_neighbor_manager
    )
    
    # Neighbor functionality is available
    _NEIGHBORS_AVAILABLE = True
    
    # Build __all__ based on available features
    __all__ = [
        "run_socialmapper",  # Deprecated - use SocialMapperClient instead
        # Neighbor functions
        "get_neighboring_states",
        "get_neighboring_counties", 
        "get_geography_from_point",
        "get_counties_from_pois",
        "get_neighbor_manager",
    ]
    
    # Add modern API if available
    if _MODERN_API_AVAILABLE:
        __all__.extend([
            # Modern API (recommended)
            "SocialMapperClient",
            "SocialMapperBuilder",
            "quick_analysis",
            "analyze_location",
            "Result",
            "Ok",
            "Err",
        ])
    
except ImportError as e:
    # Neighbor functionality not available (optional dependency missing)
    _NEIGHBORS_AVAILABLE = False
    
    # Build __all__ for limited functionality
    __all__ = [
        "run_socialmapper",  # Deprecated - use SocialMapperClient instead
    ]
    
    # Add modern API if available
    if _MODERN_API_AVAILABLE:
        __all__.extend([
            # Modern API (recommended)
            "SocialMapperClient",
            "SocialMapperBuilder",
            "quick_analysis",
            "analyze_location",
            "Result",
            "Ok",
            "Err",
        ]) 