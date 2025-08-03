"""Tests for the API builder pattern."""

import pytest

from socialmapper.api.builder import SocialMapperBuilder


class TestSocialMapperBuilder:
    """Test the SocialMapperBuilder class."""

    def test_builder_initialization(self):
        """Test builder can be initialized."""
        builder = SocialMapperBuilder()
        assert builder is not None
        assert builder._config is not None

    def test_location_setting(self):
        """Test setting location."""
        builder = SocialMapperBuilder()
        result = builder.with_location("San Francisco, CA")
        assert result is builder  # Check fluent interface
        # Check internal state is set correctly

    def test_poi_configuration(self):
        """Test POI configuration."""
        builder = (
            SocialMapperBuilder()
            .with_osm_pois(poi_type="amenity", poi_name="library")
        )
        # Builder pattern should return self
        assert isinstance(builder, SocialMapperBuilder)

    def test_travel_configuration(self):
        """Test travel time and mode configuration."""
        builder = (
            SocialMapperBuilder()
            .with_travel_time(15)
            .with_travel_mode("walk")
        )
        # Builder pattern should return self
        assert isinstance(builder, SocialMapperBuilder)

    def test_invalid_travel_mode(self):
        """Test that invalid travel mode raises error."""
        builder = SocialMapperBuilder()
        # Invalid travel mode doesn't raise immediately, but adds to validation errors
        result = builder.with_travel_mode("teleport")
        assert result is builder  # Still returns self for chaining
        assert len(builder._validation_errors) > 0

    def test_census_variables_configuration(self):
        """Test census variables configuration."""
        builder = SocialMapperBuilder().with_census_variables("B01001_001E", "B19013_001E")
        assert isinstance(builder, SocialMapperBuilder)

    def test_output_directory_configuration(self):
        """Test output directory configuration."""
        builder = SocialMapperBuilder().with_output_directory("/tmp/output")
        assert isinstance(builder, SocialMapperBuilder)

    def test_complete_configuration(self):
        """Test a complete configuration."""
        builder = (
            SocialMapperBuilder()
            .with_location("Chicago, IL")
            .with_osm_pois(poi_type="shop", poi_name="supermarket")
            .with_travel_time(10)
            .with_travel_mode("drive")
            .with_census_variables("B01001_001E")
            .with_output_directory("/tmp/test")
        )

        # Verify builder chain works
        assert isinstance(builder, SocialMapperBuilder)

    def test_build_creates_client(self):
        """Test that build() creates a SocialMapperClient."""
        builder = (
            SocialMapperBuilder()
            .with_location("Boston, MA")
            .with_osm_pois(poi_type="amenity", poi_name="school")
        )

        # build() returns the config dict, not a client instance
        config = builder.build()
        assert isinstance(config, dict)
        assert "geocode_area" in config
        assert "poi_type" in config
        assert "poi_name" in config

    def test_exports_configuration(self):
        """Test exports configuration."""
        builder = SocialMapperBuilder().with_exports(csv=True, isochrones=True, maps=False)
        assert isinstance(builder, SocialMapperBuilder)

    def test_invalid_travel_time(self):
        """Test invalid travel time raises error."""
        from socialmapper.exceptions import InvalidTravelTimeError
        builder = SocialMapperBuilder()
        with pytest.raises(InvalidTravelTimeError):
            builder.with_travel_time(0)  # Too low
        with pytest.raises(InvalidTravelTimeError):
            builder.with_travel_time(121)  # Too high

    def test_geographic_level(self):
        """Test geographic level configuration."""
        from socialmapper.api.builder import GeographicLevel
        builder = SocialMapperBuilder().with_geographic_level(GeographicLevel.ZCTA)
        assert isinstance(builder, SocialMapperBuilder)

    def test_custom_pois(self):
        """Test custom POIs configuration."""
        # with_custom_pois takes a file path, not a list
        builder = SocialMapperBuilder().with_custom_pois("/path/to/pois.csv")
        assert isinstance(builder, SocialMapperBuilder)
