"""Tests for error handling middleware."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException


class TestErrorHandlingMiddleware:
    """Test error handling middleware functionality."""

    @pytest.mark.unit
    def test_validation_error_handling(self, client):
        """Test handling of validation errors."""
        # Send invalid data
        response = client.post(
            "/api/v1/analysis/location",
            json={
                "location": "",  # Empty location
                "travel_time": -5,  # Negative time
                "travel_mode": "invalid_mode"  # Invalid mode
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "validation_error"
        assert "field_errors" in data["details"]
        assert isinstance(data["details"]["field_errors"], list)
        assert len(data["details"]["field_errors"]) > 0

        # Check error structure
        for error in data["details"]["field_errors"]:
            assert "field" in error
            assert "message" in error
            assert "type" in error

    @pytest.mark.unit
    def test_not_found_error(self, client):
        """Test 404 error handling."""
        response = client.get("/api/v1/nonexistent/endpoint")

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "resource_not_found"
        assert "message" in data

    @pytest.mark.unit
    def test_method_not_allowed(self, client):
        """Test 405 error handling."""
        # Try GET on endpoint that only supports POST
        response = client.get("/api/v1/analysis/location")

        assert response.status_code == 405
        data = response.json()
        assert data["error_code"] == "method_not_allowed"

    @pytest.mark.unit
    def test_internal_server_error(self, client, monkeypatch):
        """Test 500 error handling."""
        # Mock an internal error in the job manager
        def mock_create_job(*args, **kwargs):
            raise Exception("Internal error")

        monkeypatch.setattr(
            "api_server.services.job_manager.JobManager.create_job",
            mock_create_job
        )

        response = client.post(
            "/api/v1/analysis/location",
            json={
                "location": "Test City, ST",
                "poi_type": "amenity",
                "poi_name": "library",
                "travel_time": 15,
                "travel_mode": "drive"
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "internal_error"
        assert "incident_id" in data

    @pytest.mark.unit
    def test_custom_http_exception(self, client, monkeypatch):
        """Test custom HTTP exception handling."""
        def mock_create_job(*args, **kwargs):
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable"
            )

        monkeypatch.setattr(
            "api_server.services.job_manager.JobManager.create_job",
            mock_create_job
        )

        response = client.post(
            "/api/v1/analysis/location",
            json={
                "location": "Test City, ST",
                "poi_type": "amenity",
                "poi_name": "library",
                "travel_time": 15,
                "travel_mode": "walk"
            }
        )

        assert response.status_code == 503
        data = response.json()
        assert "error_code" in data or "detail" in data

    @pytest.mark.unit
    def test_error_response_headers(self, client):
        """Test error response headers."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"
        assert "x-request-id" in response.headers

    @pytest.mark.unit
    def test_unhandled_exception_logging(self, client, caplog):
        """Test that unhandled exceptions are logged."""
        with patch("api_server.routers.health.health_check") as mock_health:
            mock_health.side_effect = RuntimeError("Unexpected error")

            response = client.get("/api/v1/health")

            assert response.status_code == 500
            # Check that error was logged
            assert "Unexpected error" in caplog.text

    @pytest.mark.unit
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/v1/analysis/location",
            data="{'invalid': json}",  # Malformed JSON
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "validation_error"
