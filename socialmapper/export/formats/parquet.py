#!/usr/bin/env python3
"""Parquet export format implementation.

This module provides Parquet export functionality for census data.
"""

import logging
from pathlib import Path

import pandas as pd

from socialmapper.constants import CATEGORICAL_CONVERSION_THRESHOLD

from ..base import BaseExporter, ExportError

logger = logging.getLogger(__name__)


class ParquetExporter(BaseExporter):
    """
    Parquet file format exporter with automatic dtype optimization.

    Exports pandas DataFrames to Parquet files with configurable
    compression and automatic data type optimization for better
    compression ratios. Removes geometry columns automatically.
    """

    def export(
        self, data: pd.DataFrame, output_path: str | Path, compression: str = "snappy", **kwargs
    ) -> str:
        """
        Export DataFrame to Parquet file with compression.

        Automatically optimizes data types for better compression and
        removes geometry columns. Supports multiple compression
        algorithms via PyArrow.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame containing the data to export.
        output_path : str or Path
            File path where the Parquet file should be saved.
        compression : str, optional
            Compression algorithm to use. Options: 'snappy', 'gzip',
            'brotli', or None for no compression. By default 'snappy'.
        **kwargs : dict, optional
            Additional keyword arguments passed to pandas.to_parquet().

        Returns
        -------
        str
            Absolute path to the saved Parquet file.

        Raises
        ------
        ExportError
            If the file cannot be saved to the specified path.

        Examples
        --------
        >>> import pandas as pd
        >>> exporter = ParquetExporter(config)
        >>> data = pd.DataFrame({'pop': [100, 200], 'area': [1, 2]})
        >>> path = exporter.export(data, 'census.parquet',
        ...                        compression='gzip')
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
        """
        Optimize DataFrame column data types for better compression.

        Converts object columns to categorical or numeric types where
        appropriate, and downcasts numeric types to smaller sizes.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to optimize.

        Returns
        -------
        pd.DataFrame
            Optimized DataFrame with smaller memory footprint.
        """
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
                    if unique_ratio < CATEGORICAL_CONVERSION_THRESHOLD:
                        df_optimized[col] = df_optimized[col].astype("category")

            elif col_type in ["int64", "float64"]:
                # Downcast numeric types
                if "int" in str(col_type):
                    df_optimized[col] = pd.to_numeric(df_optimized[col], downcast="integer")
                else:
                    df_optimized[col] = pd.to_numeric(df_optimized[col], downcast="float")

        return df_optimized

    def get_file_extension(self) -> str:
        """
        Get the standard file extension for Parquet format.

        Returns
        -------
        str
            The file extension '.parquet'.
        """
        return ".parquet"

    def supports_geometry(self) -> bool:
        """
        Check if standard Parquet format supports geometry columns.

        Returns
        -------
        bool
            Always False. Use GeoParquet format for spatial data.
        """
        return False
