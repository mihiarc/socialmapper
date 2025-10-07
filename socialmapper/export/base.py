#!/usr/bin/env python3
"""Base classes and interfaces for the export module.

This module provides abstract base classes and configuration for exporters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
import pandas as pd


@dataclass
class DataPrepConfig:
    """
    Configuration for data preparation and export preprocessing.

    Defines column ordering, exclusions, and deduplication rules for
    preparing census and POI data before export.

    Attributes
    ----------
    preferred_column_order : list of str
        Preferred order for columns in exported data.
    excluded_columns : list of str
        Columns to exclude from exports (e.g., internal IDs).
    deduplication_columns : list of str
        Columns used as keys for deduplication.
    deduplication_agg_rules : dict
        Aggregation rules for duplicate rows (e.g., 'min', 'first').
    """

    preferred_column_order: list[str] = field(
        default_factory=lambda: [
            "census_block_group",
            "poi_name",
            "poi_type",
            "distance_miles",
            "travel_time_minutes",
            "travel_mode",
            "state_fips",
            "county_fips",
            "tract",
            "block_group",
            "total_population",
            "median_household_income",
            "median_age",
            "percent_white",
            "percent_black",
            "percent_asian",
            "percent_hispanic",
            "per_capita_income",
            "poverty_rate",
            "unemployment_rate",
            "educational_attainment_high_school",
            "educational_attainment_bachelors",
            "housing_units",
            "median_home_value",
            "median_rent",
            "percent_owner_occupied",
            "population_density",
            "lat",
            "lon",
        ]
    )

    excluded_columns: list[str] = field(
        default_factory=lambda: [
            "geometry",
            "GEOID",
            "TRACTCE",
            "BLKGRPCE",
            "AFFGEOID",
            "LSAD",
            "ALAND",
            "AWATER",
        ]
    )

    deduplication_columns: list[str] = field(
        default_factory=lambda: [
            "census_block_group",
            "poi_name",
            "poi_type",
            "travel_mode",
        ]
    )

    deduplication_agg_rules: dict[str, str] = field(
        default_factory=lambda: {
            "distance_miles": "min",
            "travel_time_minutes": "min",
            "total_population": "first",
            "median_household_income": "first",
            "median_age": "first",
        }
    )


class BaseExporter(ABC):
    """
    Abstract base class for all data export format implementations.

    Defines the interface that all exporter classes must implement,
    including format-specific export logic, file extensions, and
    geometry support capabilities.

    Parameters
    ----------
    config : DataPrepConfig, optional
        Configuration for data preparation, by default None which
        creates default configuration.

    Attributes
    ----------
    config : DataPrepConfig
        Data preparation configuration instance.
    """

    def __init__(self, config: DataPrepConfig | None = None):
        """
        Initialize exporter with optional configuration.

        Parameters
        ----------
        config : DataPrepConfig, optional
            Data preparation configuration. Creates default if None.
        """
        self.config = config or DataPrepConfig()

    @abstractmethod
    def export(
        self, data: pd.DataFrame | gpd.GeoDataFrame, output_path: str | Path, **kwargs
    ) -> str:
        """
        Export data to the format-specific file.

        Must be implemented by subclasses to handle format-specific
        export logic.

        Parameters
        ----------
        data : pd.DataFrame or gpd.GeoDataFrame
            Data to export.
        output_path : str or Path
            Destination file path.
        **kwargs : dict
            Format-specific export options.

        Returns
        -------
        str
            Absolute path to the exported file.
        """

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Get the standard file extension for this export format.

        Returns
        -------
        str
            File extension including the dot (e.g., '.csv').
        """

    @abstractmethod
    def supports_geometry(self) -> bool:
        """
        Check if this export format supports spatial geometry columns.

        Returns
        -------
        bool
            True if format can store geometry data.
        """

    def validate_output_path(self, output_path: str | Path) -> Path:
        """
        Validate and prepare output file path.

        Creates parent directories if needed and ensures the file has
        the correct extension for this export format.

        Parameters
        ----------
        output_path : str or Path
            Desired output file path.

        Returns
        -------
        pathlib.Path
            Validated and corrected output path with proper extension.

        Examples
        --------
        >>> exporter = CSVExporter()
        >>> path = exporter.validate_output_path('data/output')
        >>> str(path)
        'data/output.csv'
        """
        output_path = Path(output_path)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add extension if not present
        if output_path.suffix != self.get_file_extension():
            output_path = output_path.with_suffix(self.get_file_extension())

        return output_path


class ExportError(Exception):
    """
    Base exception for all export-related errors.

    Raised when export operations fail due to various reasons
    including I/O errors, format incompatibilities, or data issues.
    """


class DataPreparationError(ExportError):
    """
    Exception raised during data preparation phase.

    Indicates issues with cleaning, transforming, or validating data
    before export (e.g., missing required columns, invalid data types).
    """


class FormatNotSupportedError(ExportError):
    """
    Exception raised when requested export format is not supported.

    Indicates the user requested an export format that is not
    implemented or not available in the current environment.
    """
