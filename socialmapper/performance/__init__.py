"""Performance optimization utilities for SocialMapper.

This module provides comprehensive performance optimization tools including:
- Unified caching system with configurable TTL
- HTTP connection pooling for API requests
- Memory optimization utilities
- Batch processing helpers
- Performance monitoring and statistics

Examples
--------
>>> from socialmapper.performance import CacheManager, get_performance_config
>>>
>>> # Configure performance settings
>>> config = get_performance_config(preset='fast')
>>>
>>> # Use cache manager
>>> cache = CacheManager(config)
>>> result = cache.get('my_key')
"""

from .cache import CacheManager, get_cache_stats
from .config import PerformanceConfig, PerformancePreset, get_performance_config
from .connection_pool import get_http_session, init_connection_pool
from .memory import (
    clear_memory_cache,
    get_memory_stats,
    memory_efficient_iterator,
    optimize_dataframe_memory,
)

__all__ = [
    "CacheManager",
    "get_cache_stats",
    "PerformanceConfig",
    "PerformancePreset",
    "get_performance_config",
    "get_http_session",
    "init_connection_pool",
    "clear_memory_cache",
    "get_memory_stats",
    "memory_efficient_iterator",
    "optimize_dataframe_memory",
]
