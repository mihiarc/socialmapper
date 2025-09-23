"""Pytest configuration and shared fixtures."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from .factories import TestDataFactory
from .mocks import create_mock_fixtures


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory()


@pytest.fixture
def mock_services():
    """Provide mock external services."""
    return create_mock_fixtures()


@pytest.fixture
def mock_census_api(mock_services):
    """Provide mock Census API."""
    return mock_services["census_api"]


@pytest.fixture
def mock_routing_api(mock_services):
    """Provide mock routing API."""
    return mock_services["routing_api"]


@pytest.fixture
def mock_geocoder(mock_services):
    """Provide mock geocoder."""
    return mock_services["geocoder"]


@pytest.fixture
def mock_poi_service(mock_services):
    """Provide mock POI service."""
    return mock_services["poi_service"]


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_environment():
    """Mock environment variables."""
    env_vars = {
        "CENSUS_API_KEY": "test_api_key_123",
        "MAPBOX_TOKEN": "test_mapbox_token",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    # Add any singleton resets here if needed
    yield


@pytest.fixture
def sample_geojson():
    """Provide sample GeoJSON data."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-122.4, 47.6],
                [-122.3, 47.6],
                [-122.3, 47.5],
                [-122.4, 47.5],
                [-122.4, 47.6]
            ]]
        },
        "properties": {
            "name": "Test Area"
        }
    }


@pytest.fixture
def sample_census_blocks():
    """Provide sample census block data."""
    return [
        {
            "geoid": "060370001001",
            "state_fips": "06",
            "county_fips": "037",
            "tract": "000100",
            "block_group": "1",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.4, 47.6],
                    [-122.3, 47.6],
                    [-122.3, 47.5],
                    [-122.4, 47.5],
                    [-122.4, 47.6]
                ]]
            }
        },
        {
            "geoid": "060370001002",
            "state_fips": "06",
            "county_fips": "037",
            "tract": "000100",
            "block_group": "2",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.3, 47.6],
                    [-122.2, 47.6],
                    [-122.2, 47.5],
                    [-122.3, 47.5],
                    [-122.3, 47.6]
                ]]
            }
        }
    ]


@pytest.fixture
def sample_census_data():
    """Provide sample census data."""
    return {
        "060370001001": {
            "population": 2543,
            "median_income": 75000,
            "median_age": 35.5
        },
        "060370001002": {
            "population": 3127,
            "median_income": 62000,
            "median_age": 42.1
        }
    }


# Marker for tests that require real API calls
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers",
        "real_api: mark test to run with real API calls (deselect with '-m \"not real_api\"')"
    )
    config.addinivalue_line(
        "markers",
        "mock_api: mark test to run with mocked API calls"
    )