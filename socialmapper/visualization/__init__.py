"""Visualization module for creating static chloropleth maps."""

from .chloropleth import ChoroplethMap, MapType
from .config import ColorScheme, MapConfig

__all__ = ["ChoroplethMap", "MapType", "MapConfig", "ColorScheme"]