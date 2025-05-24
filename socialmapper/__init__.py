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

# Import main functionality
from .core import run_socialmapper, setup_directory

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
    
    __all__ = [
        "run_socialmapper",
        "setup_directory",
        # Neighbor functions
        "get_neighboring_states",
        "get_neighboring_counties", 
        "get_geography_from_point",
        "get_counties_from_pois",
        "get_neighbor_manager",
    ]
    
except ImportError as e:
    # Neighbor functionality not available (optional dependency missing)
    _NEIGHBORS_AVAILABLE = False
    
    __all__ = [
        "run_socialmapper",
        "setup_directory",
    ] 