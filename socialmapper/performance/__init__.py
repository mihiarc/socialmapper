"""Performance optimization utilities for SocialMapper.

Provides:
- HTTP connection pooling for API requests
- Caching for repeated queries
"""

from .cache import CacheManager, get_cache_stats
from .config import PerformanceConfig, PerformancePreset, get_performance_config
from .connection_pool import get_http_session, init_connection_pool

__all__ = [
    "CacheManager",
    "PerformanceConfig",
    "PerformancePreset",
    "get_cache_stats",
    "get_http_session",
    "get_performance_config",
    "init_connection_pool",
]
