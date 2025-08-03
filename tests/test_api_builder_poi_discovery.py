"""Tests for POI discovery extensions to the API builder pattern."""

from socialmapper.api.builder import SocialMapperBuilder
from socialmapper.api.result_types import NearbyPOIDiscoveryConfig
from socialmapper.isochrone import TravelMode


class TestSocialMapperBuilderPOIDiscovery:
    """Test POI discovery extensions to SocialMapperBuilder."""

    def test_with_nearby_poi_discovery_address_location(self):
        """Test POI discovery configuration with address location."""
        builder = SocialMapperBuilder()
        result = builder.with_nearby_poi_discovery(
            location="San Francisco, CA",
            travel_time=15,
            travel_mode=TravelMode.DRIVE
        )

        assert result is builder  # Check fluent interface
        assert builder._config["poi_discovery_enabled"] is True
        assert builder._config["poi_discovery_location"] == "San Francisco, CA"
        assert builder._config["poi_discovery_travel_time"] == 15
        assert builder._config["poi_discovery_travel_mode"] == TravelMode.DRIVE

    def test_with_nearby_poi_discovery_coordinate_location(self):
        """Test POI discovery configuration with coordinate location."""
        builder = SocialMapperBuilder()
        coords = (37.7749, -122.4194)  # San Francisco coordinates
        result = builder.with_nearby_poi_discovery(
            location=coords,
            travel_time=30,
            travel_mode="walk"
        )

        assert result is builder
        assert builder._config["poi_discovery_enabled"] is True
        assert builder._config["poi_discovery_location"] == coords
        assert builder._config["poi_discovery_travel_time"] == 30
        assert builder._config["poi_discovery_travel_mode"] == TravelMode.WALK

    def test_with_nearby_poi_discovery_with_categories(self):
        """Test POI discovery with specific categories."""
        builder = SocialMapperBuilder()
        categories = ["food_and_drink", "healthcare", "education"]
        result = builder.with_nearby_poi_discovery(
            location="Boston, MA",
            travel_time=20,
            poi_categories=categories
        )

        assert result is builder
        assert builder._config["poi_categories"] == categories

    def test_with_nearby_poi_discovery_invalid_travel_time(self):
        """Test POI discovery with invalid travel time."""
        builder = SocialMapperBuilder()
        result = builder.with_nearby_poi_discovery(
            location="Chicago, IL",
            travel_time=150,  # Too high
            travel_mode=TravelMode.DRIVE
        )

        assert result is builder  # Still returns self for chaining
        assert len(builder._validation_errors) > 0
        assert "Travel time must be between" in builder._validation_errors[0]

    def test_with_nearby_poi_discovery_invalid_coordinates(self):
        """Test POI discovery with invalid coordinates."""
        builder = SocialMapperBuilder()
        result = builder.with_nearby_poi_discovery(
            location=(200.0, -300.0),  # Invalid coordinates
            travel_time=15
        )

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "Invalid coordinates" in builder._validation_errors[0]

    def test_with_nearby_poi_discovery_empty_address(self):
        """Test POI discovery with empty address."""
        builder = SocialMapperBuilder()
        result = builder.with_nearby_poi_discovery(
            location="   ",  # Empty/whitespace address
            travel_time=15
        )

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "Location address cannot be empty" in builder._validation_errors[0]

    def test_with_nearby_poi_discovery_invalid_location_type(self):
        """Test POI discovery with invalid location type."""
        builder = SocialMapperBuilder()
        result = builder.with_nearby_poi_discovery(
            location=123,  # Invalid type
            travel_time=15
        )

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "Location must be either an address string or (lat, lon) tuple" in builder._validation_errors[0]

    def test_with_nearby_poi_discovery_invalid_travel_mode(self):
        """Test POI discovery with invalid travel mode."""
        builder = SocialMapperBuilder()
        result = builder.with_nearby_poi_discovery(
            location="Seattle, WA",
            travel_time=15,
            travel_mode="teleport"  # Invalid mode
        )

        assert result is builder
        assert len(builder._validation_errors) > 0

    def test_with_nearby_poi_discovery_invalid_categories(self):
        """Test POI discovery with invalid POI categories."""
        builder = SocialMapperBuilder()
        result = builder.with_nearby_poi_discovery(
            location="Portland, OR",
            travel_time=15,
            poi_categories=["food_and_drink", "invalid_category", "healthcare"]
        )

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "Invalid POI categories" in builder._validation_errors[0]
        assert "invalid_category" in builder._validation_errors[0]

    def test_with_poi_categories(self):
        """Test setting POI categories."""
        builder = SocialMapperBuilder()
        result = builder.with_poi_categories("food_and_drink", "shopping", "healthcare")

        assert result is builder
        assert builder._config["poi_categories"] == ["food_and_drink", "shopping", "healthcare"]

    def test_with_poi_categories_empty(self):
        """Test setting empty POI categories."""
        builder = SocialMapperBuilder()
        result = builder.with_poi_categories()

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "At least one POI category must be specified" in builder._validation_errors[0]

    def test_with_poi_categories_invalid(self):
        """Test setting invalid POI categories."""
        builder = SocialMapperBuilder()
        result = builder.with_poi_categories("food_and_drink", "invalid_category")

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "Invalid POI categories" in builder._validation_errors[0]

    def test_exclude_poi_categories(self):
        """Test excluding POI categories."""
        builder = SocialMapperBuilder()
        result = builder.exclude_poi_categories("utilities", "services")

        assert result is builder
        assert builder._config["exclude_poi_categories"] == ["utilities", "services"]

    def test_exclude_poi_categories_empty(self):
        """Test excluding empty POI categories."""
        builder = SocialMapperBuilder()
        result = builder.exclude_poi_categories()

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "At least one POI category must be specified for exclusion" in builder._validation_errors[0]

    def test_exclude_poi_categories_invalid(self):
        """Test excluding invalid POI categories."""
        builder = SocialMapperBuilder()
        result = builder.exclude_poi_categories("utilities", "invalid_category")

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "Invalid POI categories for exclusion" in builder._validation_errors[0]

    def test_limit_pois_per_category(self):
        """Test setting POI limit per category."""
        builder = SocialMapperBuilder()
        result = builder.limit_pois_per_category(25)

        assert result is builder
        assert builder._config["max_pois_per_category"] == 25

    def test_limit_pois_per_category_invalid(self):
        """Test setting invalid POI limit per category."""
        builder = SocialMapperBuilder()
        result = builder.limit_pois_per_category(0)  # Invalid - must be positive

        assert result is builder
        assert len(builder._validation_errors) > 0
        assert "POI limit per category must be positive" in builder._validation_errors[0]

    def test_list_available_poi_categories(self):
        """Test listing available POI categories."""
        builder = SocialMapperBuilder()
        categories_info = builder.list_available_poi_categories()

        assert isinstance(categories_info, dict)
        assert "categories" in categories_info
        assert "total_categories" in categories_info
        assert "category_details" in categories_info
        assert len(categories_info["categories"]) > 0

        # Check specific expected categories
        expected_categories = ["food_and_drink", "healthcare", "education", "shopping"]
        for cat in expected_categories:
            assert cat in categories_info["categories"]

    def test_poi_discovery_complete_configuration(self):
        """Test complete POI discovery configuration chain."""
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Denver, CO", 20, "bike")
            .with_poi_categories("food_and_drink", "healthcare")
            .exclude_poi_categories("utilities")
            .limit_pois_per_category(15)
            .with_output_directory("/tmp/poi_test")
        )

        assert isinstance(builder, SocialMapperBuilder)
        assert builder._config["poi_discovery_enabled"] is True
        assert builder._config["poi_discovery_location"] == "Denver, CO"
        assert builder._config["poi_discovery_travel_time"] == 20
        assert builder._config["poi_discovery_travel_mode"] == TravelMode.BIKE
        assert builder._config["poi_categories"] == ["food_and_drink", "healthcare"]
        assert builder._config["exclude_poi_categories"] == ["utilities"]
        assert builder._config["max_pois_per_category"] == 15

    def test_poi_discovery_validation_conflicting_categories(self):
        """Test validation with conflicting include/exclude categories."""
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Miami, FL", 15)
            .with_poi_categories("food_and_drink", "healthcare")
            .exclude_poi_categories("healthcare", "utilities")  # Conflict with include
        )

        errors = builder.validate()
        assert len(errors) > 0
        assert any("Categories cannot be both included and excluded" in error for error in errors)
        assert "healthcare" in " ".join(errors)

    def test_poi_discovery_validation_missing_location(self):
        """Test validation with missing POI discovery location."""
        builder = SocialMapperBuilder()
        builder._config["poi_discovery_enabled"] = True  # Enable without proper setup

        errors = builder.validate()
        assert len(errors) > 0
        assert any("POI discovery location is required" in error for error in errors)

    def test_poi_discovery_validation_missing_travel_time(self):
        """Test validation with missing POI discovery travel time."""
        builder = SocialMapperBuilder()
        builder._config["poi_discovery_enabled"] = True
        builder._config["poi_discovery_location"] = "Austin, TX"
        # Missing travel time

        errors = builder.validate()
        assert len(errors) > 0
        assert any("POI discovery travel time is required" in error for error in errors)

    def test_poi_discovery_build_creates_config_object(self):
        """Test that build() creates NearbyPOIDiscoveryConfig object."""
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Phoenix, AZ", 25, TravelMode.DRIVE)
            .with_poi_categories("shopping", "recreation")
            .limit_pois_per_category(20)
        )

        config = builder.build()

        assert isinstance(config, dict)
        assert "poi_discovery_config" in config
        assert isinstance(config["poi_discovery_config"], NearbyPOIDiscoveryConfig)

        poi_config = config["poi_discovery_config"]
        assert poi_config.location == "Phoenix, AZ"
        assert poi_config.travel_time == 25
        assert poi_config.travel_mode == TravelMode.DRIVE
        assert poi_config.poi_categories == ["shopping", "recreation"]
        assert poi_config.max_pois_per_category == 20

    def test_poi_discovery_build_without_poi_discovery(self):
        """Test that build() works normally without POI discovery."""
        builder = (
            SocialMapperBuilder()
            .with_location("Los Angeles, CA")
            .with_osm_pois("amenity", "hospital")
        )

        config = builder.build()

        assert isinstance(config, dict)
        assert "poi_discovery_config" not in config
        assert config["poi_discovery_enabled"] is False

    def test_poi_discovery_validation_success(self):
        """Test successful validation with POI discovery."""
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Nashville, TN", 15, "walk")
            .with_poi_categories("food_and_drink", "education")
        )

        errors = builder.validate()
        assert len(errors) == 0

    def test_poi_discovery_with_coordinates_validation_success(self):
        """Test successful validation with coordinate-based POI discovery."""
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery((36.1627, -86.7816), 30, TravelMode.BIKE)  # Nashville coords
            .exclude_poi_categories("utilities")
        )

        errors = builder.validate()
        assert len(errors) == 0

    def test_poi_discovery_minimum_configuration(self):
        """Test minimum valid POI discovery configuration."""
        builder = SocialMapperBuilder().with_nearby_poi_discovery("Atlanta, GA", 10)

        errors = builder.validate()
        assert len(errors) == 0

        config = builder.build()
        poi_config = config["poi_discovery_config"]
        assert poi_config.location == "Atlanta, GA"
        assert poi_config.travel_time == 10
        assert poi_config.travel_mode == TravelMode.DRIVE  # Default
        assert poi_config.poi_categories is None  # No specific categories
        assert poi_config.exclude_categories is None

    def test_poi_discovery_output_configuration(self):
        """Test POI discovery inherits output configuration from builder."""
        output_dir = "/custom/output/path"
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Orlando, FL", 15)
            .with_output_directory(output_dir)
            .with_exports(csv=True, isochrones=False, maps=True)
        )

        config = builder.build()
        poi_config = config["poi_discovery_config"]

        assert str(poi_config.output_dir) == output_dir
        assert poi_config.export_csv is True
        assert poi_config.create_map is True

    def test_builder_allows_multiple_analysis_types(self):
        """Test builder allows combining POI discovery with other analysis types."""
        builder = (
            SocialMapperBuilder()
            .with_location("San Diego, CA")
            .with_osm_pois("amenity", "restaurant")
            .with_nearby_poi_discovery("San Diego, CA", 20)
            .with_census_variables("total_population")
        )

        errors = builder.validate()
        assert len(errors) == 0

        config = builder.build()

        # Both OSM and POI discovery should be configured
        assert "poi_type" in config
        assert "poi_name" in config
        assert "geocode_area" in config
        assert "poi_discovery_config" in config
        assert config["poi_discovery_enabled"] is True

    def test_poi_discovery_with_invalid_then_valid_travel_mode(self):
        """Test POI discovery error recovery with travel mode."""
        builder = SocialMapperBuilder()

        # First set invalid travel mode
        result1 = builder.with_nearby_poi_discovery("Dallas, TX", 15, "teleport")
        assert len(builder._validation_errors) > 0

        # Then set valid configuration - should still have errors from before
        result2 = builder.with_nearby_poi_discovery("Dallas, TX", 15, "drive")
        assert len(builder._validation_errors) > 0  # Previous error persists

        # Create fresh builder for valid config
        fresh_builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Dallas, TX", 15, "drive")
        )
        assert len(fresh_builder._validation_errors) == 0

    def test_poi_discovery_category_methods_override(self):
        """Test that category methods override previous settings."""
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Houston, TX", 15, poi_categories=["food_and_drink"])
            .with_poi_categories("healthcare", "education")  # Should override
        )

        assert builder._config["poi_categories"] == ["healthcare", "education"]

        # Test exclude override
        builder.exclude_poi_categories("utilities", "services")
        assert builder._config["exclude_poi_categories"] == ["utilities", "services"]

    def test_poi_discovery_limit_override(self):
        """Test that limit method overrides previous settings."""
        builder = (
            SocialMapperBuilder()
            .with_nearby_poi_discovery("Las Vegas, NV", 15)
            .limit_pois_per_category(10)
            .limit_pois_per_category(25)  # Should override
        )

        assert builder._config["max_pois_per_category"] == 25
