"""Pytest configuration and shared fixtures for SocialMapper tests."""

import os

import pytest


@pytest.fixture(scope="session")
def census_api_key():
    """Get Census API key from environment."""
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        pytest.skip("CENSUS_API_KEY environment variable not set")
    return key


@pytest.fixture
def portland_coords():
    """Portland, OR coordinates."""
    return (45.5152, -122.6784)


@pytest.fixture
def chapel_hill_coords():
    """Chapel Hill, NC coordinates."""
    return (35.9132, -79.0558)


@pytest.fixture
def sample_geojson_polygon():
    """Sample GeoJSON polygon for testing."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [-122.68, 45.51],
            [-122.68, 45.52],
            [-122.67, 45.52],
            [-122.67, 45.51],
            [-122.68, 45.51]
        ]]
    }


@pytest.fixture
def sample_geojson_feature(sample_geojson_polygon):
    """Sample GeoJSON Feature for testing."""
    return {
        "type": "Feature",
        "geometry": sample_geojson_polygon,
        "properties": {
            "name": "Test Area"
        }
    }


@pytest.fixture
def sample_census_block():
    """Sample census block data."""
    return {
        "geoid": "410510100001",
        "state_fips": "41",
        "county_fips": "051",
        "tract": "010000",
        "block_group": "1",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-122.68, 45.51],
                [-122.68, 45.52],
                [-122.67, 45.52],
                [-122.67, 45.51],
                [-122.68, 45.51]
            ]]
        },
        "area_sq_km": 1.5
    }


@pytest.fixture
def sample_poi_data():
    """Sample POI data for testing."""
    return [
        {
            "name": "Test Library",
            "category": "library",
            "lat": 45.5152,
            "lon": -122.6784,
            "distance_km": 0.5,
            "tags": {"amenity": "library"}
        },
        {
            "name": "Test Restaurant",
            "category": "restaurant",
            "lat": 45.5160,
            "lon": -122.6790,
            "distance_km": 0.8,
            "tags": {"amenity": "restaurant", "cuisine": "italian"}
        }
    ]


@pytest.fixture
def valid_coordinates_list():
    """List of valid coordinate tuples for testing."""
    return [
        (45.5152, -122.6784),  # Portland, OR
        (35.7796, -78.6382),   # Raleigh, NC
        (40.7128, -74.0060),   # New York, NY
        (0, 0),                # Null Island (technically valid)
        (-33.8688, 151.2093),  # Sydney, Australia
    ]


@pytest.fixture
def invalid_coordinates_list():
    """List of invalid coordinate tuples for testing."""
    return [
        (91, 0),      # Latitude too high
        (-91, 0),     # Latitude too low
        (0, 181),     # Longitude too high
        (0, -181),    # Longitude too low
        (100, 200),   # Both out of range
    ]
