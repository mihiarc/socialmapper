#!/usr/bin/env python3
"""Simple disk-based caching for geocoding results.

Uses diskcache for simple, reliable caching of geocoded addresses.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import diskcache as dc

from .models import AddressInput, GeocodingConfig, GeocodingResult

logger = logging.getLogger(__name__)


class AddressCache:
    """Simple caching system for geocoded addresses using diskcache.

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
        cache_dir = Path("cache/geocoding")
        cache_dir.mkdir(parents=True, exist_ok=True)

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
        cached_data = self._cache.get(cache_key)

        if cached_data is None:
            return None

        # Check if expired
        timestamp = cached_data.get("timestamp")
        if timestamp:
            age = datetime.now() - timestamp
            if age > timedelta(hours=self.config.cache_ttl_hours):
                # Expired, remove from cache
                self._cache.delete(cache_key)
                return None

        try:
            # Reconstruct GeocodingResult from cached data
            result_data = cached_data["result"]
            result_data["input_address"] = address
            return GeocodingResult(**result_data)
        except Exception as e:
            logger.warning(f"Failed to deserialize cached result: {e}")
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

        # Store result with timestamp
        cache_data = {
            "result": result.model_dump(),
            "timestamp": datetime.now(),
        }

        self._cache.set(cache_key, cache_data)

    def save_cache(self):
        """Save cache to disk.

        Note: diskcache automatically persists to disk, so this is a no-op
        for compatibility with the old API.

        Examples
        --------
        >>> cache.save_cache()  # No-op, kept for compatibility
        """
        # diskcache automatically persists, so this is a no-op
        pass
