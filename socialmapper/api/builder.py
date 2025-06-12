"""
Modern builder pattern for SocialMapper API configuration.

Provides a fluent interface for building analysis configurations
with type safety and validation.
"""

from typing import List, Optional, Self, Dict, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class GeographicLevel(Enum):
    """Geographic unit options for census analysis."""
    BLOCK_GROUP = "block-group"
    ZCTA = "zcta"  # ZIP Code Tabulation Area


class MapBackend(Enum):
    """Supported map visualization backends."""
    PLOTLY = "plotly"


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
            .enable_map_export()
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
            "export_maps": False,
            "export_isochrones": False,
            "map_backend": MapBackend.PLOTLY,
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
        self, 
        poi_type: str, 
        poi_name: str,
        additional_tags: Optional[Dict[str, str]] = None
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
        type_field: Optional[str] = None
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
        """Add census variables to analyze."""
        self._config["census_variables"] = list(variables)
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
            self._validation_errors.append(
                f"POI limit must be positive, got {max_count}"
            )
        self._config["max_poi_count"] = max_count
        return self
    
    def enable_map_export(self, backend: MapBackend = MapBackend.PLOTLY) -> Self:
        """Enable map visualization export."""
        self._config["export_maps"] = True
        self._config["map_backend"] = backend.value
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
            errors.append(
                "Location required for OSM search (use with_location)"
            )
        
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
            raise ValueError(
                f"Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        
        return self._config.copy()