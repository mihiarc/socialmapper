#!/usr/bin/env python3
"""
Address Geocoding Engine
========================

Core geocoding engine orchestrating multiple providers with intelligent
fallback, caching, and quality validation following modern SWE practices.

Author: SocialMapper Team
Date: June 2025
"""

import time
from typing import Any, Dict, List

from ..progress import get_progress_bar
from . import AddressInput, AddressProvider, AddressQuality, GeocodingConfig, GeocodingResult
from .cache import AddressCache
from .providers import CensusProvider, NominatimProvider

from ..ui.console import get_logger
logger = get_logger(__name__)


class AddressGeocodingEngine:
    """
    High-level geocoding engine orchestrating multiple providers with
    intelligent fallback, caching, and quality validation.
    """

    def __init__(self, config: GeocodingConfig = None):
        self.config = config or GeocodingConfig()
        self.cache = AddressCache(self.config)
        self.providers = self._initialize_providers()
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "successful_geocodes": 0,
            "failed_geocodes": 0,
            "provider_usage": {provider.value: 0 for provider in AddressProvider},
        }

    def _initialize_providers(self) -> Dict[AddressProvider, Any]:
        """Initialize available geocoding providers."""
        providers = {}

        # Always available providers
        providers[AddressProvider.NOMINATIM] = NominatimProvider(self.config)
        providers[AddressProvider.CENSUS] = CensusProvider(self.config)

        # TODO: Add commercial providers based on API keys
        # if self.config.google_api_key:
        #     providers[AddressProvider.GOOGLE] = GoogleProvider(self.config)

        return providers

    def geocode_address(self, address: AddressInput) -> GeocodingResult:
        """
        Geocode a single address with intelligent provider selection and fallback.

        Args:
            address: Address string or AddressInput object

        Returns:
            GeocodingResult with geocoding outcome
        """
        # Convert string to AddressInput if needed
        if isinstance(address, str):
            address = AddressInput(address=address)

        self.stats["total_requests"] += 1

        # Check cache first
        cached_result = self.cache.get(address)
        if cached_result:
            self.stats["cache_hits"] += 1
            logger.debug(f"Cache hit for address: {address.address}")
            return cached_result

        # Determine provider order
        provider_order = self._get_provider_order(address)

        # Try providers in order
        last_error = None
        for provider_type in provider_order:
            if provider_type not in self.providers:
                continue

            provider = self.providers[provider_type]

            try:
                logger.debug(f"Trying provider {provider_type.value} for: {address.address}")
                result = provider.geocode_address(address)

                # Check quality threshold
                if result.success and self._meets_quality_threshold(result.quality, address):

                    # Update stats
                    self.stats["successful_geocodes"] += 1
                    self.stats["provider_usage"][provider_type.value] += 1

                    # Cache successful result
                    self.cache.put(result)

                    logger.info(
                        f"Successfully geocoded '{address.address}' using {provider_type.value}"
                    )
                    return result

                elif result.success:
                    logger.warning(
                        f"Result quality {result.quality.value} below threshold for {address.address}"
                    )

                last_error = result.error_message

            except Exception as e:
                logger.warning(f"Provider {provider_type.value} failed for {address.address}: {e}")
                last_error = str(e)

        # All providers failed
        self.stats["failed_geocodes"] += 1

        failed_result = GeocodingResult(
            input_address=address,
            success=False,
            quality=AddressQuality.FAILED,
            error_message=last_error or "All geocoding providers failed",
        )

        # Cache failed result (with shorter TTL)
        self.cache.put(failed_result)

        return failed_result

    def geocode_addresses_batch(
        self, addresses: List[AddressInput], progress: bool = True
    ) -> List[GeocodingResult]:
        """
        Geocode multiple addresses in batch with progress tracking.

        Args:
            addresses: List of address strings or AddressInput objects
            progress: Whether to show progress bar

        Returns:
            List of GeocodingResult objects
        """
        results = []

        # Convert strings to AddressInput
        address_inputs = []
        for addr in addresses:
            if isinstance(addr, str):
                address_inputs.append(AddressInput(address=addr))
            else:
                address_inputs.append(addr)

        # Process in batches with progress tracking
        if progress:
            progress_bar = get_progress_bar(total=len(address_inputs), desc="Geocoding addresses")

        for i in range(0, len(address_inputs), self.config.batch_size):
            batch = address_inputs[i : i + self.config.batch_size]

            for address in batch:
                result = self.geocode_address(address)
                results.append(result)

                if progress:
                    progress_bar.update(1)

                # Rate limiting between requests
                if self.config.batch_delay_seconds > 0:
                    time.sleep(self.config.batch_delay_seconds)

        if progress:
            progress_bar.close()

        # Save cache after batch processing
        self.cache.save_cache()

        return results

    def _get_provider_order(self, address: AddressInput) -> List[AddressProvider]:
        """Determine optimal provider order for an address."""
        providers = [self.config.primary_provider]

        # Add user preference if specified
        if (
            address.provider_preference
            and address.provider_preference != self.config.primary_provider
        ):
            providers.insert(0, address.provider_preference)

        # Add fallback providers
        for fallback in self.config.fallback_providers:
            if fallback not in providers:
                providers.append(fallback)

        return providers

    def _meets_quality_threshold(self, quality: AddressQuality, address: AddressInput) -> bool:
        """Check if result quality meets threshold."""
        threshold = address.quality_threshold or self.config.min_quality_threshold

        quality_order = [
            AddressQuality.EXACT,
            AddressQuality.INTERPOLATED,
            AddressQuality.CENTROID,
            AddressQuality.APPROXIMATE,
            AddressQuality.FAILED,
        ]

        return quality_order.index(quality) <= quality_order.index(threshold)

    def get_statistics(self) -> Dict[str, Any]:
        """Get geocoding engine statistics."""
        stats = self.stats.copy()

        if stats["total_requests"] > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_requests"]
            stats["success_rate"] = stats["successful_geocodes"] / stats["total_requests"]
        else:
            stats["cache_hit_rate"] = 0.0
            stats["success_rate"] = 0.0

        return stats

    def convert_to_poi_format(self, results: List[GeocodingResult]) -> Dict[str, Any]:
        """
        Convert geocoding results to standard SocialMapper POI format.

        Args:
            results: List of GeocodingResult objects

        Returns:
            Dictionary in POI format compatible with existing SocialMapper workflow
        """
        pois = []
        metadata = {
            "total_addresses": len(results),
            "successful_geocodes": 0,
            "failed_geocodes": 0,
            "geocoding_stats": self.get_statistics(),
        }

        for result in results:
            if result.success:
                poi = result.to_poi_format()
                if poi:
                    pois.append(poi)
                    metadata["successful_geocodes"] += 1
            else:
                metadata["failed_geocodes"] += 1

        return {"poi_count": len(pois), "pois": pois, "metadata": metadata}
