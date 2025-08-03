"""Centralized I/O module for SocialMapper.

This module handles all file input/output operations including:
- Reading POI data from various formats
- Writing analysis results
- Managing output directories
- Handling map files
- Tracking generated files
"""

from .manager import IOManager, OutputTracker
from .readers import read_custom_pois, read_poi_data
from .writers import (
    write_csv,
    write_geojson,
    write_geoparquet,
    write_map,
    write_parquet,
)

__all__ = [
    "IOManager",
    "OutputTracker",
    "read_custom_pois",
    "read_poi_data",
    "write_csv",
    "write_geojson",
    "write_geoparquet",
    "write_map",
    "write_parquet",
]
