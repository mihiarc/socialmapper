"""Isochrone generation backend using Valhalla routing API.

This module provides the Valhalla backend for fast isochrone generation
using the public OpenStreetMap Valhalla instance (no API key required).

Usage
-----
>>> from socialmapper.isochrone.backends import get_backend
>>> backend = get_backend()
>>> result = backend.create_isochrone(35.7796, -78.6382, 15, "drive")

Configuration
-------------
Environment variables:

VALHALLA_URL : str
    Custom Valhalla endpoint (default: public OSM instance)
"""

from .base import BaseIsochroneBackend, IsochroneBackend, IsochroneResult
from .factory import get_backend
from .routing_api import ValhallaBackend

__all__ = [
    # Base types
    "IsochroneBackend",
    "BaseIsochroneBackend",
    "IsochroneResult",
    # Factory
    "get_backend",
    # Backend
    "ValhallaBackend",
]
