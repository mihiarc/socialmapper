"""Tests for cache manager module."""

from pathlib import Path

from socialmapper.cache_manager import (
    CacheManager,
    cleanup_expired_cache_entries,
    clear_all_caches,
    clear_census_cache,
    clear_geocoding_cache,
    get_cache_statistics,
)


class TestCacheStatistics:
    """Test cache statistics functions."""

    def test_get_cache_statistics_returns_dict(self):
        """Test that get_cache_statistics returns a dictionary."""
        stats = get_cache_statistics()

        assert isinstance(stats, dict)
        assert "summary" in stats
        assert "network_cache" in stats
        assert "geocoding_cache" in stats
        assert "census_cache" in stats
        assert "general_cache" in stats

        # Check summary has required fields
        assert "total_size_mb" in stats["summary"]
        assert "total_items" in stats["summary"]

    def test_cache_statistics_structure(self):
        """Test the structure of cache statistics."""
        stats = get_cache_statistics()

        # Each cache type should have standard fields
        for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
            cache_stats = stats[cache_type]
            assert isinstance(cache_stats, dict)
            # These fields should exist even if values are 0
            assert "size_mb" in cache_stats
            assert "item_count" in cache_stats
            assert "status" in cache_stats
            assert "location" in cache_stats


class TestCacheClearing:
    """Test cache clearing functions."""

    def test_clear_geocoding_cache_returns_dict(self):
        """Test that clear_geocoding_cache returns a result dict."""
        result = clear_geocoding_cache()

        assert isinstance(result, dict)
        assert "success" in result
        assert isinstance(result["success"], bool)

        if result["success"]:
            assert "cleared_items" in result
            assert "cleared_size_mb" in result
        else:
            assert "error" in result

    def test_clear_census_cache_returns_dict(self):
        """Test that clear_census_cache returns a result dict."""
        result = clear_census_cache()

        assert isinstance(result, dict)
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_clear_all_caches_returns_summary(self):
        """Test that clear_all_caches returns a summary."""
        result = clear_all_caches()

        assert isinstance(result, dict)
        assert "summary" in result
        assert "success" in result["summary"]
        assert "total_cleared_mb" in result["summary"]

        # Should have results for each cache type
        expected_caches = ["geocoding", "census", "network", "general"]
        for cache_type in expected_caches:
            assert cache_type in result


class TestCacheManager:
    """Test CacheManager class."""

    def test_cache_manager_init(self):
        """Test CacheManager initialization."""
        manager = CacheManager()

        assert manager is not None
        assert hasattr(manager, 'cache_base_dir')
        assert hasattr(manager, 'geocoding_cache_dir')
        assert hasattr(manager, 'network_cache_dir')
        assert hasattr(manager, 'census_cache_dir')

    def test_cache_manager_directories(self):
        """Test cache directory paths."""
        manager = CacheManager()

        assert manager.cache_base_dir == Path("cache")
        assert manager.geocoding_cache_dir == Path("cache/geocoding")
        assert manager.network_cache_dir == Path("cache/networks")
        assert manager.census_cache_dir == Path("cache/census")

    def test_cache_manager_has_statistics_method(self):
        """Test that CacheManager has get_cache_statistics method."""
        manager = CacheManager()
        assert hasattr(manager, 'get_cache_statistics')
        assert callable(manager.get_cache_statistics)


class TestCacheExpiration:
    """Test cache expiration functionality."""

    def test_cleanup_expired_entries(self):
        """Test cleanup of expired cache entries."""
        result = cleanup_expired_cache_entries()

        assert isinstance(result, dict)

        # Should have results for different cache types
        expected_components = ["geocoding", "census", "network"]
        for component in expected_components:
            assert component in result
            assert "success" in result[component]
            assert isinstance(result[component]["success"], bool)
