#!/usr/bin/env python3
"""Configuration Presets for SocialMapper.

This module provides predefined configuration presets for different
use cases and system environments.
"""

import multiprocessing as mp
from typing import TYPE_CHECKING

from .system_detection import (
    get_performance_tier,
    get_recommended_cache_size_gb,
    get_recommended_memory_limit_gb,
)

if TYPE_CHECKING:
    from ..config.optimization import OptimizationConfig


class ConfigPresets:
    """Predefined performance configurations for different scenarios."""

    @staticmethod
    def for_development() -> "OptimizationConfig":
        """Configuration optimized for development and testing."""
        from ..config.optimization import OptimizationConfig

        config = OptimizationConfig()

        # Conservative settings for development
        config.isochrone.max_concurrent_downloads = 2
        config.isochrone.max_concurrent_isochrones = 2
        config.isochrone.max_cache_size_gb = 1.0
        config.memory.max_memory_gb = 1.0
        config.log_level = "DEBUG"
        config.enable_progress_bars = True

        return config

    @staticmethod
    def for_production() -> "OptimizationConfig":
        """Configuration optimized for production workloads."""
        from ..config.optimization import OptimizationConfig

        config = OptimizationConfig()

        # Aggressive settings for production
        config.isochrone.max_concurrent_downloads = 16
        config.isochrone.max_concurrent_isochrones = mp.cpu_count()
        config.isochrone.max_cache_size_gb = get_recommended_cache_size_gb()
        config.memory.max_memory_gb = get_recommended_memory_limit_gb()
        config.memory.aggressive_cleanup = True
        config.log_level = "INFO"

        return config

    @staticmethod
    def for_memory_constrained() -> "OptimizationConfig":
        """Configuration for systems with limited memory."""
        from ..config.optimization import OptimizationConfig

        config = OptimizationConfig()

        # Conservative settings for low-memory systems
        config.isochrone.max_concurrent_downloads = 2
        config.isochrone.max_concurrent_isochrones = 2
        config.isochrone.max_cache_size_gb = 0.5
        config.memory.max_memory_gb = 1.0
        config.memory.streaming_batch_size = 100
        config.memory.aggressive_cleanup = True
        config.io.streaming_batch_size = 100
        config.io.stream_threshold_mb = 50.0  # Stream smaller files

        return config

    @staticmethod
    def for_high_performance() -> "OptimizationConfig":
        """Configuration for maximum performance on powerful systems."""
        from ..config.optimization import OptimizationConfig

        config = OptimizationConfig()

        # Aggressive settings for powerful systems
        config.distance.chunk_size = 10000
        config.isochrone.max_concurrent_downloads = 32
        config.isochrone.max_concurrent_isochrones = mp.cpu_count() * 2
        config.isochrone.max_cache_size_gb = 20.0
        config.memory.max_memory_gb = 16.0
        config.io.streaming_batch_size = 2000
        config.io.stream_threshold_mb = 500.0  # Only stream very large files

        return config

    @staticmethod
    def for_benchmarking() -> "OptimizationConfig":
        """Configuration optimized for benchmarking and testing."""
        from ..config.optimization import OptimizationConfig

        config = OptimizationConfig()

        # Maximum performance settings for benchmarking
        config.distance.chunk_size = 10000
        config.isochrone.max_concurrent_downloads = 64
        config.isochrone.max_concurrent_isochrones = mp.cpu_count() * 4
        config.isochrone.max_cache_size_gb = 50.0
        config.memory.max_memory_gb = 32.0
        config.enable_progress_bars = False  # Reduce noise in benchmarks
        config.log_level = "CRITICAL"

        return config

    @staticmethod
    def auto_detect() -> "OptimizationConfig":
        """Automatically detect optimal configuration based on system capabilities."""
        from ..config.optimization import OptimizationConfig

        tier = get_performance_tier()

        if tier == "enterprise":
            return ConfigPresets.for_high_performance()
        elif tier == "high":
            return ConfigPresets.for_production()
        elif tier == "medium":
            # Balanced configuration for medium systems
            config = OptimizationConfig()
            config.isochrone.max_concurrent_downloads = 8
            config.isochrone.max_concurrent_isochrones = mp.cpu_count()
            config.isochrone.max_cache_size_gb = get_recommended_cache_size_gb()
            config.memory.max_memory_gb = get_recommended_memory_limit_gb()
            return config
        else:  # low tier
            return ConfigPresets.for_memory_constrained()

    @staticmethod
    def for_cloud_instance(instance_type: str = "medium") -> "OptimizationConfig":
        """Configuration optimized for cloud instances."""
        from ..config.optimization import OptimizationConfig

        if instance_type == "small":
            # t2.small, t3.small equivalent
            config = OptimizationConfig()
            config.isochrone.max_concurrent_downloads = 2
            config.isochrone.max_concurrent_isochrones = 1
            config.isochrone.max_cache_size_gb = 0.5
            config.memory.max_memory_gb = 1.0
        elif instance_type == "large":
            # t2.large, t3.large equivalent
            config = OptimizationConfig()
            config.isochrone.max_concurrent_downloads = 16
            config.isochrone.max_concurrent_isochrones = 8
            config.isochrone.max_cache_size_gb = 10.0
            config.memory.max_memory_gb = 6.0
        elif instance_type == "xlarge":
            # t2.xlarge, t3.xlarge equivalent
            return ConfigPresets.for_high_performance()
        else:  # medium
            # t2.medium, t3.medium equivalent
            config = OptimizationConfig()
            config.isochrone.max_concurrent_downloads = 8
            config.isochrone.max_concurrent_isochrones = 4
            config.isochrone.max_cache_size_gb = 2.0
            config.memory.max_memory_gb = 3.0

        return config

    @staticmethod
    def for_continuous_integration() -> "OptimizationConfig":
        """Configuration optimized for CI/CD environments."""
        from ..config.optimization import OptimizationConfig

        config = OptimizationConfig()

        # Conservative settings for CI environments
        config.isochrone.max_concurrent_downloads = 2
        config.isochrone.max_concurrent_isochrones = 2
        config.isochrone.max_cache_size_gb = 0.5
        config.memory.max_memory_gb = 1.0
        config.enable_progress_bars = False  # Reduce noise in CI logs
        config.log_level = "WARNING"
        config.memory.aggressive_cleanup = True

        return config

    @staticmethod
    def for_jupyter_notebook() -> "OptimizationConfig":
        """Configuration optimized for Jupyter notebook environments."""
        from ..config.optimization import OptimizationConfig

        config = OptimizationConfig()

        # Balanced settings for interactive environments
        config.isochrone.max_concurrent_downloads = 4
        config.isochrone.max_concurrent_isochrones = 4
        config.isochrone.max_cache_size_gb = 2.0
        config.memory.max_memory_gb = 2.0
        config.enable_progress_bars = True  # Nice in notebooks
        config.log_level = "INFO"

        return config


