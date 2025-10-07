#!/usr/bin/env python3
"""Modern Export Module with clean architecture.

This module provides export functionality for census data in various formats:
- CSV (legacy support)
- Parquet (efficient columnar storage)
- GeoParquet (geospatial data)
"""

import logging
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import pandas as pd

from ..constants import LARGE_DATASET_MB
from .base import DataPrepConfig, ExportError
from .formats import CSVExporter, GeoParquetExporter, ParquetExporter
from .preparation import prepare_census_data
from .utils import (
    estimate_data_size,
    generate_output_path,
    select_export_format,
    validate_export_data,
)

logger = logging.getLogger(__name__)


def export_census_data_to_csv(
    census_data: gpd.GeoDataFrame,
    poi_data: dict | list[dict],
    output_path: str | None = None,
    base_filename: str | None = None,
    output_dir: str = "output/csv",
) -> str:
    """
    Legacy CSV export function for backward compatibility.

    Parameters
    ----------
    census_data : gpd.GeoDataFrame
        GeoDataFrame with census data for block groups.
    poi_data : dict or list of dict
        Dictionary with POI data or list of POIs.
    output_path : str, optional
        Full path to save the CSV file. If None, generated
        automatically.
    base_filename : str, optional
        Base filename to use if output_path is not provided.
    output_dir : str, optional
        Directory to save the CSV if output_path is not provided.
        Default is "output/csv".

    Returns
    -------
    str
        Path to the saved CSV file.

    Notes
    -----
    Consider using export_to_parquet or export_to_geoparquet for
    better performance and smaller file sizes.
    """
    logger.info("Using legacy CSV export (consider upgrading to modern formats)")

    # Prepare data using common utilities
    config = DataPrepConfig()
    prepared_data = prepare_census_data(census_data, poi_data, config=config, deduplicate=True)

    # Generate output path if not provided
    if output_path is None:
        output_path = generate_output_path(base_filename, output_dir, "csv")

    # Export using CSV exporter
    exporter = CSVExporter(config)
    return exporter.export(prepared_data, output_path)


def export_to_parquet(data: pd.DataFrame, output_path: str | Path, **kwargs) -> str:
    """
    Export DataFrame to Parquet format.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame to export.
    output_path : str or Path
        Output file path.
    **kwargs
        Additional options passed to ParquetExporter.

    Returns
    -------
    str
        Path to saved file.
    """
    exporter = ParquetExporter()
    return exporter.export(data, output_path, **kwargs)


def export_to_geoparquet(data: gpd.GeoDataFrame, output_path: str | Path, **kwargs) -> str:
    """
    Export GeoDataFrame to GeoParquet format.

    Parameters
    ----------
    data : gpd.GeoDataFrame
        GeoDataFrame to export with geometry column.
    output_path : str or Path
        Output file path.
    **kwargs
        Additional options passed to GeoParquetExporter.

    Returns
    -------
    str
        Path to saved file.
    """
    exporter = GeoParquetExporter()
    return exporter.export(data, output_path, **kwargs)


# Public API
__all__ = [
    # Configuration
    "DataPrepConfig",
    # Exceptions
    "ExportError",
    # Main export functions
    "export_census_data",
    "export_census_data_to_csv",  # Legacy
    "export_to_geoparquet",
    "export_to_parquet",
]
