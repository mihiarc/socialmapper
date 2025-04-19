"""
Fixtures for pytest.
"""
import os
import yaml
import pytest
import tempfile
from pathlib import Path
from scripts.core.config import Config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config_file(temp_dir):
    """Create a test configuration file."""
    config_yaml = {
        'paths': {
            'data': {
                'root': str(temp_dir / 'data'),
                'input': {
                    'points_of_interest': str(temp_dir / 'data/input/poi'),
                    'county_data': str(temp_dir / 'data/input/counties'),
                    'zipcode_data': str(temp_dir / 'data/input/zipcodes'),
                },
                'output': {
                    'analysis': str(temp_dir / 'data/output/analysis'),
                    'maps': str(temp_dir / 'data/output/maps'),
                    'isochrones': str(temp_dir / 'data/output/isochrones'),
                    'temp': str(temp_dir / 'data/output/temp'),
                }
            },
            'cache': {
                'root': str(temp_dir / 'cache'),
                'api_responses': str(temp_dir / 'cache/api_responses'),
                'processed_data': str(temp_dir / 'cache/processed_data')
            }
        },
        'study_area': {
            'states': [
                {'name': 'Georgia', 'abbr': 'GA'},
            ],
            'counties': {
                'Georgia': [
                    {'name': 'Fulton', 'fips': '13121'},
                    {'name': 'DeKalb', 'fips': '13089'}
                ]
            }
        },
        'point_of_interest': {
            'type': 'walmart',
            'radius_miles': 15
        },
        'isochrone_settings': {
            'travel_time_minutes': [15, 30, 45],
            'travel_mode': 'driving'
        }
    }
    
    config_path = temp_dir / 'test_config.yaml'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config_yaml, f)
    
    return config_path


@pytest.fixture
def test_config(test_config_file):
    """Create a test Config object."""
    return Config(config_path=str(test_config_file)) 