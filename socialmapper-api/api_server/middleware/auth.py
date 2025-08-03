"""API key authentication middleware for the SocialMapper API.
"""

import hashlib
import logging
from datetime import UTC, datetime

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from ..config import get_settings
from ..models import AuthenticationError

logger = logging.getLogger(__name__)

# API key header name
API_KEY_HEADER = "X-API-Key"

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/api/v1/health",
    "/api/v1/status",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class APIKeyMiddleware:
    """API key authentication middleware.
    
    This is a simple implementation. In production, you would:
    - Store API keys in a database with metadata (user, permissions, etc.)
    - Use Redis for caching validated keys
    - Implement key rotation and expiration
    - Add rate limiting per API key
    """

    def __init__(self, app, api_keys: set[str] | None = None, enabled: bool = False):
        self.app = app
        self.enabled = enabled
        self.api_keys = api_keys or set()

        # In production, store hashed keys
        self.hashed_keys = {self._hash_key(key) for key in self.api_keys if key}

    async def __call__(self, request: Request, call_next):
        # Skip auth for public paths
        if not self.enabled or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Check for API key
        api_key = request.headers.get(API_KEY_HEADER)

        if not api_key:
            error = AuthenticationError(
                message="API key required. Please provide a valid API key in the X-API-Key header.",
                auth_method="api_key"
            )

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error.model_dump(),
                headers={"WWW-Authenticate": "API-Key"}
            )

        # Validate API key
        if not self._validate_key(api_key):
            error = AuthenticationError(
                message="Invalid API key. Please check your API key and try again.",
                auth_method="api_key"
            )

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error.model_dump(),
                headers={"WWW-Authenticate": "API-Key"}
            )

        # Add authenticated flag to request state
        request.state.authenticated = True
        request.state.api_key_hash = self._hash_key(api_key)

        # Process request
        response = await call_next(request)

        return response

    def _hash_key(self, key: str) -> str:
        """Hash API key for secure storage/comparison."""
        return hashlib.sha256(key.encode()).hexdigest()

    def _validate_key(self, key: str) -> bool:
        """Validate API key."""
        if not key or not self.hashed_keys:
            return False

        # Hash the provided key and check against stored hashes
        key_hash = self._hash_key(key)
        return key_hash in self.hashed_keys


# Optional: API key dependency for specific endpoints
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


async def get_api_key(api_key: str | None = api_key_header) -> str | None:
    """Dependency to get API key from header.
    
    Use this for endpoints that optionally support API key authentication
    for enhanced features (e.g., higher rate limits).
    """
    return api_key


async def require_api_key(api_key: str | None = api_key_header) -> str:
    """Dependency to require API key for specific endpoints.
    
    Use this for endpoints that must have API key authentication.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "AUTHENTICATION_ERROR",
                "message": "API key required",
                "timestamp": datetime.now(UTC).isoformat()
            },
            headers={"WWW-Authenticate": "API-Key"}
        )

    # In production, validate the key against database
    # For now, just return it
    return api_key


def setup_api_key_auth(app, settings=None):
    """Set up API key authentication middleware."""
    if settings is None:
        settings = get_settings()

    # Get API keys from settings
    api_keys = set()

    # Check for API keys in environment
    # In production, load from database or secure key management service
    if hasattr(settings, 'api_keys'):
        if isinstance(settings.api_keys, str):
            # Parse comma-separated keys
            api_keys = {key.strip() for key in settings.api_keys.split(',') if key.strip()}
        elif isinstance(settings.api_keys, list):
            api_keys = set(settings.api_keys)

    # Check if authentication is enabled
    enabled = getattr(settings, 'api_auth_enabled', False)

    if enabled and not api_keys:
        logger.warning("API authentication is enabled but no API keys are configured")

    # Create middleware instance
    middleware = APIKeyMiddleware(
        app,
        api_keys=api_keys,
        enabled=enabled
    )

    # Add middleware to app
    app.middleware("http")(middleware)

    if enabled:
        logger.info(f"API key authentication enabled with {len(api_keys)} keys")
    else:
        logger.info("API key authentication disabled")
