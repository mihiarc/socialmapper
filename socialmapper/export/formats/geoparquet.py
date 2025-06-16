#!/usr/bin/env python3
"""GeoParquet export format implementation.

This module provides GeoParquet export functionality for geospatial census data.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from ...ui.console import get_logger
from ..base import BaseExporter, ExportError

logger = get_logger(__name__)


class GeoParquetExporter(BaseExporter):
    """Exporter for GeoParquet format."""

    def export(
        self,
        data: pd.DataFrame | gpd.GeoDataFrame,
        output_path: str | Path,
        compression: str = "snappy",
        **kwargs,
    ) -> str:
        """Export data to GeoParquet format.

        Args:
            data: GeoDataFrame to export
            output_path: Path to save the GeoParquet file
            compression: Compression algorithm ('snappy', 'gzip', 'brotli', None)
            **kwargs: Additional geopandas to_parquet options

        Returns:
            Path to the saved GeoParquet file
        """
        output_path = self.validate_output_path(output_path)

        try:
            # Ensure we have a GeoDataFrame
            if not isinstance(data, gpd.GeoDataFrame):
                if "geometry" in data.columns:
                    logger.info("Converting DataFrame to GeoDataFrame")
                    data = gpd.GeoDataFrame(data)
                else:
                    logger.warning("No geometry column found, using standard Parquet instead")
                    from .parquet import ParquetExporter

                    parquet_exporter = ParquetExporter(self.config)
                    return parquet_exporter.export(data, output_path, compression, **kwargs)

            # Optimize data types for better compression
            data = self._optimize_geodataframe(data)

            # Default GeoParquet options
            geoparquet_options = {
                "compression": compression,
                "index": False,
            }
            geoparquet_options.update(kwargs)

            # Save to GeoParquet
            data.to_parquet(output_path, **geoparquet_options)
            logger.info(f"Successfully saved GeoParquet to {output_path}")

            return str(output_path)

        except Exception as e:
            raise ExportError(f"Could not save GeoParquet: {e}") from e

    def _optimize_geodataframe(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Optimize GeoDataFrame for better compression."""
        gdf_optimized = gdf.copy()

        # Optimize non-geometry columns
        for col in gdf_optimized.columns:
            if col != gdf_optimized.geometry.name:
                col_type = gdf_optimized[col].dtype

                if col_type == "object":
                    # Try to convert to categorical for better compression
                    unique_ratio = gdf_optimized[col].nunique() / len(gdf_optimized)
                    if unique_ratio < 0.5:  # Less than 50% unique values
                        gdf_optimized[col] = gdf_optimized[col].astype("category")

                elif col_type in ["int64", "float64"]:
                    # Downcast numeric types
                    if "int" in str(col_type):
                        gdf_optimized[col] = pd.to_numeric(gdf_optimized[col], downcast="integer")
                    else:
                        gdf_optimized[col] = pd.to_numeric(gdf_optimized[col], downcast="float")

        return gdf_optimized

    def get_file_extension(self) -> str:
        """Get the file extension for GeoParquet format."""
        return ".geoparquet"

    def supports_geometry(self) -> bool:
        """GeoParquet supports geometry columns."""
        return True
