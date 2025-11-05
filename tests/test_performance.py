"""Performance optimization tests for SocialMapper.

Tests for caching, connection pooling, memory optimization,
and batch processing functionality.
"""

import time

import pandas as pd
import pytest

from socialmapper.performance import (
    CacheManager,
    PerformanceConfig,
    PerformancePreset,
    get_http_session,
    get_performance_config,
    init_connection_pool,
    memory_efficient_iterator,
    optimize_dataframe_memory,
)
from socialmapper.performance.batch import BatchCensusDataFetcher
from socialmapper.performance.memory import MemoryMonitor, get_memory_stats


class TestPerformanceConfig:
    """Tests for performance configuration."""

    def test_default_config(self):
        """Test default balanced configuration."""
        config = get_performance_config()
        assert config.preset == "balanced"
        assert config.network_cache_size_gb == 5
        assert config.cache_ttl_hours == 168

    def test_fast_preset(self):
        """Test fast preset configuration."""
        config = get_performance_config(preset=PerformancePreset.FAST)
        assert config.preset == "fast"
        assert config.network_cache_size_gb == 10
        assert config.cache_ttl_hours == 24
        assert config.http_pool_connections == 20

    def test_memory_efficient_preset(self):
        """Test memory efficient preset configuration."""
        config = get_performance_config(preset="memory_efficient")
        assert config.preset == "memory_efficient"
        assert config.network_cache_size_gb == 2
        assert config.cache_ttl_hours == 720
        assert config.http_pool_connections == 5

    def test_config_overrides(self):
        """Test configuration with overrides."""
        config = get_performance_config(
            preset="balanced",
            cache_ttl_hours=48,
            http_pool_connections=15
        )
        assert config.cache_ttl_hours == 48
        assert config.http_pool_connections == 15
        # Other values should remain from preset
        assert config.network_cache_size_gb == 5

    def test_invalid_preset(self):
        """Test invalid preset raises error."""
        with pytest.raises(ValueError, match="Invalid preset"):
            get_performance_config(preset="invalid_preset")


class TestCacheManager:
    """Tests for unified cache manager."""

    def test_cache_manager_initialization(self):
        """Test cache manager initializes correctly."""
        config = get_performance_config(preset="balanced")
        cache = CacheManager(config)

        assert cache.config == config
        assert cache._census_cache is not None
        assert cache._geocoding_cache is not None

        cache.close()

    def test_census_caching(self):
        """Test Census data caching."""
        cache = CacheManager()

        # Cache some data
        test_data = {"B01003_001E": 2543, "B19013_001E": 65000}
        cache.set_census("test_geoid_123", test_data, ttl_hours=1)

        # Retrieve from cache
        cached = cache.get_census("test_geoid_123")
        assert cached == test_data

        # Non-existent key
        assert cache.get_census("nonexistent") is None

        cache.close()

    def test_geocoding_caching(self):
        """Test geocoding result caching."""
        cache = CacheManager()

        # Cache geocoding result
        test_result = {"lat": 47.6062, "lon": -122.3321}
        cache.set_geocoding("seattle_wa", test_result, ttl_hours=720)

        # Retrieve from cache
        cached = cache.get_geocoding("seattle_wa")
        assert cached == test_result

        cache.close()

    def test_cache_decorator_census(self):
        """Test census data caching decorator."""
        cache = CacheManager()
        call_count = 0

        @cache.cache_census_data(ttl_hours=1)
        def expensive_fetch(geoid, variables):
            nonlocal call_count
            call_count += 1
            return {var: 100 for var in variables}

        # First call should execute function
        result1 = expensive_fetch("060370001001", ["B01003_001E"])
        assert call_count == 1
        assert result1 == {"B01003_001E": 100}

        # Second call should use cache
        result2 = expensive_fetch("060370001001", ["B01003_001E"])
        assert call_count == 1  # Not incremented
        assert result2 == result1

        cache.close()

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheManager()

        # Clear cache first to ensure clean state
        cache.clear_all()

        # Add some data
        for i in range(10):
            cache.set_census(f"geoid_{i}", {"data": i})
            cache.set_geocoding(f"address_{i}", {"lat": i, "lon": i})

        stats = cache.get_stats()

        assert "census" in stats
        assert "geocoding" in stats
        assert stats["census"]["count"] == 10
        assert stats["geocoding"]["count"] == 10

        cache.close()

    def test_clear_caches(self):
        """Test clearing caches."""
        cache = CacheManager()

        # Add data
        cache.set_census("test", {"data": "value"})
        cache.set_geocoding("test", {"lat": 0, "lon": 0})

        # Clear census cache
        cache.clear_census()
        assert cache.get_census("test") is None
        assert cache.get_geocoding("test") is not None

        # Clear all
        cache.set_census("test", {"data": "value"})
        cache.clear_all()
        assert cache.get_census("test") is None
        assert cache.get_geocoding("test") is None

        cache.close()


