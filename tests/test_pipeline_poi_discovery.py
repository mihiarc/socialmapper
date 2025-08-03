"""Integration tests for POI discovery pipeline stage."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from socialmapper.api.result_types import (
    DiscoveredPOI,
    ErrorType,
    NearbyPOIDiscoveryConfig,
    NearbyPOIResult,
    Ok,
)
from socialmapper.geocoding.models import AddressInput, AddressQuality, GeocodingResult
from socialmapper.isochrone.travel_modes import TravelMode
from socialmapper.pipeline.poi_discovery import (
    NearbyPOIDiscoveryStage,
    discover_pois_near_address,
    discover_pois_near_coordinates,
    execute_poi_discovery_pipeline,
)


class TestNearbyPOIDiscoveryStage:
    """Test the NearbyPOIDiscoveryStage class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_config = NearbyPOIDiscoveryConfig(
            location="Chapel Hill, NC",
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            poi_categories=["food_and_drink", "shopping"],
            export_csv=True,
            export_geojson=True,
            create_map=False,  # Skip map creation for tests
            output_dir=self.temp_dir,
        )

    @patch("socialmapper.pipeline.poi_discovery.geocode_address")
    @patch("socialmapper.pipeline.poi_discovery.create_isochrone_from_poi")
    @patch("socialmapper.pipeline.poi_discovery.query_pois_in_polygon")
    def test_successful_pipeline_execution(
        self, mock_query_pois, mock_create_isochrone, mock_geocode
    ):
        """Test successful execution of the complete pipeline."""
        # Mock geocoding
        mock_geocode.return_value = GeocodingResult(
            input_address=AddressInput(address="Chapel Hill, NC"),
            success=True,
            latitude=35.9132,
            longitude=-79.0558,
            formatted_address="Chapel Hill, NC, USA",
            quality=AddressQuality.EXACT,
        )

        # Mock isochrone generation
        isochrone_polygon = Polygon([
            (-79.0658, 35.9032),
            (-79.0458, 35.9032),
            (-79.0458, 35.9232),
            (-79.0658, 35.9232),
            (-79.0658, 35.9032),
        ])
        mock_isochrone_gdf = gpd.GeoDataFrame(
            {"geometry": [isochrone_polygon]}, crs="EPSG:4326"
        )
        mock_create_isochrone.return_value = mock_isochrone_gdf

        # Mock POI query
        mock_pois = [
            {
                "type": "node",
                "id": 123,
                "lat": 35.9140,
                "lon": -79.0560,
                "tags": {
                    "name": "Test Coffee Shop",
                    "amenity": "cafe",
                    "cuisine": "coffee_shop",
                },
            },
            {
                "type": "way",
                "id": 456,
                "lat": 35.9150,
                "lon": -79.0570,
                "tags": {
                    "name": "Test Grocery Store",
                    "shop": "supermarket",
                },
            },
        ]
        mock_query_pois.return_value = mock_pois

        # Execute pipeline
        stage = NearbyPOIDiscoveryStage(self.test_config)
        result = stage.execute()

        # Verify success
        assert result.is_ok()
        poi_result = result.unwrap()

        assert isinstance(poi_result, NearbyPOIResult)
        assert poi_result.success
        assert poi_result.total_poi_count == 2
        assert len(poi_result.pois_by_category) >= 1
        assert poi_result.origin_location["lat"] == 35.9132
        assert poi_result.origin_location["lon"] == -79.0558
        assert poi_result.isochrone_area_km2 > 0

        # Verify mocks were called
        mock_geocode.assert_called_once()
        mock_create_isochrone.assert_called_once()
        mock_query_pois.assert_called_once()

    @patch("socialmapper.pipeline.poi_discovery.geocode_address")
    def test_geocoding_failure(self, mock_geocode):
        """Test handling of geocoding failure."""
        # Mock failed geocoding
        mock_geocode.return_value = GeocodingResult(
            input_address=AddressInput(address="Invalid Address"),
            success=False,
            latitude=None,
            longitude=None,
            formatted_address="",
            quality=AddressQuality.FAILED,
        )

        stage = NearbyPOIDiscoveryStage(self.test_config)
        result = stage.execute()

        # Verify error handling
        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.LOCATION_GEOCODING
        assert "Failed to geocode address" in error.message

    @patch("socialmapper.pipeline.poi_discovery.geocode_address")
    @patch("socialmapper.pipeline.poi_discovery.create_isochrone_from_poi")
    def test_isochrone_generation_failure(self, mock_create_isochrone, mock_geocode):
        """Test handling of isochrone generation failure."""
        # Mock successful geocoding
        mock_geocode.return_value = GeocodingResult(
            input_address=AddressInput(address="Chapel Hill, NC"),
            success=True,
            latitude=35.9132,
            longitude=-79.0558,
            formatted_address="Chapel Hill, NC, USA",
            quality=AddressQuality.EXACT,
        )

        # Mock failed isochrone generation
        mock_create_isochrone.return_value = None

        stage = NearbyPOIDiscoveryStage(self.test_config)
        result = stage.execute()

        # Verify error handling
        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.ISOCHRONE_GENERATION
        assert "Failed to generate isochrone" in error.message

    @patch("socialmapper.pipeline.poi_discovery.geocode_address")
    @patch("socialmapper.pipeline.poi_discovery.create_isochrone_from_poi")
    @patch("socialmapper.pipeline.poi_discovery.query_pois_in_polygon")
    def test_no_pois_found(self, mock_query_pois, mock_create_isochrone, mock_geocode):
        """Test handling when no POIs are found."""
        # Mock successful geocoding and isochrone
        mock_geocode.return_value = GeocodingResult(
            input_address=AddressInput(address="Chapel Hill, NC"),
            success=True,
            latitude=35.9132,
            longitude=-79.0558,
            formatted_address="Chapel Hill, NC, USA",
            quality=AddressQuality.EXACT,
        )

        isochrone_polygon = Polygon([
            (-79.0658, 35.9032),
            (-79.0458, 35.9032),
            (-79.0458, 35.9232),
            (-79.0658, 35.9232),
            (-79.0658, 35.9032),
        ])
        mock_isochrone_gdf = gpd.GeoDataFrame(
            {"geometry": [isochrone_polygon]}, crs="EPSG:4326"
        )
        mock_create_isochrone.return_value = mock_isochrone_gdf

        # Mock empty POI query result
        mock_query_pois.return_value = []

        stage = NearbyPOIDiscoveryStage(self.test_config)
        result = stage.execute()

        # Verify error handling
        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.POI_QUERY
        assert "No POIs found" in error.message

    def test_coordinate_input(self):
        """Test pipeline with coordinate input instead of address."""
        config = NearbyPOIDiscoveryConfig(
            location=(35.9132, -79.0558),  # Coordinates instead of address
            travel_time=10,
            travel_mode=TravelMode.WALK,
            output_dir=self.temp_dir,
        )

        stage = NearbyPOIDiscoveryStage(config)

        # Test geocoding step with coordinates
        geocoding_result = stage._geocode_origin()
        assert geocoding_result.is_ok()
        lat, lon = geocoding_result.unwrap()
        assert lat == 35.9132
        assert lon == -79.0558

    @patch("socialmapper.pipeline.poi_discovery.geocode_address")
    @patch("socialmapper.pipeline.poi_discovery.create_isochrone_from_poi")
    @patch("socialmapper.pipeline.poi_discovery.query_pois_in_polygon")
    def test_poi_processing_and_categorization(
        self, mock_query_pois, mock_create_isochrone, mock_geocode
    ):
        """Test POI processing and categorization logic."""
        # Mock setup
        mock_geocode.return_value = GeocodingResult(
            input_address=AddressInput(address="Chapel Hill, NC"),
            success=True,
            latitude=35.9132,
            longitude=-79.0558,
            formatted_address="Chapel Hill, NC, USA",
            quality=AddressQuality.EXACT,
        )

        isochrone_polygon = Polygon([
            (-79.0658, 35.9032),
            (-79.0458, 35.9032),
            (-79.0458, 35.9232),
            (-79.0658, 35.9232),
            (-79.0658, 35.9032),
        ])
        mock_isochrone_gdf = gpd.GeoDataFrame(
            {"geometry": [isochrone_polygon]}, crs="EPSG:4326"
        )
        mock_create_isochrone.return_value = mock_isochrone_gdf

        # Mock POIs with various tags for categorization testing
        mock_pois = [
            {
                "type": "node",
                "id": 1,
                "lat": 35.9140,
                "lon": -79.0560,
                "tags": {
                    "name": "Coffee Place",
                    "amenity": "cafe",
                    "addr:street": "Main St",
                    "phone": "+1-919-555-0123",
                    "website": "https://example.com",
                    "opening_hours": "Mo-Fr 07:00-20:00",
                },
            },
            {
                "type": "way",
                "id": 2,
                "lat": 35.9150,
                "lon": -79.0570,
                "tags": {
                    "name": "Pizza Shop",
                    "amenity": "restaurant",
                    "cuisine": "pizza",
                },
            },
            {
                "type": "node",
                "id": 3,
                "lat": 35.9160,
                "lon": -79.0580,
                "tags": {
                    "shop": "supermarket",
                    "name": "Grocery Store",
                },
            },
        ]
        mock_query_pois.return_value = mock_pois

        # Test with POI details enabled
        config = NearbyPOIDiscoveryConfig(
            location=(35.9132, -79.0558),
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            include_poi_details=True,
            output_dir=self.temp_dir,
        )

        stage = NearbyPOIDiscoveryStage(config)
        result = stage.execute()

        assert result.is_ok()
        poi_result = result.unwrap()

        # Verify POI processing
        assert poi_result.total_poi_count == 3

        # Check that POIs are categorized
        all_pois = poi_result.get_all_pois()
        assert len(all_pois) == 3

        # Find the coffee shop POI to verify details
        coffee_poi = next(p for p in all_pois if "Coffee" in p.name)
        assert coffee_poi.phone == "+1-919-555-0123"
        assert coffee_poi.website == "https://example.com"
        assert coffee_poi.opening_hours == "Mo-Fr 07:00-20:00"
        assert "Main St" in coffee_poi.address

    @patch("socialmapper.pipeline.poi_discovery.geocode_address")
    @patch("socialmapper.pipeline.poi_discovery.create_isochrone_from_poi")
    @patch("socialmapper.pipeline.poi_discovery.query_pois_in_polygon")
    def test_max_pois_per_category_limit(
        self, mock_query_pois, mock_create_isochrone, mock_geocode
    ):
        """Test that max_pois_per_category limit is enforced."""
        # Mock setup
        mock_geocode.return_value = GeocodingResult(
            input_address=AddressInput(address="Chapel Hill, NC"),
            success=True,
            latitude=35.9132,
            longitude=-79.0558,
            formatted_address="Chapel Hill, NC, USA",
            quality=AddressQuality.EXACT,
        )

        isochrone_polygon = Polygon([
            (-79.0658, 35.9032),
            (-79.0458, 35.9032),
            (-79.0458, 35.9232),
            (-79.0658, 35.9232),
            (-79.0658, 35.9032),
        ])
        mock_isochrone_gdf = gpd.GeoDataFrame(
            {"geometry": [isochrone_polygon]}, crs="EPSG:4326"
        )
        mock_create_isochrone.return_value = mock_isochrone_gdf

        # Create many POIs of the same category
        mock_pois = []
        for i in range(10):
            mock_pois.append({
                "type": "node",
                "id": i,
                "lat": 35.9140 + (i * 0.001),  # Different distances
                "lon": -79.0560,
                "tags": {
                    "name": f"Restaurant {i}",
                    "amenity": "restaurant",
                },
            })
        mock_query_pois.return_value = mock_pois

        # Test with limit
        config = NearbyPOIDiscoveryConfig(
            location=(35.9132, -79.0558),
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            max_pois_per_category=5,
            output_dir=self.temp_dir,
        )

        stage = NearbyPOIDiscoveryStage(config)
        result = stage.execute()

        assert result.is_ok()
        poi_result = result.unwrap()

        # Verify limit is enforced
        assert poi_result.total_poi_count == 5

        # Verify closest POIs are kept (they should be sorted by distance)
        all_pois = poi_result.get_all_pois()
        distances = [poi.straight_line_distance_m for poi in all_pois]
        assert distances == sorted(distances)  # Should be in ascending order

    def test_export_csv_functionality(self):
        """Test CSV export functionality."""
        # Create a simple result with POIs
        poi1 = DiscoveredPOI(
            id="poi_1",
            name="Test Coffee Shop",
            category="food_and_drink",
            subcategory="cafe",
            latitude=35.9140,
            longitude=-79.0560,
            straight_line_distance_m=500.0,
            osm_type="node",
            osm_id=123,
        )

        result = NearbyPOIResult(
            origin_location={"lat": 35.9132, "lon": -79.0558},
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=5.0,
            pois_by_category={"food_and_drink": [poi1]},
            total_poi_count=1,
            category_counts={"food_and_drink": 1},
        )

        stage = NearbyPOIDiscoveryStage(self.test_config)
        stage.results = result

        # Test CSV export
        csv_path = self.temp_dir / "test_export.csv"
        stage._export_csv(csv_path)

        # Verify CSV was created and has correct content
        assert csv_path.exists()
        df = pd.read_csv(csv_path)

        assert len(df) == 1
        assert df.iloc[0]["name"] == "Test Coffee Shop"
        assert df.iloc[0]["category"] == "food_and_drink"
        assert df.iloc[0]["distance_m"] == 500.0
        assert df.iloc[0]["distance_km"] == 0.5


