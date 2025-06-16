#!/usr/bin/env python3
"""Common utilities for export operations.

This module contains utility functions used across export operations.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from ..ui.console import get_logger

logger = get_logger(__name__)


def estimate_data_size(data: pd.DataFrame | gpd.GeoDataFrame) -> float:
    """Estimate the size of data in memory (MB).

    Args:
        data: DataFrame or GeoDataFrame to estimate

    Returns:
        Estimated size in megabytes
    """
    return data.memory_usage(deep=True).sum() / 1024**2


def generate_output_path(
    base_filename: str | None = None,
    output_dir: str = "output",
    format: str = "csv",
    include_geometry: bool = False,
) -> Path:
    """Generate output path with appropriate extension.

    Args:
        base_filename: Base filename without extension
        output_dir: Output directory
        format: Export format
        include_geometry: Whether geometry is included

    Returns:
        Generated output path
    """
    if base_filename is None:
        base_filename = "census_data"

    # Determine extension based on format
    extensions = {
        "csv": ".csv",
        "parquet": ".parquet",
        "geoparquet": ".geoparquet",
    }

    # Use geoparquet for parquet with geometry
    if format == "parquet" and include_geometry:
        format = "geoparquet"

    extension = extensions.get(format, ".csv")

    # Create output path
    output_path = Path(output_dir) / f"{base_filename}_export{extension}"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    return output_path


def select_export_format(
    data_size_mb: float, has_geometry: bool = False, format_preference: str = "auto"
) -> str:
    """Select optimal export format based on data characteristics.

    Args:
        data_size_mb: Estimated data size in MB
        has_geometry: Whether data contains geometry
        format_preference: User format preference or "auto"

    Returns:
        Selected format name
    """
    if format_preference != "auto":
        return format_preference

    # Thresholds for format selection
    LARGE_DATA_THRESHOLD_MB = 100
    MEDIUM_DATA_THRESHOLD_MB = 10

    if has_geometry:
        # Always use GeoParquet for geospatial data
        return "geoparquet"
    elif data_size_mb > LARGE_DATA_THRESHOLD_MB:
        # Use Parquet for large datasets
        return "parquet"
    elif data_size_mb > MEDIUM_DATA_THRESHOLD_MB:
        # Use Parquet for medium datasets
        return "parquet"
    else:
        # Use CSV for small datasets
        return "csv"


def validate_export_data(data: pd.DataFrame | gpd.GeoDataFrame) -> None:
    """Validate data before export.

    Args:
        data: Data to validate

    Raises:
        ValueError: If data is invalid
    """
    if data is None:
        raise ValueError("Export data cannot be None")

    if not isinstance(data, (pd.DataFrame, gpd.GeoDataFrame)):
        raise ValueError(f"Export data must be DataFrame or GeoDataFrame, got {type(data)}")

    if data.empty:
        logger.warning("Export data is empty")


def get_format_info(format: str) -> dict:
    """Get information about an export format.

    Args:
        format: Format name

    Returns:
        Dictionary with format information
    """
    format_info = {
        "csv": {
            "name": "CSV",
            "description": "Comma-separated values",
            "supports_geometry": False,
            "compression": False,
            "best_for": "Small datasets, Excel compatibility",
        },
        "parquet": {
            "name": "Parquet",
            "description": "Columnar storage format",
            "supports_geometry": False,
            "compression": True,
            "best_for": "Large datasets, data analysis",
        },
        "geoparquet": {
            "name": "GeoParquet",
            "description": "Geospatial Parquet format",
            "supports_geometry": True,
            "compression": True,
            "best_for": "Geospatial data, large datasets",
        },
    }

    return format_info.get(
        format,
        {
            "name": format.upper(),
            "description": "Unknown format",
            "supports_geometry": False,
            "compression": False,
            "best_for": "Unknown use case",
        },
    )
