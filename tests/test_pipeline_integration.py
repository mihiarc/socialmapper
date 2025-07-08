"""Integration tests for pipeline components."""

import pytest
from unittest.mock import Mock, patch
from socialmapper.pipeline import PipelineOrchestrator
from socialmapper.pipeline.environment import PipelineEnvironment
from socialmapper.pipeline.validation import PipelineValidator
from socialmapper.pipeline.helpers import calculate_total_area, format_demographic_summary


class TestPipelineEnvironment:
    """Test PipelineEnvironment class."""
    
    def test_pipeline_environment_creation(self):
        """Test creating pipeline environment."""
        config = {
            "location": "San Francisco, CA",
            "poi_type": "amenity",
            "poi_value": "library"
        }
        
        env = PipelineEnvironment(config)
        assert env.config == config
        assert env.start_time is not None
        assert env.errors == []
        assert env.warnings == []
        
    def test_add_error(self):
        """Test adding error to environment."""
        env = PipelineEnvironment({})
        env.add_error("Test error")
        
        assert len(env.errors) == 1
        assert env.errors[0] == "Test error"
        
    def test_add_warning(self):
        """Test adding warning to environment."""
        env = PipelineEnvironment({})
        env.add_warning("Test warning")
        
        assert len(env.warnings) == 1
        assert env.warnings[0] == "Test warning"
        
    def test_has_errors(self):
        """Test checking for errors."""
        env = PipelineEnvironment({})
        assert env.has_errors() is False
        
        env.add_error("Error")
        assert env.has_errors() is True
        
    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        env = PipelineEnvironment({})
        elapsed = env.get_elapsed_time()
        
        assert elapsed >= 0
        assert isinstance(elapsed, float)


class TestPipelineValidator:
    """Test PipelineValidator class."""
    
    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        config = {
            "location": "San Francisco, CA",
            "poi_type": "amenity", 
            "poi_value": "library",
            "travel_time_minutes": 15,
            "travel_mode": "walk"
        }
        
        validator = PipelineValidator()
        result = validator.validate_config(config)
        
        assert result is True
        
    def test_validate_config_missing_location(self):
        """Test validation fails with missing location."""
        config = {
            "poi_type": "amenity",
            "poi_value": "library"
        }
        
        validator = PipelineValidator()
        result = validator.validate_config(config)
        
        assert result is False
        
    def test_validate_travel_time_valid(self):
        """Test validating valid travel time."""
        validator = PipelineValidator()
        
        assert validator.validate_travel_time(15) is True
        assert validator.validate_travel_time(1) is True
        assert validator.validate_travel_time(120) is True
        
    def test_validate_travel_time_invalid(self):
        """Test validating invalid travel time."""
        validator = PipelineValidator()
        
        assert validator.validate_travel_time(0) is False
        assert validator.validate_travel_time(121) is False
        assert validator.validate_travel_time(-5) is False


class TestPipelineHelpers:
    """Test pipeline helper functions."""
    
    def test_calculate_total_area(self):
        """Test calculating total area."""
        # Mock GeoDataFrame with area attribute
        mock_gdf = Mock()
        mock_gdf.area.sum.return_value = 1000000.0  # Square meters
        
        area_sq_km = calculate_total_area(mock_gdf)
        assert area_sq_km == 1.0  # 1,000,000 sq m = 1 sq km
        
    def test_format_demographic_summary(self):
        """Test formatting demographic summary."""
        demographics = {
            "total_population": 50000,
            "median_age": 35.5,
            "median_income": 75000
        }
        
        summary = format_demographic_summary(demographics)
        
        assert isinstance(summary, str)
        assert "50,000" in summary  # Formatted population
        assert "35.5" in summary    # Age
        assert "$75,000" in summary # Formatted income


class TestPipelineOrchestrator:
    """Test PipelineOrchestrator class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return {
            "location": "San Francisco, CA",
            "poi_type": "amenity",
            "poi_value": "library",
            "travel_time_minutes": 15,
            "travel_mode": "walk",
            "output_dir": "/tmp/test"
        }
    
    def test_orchestrator_initialization(self, mock_config):
        """Test orchestrator initialization."""
        orchestrator = PipelineOrchestrator(mock_config)
        
        assert orchestrator.config == mock_config
        assert orchestrator.env is not None
        assert isinstance(orchestrator.env, PipelineEnvironment)
        
    @patch('socialmapper.pipeline.orchestrator.ExtractionStep')
    @patch('socialmapper.pipeline.orchestrator.TransformationStep')
    @patch('socialmapper.pipeline.orchestrator.LoadStep')
    def test_run_pipeline_success(self, mock_load, mock_transform, mock_extract, mock_config):
        """Test successful pipeline run."""
        # Mock step instances
        mock_extract_instance = Mock()
        mock_extract_instance.run.return_value = {"pois": []}
        mock_extract.return_value = mock_extract_instance
        
        mock_transform_instance = Mock()
        mock_transform_instance.run.return_value = {"isochrones": []}
        mock_transform.return_value = mock_transform_instance
        
        mock_load_instance = Mock()
        mock_load_instance.run.return_value = {"files": []}
        mock_load.return_value = mock_load_instance
        
        orchestrator = PipelineOrchestrator(mock_config)
        result = orchestrator.run()
        
        assert result is not None
        assert "pipeline_successful" in result
        assert result["pipeline_successful"] is True
        
    def test_validate_before_run(self, mock_config):
        """Test validation before running pipeline."""
        # Test with invalid config
        invalid_config = {"poi_type": "amenity"}  # Missing location
        orchestrator = PipelineOrchestrator(invalid_config)
        
        with patch.object(orchestrator, '_validate') as mock_validate:
            mock_validate.return_value = False
            result = orchestrator.run()
            
            assert result["pipeline_successful"] is False
            assert len(result["errors"]) > 0