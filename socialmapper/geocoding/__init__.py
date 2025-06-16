#!/usr/bin/env python3
"""SocialMapper Address Geocoding System
====================================

Modern, production-ready address lookup system following SWE and ETL best practices.

Key Features:
- Multiple geocoding providers (Nominatim, Google, Census, etc.)
- Intelligent provider fallback and failover
- Comprehensive caching and rate limiting
- Data quality validation and normalization
- Batch processing capabilities
- Monitoring and observability
- Type-safe interfaces with Pydantic validation

Author: SocialMapper Team
Date: June 2025
"""

from typing import Any, Union

from .engine import AddressGeocodingEngine
from .models import (
    AddressInput,
    AddressProvider,
    AddressQuality,
    GeocodingConfig,
    GeocodingResult,
)


# High-level convenience functions
def geocode_address(address: str | AddressInput, config: GeocodingConfig = None) -> GeocodingResult:
    """Convenience function to geocode a single address.

    Args:
        address: Address string or AddressInput object
        config: Optional geocoding configuration

    Returns:
        GeocodingResult
    """
    engine = AddressGeocodingEngine(config)
    return engine.geocode_address(address)


def geocode_addresses(
    addresses: list[str | AddressInput], config: GeocodingConfig = None, progress: bool = True
) -> list[GeocodingResult]:
    """Convenience function to geocode multiple addresses.

    Args:
        addresses: List of address strings or AddressInput objects
        config: Optional geocoding configuration
        progress: Whether to show progress bar

    Returns:
        List of GeocodingResult objects
    """
    engine = AddressGeocodingEngine(config)
    return engine.geocode_addresses_batch(addresses, progress)


def addresses_to_poi_format(
    addresses: list[str | AddressInput], config: GeocodingConfig = None
) -> dict[str, Any]:
    """Convenience function to geocode addresses and convert to POI format.

    Args:
        addresses: List of address strings or AddressInput objects
        config: Optional geocoding configuration

    Returns:
        Dictionary in POI format compatible with SocialMapper
    """
    engine = AddressGeocodingEngine(config)
    results = engine.geocode_addresses_batch(addresses)

    # Convert results to POI format
    pois = []
    metadata = {
        "total_addresses": len(results),
        "successful_geocodes": 0,
        "failed_geocodes": 0,
        "geocoding_stats": engine.get_statistics(),
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


# Export public API
__all__ = [
    # Models
    "AddressProvider",
    "AddressQuality",
    "GeocodingConfig",
    "AddressInput",
    "GeocodingResult",
    # Engine
    "AddressGeocodingEngine",
    # Convenience functions
    "geocode_address",
    "geocode_addresses",
    "addresses_to_poi_format",
]
