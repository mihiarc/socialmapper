"""Batch processing utilities for efficient API requests.

Provides optimized batch processing for Census API and other
data sources to minimize API calls and improve performance.
"""

import logging
from collections import defaultdict
from typing import Any

from .cache import CacheManager
from .config import PerformanceConfig
from .connection_pool import get_http_session

logger = logging.getLogger(__name__)


class BatchCensusDataFetcher:
    """Optimized batch fetcher for Census API data.

    Implements intelligent batching, caching, and connection pooling
    to minimize API calls and improve performance.

    Parameters
    ----------
    config : PerformanceConfig, optional
        Performance configuration. Creates balanced config if None.
    cache : CacheManager, optional
        Cache manager instance. Creates new instance if None.

    Examples
    --------
    >>> from socialmapper.performance import BatchCensusDataFetcher
    >>> fetcher = BatchCensusDataFetcher()
    >>>
    >>> # Fetch data for multiple GEOIDs efficiently
    >>> geoids = ['060370001001', '060370001002', '060370001003']
    >>> variables = ['B01003_001E', 'B19013_001E']
    >>> results = fetcher.fetch_batch(geoids, variables, year=2023)
    """

    def __init__(
        self,
        config: PerformanceConfig | None = None,
        cache: CacheManager | None = None
    ):
        """Initialize batch Census data fetcher.

        Parameters
        ----------
        config : PerformanceConfig, optional
            Performance configuration.
        cache : CacheManager, optional
            Cache manager instance.
        """
        if config is None:
            from .config import get_performance_config
            config = get_performance_config(preset='balanced')

        self.config = config
        self.cache = cache or CacheManager(config)
        self.session = get_http_session()

    def fetch_batch(
        self,
        geoids: list[str],
        variables: list[str],
        year: int = 2023
    ) -> dict[str, dict[str, Any]]:
        """Fetch Census data for multiple GEOIDs with caching.

        Implements intelligent caching and batching to minimize
        API calls. Checks cache first, then fetches missing data
        in optimized batches.

        Parameters
        ----------
        geoids : list of str
            List of 12-digit census GEOIDs.
        variables : list of str
            List of census variable codes.
        year : int, optional
            Census year, by default 2023.

        Returns
        -------
        dict
            Nested dictionary: {geoid: {variable: value, ...}, ...}

        Examples
        --------
        >>> fetcher = BatchCensusDataFetcher()
        >>> geoids = ['060370001001', '060370001002']
        >>> variables = ['B01003_001E']
        >>> data = fetcher.fetch_batch(geoids, variables)
        >>> data['060370001001']['B01003_001E']
        2543
        """
        if not geoids or not variables:
            return {}

        results = {}
        cache_misses = []

        # Check cache first
        for geoid in geoids:
            cache_key = self._make_cache_key(geoid, variables, year)
            cached = self.cache.get_census(cache_key)

            if cached is not None:
                results[geoid] = cached
                logger.debug(f"Cache hit for GEOID {geoid}")
            else:
                cache_misses.append(geoid)

        logger.info(
            f"Census data cache: {len(results)} hits, "
            f"{len(cache_misses)} misses ({len(geoids)} total)"
        )

        # Fetch missing data if needed
        if cache_misses:
            fetched_data = self._fetch_from_api(cache_misses, variables, year)

            # Cache the results
            for geoid, data in fetched_data.items():
                cache_key = self._make_cache_key(geoid, variables, year)
                self.cache.set_census(cache_key, data)
                results[geoid] = data

        return results

    def _make_cache_key(
        self,
        geoid: str,
        variables: list[str],
        year: int
    ) -> str:
        """Generate cache key for Census data.

        Parameters
        ----------
        geoid : str
            Census GEOID.
        variables : list of str
            Variable codes.
        year : int
            Census year.

        Returns
        -------
        str
            Cache key string.
        """
        vars_str = "|".join(sorted(variables))
        return f"census_{year}_{geoid}_{vars_str}"

    def _fetch_from_api(
        self,
        geoids: list[str],
        variables: list[str],
        year: int
    ) -> dict[str, dict[str, Any]]:
        """Fetch data from Census API with optimized batching.

        Parameters
        ----------
        geoids : list of str
            GEOIDs to fetch.
        variables : list of str
            Variables to fetch.
        year : int
            Census year.

        Returns
        -------
        dict
            Fetched data: {geoid: {variable: value, ...}, ...}
        """
        from .._census import VARIABLE_MAPPING, fetch_census_data

        # Group by state for efficient querying
        geoids_by_state = defaultdict(list)
        for geoid in geoids:
            if len(geoid) >= 2:
                state = geoid[:2]
                geoids_by_state[state].append(geoid)

        results = {}

        # Fetch data for each state
        for state, state_geoids in geoids_by_state.items():
            # Process in batches
            batch_size = self.config.batch_size_census

            for i in range(0, len(state_geoids), batch_size):
                batch = state_geoids[i:i + batch_size]

                try:
                    # Use existing fetch_census_data function
                    batch_data = fetch_census_data(batch, variables, year)
                    results.update(batch_data)

                    logger.debug(
                        f"Fetched Census data for {len(batch)} GEOIDs "
                        f"(state {state}, batch {i // batch_size + 1})"
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch batch for state {state}: {e}")
                    # Continue with other batches
                    continue

        return results


class BatchGeocodingFetcher:
    """Optimized batch fetcher for geocoding requests.

    Implements caching and batching for geocoding operations
    to reduce API calls and improve performance.

    Parameters
    ----------
    config : PerformanceConfig, optional
        Performance configuration. Creates balanced config if None.
    cache : CacheManager, optional
        Cache manager instance. Creates new instance if None.

    Examples
    --------
    >>> from socialmapper.performance import BatchGeocodingFetcher
    >>> fetcher = BatchGeocodingFetcher()
    >>>
    >>> # Geocode multiple addresses efficiently
    >>> addresses = ['123 Main St, Seattle, WA', '456 Oak Ave, Portland, OR']
    >>> results = fetcher.geocode_batch(addresses)
    """

    def __init__(
        self,
        config: PerformanceConfig | None = None,
        cache: CacheManager | None = None
    ):
        """Initialize batch geocoding fetcher.

        Parameters
        ----------
        config : PerformanceConfig, optional
            Performance configuration.
        cache : CacheManager, optional
            Cache manager instance.
        """
        if config is None:
            from .config import get_performance_config
            config = get_performance_config(preset='balanced')

        self.config = config
        self.cache = cache or CacheManager(config)
        self.session = get_http_session()

    def geocode_batch(
        self,
        addresses: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Geocode multiple addresses with caching.

        Parameters
        ----------
        addresses : list of str
            List of address strings to geocode.

        Returns
        -------
        dict
            Geocoding results: {address: {lat, lon, ...}, ...}

        Examples
        --------
        >>> fetcher = BatchGeocodingFetcher()
        >>> addresses = ['1600 Pennsylvania Ave NW, Washington, DC']
        >>> results = fetcher.geocode_batch(addresses)
        >>> results[addresses[0]]['lat']
        38.8977
        """
        if not addresses:
            return {}

        results = {}
        cache_misses = []

        # Check cache first
        for address in addresses:
            cache_key = self._make_cache_key(address)
            cached = self.cache.get_geocoding(cache_key)

            if cached is not None:
                results[address] = cached
                logger.debug(f"Cache hit for address: {address}")
            else:
                cache_misses.append(address)

        logger.info(
            f"Geocoding cache: {len(results)} hits, "
            f"{len(cache_misses)} misses ({len(addresses)} total)"
        )

        # Geocode missing addresses
        if cache_misses:
            geocoded = self._geocode_from_api(cache_misses)

            # Cache the results
            for address, data in geocoded.items():
                cache_key = self._make_cache_key(address)
                # Use longer TTL for geocoding (addresses don't change)
                self.cache.set_geocoding(cache_key, data, ttl_hours=720)  # 30 days
                results[address] = data

        return results

    def _make_cache_key(self, address: str) -> str:
        """Generate cache key for geocoding result.

        Parameters
        ----------
        address : str
            Address string.

        Returns
        -------
        str
            Cache key string.
        """
        # Normalize address for consistent caching
        normalized = address.lower().strip()
        return f"geocode_{normalized}"

    def _geocode_from_api(
        self,
        addresses: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Geocode addresses using Census Geocoding API.

        Parameters
        ----------
        addresses : list of str
            Addresses to geocode.

        Returns
        -------
        dict
            Geocoding results: {address: {lat, lon, ...}, ...}
        """
        from .._geocoding import geocode_address

        results = {}
        batch_size = self.config.batch_size_geocoding

        # Process in batches to avoid overwhelming the API
        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]

            for address in batch:
                try:
                    result = geocode_address(address)
                    if result:
                        results[address] = {
                            'lat': result.get('lat'),
                            'lon': result.get('lon'),
                            'match_type': result.get('match_type'),
                            'formatted_address': result.get('formatted_address')
                        }
                        logger.debug(f"Geocoded: {address}")
                except Exception as e:
                    logger.warning(f"Failed to geocode '{address}': {e}")
                    continue

        return results
