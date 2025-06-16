#!/usr/bin/env python3
"""Configuration Schemas for SocialMapper Optimization.

This module provides clean dataclass-based configuration schemas for all
optimization settings, with no utility functions or system detection logic.
"""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DistanceConfig:
    """Configuration for distance calculation optimization."""

    # Distance engine settings
    engine: str = "vectorized_numba"
    parallel_processes: int = 0  # 0 = auto-detect
    chunk_size: int = 5000
    enable_jit: bool = True


@dataclass
class IsochroneConfig:
    """Configuration for isochrone generation optimization."""

    # Clustering settings
    clustering_algorithm: str = "dbscan"
    max_cluster_radius_km: float = 15.0
    min_cluster_size: int = 2
    auto_clustering_threshold: int = 5

    # Caching settings
    enable_caching: bool = True
    cache_dir: str = "cache/networks"
    max_cache_size_gb: float = 5.0
    cache_compression_level: int = 6

    # Concurrent processing settings
    max_concurrent_downloads: int = 8
    max_concurrent_isochrones: int | None = None
    auto_concurrent_threshold: int = 3
    enable_resource_monitoring: bool = True


@dataclass
class MemoryConfig:
    """Configuration for memory management optimization."""

    # Memory management
    max_memory_gb: float = 3.0
    streaming_batch_size: int = 1000
    aggressive_cleanup: bool = True
    enable_memory_monitoring: bool = True
    memory_warning_threshold: float = 0.85
    cleanup_threshold_mb: float = 1024.0


@dataclass
class IOConfig:
    """Configuration for I/O optimization."""

    # Modern data formats
    default_format: str = "parquet"
    compression: str = "snappy"
    use_polars: bool = True
    enable_arrow: bool = True
    parallel_io: bool = True

    # Streaming configuration
    streaming_batch_size: int = 1000
    enable_streaming: bool = True
    stream_threshold_mb: float = 100.0

    # Memory management
    max_memory_per_operation_mb: float = 1024.0
    enable_memory_monitoring: bool = True
    aggressive_cleanup: bool = True

    # Format-specific settings
    parquet_row_group_size: int = 50000
    parquet_compression_level: int = 6
    arrow_batch_size: int = 10000

    def get_optimal_format_for_size(self, size_mb: float) -> str:
        """Get optimal format based on data size."""
        if size_mb > self.stream_threshold_mb:
            return "streaming_parquet"
        elif size_mb > 10.0:
            return "parquet"
        else:
            return "memory"

    def should_use_streaming(self, size_mb: float) -> bool:
        """Determine if streaming should be used for given data size."""
        return self.enable_streaming and size_mb > self.stream_threshold_mb


@dataclass
class OptimizationConfig:
    """Master configuration for all SocialMapper optimizations."""

    # Component configurations
    distance: DistanceConfig = field(default_factory=DistanceConfig)
    isochrone: IsochroneConfig = field(default_factory=IsochroneConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    io: IOConfig = field(default_factory=IOConfig)

    # Global settings
    enable_performance_monitoring: bool = True
    log_level: str = "INFO"
    enable_progress_bars: bool = True

    @classmethod
    def from_environment(cls) -> "OptimizationConfig":
        """Create configuration from environment variables."""
        config = cls()

        # Distance settings
        if os.getenv("SOCIALMAPPER_PARALLEL_PROCESSES"):
            config.distance.parallel_processes = int(os.getenv("SOCIALMAPPER_PARALLEL_PROCESSES"))

        if os.getenv("SOCIALMAPPER_CHUNK_SIZE"):
            config.distance.chunk_size = int(os.getenv("SOCIALMAPPER_CHUNK_SIZE"))

        # Isochrone settings
        if os.getenv("SOCIALMAPPER_MAX_CLUSTER_RADIUS"):
            config.isochrone.max_cluster_radius_km = float(
                os.getenv("SOCIALMAPPER_MAX_CLUSTER_RADIUS")
            )

        if os.getenv("SOCIALMAPPER_CACHE_SIZE_GB"):
            config.isochrone.max_cache_size_gb = float(os.getenv("SOCIALMAPPER_CACHE_SIZE_GB"))

        if os.getenv("SOCIALMAPPER_MAX_WORKERS"):
            config.isochrone.max_concurrent_downloads = int(os.getenv("SOCIALMAPPER_MAX_WORKERS"))

        # Memory settings
        if os.getenv("SOCIALMAPPER_MAX_MEMORY_GB"):
            config.memory.max_memory_gb = float(os.getenv("SOCIALMAPPER_MAX_MEMORY_GB"))

        # Global settings
        if os.getenv("SOCIALMAPPER_LOG_LEVEL"):
            config.log_level = os.getenv("SOCIALMAPPER_LOG_LEVEL")

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "distance": {
                "engine": self.distance.engine,
                "parallel_processes": self.distance.parallel_processes,
                "chunk_size": self.distance.chunk_size,
                "enable_jit": self.distance.enable_jit,
            },
            "isochrone": {
                "clustering_algorithm": self.isochrone.clustering_algorithm,
                "max_cluster_radius_km": self.isochrone.max_cluster_radius_km,
                "min_cluster_size": self.isochrone.min_cluster_size,
                "enable_caching": self.isochrone.enable_caching,
                "cache_dir": self.isochrone.cache_dir,
                "max_cache_size_gb": self.isochrone.max_cache_size_gb,
                "max_concurrent_downloads": self.isochrone.max_concurrent_downloads,
                "max_concurrent_isochrones": self.isochrone.max_concurrent_isochrones,
            },
            "memory": {
                "max_memory_gb": self.memory.max_memory_gb,
                "streaming_batch_size": self.memory.streaming_batch_size,
                "aggressive_cleanup": self.memory.aggressive_cleanup,
            },
            "io": {
                "default_format": self.io.default_format,
                "compression": self.io.compression,
                "use_polars": self.io.use_polars,
                "enable_arrow": self.io.enable_arrow,
            },
            "global": {
                "enable_performance_monitoring": self.enable_performance_monitoring,
                "log_level": self.log_level,
                "enable_progress_bars": self.enable_progress_bars,
            },
        }
