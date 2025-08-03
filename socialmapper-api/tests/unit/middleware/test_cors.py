"""Tests for CORS middleware."""

import pytest


class TestCORSMiddleware:
    """Test CORS middleware functionality."""

    @pytest.mark.unit
    def test_cors_headers_on_get(self, client):
        """Test CORS headers on GET request."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:8501"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:8501"

    @pytest.mark.unit
    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request."""
        response = client.options(
            "/api/v1/analysis/location",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-api-key"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

        # Check allowed methods
        allowed_methods = response.headers["access-control-allow-methods"]
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "DELETE" in allowed_methods

        # Check allowed headers
        allowed_headers = response.headers["access-control-allow-headers"].lower()
        assert "content-type" in allowed_headers
        assert "x-api-key" in allowed_headers

    @pytest.mark.unit
    def test_cors_actual_request_with_origin(self, client):
        """Test CORS headers on actual request with Origin header."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:8501"}
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:8501"

    @pytest.mark.unit
    def test_cors_credentials_allowed(self, client):
        """Test that credentials are allowed for specific origins."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "GET"
            }
        )

        # Should include credentials header for specific origins
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.unit
    def test_cors_max_age_header(self, client):
        """Test CORS max age header for caching preflight."""
        response = client.options(
            "/api/v1/analysis/location",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "POST"
            }
        )

        assert response.status_code == 200
        assert "access-control-max-age" in response.headers
        # Configured to 86400 seconds (24 hours)
        assert int(response.headers["access-control-max-age"]) == 86400
