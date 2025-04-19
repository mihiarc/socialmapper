import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    def __init__(self, config_path: str = "cfg/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_paths()
        self._create_directories()

    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config

    def _validate_paths(self):
        """Validate that all required paths are defined in config."""
        required_paths = [
            'paths.data.root',
            'paths.data.input.points_of_interest',
            'paths.data.input.county_data',
            'paths.data.input.zipcode_data',
            'paths.data.output.analysis',
            'paths.data.output.maps',
            'paths.data.output.isochrones',
            'paths.data.output.temp',
            'paths.cache.root',
            'paths.cache.api_responses',
            'paths.cache.processed_data'
        ]
        
        for path in required_paths:
            try:
                self._get_nested_dict_value(self.config, path.split('.'))
            except KeyError:
                raise KeyError(f"Required path '{path}' not found in config")

    def _create_directories(self):
        """Create all output and cache directories if they don't exist."""
        dirs_to_create = [
            self.get_path('data.root'),
            self.get_path('data.input.points_of_interest'),
            self.get_path('data.input.county_data'),
            self.get_path('data.input.zipcode_data'),
            self.get_path('data.output.analysis'),
            self.get_path('data.output.maps'),
            self.get_path('data.output.isochrones'),
            self.get_path('data.output.temp'),
            self.get_path('cache.root'),
            self.get_path('cache.api_responses'),
            self.get_path('cache.processed_data')
        ]
        
        for directory in dirs_to_create:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _get_nested_dict_value(self, d: Dict[str, Any], keys: list) -> Any:
        """Get a value from nested dictionary using a list of keys."""
        for key in keys:
            d = d[key]
        return d

    def get_path(self, path_key: str) -> str:
        """
        Get a path from the config using dot notation.
        Example: config.get_path('data.output.maps')
        """
        try:
            path = self._get_nested_dict_value(self.config['paths'], path_key.split('.'))
            # Handle variable interpolation
            if isinstance(path, str) and '${' in path:
                # Replace ${paths.xxx.yyy} with actual path
                while '${' in path:
                    start = path.find('${')
                    end = path.find('}', start)
                    if start != -1 and end != -1:
                        var_path = path[start+2:end]
                        replacement = self.get_path(var_path.replace('paths.', ''))
                        path = path[:start] + replacement + path[end+1:]
            return path
        except KeyError:
            raise KeyError(f"Path '{path_key}' not found in config")

    def get_study_area(self) -> Dict[str, Any]:
        """Get study area configuration."""
        return self.config['study_area']

    def get_poi(self) -> Dict[str, Any]:
        """Get point of interest configuration."""
        return self.config['point_of_interest']

    def get_isochrone_settings(self) -> Dict[str, Any]:
        """Get isochrone settings."""
        return self.config['isochrone_settings'] 