class TestConvenienceFunctions:
    """Test convenience functions for POI discovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    @patch("socialmapper.pipeline.poi_discovery.execute_poi_discovery_pipeline")
    def test_discover_pois_near_address(self, mock_execute):
        """Test discover_pois_near_address convenience function."""
        mock_execute.return_value = Ok(
            NearbyPOIResult(
                origin_location={"lat": 35.9132, "lon": -79.0558},
                travel_time=15,
                travel_mode=TravelMode.DRIVE,
                isochrone_area_km2=5.0,
            )
        )

        result = discover_pois_near_address(
            address="Chapel Hill, NC",
            travel_time=20,
            travel_mode=TravelMode.BIKE,
            categories=["food_and_drink"],
            output_dir=self.temp_dir,
        )

        # Verify function was called with correct config
        assert result.is_ok()
        mock_execute.assert_called_once()

        # Check the config passed to execute_poi_discovery_pipeline
        call_args = mock_execute.call_args[0][0]
        assert call_args.location == "Chapel Hill, NC"
        assert call_args.travel_time == 20
        assert call_args.travel_mode == TravelMode.BIKE
        assert call_args.poi_categories == ["food_and_drink"]
        assert call_args.output_dir == self.temp_dir

    @patch("socialmapper.pipeline.poi_discovery.execute_poi_discovery_pipeline")
    def test_discover_pois_near_coordinates(self, mock_execute):
        """Test discover_pois_near_coordinates convenience function."""
        mock_execute.return_value = Ok(
            NearbyPOIResult(
                origin_location={"lat": 35.9132, "lon": -79.0558},
                travel_time=30,
                travel_mode=TravelMode.WALK,
                isochrone_area_km2=2.0,
            )
        )

        result = discover_pois_near_coordinates(
            latitude=35.9132,
            longitude=-79.0558,
            travel_time=30,
            travel_mode=TravelMode.WALK,
            categories=["shopping"],
            output_dir=self.temp_dir,
        )

        # Verify function was called with correct config
        assert result.is_ok()
        mock_execute.assert_called_once()

        # Check the config passed to execute_poi_discovery_pipeline
        call_args = mock_execute.call_args[0][0]
        assert call_args.location == (35.9132, -79.0558)
        assert call_args.travel_time == 30
        assert call_args.travel_mode == TravelMode.WALK
        assert call_args.poi_categories == ["shopping"]
        assert call_args.output_dir == self.temp_dir


class TestExecutePOIDiscoveryPipeline:
    """Test the main execute_poi_discovery_pipeline function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_invalid_configuration_error(self):
        """Test that invalid configuration raises proper error."""
        # Test that invalid travel time during config creation raises ValueError
        with pytest.raises(ValueError):
            NearbyPOIDiscoveryConfig(
                location="Test Location",
                travel_time=0,  # Invalid - below minimum
                output_dir=self.temp_dir,
            )

    @patch("socialmapper.pipeline.poi_discovery.NearbyPOIDiscoveryStage")
    def test_unexpected_error_handling(self, mock_stage_class):
        """Test handling of unexpected errors during pipeline execution."""
        # Mock stage to raise an unexpected exception
        mock_stage = MagicMock()
        mock_stage.execute.side_effect = RuntimeError("Unexpected error")
        mock_stage_class.return_value = mock_stage

        config = NearbyPOIDiscoveryConfig(
            location="Test Location",
            travel_time=15,
            output_dir=self.temp_dir,
        )

        result = execute_poi_discovery_pipeline(config)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.POI_DISCOVERY
        assert "Unexpected error" in error.message


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_empty_isochrone_handling(self):
        """Test handling of empty isochrone."""
        config = NearbyPOIDiscoveryConfig(
            location=(35.9132, -79.0558),
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            output_dir=self.temp_dir,
        )

        stage = NearbyPOIDiscoveryStage(config)

        # Test with empty isochrone
        empty_gdf = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:4326")
        result = stage._query_pois_in_isochrone(empty_gdf)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.POI_QUERY
        assert "Isochrone is empty" in error.message

    def test_poi_without_coordinates(self):
        """Test handling of POI data without coordinates."""
        config = NearbyPOIDiscoveryConfig(
            location=(35.9132, -79.0558),
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            output_dir=self.temp_dir,
        )

        stage = NearbyPOIDiscoveryStage(config)
        stage.results = NearbyPOIResult(
            origin_location={"lat": 35.9132, "lon": -79.0558},
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=5.0,
        )

        # POI without coordinates
        raw_pois = [
            {
                "type": "node",
                "id": 123,
                "tags": {"name": "Test POI"},
                # Missing lat/lon
            }
        ]

        result = stage._process_pois(raw_pois, (35.9132, -79.0558))

        # Should succeed but skip the invalid POI
        assert result.is_ok()
        assert stage.results.total_poi_count == 0

    def test_exclude_categories_filtering(self):
        """Test that excluded categories are properly filtered."""
        config = NearbyPOIDiscoveryConfig(
            location=(35.9132, -79.0558),
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            exclude_categories=["transportation"],
            output_dir=self.temp_dir,
        )

        stage = NearbyPOIDiscoveryStage(config)
        stage.results = NearbyPOIResult(
            origin_location={"lat": 35.9132, "lon": -79.0558},
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=5.0,
        )

        # Mix of POIs including excluded category
        raw_pois = [
            {
                "type": "node",
                "id": 1,
                "lat": 35.9140,
                "lon": -79.0560,
                "tags": {"name": "Coffee Shop", "amenity": "cafe"},
            },
            {
                "type": "node",
                "id": 2,
                "lat": 35.9150,
                "lon": -79.0570,
                "tags": {"name": "Gas Station", "amenity": "fuel"},
            },
        ]

        result = stage._process_pois(raw_pois, (35.9132, -79.0558))

        assert result.is_ok()
        # Should only have the coffee shop, not the gas station
        assert stage.results.total_poi_count == 1
        all_pois = stage.results.get_all_pois()
        assert "Coffee Shop" in all_pois[0].name


