"""End-to-end integration tests for the SocialMapper pipeline."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pandas as pd
import geopandas as gpd

from socialmapper.pipeline.orchestrator import PipelineOrchestrator
from socialmapper.api.client import SocialMapperClient
from socialmapper.api.builder import SocialMapperBuilder


@pytest.mark.integration
class TestPipelineEndToEnd:
    """End-to-end integration tests for the complete pipeline."""

    @pytest.fixture
    def mock_external_apis(self):
        """Mock all external API calls for integration testing."""
        with patch("socialmapper.census.infrastructure.api_client.CensusAPIClient") as mock_census, \
             patch("socialmapper.geocoding.providers.geocode") as mock_geocoding, \
             patch("overpy.Overpass") as mock_overpass, \
             patch("osmnx.graph_from_point") as mock_osmnx:
            
            # Configure census API mock
            mock_census_instance = Mock()
            mock_census_instance.get_block_group_data.return_value = [
                ["NAME", "B01003_001E", "B19013_001E", "state", "county", "tract", "block group"],
                ["Block Group 1", "1250", "75000", "53", "033", "000100", "1"]
            ]
            mock_census.return_value = mock_census_instance
            
            # Configure geocoding mock
            mock_geocoding.return_value = (47.6062, -122.3321)
            
            # Configure Overpass API mock
            mock_overpass_instance = Mock()
            mock_overpass_instance.query.return_value.elements = [
                Mock(
                    id=123456,
                    lat=47.6062,
                    lon=-122.3321,
                    tags={"amenity": "library", "name": "Central Library"}
                )
            ]
            mock_overpass.return_value = mock_overpass_instance
            
            # Configure OSMnx mock
            mock_graph = Mock()
            mock_graph.nodes = {1: {"x": -122.3321, "y": 47.6062}}
            mock_osmnx.return_value = mock_graph
            
            yield {
                "census": mock_census_instance,
                "geocoding": mock_geocoding,
                "overpass": mock_overpass_instance,
                "osmnx": mock_osmnx
            }

    def test_complete_poi_analysis_pipeline(self, mock_external_apis, temp_dir):
        """Test complete pipeline from POI query to final output."""
        # Configure pipeline
        config = {
            "poi_query": "library",
            "travel_mode": "walk",
            "travel_time": 15,
            "output_dir": str(temp_dir),
            "geographic_level": "block_group"
        }
        
        orchestrator = PipelineOrchestrator(config)
        
        # Execute pipeline
        result = orchestrator.execute()
        
        # Verify pipeline completed successfully
        assert result["status"] == "completed"
        assert "data" in result
        assert "output_files" in result
        
        # Verify output files were created
        csv_output = temp_dir / "analysis_results.csv"
        assert csv_output.exists()
        
        # Verify data structure
        output_data = pd.read_csv(csv_output)
        assert not output_data.empty
        assert "poi_name" in output_data.columns
        assert "travel_time" in output_data.columns
        assert "total_population" in output_data.columns

    def test_address_geocoding_pipeline(self, mock_external_apis, temp_dir):
        """Test pipeline with address geocoding."""
        config = {
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
            "poi_query": "restaurant",
            "travel_mode": "drive",
            "travel_time": 10,
            "output_dir": str(temp_dir)
        }
        
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.execute()
        
        assert result["status"] == "completed"
        
        # Verify geocoding was called
        mock_external_apis["geocoding"].assert_called_once()

    def test_custom_coordinates_pipeline(self, mock_external_apis, temp_dir, sample_coordinates):
        """Test pipeline with custom coordinates."""
        config = {
            "latitude": sample_coordinates["latitude"],
            "longitude": sample_coordinates["longitude"],
            "poi_query": "school",
            "travel_mode": "bike",
            "travel_time": 20,
            "output_dir": str(temp_dir)
        }
        
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.execute()
        
        assert result["status"] == "completed"
        assert result["input_coordinates"]["latitude"] == sample_coordinates["latitude"]
        assert result["input_coordinates"]["longitude"] == sample_coordinates["longitude"]

    @pytest.mark.slow
    def test_large_dataset_processing(self, mock_external_apis, temp_dir):
        """Test pipeline with large dataset (performance test)."""
        # Configure mock to return larger dataset
        large_census_data = []
        for i in range(100):
            large_census_data.append([
                f"Block Group {i}",
                str(1000 + i * 10),
                str(50000 + i * 1000),
                "53", "033", f"{i:06d}", "1"
            ])
        
        mock_external_apis["census"].get_block_group_data.return_value = large_census_data
        
        config = {
            "poi_query": "library",
            "travel_mode": "walk",
            "travel_time": 15,
            "output_dir": str(temp_dir),
            "batch_size": 50  # Test batch processing
        }
        
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.execute()
        
        assert result["status"] == "completed"
        
        # Verify large dataset was processed
        output_data = pd.read_csv(temp_dir / "analysis_results.csv")
        assert len(output_data) > 0  # Should have processed some data

    def test_api_client_integration(self, mock_external_apis):
        """Test API client integration with mocked services."""
        config = {
            "census_api_key": "test_key",
            "cache_enabled": False
        }
        
        with SocialMapperClient(config=config) as client:
            result = client.poi_query("library")
            
            assert result.is_ok()
            data = result.unwrap()
            assert "elements" in data or "pois" in data

    def test_builder_pattern_integration(self, mock_external_apis, temp_dir):
        """Test builder pattern integration."""
        result = (SocialMapperBuilder()
                 .poi_query("library")
                 .set_travel_mode("walk")
                 .set_travel_time(15)
                 .set_output_dir(str(temp_dir))
                 .build()
                 .run())
        
        assert result.is_ok()
        analysis_data = result.unwrap()
        assert "pois" in analysis_data or "data" in analysis_data

    def test_error_recovery_integration(self, temp_dir):
        """Test error recovery in integration scenarios."""
        # Configure pipeline with invalid API key to trigger error
        config = {
            "poi_query": "library",
            "census_api_key": "",  # Invalid key
            "output_dir": str(temp_dir)
        }
        
        orchestrator = PipelineOrchestrator(config)
        
        with pytest.raises(ValueError, match="Census API key"):
            orchestrator.execute()

    def test_pipeline_with_isochrone_export(self, mock_external_apis, temp_dir):
        """Test pipeline with isochrone export enabled."""
        config = {
            "poi_query": "library",
            "travel_mode": "walk",
            "travel_time": 15,
            "output_dir": str(temp_dir),
            "enable_isochrone_export": True
        }
        
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.execute()
        
        assert result["status"] == "completed"
        
        # Verify isochrone files were created
        isochrone_file = temp_dir / "isochrones.geoparquet"
        if isochrone_file.exists():
            isochrone_data = gpd.read_parquet(isochrone_file)
            assert not isochrone_data.empty
            assert "geometry" in isochrone_data.columns

    @pytest.mark.external
    def test_real_api_integration(self, sample_coordinates):
        """Test with real API calls (requires API keys and network)."""
        pytest.importorskip("CENSUS_API_KEY")  # Skip if no real API key
        
        # This test would use real API calls
        config = {
            "latitude": sample_coordinates["latitude"],
            "longitude": sample_coordinates["longitude"],
            "poi_query": "library",
            "travel_mode": "walk",
            "travel_time": 10
        }
        
        # Only run if environment is configured for external tests
        if "ENABLE_EXTERNAL_TESTS" in os.environ:
            orchestrator = PipelineOrchestrator(config)
            result = orchestrator.execute()
            assert result["status"] == "completed"
        else:
            pytest.skip("External API tests not enabled")

    def test_concurrent_pipeline_execution(self, mock_external_apis, temp_dir):
        """Test concurrent execution of multiple pipelines."""
        import concurrent.futures
        
        configs = [
            {
                "poi_query": "library",
                "travel_mode": "walk",
                "travel_time": 15,
                "output_dir": str(temp_dir / f"run_{i}")
            }
            for i in range(3)
        ]
        
        def run_pipeline(config):
            orchestrator = PipelineOrchestrator(config)
            return orchestrator.execute()
        
        # Create output directories
        for config in configs:
            Path(config["output_dir"]).mkdir(exist_ok=True)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_pipeline, config) for config in configs]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all pipelines completed successfully
        assert all(result["status"] == "completed" for result in results)

    @pytest.mark.benchmark
    def test_pipeline_performance(self, mock_external_apis, temp_dir, benchmark):
        """Benchmark pipeline performance."""
        config = {
            "poi_query": "library",
            "travel_mode": "walk", 
            "travel_time": 15,
            "output_dir": str(temp_dir)
        }
        
        def run_pipeline():
            orchestrator = PipelineOrchestrator(config)
            return orchestrator.execute()
        
        result = benchmark(run_pipeline)
        assert result["status"] == "completed"