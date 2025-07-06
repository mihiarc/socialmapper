"""Centralized I/O module for SocialMapper.

This module handles all file input/output operations including:
- Reading POI data from various formats
- Writing analysis results
- Managing output directories
- Handling map files
- Tracking generated files
"""

from .manager import IOManager, OutputTracker
from .readers import read_poi_data, read_custom_pois
from .writers import (
    write_csv,
    write_geojson,
    write_geoparquet,
    write_parquet,
    write_map,
)

__all__ = [
    "IOManager",
    "OutputTracker",
    "read_poi_data",
    "read_custom_pois",
    "write_csv",
    "write_geojson",
    "write_geoparquet",
    "write_parquet",
    "write_map",
]