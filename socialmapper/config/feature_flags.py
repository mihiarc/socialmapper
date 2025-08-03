"""Configuration system for SocialMapper backend."""

import os
from typing import Any


class BackendConfig:
    """Configuration for SocialMapper backend services."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # API Server Configuration
        self.enable_api_server = self._get_bool_env("SOCIALMAPPER_ENABLE_API_SERVER", False)
        self.api_server_host = os.getenv("SOCIALMAPPER_API_SERVER_HOST", "localhost")
        self.api_server_port = int(os.getenv("SOCIALMAPPER_API_SERVER_PORT", "8000"))

        # Development and Testing
        self.debug_mode = self._get_bool_env("SOCIALMAPPER_DEBUG_MODE", False)
        self.mock_api_responses = self._get_bool_env("SOCIALMAPPER_MOCK_API_RESPONSES", False)

        # Performance and Caching
        self.enable_caching = self._get_bool_env("SOCIALMAPPER_ENABLE_CACHING", True)
        self.cache_ttl_seconds = int(os.getenv("SOCIALMAPPER_CACHE_TTL", "3600"))

        # External API Configuration
        self.census_api_key = os.getenv("CENSUS_API_KEY")
        self.overpass_api_url = os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")
        self.rate_limit_requests_per_second = int(os.getenv("SOCIALMAPPER_RATE_LIMIT_RPS", "10"))

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")


# Global backend config instance
_backend_config: BackendConfig = None


def get_backend_config() -> BackendConfig:
    """Get the global backend configuration instance."""
    global _backend_config
    if _backend_config is None:
        _backend_config = BackendConfig()
    return _backend_config


def get_api_base_url() -> str:
    """Get the API base URL."""
    config = get_backend_config()
    return f"http://{config.api_server_host}:{config.api_server_port}"


def get_runtime_config() -> dict[str, Any]:
    """Get runtime configuration for backend services."""
    config = get_backend_config()

    return {
        "api_enabled": config.enable_api_server,
        "debug_mode": config.debug_mode,
        "caching_enabled": config.enable_caching,
        "cache_ttl": config.cache_ttl_seconds,
        "api_base_url": get_api_base_url(),
        "overpass_api_url": config.overpass_api_url,
        "rate_limit_rps": config.rate_limit_requests_per_second,
    }
