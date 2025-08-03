"""Shared pytest fixtures and configuration."""

import asyncio

# Import the FastAPI app
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from api_server.config import Settings, get_settings
from api_server.main import create_app
from api_server.services.job_manager import JobManager
from api_server.services.result_storage import ResultStorage


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with temporary directories."""
    # Create a minimal settings instance for testing
    import os
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8501,http://127.0.0.1:8501"
    os.environ["API_AUTH_ENABLED"] = "false"
    os.environ["RATE_LIMIT_PER_MINUTE"] = "60"

    settings = Settings()
    yield settings


@pytest.fixture
def app(test_settings):
    """Create a test FastAPI app instance."""
    # Override settings
    def override_get_settings():
        return test_settings

    app = create_app()
    app.dependency_overrides[get_settings] = override_get_settings
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app) -> AsyncGenerator:
    """Create an async test client."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_socialmapper():
    """Mock the SocialMapper module."""
    # Since the API server uses its own mock implementation,
    # we don't need to patch anything for most tests
    yield None


@pytest.fixture
def job_manager(test_settings) -> JobManager:
    """Create a test job manager."""
    return JobManager()


@pytest.fixture
def result_storage() -> ResultStorage:
    """Create a test result storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultStorage(storage_path=temp_dir)
        yield storage


@pytest.fixture
def sample_analysis_request():
    """Sample analysis request data."""
    return {
        "location": "Chapel Hill, NC",
        "travel_time_minutes": 15,
        "travel_mode": "drive",
        "poi_types": {
            "amenity": ["library"]
        },
        "census_variables": ["B01003_001E"]
    }


@pytest.fixture
def sample_job_result():
    """Sample job result data."""
    return {
        "job_id": "test-job-123",
        "status": "completed",
        "result": {
            "census_data": [
                {
                    "tract": "37135020501",
                    "B01003_001E": 5432,
                    "geometry": {"type": "Polygon", "coordinates": []}
                }
            ],
            "isochrones": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": []},
                    "properties": {"time": 15}
                }]
            },
            "map_files": {
                "accessibility": "test_accessibility_map.png",
                "distance": "test_distance_map.png",
                "B01003_001E": "test_demographic_map.png"
            }
        },
        "metadata": {
            "location": "Chapel Hill, NC",
            "travel_time": 15,
            "travel_mode": "drive",
            "created_at": "2025-01-21T10:00:00",
            "completed_at": "2025-01-21T10:01:00"
        }
    }


@pytest.fixture
def auth_headers():
    """Headers with API key for authenticated requests."""
    return {"X-API-Key": "test-api-key-123"}
