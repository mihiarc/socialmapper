"""Isochrone generation backends.

This module provides multiple backends for isochrone generation, allowing
users to choose between fast API-based backends and offline-capable local
computation.

Available Backends
------------------
networkx : Local NetworkX/OSMnx backend
    Uses OpenStreetMap data and graph algorithms locally.
    Slower (3-15 seconds) but works offline after network download.

valhalla : Valhalla routing API backend
    Uses public Valhalla instance (no API key required).
    Fast (0.5-2 seconds), recommended for most use cases.

ors : OpenRouteService API backend
    Requires free API key (ORS_API_KEY environment variable).
    Fast and high quality isochrones.

osrm : Mapbox OSRM API backend
    Requires Mapbox API key (MAPBOX_API_KEY environment variable).
    Fast isochrone generation.

graphhopper : GraphHopper API backend
    Requires free API key (GRAPHHOPPER_API_KEY environment variable).
    Fast and supports multiple travel modes.

Usage
-----
>>> from socialmapper.isochrone.backends import get_backend
>>> backend = get_backend("valhalla")  # Use specific backend
>>> result = backend.create_isochrone(35.7796, -78.6382, 15, "drive")

>>> # Auto-select best available backend
>>> backend = get_backend("auto")

>>> # List available backends
>>> from socialmapper.isochrone.backends import list_available_backends
>>> print(list_available_backends())
['valhalla', 'networkx']

Configuration
-------------
Environment variables for backend configuration:

SOCIALMAPPER_ROUTING_BACKEND : str
    Default backend selection ("auto", "valhalla", "ors", etc.)

VALHALLA_URL : str
    Custom Valhalla endpoint (default: public OSM instance)

ORS_API_KEY : str
    OpenRouteService API key (for ORS backend)

MAPBOX_API_KEY : str
    Mapbox API key (for OSRM backend)

GRAPHHOPPER_API_KEY : str
    GraphHopper API key (for GraphHopper backend)
"""

from .base import BaseIsochroneBackend, IsochroneBackend, IsochroneResult
from .factory import (
    get_backend,
    get_backend_info,
    list_available_backends,
)
from .networkx_backend import NetworkXBackend
from .routing_api import (
    GraphHopperBackend,
    ORSBackend,
    OSRMBackend,
    ValhallaBackend,
)

__all__ = [
    # Base types
    "IsochroneBackend",
    "BaseIsochroneBackend",
    "IsochroneResult",
    # Factory functions
    "get_backend",
    "list_available_backends",
    "get_backend_info",
    # Backend implementations
    "NetworkXBackend",
    "ValhallaBackend",
    "ORSBackend",
    "OSRMBackend",
    "GraphHopperBackend",
]