# Convenience functions for common patterns
def get_development_config() -> "OptimizationConfig":
    """Get development configuration."""
    return ConfigPresets.for_development()


def get_production_config() -> "OptimizationConfig":
    """Get production configuration."""
    return ConfigPresets.for_production()


def get_auto_config() -> "OptimizationConfig":
    """Get automatically detected configuration."""
    return ConfigPresets.auto_detect()


def get_config_for_environment(env: str = "auto") -> "OptimizationConfig":
    """Get configuration for a specific environment.

    Args:
        env: Environment type ("auto", "development", "production", "ci", "jupyter",
             "cloud-small", "cloud-medium", "cloud-large", "benchmark")

    Returns:
        Optimized configuration for the environment
    """
    env = env.lower()

    if env == "auto":
        return ConfigPresets.auto_detect()
    elif env == "development" or env == "dev":
        return ConfigPresets.for_development()
    elif env == "production" or env == "prod":
        return ConfigPresets.for_production()
    elif env == "ci" or env == "continuous-integration":
        return ConfigPresets.for_continuous_integration()
    elif env == "jupyter" or env == "notebook":
        return ConfigPresets.for_jupyter_notebook()
    elif env == "benchmark" or env == "benchmarking":
        return ConfigPresets.for_benchmarking()
    elif env.startswith("cloud-"):
        instance_type = env.split("-", 1)[1]
        return ConfigPresets.for_cloud_instance(instance_type)
    else:
        # Default to auto-detection
        return ConfigPresets.auto_detect()
