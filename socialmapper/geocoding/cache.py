#!/usr/bin/env python3
"""Simple disk-based caching for geocoding results.

Uses diskcache for simple, reliable caching of geocoded addresses.
"""

import logging
import os
from pathlib import Path

import diskcache as dc

from .models import AddressInput, GeocodingConfig, GeocodingResult

logger = logging.getLogger(__name__)


class AddressCache:
    """Simple caching system for geocoded addresses using diskcache.

    Uses environment variables for configuration:
    - SOCIALMAPPER_CACHE_DIR: Base cache directory (default: 'cache')

    Parameters
    ----------
    config : GeocodingConfig
        Configuration including TTL and cache settings.

    Examples
    --------
    >>> config = GeocodingConfig(enable_cache=True, cache_ttl_hours=24)
    >>> cache = AddressCache(config)
    >>> result = cache.get(address)
    """

    def __init__(self, config: GeocodingConfig):
        """Initialize the address cache.

        Parameters
        ----------
        config : GeocodingConfig
            Configuration for caching behavior.
        """
        self.config = config

        # Use environment variable for cache directory
        base_cache_dir = os.environ.get('SOCIALMAPPER_CACHE_DIR', 'cache')
        cache_dir = Path(base_cache_dir) / 'geocoding'
        cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing geocoding cache: dir={cache_dir}, ttl={config.cache_ttl_hours}h")

        # diskcache handles thread safety, compression, and eviction
        self._cache = dc.Cache(
            str(cache_dir),
            size_limit=config.cache_max_size * 1024,  # Convert to bytes
        )

    def get(self, address: AddressInput) -> GeocodingResult | None:
        """Get cached result for address.

        Parameters
        ----------
        address : AddressInput
            The address to look up.

        Returns
        -------
        GeocodingResult | None
            Cached result if found and not expired, None otherwise.

        Examples
        --------
        >>> result = cache.get(address)
        >>> if result:
        ...     print(f"Cached: {result.latitude}, {result.longitude}")
        """
        if not self.config.enable_cache:
            return None

        cache_key = address.get_cache_key()

        # Use diskcache's built-in expiration support to avoid race conditions
        # The 'expire_time' parameter ensures atomic TTL checking
        cached_data = self._cache.get(cache_key, default=None, expire_time=True)

        if cached_data is None:
            return None

        try:
            # Reconstruct GeocodingResult from cached data
            result_data = cached_data["result"]
            result_data["input_address"] = address
            return GeocodingResult(**result_data)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to deserialize cached result: {e}")
            # Invalid data - remove from cache
            self._cache.delete(cache_key)
            return None

    def put(self, result: GeocodingResult):
        """Cache a geocoding result.

        Parameters
        ----------
        result : GeocodingResult
            The geocoding result to cache.

        Examples
        --------
        >>> cache.put(geocoding_result)
        """
        if not self.config.enable_cache:
            return

        cache_key = result.input_address.get_cache_key()

        # Store result with TTL using diskcache's built-in expiration
        cache_data = {
            "result": result.model_dump(),
        }

        # Set with expiration time to avoid race conditions
        ttl_seconds = self.config.cache_ttl_hours * 3600
        self._cache.set(cache_key, cache_data, expire=ttl_seconds)

    def save_cache(self):
        """Save cache to disk.

        Note: diskcache automatically persists to disk, so this is a no-op
        for compatibility with the old API.

        Examples
        --------
        >>> cache.save_cache()  # No-op, kept for compatibility
        """
        # diskcache automatically persists, so this is a no-op

    def close(self):
        """Close the cache and release resources.

        Examples
        --------
        >>> cache = AddressCache(config)
        >>> cache.close()
        """
        if self._cache is not None:
            self._cache.close()

    def __enter__(self):
        """Context manager entry.

        Returns
        -------
        AddressCache
            Self for use in with statements.

        Examples
        --------
        >>> with AddressCache(config) as cache:
        ...     result = cache.get(address)
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit.

        Parameters
        ----------
        exc_type : type
            Exception type if an exception occurred.
        exc_val : Exception
            Exception value if an exception occurred.
        exc_tb : traceback
            Exception traceback if an exception occurred.

        Returns
        -------
        bool
            False to propagate any exception.
        """
        self.close()
        return False
