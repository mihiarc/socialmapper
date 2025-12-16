"""Unified caching system for SocialMapper.

Provides a centralized cache manager for Census API responses,
geocoding results, network graphs, and other frequently accessed data.

This module consolidates all caching functionality including:
- Census data caching
- Geocoding result caching
- Network graph cache statistics
- Cache administration (clearing, statistics)
"""

import functools
import hashlib
import logging
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import diskcache as dc

from .config import PerformanceConfig

logger = logging.getLogger(__name__)

# Global cache instances
_census_cache: dc.Cache | None = None
_geocoding_cache: dc.Cache | None = None


class CacheManager:
    """Unified cache manager for all SocialMapper caching needs.

    Manages separate caches for different data types with configurable
    TTL and size limits. Provides decorator for easy function caching.

    Parameters
    ----------
    config : PerformanceConfig
        Performance configuration with cache settings.

    Examples
    --------
    >>> from socialmapper.performance import get_performance_config
    >>> config = get_performance_config(preset='balanced')
    >>> cache = CacheManager(config)
    >>>
    >>> # Cache a value
    >>> cache.set_census('key', {'data': 'value'}, ttl_hours=24)
    >>>
    >>> # Retrieve cached value
    >>> result = cache.get_census('key')
    >>>
    >>> # Use as decorator
    >>> @cache.cache_census_data(ttl_hours=24)
    ... def fetch_data(location):
    ...     # Expensive API call
    ...     return api_call(location)
    """

    def __init__(self, config: PerformanceConfig | None = None):
        """Initialize cache manager.

        Parameters
        ----------
        config : PerformanceConfig, optional
            Performance configuration. Creates balanced config if None.
        """
        if config is None:
            from .config import get_performance_config
            config = get_performance_config(preset='balanced')

        self.config = config

        # Get base cache directory from environment
        base_cache_dir = os.environ.get('SOCIALMAPPER_CACHE_DIR', 'cache')
        self._base_path = Path(base_cache_dir)

        # Initialize caches
        self._census_cache = self._init_cache('census', config.census_cache_size_mb)
        self._geocoding_cache = self._init_cache('geocoding', config.geocoding_cache_size_mb)

        logger.info(
            f"Initialized CacheManager with preset='{config.preset}' "
            f"(Census: {config.census_cache_size_mb}MB, "
            f"Geocoding: {config.geocoding_cache_size_mb}MB, "
            f"TTL: {config.cache_ttl_hours}h)"
        )

    def _init_cache(self, cache_name: str, size_mb: int) -> dc.Cache:
        """Initialize a disk cache instance.

        Parameters
        ----------
        cache_name : str
            Name of the cache (used for directory).
        size_mb : int
            Maximum size in megabytes.

        Returns
        -------
        dc.Cache
            Initialized disk cache instance.
        """
        cache_dir = self._base_path / cache_name
        cache_dir.mkdir(parents=True, exist_ok=True)

        size_limit = size_mb * 1024 * 1024  # Convert MB to bytes

        return dc.Cache(
            str(cache_dir),
            size_limit=size_limit,
            eviction_policy='least-recently-used'
        )

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments.

        Parameters
        ----------
        *args
            Positional arguments.
        **kwargs
            Keyword arguments.

        Returns
        -------
        str
            SHA-256 hash of serialized arguments.
        """
        # Create deterministic string representation
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)

        return hashlib.sha256(key_string.encode()).hexdigest()

    # Census data caching methods

    def get_census(self, key: str) -> Any | None:
        """Get cached Census data.

        Parameters
        ----------
        key : str
            Cache key.

        Returns
        -------
        Any or None
            Cached value or None if not found/expired.

        Examples
        --------
        >>> data = cache.get_census('population_060370001001')
        >>> if data is not None:
        ...     print("Cache hit!")
        """
        return self._census_cache.get(key, default=None)

    def set_census(self, key: str, value: Any, ttl_hours: int | None = None):
        """Cache Census data.

        Parameters
        ----------
        key : str
            Cache key.
        value : Any
            Value to cache.
        ttl_hours : int, optional
            Time-to-live in hours. Uses config default if None.

        Examples
        --------
        >>> cache.set_census('population_060370001001',
        ...                  {'B01003_001E': 2543},
        ...                  ttl_hours=24)
        """
        ttl = ttl_hours or self.config.cache_ttl_hours
        expire_seconds = ttl * 3600
        self._census_cache.set(key, value, expire=expire_seconds)

    def cache_census_data(self, ttl_hours: int | None = None) -> Callable:
        """Create a decorator to cache Census data function results.

        Parameters
        ----------
        ttl_hours : int, optional
            Time-to-live in hours. Uses config default if None.

        Returns
        -------
        Callable
            Decorated function with caching.

        Examples
        --------
        >>> @cache.cache_census_data(ttl_hours=24)
        ... def fetch_census_data(geoid, variables):
        ...     # Expensive API call
        ...     return census_api.get(geoid, variables)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{func.__name__}:{self._generate_key(*args, **kwargs)}"

                # Check cache
                cached = self.get_census(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached

                # Call function and cache result
                result = func(*args, **kwargs)
                self.set_census(cache_key, result, ttl_hours=ttl_hours)

                return result

            return wrapper
        return decorator

    # Geocoding caching methods

    def get_geocoding(self, key: str) -> Any | None:
        """Get cached geocoding result.

        Parameters
        ----------
        key : str
            Cache key.

        Returns
        -------
        Any or None
            Cached value or None if not found/expired.

        Examples
        --------
        >>> result = cache.get_geocoding('123_main_st_seattle_wa')
        >>> if result is not None:
        ...     print(f"Cached coords: {result['lat']}, {result['lon']}")
        """
        return self._geocoding_cache.get(key, default=None)

    def set_geocoding(self, key: str, value: Any, ttl_hours: int | None = None):
        """Cache geocoding result.

        Parameters
        ----------
        key : str
            Cache key.
        value : Any
            Value to cache.
        ttl_hours : int, optional
            Time-to-live in hours. Uses config default if None.

        Examples
        --------
        >>> cache.set_geocoding('123_main_st_seattle_wa',
        ...                     {'lat': 47.6062, 'lon': -122.3321},
        ...                     ttl_hours=720)  # 30 days
        """
        ttl = ttl_hours or self.config.cache_ttl_hours
        expire_seconds = ttl * 3600
        self._geocoding_cache.set(key, value, expire=expire_seconds)

    def cache_geocoding_result(self, ttl_hours: int | None = None) -> Callable:
        """Create a decorator to cache geocoding function results.

        Parameters
        ----------
        ttl_hours : int, optional
            Time-to-live in hours. Uses config default if None.

        Returns
        -------
        Callable
            Decorated function with caching.

        Examples
        --------
        >>> @cache.cache_geocoding_result(ttl_hours=720)
        ... def geocode_address(address):
        ...     # Expensive geocoding call
        ...     return geocoding_api.geocode(address)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{func.__name__}:{self._generate_key(*args, **kwargs)}"

                # Check cache
                cached = self.get_geocoding(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached

                # Call function and cache result
                result = func(*args, **kwargs)
                self.set_geocoding(cache_key, result, ttl_hours=ttl_hours)

                return result

            return wrapper
        return decorator

    # Cache management methods

    def clear_census(self):
        """Clear all Census data cache.

        Examples
        --------
        >>> cache.clear_census()
        """
        self._census_cache.clear()
        logger.info("Cleared Census data cache")

    def clear_geocoding(self):
        """Clear all geocoding cache.

        Examples
        --------
        >>> cache.clear_geocoding()
        """
        self._geocoding_cache.clear()
        logger.info("Cleared geocoding cache")

    def clear_all(self):
        """Clear all caches.

        Examples
        --------
        >>> cache.clear_all()
        """
        self.clear_census()
        self.clear_geocoding()
        logger.info("Cleared all caches")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns
        -------
        dict
            Dictionary with cache statistics for each cache type.

        Examples
        --------
        >>> stats = cache.get_stats()
        >>> print(f"Census cache: {stats['census']['size_mb']:.2f} MB")
        >>> print(f"Geocoding cache: {stats['geocoding']['size_mb']:.2f} MB")
        """
        return {
            "census": {
                "size_mb": self._census_cache.volume() / (1024 * 1024),
                "count": len(self._census_cache),
                "limit_mb": self.config.census_cache_size_mb
            },
            "geocoding": {
                "size_mb": self._geocoding_cache.volume() / (1024 * 1024),
                "count": len(self._geocoding_cache),
                "limit_mb": self.config.geocoding_cache_size_mb
            }
        }

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics for all cache subsystems.

        Collects size, item count, and status information from
        all cache types including network cache.

        Returns
        -------
        dict
            Nested dictionary with keys 'summary',
            'network_cache', 'geocoding_cache', 'census_cache'.
            Summary contains 'total_size_mb', 'total_items',
            'last_updated'.

        Examples
        --------
        >>> cache = CacheManager()
        >>> stats = cache.get_cache_statistics()
        >>> stats['summary']['total_size_mb']
        45.3
        """
        from ..isochrone.cache import get_cache_stats as get_network_stats

        stats = {
            "summary": {
                "total_size_mb": 0,
                "total_items": 0,
                "last_updated": datetime.now().isoformat(),
            },
            "network_cache": self._get_network_cache_stats(get_network_stats),
            "geocoding_cache": {
                "size_mb": self._geocoding_cache.volume() / (1024 * 1024),
                "item_count": len(self._geocoding_cache),
                "status": "active" if len(self._geocoding_cache) > 0 else "empty",
                "location": str(self._base_path / "geocoding"),
            },
            "census_cache": {
                "size_mb": self._census_cache.volume() / (1024 * 1024),
                "item_count": len(self._census_cache),
                "status": "active" if len(self._census_cache) > 0 else "empty",
                "location": str(self._base_path / "census"),
            },
        }

        # Calculate totals
        for cache_type in ["network_cache", "geocoding_cache", "census_cache"]:
            cache_stats = stats[cache_type]
            stats["summary"]["total_size_mb"] += cache_stats.get("size_mb", 0)
            stats["summary"]["total_items"] += cache_stats.get("item_count", 0)

        return stats

    def _get_network_cache_stats(self, get_network_stats) -> dict[str, Any]:
        """Get statistics for network routing cache."""
        try:
            cache_stats = get_network_stats()
            return {
                "size_mb": cache_stats.get("size_mb", 0),
                "item_count": cache_stats.get("count", 0),
                "status": "active" if cache_stats.get("count", 0) > 0 else "empty",
                "location": str(self._base_path / "networks"),
            }
        except (OSError, KeyError, ValueError, AttributeError) as e:
            logger.error(f"Failed to get network cache stats: {e}")
            return {"size_mb": 0, "item_count": 0, "status": "error", "error": str(e)}

    def clear_network_cache(self) -> dict[str, Any]:
        """Clear the network routing cache.

        Returns
        -------
        dict
            Dictionary with 'success', 'message', 'cleared_size_mb'.
        """
        try:
            from ..isochrone.cache import clear_cache as clear_network
            from ..isochrone.cache import get_cache_stats as get_network_stats

            stats_before = get_network_stats()
            clear_network()

            return {
                "success": True,
                "message": "Network cache cleared successfully",
                "cleared_size_mb": stats_before.get("size_mb", 0),
            }
        except (OSError, KeyError, ValueError, AttributeError) as e:
            logger.error(f"Failed to clear network cache: {e}")
            return {"success": False, "error": str(e)}

    def clear_all_caches(self) -> dict[str, Any]:
        """Clear all cache subsystems.

        Returns
        -------
        dict
            Nested dictionary with results for each cache type
            plus summary.
        """
        results = {
            "network": self.clear_network_cache(),
            "geocoding": {"success": True, "cleared_size_mb": self._geocoding_cache.volume() / (1024 * 1024)},
            "census": {"success": True, "cleared_size_mb": self._census_cache.volume() / (1024 * 1024)},
        }

        # Clear the caches
        self.clear_geocoding()
        self.clear_census()

        # Calculate totals
        total_cleared_mb = sum(result.get("cleared_size_mb", 0) for result in results.values())
        all_successful = all(result.get("success", False) for result in results.values())

        results["summary"] = {
            "success": all_successful,
            "total_cleared_mb": total_cleared_mb,
            "timestamp": datetime.now().isoformat(),
        }

        return results

    def close(self):
        """Close all caches and release resources.

        Examples
        --------
        >>> cache.close()
        """
        if self._census_cache is not None:
            self._census_cache.close()
        if self._geocoding_cache is not None:
            self._geocoding_cache.close()
        logger.debug("Closed all caches")

    def __enter__(self):
        """Context manager entry.

        Returns
        -------
        CacheManager
            Self for use in with statements.

        Examples
        --------
        >>> with CacheManager() as cache:
        ...     data = cache.get_census('key')
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def get_cache_stats() -> dict[str, Any]:
    """Get global cache statistics.

    Convenience function to get statistics from all active caches
    including network graph cache from isochrone module.

    Returns
    -------
    dict
        Dictionary with statistics for all cache types.

    Examples
    --------
    >>> from socialmapper.performance import get_cache_stats
    >>> stats = get_cache_stats()
    >>> for cache_type, cache_stats in stats.items():
    ...     print(f"{cache_type}: {cache_stats['size_mb']:.2f} MB")
    """
    from ..isochrone.cache import get_cache_stats as get_network_stats

    stats = {
        "network": get_network_stats()
    }

    # Add census and geocoding stats if caches exist
    if _census_cache is not None:
        stats["census"] = {
            "size_mb": _census_cache.volume() / (1024 * 1024),
            "count": len(_census_cache)
        }

    if _geocoding_cache is not None:
        stats["geocoding"] = {
            "size_mb": _geocoding_cache.volume() / (1024 * 1024),
            "count": len(_geocoding_cache)
        }

    return stats


# Module-level convenience functions for cache administration
# These maintain backward compatibility with the old cache_manager module

def get_cache_statistics() -> dict[str, Any]:
    """Get comprehensive statistics for all caches.

    Convenience function that creates a manager and collects all
    cache statistics in one call.

    Returns
    -------
    dict
        Nested dictionary with 'summary' and individual cache
        type statistics.

    Examples
    --------
    >>> stats = get_cache_statistics()
    >>> total_mb = stats['summary']['total_size_mb']
    >>> total_mb >= 0
    True
    """
    manager = CacheManager()
    return manager.get_cache_statistics()


def clear_all_caches() -> dict[str, Any]:
    """Clear all SocialMapper cache subsystems.

    Convenience function for removing all cached data in one call.

    Returns
    -------
    dict
        Dictionary with results for each cache type plus summary.

    Examples
    --------
    >>> result = clear_all_caches()
    >>> result['summary']['success']
    True
    """
    manager = CacheManager()
    return manager.clear_all_caches()


def clear_geocoding_cache() -> dict[str, Any]:
    """Clear the geocoding address cache.

    Returns
    -------
    dict
        Dictionary with 'success', 'message', 'cleared_size_mb'.
    """
    manager = CacheManager()
    stats_before = manager.get_stats()
    manager.clear_geocoding()
    return {
        "success": True,
        "message": "Geocoding cache cleared successfully",
        "cleared_size_mb": stats_before["geocoding"]["size_mb"],
    }


def clear_census_cache() -> dict[str, Any]:
    """Clear the census data cache.

    Returns
    -------
    dict
        Dictionary with 'success', 'message', 'cleared_size_mb'.
    """
    manager = CacheManager()
    stats_before = manager.get_stats()
    manager.clear_census()
    return {
        "success": True,
        "message": "Census cache cleared successfully",
        "cleared_size_mb": stats_before["census"]["size_mb"],
    }


def cleanup_expired_cache_entries() -> dict[str, Any]:
    """Clean up expired entries from all caches.

    Returns
    -------
    dict
        Dictionary with status for each cache type.
    """
    return {
        "census": {
            "success": True,
            "message": "Census cache uses LRU eviction",
        },
        "network": {
            "success": True,
            "message": "Network cache uses LRU eviction",
        },
        "geocoding": {
            "success": True,
            "message": "Geocoding cache uses LRU eviction",
        },
    }
