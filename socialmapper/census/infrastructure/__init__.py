"""Infrastructure layer for the modern census module.

This package contains concrete implementations of external dependencies
like API clients, caches, databases, and other infrastructure concerns.
"""

from .api_client import CensusAPIClientImpl, CensusAPIError, CensusAPIRateLimitError
from .cache import FileCacheProvider, HybridCacheProvider, InMemoryCacheProvider, NoOpCacheProvider
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError
from .configuration import CensusConfig, ConfigurationProvider
from .enhanced_api_client import EnhancedCensusAPIClient
from .factory import (
    create_census_api_client,
    create_census_cache,
    create_census_system,
    create_rate_limiter,
)
from .geocoder import CensusGeocoder, GeocodingError, MockGeocoder, NoOpGeocoder
from .memory import (
    MemoryEfficientDataProcessor,
    MemoryMonitor,
    get_memory_monitor,
    memory_efficient_processing,
)
from .metrics import APIMetrics, MetricsCollector, RequestTimer
from .rate_limiter import AdaptiveRateLimiter, NoOpRateLimiter, TokenBucketRateLimiter
from .repository import InMemoryRepository, NoOpRepository, RepositoryError, SQLiteRepository
from .request_deduplicator import AsyncRequestDeduplicator, RequestDeduplicator, deduplicate_key
from .streaming import ModernDataExporter, StreamingDataPipeline, get_streaming_pipeline

__all__ = [
    "AdaptiveRateLimiter",
    # API Client
    "APIMetrics",
    "AsyncRequestDeduplicator",
    "CensusAPIClientImpl",
    "CensusAPIError",
    "CensusAPIRateLimitError",
    # Configuration
    "CensusConfig",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    # Geocoding
    "CensusGeocoder",
    "ConfigurationProvider",
    # Enhanced API Client
    "EnhancedCensusAPIClient",
    "FileCacheProvider",
    "GeocodingError",
    "HybridCacheProvider",
    # Cache
    "InMemoryCacheProvider",
    "InMemoryRepository",
    "MemoryEfficientDataProcessor",
    # Memory Management
    "MemoryMonitor",
    # Metrics
    "MetricsCollector",
    "MockGeocoder",
    "ModernDataExporter",
    "NoOpCacheProvider",
    "NoOpGeocoder",
    "NoOpRateLimiter",
    "NoOpRepository",
    # Request Deduplication
    "RequestDeduplicator",
    "RequestTimer",
    "RepositoryError",
    # Repository
    "SQLiteRepository",
    # Streaming
    "StreamingDataPipeline",
    # Rate Limiting
    "TokenBucketRateLimiter",
    # Factory methods
    "create_census_api_client",
    "create_census_cache",
    "create_census_system",
    "create_rate_limiter",
    "deduplicate_key",
    "get_memory_monitor",
    "get_streaming_pipeline",
    "memory_efficient_processing",
]
