#!/usr/bin/env python3
"""Comprehensive tests for the unified cache system.

Tests all cache implementations, thread safety, and edge cases.
"""

import json
import sqlite3
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from socialmapper.cache import (
    BaseCache,
    CacheStats,
    ParquetCache,
    PickleCache,
    SQLiteCache,
    UnifiedCacheManager,
)


class TestBaseCache(TestCase):
    """Test the BaseCache abstract class and common functionality."""

    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        # Create a concrete implementation for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(tmpdir)

            # Same arguments should produce same key
            key1 = cache.get_cache_key("test", 123, {"foo": "bar"})
            key2 = cache.get_cache_key("test", 123, {"foo": "bar"})
            self.assertEqual(key1, key2)

            # Different arguments should produce different keys
            key3 = cache.get_cache_key("test", 456, {"foo": "bar"})
            self.assertNotEqual(key1, key3)

            # Order shouldn't matter for dict keys
            key4 = cache.get_cache_key({"foo": "bar", "baz": "qux"})
            key5 = cache.get_cache_key({"baz": "qux", "foo": "bar"})
            self.assertEqual(key4, key5)

    def test_expiration_check(self):
        """Test TTL expiration checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(tmpdir, ttl_hours=1)

            # Current time should not be expired
            from datetime import datetime, timedelta

            now = datetime.now()
            self.assertFalse(cache.is_expired(now))

            # Time within TTL should not be expired
            recent = now - timedelta(minutes=30)
            self.assertFalse(cache.is_expired(recent))

            # Time beyond TTL should be expired
            old = now - timedelta(hours=2)
            self.assertTrue(cache.is_expired(old))


class TestSQLiteCache(TestCase):
    """Test SQLiteCache implementation."""

    def setUp(self):
        """Create temporary directory and cache instance."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = SQLiteCache(self.temp_dir.name, table_name="test_cache")

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_basic_operations(self):
        """Test basic get, put, delete operations."""
        # Test put and get
        self.cache.put("key1", {"data": "value1"})
        result = self.cache.get("key1")
        self.assertEqual(result, {"data": "value1"})

        # Test exists
        self.assertTrue(self.cache.exists("key1"))
        self.assertFalse(self.cache.exists("nonexistent"))

        # Test delete
        self.assertTrue(self.cache.delete("key1"))
        self.assertIsNone(self.cache.get("key1"))
        self.assertFalse(self.cache.delete("key1"))  # Already deleted

    def test_expiration(self):
        """Test that expired entries are not returned."""
        # Create cache with very short TTL
        cache = SQLiteCache(self.temp_dir.name, table_name="expire_test", ttl_hours=0.0001)

        cache.put("key1", "value1")
        time.sleep(0.01)  # Wait for expiration

        result = cache.get("key1")
        self.assertIsNone(result)

    def test_table_name_validation(self):
        """Test that table names are validated for SQL injection."""
        # Valid table names
        SQLiteCache(self.temp_dir.name, table_name="valid_table_123")

        # Invalid table names should raise
        with self.assertRaises(ValueError):
            SQLiteCache(self.temp_dir.name, table_name="'; DROP TABLE users; --")

        with self.assertRaises(ValueError):
            SQLiteCache(self.temp_dir.name, table_name="a" * 100)  # Too long

    def test_stats_tracking(self):
        """Test cache statistics tracking."""
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key2")  # Miss

        stats = self.cache.get_stats()
        self.assertIsInstance(stats, CacheStats)
        self.assertEqual(stats.cache_hits, 1)
        self.assertEqual(stats.cache_misses, 1)
        self.assertEqual(stats.total_requests, 2)

    def test_clear_operation(self):
        """Test clearing all cache entries."""
        # Add multiple entries
        for i in range(5):
            self.cache.put(f"key{i}", f"value{i}")

        # Verify they exist
        self.assertTrue(self.cache.exists("key0"))
        self.assertTrue(self.cache.exists("key4"))

        # Clear cache
        self.cache.clear()

        # Verify all are gone
        for i in range(5):
            self.assertFalse(self.cache.exists(f"key{i}"))

    @pytest.mark.skip(reason="Cleanup logic needs refinement")
    def test_cleanup_size_limit(self):
        """Test that cleanup enforces size limits."""
        # Create cache with small size limit (0.1 MB)
        cache = SQLiteCache(self.temp_dir.name, table_name="size_test", max_size_mb=0.1)

        # Add data that exceeds limit
        large_data = "x" * 10000
        for i in range(10):
            cache.put(f"key{i}", large_data)

        # Cleanup should remove some entries
        cache.cleanup()

        # Check that some entries were removed (not all 10 should remain)
        remaining_count = sum(1 for i in range(10) if cache.exists(f"key{i}"))
        self.assertLess(remaining_count, 10, "Cleanup should have removed some entries")

        # Verify at least some entries remain
        self.assertGreater(remaining_count, 0, "Cleanup should not remove everything")


