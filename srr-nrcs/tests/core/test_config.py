"""
Tests for the Config class.
"""
import pytest
import yaml
from pathlib import Path
from scripts.core.config import Config


class TestConfig:
    """Tests for the Config class."""

    def test_config_initialization(self, test_config_file):
        """Test that the Config class initializes properly."""
        config = Config(config_path=str(test_config_file))
        assert isinstance(config, Config)
        assert config.config_path == str(test_config_file)
        assert isinstance(config.config, dict)

    def test_get_path(self, test_config):
        """Test that the get_path method works correctly."""
        # Test basic path
        data_root = test_config.get_path('data.root')
        assert isinstance(data_root, str)
        assert Path(data_root).exists()

        # Test nested path
        poi_path = test_config.get_path('data.input.points_of_interest')
        assert isinstance(poi_path, str)
        assert Path(poi_path).exists()

    def test_get_study_area(self, test_config):
        """Test that the get_study_area method works correctly."""
        study_area = test_config.get_study_area()
        assert isinstance(study_area, dict)
        assert 'states' in study_area
        assert isinstance(study_area['states'], list)
        assert len(study_area['states']) > 0
        assert 'name' in study_area['states'][0]
        assert 'counties' in study_area
        assert isinstance(study_area['counties'], dict)

    def test_get_poi(self, test_config):
        """Test that the get_poi method works correctly."""
        poi = test_config.get_poi()
        assert isinstance(poi, dict)
        assert 'type' in poi
        assert 'radius_miles' in poi

    def test_get_isochrone_settings(self, test_config):
        """Test that the get_isochrone_settings method works correctly."""
        settings = test_config.get_isochrone_settings()
        assert isinstance(settings, dict)
        assert 'travel_time_minutes' in settings
        assert 'travel_mode' in settings
        assert isinstance(settings['travel_time_minutes'], list)

    def test_validate_paths_missing_path(self, temp_dir):
        """Test validation of paths when a required path is missing."""
        incomplete_config_path = temp_dir / 'incomplete_config.yaml'
        
        # Create an incomplete config
        incomplete_config = {
            'paths': {
                'data': {
                    'root': str(temp_dir / 'data'),
                    # Missing some required paths
                }
            }
        }
        
        with open(incomplete_config_path, 'w') as f:
            yaml.dump(incomplete_config, f)
        
        with pytest.raises(KeyError, match="Required path .* not found in config"):
            Config(config_path=str(incomplete_config_path))

    def test_directory_creation(self, test_config, temp_dir):
        """Test that directories are created correctly."""
        # Check that all required directories exist
        paths = [
            'data.root',
            'data.input.points_of_interest',
            'data.input.county_data',
            'data.input.zipcode_data',
            'data.output.analysis',
            'data.output.maps',
            'data.output.isochrones',
            'data.output.temp',
            'cache.root',
            'cache.api_responses',
            'cache.processed_data'
        ]
        
        for path_key in paths:
            path = test_config.get_path(path_key)
            assert Path(path).exists(), f"Path {path_key} -> {path} does not exist"
            assert Path(path).is_dir(), f"Path {path_key} -> {path} is not a directory" 