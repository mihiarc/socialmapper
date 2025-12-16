#!/usr/bin/env python3
"""Geocoding providers for address lookup.

This module contains implementations of various geocoding providers.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from ..constants import (
    CENSUS_GEOCODER_LOCATIONS_URL,
    NOMINATIM_API_URL,
    USER_AGENT,
)
from ..neighbors import get_neighbor_manager
from ..performance.connection_pool import get_http_session
from .models import (
    AddressInput,
    AddressProvider,
    AddressQuality,
    GeocodingConfig,
    GeocodingResult,
)

logger = logging.getLogger(__name__)


class GeocodingProvider(ABC):
    """
    Abstract base class for geocoding providers.

    Provides common functionality for HTTP session management,
    rate limiting, and retry logic. Uses centralized connection
    pool for consistent HTTP handling across the application.

    Parameters
    ----------
    config : GeocodingConfig
        Configuration for geocoding behavior.

    Attributes
    ----------
    config : GeocodingConfig
        Active configuration.
    last_request_time : float
        Timestamp of last request for rate limiting.
    """

    def __init__(self, config: GeocodingConfig):
        self.config = config
        self.last_request_time = 0.0

    @property
    def session(self):
        """Get HTTP session from centralized connection pool."""
        return get_http_session()

    def _enforce_rate_limit(self):
        """
        Enforce rate limiting between requests.

        Sleeps if necessary to maintain configured rate
        limit.
        """
        rate_limit = self.config.rate_limit_requests_per_second
        min_interval = 1.0 / rate_limit
        elapsed = time.time() - self.last_request_time

        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @abstractmethod
    def geocode_address(self, address: AddressInput) -> GeocodingResult:
        """
        Geocode a single address.

        Parameters
        ----------
        address : AddressInput
            Address to geocode.

        Returns
        -------
        GeocodingResult
            Result with coordinates and quality
            information.
        """

    @abstractmethod
    def get_provider_name(self) -> AddressProvider:
        """
        Get the provider identifier.

        Returns
        -------
        AddressProvider
            Enum identifying this provider.
        """


class NominatimProvider(GeocodingProvider):
    """
    OpenStreetMap Nominatim geocoding provider.

    Free geocoding service with rate limiting. Best for
    international addresses and general geocoding needs.

    Notes
    -----
    Requires respectful rate limiting (max 1
    request/second). See the following URL for usage
    policy:
    https://operations.osmfoundation.org/policies/nominatim/
    """

    BASE_URL = NOMINATIM_API_URL

    def get_provider_name(self) -> AddressProvider:
        """
        Return the provider name for this geocoder.

        Returns
        -------
        AddressProvider
            NOMINATIM enum value.
        """
        return AddressProvider.NOMINATIM

    def geocode_address(self, address: AddressInput) -> GeocodingResult:
        """
        Geocode address using Nominatim API.

        Parameters
        ----------
        address : AddressInput
            Address to geocode.

        Returns
        -------
        GeocodingResult
            Geocoding result with coordinates and quality
            assessment.
        """
        start_time = time.time()

        try:
            self._enforce_rate_limit()

            params = {
                "q": address.get_formatted_address(),
                "format": "json",
                "addressdetails": 1,
                "limit": 1,
                "countrycodes": address.country.lower(),
                "extratags": 1,
            }

            headers = {"User-Agent": USER_AGENT}

            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()

            if not data:
                return GeocodingResult(
                    input_address=address,
                    success=False,
                    quality=AddressQuality.FAILED,
                    error_message="No results found",
                    processing_time_ms=(
                        (time.time() - start_time) * 1000
                    ),
                )

            result = data[0]
            lat = float(result["lat"])
            lon = float(result["lon"])

            # Determine quality based on OSM class and type
            quality = self._determine_quality_from_osm(result)

            # Extract address components
            address_parts = result.get("address", {})

            geocoding_result = GeocodingResult(
                input_address=address,
                success=True,
                latitude=lat,
                longitude=lon,
                quality=quality,
                provider_used=AddressProvider.NOMINATIM,
                confidence_score=self._calculate_confidence(
                    result
                ),
                formatted_address=result.get("display_name"),
                street_number=address_parts.get("house_number"),
                street_name=address_parts.get("road"),
                city=(
                    address_parts.get("city")
                    or address_parts.get("town")
                    or address_parts.get("village")
                ),
                state=address_parts.get("state"),
                postal_code=address_parts.get("postcode"),
                country=address_parts.get(
                    "country_code", ""
                ).upper(),
                processing_time_ms=(
                    (time.time() - start_time) * 1000
                ),
            )

            # Add geographic context using neighbor system
            self._add_geographic_context(geocoding_result)

            return geocoding_result

        except (ValueError, KeyError, TypeError) as e:
            error_msg = f"Nominatim geocoding data error for {address.address}: {e}"
            logger.warning(error_msg)
            return GeocodingResult(
                input_address=address,
                success=False,
                quality=AddressQuality.FAILED,
                error_message=str(e),
                processing_time_ms=((time.time() - start_time) * 1000),
            )
        except (OSError, ConnectionError, TimeoutError) as e:
            error_msg = f"Nominatim geocoding network error for {address.address}: {e}"
            logger.warning(error_msg)
            return GeocodingResult(
                input_address=address,
                success=False,
                quality=AddressQuality.FAILED,
                error_message=str(e),
                processing_time_ms=((time.time() - start_time) * 1000),
            )

    def _determine_quality_from_osm(
        self, result: dict[str, Any]
    ) -> AddressQuality:
        """Determine address quality from OSM result."""
        osm_class = result.get("class", "")
        osm_type = result.get("type", "")

        # Address-level matches
        if osm_class == "place" and osm_type in ["house", "address"]:
            return AddressQuality.EXACT

        # Street-level matches
        if osm_class == "highway":
            return AddressQuality.INTERPOLATED

        # Administrative area matches
        admin_types = ["city", "town", "village"]
        if osm_class == "place" and osm_type in admin_types:
            return AddressQuality.CENTROID

        # Default to approximate
        return AddressQuality.APPROXIMATE

    def _calculate_confidence(
        self, result: dict[str, Any]
    ) -> float:
        """Calculate confidence score from OSM result."""
        importance = float(result.get("importance", 0.5))
        # Scale to 0-1 range
        return min(importance * 2, 1.0)

    def _add_geographic_context(
        self, result: GeocodingResult
    ):
        """Add geographic context using neighbor system."""
        if (
            not result.success
            or not result.latitude
            or not result.longitude
        ):
            return

        try:
            neighbor_manager = get_neighbor_manager()
            geo_info = (
                neighbor_manager.get_geography_from_point(
                    result.latitude, result.longitude
                )
            )

            if geo_info:
                result.state_fips = geo_info.get(
                    "state_fips"
                )
                result.county_fips = geo_info.get(
                    "county_fips"
                )
                result.tract_geoid = geo_info.get(
                    "tract_geoid"
                )
                result.block_group_geoid = geo_info.get(
                    "block_group_geoid"
                )

        except (ValueError, KeyError, TypeError, OSError, ConnectionError) as e:
            logger.warning(
                f"Failed to get geographic context: {e}"
            )


class CensusProvider(GeocodingProvider):
    """
    US Census Bureau geocoding provider.

    Free, high-quality geocoding for US addresses. Best for
    US-only applications requiring accurate census
    block-level matching.

    Notes
    -----
    US addresses only. Automatically enriches results with
    census geography (FIPS codes, block groups).
    """

    BASE_URL = CENSUS_GEOCODER_LOCATIONS_URL

    def get_provider_name(self) -> AddressProvider:
        """
        Return the provider name for this geocoder.

        Returns
        -------
        AddressProvider
            CENSUS enum value.
        """
        return AddressProvider.CENSUS

    def geocode_address(self, address: AddressInput) -> GeocodingResult:
        """
        Geocode address using Census Bureau API.

        Parameters
        ----------
        address : AddressInput
            Address to geocode (must be US address).

        Returns
        -------
        GeocodingResult
            Geocoding result with census geography
            enrichment.
        """
        start_time = time.time()

        try:
            self._enforce_rate_limit()

            params = {
                "address": address.get_formatted_address(),
                "benchmark": "Public_AR_Current",
                "format": "json",
            }

            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()

            # Check for successful geocoding
            if (
                "result" not in data
                or "addressMatches" not in data["result"]
                or not data["result"]["addressMatches"]
            ):
                return GeocodingResult(
                    input_address=address,
                    success=False,
                    quality=AddressQuality.FAILED,
                    error_message="No address matches found",
                    processing_time_ms=(
                        (time.time() - start_time) * 1000
                    ),
                )

            match = data["result"]["addressMatches"][0]
            coords = match["coordinates"]

            lat = float(coords["y"])
            lon = float(coords["x"])

            # Census always provides high-quality results
            quality = AddressQuality.EXACT

            # Extract address components
            address_parts = match.get("addressComponents", {})

            geocoding_result = GeocodingResult(
                input_address=address,
                success=True,
                latitude=lat,
                longitude=lon,
                quality=quality,
                provider_used=AddressProvider.CENSUS,
                # Census results are typically high quality
                confidence_score=0.95,
                formatted_address=match.get("matchedAddress"),
                street_number=address_parts.get("fromAddress"),
                street_name=address_parts.get("streetName"),
                city=address_parts.get("city"),
                state=address_parts.get("state"),
                postal_code=address_parts.get("zip"),
                country="US",
                processing_time_ms=(
                    (time.time() - start_time) * 1000
                ),
            )

            # Add geographic context using neighbor system
            self._add_geographic_context(geocoding_result)

            return geocoding_result

        except (ValueError, KeyError, TypeError) as e:
            error_msg = f"Census geocoding data error for {address.address}: {e}"
            logger.warning(error_msg)
            return GeocodingResult(
                input_address=address,
                success=False,
                quality=AddressQuality.FAILED,
                error_message=str(e),
                processing_time_ms=((time.time() - start_time) * 1000),
            )
        except (OSError, ConnectionError, TimeoutError) as e:
            error_msg = f"Census geocoding network error for {address.address}: {e}"
            logger.warning(error_msg)
            return GeocodingResult(
                input_address=address,
                success=False,
                quality=AddressQuality.FAILED,
                error_message=str(e),
                processing_time_ms=((time.time() - start_time) * 1000),
            )

    def _add_geographic_context(
        self, result: GeocodingResult
    ):
        """Add geographic context using neighbor system."""
        if (
            not result.success
            or not result.latitude
            or not result.longitude
        ):
            return

        try:
            neighbor_manager = get_neighbor_manager()
            geo_info = (
                neighbor_manager.get_geography_from_point(
                    result.latitude, result.longitude
                )
            )

            if geo_info:
                result.state_fips = geo_info.get(
                    "state_fips"
                )
                result.county_fips = geo_info.get(
                    "county_fips"
                )
                result.tract_geoid = geo_info.get(
                    "tract_geoid"
                )
                result.block_group_geoid = geo_info.get(
                    "block_group_geoid"
                )

        except (ValueError, KeyError, TypeError, OSError, ConnectionError) as e:
            logger.warning(
                f"Failed to get geographic context: {e}"
            )


# Factory function for creating providers
def create_provider(
    provider_type: AddressProvider, config: GeocodingConfig
) -> GeocodingProvider:
    """Create a geocoding provider instance."""
    providers = {
        AddressProvider.NOMINATIM: NominatimProvider,
        AddressProvider.CENSUS: CensusProvider,
    }

    provider_class = providers.get(provider_type)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider_type}")

    return provider_class(config)
