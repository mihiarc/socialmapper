"""Configuration settings for the SocialMapper API server."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # CORS configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins for frontend communication",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
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
    cleanup_interval_minutes: int = Field(
        default=60, description="Interval between cleanup runs in minutes"
    )

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute per client")

    # Census API configuration (inherited from SocialMapper)
    census_api_key: str = Field(default="", description="Census Bureau API key")

    # API authentication
    api_auth_enabled: bool = Field(default=False, description="Enable API key authentication")
    api_keys: str = Field(default="", description="Comma-separated list of valid API keys")

    # Storage configuration
    result_storage_path: str = Field(
        default="./results", description="Path to store analysis results"
    )

    # External API configuration
    osm_api_timeout: int = Field(default=30, description="OpenStreetMap API timeout in seconds")
    census_api_timeout: int = Field(default=30, description="Census API timeout in seconds")

    # Analysis configuration
    default_travel_time_minutes: int = Field(
        default=15, description="Default travel time for analysis"
    )
    max_travel_time_minutes: int = Field(default=60, description="Maximum allowed travel time")
    max_poi_types_per_request: int = Field(default=10, description="Maximum POI types per request")
    max_census_variables_per_request: int = Field(
        default=20, description="Maximum census variables per request"
    )

    # Development/Debug settings
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Redis cache configuration
    redis_host: str = Field(default="localhost", description="Redis server host")
    redis_port: int = Field(default=6379, description="Redis server port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: str = Field(default="", description="Redis password")
    cache_enabled: bool = Field(default=True, description="Enable Redis caching")
    
    # Database configuration
    database_url: str = Field(default="", description="PostgreSQL connection URL")
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="socialmapper", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="", description="Database password")
    db_pool_min_size: int = Field(default=10, description="Min database connections")
    db_pool_max_size: int = Field(default=50, description="Max database connections")
    
    # WebSocket configuration
    websocket_enabled: bool = Field(default=True, description="Enable WebSocket support")
    websocket_heartbeat_interval: int = Field(default=30, description="WebSocket heartbeat interval in seconds")
    
    # Performance optimization
    enable_response_compression: bool = Field(default=True, description="Enable response compression")
    pagination_default_limit: int = Field(default=100, description="Default pagination limit")
    pagination_max_limit: int = Field(default=1000, description="Maximum pagination limit")
    
    # Demo platform configuration
    demo_mode_enabled: bool = Field(default=False, description="Enable demo mode restrictions")
    demo_max_concurrent_jobs: int = Field(default=3, description="Max concurrent jobs per demo session")
    demo_session_timeout_minutes: int = Field(default=60, description="Demo session timeout")
    
    # MCP (Model Context Protocol) configuration
    mcp_enabled: bool = Field(default=True, description="Enable MCP integration")
    mcp_mount_path: str = Field(default="/mcp", description="Path to mount MCP server")
    mcp_auth_enabled: bool = Field(default=True, description="Enable MCP authentication")
    mcp_allowed_tools: list[str] = Field(
        default=[],
        description="List of allowed MCP tools (empty list allows all)"
    )
    mcp_tool_timeout: int = Field(default=30, description="Default timeout for MCP tools in seconds")
    mcp_max_concurrent: int = Field(default=10, description="Maximum concurrent MCP requests")
    mcp_cache_enabled: bool = Field(default=True, description="Enable MCP response caching")
    mcp_cache_ttl: int = Field(default=300, description="MCP cache TTL in seconds")
    mcp_rate_limit_per_minute: int = Field(default=60, description="MCP rate limit per minute")
    
    # MCP context middleware configuration
    mcp_enable_performance_logging: bool = Field(
        default=True, 
        description="Enable MCP performance metrics logging"
    )
    mcp_enable_request_logging: bool = Field(
        default=True, 
        description="Enable MCP request/response logging"
    )
    mcp_performance_threshold_ms: float = Field(
        default=1000.0, 
        description="Threshold for slow MCP request warnings in milliseconds"
    )
    
    # MCP metrics configuration
    mcp_metrics_enabled: bool = Field(
        default=True, 
        description="Enable detailed MCP metrics collection"
    )
    mcp_metrics_retention_hours: int = Field(
        default=24, 
        description="Hours to retain detailed MCP metrics"
    )
    mcp_metrics_detailed_tracking: bool = Field(
        default=True, 
        description="Enable detailed per-invocation tracking"
    )

    @field_validator("api_keys", mode="before")
    @classmethod
    def validate_api_keys(cls, v):
        """Validate API keys format."""
        if isinstance(v, list):
            return ",".join(v)
        return v
    
    @field_validator("mcp_allowed_tools", mode="before")
    @classmethod
    def parse_mcp_allowed_tools(cls, v):
        """Parse MCP allowed tools from comma-separated string or list."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [tool.strip() for tool in v.split(",") if tool.strip()]
        return v or []

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v_upper

    class Config:
        """Pydantic configuration for environment variable loading."""
        env_file = ".env"
        env_prefix = "SOCIALMAPPER_API_"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
