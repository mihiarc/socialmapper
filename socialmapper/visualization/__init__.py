"""Visualization module for creating static choropleth maps.

Simplified interface - pass parameters directly instead of using config objects.
"""

from .chloropleth import ChoroplethMap, MapType
from .config import (
    ColorScheme,  # Deprecated - raises helpful error
    ClassificationScheme,  # Deprecated - raises helpful error
    MapConfig,  # Deprecated - raises helpful error
)

__all__ = [
    "ChoroplethMap",
    "MapType",
    # Deprecated classes kept for backward compatibility (raise errors)
    "ColorScheme",
    "ClassificationScheme",
    "MapConfig",
]
