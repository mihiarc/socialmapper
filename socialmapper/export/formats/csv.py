#!/usr/bin/env python3
"""CSV export format implementation.

This module provides CSV export functionality for census data.
"""

import logging
from pathlib import Path

import pandas as pd

from ..base import BaseExporter, ExportError

logger = logging.getLogger(__name__)


class CSVExporter(BaseExporter):
    """
    CSV file format exporter for tabular census data.

    Exports pandas DataFrames to CSV files with automatic geometry
    column removal and fallback handling for write failures.
    """

    def export(self, data: pd.DataFrame, output_path: str | Path, **kwargs) -> str:
        """
        Export DataFrame to CSV file format.

        Automatically removes geometry columns as CSV does not support
        spatial data. Falls back to current directory if output path
        is not writable.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame containing the data to export.
        output_path : str or Path
            File path where the CSV should be saved.
        **kwargs : dict, optional
            Additional keyword arguments passed to pandas.to_csv().
            Common options include 'sep' for delimiter and 'columns'
            for column selection.

        Returns
        -------
        str
            Absolute path to the saved CSV file.

        Raises
        ------
        ExportError
            If the file cannot be saved to both the specified path
            and the fallback location.

        Examples
        --------
        >>> import pandas as pd
        >>> exporter = CSVExporter(config)
        >>> data = pd.DataFrame({'pop': [100, 200], 'area': [1, 2]})
        >>> path = exporter.export(data, 'census_data.csv')
        """
        output_path = self.validate_output_path(output_path)

        # Handle empty dataframe case
        if data.empty:
            logger.warning("Creating minimal CSV with no data")
            data = pd.DataFrame({"message": ["No census data available for export"]})

        try:
            # Remove geometry column if present (CSV doesn't support geometry)
            if "geometry" in data.columns:
                data = data.drop(columns=["geometry"])

            # Default CSV options
            csv_options = {
                "index": False,
                "encoding": "utf-8",
            }
            csv_options.update(kwargs)

            # Save to CSV
            data.to_csv(output_path, **csv_options)
            logger.info(f"Successfully saved CSV to {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")

            # Try fallback location
            fallback_path = Path.cwd() / "census_data_fallback.csv"
            try:
                data.to_csv(fallback_path, **csv_options)
                logger.warning(f"Saved to fallback location: {fallback_path}")
                return str(fallback_path)
            except Exception as fallback_error:
                raise ExportError(f"Could not save CSV: {e}") from fallback_error

    def get_file_extension(self) -> str:
        """
        Get the standard file extension for CSV format.

        Returns
        -------
        str
            The file extension '.csv'.
        """
        return ".csv"

    def supports_geometry(self) -> bool:
        """
        Check if CSV format supports geometry columns.

        Returns
        -------
        bool
            Always False, as CSV cannot store spatial geometry data.
        """
        return False
