#!/usr/bin/env python3
"""Common utilities for export operations.

This module contains utility functions used across export operations.
"""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)


def estimate_data_size(data: pd.DataFrame | gpd.GeoDataFrame) -> float:
    """
    Estimate the memory footprint of DataFrame or GeoDataFrame.

    Calculates deep memory usage including object dtype columns
    and returns the result in megabytes.

    Parameters
    ----------
    data : pd.DataFrame or gpd.GeoDataFrame
        DataFrame or GeoDataFrame to estimate memory usage for.

    Returns
    -------
    float
        Estimated size in megabytes (MB).

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({'a': range(1000), 'b': range(1000)})
    >>> size_mb = estimate_data_size(data)
    >>> size_mb > 0
    True
    """
    return data.memory_usage(deep=True).sum() / 1024**2


def generate_output_path(
    base_filename: str | None = None,
    output_dir: str = "output",
    format: str = "csv",
    include_geometry: bool = False,
) -> Path:
    """
    Generate output file path with appropriate format extension.

    Automatically selects file extension based on format and geometry
    presence. Creates output directory if it doesn't exist.

    Parameters
    ----------
    base_filename : str, optional
        Base filename without extension. Defaults to 'census_data'.
    output_dir : str, optional
        Directory for output file, by default 'output'.
    format : str, optional
        Export format ('csv', 'parquet', 'geoparquet'), by default
        'csv'.
    include_geometry : bool, optional
        Whether output includes geometry. Upgrades 'parquet' to
        'geoparquet' if True, by default False.

    Returns
    -------
    pathlib.Path
        Complete output path with directory and extension.

    Examples
    --------
    >>> path = generate_output_path('my_data', format='parquet')
    >>> str(path)
    'output/my_data_export.parquet'

    >>> path = generate_output_path(format='parquet',
    ...                            include_geometry=True)
    >>> str(path)
    'output/census_data_export.geoparquet'
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
    """
    Select optimal export format based on data characteristics.

    Automatically chooses the best format based on data size and
    geometry presence. Uses GeoParquet for spatial data, Parquet
    for large datasets, and CSV for small datasets.

    Parameters
    ----------
    data_size_mb : float
        Estimated data size in megabytes.
    has_geometry : bool, optional
        Whether data contains spatial geometry columns, by default
        False.
    format_preference : str, optional
        User's preferred format or 'auto' for automatic selection,
        by default 'auto'.

    Returns
    -------
    str
        Selected format name ('csv', 'parquet', or 'geoparquet').

    Examples
    --------
    >>> select_export_format(5.0, has_geometry=False)
    'csv'

    >>> select_export_format(150.0, has_geometry=False)
    'parquet'

    >>> select_export_format(10.0, has_geometry=True)
    'geoparquet'
    """
    if format_preference != "auto":
        return format_preference

    # Thresholds for format selection
    large_data_threshold_mb = 100
    medium_data_threshold_mb = 10

    if has_geometry:
        # Always use GeoParquet for geospatial data
        return "geoparquet"
    elif data_size_mb > large_data_threshold_mb:
        # Use Parquet for large datasets
        return "parquet"
    elif data_size_mb > medium_data_threshold_mb:
        # Use Parquet for medium datasets
        return "parquet"
    else:
        # Use CSV for small datasets
        return "csv"


def validate_export_data(data: pd.DataFrame | gpd.GeoDataFrame) -> None:
    """
    Validate data before export to ensure it meets requirements.

    Checks that data is not None, is a valid DataFrame type, and
    logs a warning if the data is empty.

    Parameters
    ----------
    data : pd.DataFrame or gpd.GeoDataFrame
        Data to validate before export.

    Raises
    ------
    ValueError
        If data is None or not a DataFrame/GeoDataFrame instance.

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({'col': [1, 2, 3]})
    >>> validate_export_data(data)  # No exception raised

    >>> validate_export_data(None)  # Raises ValueError
    Traceback (most recent call last):
        ...
    ValueError: Export data cannot be None
    """
    if data is None:
        raise ValueError("Export data cannot be None")

    if not isinstance(data, pd.DataFrame | gpd.GeoDataFrame):
        raise ValueError(f"Export data must be DataFrame or GeoDataFrame, got {type(data)}")

    if data.empty:
        logger.warning("Export data is empty")


def get_format_info(format: str) -> dict:
    """
    Get detailed metadata about an export format.

    Returns a dictionary containing format name, description,
    capabilities, and recommended use cases.

    Parameters
    ----------
    format : str
        Format name ('csv', 'parquet', or 'geoparquet').

    Returns
    -------
    dict
        Dictionary with keys: 'name', 'description',
        'supports_geometry', 'compression', 'best_for'.

    Examples
    --------
    >>> info = get_format_info('csv')
    >>> info['name']
    'CSV'
    >>> info['supports_geometry']
    False

    >>> info = get_format_info('geoparquet')
    >>> info['supports_geometry']
    True
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