class TestIntegrationWithMockedAPIs:
    """Integration tests with mocked external APIs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    @patch("socialmapper.pipeline.poi_discovery.geocode_address")
    @patch("socialmapper.pipeline.poi_discovery.create_isochrone_from_poi")
    @patch("socialmapper.pipeline.poi_discovery.query_pois_in_polygon")
    def test_full_pipeline_integration(
        self, mock_query_pois, mock_create_isochrone, mock_geocode
    ):
        """Test full pipeline integration with realistic data."""
        # Mock geocoding
        mock_geocode.return_value = GeocodingResult(
            input_address=AddressInput(address="Carrboro, NC"),
            success=True,
            latitude=35.9132,
            longitude=-79.0558,
            formatted_address="Chapel Hill, NC 27514, USA",
            quality=AddressQuality.EXACT,
        )

        # Mock isochrone generation with realistic polygon
        isochrone_polygon = Polygon([
            (-79.0658, 35.9032),
            (-79.0458, 35.9032),
            (-79.0458, 35.9232),
            (-79.0658, 35.9232),
            (-79.0658, 35.9032),
        ])
        mock_isochrone_gdf = gpd.GeoDataFrame(
            {"geometry": [isochrone_polygon]}, crs="EPSG:4326"
        )
        mock_create_isochrone.return_value = mock_isochrone_gdf

        # Mock realistic POI data
        mock_pois = [
            {
                "type": "node",
                "id": 123456,
                "lat": 35.9140,
                "lon": -79.0560,
                "tags": {
                    "name": "Carrboro Coffee Roasters",
                    "amenity": "cafe",
                    "cuisine": "coffee_shop",
                    "addr:street": "West Main Street",
                    "addr:city": "Carrboro",
                    "addr:state": "NC",
                    "phone": "+1-919-542-5282",
                    "website": "https://carrbororoasters.com",
                    "opening_hours": "Mo-Su 06:30-19:00",
                },
            },
            {
                "type": "way",
                "id": 789012,
                "lat": 35.9150,
                "lon": -79.0570,
                "tags": {
                    "name": "Weaver Street Market",
                    "shop": "supermarket",
                    "organic": "yes",
                    "addr:street": "West Weaver Street",
                    "addr:city": "Carrboro",
                    "website": "https://weaverstreetmarket.coop",
                },
            },
            {
                "type": "node",
                "id": 345678,
                "lat": 35.9160,
                "lon": -79.0580,
                "tags": {
                    "name": "Local 506",
                    "amenity": "bar",
                    "addr:street": "West Franklin Street",
                    "addr:city": "Chapel Hill",
                },
            },
        ]
        mock_query_pois.return_value = mock_pois

        # Execute pipeline with comprehensive config
        config = NearbyPOIDiscoveryConfig(
            location="Carrboro, NC",
            travel_time=15,
            travel_mode=TravelMode.BIKE,
            poi_categories=["food_and_drink", "shopping", "entertainment"],
            include_poi_details=True,
            export_csv=True,
            export_geojson=True,
            create_map=False,  # Skip map for test
            output_dir=self.temp_dir,
            max_pois_per_category=10,
        )

        result = execute_poi_discovery_pipeline(config)

        # Comprehensive verification
        assert result.is_ok()
        poi_result = result.unwrap()

        # Basic result properties
        assert poi_result.success
        assert poi_result.total_poi_count == 3
        assert poi_result.origin_location["lat"] == 35.9132
        assert poi_result.origin_location["lon"] == -79.0558
        assert poi_result.travel_time == 15
        assert poi_result.travel_mode == TravelMode.BIKE
        assert poi_result.isochrone_area_km2 > 0

        # Category organization
        assert len(poi_result.pois_by_category) >= 2  # Should have multiple categories
        assert poi_result.total_poi_count == sum(poi_result.category_counts.values())

        # POI details
        all_pois = poi_result.get_all_pois()
        coffee_shop = next(p for p in all_pois if "Coffee" in p.name)
        assert coffee_shop.phone == "+1-919-542-5282"
        assert coffee_shop.website == "https://carrbororoasters.com"
        assert coffee_shop.opening_hours == "Mo-Su 06:30-19:00"
        assert "West Main Street" in coffee_shop.address

        # Distance calculations
        distances = [poi.straight_line_distance_m for poi in all_pois]
        assert all(d >= 0 for d in distances)

        # File exports
        csv_files = list(self.temp_dir.glob("*.csv"))
        geojson_files = list(self.temp_dir.glob("*.geojson"))
        assert len(csv_files) == 1
        assert len(geojson_files) == 2  # POIs + isochrone

        # Verify CSV content
        df = pd.read_csv(csv_files[0])
        assert len(df) == 3
        assert "Carrboro Coffee Roasters" in df["name"].values
        assert all(col in df.columns for col in ["name", "category", "distance_m", "latitude", "longitude"])

        # Metadata
        assert "query_categories" in poi_result.metadata
        assert "processing_time" not in poi_result.metadata or isinstance(poi_result.metadata["processing_time"], (int, float))

        # Summary statistics
        stats = poi_result.get_summary_stats()
        assert stats["total_pois"] == 3
        assert stats["categories"] >= 2
        assert stats["avg_distance_m"] > 0
        assert stats["min_distance_m"] >= 0
        assert stats["max_distance_m"] >= stats["min_distance_m"]
