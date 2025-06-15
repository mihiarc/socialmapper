"""
Infrastructure layer for the modern census module.

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
    # Configuration
    "CensusConfig",
    "ConfigurationProvider",
    
    # API Client
    "CensusAPIClientImpl",
    "CensusAPIError",
    
    # Cache
    "InMemoryCacheProvider",
    "FileCacheProvider", 
    "NoOpCacheProvider",
    "HybridCacheProvider",
    
    # Rate Limiting
    "TokenBucketRateLimiter",
    "AdaptiveRateLimiter",
    "NoOpRateLimiter",
    
    # Repository
    "SQLiteRepository",
    "NoOpRepository",
    "InMemoryRepository",
    "RepositoryError",
    
    # Geocoding
    "CensusGeocoder",
    "MockGeocoder",
    "NoOpGeocoder",
    "GeocodingError",
    
    # Memory Management
    "MemoryMonitor",
    "MemoryEfficientDataProcessor", 
    "get_memory_monitor",
    "memory_efficient_processing",
    
    # Streaming
    "StreamingDataPipeline",
    "ModernDataExporter",
    "get_streaming_pipeline",
] 