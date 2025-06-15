#!/usr/bin/env python3
"""
CSV export format implementation.

This module provides CSV export functionality for census data.
"""

from pathlib import Path
from typing import Union

import pandas as pd

from ...ui.console import get_logger
from ..base import BaseExporter, ExportError

logger = get_logger(__name__)


class CSVExporter(BaseExporter):
    """Exporter for CSV format."""
    
    def export(
        self,
        data: pd.DataFrame,
        output_path: Union[str, Path],
        **kwargs
    ) -> str:
        """
        Export data to CSV format.
        
        Args:
            data: DataFrame to export
            output_path: Path to save the CSV file
            **kwargs: Additional pandas to_csv options
            
        Returns:
            Path to the saved CSV file
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
        """Get the file extension for CSV format."""
        return ".csv"
    
    def supports_geometry(self) -> bool:
        """CSV does not support geometry columns."""
        return False