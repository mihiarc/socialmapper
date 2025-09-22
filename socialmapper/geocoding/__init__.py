#!/usr/bin/env python3
"""SocialMapper Address Geocoding System.

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
    """
    Geocode a single address to geographic coordinates.

    Converts street addresses to latitude/longitude coordinates using
    intelligent provider selection and fallback mechanisms.

    Parameters
    ----------
    address : str or AddressInput
        Street address string or structured AddressInput object.
    config : GeocodingConfig, optional
        Configuration for geocoding behavior (providers, timeouts, etc.).

    Returns
    -------
    GeocodingResult
        Result object containing coordinates, confidence, and metadata.

    Examples
    --------
    >>> result = geocode_address("1600 Pennsylvania Ave, Washington DC")
    >>> print(f"Lat: {result.latitude}, Lon: {result.longitude}")
    Lat: 38.8976, Lon: -77.0365
    """
    engine = AddressGeocodingEngine(config)
    return engine.geocode_address(address)


def geocode_addresses(
    addresses: list[str | AddressInput], config: GeocodingConfig = None, progress: bool = True
) -> list[GeocodingResult]:
    """
    Geocode multiple addresses in batch with progress tracking.

    Efficiently processes multiple addresses with rate limiting,
    caching, and automatic retries on failure.

    Parameters
    ----------
    addresses : list of str or AddressInput
        List of address strings or structured AddressInput objects.
    config : GeocodingConfig, optional
        Configuration for geocoding behavior.
    progress : bool, optional
        Whether to display progress bar, by default True.

    Returns
    -------
    list of GeocodingResult
        List of geocoding results in same order as input addresses.

    Examples
    --------
    >>> addresses = ["Seattle, WA", "Portland, OR", "San Francisco, CA"]
    >>> results = geocode_addresses(addresses)
    >>> successful = sum(1 for r in results if r.success)
    >>> print(f"Geocoded {successful}/{len(addresses)} addresses")
    """
    engine = AddressGeocodingEngine(config)
    return engine.geocode_addresses_batch(addresses, progress)


def addresses_to_poi_format(
    addresses: list[str | AddressInput], config: GeocodingConfig = None
) -> dict[str, Any]:
    """
    Geocode addresses and convert to SocialMapper POI format.

    Combines geocoding with format conversion to create POI data
    ready for analysis in the SocialMapper pipeline.

    Parameters
    ----------
    addresses : list of str or AddressInput
        List of addresses to geocode and convert.
    config : GeocodingConfig, optional
        Configuration for geocoding behavior.

    Returns
    -------
    dict
        POI format dictionary containing:
        - 'pois': List of POI dictionaries with lat/lon
        - 'poi_count': Number of successfully geocoded POIs
        - 'metadata': Statistics about geocoding process

    Examples
    --------
    >>> addresses = ["Space Needle, Seattle", "Pike Place Market, Seattle"]
    >>> poi_data = addresses_to_poi_format(addresses)
    >>> print(f"Created {poi_data['poi_count']} POIs")
    Created 2 POIs
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
    # Engine
    "AddressGeocodingEngine",
    "AddressInput",
    # Models
    "AddressProvider",
    "AddressQuality",
    "GeocodingConfig",
    "GeocodingResult",
    "addresses_to_poi_format",
    # Convenience functions
    "geocode_address",
    "geocode_addresses",
]
