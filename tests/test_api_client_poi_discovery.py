"""Integration tests for SocialMapperClient POI discovery functionality.

This module tests the POI discovery extensions to the SocialMapperClient,
ensuring proper integration with the POI discovery pipeline stage.
"""

from unittest.mock import Mock, patch

import pytest

from socialmapper.api.client import ClientConfig, SocialMapperClient
from socialmapper.api.result_types import (
    DiscoveredPOI,
    Err,
    Error,
    ErrorType,
    NearbyPOIDiscoveryConfig,
    NearbyPOIResult,
    Ok,
)
from socialmapper.isochrone import TravelMode


class TestSocialMapperClientPOIDiscovery:
    """Test suite for POI discovery functionality in SocialMapperClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ClientConfig(rate_limit=10, timeout=30)
        self.client = SocialMapperClient(self.config)

        # Sample POI discovery result for mocking
        self.sample_poi = DiscoveredPOI(
            id="node_123456",
            name="Test Restaurant",
            category="food_and_drink",
            subcategory="restaurant",
            latitude=35.9132,
            longitude=-79.0558,
            straight_line_distance_m=750.5,
            osm_type="node",
            osm_id=123456,
            tags={"cuisine": "italian", "name": "Test Restaurant"},
        )

        self.sample_result = NearbyPOIResult(
            origin_location={"lat": 35.9132, "lon": -79.0558},
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=12.5,
            pois_by_category={"food_and_drink": [self.sample_poi]},
            total_poi_count=1,
            category_counts={"food_and_drink": 1},
        )

    def test_discover_nearby_pois_basic_usage(self):
        """Test basic POI discovery with default parameters."""
        with patch.object(self.client, 'run_analysis') as mock_run:
            mock_run.return_value = Ok(self.sample_result)

            with self.client:
                result = self.client.discover_nearby_pois(
                    location="Chapel Hill, NC"
                )

            assert result.is_ok()
            poi_result = result.unwrap()
            assert isinstance(poi_result, NearbyPOIResult)
            assert poi_result.total_poi_count == 1
            assert "food_and_drink" in poi_result.pois_by_category

            # Verify run_analysis was called with correct config
            mock_run.assert_called_once()
            config = mock_run.call_args[0][0]
            assert config["poi_discovery_enabled"] is True
            assert config["poi_discovery_location"] == "Chapel Hill, NC"
            assert config["poi_discovery_travel_time"] == 15

    def test_discover_nearby_pois_with_coordinates(self):
        """Test POI discovery using coordinate tuple."""
        with patch.object(self.client, 'run_analysis') as mock_run:
            mock_run.return_value = Ok(self.sample_result)

            with self.client:
                result = self.client.discover_nearby_pois(
                    location=(35.9132, -79.0558),
                    travel_time=20,
                    travel_mode="walk"
                )

            assert result.is_ok()

            # Verify configuration
            config = mock_run.call_args[0][0]
            assert config["poi_discovery_location"] == (35.9132, -79.0558)
            assert config["poi_discovery_travel_time"] == 20
            assert config["poi_discovery_travel_mode"] == TravelMode.WALK

    def test_discover_nearby_pois_with_categories(self):
        """Test POI discovery with specific categories."""
        with patch.object(self.client, 'run_analysis') as mock_run:
            mock_run.return_value = Ok(self.sample_result)

            with self.client:
                result = self.client.discover_nearby_pois(
                    location="Durham, NC",
                    poi_categories=["food_and_drink", "healthcare"],
                    exclude_categories=["utilities"],
                    max_pois_per_category=25
                )

            assert result.is_ok()

            # Verify builder methods were called
            config = mock_run.call_args[0][0]
            assert config["poi_categories"] == ["food_and_drink", "healthcare"]
            assert config["exclude_poi_categories"] == ["utilities"]
            assert config["max_pois_per_category"] == 25

    def test_discover_nearby_pois_invalid_travel_mode(self):
        """Test validation of invalid travel mode."""
        with self.client:
            result = self.client.discover_nearby_pois(
                location="Raleigh, NC",
                travel_mode="invalid_mode"
            )

        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.VALIDATION
        assert "Invalid travel mode" in error.message
        assert "invalid_mode" in error.message

    def test_discover_nearby_pois_export_options(self):
        """Test POI discovery with different export options."""
        with patch.object(self.client, 'run_analysis') as mock_run:
            mock_run.return_value = Ok(self.sample_result)

            with self.client:
                result = self.client.discover_nearby_pois(
                    location="Greensboro, NC",
                    export_csv=False,
                    create_map=False,
                    output_dir="/tmp/test_output"
                )

            assert result.is_ok()

            # Verify builder configuration
            config = mock_run.call_args[0][0]
            assert config["export_csv"] is False
            # Note: create_map option is handled differently in POI discovery config
            assert "/tmp/test_output" in str(config["output_dir"])

    def test_discover_nearby_pois_session_not_active(self):
        """Test error when client session is not active."""
        result = self.client.discover_nearby_pois(
            location="Charlotte, NC"
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.VALIDATION
        assert "context manager" in error.message

    def test_run_analysis_poi_discovery_enabled(self):
        """Test run_analysis with POI discovery configuration."""
        with patch('socialmapper.pipeline.poi_discovery.execute_poi_discovery_pipeline') as mock_execute:
            mock_execute.return_value = Ok(self.sample_result)

            config = {
                "poi_discovery_enabled": True,
                "poi_discovery_config": NearbyPOIDiscoveryConfig(
                    location="Chapel Hill, NC",
                    travel_time=15,
                    travel_mode=TravelMode.DRIVE,
                )
            }

            with self.client:
                result = self.client.run_analysis(config)

            assert result.is_ok()
            poi_result = result.unwrap()
            assert isinstance(poi_result, NearbyPOIResult)

            # Verify pipeline was called
            mock_execute.assert_called_once()

    def test_run_analysis_poi_discovery_missing_config(self):
        """Test error when POI discovery is enabled but config is missing."""
        config = {
            "poi_discovery_enabled": True,
            # Missing poi_discovery_config
        }

        with self.client:
            result = self.client.run_analysis(config)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.type == ErrorType.CONFIGURATION
        assert "POI discovery configuration missing" in error.message

    def test_run_analysis_poi_discovery_pipeline_error(self):
        """Test handling of POI discovery pipeline errors."""
        with patch('socialmapper.pipeline.poi_discovery.execute_poi_discovery_pipeline') as mock_execute:
            pipeline_error = Error(
                type=ErrorType.POI_DISCOVERY,
                message="Pipeline failed",
            )
            mock_execute.return_value = Err(pipeline_error)

            config = {
                "poi_discovery_enabled": True,
                "poi_discovery_config": NearbyPOIDiscoveryConfig(
                    location="Test Location",
                    travel_time=15,
                    travel_mode=TravelMode.DRIVE,
                )
            }

            with self.client:
                result = self.client.run_analysis(config)

            assert result.is_err()
            error = result.unwrap_err()
            assert error.type == ErrorType.POI_DISCOVERY

    def test_run_analysis_standard_vs_poi_discovery(self):
        """Test that standard analysis still works when POI discovery is not enabled."""
        from socialmapper.pipeline import PipelineOrchestrator

        with patch.object(PipelineOrchestrator, 'run') as mock_run:
            mock_run.return_value = {
                "pois": [],
                "census_data": [],
                "isochrones": []
            }

            config = {
                "poi_discovery_enabled": False,
                "geocode_area": "Chapel Hill, NC",
                "poi_type": "amenity",
                "poi_name": "library",
            }

            with self.client:
                result = self.client.run_analysis(config)

            # Should use standard pipeline, not POI discovery
            assert result.is_ok()
            mock_run.assert_called_once()

    def test_cache_key_generation_poi_discovery(self):
        """Test cache key generation for POI discovery configurations."""
        poi_config = NearbyPOIDiscoveryConfig(
            location="Chapel Hill, NC",
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            poi_categories=["food_and_drink", "healthcare"],
            exclude_categories=["utilities"],
        )

        config = {
            "poi_discovery_enabled": True,
            "poi_discovery_config": poi_config,
        }

        cache_key = self.client._generate_cache_key(config)

        assert "poi_discovery" in cache_key
        assert "Chapel Hill, NC" in cache_key
        assert "15" in cache_key
        assert "drive" in cache_key
        assert cache_key.count(":") >= 4  # Multiple parts separated by colons

    def test_cache_key_generation_standard_analysis(self):
        """Test cache key generation for standard analysis."""
        config = {
            "poi_discovery_enabled": False,
            "geocode_area": "Durham, NC",
            "poi_type": "amenity",
            "poi_name": "hospital",
            "travel_time": 20,
        }

        cache_key = self.client._generate_cache_key(config)

        assert "Durham, NC" in cache_key
        assert "amenity" in cache_key
        assert "hospital" in cache_key
        assert "20" in cache_key
        assert "poi_discovery" not in cache_key

    def test_error_classification_poi_discovery(self):
        """Test error classification for POI discovery specific errors."""
        # POI discovery error
        poi_error = Exception("POI discovery failed due to timeout")
        error_type = self.client._classify_error(poi_error)
        assert error_type == ErrorType.POI_DISCOVERY

        # Isochrone error
        iso_error = Exception("Isochrone generation failed")
        error_type = self.client._classify_error(iso_error)
        assert error_type == ErrorType.ISOCHRONE_GENERATION

        # POI query error
        query_error = Exception("POI query returned no results")
        error_type = self.client._classify_error(query_error)
        assert error_type == ErrorType.POI_QUERY

        # Geocoding error
        geocode_error = Exception("Geocoding failed for address")
        error_type = self.client._classify_error(geocode_error)
        assert error_type == ErrorType.LOCATION_GEOCODING

    def test_progress_callback_poi_discovery(self):
        """Test progress callback functionality during POI discovery."""
        progress_calls = []

        def progress_callback(progress):
            progress_calls.append(progress)

        with patch('socialmapper.pipeline.poi_discovery.execute_poi_discovery_pipeline') as mock_execute:
            mock_execute.return_value = Ok(self.sample_result)

            config = {
                "poi_discovery_enabled": True,
                "poi_discovery_config": NearbyPOIDiscoveryConfig(
                    location="Test Location",
                    travel_time=15,
                    travel_mode=TravelMode.DRIVE,
                )
            }

            with self.client:
                result = self.client.run_analysis(config, on_progress=progress_callback)

            assert result.is_ok()
            assert len(progress_calls) >= 3  # Should have start, middle, and end calls
            assert 10.0 in progress_calls  # Starting
            assert 90.0 in progress_calls  # Nearly complete
            assert 100.0 in progress_calls  # Complete

    def test_caching_poi_discovery_results(self):
        """Test caching functionality for POI discovery results."""
        cache_strategy = Mock()
        cache_strategy.get.return_value = None  # No cached result initially

        client_config = ClientConfig(cache_strategy=cache_strategy)
        client = SocialMapperClient(client_config)

        with patch('socialmapper.pipeline.poi_discovery.execute_poi_discovery_pipeline') as mock_execute:
            mock_execute.return_value = Ok(self.sample_result)

            config = {
                "poi_discovery_enabled": True,
                "poi_discovery_config": NearbyPOIDiscoveryConfig(
                    location="Test Location",
                    travel_time=15,
                    travel_mode=TravelMode.DRIVE,
                )
            }

            with client:
                result = client.run_analysis(config)

            assert result.is_ok()

            # Verify cache.set was called
            cache_strategy.set.assert_called_once()
            args, kwargs = cache_strategy.set.call_args
            assert len(args) >= 2  # key and value
            assert isinstance(args[1], NearbyPOIResult)
            assert kwargs.get('ttl', 3600) == 3600

    def test_builder_integration_complete_flow(self):
        """Test complete integration flow using the builder pattern."""
        with patch('socialmapper.pipeline.poi_discovery.execute_poi_discovery_pipeline') as mock_execute:
            mock_execute.return_value = Ok(self.sample_result)

            with self.client:
                # Use builder pattern through client
                analysis = (
                    self.client.create_analysis()
                    .with_nearby_poi_discovery(
                        location="Research Triangle Park, NC",
                        travel_time=25,
                        travel_mode=TravelMode.BIKE,
                        poi_categories=["food_and_drink", "services"]
                    )
                    .exclude_poi_categories("utilities")
                    .limit_pois_per_category(50)
                    .with_output_directory("/tmp/test")
                    .build()
                )

                result = self.client.run_analysis(analysis)

            assert result.is_ok()
            poi_result = result.unwrap()
            assert isinstance(poi_result, NearbyPOIResult)

            # Verify pipeline was called with correct config
            mock_execute.assert_called_once()
            pipeline_config = mock_execute.call_args[0][0]
            assert pipeline_config.location == "Research Triangle Park, NC"
            assert pipeline_config.travel_time == 25
            assert pipeline_config.travel_mode == TravelMode.BIKE
            assert pipeline_config.poi_categories == ["food_and_drink", "services"]
            assert pipeline_config.exclude_categories == ["utilities"]
            assert pipeline_config.max_pois_per_category == 50


class TestPOIDiscoveryResultHandling:
    """Test suite for handling POI discovery results."""

    def test_poi_result_properties_and_methods(self):
        """Test NearbyPOIResult properties and methods."""
        poi1 = DiscoveredPOI(
            id="poi_1", name="Close POI", category="food_and_drink", subcategory="restaurant",
            latitude=35.9132, longitude=-79.0558, straight_line_distance_m=500.0,
            osm_type="node", osm_id=1
        )
        poi2 = DiscoveredPOI(
            id="poi_2", name="Far POI", category="healthcare", subcategory="hospital",
            latitude=35.9140, longitude=-79.0560, straight_line_distance_m=1500.0,
            osm_type="way", osm_id=2
        )

        result = NearbyPOIResult(
            origin_location={"lat": 35.9132, "lon": -79.0558},
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=8.5,
            pois_by_category={
                "food_and_drink": [poi1],
                "healthcare": [poi2]
            },
            total_poi_count=2,
            category_counts={"food_and_drink": 1, "healthcare": 1}
        )

        # Test success property
        assert result.success is True

        # Test get_all_pois
        all_pois = result.get_all_pois()
        assert len(all_pois) == 2
        assert poi1 in all_pois
        assert poi2 in all_pois

        # Test get_pois_by_distance
        sorted_pois = result.get_pois_by_distance()
        assert sorted_pois[0] == poi1  # Closer POI first
        assert sorted_pois[1] == poi2

        # Test distance filtering
        close_pois = result.get_pois_by_distance(max_distance_m=1000.0)
        assert len(close_pois) == 1
        assert close_pois[0] == poi1

        # Test summary stats
        stats = result.get_summary_stats()
        assert stats["total_pois"] == 2
        assert stats["categories"] == 2
        assert stats["min_distance_m"] == 500.0
        assert stats["max_distance_m"] == 1500.0
        assert stats["avg_distance_m"] == 1000.0
        assert stats["isochrone_area_km2"] == 8.5

    def test_empty_poi_result(self):
        """Test handling of empty POI discovery results."""
        result = NearbyPOIResult(
            origin_location={"lat": 35.9132, "lon": -79.0558},
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            isochrone_area_km2=5.0,
            total_poi_count=0
        )

        assert result.success is False
        assert len(result.get_all_pois()) == 0
        assert len(result.get_pois_by_distance()) == 0

        stats = result.get_summary_stats()
        assert stats["total_pois"] == 0
        assert stats["categories"] == 0
        assert stats["avg_distance_m"] == 0
        assert stats["min_distance_m"] == 0
        assert stats["max_distance_m"] == 0


@pytest.mark.integration
class TestSocialMapperClientPOIDiscoveryIntegration:
    """Integration tests that require actual pipeline components."""

    def test_discover_nearby_pois_with_mock_pipeline(self):
        """Integration test with mocked pipeline components."""
        # This would be a more comprehensive test that mocks the actual
        # pipeline components (geocoding, isochrone generation, POI queries)
        # to test the full integration without external API calls

    def test_error_propagation_from_pipeline(self):
        """Test that errors from pipeline components are properly propagated."""
        # Test various error scenarios from different pipeline stages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
