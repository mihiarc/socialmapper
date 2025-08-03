"""Tests for configuration modules."""

from socialmapper.config.optimization import (
    DistanceConfig,
    IOConfig,
    IsochroneConfig,
    MemoryConfig,
    OptimizationConfig,
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
        assert config.memory.enable_memory_monitoring is True

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
            enable_memory_monitoring=False,
            max_memory_gb=4.0,
            streaming_batch_size=2000
        )

        assert memory_config.enable_memory_monitoring is False
        assert memory_config.max_memory_gb == 4.0
        assert memory_config.streaming_batch_size == 2000

    def test_io_config(self):
        """Test IO configuration."""
        io_config = IOConfig(
            default_format="parquet",
            use_polars=True,
            enable_arrow=True
        )

        assert io_config.default_format == "parquet"
        assert io_config.use_polars is True
        assert io_config.enable_arrow is True

    def test_optimization_config_defaults(self):
        """Test optimization config has sensible defaults."""
        config = OptimizationConfig()

        # Test defaults exist and are reasonable
        assert config.distance.parallel_processes >= 0
        assert config.isochrone.max_cache_size_gb > 0
        assert config.memory.max_memory_gb > 0
        assert config.io.streaming_batch_size > 0
