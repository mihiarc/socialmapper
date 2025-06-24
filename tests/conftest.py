"""Pytest configuration and shared fixtures for SocialMapper tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock
from typing import Any, Dict, Generator

import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from faker import Faker

# Set test environment variables
os.environ["CENSUS_API_KEY"] = "test_key_for_mocking"
os.environ["CENSUS_CACHE_ENABLED"] = "false"
os.environ["CENSUS_LOG_LEVEL"] = "ERROR"

fake = Faker()


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_census_api_key() -> str:
    """Mock Census API key for testing."""
    return "test_census_api_key_12345"


@pytest.fixture
def sample_coordinates() -> Dict[str, float]:
    """Sample coordinates for testing (University of Washington, Seattle)."""
    return {
        "latitude": 47.6062,
        "longitude": -122.3321
    }


@pytest.fixture
def sample_addresses() -> list[str]:
    """Sample addresses for geocoding tests."""
    return [
        "1600 Amphitheatre Parkway, Mountain View, CA",
        "1 Microsoft Way, Redmond, WA",
        "410 Terry Ave N, Seattle, WA",
        "University of Washington, Seattle, WA"
    ]


@pytest.fixture
def sample_poi_data() -> pd.DataFrame:
    """Sample POI data for testing."""
    return pd.DataFrame({
        "name": ["Central Library", "Community Center", "City Park"],
        "amenity": ["library", "community_centre", "park"],
        "lat": [47.6062, 47.6152, 47.6205],
        "lon": [-122.3321, -122.3411, -122.3501],
        "osm_id": [123456, 234567, 345678]
    })


@pytest.fixture
def sample_census_data() -> pd.DataFrame:
    """Sample census demographic data for testing."""
    return pd.DataFrame({
        "GEOID": ["530330001001", "530330001002", "530330001003"],
        "B01003_001E": [1250, 980, 1340],  # Total population
        "B25003_002E": [450, 380, 520],    # Owner occupied housing
        "B25003_003E": [200, 180, 240],    # Renter occupied housing
        "B19013_001E": [75000, 65000, 85000],  # Median household income
        "geometry": [
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
            Polygon([(0, 1), (1, 1), (1, 2), (0, 2)])
        ]
    })


@pytest.fixture
def sample_geodataframe(sample_census_data: pd.DataFrame) -> gpd.GeoDataFrame:
    """Sample GeoDataFrame with census block group data."""
    return gpd.GeoDataFrame(sample_census_data, crs="EPSG:4326")


@pytest.fixture
def sample_isochrone_polygon() -> Polygon:
    """Sample isochrone polygon for testing."""
    # Create a roughly circular polygon
    center = Point(-122.3321, 47.6062)
    return center.buffer(0.01)  # Approximately 1km radius


@pytest.fixture
def mock_osm_response() -> Dict[str, Any]:
    """Mock OpenStreetMap Overpass API response."""
    return {
        "elements": [
            {
                "type": "node",
                "id": 123456,
                "lat": 47.6062,
                "lon": -122.3321,
                "tags": {
                    "amenity": "library",
                    "name": "Central Library",
                    "addr:street": "4th Avenue",
                    "addr:housenumber": "1000"
                }
            },
            {
                "type": "node", 
                "id": 234567,
                "lat": 47.6152,
                "lon": -122.3411,
                "tags": {
                    "amenity": "community_centre",
                    "name": "Community Center"
                }
            }
        ]
    }


@pytest.fixture
def mock_census_response() -> Dict[str, Any]:
    """Mock Census API response."""
    return [
        ["NAME", "B01003_001E", "state", "county", "tract", "block group"],
        ["Block Group 1, Census Tract 1, King County, Washington", "1250", "53", "033", "000100", "1"],
        ["Block Group 2, Census Tract 1, King County, Washington", "980", "53", "033", "000100", "2"],
        ["Block Group 3, Census Tract 1, King County, Washington", "1340", "53", "033", "000100", "3"]
    ]


@pytest.fixture
def mock_geocoding_response() -> Dict[str, Any]:
    """Mock geocoding API response."""
    return {
        "results": [
            {
                "geometry": {
                    "location": {
                        "lat": 47.6062,
                        "lng": -122.3321
                    }
                },
                "formatted_address": "1000 4th Ave, Seattle, WA 98104, USA",
                "place_id": "test_place_id_123"
            }
        ],
        "status": "OK"
    }


@pytest.fixture
def mock_network_graph() -> Mock:
    """Mock OSMnx network graph."""
    graph = Mock()
    graph.nodes = {
        1: {"x": -122.3321, "y": 47.6062},
        2: {"x": -122.3311, "y": 47.6072},
        3: {"x": -122.3331, "y": 47.6052}
    }
    graph.edges = [
        (1, 2, {"length": 100, "highway": "residential"}),
        (2, 3, {"length": 150, "highway": "primary"}),
        (1, 3, {"length": 200, "highway": "secondary"})
    ]
    return graph


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset all caches before each test to ensure test isolation."""
    # Clear any module-level caches
    yield
    # Cleanup after test if needed


@pytest.fixture
def mock_api_responses(monkeypatch):
    """Mock all external API responses for integration tests."""
    # This fixture can be extended to mock specific API calls
    pass


# Async fixtures for async testing
@pytest.fixture
async def async_sample_data():
    """Async fixture for testing async functions."""
    # Simulate async data preparation
    return {"async_data": "test_value"}


# Performance testing fixtures
@pytest.fixture
def large_dataset() -> pd.DataFrame:
    """Large dataset for performance testing."""
    fake = Faker()
    return pd.DataFrame({
        "id": range(10000),
        "name": [fake.company() for _ in range(10000)],
        "lat": [fake.latitude() for _ in range(10000)],
        "lon": [fake.longitude() for _ in range(10000)]
    })


# Property-based testing helpers
@pytest.fixture
def hypothesis_settings():
    """Hypothesis settings for property-based tests."""
    from hypothesis import settings
    return settings(max_examples=100, deadline=None)