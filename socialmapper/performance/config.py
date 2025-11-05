"""Performance configuration for SocialMapper.

Provides centralized configuration for performance tuning with
predefined presets optimized for different use cases.
"""

import logging
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PerformancePreset(str, Enum):
    """Predefined performance configuration presets.

    Attributes
    ----------
    FAST : str
        Optimized for speed with larger memory usage.
        - Large caches (10GB networks, 1GB geocoding, 500MB Census)
        - Aggressive connection pooling (20 connections)
        - Short cache TTL (24 hours)
    BALANCED : str
        Balanced between speed and memory efficiency.
        - Medium caches (5GB networks, 500MB geocoding, 250MB Census)
        - Moderate connection pooling (10 connections)
        - Medium cache TTL (7 days)
    MEMORY_EFFICIENT : str
        Optimized for low memory usage with slower operations.
        - Small caches (2GB networks, 100MB geocoding, 50MB Census)
        - Minimal connection pooling (5 connections)
        - Long cache TTL (30 days to reduce re-fetching)

    Examples
    --------
    >>> config = get_performance_config(preset=PerformancePreset.FAST)
    >>> config.network_cache_size_gb
    10
    """

    FAST = "fast"
    BALANCED = "balanced"
    MEMORY_EFFICIENT = "memory_efficient"


class PerformanceConfig(BaseModel):
    """Configuration for SocialMapper performance optimizations.

    Parameters
    ----------
    network_cache_size_gb : int
        Maximum size of network graph cache in GB, by default 5.
    geocoding_cache_size_mb : int
        Maximum size of geocoding cache in MB, by default 500.
    census_cache_size_mb : int
        Maximum size of Census data cache in MB, by default 250.
    cache_ttl_hours : int
        Time-to-live for cached data in hours, by default 168 (7 days).
    http_pool_connections : int
        Number of connection pool instances, by default 10.
    http_pool_maxsize : int
        Maximum connections per pool, by default 10.
    http_timeout_seconds : int
        Request timeout in seconds, by default 30.
    batch_size_census : int
        Batch size for Census API requests, by default 50.
    batch_size_geocoding : int
        Batch size for geocoding requests, by default 100.
    enable_memory_optimization : bool
        Enable automatic memory optimization, by default True.
    enable_connection_pooling : bool
        Enable HTTP connection pooling, by default True.
    preset : str, optional
        Preset name if created from preset, by default None.

    Examples
    --------
    >>> config = PerformanceConfig(
    ...     network_cache_size_gb=10,
    ...     cache_ttl_hours=24
    ... )
    >>> config.network_cache_size_gb
    10
    """

    network_cache_size_gb: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum size of network graph cache in GB"
    )
    geocoding_cache_size_mb: int = Field(
        default=500,
        ge=10,
        le=10000,
        description="Maximum size of geocoding cache in MB"
    )
    census_cache_size_mb: int = Field(
        default=250,
        ge=10,
        le=5000,
        description="Maximum size of Census data cache in MB"
    )
    cache_ttl_hours: int = Field(
        default=168,  # 7 days
        ge=1,
        le=8760,  # 1 year
        description="Time-to-live for cached data in hours"
    )
    http_pool_connections: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of connection pool instances"
    )
    http_pool_maxsize: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum connections per pool"
    )
    http_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds"
    )
    batch_size_census: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Batch size for Census API requests"
    )
    batch_size_geocoding: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Batch size for geocoding requests"
    )
    enable_memory_optimization: bool = Field(
        default=True,
        description="Enable automatic memory optimization"
    )
    enable_connection_pooling: bool = Field(
        default=True,
        description="Enable HTTP connection pooling"
    )
    preset: str | None = Field(
        default=None,
        description="Preset name if created from preset"
    )

    model_config = {"frozen": False}  # Allow modifications after creation


def get_performance_config(
    preset: Literal["fast", "balanced", "memory_efficient"] | PerformancePreset = "balanced",
    **overrides
) -> PerformanceConfig:
    """Get performance configuration with optional overrides.

    Creates a performance configuration from a predefined preset
    with optional parameter overrides for fine-tuning.

    Parameters
    ----------
    preset : str or PerformancePreset
        Preset configuration to use. Options:
        - 'fast': Maximum speed, higher memory usage
        - 'balanced': Good balance (default)
        - 'memory_efficient': Minimal memory, slower operations
    **overrides
        Optional parameter overrides (e.g., cache_ttl_hours=24).

    Returns
    -------
    PerformanceConfig
        Configured performance settings.

    Raises
    ------
    ValueError
        If preset is invalid.

    Examples
    --------
    >>> # Use fast preset
    >>> config = get_performance_config(preset='fast')
    >>> config.network_cache_size_gb
    10

    >>> # Use balanced with custom TTL
    >>> config = get_performance_config(
    ...     preset='balanced',
    ...     cache_ttl_hours=24
    ... )
    >>> config.cache_ttl_hours
    24

    >>> # Memory efficient for resource-constrained environments
    >>> config = get_performance_config(preset='memory_efficient')
    >>> config.network_cache_size_gb
    2
    """
    # Convert string to enum if needed
    if isinstance(preset, str):
        try:
            preset = PerformancePreset(preset)
        except ValueError as e:
            raise ValueError(
                f"Invalid preset '{preset}'. Choose from: "
                f"{', '.join(p.value for p in PerformancePreset)}"
            ) from e

    # Define preset configurations
    preset_configs = {
        PerformancePreset.FAST: {
            "network_cache_size_gb": 10,
            "geocoding_cache_size_mb": 1000,
            "census_cache_size_mb": 500,
            "cache_ttl_hours": 24,
            "http_pool_connections": 20,
            "http_pool_maxsize": 20,
            "http_timeout_seconds": 30,
            "batch_size_census": 50,
            "batch_size_geocoding": 100,
            "enable_memory_optimization": False,
            "enable_connection_pooling": True,
            "preset": "fast"
        },
        PerformancePreset.BALANCED: {
            "network_cache_size_gb": 5,
            "geocoding_cache_size_mb": 500,
            "census_cache_size_mb": 250,
            "cache_ttl_hours": 168,  # 7 days
            "http_pool_connections": 10,
            "http_pool_maxsize": 10,
            "http_timeout_seconds": 30,
            "batch_size_census": 50,
            "batch_size_geocoding": 100,
            "enable_memory_optimization": True,
            "enable_connection_pooling": True,
            "preset": "balanced"
        },
        PerformancePreset.MEMORY_EFFICIENT: {
            "network_cache_size_gb": 2,
            "geocoding_cache_size_mb": 100,
            "census_cache_size_mb": 50,
            "cache_ttl_hours": 720,  # 30 days
            "http_pool_connections": 5,
            "http_pool_maxsize": 5,
            "http_timeout_seconds": 45,
            "batch_size_census": 25,
            "batch_size_geocoding": 50,
            "enable_memory_optimization": True,
            "enable_connection_pooling": True,
            "preset": "memory_efficient"
        }
    }

    # Get base configuration
    config_dict = preset_configs[preset].copy()

    # Apply overrides
    config_dict.update(overrides)

    logger.info(f"Creating performance configuration with preset='{preset.value}'")

    return PerformanceConfig(**config_dict)
