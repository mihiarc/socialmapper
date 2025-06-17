#!/usr/bin/env python3
"""Modern Export Module with clean architecture.

This module provides export functionality for census data in various formats:
- CSV (legacy support)
- Parquet (efficient columnar storage)
- GeoParquet (geospatial data)
"""

from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import pandas as pd

from ..census.infrastructure import ModernDataExporter, get_streaming_pipeline
from ..config.optimization import OptimizationConfig
from ..constants import LARGE_DATASET_MB
from ..ui.console import get_logger
from .base import DataPrepConfig, ExportError
from .formats import CSVExporter, GeoParquetExporter, ParquetExporter
from .preparation import prepare_census_data
from .utils import (
    estimate_data_size,
    generate_output_path,
    select_export_format,
    validate_export_data,
)

logger = get_logger(__name__)


def export_census_data_to_csv(
    census_data: gpd.GeoDataFrame,
    poi_data: dict | list[dict],
    output_path: str | None = None,
    base_filename: str | None = None,
    output_dir: str = "output/csv",
) -> str:
    """Legacy CSV export function (maintained for backward compatibility).

    Args:
        census_data: GeoDataFrame with census data for block groups
        poi_data: Dictionary with POI data or list of POIs
        output_path: Full path to save the CSV file
        base_filename: Base filename to use if output_path is not provided
        output_dir: Directory to save the CSV if output_path is not provided

    Returns:
        Path to the saved CSV file
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


def export_census_data(
    census_data: gpd.GeoDataFrame,
    poi_data: dict | list[dict],
    output_path: str | None = None,
    base_filename: str | None = None,
    output_dir: str = "output",
    format: str = "auto",
    include_geometry: bool = True,
    travel_time_minutes: int | None = None,
    travel_mode: str | None = None,
    config: OptimizationConfig | None = None,
) -> str:
    """Export census data in modern formats with automatic optimization.

    Args:
        census_data: GeoDataFrame with census data
        poi_data: POI data dictionary or list
        output_path: Full path to save the file
        base_filename: Base filename if output_path not provided
        output_dir: Output directory if output_path not provided
        format: Export format ('auto', 'csv', 'parquet', 'geoparquet')
        include_geometry: Whether to include geometry in output
        travel_time_minutes: Travel time in minutes
        travel_mode: Travel mode (walk, bike, drive)
        config: Optimization configuration

    Returns:
        Path to the saved file
    """
    try:
        # Validate input data
        validate_export_data(census_data)

        # Estimate data size and select format
        data_size_mb = estimate_data_size(census_data)
        has_geometry = include_geometry and "geometry" in census_data.columns
        selected_format = select_export_format(data_size_mb, has_geometry, format)

        logger.info(
            f"Exporting {len(census_data)} records as {selected_format.upper()} "
            f"(~{data_size_mb:.1f} MB)"
        )

        # For very large datasets, use streaming
        if data_size_mb > LARGE_DATASET_MB and selected_format in ["parquet", "geoparquet"]:
            logger.info("Using streaming export for large dataset")
            return _export_with_streaming(
                census_data,
                poi_data,
                output_path,
                base_filename,
                output_dir,
                selected_format,
                include_geometry,
            )

        # Prepare data
        prep_config = DataPrepConfig()
        prepared_data = prepare_census_data(
            census_data,
            poi_data,
            config=prep_config,
            travel_time_minutes=travel_time_minutes,
            travel_mode=travel_mode,
            deduplicate=True,
        )

        # Generate output path if not provided
        if output_path is None:
            output_path = generate_output_path(
                base_filename, output_dir, selected_format, include_geometry
            )

        # Select appropriate exporter
        exporters = {
            "csv": CSVExporter,
            "parquet": ParquetExporter,
            "geoparquet": GeoParquetExporter,
        }

        exporter_class = exporters.get(selected_format, CSVExporter)
        exporter = exporter_class(prep_config)

        # Handle geometry conversion for GeoParquet
        if selected_format == "geoparquet" and not isinstance(prepared_data, gpd.GeoDataFrame) and "geometry" in census_data.columns:
            # Add geometry back to prepared data
            prepared_data = gpd.GeoDataFrame(
                prepared_data, geometry=census_data["geometry"][: len(prepared_data)]
            )

        # Export data
        return exporter.export(prepared_data, output_path)

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise ExportError(f"Failed to export census data: {e}") from e


def export_to_parquet(data: pd.DataFrame, output_path: str | Path, **kwargs) -> str:
    """Export DataFrame to Parquet format.

    Args:
        data: DataFrame to export
        output_path: Output file path
        **kwargs: Additional options for ParquetExporter

    Returns:
        Path to saved file
    """
    exporter = ParquetExporter()
    return exporter.export(data, output_path, **kwargs)


def export_to_geoparquet(data: gpd.GeoDataFrame, output_path: str | Path, **kwargs) -> str:
    """Export GeoDataFrame to GeoParquet format.

    Args:
        data: GeoDataFrame to export
        output_path: Output file path
        **kwargs: Additional options for GeoParquetExporter

    Returns:
        Path to saved file
    """
    exporter = GeoParquetExporter()
    return exporter.export(data, output_path, **kwargs)


def _export_with_streaming(
    census_data: gpd.GeoDataFrame,
    poi_data: dict | list[dict],
    output_path: str | None,
    base_filename: str | None,
    output_dir: str,
    format: str,
    include_geometry: bool,
) -> str:
    """Use streaming pipeline for large datasets."""
    # Generate output path
    if output_path is None:
        output_path = generate_output_path(base_filename, output_dir, format, include_geometry)

    # Use Phase 3 streaming exporter
    with ModernDataExporter() as exporter:
        return exporter.export_census_data_modern(
            census_data, poi_data, output_path, format=format, include_geometry=include_geometry
        )


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