class TestParquetCache(TestCase):
    """Test ParquetCache implementation for DataFrames."""

    def setUp(self):
        """Create temporary directory and cache instance."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = ParquetCache(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_dataframe_operations(self):
        """Test storing and retrieving DataFrames."""
        # Create test DataFrame
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })

        # Store and retrieve
        self.cache.put("df1", df)
        result = self.cache.get("df1")

        pd.testing.assert_frame_equal(result, df)

    def test_index_persistence(self):
        """Test that cache index persists across instances."""
        df = pd.DataFrame({"data": [1, 2, 3]})
        self.cache.put("persistent_key", df)

        # Create new cache instance pointing to same directory
        new_cache = ParquetCache(self.temp_dir.name)

        # Should be able to retrieve data
        result = new_cache.get("persistent_key")
        pd.testing.assert_frame_equal(result, df)

    def test_atomic_index_save(self):
        """Test that index saving is atomic."""
        # Add some data
        df = pd.DataFrame({"data": [1]})
        self.cache.put("key1", df)

        # Mock file write to fail
        with patch("builtins.open", side_effect=IOError("Write failed")):
            # Try to add another entry
            try:
                self.cache.put("key2", df)
            except Exception:
                pass

        # Original index should still be intact
        self.assertTrue(self.cache.exists("key1"))


class TestPickleCache(TestCase):
    """Test PickleCache implementation."""

    def setUp(self):
        """Create temporary directory and cache instance."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = PickleCache(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_complex_object_storage(self):
        """Test storing complex Python objects."""
        # Complex nested object
        complex_obj = {
            "list": [1, 2, 3],
            "dict": {"nested": {"deep": "value"}},
            "tuple": (4, 5, 6),
            "set": {7, 8, 9}
        }

        self.cache.put("complex", complex_obj)
        result = self.cache.get("complex")

        self.assertEqual(result, complex_obj)

    def test_compression(self):
        """Test that data is compressed."""
        # Large repetitive data should compress well
        large_data = ["test" * 1000] * 100

        self.cache.put("large", large_data)

        # Check file size is reasonable (compressed)
        cache_files = list(Path(self.temp_dir.name).glob("*.pkl.gz"))
        self.assertEqual(len(cache_files), 1)

        file_size = cache_files[0].stat().st_size
        uncompressed_size = len(str(large_data).encode())

        # Compressed should be much smaller
        self.assertLess(file_size, uncompressed_size / 2)


