"""Modern SocialMapper client with improved API design.

Provides a clean, type-safe interface with proper error handling,
resource management, and extensibility.
"""

import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ..constants import COORDINATE_PAIR_PARTS, DEFAULT_API_TIMEOUT, MAX_TRAVEL_TIME, MIN_TRAVEL_TIME
from ..pipeline import PipelineConfig, PipelineOrchestrator
from ..ui.console import get_logger
from ..util import CENSUS_VARIABLE_MAPPING, normalize_census_variable
from .builder import AnalysisResult, GeographicLevel, SocialMapperBuilder
from .result_types import Err, Error, ErrorType, Ok, Result

logger = get_logger(__name__)


@runtime_checkable
class CacheStrategy(Protocol):
    """Protocol for cache strategies."""

    def get(self, key: str) -> Any | None:
        """Retrieve item from cache."""
        ...

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store item in cache."""
        ...

    def invalidate(self, key: str) -> None:
        """Remove item from cache."""
        ...


@dataclass
class ClientConfig:
    """Configuration for SocialMapper client."""

    api_key: str | None = None
    cache_strategy: CacheStrategy | None = None
    rate_limit: int = 10  # requests per second
    timeout: int = 300  # seconds
    retry_attempts: int = 3
    user_agent: str = "SocialMapper/0.5.4"
    # Connection pooling settings
    max_connections: int = 100
    max_connections_per_host: int = DEFAULT_API_TIMEOUT
    keepalive_timeout: int = DEFAULT_API_TIMEOUT


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_second: int):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class SocialMapperClient:
    """Modern client for SocialMapper with improved API design.

    Example:
        ```python
        # Simple usage
        with SocialMapperClient() as client:
            result = client.analyze(
                location="San Francisco, CA", poi_type="amenity", poi_name="library"
            )

            match result:
                case Ok(analysis):
                    print(f"Found {analysis.poi_count} libraries")
                case Err(error):
                    print(f"Analysis failed: {error}")

        # Advanced usage with configuration
        config = ClientConfig(
            api_key="your-census-api-key", cache_strategy=RedisCache(), rate_limit=5
        )

        with SocialMapperClient(config) as client:
            # Create analysis with builder
            analysis = (
                client.create_analysis()
                .with_location("Chicago", "IL")
                .with_osm_pois("leisure", "park")
                .with_travel_time(20)
                .build()
            )

            # Run with progress callback
            result = client.run_analysis(
                analysis, on_progress=lambda p: print(f"Progress: {p}%")
            )
        ```
    """

    def __init__(self, config: ClientConfig | None = None):
        """Initialize client with optional configuration."""
        self.config = config or ClientConfig()
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        self._session_active = False

    def __enter__(self):
        """Enter context manager."""
        self._session_active = True
        logger.info("SocialMapper client session started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self._session_active = False
        logger.info("SocialMapper client session ended")

    def create_analysis(self) -> SocialMapperBuilder:
        """Create a new analysis configuration builder.

        Returns:
            Builder for fluent configuration
        """
        builder = SocialMapperBuilder()
        # Pre-configure with client settings
        if self.config.api_key:
            builder.with_census_api_key(self.config.api_key)
        return builder

    def analyze(
        self,
        location: str,
        poi_type: str,
        poi_name: str,
        travel_time: int = 15,
        census_variables: list[str] | None = None,
        **kwargs,
    ) -> Result[AnalysisResult, Error]:
        """Simple analysis method for common use cases.

        Args:
            location: City and state (e.g., "San Francisco, CA")
            poi_type: OSM POI type (e.g., "amenity")
            poi_name: OSM POI name (e.g., "library")
            travel_time: Travel time in minutes
            census_variables: List of census variables to analyze
            **kwargs: Additional options

        Returns:
            Result with AnalysisResult or Error
        """
        try:
            # Parse location
            parts = location.split(",")
            if len(parts) != COORDINATE_PAIR_PARTS:
                return Err(
                    Error(
                        type=ErrorType.VALIDATION,
                        message="Location must be in format 'City, State'",
                        context={"location": location},
                    )
                )

            city = parts[0].strip()
            state = parts[1].strip()

            # Build configuration
            builder = self.create_analysis()
            builder.with_location(city, state)
            builder.with_osm_pois(poi_type, poi_name)
            builder.with_travel_time(travel_time)

            if census_variables:
                builder.with_census_variables(*census_variables)

            # Apply additional options
            if kwargs.get("output_dir"):
                builder.with_output_directory(kwargs["output_dir"])

            config = builder.build()
            return self.run_analysis(config)

        except ValueError as e:
            return Err(Error(type=ErrorType.VALIDATION, message=str(e), cause=e))
        except Exception as e:
            return Err(Error(type=ErrorType.UNKNOWN, message=f"Unexpected error: {e!s}", cause=e))

    def run_analysis(
        self, config: dict[str, Any], on_progress: Callable[[float], None] | None = None
    ) -> Result[AnalysisResult, Error]:
        """Run analysis with the given configuration.

        Args:
            config: Configuration from builder
            on_progress: Optional progress callback (0-100)

        Returns:
            Result with AnalysisResult or Error
        """
        if not self._session_active:
            return Err(
                Error(
                    type=ErrorType.VALIDATION,
                    message="Client must be used within a context manager",
                )
            )

        try:
            # Check cache if available
            cache_key = self._generate_cache_key(config)
            if self.config.cache_strategy:
                cached = self.config.cache_strategy.get(cache_key)
                if cached:
                    logger.info("Returning cached analysis result")
                    return Ok(cached)

            # Rate limit check
            self.rate_limiter.wait_if_needed()

            # Run pipeline
            pipeline_config = PipelineConfig(**config)
            orchestrator = PipelineOrchestrator(pipeline_config)

            # Execute with progress tracking
            result_data = orchestrator.run()

            # Extract POIs and demographics from result
            pois = result_data.get("pois", [])

            # Calculate demographics summary (aggregate from census data)
            demographics = {}
            if "census_data" in result_data and hasattr(result_data["census_data"], 'to_dict'):
                census_df = result_data["census_data"]
                # Sum up population and average income across all census units
                for var in config.get("census_variables", []):
                    if var in census_df.columns:
                        if var == "B01003_001E":  # Total population - sum
                            demographics[var] = census_df[var].sum()
                        elif var == "B19013_001E":  # Median income - weighted average
                            # For simplicity, just take the mean
                            demographics[var] = census_df[var].mean()
                        else:
                            demographics[var] = census_df[var].sum()

            # Calculate isochrone area if available
            isochrone_area = 0.0
            if "isochrones" in result_data and hasattr(result_data["isochrones"], 'geometry'):
                try:
                    # Project to equal area projection for accurate area calculation
                    iso_gdf = result_data["isochrones"].to_crs("EPSG:5070")
                    # Sum area in square meters and convert to square kilometers
                    isochrone_area = iso_gdf.geometry.area.sum() / 1_000_000
                except Exception:
                    pass

            # Convert to structured result
            result = AnalysisResult(
                poi_count=len(pois),
                isochrone_count=len(result_data.get("isochrones", [])),
                census_units_analyzed=len(result_data.get("census_data", [])),
                files_generated=self._extract_file_paths(result_data),
                metadata={
                    "travel_time": config.get("travel_time"),
                    "geographic_level": config.get("geographic_level"),
                    "census_variables": config.get("census_variables"),
                    "center_lat": pois[0]["lat"] if pois else config.get("lat"),
                    "center_lon": pois[0]["lon"] if pois else config.get("lon"),
                },
                pois=pois,
                demographics=demographics,
                isochrone_area=isochrone_area,
            )

            # Cache result if strategy available
            if self.config.cache_strategy:
                self.config.cache_strategy.set(cache_key, result, ttl=3600)

            return Ok(result)

        except Exception as e:
            logger.error(f"Analysis failed: {e!s}")

            # Determine error type based on exception
            error_type = self._classify_error(e)

            return Err(Error(type=error_type, message=str(e), context={"config": config}, cause=e))

    def validate_configuration(self, config: dict[str, Any]) -> Result[dict[str, Any], Error]:
        """Comprehensive configuration validation with detailed error reporting.

        Args:
            config: Configuration to validate

        Returns:
            Result with validated config or detailed Error
        """
        try:
            validation_errors = []

            # Validate census variables if provided
            if "census_variables" in config:
                invalid_vars = []
                for var in config["census_variables"]:
                    normalized = normalize_census_variable(var)
                    # Check if it's a known variable or valid format
                    if (
                        normalized not in CENSUS_VARIABLE_MAPPING.values()
                        and not normalized.startswith("B")
                        and "_" in normalized
                        and normalized.endswith("E")
                    ):
                        invalid_vars.append(var)

                if invalid_vars:
                    validation_errors.append(
                        f"Invalid census variables: {', '.join(invalid_vars)}. "
                        f"Available: {', '.join(CENSUS_VARIABLE_MAPPING.keys())}"
                    )

            # Validate geographic level
            if "geographic_level" in config:
                valid_levels = [level.value for level in GeographicLevel]
                if config["geographic_level"] not in valid_levels:
                    validation_errors.append(
                        f"Invalid geographic level: {config['geographic_level']}. "
                        f"Must be one of: {', '.join(valid_levels)}"
                    )

            # Validate travel time
            if "travel_time" in config:
                travel_time = config["travel_time"]
                if not isinstance(travel_time, int) or not MIN_TRAVEL_TIME <= travel_time <= MAX_TRAVEL_TIME:
                    validation_errors.append(
                        f"Travel time must be an integer between {MIN_TRAVEL_TIME} and {MAX_TRAVEL_TIME} minutes"
                    )

            # Validate output directory
            if "output_dir" in config:
                try:
                    Path(config["output_dir"]).resolve()
                except Exception:
                    validation_errors.append(f"Invalid output directory: {config['output_dir']}")

            # Use builder validation for remaining checks
            builder = SocialMapperBuilder()
            builder._config = config.copy()
            builder_errors = builder.validate()
            validation_errors.extend(builder_errors)

            if validation_errors:
                return Err(
                    Error(
                        type=ErrorType.VALIDATION,
                        message="Configuration validation failed",
                        context={"errors": validation_errors, "config": config},
                    )
                )

            return Ok(config)

        except Exception as e:
            return Err(
                Error(type=ErrorType.VALIDATION, message=f"Validation error: {e!s}", cause=e)
            )

    @contextmanager
    def batch_analyses(self, configs: list[dict[str, Any]]):
        """Context manager for batch processing multiple analyses.

        Example:
            ```python
            configs = [config1, config2, config3]

            with client.batch_analyses(configs) as batch:
                results = batch.run_all()
                for i, result in enumerate(results):
                    print(f"Analysis {i}: {result}")
            ```
        """

        class BatchProcessor:
            def __init__(self, client, configs):
                self.client = client
                self.configs = configs
                self.results = []

            def run_all(self) -> list[Result[AnalysisResult, Error]]:
                """Run all analyses in batch."""
                for i, config in enumerate(self.configs):
                    logger.info(f"Running batch analysis {i + 1}/{len(self.configs)}")
                    result = self.client.run_analysis(config)
                    self.results.append(result)
                return self.results

        processor = BatchProcessor(self, configs)
        yield processor

    def _generate_cache_key(self, config: dict[str, Any]) -> str:
        """Generate cache key from configuration."""
        # Simple implementation - in production would use better hashing
        key_parts = [
            config.get("geocode_area", ""),
            config.get("poi_type", ""),
            config.get("poi_name", ""),
            str(config.get("travel_time", 15)),
        ]
        return ":".join(key_parts)

    def _extract_file_paths(self, result_data: dict[str, Any]) -> dict[str, Path]:
        """Extract file paths from pipeline results."""
        files = {}

        # Extract CSV data file
        if "csv_data" in result_data:
            csv_data = result_data["csv_data"]
            if isinstance(csv_data, dict) and "csv_data" in csv_data:
                files["census_data"] = Path(csv_data["csv_data"])
            elif isinstance(csv_data, str | Path):
                files["census_data"] = Path(csv_data)

        # Extract map files
        if "maps" in result_data:
            maps_info = result_data["maps"]
            if isinstance(maps_info, dict):
                if "output_paths" in maps_info:
                    # Add individual map paths
                    for map_type, map_path in maps_info["output_paths"].items():
                        files[f"map_{map_type}"] = Path(map_path)
                if "output_directory" in maps_info:
                    files["maps_directory"] = Path(maps_info["output_directory"])

        # Extract isochrone file
        if "isochrone_file" in result_data:
            files["isochrones"] = Path(result_data["isochrone_file"])

        return files

    def _classify_error(self, exception: Exception) -> ErrorType:
        """Classify exception into error type."""
        error_msg = str(exception).lower()

        if "validation" in error_msg or "invalid" in error_msg:
            return ErrorType.VALIDATION
        elif "network" in error_msg or "connection" in error_msg:
            return ErrorType.NETWORK
        elif "not found" in error_msg:
            return ErrorType.FILE_NOT_FOUND
        elif "permission" in error_msg or "denied" in error_msg:
            return ErrorType.PERMISSION_DENIED
        elif "rate limit" in error_msg:
            return ErrorType.RATE_LIMIT
        elif "census" in error_msg:
            return ErrorType.CENSUS_API
        elif "osm" in error_msg or "overpass" in error_msg:
            return ErrorType.OSM_API
        else:
            return ErrorType.UNKNOWN
