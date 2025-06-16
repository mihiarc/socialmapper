"""TIGER geometry fetching submodule.

This submodule provides a unified interface for fetching geometries from the
US Census TIGER REST API for various geographic levels including counties,
block groups, and ZCTAs (ZIP Code Tabulation Areas).
"""

from .client import TigerGeometryClient
from .models import GeographyLevel, GeometryQuery, GeometryResult

__all__ = [
    "GeographyLevel",
    "GeometryQuery",
    "GeometryResult",
    "TigerGeometryClient",
]