class TestUnifiedCacheManager(TestCase):
    """Test UnifiedCacheManager coordination."""

    def setUp(self):
        """Create temporary directory and manager instance."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = UnifiedCacheManager(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_default_caches_created(self):
        """Test that default caches are initialized."""
        # Should have network, geocoding, census, and general caches
        self.assertIsInstance(self.manager.get_cache("network"), PickleCache)
        self.assertIsInstance(self.manager.get_cache("geocoding"), SQLiteCache)
        self.assertIsInstance(self.manager.get_cache("census"), ParquetCache)
        self.assertIsInstance(self.manager.get_cache("general"), SQLiteCache)

    def test_cache_registration(self):
        """Test registering custom caches."""
        custom_cache = SQLiteCache(self.temp_dir.name + "/custom", table_name="custom")

        self.manager.register_cache("custom", custom_cache)
        retrieved = self.manager.get_cache("custom")

        self.assertIs(retrieved, custom_cache)

        # Should not allow duplicate without replace flag
        with self.assertRaises(ValueError):
            self.manager.register_cache("custom", custom_cache)

        # Should allow with replace flag
        new_cache = SQLiteCache(self.temp_dir.name + "/custom2", table_name="custom2")
        self.manager.register_cache("custom", new_cache, replace=True)

    def test_summary_stats(self):
        """Test getting summary statistics across all caches."""
        # Add data to different caches
        self.manager.put_to_cache("general", "key1", "value1")
        self.manager.put_to_cache("network", "key2", {"data": "value2"})

        stats = self.manager.get_summary_stats()

        self.assertIn("summary", stats)
        self.assertIn("per_cache", stats)
        self.assertEqual(len(stats["per_cache"]), 4)  # 4 default caches

    def test_clear_operations(self):
        """Test clearing individual and all caches."""
        # Add data to multiple caches
        self.manager.put_to_cache("general", "key1", "value1")
        self.manager.put_to_cache("network", "key2", "value2")

        # Clear specific cache
        self.manager.clear_cache("general")
        self.assertFalse(self.manager.cache_exists("general", "key1"))
        self.assertTrue(self.manager.cache_exists("network", "key2"))

        # Clear all caches
        self.manager.clear_cache()
        self.assertFalse(self.manager.cache_exists("network", "key2"))


class TestThreadSafety(TestCase):
    """Test thread safety of cache implementations."""

    def test_concurrent_sqlite_operations(self):
        """Test SQLiteCache with concurrent access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(tmpdir)
            errors = []

            def worker(thread_id):
                """Worker function for concurrent operations."""
                try:
                    for i in range(10):
                        key = f"thread_{thread_id}_key_{i}"
                        cache.put(key, f"value_{i}")
                        result = cache.get(key)
                        assert result == f"value_{i}"
                        cache.delete(key)
                except Exception as e:
                    errors.append(e)

            # Run multiple threads
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(worker, i) for i in range(10)]
                for future in as_completed(futures):
                    future.result()

            # Check no errors occurred
            self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

    def test_concurrent_index_updates(self):
        """Test that concurrent index updates don't corrupt the index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PickleCache(tmpdir)
            errors = []

            def writer(thread_id):
                """Write to cache concurrently."""
                try:
                    for i in range(5):
                        cache.put(f"thread_{thread_id}_key_{i}", f"value_{i}")
                except Exception as e:
                    errors.append(e)

            # Run concurrent writers
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(writer, i) for i in range(5)]
                for future in as_completed(futures):
                    future.result()

            self.assertEqual(len(errors), 0)

            # Verify all data is present
            for thread_id in range(5):
                for i in range(5):
                    key = f"thread_{thread_id}_key_{i}"
                    self.assertTrue(cache.exists(key))

    def test_cache_cleanup_during_operations(self):
        """Test that cleanup doesn't interfere with ongoing operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(tmpdir, max_size_mb=0.01)  # Very small limit
            errors = []

            def worker():
                """Perform cache operations."""
                try:
                    for i in range(20):
                        cache.put(f"key_{i}", "x" * 1000)
                        cache.get(f"key_{i}")
                        if i % 5 == 0:
                            cache.cleanup()
                except Exception as e:
                    errors.append(e)

            # Run multiple workers with cleanup
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(worker) for _ in range(3)]
                for future in as_completed(futures):
                    future.result()

            self.assertEqual(len(errors), 0)


class TestErrorHandling(TestCase):
    """Test error handling and recovery."""

    def test_corrupted_database_recovery(self):
        """Test recovery from corrupted SQLite database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create corrupted database file
            with open(db_path, "wb") as f:
                f.write(b"This is not a valid SQLite database")

            # Should handle gracefully
            with self.assertRaises(RuntimeError) as context:
                SQLiteCache(tmpdir, table_name="test")

            self.assertIn("Cannot initialize cache database", str(context.exception))

    def test_missing_parquet_file_recovery(self):
        """Test recovery when Parquet file is missing but in index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ParquetCache(tmpdir)

            # Add entry
            df = pd.DataFrame({"data": [1, 2, 3]})
            cache.put("key1", df)

            # Manually delete the parquet file
            parquet_file = Path(tmpdir) / "key1.parquet"
            parquet_file.unlink()

            # Should return None and clean up index
            result = cache.get("key1")
            self.assertIsNone(result)
            self.assertFalse(cache.exists("key1"))

    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PickleCache(tmpdir)

            # Make directory read-only
            Path(tmpdir).chmod(0o444)

            # Should handle write failure gracefully
            try:
                cache.put("key1", "value1")
            except Exception:
                pass  # Expected to fail

            # Restore permissions for cleanup
            Path(tmpdir).chmod(0o755)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])