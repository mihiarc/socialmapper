"""Tests for POI discovery data structures."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from socialmapper.api.result_types import (
    DiscoveredPOI,
    NearbyPOIDiscoveryConfig,
    NearbyPOIResult,
)
from socialmapper.constants import MAX_TRAVEL_TIME, MIN_TRAVEL_TIME
from socialmapper.isochrone.travel_modes import TravelMode


class TestDiscoveredPOI:
    """Test the DiscoveredPOI frozen dataclass."""

    def test_valid_poi_creation(self):
        """Test creating a valid DiscoveredPOI."""
        poi = DiscoveredPOI(
            id="poi_123",
            name="Test Coffee Shop",
            category="food",
            subcategory="cafe",
            latitude=40.7128,
            longitude=-74.0060,
            address="123 Main St, New York, NY",
            straight_line_distance_m=500.0,
            estimated_travel_time_min=10.0,
            osm_type="node",
            osm_id=12345,
            tags={"amenity": "cafe", "cuisine": "coffee_shop"},
            phone="+1-212-555-0123",
            website="https://example.com",
            opening_hours="Mo-Fr 07:00-20:00",
        )

        assert poi.id == "poi_123"
        assert poi.name == "Test Coffee Shop"
        assert poi.category == "food"
        assert poi.subcategory == "cafe"
        assert poi.latitude == 40.7128
        assert poi.longitude == -74.0060
        assert poi.address == "123 Main St, New York, NY"
        assert poi.straight_line_distance_m == 500.0
        assert poi.estimated_travel_time_min == 10.0
        assert poi.osm_type == "node"
        assert poi.osm_id == 12345
        assert poi.tags == {"amenity": "cafe", "cuisine": "coffee_shop"}
        assert poi.phone == "+1-212-555-0123"
        assert poi.website == "https://example.com"
        assert poi.opening_hours == "Mo-Fr 07:00-20:00"

    def test_minimal_poi_creation(self):
        """Test creating a POI with only required fields."""
        poi = DiscoveredPOI(
            id="poi_456",
            name="Simple Store",
            category="retail",
            subcategory="general",
            latitude=51.5074,
            longitude=-0.1278,
            straight_line_distance_m=1000.0,
            osm_type="way",
            osm_id=67890,
        )

        assert poi.id == "poi_456"
        assert poi.name == "Simple Store"
        assert poi.address is None
        assert poi.estimated_travel_time_min is None
        assert poi.tags == {}
        assert poi.phone is None
        assert poi.website is None
        assert poi.opening_hours is None

    def test_poi_is_frozen(self):
        """Test that DiscoveredPOI is immutable (frozen)."""
        poi = DiscoveredPOI(
            id="poi_789",
            name="Frozen Test",
            category="test",
            subcategory="test",
            latitude=0.0,
            longitude=0.0,
            straight_line_distance_m=100.0,
            osm_type="node",
            osm_id=111,
        )

        with pytest.raises(FrozenInstanceError):
            poi.name = "New Name"

        with pytest.raises(FrozenInstanceError):
            poi.latitude = 45.0

    def test_empty_id_validation(self):
        """Test that empty POI ID raises ValueError."""
        with pytest.raises(ValueError, match="POI ID cannot be empty"):
            DiscoveredPOI(
                id="",
                name="Test",
                category="test",
                subcategory="test",
                latitude=0.0,
                longitude=0.0,
                straight_line_distance_m=100.0,
                osm_type="node",
                osm_id=123,
            )

    def test_empty_name_validation(self):
        """Test that empty POI name raises ValueError."""
        with pytest.raises(ValueError, match="POI name cannot be empty"):
            DiscoveredPOI(
                id="poi_123",
                name="",
                category="test",
                subcategory="test",
                latitude=0.0,
                longitude=0.0,
                straight_line_distance_m=100.0,
                osm_type="node",
                osm_id=123,
            )

    def test_invalid_latitude(self):
        """Test that invalid latitude raises ValueError."""
        # Latitude too high
        with pytest.raises(ValueError, match="Invalid coordinates"):
            DiscoveredPOI(
                id="poi_123",
                name="Test",
                category="test",
                subcategory="test",
                latitude=91.0,  # > 90
                longitude=0.0,
                straight_line_distance_m=100.0,
                osm_type="node",
                osm_id=123,
            )

        # Latitude too low
        with pytest.raises(ValueError, match="Invalid coordinates"):
            DiscoveredPOI(
                id="poi_123",
                name="Test",
                category="test",
                subcategory="test",
                latitude=-91.0,  # < -90
                longitude=0.0,
                straight_line_distance_m=100.0,
                osm_type="node",
                osm_id=123,
            )

    def test_invalid_longitude(self):
        """Test that invalid longitude raises ValueError."""
        # Longitude too high
        with pytest.raises(ValueError, match="Invalid coordinates"):
            DiscoveredPOI(
                id="poi_123",
                name="Test",
                category="test",
                subcategory="test",
                latitude=0.0,
                longitude=181.0,  # > 180
                straight_line_distance_m=100.0,
                osm_type="node",
                osm_id=123,
            )

        # Longitude too low
        with pytest.raises(ValueError, match="Invalid coordinates"):
            DiscoveredPOI(
                id="poi_123",
                name="Test",
                category="test",
                subcategory="test",
                latitude=0.0,
                longitude=-181.0,  # < -180
                straight_line_distance_m=100.0,
                osm_type="node",
                osm_id=123,
            )

    def test_edge_case_coordinates(self):
        """Test edge case coordinates (poles, date line)."""
        # North pole
        poi_north = DiscoveredPOI(
            id="poi_north",
            name="North Pole",
            category="test",
            subcategory="test",
            latitude=90.0,
            longitude=0.0,
            straight_line_distance_m=100.0,
            osm_type="node",
            osm_id=123,
        )
        assert poi_north.latitude == 90.0

        # South pole
        poi_south = DiscoveredPOI(
            id="poi_south",
            name="South Pole",
            category="test",
            subcategory="test",
            latitude=-90.0,
            longitude=0.0,
            straight_line_distance_m=100.0,
            osm_type="node",
            osm_id=123,
        )
        assert poi_south.latitude == -90.0

        # Date line
        poi_dateline = DiscoveredPOI(
            id="poi_dateline",
            name="Date Line",
            category="test",
            subcategory="test",
            latitude=0.0,
            longitude=180.0,
            straight_line_distance_m=100.0,
            osm_type="node",
            osm_id=123,
        )
        assert poi_dateline.longitude == 180.0

        # Anti-meridian
        poi_antimeridian = DiscoveredPOI(
            id="poi_antimeridian",
            name="Anti-Meridian",
            category="test",
            subcategory="test",
            latitude=0.0,
            longitude=-180.0,
            straight_line_distance_m=100.0,
            osm_type="node",
            osm_id=123,
        )
        assert poi_antimeridian.longitude == -180.0

    def test_negative_distance_validation(self):
        """Test that negative distance raises ValueError."""
        with pytest.raises(ValueError, match="Distance cannot be negative"):
            DiscoveredPOI(
                id="poi_123",
                name="Test",
                category="test",
                subcategory="test",
                latitude=0.0,
                longitude=0.0,
                straight_line_distance_m=-100.0,
                osm_type="node",
                osm_id=123,
            )

    def test_negative_travel_time_validation(self):
        """Test that negative travel time raises ValueError."""
        with pytest.raises(ValueError, match="Travel time cannot be negative"):
            DiscoveredPOI(
                id="poi_123",
                name="Test",
                category="test",
                subcategory="test",
                latitude=0.0,
                longitude=0.0,
                straight_line_distance_m=100.0,
                estimated_travel_time_min=-5.0,
                osm_type="node",
                osm_id=123,
            )

    def test_zero_distance_allowed(self):
        """Test that zero distance is allowed (POI at origin)."""
        poi = DiscoveredPOI(
            id="poi_123",
            name="Origin POI",
            category="test",
            subcategory="test",
            latitude=0.0,
            longitude=0.0,
            straight_line_distance_m=0.0,
            estimated_travel_time_min=0.0,
            osm_type="node",
            osm_id=123,
        )
        assert poi.straight_line_distance_m == 0.0
        assert poi.estimated_travel_time_min == 0.0


class TestNearbyPOIDiscoveryConfig:
    """Test the NearbyPOIDiscoveryConfig dataclass."""

    def test_valid_config_with_address(self):
        """Test creating a valid config with address location."""
        config = NearbyPOIDiscoveryConfig(
            location="123 Main St, New York, NY",
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            poi_categories=["food", "retail"],
            exclude_categories=["gas_station"],
            export_csv=True,
            export_geojson=False,
            create_map=True,
            output_dir=Path("/tmp/output"),
            max_pois_per_category=50,
            include_poi_details=True,
        )

        assert config.location == "123 Main St, New York, NY"
        assert config.travel_time == 30
        assert config.travel_mode == TravelMode.DRIVE
        assert config.poi_categories == ["food", "retail"]
        assert config.exclude_categories == ["gas_station"]
        assert config.export_csv is True
        assert config.export_geojson is False
        assert config.create_map is True
        assert config.output_dir == Path("/tmp/output")
        assert config.max_pois_per_category == 50
        assert config.include_poi_details is True

    def test_valid_config_with_coordinates(self):
        """Test creating a valid config with coordinate location."""
        config = NearbyPOIDiscoveryConfig(
            location=(40.7128, -74.0060),
            travel_time=15,
            travel_mode=TravelMode.WALK,
        )

        assert config.location == (40.7128, -74.0060)
        assert config.travel_time == 15
        assert config.travel_mode == TravelMode.WALK

        # Check defaults
        assert config.poi_categories is None
        assert config.exclude_categories is None
        assert config.export_csv is True
        assert config.export_geojson is True
        assert config.create_map is True
        assert config.output_dir == Path("output")
        assert config.max_pois_per_category is None
        assert config.include_poi_details is True

    def test_minimal_config(self):
        """Test creating config with minimal required fields."""
        config = NearbyPOIDiscoveryConfig(
            location="New York, NY",
            travel_time=30,
        )

        assert config.location == "New York, NY"
        assert config.travel_time == 30
        assert config.travel_mode == TravelMode.DRIVE  # default

    def test_travel_time_validation_min(self):
        """Test that travel time below minimum raises ValueError."""
        with pytest.raises(ValueError, match=f"Travel time must be between {MIN_TRAVEL_TIME} and {MAX_TRAVEL_TIME} minutes"):
            NearbyPOIDiscoveryConfig(
                location="Test Location",
                travel_time=0,  # < MIN_TRAVEL_TIME (1)
            )

    def test_travel_time_validation_max(self):
        """Test that travel time above maximum raises ValueError."""
        with pytest.raises(ValueError, match=f"Travel time must be between {MIN_TRAVEL_TIME} and {MAX_TRAVEL_TIME} minutes"):
            NearbyPOIDiscoveryConfig(
                location="Test Location",
                travel_time=121,  # > MAX_TRAVEL_TIME (120)
            )

    def test_travel_time_edge_cases(self):
        """Test travel time at boundaries."""
        # Minimum allowed
        config_min = NearbyPOIDiscoveryConfig(
            location="Test Location",
            travel_time=MIN_TRAVEL_TIME,
        )
        assert config_min.travel_time == MIN_TRAVEL_TIME

        # Maximum allowed
        config_max = NearbyPOIDiscoveryConfig(
            location="Test Location",
            travel_time=MAX_TRAVEL_TIME,
        )
        assert config_max.travel_time == MAX_TRAVEL_TIME

    def test_invalid_coordinate_location(self):
        """Test that invalid coordinates raise ValueError."""
        # Invalid latitude
        with pytest.raises(ValueError, match="Invalid coordinates"):
            NearbyPOIDiscoveryConfig(
                location=(91.0, 0.0),  # latitude > 90
                travel_time=30,
            )

        # Invalid longitude
        with pytest.raises(ValueError, match="Invalid coordinates"):
            NearbyPOIDiscoveryConfig(
                location=(0.0, 181.0),  # longitude > 180
                travel_time=30,
            )

    def test_empty_address_location(self):
        """Test that empty address string raises ValueError."""
        with pytest.raises(ValueError, match="Location address cannot be empty"):
            NearbyPOIDiscoveryConfig(
                location="",
                travel_time=30,
            )

        # Whitespace-only string
        with pytest.raises(ValueError, match="Location address cannot be empty"):
            NearbyPOIDiscoveryConfig(
                location="   ",
                travel_time=30,
            )

    def test_invalid_location_type(self):
        """Test that invalid location type raises ValueError."""
        with pytest.raises(ValueError, match="Location must be either an address string or \\(lat, lon\\) tuple"):
            NearbyPOIDiscoveryConfig(
                location=123,  # Invalid type
                travel_time=30,
            )

        with pytest.raises(ValueError, match="Location must be either an address string or \\(lat, lon\\) tuple"):
            NearbyPOIDiscoveryConfig(
                location=["New York"],  # Invalid type
                travel_time=30,
            )

    def test_invalid_max_pois_per_category(self):
        """Test that invalid max_pois_per_category raises ValueError."""
        with pytest.raises(ValueError, match="max_pois_per_category must be positive"):
            NearbyPOIDiscoveryConfig(
                location="Test Location",
                travel_time=30,
                max_pois_per_category=0,
            )

        with pytest.raises(ValueError, match="max_pois_per_category must be positive"):
            NearbyPOIDiscoveryConfig(
                location="Test Location",
                travel_time=30,
                max_pois_per_category=-10,
            )

    def test_all_travel_modes(self):
        """Test config with all available travel modes."""
        for mode in TravelMode:
            config = NearbyPOIDiscoveryConfig(
                location="Test Location",
                travel_time=30,
                travel_mode=mode,
            )
            assert config.travel_mode == mode


class TestNearbyPOIResult:
    """Test the NearbyPOIResult dataclass."""

    def test_valid_result_creation(self):
        """Test creating a valid NearbyPOIResult."""
        poi1 = DiscoveredPOI(
            id="poi_1",
            name="Coffee Shop",
            category="food",
            subcategory="cafe",
            latitude=40.7128,
            longitude=-74.0060,
            straight_line_distance_m=500.0,
            osm_type="node",
            osm_id=123,
        )

        poi2 = DiscoveredPOI(
            id="poi_2",
            name="Grocery Store",
            category="retail",
            subcategory="supermarket",
            latitude=40.7150,
            longitude=-74.0080,
            straight_line_distance_m=800.0,
            osm_type="way",
            osm_id=456,
        )

        result = NearbyPOIResult(
            origin_location={"lat": 40.7100, "lon": -74.0050},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=25.5,
            pois_by_category={
                "food": [poi1],
                "retail": [poi2],
            },
            total_poi_count=2,
            category_counts={"food": 1, "retail": 1},
            files_generated={
                "csv": Path("/tmp/pois.csv"),
                "geojson": Path("/tmp/pois.geojson"),
            },
            metadata={"processing_time": 5.2},
            warnings=["Some POIs may be missing"],
        )

        assert result.origin_location == {"lat": 40.7100, "lon": -74.0050}
        assert result.travel_time == 30
        assert result.travel_mode == TravelMode.DRIVE
        assert result.isochrone_area_km2 == 25.5
        assert len(result.pois_by_category) == 2
        assert result.total_poi_count == 2
        assert result.category_counts == {"food": 1, "retail": 1}
        assert result.files_generated["csv"] == Path("/tmp/pois.csv")
        assert result.metadata["processing_time"] == 5.2
        assert len(result.warnings) == 1

    def test_minimal_result_creation(self):
        """Test creating result with minimal fields."""
        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=15,
            travel_mode=TravelMode.WALK,
            isochrone_area_km2=2.5,
        )

        assert result.origin_location == {"lat": 0.0, "lon": 0.0}
        assert result.travel_time == 15
        assert result.travel_mode == TravelMode.WALK
        assert result.isochrone_area_km2 == 2.5
        assert result.pois_by_category == {}
        assert result.total_poi_count == 0
        assert result.category_counts == {}
        assert result.isochrone_geometry is None
        assert result.poi_points is None
        assert result.files_generated == {}
        assert result.metadata == {}
        assert result.warnings == []

    def test_success_property_with_pois(self):
        """Test success property returns True when POIs found."""
        poi = DiscoveredPOI(
            id="poi_1",
            name="Test POI",
            category="test",
            subcategory="test",
            latitude=0.0,
            longitude=0.0,
            straight_line_distance_m=100.0,
            osm_type="node",
            osm_id=123,
        )

        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
            pois_by_category={"test": [poi]},
            total_poi_count=1,
        )

        assert result.success is True

    def test_success_property_without_pois(self):
        """Test success property returns False when no POIs found."""
        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
            total_poi_count=0,
        )

        assert result.success is False

    def test_get_all_pois(self):
        """Test get_all_pois method returns flat list of POIs."""
        poi1 = DiscoveredPOI(
            id="poi_1", name="POI 1", category="cat1", subcategory="sub1",
            latitude=0.0, longitude=0.0, straight_line_distance_m=100.0,
            osm_type="node", osm_id=1,
        )
        poi2 = DiscoveredPOI(
            id="poi_2", name="POI 2", category="cat1", subcategory="sub1",
            latitude=0.0, longitude=0.0, straight_line_distance_m=200.0,
            osm_type="node", osm_id=2,
        )
        poi3 = DiscoveredPOI(
            id="poi_3", name="POI 3", category="cat2", subcategory="sub2",
            latitude=0.0, longitude=0.0, straight_line_distance_m=300.0,
            osm_type="node", osm_id=3,
        )

        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
            pois_by_category={
                "cat1": [poi1, poi2],
                "cat2": [poi3],
            },
        )

        all_pois = result.get_all_pois()
        assert len(all_pois) == 3
        assert poi1 in all_pois
        assert poi2 in all_pois
        assert poi3 in all_pois

    def test_get_all_pois_empty(self):
        """Test get_all_pois with no POIs."""
        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
        )

        all_pois = result.get_all_pois()
        assert all_pois == []

    def test_get_pois_by_distance(self):
        """Test get_pois_by_distance returns sorted POIs."""
        poi1 = DiscoveredPOI(
            id="poi_1", name="Far", category="test", subcategory="test",
            latitude=0.0, longitude=0.0, straight_line_distance_m=1000.0,
            osm_type="node", osm_id=1,
        )
        poi2 = DiscoveredPOI(
            id="poi_2", name="Near", category="test", subcategory="test",
            latitude=0.0, longitude=0.0, straight_line_distance_m=100.0,
            osm_type="node", osm_id=2,
        )
        poi3 = DiscoveredPOI(
            id="poi_3", name="Medium", category="test", subcategory="test",
            latitude=0.0, longitude=0.0, straight_line_distance_m=500.0,
            osm_type="node", osm_id=3,
        )

        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
            pois_by_category={"test": [poi1, poi2, poi3]},
        )

        sorted_pois = result.get_pois_by_distance()
        assert len(sorted_pois) == 3
        assert sorted_pois[0] == poi2  # 100m
        assert sorted_pois[1] == poi3  # 500m
        assert sorted_pois[2] == poi1  # 1000m

    def test_get_pois_by_distance_with_max(self):
        """Test get_pois_by_distance with max_distance_m filter."""
        poi1 = DiscoveredPOI(
            id="poi_1", name="Far", category="test", subcategory="test",
            latitude=0.0, longitude=0.0, straight_line_distance_m=1000.0,
            osm_type="node", osm_id=1,
        )
        poi2 = DiscoveredPOI(
            id="poi_2", name="Near", category="test", subcategory="test",
            latitude=0.0, longitude=0.0, straight_line_distance_m=100.0,
            osm_type="node", osm_id=2,
        )
        poi3 = DiscoveredPOI(
            id="poi_3", name="Medium", category="test", subcategory="test",
            latitude=0.0, longitude=0.0, straight_line_distance_m=500.0,
            osm_type="node", osm_id=3,
        )

        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
            pois_by_category={"test": [poi1, poi2, poi3]},
        )

        # Filter to POIs within 600m
        filtered_pois = result.get_pois_by_distance(max_distance_m=600.0)
        assert len(filtered_pois) == 2
        assert filtered_pois[0] == poi2  # 100m
        assert filtered_pois[1] == poi3  # 500m
        # poi1 (1000m) should be excluded

    def test_get_summary_stats_with_pois(self):
        """Test get_summary_stats with multiple POIs."""
        poi1 = DiscoveredPOI(
            id="poi_1", name="POI 1", category="cat1", subcategory="sub1",
            latitude=0.0, longitude=0.0, straight_line_distance_m=100.0,
            osm_type="node", osm_id=1,
        )
        poi2 = DiscoveredPOI(
            id="poi_2", name="POI 2", category="cat1", subcategory="sub1",
            latitude=0.0, longitude=0.0, straight_line_distance_m=200.0,
            osm_type="node", osm_id=2,
        )
        poi3 = DiscoveredPOI(
            id="poi_3", name="POI 3", category="cat2", subcategory="sub2",
            latitude=0.0, longitude=0.0, straight_line_distance_m=300.0,
            osm_type="node", osm_id=3,
        )

        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=15.5,
            pois_by_category={
                "cat1": [poi1, poi2],
                "cat2": [poi3],
            },
        )

        stats = result.get_summary_stats()
        assert stats["total_pois"] == 3
        assert stats["categories"] == 2
        assert stats["avg_distance_m"] == 200.0  # (100 + 200 + 300) / 3
        assert stats["min_distance_m"] == 100.0
        assert stats["max_distance_m"] == 300.0
        assert stats["isochrone_area_km2"] == 15.5

    def test_get_summary_stats_empty(self):
        """Test get_summary_stats with no POIs."""
        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
        )

        stats = result.get_summary_stats()
        assert stats["total_pois"] == 0
        assert stats["categories"] == 0
        assert stats["avg_distance_m"] == 0
        assert stats["min_distance_m"] == 0
        assert stats["max_distance_m"] == 0

    def test_result_with_geodataframes(self):
        """Test result can store geometry data (using None as placeholder)."""
        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
            isochrone_geometry="placeholder_geodataframe",  # In real usage, this would be a GeoDataFrame
            poi_points="placeholder_geodataframe",  # In real usage, this would be a GeoDataFrame
        )

        assert result.isochrone_geometry == "placeholder_geodataframe"
        assert result.poi_points == "placeholder_geodataframe"

    def test_mutable_collections(self):
        """Test that mutable collections can be modified."""
        result = NearbyPOIResult(
            origin_location={"lat": 0.0, "lon": 0.0},
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=10.0,
        )

        # Add POI to category
        poi = DiscoveredPOI(
            id="poi_1", name="New POI", category="test", subcategory="test",
            latitude=0.0, longitude=0.0, straight_line_distance_m=100.0,
            osm_type="node", osm_id=123,
        )
        result.pois_by_category["test"] = [poi]
        assert len(result.pois_by_category) == 1

        # Add warning
        result.warnings.append("New warning")
        assert len(result.warnings) == 1

        # Add metadata
        result.metadata["new_key"] = "new_value"
        assert result.metadata["new_key"] == "new_value"

        # Add file
        result.files_generated["map"] = Path("/tmp/map.html")
        assert result.files_generated["map"] == Path("/tmp/map.html")


class TestIntegration:
    """Integration tests for POI discovery data structures."""

    def test_complete_workflow(self):
        """Test a complete workflow with all data structures."""
        # Create configuration
        config = NearbyPOIDiscoveryConfig(
            location=(40.7589, -73.9851),  # Times Square, NYC
            travel_time=15,
            travel_mode=TravelMode.WALK,
            poi_categories=["food", "retail", "entertainment"],
            max_pois_per_category=10,
        )

        # Simulate discovered POIs
        pois = []
        categories = ["food", "retail", "entertainment"]
        for i in range(15):
            category = categories[i % 3]
            poi = DiscoveredPOI(
                id=f"poi_{i}",
                name=f"Place {i}",
                category=category,
                subcategory=f"sub_{category}",
                latitude=40.7589 + (i * 0.001),
                longitude=-73.9851 + (i * 0.001),
                straight_line_distance_m=100.0 * (i + 1),
                estimated_travel_time_min=2.0 * (i + 1),
                osm_type="node",
                osm_id=1000 + i,
                tags={"name": f"Place {i}", "category": category},
            )
            pois.append(poi)

        # Create result
        result = NearbyPOIResult(
            origin_location={"lat": 40.7589, "lon": -73.9851},
            travel_time=config.travel_time,
            travel_mode=config.travel_mode,
            isochrone_area_km2=3.14,  # ~1km radius circle
            pois_by_category={
                "food": [p for p in pois if p.category == "food"],
                "retail": [p for p in pois if p.category == "retail"],
                "entertainment": [p for p in pois if p.category == "entertainment"],
            },
            total_poi_count=len(pois),
            category_counts={
                "food": 5,
                "retail": 5,
                "entertainment": 5,
            },
            files_generated={
                "csv": Path("output/pois.csv"),
                "geojson": Path("output/pois.geojson"),
                "map": Path("output/map.html"),
            },
        )

        # Verify integration
        assert result.success is True
        assert result.total_poi_count == 15
        assert len(result.get_all_pois()) == 15

        # Check sorting
        sorted_pois = result.get_pois_by_distance()
        assert sorted_pois[0].straight_line_distance_m == 100.0
        assert sorted_pois[-1].straight_line_distance_m == 1500.0

        # Check filtering
        nearby_pois = result.get_pois_by_distance(max_distance_m=500.0)
        assert len(nearby_pois) == 5  # POIs 0-4 with distances 100-500m

        # Check statistics
        stats = result.get_summary_stats()
        assert stats["total_pois"] == 15
        assert stats["categories"] == 3
        assert stats["avg_distance_m"] == 800.0  # Average of 100, 200, ..., 1500

    def test_serialization_compatibility(self):
        """Test that data structures can be serialized (for API responses)."""
        import json
        from dataclasses import asdict

        # Create POI
        poi = DiscoveredPOI(
            id="poi_123",
            name="Test POI",
            category="test",
            subcategory="test",
            latitude=40.7128,
            longitude=-74.0060,
            straight_line_distance_m=500.0,
            osm_type="node",
            osm_id=12345,
        )

        # Convert to dict (simulating API serialization)
        poi_dict = asdict(poi)
        poi_json = json.dumps(poi_dict)

        # Verify it can be serialized and deserialized
        poi_data = json.loads(poi_json)
        assert poi_data["id"] == "poi_123"
        assert poi_data["latitude"] == 40.7128

        # Test config serialization
        config = NearbyPOIDiscoveryConfig(
            location="New York, NY",
            travel_time=30,
            travel_mode=TravelMode.DRIVE,
        )

        # Need special handling for Path and Enum
        config_dict = asdict(config)
        config_dict["output_dir"] = str(config_dict["output_dir"])
        config_dict["travel_mode"] = config_dict["travel_mode"].value

        config_json = json.dumps(config_dict)
        config_data = json.loads(config_json)
        assert config_data["location"] == "New York, NY"
        assert config_data["travel_time"] == 30
