"""
Infrastructure layer for the modern census module.

This package contains concrete implementations of external dependencies
like API clients, caches, databases, and other infrastructure concerns.
"""

from .configuration import CensusConfig, ConfigurationProvider
from .api_client import CensusAPIClientImpl, CensusAPIError
from .cache import InMemoryCacheProvider, FileCacheProvider, NoOpCacheProvider, HybridCacheProvider
from .rate_limiter import TokenBucketRateLimiter, AdaptiveRateLimiter, NoOpRateLimiter
from .repository import SQLiteRepository, NoOpRepository, InMemoryRepository, RepositoryError
from .geocoder import CensusGeocoder, MockGeocoder, NoOpGeocoder, GeocodingError

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
] 