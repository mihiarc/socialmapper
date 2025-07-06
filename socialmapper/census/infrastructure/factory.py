"""Factory methods for creating census infrastructure components.

Provides convenient factory methods for creating properly configured
census API clients and related components.
"""

import logging
import os
from typing import Any

from .api_client import CensusAPIClientImpl
from .cache import HybridCacheProvider, InMemoryCacheProvider, NoOpCacheProvider
from .configuration import CensusConfig
from .enhanced_api_client import EnhancedCensusAPIClient
from .rate_limiter import AdaptiveRateLimiter, NoOpRateLimiter, TokenBucketRateLimiter


def create_census_api_client(
    api_key: str | None = None,
    enhanced: bool = True,
    cache_enabled: bool = True,
    cache_type: str = "hybrid",
    rate_limit_per_minute: int = 60,
    adaptive_rate_limiting: bool = True,
    logger: logging.Logger | None = None,
    **config_overrides: Any,
) -> CensusAPIClientImpl | EnhancedCensusAPIClient:
    """Create a census API client with sensible defaults.

    Args:
        api_key: Census API key (defaults to CENSUS_API_KEY env var)
        enhanced: Whether to use enhanced client with reliability features
        cache_enabled: Whether to enable caching
        cache_type: Type of cache ("memory", "file", "hybrid", "none")
        rate_limit_per_minute: API rate limit
        adaptive_rate_limiting: Whether to use adaptive rate limiting
        logger: Logger instance (creates default if not provided)
        **config_overrides: Additional configuration overrides

    Returns:
        Configured census API client

    Example:
        >>> # Create enhanced client with defaults
        >>> client = create_census_api_client()
        
        >>> # Create basic client without enhancements
        >>> client = create_census_api_client(enhanced=False)
        
        >>> # Create client with custom configuration
        >>> client = create_census_api_client(
        ...     cache_type="memory",
        ...     rate_limit_per_minute=30,
        ...     max_retries=5,
        ... )
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("CENSUS_API_KEY", "")

    # Create logger if not provided
    if logger is None:
        logger = logging.getLogger("census_api")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    # Create configuration
    config_params = {
        "census_api_key": api_key,
        "cache_enabled": cache_enabled,
        "rate_limit_requests_per_minute": rate_limit_per_minute,
        **config_overrides,
    }
    config = CensusConfig(**config_params)

    # Create appropriate client
    if enhanced:
        return EnhancedCensusAPIClient(config, logger)
    else:
        return CensusAPIClientImpl(config, logger)


def create_census_cache(cache_type: str = "hybrid", **kwargs: Any):
    """Create a cache provider for census data.

    Args:
        cache_type: Type of cache ("memory", "file", "hybrid", "none")
        **kwargs: Additional arguments for cache provider

    Returns:
        Cache provider instance

    Example:
        >>> # Create hybrid cache with custom TTL
        >>> cache = create_census_cache("hybrid", ttl_seconds=7200)
        
        >>> # Create memory-only cache with size limit
        >>> cache = create_census_cache("memory", max_size=5000)
    """
    cache_type = cache_type.lower()

    if cache_type == "memory":
        return InMemoryCacheProvider(
            max_size=kwargs.get("max_size", 1000)
        )
    elif cache_type == "file":
        from .cache import FileCacheProvider
        return FileCacheProvider(
            cache_dir=kwargs.get("cache_dir", ".census_cache"),
            ttl_seconds=kwargs.get("ttl_seconds", 3600),
        )
    elif cache_type == "hybrid":
        return HybridCacheProvider(
            memory_size=kwargs.get("memory_size", 100),
            cache_dir=kwargs.get("cache_dir", ".census_cache"),
            ttl_seconds=kwargs.get("ttl_seconds", 3600),
        )
    elif cache_type == "none":
        return NoOpCacheProvider()
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")


def create_rate_limiter(
    rate_limit_per_minute: int = 60,
    adaptive: bool = True,
    **kwargs: Any,
):
    """Create a rate limiter for census API calls.

    Args:
        rate_limit_per_minute: Base rate limit
        adaptive: Whether to use adaptive rate limiting
        **kwargs: Additional arguments for rate limiter

    Returns:
        Rate limiter instance

    Example:
        >>> # Create adaptive rate limiter
        >>> limiter = create_rate_limiter(60, adaptive=True)
        
        >>> # Create fixed rate limiter with burst
        >>> limiter = create_rate_limiter(
        ...     60, 
        ...     adaptive=False, 
        ...     burst_size=100
        ... )
    """
    if rate_limit_per_minute <= 0:
        return NoOpRateLimiter()

    if adaptive:
        return AdaptiveRateLimiter(
            initial_requests_per_minute=rate_limit_per_minute,
            min_requests_per_minute=kwargs.get("min_requests_per_minute", 10),
            max_requests_per_minute=kwargs.get("max_requests_per_minute", 120),
            adaptation_factor=kwargs.get("adaptation_factor", 0.1),
        )
    else:
        return TokenBucketRateLimiter(
            requests_per_minute=rate_limit_per_minute,
            burst_size=kwargs.get("burst_size", rate_limit_per_minute),
        )


def create_census_system(
    api_key: str | None = None,
    enhanced: bool = True,
    logger: logging.Logger | None = None,
    **config_overrides: Any,
) -> dict[str, Any]:
    """Create a complete census system with all components.

    Args:
        api_key: Census API key
        enhanced: Whether to use enhanced features
        logger: Logger instance
        **config_overrides: Configuration overrides

    Returns:
        Dictionary with configured components:
        - client: Census API client
        - cache: Cache provider
        - rate_limiter: Rate limiter
        - config: Configuration object

    Example:
        >>> # Create complete system
        >>> system = create_census_system()
        >>> client = system["client"]
        >>> 
        >>> # Use the client
        >>> data = client.get_census_data(
        ...     variables=["B01003_001E"],
        ...     geography="state:*",
        ...     year=2022,
        ...     dataset="acs/acs5"
        ... )
    """
    # Extract component-specific config
    cache_type = config_overrides.pop("cache_type", "hybrid")
    cache_enabled = config_overrides.get("cache_enabled", True)
    rate_limit_per_minute = config_overrides.get("rate_limit_per_minute", 60)
    adaptive_rate_limiting = config_overrides.pop("adaptive_rate_limiting", True)

    # Create configuration
    config = CensusConfig(
        census_api_key=api_key or os.getenv("CENSUS_API_KEY", ""),
        **config_overrides,
    )

    # Create components
    cache = create_census_cache(cache_type) if cache_enabled else NoOpCacheProvider()
    rate_limiter = create_rate_limiter(rate_limit_per_minute, adaptive_rate_limiting)

    # Create client
    client = create_census_api_client(
        api_key=config.census_api_key,
        enhanced=enhanced,
        cache_enabled=cache_enabled,
        rate_limit_per_minute=rate_limit_per_minute,
        logger=logger,
        **config_overrides,
    )

    return {
        "client": client,
        "cache": cache,
        "rate_limiter": rate_limiter,
        "config": config,
    }
