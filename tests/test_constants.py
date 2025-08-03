"""Tests for constants module."""

from socialmapper.constants import (
    # Census related
    BLOCK_GROUP_LENGTH,
    COUNTY_FIPS_LENGTH,
    # API related
    DEFAULT_API_TIMEOUT,
    DEFAULT_TRAVEL_TIME_MINUTES,
    FULL_BLOCK_GROUP_GEOID_LENGTH,
    FULL_TRACT_GEOID_LENGTH,
    LARGE_DATASET_MB,
    # Performance thresholds
    LARGE_DATASET_RECORDS,
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_RETRIES,
    MAX_TRAVEL_TIME,
    MEDIUM_DATASET_MB,
    MEDIUM_DATASET_RECORDS,
    # Geographic
    MIN_LATITUDE,
    MIN_LONGITUDE,
    # Travel related
    MIN_TRAVEL_TIME,
    # File size limits
    SMALL_DATASET_MB,
    SMALL_DATASET_RECORDS,
    STATE_FIPS_LENGTH,
    TRACT_LENGTH,
    WEB_MERCATOR_EPSG,
    WGS84_EPSG,
)


class TestCensusConstants:
    """Test census-related constants."""

    def test_fips_lengths(self):
        """Test FIPS code length constants."""
        assert STATE_FIPS_LENGTH == 2
        assert COUNTY_FIPS_LENGTH == 3
        assert TRACT_LENGTH == 6
        assert BLOCK_GROUP_LENGTH == 1

        # Total GEOID lengths
        assert FULL_TRACT_GEOID_LENGTH == 11  # state + county + tract
        assert FULL_BLOCK_GROUP_GEOID_LENGTH == 12  # state + county + tract + block group

    def test_geoid_consistency(self):
        """Test GEOID length consistency."""
        # Tract GEOID should be state + county + tract
        assert FULL_TRACT_GEOID_LENGTH == STATE_FIPS_LENGTH + COUNTY_FIPS_LENGTH + TRACT_LENGTH

        # Block group GEOID should be tract + block group
        assert FULL_BLOCK_GROUP_GEOID_LENGTH == FULL_TRACT_GEOID_LENGTH + BLOCK_GROUP_LENGTH


class TestTravelConstants:
    """Test travel-related constants."""

    def test_travel_time_limits(self):
        """Test travel time boundaries."""
        assert MIN_TRAVEL_TIME == 1
        assert MAX_TRAVEL_TIME == 120
        assert DEFAULT_TRAVEL_TIME_MINUTES == 30

        # Default should be within bounds
        assert MIN_TRAVEL_TIME <= DEFAULT_TRAVEL_TIME_MINUTES <= MAX_TRAVEL_TIME

    def test_travel_time_validity(self):
        """Test travel time values are reasonable."""
        # Max travel time should be 2 hours (120 minutes)
        assert MAX_TRAVEL_TIME <= 120

        # Min travel time should be positive
        assert MIN_TRAVEL_TIME > 0


class TestDatasetSizeConstants:
    """Test dataset size constants."""

    def test_size_thresholds(self):
        """Test dataset size thresholds."""
        # Sizes should be in ascending order
        assert SMALL_DATASET_MB < MEDIUM_DATASET_MB < LARGE_DATASET_MB

        # Check reasonable values
        assert SMALL_DATASET_MB >= 1  # At least 1 MB
        assert MEDIUM_DATASET_MB >= 10  # At least 10 MB
        assert LARGE_DATASET_MB >= 100  # At least 100 MB

    def test_record_thresholds(self):
        """Test dataset record count thresholds."""
        # Record counts should be in ascending order
        assert SMALL_DATASET_RECORDS < MEDIUM_DATASET_RECORDS < LARGE_DATASET_RECORDS

        # Check reasonable values
        assert SMALL_DATASET_RECORDS >= 1000
        assert MEDIUM_DATASET_RECORDS >= 10000
        assert LARGE_DATASET_RECORDS >= 100000


class TestGeographicConstants:
    """Test geographic constants."""

    def test_latitude_bounds(self):
        """Test latitude boundaries."""
        assert MIN_LATITUDE == -90.0
        assert MAX_LATITUDE == 90.0

        # Valid range
        assert MIN_LATITUDE < MAX_LATITUDE

    def test_longitude_bounds(self):
        """Test longitude boundaries."""
        assert MIN_LONGITUDE == -180.0
        assert MAX_LONGITUDE == 180.0

        # Valid range
        assert MIN_LONGITUDE < MAX_LONGITUDE

    def test_coordinate_ranges(self):
        """Test coordinate ranges are valid."""
        # Latitude range should be 180 degrees
        assert MAX_LATITUDE - MIN_LATITUDE == 180.0

        # Longitude range should be 360 degrees
        assert MAX_LONGITUDE - MIN_LONGITUDE == 360.0

    def test_epsg_codes(self):
        """Test EPSG coordinate system codes."""
        assert WGS84_EPSG == 4326  # Standard lat/lon
        assert WEB_MERCATOR_EPSG == 3857  # Web mapping standard

        # Should be different systems
        assert WGS84_EPSG != WEB_MERCATOR_EPSG


class TestAPIConstants:
    """Test API-related constants."""

    def test_timeout_values(self):
        """Test API timeout values."""
        assert DEFAULT_API_TIMEOUT > 0
        assert DEFAULT_API_TIMEOUT <= 300  # Max 5 minutes

    def test_retry_values(self):
        """Test retry configuration."""
        assert MAX_RETRIES >= 1
        assert MAX_RETRIES <= 10  # Reasonable retry limit
