#!/usr/bin/env python3
"""
Base classes and interfaces for the export module.

This module provides abstract base classes and configuration for exporters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import geopandas as gpd
import pandas as pd


@dataclass
class DataPrepConfig:
    """Configuration for data preparation."""
    
    preferred_column_order: List[str] = field(default_factory=lambda: [
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
    ])
    
    excluded_columns: List[str] = field(default_factory=lambda: [
        "geometry",
        "GEOID",
        "TRACTCE",
        "BLKGRPCE",
        "AFFGEOID",
        "LSAD",
        "ALAND",
        "AWATER",
    ])
    
    deduplication_columns: List[str] = field(default_factory=lambda: [
        "census_block_group",
        "poi_name",
        "poi_type",
        "travel_mode",
    ])
    
    deduplication_agg_rules: Dict[str, str] = field(default_factory=lambda: {
        "distance_miles": "min",
        "travel_time_minutes": "min",
        "total_population": "first",
        "median_household_income": "first",
        "median_age": "first",
    })


class BaseExporter(ABC):
    """Base class for all export formats."""
    
    def __init__(self, config: Optional[DataPrepConfig] = None):
        """Initialize exporter with configuration."""
        self.config = config or DataPrepConfig()
    
    @abstractmethod
    def export(
        self,
        data: Union[pd.DataFrame, gpd.GeoDataFrame],
        output_path: Union[str, Path],
        **kwargs
    ) -> str:
        """
        Export data to the specific format.
        
        Args:
            data: Data to export
            output_path: Path to save the exported file
            **kwargs: Format-specific options
            
        Returns:
            Path to the exported file
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this format."""
        pass
    
    @abstractmethod
    def supports_geometry(self) -> bool:
        """Check if this format supports geometry columns."""
        pass
    
    def validate_output_path(self, output_path: Union[str, Path]) -> Path:
        """Validate and prepare output path."""
        output_path = Path(output_path)
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add extension if not present
        if output_path.suffix != self.get_file_extension():
            output_path = output_path.with_suffix(self.get_file_extension())
        
        return output_path


class ExportError(Exception):
    """Base exception for export errors."""
    pass


class DataPreparationError(ExportError):
    """Exception raised during data preparation."""
    pass


class FormatNotSupportedError(ExportError):
    """Exception raised when a format is not supported."""
    pass