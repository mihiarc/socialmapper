"""
Configuration management for census operations.

Provides a clean, testable way to manage configuration without global state.
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass


@dataclass(frozen=True)
class CensusConfig:
    """Immutable configuration for census operations."""
    
    # API Configuration
    census_api_key: Optional[str] = None
    api_base_url: str = "https://api.census.gov/data"
    api_timeout_seconds: int = 30
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_max_size: int = 1000
    
    # Retry Configuration
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    
    # Logging
    log_level: str = "INFO"
    log_api_requests: bool = False
    
    # Data Storage
    enable_repository: bool = False
    repository_path: Optional[str] = None
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting by key."""
        return getattr(self, key, default)
    
    @classmethod
    def from_environment(cls) -> "CensusConfig":
        """
        Create configuration from environment variables.
        
        Environment variables:
        - CENSUS_API_KEY: Census Bureau API key
        - CENSUS_API_BASE_URL: Base URL for Census API
        - CENSUS_API_TIMEOUT: API timeout in seconds
        - CENSUS_RATE_LIMIT: Rate limit requests per minute
        - CENSUS_CACHE_ENABLED: Enable caching (true/false)
        - CENSUS_CACHE_TTL: Cache TTL in seconds
        - CENSUS_LOG_LEVEL: Logging level
        
        Returns:
            CensusConfig instance with environment-based settings
        """
        return cls(
            # API Configuration
            census_api_key=os.getenv("CENSUS_API_KEY"),
            api_base_url=os.getenv("CENSUS_API_BASE_URL", "https://api.census.gov/data"),
            api_timeout_seconds=int(os.getenv("CENSUS_API_TIMEOUT", "30")),
            
            # Rate Limiting
            rate_limit_requests_per_minute=int(os.getenv("CENSUS_RATE_LIMIT", "60")),
            rate_limit_burst_size=int(os.getenv("CENSUS_RATE_BURST", "10")),
            
            # Caching
            cache_enabled=os.getenv("CENSUS_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("CENSUS_CACHE_TTL", "3600")),
            cache_max_size=int(os.getenv("CENSUS_CACHE_MAX_SIZE", "1000")),
            
            # Retry Configuration
            max_retries=int(os.getenv("CENSUS_MAX_RETRIES", "3")),
            retry_backoff_factor=float(os.getenv("CENSUS_RETRY_BACKOFF", "0.5")),
            
            # Logging
            log_level=os.getenv("CENSUS_LOG_LEVEL", "INFO"),
            log_api_requests=os.getenv("CENSUS_LOG_API", "false").lower() == "true",
            
            # Data Storage
            enable_repository=os.getenv("CENSUS_ENABLE_REPOSITORY", "false").lower() == "true",
            repository_path=os.getenv("CENSUS_REPOSITORY_PATH"),
        )


class ConfigurationProvider:
    """Provides configuration from environment variables and defaults."""
    
    def __init__(self, config: Optional[CensusConfig] = None):
        """Initialize with optional configuration override."""
        self._config = config or self._load_from_environment()
    
    @property
    def census_api_key(self) -> Optional[str]:
        """Census Bureau API key."""
        return self._config.census_api_key
    
    @property
    def cache_enabled(self) -> bool:
        """Whether caching is enabled."""
        return self._config.cache_enabled
    
    @property
    def cache_ttl_seconds(self) -> int:
        """Default cache TTL in seconds."""
        return self._config.cache_ttl_seconds
    
    @property
    def rate_limit_requests_per_minute(self) -> int:
        """API rate limit."""
        return self._config.rate_limit_requests_per_minute
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        return self._config.get_setting(key, default)
    
    @classmethod
    def _load_from_environment(cls) -> CensusConfig:
        """Load configuration from environment variables."""
        return CensusConfig(
            # API Configuration
            census_api_key=os.getenv("CENSUS_API_KEY"),
            api_base_url=os.getenv("CENSUS_API_BASE_URL", "https://api.census.gov/data"),
            api_timeout_seconds=int(os.getenv("CENSUS_API_TIMEOUT", "30")),
            
            # Rate Limiting
            rate_limit_requests_per_minute=int(os.getenv("CENSUS_RATE_LIMIT", "60")),
            rate_limit_burst_size=int(os.getenv("CENSUS_RATE_BURST", "10")),
            
            # Caching
            cache_enabled=os.getenv("CENSUS_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("CENSUS_CACHE_TTL", "3600")),
            cache_max_size=int(os.getenv("CENSUS_CACHE_MAX_SIZE", "1000")),
            
            # Retry Configuration
            max_retries=int(os.getenv("CENSUS_MAX_RETRIES", "3")),
            retry_backoff_factor=float(os.getenv("CENSUS_RETRY_BACKOFF", "0.5")),
            
            # Logging
            log_level=os.getenv("CENSUS_LOG_LEVEL", "INFO"),
            log_api_requests=os.getenv("CENSUS_LOG_API", "false").lower() == "true",
            
            # Data Storage
            enable_repository=os.getenv("CENSUS_ENABLE_REPOSITORY", "false").lower() == "true",
            repository_path=os.getenv("CENSUS_REPOSITORY_PATH"),
        )
    
    @classmethod
    def for_testing(cls, **overrides) -> "ConfigurationProvider":
        """Create a configuration provider for testing."""
        test_config = CensusConfig(
            census_api_key="test_key",
            cache_enabled=False,
            rate_limit_requests_per_minute=1000,  # No rate limiting in tests
            log_level="DEBUG",
            **overrides
        )
        return cls(test_config) 