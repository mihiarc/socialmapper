#!/usr/bin/env python3
"""Parquet export format implementation.

This module provides Parquet export functionality for census data.
"""

from pathlib import Path

import pandas as pd

from ...ui.console import get_logger
from ..base import BaseExporter, ExportError

logger = get_logger(__name__)


class ParquetExporter(BaseExporter):
    """Exporter for Parquet format."""

    def export(
        self, data: pd.DataFrame, output_path: str | Path, compression: str = "snappy", **kwargs
    ) -> str:
        """Export data to Parquet format.

        Args:
            data: DataFrame to export
            output_path: Path to save the Parquet file
            compression: Compression algorithm ('snappy', 'gzip', 'brotli', None)
            **kwargs: Additional pandas to_parquet options

        Returns:
            Path to the saved Parquet file
        """
        output_path = self.validate_output_path(output_path)

        try:
            # Remove geometry column if present (use GeoParquet for geometry)
            if "geometry" in data.columns:
                logger.info("Removing geometry column for standard Parquet export")
                data = data.drop(columns=["geometry"])

            # Optimize data types for better compression
            data = self._optimize_dtypes(data)

            # Default Parquet options
            parquet_options = {
                "engine": "pyarrow",
                "compression": compression,
                "index": False,
            }
            parquet_options.update(kwargs)

            # Save to Parquet
            data.to_parquet(output_path, **parquet_options)
            logger.info(f"Successfully saved Parquet to {output_path}")

            # Log compression ratio if original size is available
            if hasattr(data, "_original_size"):
                compressed_size = output_path.stat().st_size
                ratio = data._original_size / compressed_size
                logger.info(f"Compression ratio: {ratio:.1f}x")

            return str(output_path)

        except Exception as e:
            raise ExportError(f"Could not save Parquet: {e}") from e

    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame dtypes for better compression."""
        df_optimized = df.copy()

        for col in df_optimized.columns:
            col_type = df_optimized[col].dtype

            if col_type == "object":
                # Try to convert to numeric first
                numeric_series = pd.to_numeric(df_optimized[col], errors="coerce")
                if not numeric_series.isna().all():
                    df_optimized[col] = numeric_series
                else:
                    # Convert to categorical if low cardinality
                    unique_ratio = df_optimized[col].nunique() / len(df_optimized)
                    if unique_ratio < 0.5:
                        df_optimized[col] = df_optimized[col].astype("category")

            elif col_type in ["int64", "float64"]:
                # Downcast numeric types
                if "int" in str(col_type):
                    df_optimized[col] = pd.to_numeric(df_optimized[col], downcast="integer")
                else:
                    df_optimized[col] = pd.to_numeric(df_optimized[col], downcast="float")

        return df_optimized

    def get_file_extension(self) -> str:
        """Get the file extension for Parquet format."""
        return ".parquet"

    def supports_geometry(self) -> bool:
        """Standard Parquet does not support geometry columns."""
        return False
