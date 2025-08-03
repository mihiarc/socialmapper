"""Tests for API middleware components (rate limiting, authentication).
"""

from datetime import UTC, datetime

import pytest
from api_server.config import Settings
from api_server.middleware import setup_api_key_auth, setup_rate_limiting
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def settings():
    """Test settings."""
    return Settings(
        rate_limit_per_minute=10,  # Low limit for testing
        api_auth_enabled=True,
        api_keys="test-key-1,test-key-2"
    )


@pytest.fixture
def app_with_middleware(settings):
    """Create test app with middleware."""
    app = FastAPI()

    # Add middleware
    setup_rate_limiting(app, settings)
    setup_api_key_auth(app, settings)

    # Add test endpoints
    @app.get("/api/v1/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/api/v1/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app_with_middleware):
    """Test client."""
    return TestClient(app_with_middleware)


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_allows_requests_within_limit(self, client):
        """Test that requests within rate limit are allowed."""
        # Make requests within limit (10 per minute)
        for i in range(5):
            response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert int(response.headers["X-RateLimit-Remaining"]) == 9 - i

    def test_rate_limit_blocks_excessive_requests(self, client, settings):
        """Test that excessive requests are blocked."""
        # Make requests up to the limit
        for _ in range(settings.rate_limit_per_minute):
            response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
            assert response.status_code == 200

        # Next request should be blocked
        response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
        assert response.status_code == 429
        assert "Retry-After" in response.headers

        # Check error response
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert data["limit"] == settings.rate_limit_per_minute
        assert data["retry_after_seconds"] > 0

    def test_rate_limit_headers(self, client, settings):
        """Test rate limit headers."""
        response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
        assert response.status_code == 200

        # Check headers
        assert response.headers["X-RateLimit-Limit"] == str(settings.rate_limit_per_minute)
        assert int(response.headers["X-RateLimit-Remaining"]) < settings.rate_limit_per_minute
        assert "X-RateLimit-Reset" in response.headers

        # Reset timestamp should be in the future
        reset_timestamp = int(response.headers["X-RateLimit-Reset"])
        assert reset_timestamp > int(datetime.now(UTC).timestamp())

    def test_rate_limit_per_client(self, client):
        """Test that rate limits are per client IP."""
        # Make requests from first "client"
        for _ in range(5):
            response = client.get("/api/v1/test", headers={
                "X-API-Key": "test-key-1",
                "X-Forwarded-For": "192.168.1.1"
            })
            assert response.status_code == 200

        # Make requests from second "client" - should not be rate limited
        for _ in range(5):
            response = client.get("/api/v1/test", headers={
                "X-API-Key": "test-key-1",
                "X-Forwarded-For": "192.168.1.2"
            })
            assert response.status_code == 200

    def test_health_endpoint_exempt_from_rate_limit(self, client, settings):
        """Test that health endpoint is exempt from rate limiting."""
        # Make many requests to health endpoint
        for _ in range(settings.rate_limit_per_minute + 5):
            response = client.get("/api/v1/health")
            assert response.status_code == 200


class TestAPIKeyAuthentication:
    """Test API key authentication middleware."""

    def test_request_without_api_key_rejected(self, client):
        """Test that requests without API key are rejected."""
        response = client.get("/api/v1/test")
        assert response.status_code == 401

        data = response.json()
        assert data["error_code"] == "AUTHENTICATION_ERROR"
        assert "API key required" in data["message"]

    def test_request_with_valid_api_key_allowed(self, client):
        """Test that requests with valid API key are allowed."""
        response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
        assert response.status_code == 200

        # Test with second key
        response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-2"})
        assert response.status_code == 200

    def test_request_with_invalid_api_key_rejected(self, client):
        """Test that requests with invalid API key are rejected."""
        response = client.get("/api/v1/test", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == 401

        data = response.json()
        assert data["error_code"] == "AUTHENTICATION_ERROR"
        assert "Invalid API key" in data["message"]

    def test_health_endpoint_public(self, client):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"

    def test_api_key_header_name(self, client):
        """Test that API key must be in correct header."""
        # Wrong header name
        response = client.get("/api/v1/test", headers={"Authorization": "test-key-1"})
        assert response.status_code == 401

        # Correct header name
        response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
        assert response.status_code == 200


class TestMiddlewareIntegration:
    """Test middleware integration."""

    def test_rate_limit_and_auth_together(self, client, settings):
        """Test that rate limiting and authentication work together."""
        # Request without API key - should fail auth first
        response = client.get("/api/v1/test")
        assert response.status_code == 401

        # Requests with API key - should be rate limited
        for i in range(settings.rate_limit_per_minute):
            response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/api/v1/test", headers={"X-API-Key": "test-key-1"})
        assert response.status_code == 429

    def test_different_api_keys_share_rate_limit(self, client, settings):
        """Test that different API keys from same IP share rate limit."""
        # Use up half the limit with first key
        for _ in range(settings.rate_limit_per_minute // 2):
            response = client.get("/api/v1/test", headers={
                "X-API-Key": "test-key-1",
                "X-Forwarded-For": "192.168.1.100"
            })
            assert response.status_code == 200

        # Use remaining limit with second key from same IP
        for _ in range(settings.rate_limit_per_minute // 2):
            response = client.get("/api/v1/test", headers={
                "X-API-Key": "test-key-2",
                "X-Forwarded-For": "192.168.1.100"
            })
            assert response.status_code == 200

        # Next request should be rate limited regardless of key
        response = client.get("/api/v1/test", headers={
            "X-API-Key": "test-key-1",
            "X-Forwarded-For": "192.168.1.100"
        })
        assert response.status_code == 429


class TestMiddlewareConfiguration:
    """Test middleware configuration."""

    def test_auth_disabled_allows_all_requests(self):
        """Test that disabling auth allows all requests."""
        # Create app with auth disabled
        settings = Settings(api_auth_enabled=False)
        app = FastAPI()
        setup_api_key_auth(app, settings)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)

        # Request without API key should succeed
        response = client.get("/api/v1/test")
        assert response.status_code == 200

    def test_custom_rate_limit(self):
        """Test custom rate limit configuration."""
        # Create app with custom rate limit
        settings = Settings(rate_limit_per_minute=5)
        app = FastAPI()
        setup_rate_limiting(app, settings)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)

        # Make requests up to custom limit
        for _ in range(5):
            response = client.get("/api/v1/test")
            assert response.status_code == 200

        # Next request should be blocked
        response = client.get("/api/v1/test")
        assert response.status_code == 429


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
