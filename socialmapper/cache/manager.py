#!/usr/bin/env python3
"""Unified cache manager for SocialMapper.

This module provides a centralized cache management system that
coordinates all caching operations across the application.
"""

from pathlib import Path
from typing import Any, Dict

from ..console import get_logger
from .base import BaseCache, CacheStats
from .implementations import ParquetCache, PickleCache, SQLiteCache

logger = get_logger(__name__)


class UnifiedCacheManager:
    """Centralized cache manager for all SocialMapper caching needs.

    This manager provides a single interface for managing multiple
    cache types used throughout the application.

    Parameters
    ----------
    base_dir : str | Path, optional
        Base directory for all cache storage, by default "cache".
    """

    def __init__(self, base_dir: str | Path = "cache"):
        """Initialize the unified cache manager.

        Parameters
        ----------
        base_dir : str | Path, optional
            Base directory for all cache storage, by default "cache".
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Initialize different cache types
        self._caches: Dict[str, BaseCache] = {}
        self._init_default_caches()

    def _init_default_caches(self):
        """Initialize default cache instances."""
        # Network cache - uses pickle with compression for graph objects
        self._caches["network"] = PickleCache(
            cache_dir=self.base_dir / "networks",
            max_size_mb=5000.0,  # 5GB for network graphs
            ttl_hours=24 * 7,  # 1 week TTL
            compression_level=6
        )

        # Geocoding cache - uses SQLite for fast lookups
        self._caches["geocoding"] = SQLiteCache(
            cache_dir=self.base_dir / "geocoding",
            table_name="addresses",
            max_size_mb=500.0,  # 500MB for geocoding
            ttl_hours=24 * 30  # 30 days TTL
        )

        # Census cache - uses Parquet for DataFrames
        self._caches["census"] = ParquetCache(
            cache_dir=self.base_dir / "census",
            max_size_mb=1000.0,  # 1GB for census data
            ttl_hours=24 * 90  # 90 days TTL
        )

        # General purpose cache - uses SQLite
        self._caches["general"] = SQLiteCache(
            cache_dir=self.base_dir / "general",
            table_name="general",
            max_size_mb=100.0,  # 100MB for general use
            ttl_hours=24  # 24 hours TTL
        )

    def get_cache(self, cache_type: str) -> BaseCache:
        """Get a specific cache instance.

        Parameters
        ----------
        cache_type : str
            Type of cache to retrieve ("network", "geocoding", "census", "general").

        Returns
        -------
        BaseCache
            The requested cache instance.

        Raises
        ------
        ValueError
            If the cache type is not recognized.
        """
        if cache_type not in self._caches:
            raise ValueError(
                f"Unknown cache type: {cache_type}. "
                f"Available types: {list(self._caches.keys())}"
            )
        return self._caches[cache_type]

    def register_cache(
        self,
        name: str,
        cache: BaseCache,
        replace: bool = False
    ) -> None:
        """Register a custom cache instance.

        Parameters
        ----------
        name : str
            Name to register the cache under.
        cache : BaseCache
            Cache instance to register.
        replace : bool, optional
            Whether to replace existing cache, by default False.

        Raises
        ------
        ValueError
            If cache name already exists and replace is False.
        """
        if name in self._caches and not replace:
            raise ValueError(
                f"Cache '{name}' already exists. Set replace=True to override."
            )
        self._caches[name] = cache
        logger.info(f"Registered cache: {name}")

    def get_all_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all cache types.

        Returns
        -------
        Dict[str, CacheStats]
            Statistics for each cache type.
        """
        stats = {}
        for name, cache in self._caches.items():
            try:
                stats[name] = cache.get_stats()
            except Exception as e:
                logger.warning(f"Failed to get stats for cache '{name}': {e}")
                stats[name] = CacheStats(
                    total_requests=0,
                    cache_hits=0,
                    cache_misses=0,
                    total_size_mb=0.0,
                    item_count=0,
                    oldest_entry=None,
                    newest_entry=None
                )
        return stats

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics across all caches.

        Returns
        -------
        Dict[str, Any]
            Summary statistics including totals and per-cache breakdowns.
        """
        all_stats = self.get_all_stats()

        total_size_mb = sum(stats.total_size_mb for stats in all_stats.values())
        total_items = sum(stats.item_count for stats in all_stats.values())
        total_requests = sum(stats.total_requests for stats in all_stats.values())
        total_hits = sum(stats.cache_hits for stats in all_stats.values())
        total_misses = sum(stats.cache_misses for stats in all_stats.values())

        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "summary": {
                "total_size_mb": total_size_mb,
                "total_items": total_items,
                "total_requests": total_requests,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_rate_percent": hit_rate,
                "cache_types": list(self._caches.keys())
            },
            "per_cache": {
                name: {
                    "size_mb": stats.total_size_mb,
                    "items": stats.item_count,
                    "requests": stats.total_requests,
                    "hits": stats.cache_hits,
                    "misses": stats.cache_misses,
                    "hit_rate": (
                        (stats.cache_hits / stats.total_requests * 100)
                        if stats.total_requests > 0 else 0
                    ),
                    "oldest_entry": stats.oldest_entry.isoformat()
                    if stats.oldest_entry else None,
                    "newest_entry": stats.newest_entry.isoformat()
                    if stats.newest_entry else None,
                }
                for name, stats in all_stats.items()
            }
        }

    def clear_cache(self, cache_type: str | None = None) -> None:
        """Clear one or all cache types.

        Parameters
        ----------
        cache_type : str | None, optional
            Specific cache to clear, or None to clear all.
        """
        if cache_type:
            if cache_type not in self._caches:
                raise ValueError(f"Unknown cache type: {cache_type}")
            self._caches[cache_type].clear()
            logger.info(f"Cleared cache: {cache_type}")
        else:
            for name, cache in self._caches.items():
                cache.clear()
                logger.info(f"Cleared cache: {name}")

    def cleanup_all(self) -> None:
        """Run cleanup on all cache types."""
        for name, cache in self._caches.items():
            try:
                cache.cleanup()
                logger.debug(f"Cleaned up cache: {name}")
            except Exception as e:
                logger.warning(f"Failed to cleanup cache '{name}': {e}")

    def get_cache_dir(self, cache_type: str) -> Path:
        """Get the directory for a specific cache type.

        Parameters
        ----------
        cache_type : str
            Type of cache.

        Returns
        -------
        Path
            Directory path for the cache.
        """
        cache = self.get_cache(cache_type)
        return cache.cache_dir

    def cache_exists(self, cache_type: str, key: str) -> bool:
        """Check if a key exists in a specific cache.

        Parameters
        ----------
        cache_type : str
            Type of cache to check.
        key : str
            Cache key to check.

        Returns
        -------
        bool
            True if the key exists, False otherwise.
        """
        cache = self.get_cache(cache_type)
        return cache.exists(key)

    def get_from_cache(self, cache_type: str, key: str) -> Any | None:
        """Get a value from a specific cache.

        Parameters
        ----------
        cache_type : str
            Type of cache to query.
        key : str
            Cache key to retrieve.

        Returns
        -------
        Any | None
            The cached value if found, None otherwise.
        """
        cache = self.get_cache(cache_type)
        return cache.get(key)

    def put_to_cache(self, cache_type: str, key: str, value: Any) -> None:
        """Store a value in a specific cache.

        Parameters
        ----------
        cache_type : str
            Type of cache to use.
        key : str
            Cache key to store under.
        value : Any
            Value to cache.
        """
        cache = self.get_cache(cache_type)
        cache.put(key, value)


# Global instance for convenience
_global_cache_manager: UnifiedCacheManager | None = None


def get_cache_manager() -> UnifiedCacheManager:
    """Get the global cache manager instance.

    Returns
    -------
    UnifiedCacheManager
        The global cache manager.
    """
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = UnifiedCacheManager()
    return _global_cache_manager


def set_cache_manager(manager: UnifiedCacheManager) -> None:
    """Set the global cache manager instance.

    Parameters
    ----------
    manager : UnifiedCacheManager
        Cache manager to use globally.
    """
    global _global_cache_manager
    _global_cache_manager = manager