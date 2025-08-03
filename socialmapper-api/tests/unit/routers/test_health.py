"""Tests for health check endpoints."""


import pytest


class TestHealthEndpoints:
    """Test health check and status endpoints."""

    @pytest.mark.unit
    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.unit
    def test_status_endpoint(self, client, job_manager):
        """Test detailed status endpoint."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "system_info" in data
        assert "configuration" in data

        # Check system info
        assert "python_version" in data["system_info"]
        assert "platform" in data["system_info"]
        assert "architecture" in data["system_info"]

        # Check configuration
        assert "cors_origins" in data["configuration"]
        assert "max_concurrent_jobs" in data["configuration"]
        assert "rate_limit_per_minute" in data["configuration"]

    @pytest.mark.unit
    def test_health_check_response_headers(self, client):
        """Test health check response headers."""
        # Make request with Origin header to trigger CORS
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )

        # Check basic response
        assert response.status_code == 200

        # Check content type
        assert "application/json" in response.headers.get("content-type", "")

    @pytest.mark.unit
    def test_status_endpoint_configuration(self, client):
        """Test status endpoint configuration values."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200

        data = response.json()
        config = data["configuration"]

        # Check that configuration values are present and valid
        assert isinstance(config["cors_origins"], list)
        assert isinstance(config["max_concurrent_jobs"], int)
        assert isinstance(config["rate_limit_per_minute"], int)
        assert isinstance(config["has_census_api_key"], bool)
