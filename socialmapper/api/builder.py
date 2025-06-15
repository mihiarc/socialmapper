"""
Modern builder pattern for SocialMapper API configuration.

Provides a fluent interface for building analysis configurations
with type safety and validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Self, Union

# Import census variable validation
from ..util import CENSUS_VARIABLE_MAPPING, normalize_census_variable, validate_census_variable


class GeographicLevel(Enum):
    """Geographic unit options for census analysis."""

    BLOCK_GROUP = "block-group"
    ZCTA = "zcta"  # ZIP Code Tabulation Area



@dataclass
class AnalysisResult:
    """Structured result from a SocialMapper analysis."""

    poi_count: int
    isochrone_count: int
    census_units_analyzed: int
    files_generated: Dict[str, Path]
    metadata: Dict[str, any]
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if the analysis completed successfully."""
        return self.poi_count > 0 and self.isochrone_count > 0


class SocialMapperBuilder:
    """
    Modern builder for SocialMapper analysis configuration.

    Example:
        ```python
        config = (SocialMapperBuilder()
            .with_location("San Francisco", "CA")
            .with_osm_pois("amenity", "library")
            .with_travel_time(15)
            .with_census_variables("total_population", "median_income")
            .build()
        )
        ```
    """

    def __init__(self):
        """Initialize builder with sensible defaults."""
        self._config = {
            "travel_time": 15,
            "geographic_level": GeographicLevel.BLOCK_GROUP,
            "census_variables": ["total_population"],
            "export_csv": True,
            "export_isochrones": False,
            "output_dir": Path("output"),
        }
        self._validation_errors = []

    def with_location(self, area: str, state: Optional[str] = None) -> Self:
        """Set the geographic area for analysis."""
        self._config["geocode_area"] = area
        if state:
            self._config["state"] = state
        return self

    def with_osm_pois(
        self, poi_type: str, poi_name: str, additional_tags: Optional[Dict[str, str]] = None
    ) -> Self:
        """Configure OpenStreetMap POI search."""
        self._config["poi_type"] = poi_type
        self._config["poi_name"] = poi_name
        if additional_tags:
            self._config["additional_tags"] = additional_tags
        return self

    def with_custom_pois(
        self,
        file_path: Union[str, Path],
        name_field: Optional[str] = None,
        type_field: Optional[str] = None,
    ) -> Self:
        """Use custom POI coordinates from a file."""
        self._config["custom_coords_path"] = str(file_path)
        if name_field:
            self._config["name_field"] = name_field
        if type_field:
            self._config["type_field"] = type_field
        return self

    def with_travel_time(self, minutes: int) -> Self:
        """Set the travel time for isochrone generation."""
        if not 1 <= minutes <= 120:
            self._validation_errors.append(
                f"Travel time must be between 1 and 120 minutes, got {minutes}"
            )
        self._config["travel_time"] = minutes
        return self

    def with_census_variables(self, *variables: str) -> Self:
        """Add census variables to analyze with validation."""
        validated_variables = []
        for var in variables:
            try:
                # First validate the input variable name/code
                validate_census_variable(var)
                # Then normalize it (which may return a list for calculated variables)
                normalized = normalize_census_variable(var)
                # For calculated variables, normalized will be a list of census codes
                # For simple variables, it will be a single census code
                # Both are valid, so we add them as-is
                validated_variables.append(var)  # Store the original variable name
            except Exception as e:
                self._validation_errors.append(
                    f"Invalid census variable '{var}': {str(e)}"
                )
        
        self._config["census_variables"] = validated_variables
        return self

    def with_census_api_key(self, api_key: str) -> Self:
        """Set Census API key for faster access."""
        self._config["api_key"] = api_key
        return self

    def with_geographic_level(self, level: GeographicLevel) -> Self:
        """Set the geographic unit for census analysis."""
        self._config["geographic_level"] = level.value
        return self

    def limit_pois(self, max_count: int) -> Self:
        """Limit the number of POIs to process."""
        if max_count < 1:
            self._validation_errors.append(f"POI limit must be positive, got {max_count}")
        self._config["max_poi_count"] = max_count
        return self

    def enable_isochrone_export(self) -> Self:
        """Enable isochrone shape export."""
        self._config["export_isochrones"] = True
        return self

    def disable_csv_export(self) -> Self:
        """Disable CSV export (enabled by default)."""
        self._config["export_csv"] = False
        return self

    def with_output_directory(self, path: Union[str, Path]) -> Self:
        """Set custom output directory."""
        self._config["output_dir"] = str(path)
        return self

    def with_exports(self, csv: bool = True, isochrones: bool = False) -> Self:
        """Configure export options."""
        self._config["export_csv"] = csv
        self._config["export_isochrones"] = isochrones
        return self

    def validate(self) -> List[str]:
        """Validate the configuration and return any errors."""
        errors = self._validation_errors.copy()

        # Check required fields based on input method
        has_custom = "custom_coords_path" in self._config
        has_osm = all(key in self._config for key in ["poi_type", "poi_name"])

        if not has_custom and not has_osm:
            errors.append(
                "Must specify either custom POIs (with_custom_pois) "
                "or OSM search (with_osm_pois)"
            )

        if has_osm and "geocode_area" not in self._config:
            errors.append("Location required for OSM search (use with_location)")

        return errors

    def build(self) -> Dict[str, any]:
        """
        Build and validate the configuration.

        Returns:
            Configuration dictionary ready for use

        Raises:
            ValueError: If configuration is invalid
        """
        errors = self.validate()
        if errors:
            raise ValueError("Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors))

        return self._config.copy()

    def list_available_census_variables(self) -> Dict[str, str]:
        """List available census variables with their codes."""
        return CENSUS_VARIABLE_MAPPING.copy()
