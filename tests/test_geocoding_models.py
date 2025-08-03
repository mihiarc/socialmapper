"""Tests for geocoding models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from socialmapper.geocoding.models import (
    AddressInput,
    AddressProvider,
    AddressQuality,
    GeocodingConfig,
    GeocodingResult,
)


class TestAddressProvider:
    """Test AddressProvider enum."""

    def test_provider_values(self):
        """Test provider enum values."""
        assert AddressProvider.NOMINATIM.value == "nominatim"
        assert AddressProvider.GOOGLE.value == "google"
        assert AddressProvider.CENSUS.value == "census"
        assert AddressProvider.HERE.value == "here"
        assert AddressProvider.MAPBOX.value == "mapbox"

    def test_all_providers(self):
        """Test all providers are valid."""
        providers = list(AddressProvider)
        assert len(providers) == 5
        for provider in providers:
            assert isinstance(provider.value, str)


class TestAddressQuality:
    """Test AddressQuality enum."""

    def test_quality_levels(self):
        """Test quality level values."""
        assert AddressQuality.EXACT.value == "exact"
        assert AddressQuality.INTERPOLATED.value == "interpolated"
        assert AddressQuality.CENTROID.value == "centroid"
        assert AddressQuality.APPROXIMATE.value == "approximate"
        assert AddressQuality.FAILED.value == "failed"

    def test_quality_ordering(self):
        """Test quality levels have logical ordering."""
        # Higher quality should come first in the enum
        qualities = list(AddressQuality)
        assert qualities[0] == AddressQuality.EXACT
        assert qualities[-1] == AddressQuality.FAILED


class TestGeocodingConfig:
    """Test GeocodingConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GeocodingConfig()

        assert config.primary_provider == AddressProvider.NOMINATIM
        assert config.fallback_providers == [AddressProvider.CENSUS]
        assert config.timeout_seconds == 10
        assert config.max_retries == 3
        assert config.rate_limit_requests_per_second == 1.0
        assert config.min_quality_threshold == AddressQuality.CENTROID
        assert config.require_country_match is True
        assert config.default_country == "US"
        assert config.enable_cache is True
        assert config.cache_ttl_hours == 24 * 7
        assert config.batch_size == 100

    def test_custom_config(self):
        """Test custom configuration."""
        config = GeocodingConfig(
            primary_provider=AddressProvider.GOOGLE,
            fallback_providers=[AddressProvider.HERE, AddressProvider.MAPBOX],
            google_api_key="test_key",
            timeout_seconds=30,
            enable_cache=False
        )

        assert config.primary_provider == AddressProvider.GOOGLE
        assert len(config.fallback_providers) == 2
        assert config.google_api_key == "test_key"
        assert config.timeout_seconds == 30
        assert config.enable_cache is False


class TestAddressInput:
    """Test AddressInput model."""

    def test_valid_address_input(self):
        """Test creating valid address input."""
        addr = AddressInput(
            address="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94105"
        )

        assert addr.address == "123 Main St"
        assert addr.city == "San Francisco"
        assert addr.state == "CA"
        assert addr.postal_code == "94105"
        assert addr.country == "US"  # Default

    def test_minimal_address_input(self):
        """Test minimal address input."""
        addr = AddressInput(address="Golden Gate Bridge")

        assert addr.address == "Golden Gate Bridge"
        assert addr.city is None
        assert addr.state is None
        assert addr.postal_code is None
        assert addr.country == "US"

    def test_address_stripping(self):
        """Test that addresses are stripped of whitespace."""
        addr = AddressInput(address="  123 Main St  ")
        assert addr.address == "123 Main St"

    def test_empty_address_validation(self):
        """Test that empty addresses are rejected."""
        with pytest.raises(ValidationError):
            AddressInput(address="")

        with pytest.raises(ValidationError):
            AddressInput(address="   ")  # Only whitespace

    def test_address_with_metadata(self):
        """Test address with optional metadata."""
        addr = AddressInput(
            address="456 Oak Ave",
            id="addr_123",
            source="customer_db",
            provider_preference=AddressProvider.GOOGLE,
            quality_threshold=AddressQuality.EXACT
        )

        assert addr.id == "addr_123"
        assert addr.source == "customer_db"
        assert addr.provider_preference == AddressProvider.GOOGLE
        assert addr.quality_threshold == AddressQuality.EXACT

    def test_get_formatted_address(self):
        """Test formatted address generation."""
        # Full address
        addr = AddressInput(
            address="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94105",
            country="US"
        )

        formatted = addr.get_formatted_address()
        assert formatted == "123 Main St, San Francisco, CA, 94105, US"

        # Minimal address
        addr2 = AddressInput(address="Golden Gate Bridge")
        assert addr2.get_formatted_address() == "Golden Gate Bridge, US"

    def test_get_cache_key(self):
        """Test cache key generation."""
        addr1 = AddressInput(address="123 Main St, San Francisco")
        addr2 = AddressInput(address="123 Main St, San Francisco")
        addr3 = AddressInput(address="456 Oak Ave, Los Angeles")

        # Same address should generate same key
        assert addr1.get_cache_key() == addr2.get_cache_key()

        # Different address should generate different key
        assert addr1.get_cache_key() != addr3.get_cache_key()

        # Key should be a valid hex string (SHA256)
        key = addr1.get_cache_key()
        assert len(key) == 64  # SHA256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in key)


