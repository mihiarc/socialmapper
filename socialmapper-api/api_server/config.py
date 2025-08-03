"""Configuration settings for the SocialMapper API server.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # CORS configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:8501", "http://127.0.0.1:8501"],
        description="Allowed CORS origins for frontend communication"
    )

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    # API configuration
    api_title: str = Field(default="SocialMapper API", description="API title")
    api_version: str = Field(default="0.1.0", description="API version")

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Job processing configuration
    max_concurrent_jobs: int = Field(default=10, description="Maximum concurrent analysis jobs")
    result_ttl_hours: int = Field(default=24, description="Result time-to-live in hours")
    cleanup_interval_minutes: int = Field(default=60, description="Interval between cleanup runs in minutes")

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute per client")

    # Census API configuration (inherited from SocialMapper)
    census_api_key: str = Field(default="", description="Census Bureau API key")

    # API authentication
    api_auth_enabled: bool = Field(default=False, description="Enable API key authentication")
    api_keys: str = Field(default="", description="Comma-separated list of valid API keys")

    # Storage configuration
    result_storage_path: str = Field(default="./results", description="Path to store analysis results")

    # External API configuration
    osm_api_timeout: int = Field(default=30, description="OpenStreetMap API timeout in seconds")
    census_api_timeout: int = Field(default=30, description="Census API timeout in seconds")

    # Analysis configuration
    default_travel_time_minutes: int = Field(default=15, description="Default travel time for analysis")
    max_travel_time_minutes: int = Field(default=60, description="Maximum allowed travel time")
    max_poi_types_per_request: int = Field(default=10, description="Maximum POI types per request")
    max_census_variables_per_request: int = Field(default=20, description="Maximum census variables per request")

    # Development/Debug settings
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator('api_keys', mode='before')
    @classmethod
    def validate_api_keys(cls, v):
        """Validate API keys format."""
        if isinstance(v, list):
            return ','.join(v)
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v_upper

    class Config:
        env_file = ".env"
        env_prefix = "SOCIALMAPPER_API_"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
