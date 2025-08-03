"""Modern builder pattern for SocialMapper API configuration.

Provides a fluent interface for building analysis configurations
with type safety and validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Self

# Import constants and travel mode
from ..constants import MAX_TRAVEL_TIME, MIN_TRAVEL_TIME, validate_coordinates, validate_travel_time
from ..exceptions import (
    InvalidConfigurationError,
    InvalidTravelTimeError,
)
from ..isochrone import TravelMode

# Import POI categorization for validation
from ..poi_categorization import get_poi_category_info, is_valid_category

# Import census variable validation
from ..util import CENSUS_VARIABLE_MAPPING, normalize_census_variable, validate_census_variable

# Import POI discovery config
from .result_types import NearbyPOIDiscoveryConfig


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
    files_generated: dict[str, Path]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    # Include the actual data for UI consumption
    pois: list[dict] = field(default_factory=list)
    demographics: dict[str, float] = field(default_factory=dict)
    isochrone_area: float = 0.0
    isochrones: Any = None  # GeoDataFrame with isochrone geometries

    @property
    def success(self) -> bool:
        """Check if the analysis completed successfully."""
        return self.poi_count > 0 and self.isochrone_count > 0


class SocialMapperBuilder:
    """Modern builder for SocialMapper analysis configuration.

    Supports three main types of analysis:
    1. OSM POI analysis with demographic data
    2. Custom POI analysis from file
    3. Nearby POI discovery around a location

    Examples:
        OSM POI Analysis:
        ```python
        config = (
            SocialMapperBuilder()
            .with_location("San Francisco", "CA")
            .with_osm_pois("amenity", "library")
            .with_travel_time(15)
            .with_census_variables("total_population", "median_income")
            .build()
        )
        ```

        Nearby POI Discovery:
        ```python
        config = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("San Francisco, CA", 20, "walk")
            .with_poi_categories("food_and_drink", "healthcare", "education")
            .exclude_poi_categories("utilities")
            .limit_pois_per_category(25)
            .with_exports(csv=True, maps=True)
            .build()
        )
        ```

        Combined Analysis:
        ```python
        config = (
            SocialMapperBuilder()
            .with_location("Boston, MA")
            .with_osm_pois("amenity", "hospital")
            .with_nearby_poi_discovery("Boston, MA", 15)
            .with_poi_categories("healthcare", "services")
            .with_census_variables("total_population")
            .build()
        )
        ```
    """

    def __init__(self):
        """Initialize builder with sensible defaults."""
        self._config = {
            "travel_time": 15,
            "travel_mode": TravelMode.DRIVE,
            "geographic_level": GeographicLevel.BLOCK_GROUP.value,  # Use string value
            "census_variables": ["total_population"],
            "export_csv": True,
            "export_isochrones": False,
            "create_maps": True,  # Enable choropleth maps by default
            "output_dir": Path("output"),
            # POI discovery configuration
            "poi_discovery_enabled": False,
            "poi_discovery_location": None,
            "poi_discovery_travel_time": None,
            "poi_discovery_travel_mode": None,
            "poi_categories": None,
            "exclude_poi_categories": None,
            "max_pois_per_category": None,
        }
        self._validation_errors = []

    def with_location(self, area: str, state: str | None = None) -> Self:
        """Set the geographic area for analysis."""
        self._config["geocode_area"] = area
        if state:
            self._config["state"] = state
        return self

    def with_osm_pois(
        self, poi_type: str, poi_name: str, additional_tags: dict[str, str] | None = None
    ) -> Self:
        """Configure OpenStreetMap POI search."""
        self._config["poi_type"] = poi_type
        self._config["poi_name"] = poi_name
        if additional_tags:
            self._config["additional_tags"] = additional_tags
        return self

    def with_custom_pois(
        self,
        file_path: str | Path,
        name_field: str | None = None,
        type_field: str | None = None,
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
        if not MIN_TRAVEL_TIME <= minutes <= MAX_TRAVEL_TIME:
            raise InvalidTravelTimeError(minutes, MIN_TRAVEL_TIME, MAX_TRAVEL_TIME)
        self._config["travel_time"] = minutes
        return self

    def with_travel_mode(self, mode: str | TravelMode) -> Self:
        """Set the travel mode for isochrone generation (walk, bike, drive)."""
        if isinstance(mode, str):
            try:
                mode = TravelMode.from_string(mode)
            except ValueError as e:
                self._validation_errors.append(str(e))
                return self
        self._config["travel_mode"] = mode
        return self

    def with_census_variables(self, *variables: str) -> Self:
        """Add census variables to analyze with validation."""
        validated_variables = []
        for var in variables:
            try:
                # First validate the input variable name/code
                validate_census_variable(var)
                # Then normalize it (which may return a list for calculated variables)
                normalize_census_variable(var)
                # For calculated variables, normalized will be a list of census codes
                # For simple variables, it will be a single census code
                # Both are valid, so we add them as-is
                validated_variables.append(var)  # Store the original variable name
            except Exception as e:
                self._validation_errors.append(f"Invalid census variable '{var}': {e!s}")

        self._config["census_variables"] = validated_variables
        return self

    def with_census_api_key(self, api_key: str) -> Self:
        """Set Census API key for faster access."""
        self._config["api_key"] = api_key
        return self

    def with_geographic_level(self, level: GeographicLevel) -> Self:
        """Set the geographic unit for census analysis."""
        self._config["geographic_level"] = level.value if isinstance(level, GeographicLevel) else level
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

    def enable_map_generation(self) -> Self:
        """Enable choropleth map generation."""
        self._config["create_maps"] = True
        return self

    def disable_csv_export(self) -> Self:
        """Disable CSV export (enabled by default)."""
        self._config["export_csv"] = False
        return self

    def with_output_directory(self, path: str | Path) -> Self:
        """Set custom output directory."""
        self._config["output_dir"] = str(path)
        return self

    def with_exports(self, csv: bool = True, isochrones: bool = False, maps: bool = False) -> Self:
        """Configure export options.

        Args:
            csv: Export demographic data to CSV format
            isochrones: Export isochrone boundaries as shapefiles
            maps: Generate choropleth maps visualizing demographic patterns
        """
        self._config["export_csv"] = csv
        self._config["export_isochrones"] = isochrones
        self._config["create_maps"] = maps
        return self

    def validate(self) -> list[str]:
        """Validate the configuration and return any errors."""
        errors = self._validation_errors.copy()

        # Check required fields based on input method
        has_custom = "custom_coords_path" in self._config
        has_osm = all(key in self._config for key in ["poi_type", "poi_name"])
        has_poi_discovery = self._config.get("poi_discovery_enabled", False)

        # At least one analysis method must be configured
        if not has_custom and not has_osm and not has_poi_discovery:
            errors.append(
                "Must specify either custom POIs (with_custom_pois), "
                "OSM search (with_osm_pois), or POI discovery (with_nearby_poi_discovery)"
            )

        if has_osm and "geocode_area" not in self._config:
            errors.append("Location required for OSM search (use with_location)")

        # POI discovery specific validation
        if has_poi_discovery:
            if not self._config.get("poi_discovery_location"):
                errors.append("POI discovery location is required when POI discovery is enabled")

            if not self._config.get("poi_discovery_travel_time"):
                errors.append("POI discovery travel time is required when POI discovery is enabled")

            # Check for conflicting category specifications
            poi_cats = self._config.get("poi_categories")
            exclude_cats = self._config.get("exclude_poi_categories")
            if poi_cats and exclude_cats:
                overlapping = set(poi_cats) & set(exclude_cats)
                if overlapping:
                    errors.append(
                        f"Categories cannot be both included and excluded: {list(overlapping)}"
                    )

        return errors

    def build(self) -> dict[str, Any]:
        """Build and validate the configuration.

        Returns:
            Configuration dictionary ready for use

        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        errors = self.validate()
        if errors:
            raise InvalidConfigurationError(
                field="configuration",
                value="multiple errors",
                reason="\n".join(errors)
            ).add_suggestion("Fix the configuration errors listed above")

        config = self._config.copy()

        # If POI discovery is enabled, create the POI discovery config object
        if config.get("poi_discovery_enabled", False):
            poi_config = NearbyPOIDiscoveryConfig(
                location=config["poi_discovery_location"],
                travel_time=config["poi_discovery_travel_time"],
                travel_mode=config["poi_discovery_travel_mode"],
                poi_categories=config.get("poi_categories"),
                exclude_categories=config.get("exclude_poi_categories"),
                max_pois_per_category=config.get("max_pois_per_category"),
                output_dir=Path(config["output_dir"]),
                export_csv=config["export_csv"],
                create_map=config["create_maps"],
            )
            config["poi_discovery_config"] = poi_config

        return config

    def with_nearby_poi_discovery(
        self,
        location: str | tuple[float, float],
        travel_time: int,
        travel_mode: str | TravelMode = TravelMode.DRIVE,
        poi_categories: list[str] | None = None,
    ) -> Self:
        """Configure nearby POI discovery analysis.
        
        Args:
            location: Either an address string or (lat, lon) tuple for the origin
            travel_time: Travel time in minutes for isochrone generation
            travel_mode: Travel mode (walk, bike, drive)
            poi_categories: Optional list of POI categories to include
            
        Returns:
            Self for method chaining
        """
        # Validate travel time
        if not validate_travel_time(travel_time):
            self._validation_errors.append(
                f"Travel time must be between {MIN_TRAVEL_TIME} and {MAX_TRAVEL_TIME} minutes"
            )
            return self

        # Validate location if coordinates
        if isinstance(location, tuple):
            lat, lon = location
            if not validate_coordinates(lat, lon):
                self._validation_errors.append(f"Invalid coordinates: {location}")
                return self
        elif isinstance(location, str):
            if not location.strip():
                self._validation_errors.append("Location address cannot be empty")
                return self
        else:
            self._validation_errors.append(
                "Location must be either an address string or (lat, lon) tuple"
            )
            return self

        # Validate travel mode
        if isinstance(travel_mode, str):
            try:
                travel_mode = TravelMode.from_string(travel_mode)
            except ValueError as e:
                self._validation_errors.append(str(e))
                return self

        # Validate POI categories if provided
        if poi_categories:
            invalid_categories = [cat for cat in poi_categories if not is_valid_category(cat)]
            if invalid_categories:
                available_cats = list(get_poi_category_info()["categories"])
                self._validation_errors.append(
                    f"Invalid POI categories: {invalid_categories}. "
                    f"Available categories: {available_cats}"
                )
                return self

        # Configure POI discovery
        self._config["poi_discovery_enabled"] = True
        self._config["poi_discovery_location"] = location
        self._config["poi_discovery_travel_time"] = travel_time
        self._config["poi_discovery_travel_mode"] = travel_mode
        if poi_categories:
            self._config["poi_categories"] = poi_categories.copy()

        return self

    def with_poi_categories(self, *categories: str) -> Self:
        """Set POI categories to include in discovery.
        
        Args:
            *categories: POI category names to include
            
        Returns:
            Self for method chaining
        """
        if not categories:
            self._validation_errors.append("At least one POI category must be specified")
            return self

        # Validate all categories
        invalid_categories = [cat for cat in categories if not is_valid_category(cat)]
        if invalid_categories:
            available_cats = list(get_poi_category_info()["categories"])
            self._validation_errors.append(
                f"Invalid POI categories: {invalid_categories}. "
                f"Available categories: {available_cats}"
            )
            return self

        self._config["poi_categories"] = list(categories)
        return self

    def exclude_poi_categories(self, *categories: str) -> Self:
        """Set POI categories to exclude from discovery.
        
        Args:
            *categories: POI category names to exclude
            
        Returns:
            Self for method chaining
        """
        if not categories:
            self._validation_errors.append("At least one POI category must be specified for exclusion")
            return self

        # Validate all categories
        invalid_categories = [cat for cat in categories if not is_valid_category(cat)]
        if invalid_categories:
            available_cats = list(get_poi_category_info()["categories"])
            self._validation_errors.append(
                f"Invalid POI categories for exclusion: {invalid_categories}. "
                f"Available categories: {available_cats}"
            )
            return self

        self._config["exclude_poi_categories"] = list(categories)
        return self

    def limit_pois_per_category(self, max_count: int) -> Self:
        """Set maximum number of POIs per category.
        
        Args:
            max_count: Maximum POIs to return per category
            
        Returns:
            Self for method chaining
        """
        if max_count < 1:
            self._validation_errors.append(f"POI limit per category must be positive, got {max_count}")
            return self

        self._config["max_pois_per_category"] = max_count
        return self

    def list_available_census_variables(self) -> dict[str, str]:
        """List available census variables with their codes."""
        return CENSUS_VARIABLE_MAPPING.copy()

    def list_available_poi_categories(self) -> dict[str, Any]:
        """List available POI categories with details.
        
        Returns:
            Dictionary containing category information
        """
        return get_poi_category_info()