class TestGeocodingResult:
    """Test GeocodingResult model."""

    def test_successful_result(self):
        """Test successful geocoding result."""
        input_addr = AddressInput(address="123 Main St")

        result = GeocodingResult(
            input_address=input_addr,
            success=True,
            latitude=37.7749,
            longitude=-122.4194,
            quality=AddressQuality.EXACT,
            provider_used=AddressProvider.NOMINATIM,
            confidence_score=0.95,
            formatted_address="123 Main St, San Francisco, CA 94105",
            city="San Francisco",
            state="CA",
            postal_code="94105",
            state_fips="06",
            county_fips="075"
        )

        assert result.success is True
        assert result.latitude == 37.7749
        assert result.longitude == -122.4194
        assert result.provider_used == AddressProvider.NOMINATIM
        assert result.quality == AddressQuality.EXACT
        assert result.confidence_score == 0.95
        assert result.state_fips == "06"

    def test_failed_result(self):
        """Test failed geocoding result."""
        input_addr = AddressInput(address="Unknown Place")

        result = GeocodingResult(
            input_address=input_addr,
            success=False,
            quality=AddressQuality.FAILED,
            error_message="Address not found"
        )

        assert result.success is False
        assert result.error_message == "Address not found"
        assert result.latitude is None
        assert result.longitude is None
        assert result.quality == AddressQuality.FAILED

    def test_coordinate_validation(self):
        """Test coordinate boundary validation."""
        input_addr = AddressInput(address="Test")

        # Valid coordinates
        result = GeocodingResult(
            input_address=input_addr,
            success=True,
            latitude=45.0,
            longitude=-100.0,
            quality=AddressQuality.EXACT
        )
        assert result.latitude == 45.0
        assert result.longitude == -100.0

        # Invalid latitude (too high)
        with pytest.raises(ValidationError):
            GeocodingResult(
                input_address=input_addr,
                success=True,
                latitude=91.0,
                longitude=0,
                quality=AddressQuality.EXACT
            )

        # Invalid longitude (too low)
        with pytest.raises(ValidationError):
            GeocodingResult(
                input_address=input_addr,
                success=True,
                latitude=0,
                longitude=-181.0,
                quality=AddressQuality.EXACT
            )

    def test_to_poi_format(self):
        """Test conversion to POI format."""
        input_addr = AddressInput(
            address="Central Library",
            id="lib_001",
            source="library_db"
        )

        result = GeocodingResult(
            input_address=input_addr,
            success=True,
            latitude=40.7128,
            longitude=-74.0060,
            quality=AddressQuality.EXACT,
            provider_used=AddressProvider.CENSUS,
            confidence_score=0.9,
            formatted_address="Central Library, New York, NY 10001",
            city="New York",
            state="NY",
            postal_code="10001",
            state_fips="36",
            county_fips="061"
        )

        poi = result.to_poi_format()

        assert poi is not None
        assert poi["id"] == "lib_001"
        assert poi["name"] == "Central Library, New York, NY 10001"
        assert poi["lat"] == 40.7128
        assert poi["lon"] == -74.0060
        assert poi["type"] == "address"

        # Check tags
        tags = poi["tags"]
        assert tags["addr:city"] == "New York"
        assert tags["addr:state"] == "NY"
        assert tags["geocoding:provider"] == "census"
        assert tags["geocoding:quality"] == "exact"
        assert tags["geocoding:confidence"] == 0.9

        # Check metadata
        metadata = poi["metadata"]
        assert metadata["geocoded"] is True
        assert metadata["source"] == "library_db"
        assert metadata["state_fips"] == "36"
        assert metadata["county_fips"] == "061"

    def test_failed_to_poi_format(self):
        """Test failed result returns None for POI format."""
        input_addr = AddressInput(address="Unknown")

        result = GeocodingResult(
            input_address=input_addr,
            success=False,
            quality=AddressQuality.FAILED,
            error_message="Not found"
        )

        assert result.to_poi_format() is None

    def test_timestamp_default(self):
        """Test that timestamp is set by default."""
        input_addr = AddressInput(address="Test")

        result = GeocodingResult(
            input_address=input_addr,
            success=True,
            latitude=0,
            longitude=0,
            quality=AddressQuality.EXACT
        )

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)
        # Should be recent (within last minute)
        assert (datetime.now() - result.timestamp).total_seconds() < 60
