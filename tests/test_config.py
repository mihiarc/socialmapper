"""Tests for configuration modules."""

import pytest
from socialmapper.config.optimization import (
    OptimizationConfig, 
    DistanceConfig, 
    IsochroneConfig, 
    MemoryConfig,
    IOConfig
)


class TestOptimizationConfig:
    """Test OptimizationConfig class."""

    def test_default_config(self):
        """Test default optimization configuration."""
        config = OptimizationConfig()
        
        # Check sub-configs exist
        assert isinstance(config.distance, DistanceConfig)
        assert isinstance(config.isochrone, IsochroneConfig)
        assert isinstance(config.memory, MemoryConfig)
        assert isinstance(config.io, IOConfig)
        
        # Check some default values
        assert config.distance.engine == "vectorized_numba"
        assert config.isochrone.enable_caching is True
        assert config.memory.enable_monitoring is True

    def test_custom_distance_config(self):
        """Test custom distance configuration."""
        distance_config = DistanceConfig(
            engine="sklearn",
            chunk_size=10000,
            enable_jit=False
        )
        
        config = OptimizationConfig(distance=distance_config)
        
        assert config.distance.engine == "sklearn"
        assert config.distance.chunk_size == 10000
        assert config.distance.enable_jit is False

    def test_isochrone_config(self):
        """Test isochrone configuration."""
        isochrone_config = IsochroneConfig(
            clustering_algorithm="kmeans",
            max_cluster_radius_km=20.0,
            enable_caching=False
        )
        
        assert isochrone_config.clustering_algorithm == "kmeans"
        assert isochrone_config.max_cluster_radius_km == 20.0
        assert isochrone_config.enable_caching is False

    def test_memory_config(self):
        """Test memory configuration."""
        memory_config = MemoryConfig(
            enable_monitoring=False,
            small_dataset_mb=100.0,
            max_concurrent_io=8
        )
        
        assert memory_config.enable_monitoring is False
        assert memory_config.small_dataset_mb == 100.0
        assert memory_config.max_concurrent_io == 8

    def test_io_config(self):
        """Test IO configuration."""
        io_config = IOConfig(
            file_reader="polars",
            enable_compression=True,
            parquet_engine="pyarrow"
        )
        
        assert io_config.file_reader == "polars"
        assert io_config.enable_compression is True
        assert io_config.parquet_engine == "pyarrow"

    def test_optimization_config_defaults(self):
        """Test optimization config has sensible defaults."""
        config = OptimizationConfig()
        
        # Test defaults exist and are reasonable
        assert config.distance.parallel_processes >= 0
        assert config.isochrone.max_cache_size_gb > 0
        assert config.memory.small_dataset_mb > 0
        assert config.io.batch_size > 0