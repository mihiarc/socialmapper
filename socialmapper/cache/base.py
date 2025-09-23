#!/usr/bin/env python3
"""Base cache interface for unified caching strategy.

This module provides an abstract base class that all cache implementations
should inherit from, ensuring consistent behavior across the application.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    total_requests: int
    cache_hits: int
    cache_misses: int
    total_size_mb: float
    item_count: int
    oldest_entry: datetime | None
    newest_entry: datetime | None


class BaseCache(ABC, Generic[T]):
    """Abstract base class for all cache implementations.

    This class defines the interface that all cache implementations must follow
    to ensure consistent behavior and allow for easy swapping of cache backends.

    Parameters
    ----------
    cache_dir : str | Path
        Directory to store cache files.
    max_size_mb : float, optional
        Maximum cache size in megabytes, by default 1000.0.
    ttl_hours : float, optional
        Time-to-live for cache entries in hours, by default 24.0.
    """

    def __init__(
        self,
        cache_dir: str | Path,
        max_size_mb: float = 1000.0,
        ttl_hours: float = 24.0
    ):
        """Initialize the base cache.

        Parameters
        ----------
        cache_dir : str | Path
            Directory to store cache files.
        max_size_mb : float, optional
            Maximum cache size in megabytes, by default 1000.0.
        ttl_hours : float, optional
            Time-to-live for cache entries in hours, by default 24.0.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.ttl_hours = ttl_hours
        self._stats = CacheStats(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            total_size_mb=0.0,
            item_count=0,
            oldest_entry=None,
            newest_entry=None
        )

    @abstractmethod
    def get(self, key: str) -> T | None:
        """Retrieve an item from the cache.

        Parameters
        ----------
        key : str
            The cache key to retrieve.

        Returns
        -------
        T | None
            The cached item if found and valid, None otherwise.
        """
        pass

    @abstractmethod
    def put(self, key: str, value: T) -> None:
        """Store an item in the cache.

        Parameters
        ----------
        key : str
            The cache key to store under.
        value : T
            The value to cache.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an item from the cache.

        Parameters
        ----------
        key : str
            The cache key to delete.

        Returns
        -------
        bool
            True if the item was deleted, False if not found.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all items from the cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Parameters
        ----------
        key : str
            The cache key to check.

        Returns
        -------
        bool
            True if the key exists, False otherwise.
        """
        pass

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns
        -------
        CacheStats
            Statistics about cache performance and size.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up expired entries and enforce size limits."""
        pass

    def get_cache_key(self, *args: Any) -> str:
        """Generate a cache key from arguments.

        Parameters
        ----------
        *args : Any
            Arguments to generate key from.

        Returns
        -------
        str
            A unique cache key.
        """
        import hashlib
        import json

        # Convert args to a stable string representation
        key_data = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()

    def is_expired(self, timestamp: datetime) -> bool:
        """Check if a cached item has expired.

        Parameters
        ----------
        timestamp : datetime
            The timestamp when the item was cached.

        Returns
        -------
        bool
            True if the item has expired, False otherwise.
        """
        from datetime import timedelta

        age = datetime.now() - timestamp
        return age > timedelta(hours=self.ttl_hours)