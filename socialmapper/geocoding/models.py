#!/usr/bin/env python3
"""
Data models for the geocoding system.

This module contains all the data models and enumerations used by the geocoding system.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressProvider(Enum):
    """Enumeration of supported geocoding providers."""

    NOMINATIM = "nominatim"
    GOOGLE = "google"
    CENSUS = "census"
    HERE = "here"
    MAPBOX = "mapbox"


class AddressQuality(Enum):
    """Address quality levels based on geocoding precision."""

    EXACT = "exact"  # Rooftop/exact address match
    INTERPOLATED = "interpolated"  # Street interpolation
    CENTROID = "centroid"  # ZIP/city centroid
    APPROXIMATE = "approximate"  # Low precision match
    FAILED = "failed"  # Geocoding failed


@dataclass
class GeocodingConfig:
    """Configuration for geocoding operations."""

    # Provider settings
    primary_provider: AddressProvider = AddressProvider.NOMINATIM
    fallback_providers: List[AddressProvider] = field(
        default_factory=lambda: [AddressProvider.CENSUS]
    )

    # API credentials
    google_api_key: Optional[str] = None
    here_api_key: Optional[str] = None
    mapbox_api_key: Optional[str] = None

    # Performance settings
    timeout_seconds: int = 10
    max_retries: int = 3
    rate_limit_requests_per_second: float = 1.0

    # Quality settings
    min_quality_threshold: AddressQuality = AddressQuality.CENTROID
    require_country_match: bool = True
    default_country: str = "US"

    # Caching
    enable_cache: bool = True
    cache_ttl_hours: int = 24 * 7  # 1 week
    cache_max_size: int = 10000

    # Batch processing
    batch_size: int = 100
    batch_delay_seconds: float = 0.1


class AddressInput(BaseModel):
    """Validated input for address geocoding."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Core address components
    address: str = Field(..., min_length=1, description="Full address or search string")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State name or abbreviation")
    postal_code: Optional[str] = Field(None, description="ZIP/postal code")
    country: Optional[str] = Field("US", description="Country code")

    # Metadata
    id: Optional[str] = Field(None, description="Unique identifier for this address")
    source: Optional[str] = Field(None, description="Source system or dataset")

    # Processing options
    provider_preference: Optional[AddressProvider] = Field(
        None, description="Preferred geocoding provider"
    )
    quality_threshold: Optional[AddressQuality] = Field(
        None, description="Minimum quality requirement"
    )

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate and normalize address string."""
        if not v or v.strip() == "":
            raise ValueError("Address cannot be empty")
        return v.strip()

    def get_formatted_address(self) -> str:
        """Get a standardized formatted address for geocoding."""
        components = [self.address]
        if self.city:
            components.append(self.city)
        if self.state:
            components.append(self.state)
        if self.postal_code:
            components.append(self.postal_code)
        if self.country:
            components.append(self.country)
        return ", ".join(components)

    def get_cache_key(self) -> str:
        """Generate a cache key for this address."""
        address_str = self.get_formatted_address().lower()
        return hashlib.sha256(address_str.encode()).hexdigest()


class GeocodingResult(BaseModel):
    """Result of address geocoding operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Input reference
    input_address: AddressInput

    # Geocoding results
    success: bool
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    # Quality and metadata
    quality: AddressQuality
    provider_used: Optional[AddressProvider] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

    # Standardized address components
    formatted_address: Optional[str] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Geographic context
    state_fips: Optional[str] = None
    county_fips: Optional[str] = None
    tract_geoid: Optional[str] = None
    block_group_geoid: Optional[str] = None

    # Processing metadata
    processing_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None

    def to_poi_format(self) -> Optional[Dict[str, Any]]:
        """Convert to standard POI format for SocialMapper integration."""
        if not self.success or not self.latitude or not self.longitude:
            return None

        poi = {
            "id": self.input_address.id
            or f"addr_{hash(self.input_address.get_formatted_address())}",
            "name": self.formatted_address or self.input_address.address,
            "lat": self.latitude,
            "lon": self.longitude,
            "type": "address",
            "tags": {
                "addr:full": self.formatted_address,
                "addr:street": self.street_name,
                "addr:city": self.city,
                "addr:state": self.state,
                "addr:postcode": self.postal_code,
                "addr:country": self.country,
                "geocoding:provider": self.provider_used.value if self.provider_used else None,
                "geocoding:quality": self.quality.value,
                "geocoding:confidence": self.confidence_score,
            },
            "metadata": {
                "geocoded": True,
                "source": self.input_address.source,
                "state_fips": self.state_fips,
                "county_fips": self.county_fips,
                "tract_geoid": self.tract_geoid,
                "block_group_geoid": self.block_group_geoid,
            },
        }

        return poi