"""Enhanced Census Bureau API client with improved reliability features.

This enhanced client includes:
- Connection pooling for better performance
- Circuit breaker pattern for fault tolerance
- Request deduplication to prevent duplicate calls
- Comprehensive metrics collection
- Batch request optimization
"""

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...constants import HTTP_TOO_MANY_REQUESTS, COUNTY_FIPS_LENGTH, STATE_FIPS_LENGTH
from ..domain.interfaces import ConfigurationProvider
from .api_client import CensusAPIClientImpl, CensusAPIError, CensusAPIRateLimitError
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError
from .metrics import MetricsCollector, RequestTimer
from .request_deduplicator import RequestDeduplicator, deduplicate_key


class EnhancedCensusAPIClient(CensusAPIClientImpl):
    """Enhanced Census API client with reliability improvements."""

    def __init__(self, config: ConfigurationProvider, logger: logging.Logger):
        """Initialize enhanced client with additional features."""
        super().__init__(config, logger)

        # Initialize new components
        self._circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                success_threshold=2,
                excluded_exceptions=(CensusAPIRateLimitError,),
            )
        )
        self._deduplicator = RequestDeduplicator()
        self._metrics = MetricsCollector()

        # Configure connection pooling
        self._configure_connection_pool()

    def _configure_connection_pool(self) -> None:
        """Configure HTTP adapter with connection pooling and retry strategy."""
        # Create adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection pools
            pool_maxsize=10,  # Connections per pool
            pool_block=False,  # Don't block when pool is full
            max_retries=Retry(
                total=0,  # We handle retries ourselves
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504],
            ),
        )

        # Mount adapter for both HTTP and HTTPS
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        self._logger.info("Configured connection pooling with max 10 connections")

    def get_census_data(
        self, variables: list[str], geography: str, year: int, dataset: str, **kwargs
    ) -> dict[str, Any]:
        """Fetch census data with enhanced reliability features.

        This method adds:
        - Circuit breaker protection
        - Request deduplication
        - Metrics collection
        - Batch optimization for multiple counties
        """
        # Generate deduplication key
        dedup_key = deduplicate_key(variables, geography, year, dataset, **kwargs)

        try:
            # Use deduplicator to prevent concurrent duplicate requests
            return self._deduplicator.deduplicate(
                dedup_key,
                lambda: self._get_census_data_with_circuit_breaker(
                    variables, geography, year, dataset, **kwargs
                ),
                timeout=self._timeout * 2,  # Allow extra time for deduplication
            )
        except Exception as e:
            self._logger.error(f"Census data request failed: {e}")
            raise

    def _get_census_data_with_circuit_breaker(
        self, variables: list[str], geography: str, year: int, dataset: str, **kwargs
    ) -> dict[str, Any]:
        """Fetch census data with circuit breaker protection."""
        try:
            # Check circuit breaker state
            if self._circuit_breaker.is_open:
                status = self._circuit_breaker.get_status()
                self._metrics.record_error("CircuitBreakerOpen", f"Recovery in {status['recovery_time']:.1f}s")
                raise CensusAPIError(
                    f"Circuit breaker is open due to repeated failures. "
                    f"Retry in {status['recovery_time']:.1f} seconds"
                )

            # Execute request with circuit breaker
            return self._circuit_breaker.call(
                self._fetch_census_data_internal,
                variables, geography, year, dataset, **kwargs
            )
        except CircuitBreakerError as e:
            self._metrics.record_circuit_breaker_open()
            raise CensusAPIError(str(e)) from e

    def _fetch_census_data_internal(
        self, variables: list[str], geography: str, year: int, dataset: str, **kwargs
    ) -> dict[str, Any]:
        """Internal method to fetch census data with metrics."""
        with RequestTimer(self._metrics):
            return super().get_census_data(variables, geography, year, dataset, **kwargs)

    def get_census_data_batch(
        self,
        geoids: list[str],
        variables: list[str],
        year: int = 2021,
        dataset: str = "acs/acs5",
        batch_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch census data in optimized batches.

        Args:
            geoids: List of geographic identifiers
            variables: List of variable codes
            year: Census year
            dataset: Dataset identifier
            batch_size: Number of geoids per batch

        Returns:
            Combined results from all batches
        """
        all_results = []
        total_batches = (len(geoids) + batch_size - 1) // batch_size

        self._logger.info(
            f"Fetching census data in {total_batches} batches "
            f"({batch_size} geoids per batch)"
        )

        for i in range(0, len(geoids), batch_size):
            batch = geoids[i : i + batch_size]
            batch_num = i // batch_size + 1

            self._logger.debug(f"Processing batch {batch_num}/{total_batches}")

            try:
                # Parse geoids to extract state and county info
                states_counties = self._parse_geoids_by_county(batch)

                # Fetch data for each county in the batch
                for (state, county), county_geoids in states_counties.items():
                    geography = f"block group:*&in=state:{state} county:{county}"

                    result = self.get_census_data(
                        variables=variables,
                        geography=geography,
                        year=year,
                        dataset=dataset,
                    )

                    # Filter results to only include requested geoids
                    if isinstance(result, list) and len(result) > 1:
                        headers = result[0]
                        rows = result[1:]

                        # Find GEOID column index
                        geoid_idx = None
                        for idx, header in enumerate(headers):
                            if header.upper() == "GEO_ID":
                                geoid_idx = idx
                                break

                        if geoid_idx is not None:
                            # Filter rows
                            filtered_rows = [
                                row for row in rows
                                if row[geoid_idx] in county_geoids
                            ]

                            if filtered_rows:
                                all_results.append([headers, *filtered_rows])

            except Exception as e:
                self._logger.error(f"Failed to process batch {batch_num}: {e}")
                self._metrics.record_error(type(e).__name__, str(e))

                # Continue with next batch instead of failing completely
                continue

        # Combine results
        return self._combine_batch_results(all_results)

    def _parse_geoids_by_county(self, geoids: list[str]) -> dict[tuple[str, str], set[str]]:
        """Parse geoids and group by state and county.

        Args:
            geoids: List of geographic identifiers

        Returns:
            Dictionary mapping (state, county) to set of geoids
        """
        counties = {}

        for geoid in geoids:
            # Census block group GEOID format: SSCCCTTTTTTB
            # SS = State, CCC = County, TTTTTT = Tract, B = Block Group
            min_geoid_length = STATE_FIPS_LENGTH + COUNTY_FIPS_LENGTH
            if len(geoid) >= min_geoid_length:
                state = geoid[:STATE_FIPS_LENGTH]
                county = geoid[STATE_FIPS_LENGTH:STATE_FIPS_LENGTH + COUNTY_FIPS_LENGTH]
                counties.setdefault((state, county), set()).add(geoid)

        return counties

    def _combine_batch_results(self, batch_results: list[list[Any]]) -> list[Any]:
        """Combine results from multiple batches.

        Args:
            batch_results: List of batch results

        Returns:
            Combined results with single header row
        """
        if not batch_results:
            return []

        # Use first batch's headers
        combined = batch_results[0]

        # Add data rows from all batches
        for batch in batch_results[1:]:
            if len(batch) > 1:
                # Skip header row, add data rows
                combined.extend(batch[1:])

        return combined

    def _make_request_with_retries(
        self, url: str, params: dict[str, Any], max_retries: int | None = None
    ) -> dict[str, Any]:
        """Enhanced request method with metrics and rate limit tracking."""
        if max_retries is None:
            max_retries = self._config.get_setting("max_retries", 3)

        backoff_factor = self._config.get_setting("retry_backoff_factor", 0.5)
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Log API requests if enabled
                if self._config.get_setting("log_api_requests", False):
                    self._logger.info(f"API Request (attempt {attempt + 1}): {url}")

                start_time = time.time()
                response = self._session.get(url, params=params, timeout=self._timeout)
                response_time = time.time() - start_time

                # Handle rate limiting
                if response.status_code == HTTP_TOO_MANY_REQUESTS:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self._logger.warning(f"Rate limited, waiting {retry_after} seconds")

                    # Record metrics
                    self._metrics.record_rate_limit(retry_after)

                    time.sleep(retry_after)
                    raise CensusAPIRateLimitError("Rate limit exceeded")

                # Raise for other HTTP errors
                response.raise_for_status()

                # Parse JSON response
                try:
                    data = response.json()
                except ValueError as e:
                    raise CensusAPIError(f"Invalid JSON response: {e}") from e

                # Check for API-level errors
                if isinstance(data, dict) and "error" in data:
                    error_msg = data.get("error", "Unknown API error")
                    raise CensusAPIError(f"Census API error: {error_msg}")

                # Record success metrics
                self._metrics.record_success(response_time)

                # Record circuit breaker success
                if self._circuit_breaker.state.value == "half_open":
                    self._metrics.record_circuit_breaker_success()

                return data

            except (requests.RequestException, CensusAPIError) as e:
                last_exception = e

                if attempt < max_retries:
                    # Calculate backoff delay
                    delay = backoff_factor * (2**attempt)
                    self._logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    time.sleep(delay)
                else:
                    self._logger.error(f"All retries exhausted. Last error: {e}")

        # If we get here, all retries failed
        raise CensusAPIError(f"Request failed after {max_retries + 1} attempts: {last_exception}")

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get comprehensive metrics summary."""
        metrics = self._metrics.get_metrics()
        return {
            **metrics.to_dict(),
            "circuit_breaker": self._circuit_breaker.get_status(),
            "deduplicator": self._deduplicator.get_status(),
            "uptime": self._metrics.get_uptime(),
            "recent_metrics": self._metrics.get_recent_metrics(5),
        }

    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker."""
        self._circuit_breaker.reset()
        self._logger.info("Circuit breaker manually reset")

    def health_check(self) -> dict[str, Any]:
        """Enhanced health check with detailed status."""
        start_time = time.time()

        try:
            # Try simple API call
            api_healthy = super().health_check()
            response_time = time.time() - start_time

            return {
                "healthy": api_healthy,
                "response_time": f"{response_time:.3f}s",
                "circuit_breaker": self._circuit_breaker.get_status(),
                "metrics": self._metrics.get_recent_metrics(1),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "circuit_breaker": self._circuit_breaker.get_status(),
            }