class TestConnectionPooling:
    """Tests for HTTP connection pooling."""

    def test_connection_pool_initialization(self):
        """Test connection pool initializes correctly."""
        config = get_performance_config(preset="fast")
        pool = init_connection_pool(config)

        assert pool is not None
        assert pool.config == config

        session = pool.get_session()
        assert session is not None

        pool.close()

    def test_get_http_session(self):
        """Test getting global HTTP session."""
        session1 = get_http_session()
        session2 = get_http_session()

        # Should return same instance
        assert session1 is session2

    @pytest.mark.external
    def test_session_makes_requests(self):
        """Test session can make actual requests."""
        session = get_http_session()

        # Simple request to check connectivity
        response = session.get("https://httpbin.org/get", timeout=10)
        assert response.status_code == 200


class TestMemoryOptimization:
    """Tests for memory optimization utilities."""

    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        stats = get_memory_stats()

        assert "used_mb" in stats
        assert "available_mb" in stats
        assert "percent" in stats
        assert "total_mb" in stats

        assert stats["used_mb"] > 0
        assert stats["total_mb"] > 0

    def test_optimize_dataframe_memory(self):
        """Test DataFrame memory optimization."""
        # Create DataFrame with inefficient dtypes
        df = pd.DataFrame({
            "id": range(1000),
            "value": [1.0] * 1000,
            "category": ["A"] * 500 + ["B"] * 500
        })

        initial_memory = df.memory_usage(deep=True).sum()

        # Optimize
        df_optimized = optimize_dataframe_memory(df)

        final_memory = df_optimized.memory_usage(deep=True).sum()

        # Memory should be reduced
        assert final_memory < initial_memory

        # Data should be preserved
        assert len(df_optimized) == len(df)
        assert list(df_optimized.columns) == list(df.columns)

    def test_memory_efficient_iterator(self):
        """Test memory-efficient iterator."""
        data = list(range(1000))
        chunk_size = 100

        chunks = list(memory_efficient_iterator(data, chunk_size))

        assert len(chunks) == 10
        assert len(chunks[0]) == chunk_size
        assert chunks[0] == list(range(100))

    def test_memory_monitor(self):
        """Test memory monitoring context manager."""
        with MemoryMonitor("test operation") as monitor:
            # Allocate some memory
            large_list = [0] * 1000000

        # Monitor should have tracked memory change
        assert hasattr(monitor, "memory_delta_mb")


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Benchmark tests for performance optimizations."""

    def test_cache_performance(self):
        """Benchmark caching performance."""
        cache = CacheManager()

        # Measure cache write performance
        start = time.time()
        for i in range(100):
            cache.set_census(f"key_{i}", {"data": i})
        write_time = time.time() - start

        # Measure cache read performance
        start = time.time()
        for i in range(100):
            cache.get_census(f"key_{i}")
        read_time = time.time() - start

        print(f"\nCache write time: {write_time:.4f}s")
        print(f"Cache read time: {read_time:.4f}s")

        # Reads should be fast
        assert read_time < 1.0

        cache.close()

    def test_batch_vs_individual_fetching(self):
        """Compare batch vs individual fetching performance."""
        # Note: This test requires actual API calls
        # Skip if API keys not available
        import os
        if not os.getenv("CENSUS_API_KEY"):
            pytest.skip("Census API key not available")

        geoids = [
            "060370001001",
            "060370001002",
            "060370001003"
        ]
        variables = ["B01003_001E"]

        # Time batch fetching
        fetcher = BatchCensusDataFetcher()
        start = time.time()
        batch_results = fetcher.fetch_batch(geoids, variables, year=2023)
        batch_time = time.time() - start

        print(f"\nBatch fetch time: {batch_time:.4f}s")
        print(f"Results count: {len(batch_results)}")

        # Should complete reasonably fast
        assert batch_time < 10.0
        assert len(batch_results) > 0


class TestBatchProcessing:
    """Tests for batch processing utilities."""

    def test_batch_census_fetcher_initialization(self):
        """Test batch Census fetcher initialization."""
        config = get_performance_config(preset="balanced")
        fetcher = BatchCensusDataFetcher(config=config)

        assert fetcher.config == config
        assert fetcher.cache is not None
        assert fetcher.session is not None

    def test_cache_key_generation(self):
        """Test cache key generation."""
        fetcher = BatchCensusDataFetcher()

        key1 = fetcher._make_cache_key(
            "060370001001",
            ["B01003_001E", "B19013_001E"],
            2023
        )
        key2 = fetcher._make_cache_key(
            "060370001001",
            ["B19013_001E", "B01003_001E"],  # Different order
            2023
        )

        # Same variables in different order should produce same key
        assert key1 == key2

        # Different GEOID should produce different key
        key3 = fetcher._make_cache_key(
            "060370001002",
            ["B01003_001E", "B19013_001E"],
            2023
        )
        assert key1 != key3
