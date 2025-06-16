"""Domain interfaces (protocols) for census operations.

These define the contracts that infrastructure implementations must fulfill.
Using protocols enables dependency injection and easy testing with mocks.
"""

from typing import Any, Protocol

from .entities import (
    BoundaryData,
    CacheEntry,
    CensusDataPoint,
    GeocodeResult,
    NeighborRelationship,
)


class CensusAPIClient(Protocol):
    """Protocol for accessing Census Bureau APIs."""

    def get_census_data(
        self, variables: list[str], geography: str, year: int, dataset: str, **kwargs
    ) -> dict[str, Any]:
        """Fetch census data from the API."""
        ...

    def get_geographies(
        self, geography_type: str, state_code: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Fetch geographic boundaries from the API."""
        ...


class GeocodeProvider(Protocol):
    """Protocol for geocoding services."""

    def geocode_point(self, latitude: float, longitude: float) -> GeocodeResult:
        """Geocode a lat/lon point to geographic units."""
        ...

    def geocode_address(self, address: str) -> GeocodeResult:
        """Geocode an address to geographic units."""
        ...


class CacheProvider(Protocol):
    """Protocol for caching implementations."""

    def get(self, key: str) -> CacheEntry | None:
        """Retrieve a cached entry."""
        ...

    def set(self, key: str, data: Any, ttl: int | None = None) -> None:
        """Store data in cache with optional TTL."""
        ...

    def delete(self, key: str) -> None:
        """Remove an entry from cache."""
        ...

    def clear(self) -> None:
        """Clear all cached data."""
        ...


class DataRepository(Protocol):
    """Protocol for data persistence."""

    def save_census_data(self, data_points: list[CensusDataPoint]) -> None:
        """Persist census data points."""
        ...

    def get_census_data(
        self, geoids: list[str], variable_codes: list[str]
    ) -> list[CensusDataPoint]:
        """Retrieve stored census data."""
        ...

    def save_boundaries(self, boundaries: list[BoundaryData]) -> None:
        """Persist boundary data."""
        ...

    def get_boundaries(self, geoids: list[str]) -> list[BoundaryData]:
        """Retrieve stored boundary data."""
        ...

    def save_neighbor_relationships(self, relationships: list[NeighborRelationship]) -> None:
        """Persist neighbor relationships."""
        ...

    def get_neighbors(self, geoid: str) -> list[NeighborRelationship]:
        """Get neighbor relationships for a geographic unit."""
        ...


class ConfigurationProvider(Protocol):
    """Protocol for configuration management."""

    @property
    def census_api_key(self) -> str | None:
        """Census Bureau API key."""
        ...

    @property
    def cache_enabled(self) -> bool:
        """Whether caching is enabled."""
        ...

    @property
    def cache_ttl_seconds(self) -> int:
        """Default cache TTL in seconds."""
        ...

    @property
    def rate_limit_requests_per_minute(self) -> int:
        """API rate limit."""
        ...

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        ...


class RateLimiter(Protocol):
    """Protocol for rate limiting API calls."""

    def wait_if_needed(self, resource: str) -> None:
        """Wait if rate limit would be exceeded."""
        ...

    def reset_limits(self, resource: str) -> None:
        """Reset rate limiting for a resource."""
        ...


class Logger(Protocol):
    """Protocol for logging."""

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        ...

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        ...


class EventPublisher(Protocol):
    """Protocol for publishing domain events."""

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish a domain event."""
        ...


# Composite protocols for service dependencies


class CensusDataDependencies(Protocol):
    """All dependencies needed for census data operations."""

    api_client: CensusAPIClient
    cache: CacheProvider
    repository: DataRepository
    config: ConfigurationProvider
    rate_limiter: RateLimiter
    logger: Logger


class GeographyDependencies(Protocol):
    """All dependencies needed for geography operations."""

    api_client: CensusAPIClient
    geocoder: GeocodeProvider
    cache: CacheProvider
    repository: DataRepository
    config: ConfigurationProvider
    logger: Logger


class NeighborDependencies(Protocol):
    """All dependencies needed for neighbor operations."""

    repository: DataRepository
    geocoder: GeocodeProvider
    cache: CacheProvider
    config: ConfigurationProvider
    logger: Logger
