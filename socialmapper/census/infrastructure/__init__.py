"""Infrastructure layer for the modern census module.

This package contains concrete implementations of external dependencies
like API clients, caches, databases, and other infrastructure concerns.
"""

from .api_client import CensusAPIClientImpl, CensusAPIError
from .cache import FileCacheProvider, HybridCacheProvider, InMemoryCacheProvider, NoOpCacheProvider
from .configuration import CensusConfig, ConfigurationProvider
from .geocoder import CensusGeocoder, GeocodingError, MockGeocoder, NoOpGeocoder
from .memory import (
    MemoryEfficientDataProcessor,
    MemoryMonitor,
    get_memory_monitor,
    memory_efficient_processing,
)
from .rate_limiter import AdaptiveRateLimiter, NoOpRateLimiter, TokenBucketRateLimiter
from .repository import InMemoryRepository, NoOpRepository, RepositoryError, SQLiteRepository
from .streaming import ModernDataExporter, StreamingDataPipeline, get_streaming_pipeline

__all__ = [
    "AdaptiveRateLimiter",
    # API Client
    "CensusAPIClientImpl",
    "CensusAPIError",
    # Configuration
    "CensusConfig",
    # Geocoding
    "CensusGeocoder",
    "ConfigurationProvider",
    "FileCacheProvider",
    "GeocodingError",
    "HybridCacheProvider",
    # Cache
    "InMemoryCacheProvider",
    "InMemoryRepository",
    "MemoryEfficientDataProcessor",
    # Memory Management
    "MemoryMonitor",
    "MockGeocoder",
    "ModernDataExporter",
    "NoOpCacheProvider",
    "NoOpGeocoder",
    "NoOpRateLimiter",
    "NoOpRepository",
    "RepositoryError",
    # Repository
    "SQLiteRepository",
    # Streaming
    "StreamingDataPipeline",
    # Rate Limiting
    "TokenBucketRateLimiter",
    "get_memory_monitor",
    "get_streaming_pipeline",
    "memory_efficient_processing",
]
