#!/usr/bin/env python3
"""Concrete cache implementations.

This module provides different cache backend implementations
that all conform to the BaseCache interface.
"""

import gzip
import json
import logging
import pickle
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .base import BaseCache, CacheStats

logger = logging.getLogger(__name__)


class SQLiteCache(BaseCache[Any]):
    """SQLite-based cache implementation.

    This cache uses SQLite for indexing and storage, providing
    fast lookups and good performance for moderate data sizes.

    Parameters
    ----------
    cache_dir : str | Path
        Directory to store cache database.
    table_name : str, optional
        Name of the cache table, by default "cache".
    **kwargs
        Additional arguments passed to BaseCache.
    """

    def __init__(
        self,
        cache_dir: str | Path,
        table_name: str = "cache",
        **kwargs
    ):
        """Initialize SQLite cache."""
        super().__init__(cache_dir, **kwargs)
        # Validate table name to prevent SQL injection
        if not table_name.replace('_', '').isalnum():
            raise ValueError("Table name must contain only alphanumeric characters and underscores")
        if len(table_name) > 64:
            raise ValueError("Table name too long (max 64 characters)")

        self.table_name = table_name
        self.db_path = self.cache_dir / f"{table_name}.db"
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database with optimizations."""
        try:
            with sqlite3.connect(self.db_path, isolation_level='IMMEDIATE') as conn:
                # Performance optimizations
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")

                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        cache_key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at REAL,
                        accessed_at REAL,
                        access_count INTEGER DEFAULT 0,
                        size_bytes INTEGER
                    )
                """)
                conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created
                    ON {self.table_name}(created_at)
                """)
                conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_accessed
                    ON {self.table_name}(accessed_at)
                """)
                conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_size
                    ON {self.table_name}(size_bytes)
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise RuntimeError(f"Cannot initialize cache database: {e}") from e

    def get(self, key: str) -> Any | None:
        """Retrieve an item from the cache."""
        self._stats.total_requests += 1

        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        f"SELECT value, created_at FROM {self.table_name} WHERE cache_key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()

                    if row:
                        value_blob, created_at = row
                        created_time = datetime.fromtimestamp(created_at)

                        # Check expiration
                        if self.is_expired(created_time):
                            self.delete(key)
                            self._stats.cache_misses += 1
                            return None

                        # Update access stats
                        conn.execute(
                            f"""UPDATE {self.table_name}
                            SET accessed_at = ?, access_count = access_count + 1
                            WHERE cache_key = ?""",
                            (datetime.now().timestamp(), key)
                        )

                        self._stats.cache_hits += 1
                        return pickle.loads(value_blob)

                    self._stats.cache_misses += 1
                    return None

            except Exception as e:
                logger.warning(f"Cache get error for key {key}: {e}")
                self._stats.cache_misses += 1
                return None

    def put(self, key: str, value: Any) -> None:
        """Store an item in the cache."""
        with self._lock:
            try:
                value_blob = pickle.dumps(value)
                now = datetime.now().timestamp()

                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        f"""INSERT OR REPLACE INTO {self.table_name}
                        (cache_key, value, created_at, accessed_at, access_count, size_bytes)
                        VALUES (?, ?, ?, ?, 0, ?)""",
                        (key, value_blob, now, now, len(value_blob))
                    )

                # Cleanup if needed
                self.cleanup()

            except Exception as e:
                logger.warning(f"Cache put error for key {key}: {e}")

    def delete(self, key: str) -> bool:
        """Delete an item from the cache."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        f"DELETE FROM {self.table_name} WHERE cache_key = ?",
                        (key,)
                    )
                    return cursor.rowcount > 0
            except Exception as e:
                logger.warning(f"Cache delete error for key {key}: {e}")
                return False

    def clear(self) -> None:
        """Clear all items from the cache."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(f"DELETE FROM {self.table_name}")
            except Exception as e:
                logger.warning(f"Cache clear error: {e}")

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    f"SELECT 1 FROM {self.table_name} WHERE cache_key = ? LIMIT 1",
                    (key,)
                )
                return cursor.fetchone() is not None
        except Exception:
            return False

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get basic stats
                cursor = conn.execute(f"""
                    SELECT
                        COUNT(*) as count,
                        SUM(size_bytes) as total_bytes,
                        MIN(created_at) as oldest,
                        MAX(created_at) as newest
                    FROM {self.table_name}
                """)
                count, total_bytes, oldest, newest = cursor.fetchone()

                self._stats.item_count = count or 0
                self._stats.total_size_mb = (total_bytes or 0) / 1024 / 1024
                self._stats.oldest_entry = (
                    datetime.fromtimestamp(oldest) if oldest else None
                )
                self._stats.newest_entry = (
                    datetime.fromtimestamp(newest) if newest else None
                )

        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")

        return self._stats

    def cleanup(self) -> None:
        """Clean up expired entries and enforce size limits."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove expired entries
                expiry_time = datetime.now().timestamp() - (self.ttl_hours * 3600)
                conn.execute(
                    f"DELETE FROM {self.table_name} WHERE created_at < ?",
                    (expiry_time,)
                )

                # Enforce size limit by removing least recently accessed
                cursor = conn.execute(
                    f"SELECT SUM(size_bytes) FROM {self.table_name}"
                )
                total_bytes = cursor.fetchone()[0] or 0
                max_bytes = self.max_size_mb * 1024 * 1024

                if total_bytes > max_bytes:
                    # Remove least recently accessed until under limit
                    conn.execute(f"""
                        DELETE FROM {self.table_name}
                        WHERE cache_key IN (
                            SELECT cache_key FROM {self.table_name}
                            ORDER BY accessed_at ASC
                            LIMIT (SELECT COUNT(*) / 4 FROM {self.table_name})
                        )
                    """)

        except Exception as e:
            logger.warning(f"Cache cleanup error: {e}")


class ParquetCache(BaseCache[pd.DataFrame]):
    """Parquet-based cache for DataFrame storage.

    This cache is optimized for storing pandas DataFrames
    efficiently using the Parquet format.

    Parameters
    ----------
    cache_dir : str | Path
        Directory to store cache files.
    **kwargs
        Additional arguments passed to BaseCache.
    """

    def __init__(self, cache_dir: str | Path, **kwargs):
        """Initialize Parquet cache."""
        super().__init__(cache_dir, **kwargs)
        self._index = {}
        self._lock = threading.Lock()
        self._load_index()

    def _load_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._index = {}

    def _save_index(self):
        """Save cache index to disk atomically."""
        index_file = self.cache_dir / "cache_index.json"
        temp_file = index_file.with_suffix('.json.tmp')

        try:
            # Write to temporary file first
            with open(temp_file, "w") as f:
                json.dump(self._index, f)
            # Atomic rename
            temp_file.replace(index_file)
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            logger.warning(f"Failed to save cache index: {e}")

    def get(self, key: str) -> pd.DataFrame | None:
        """Retrieve a DataFrame from the cache."""
        self._stats.total_requests += 1

        with self._lock:
            if key in self._index:
                entry = self._index[key]
                created_time = datetime.fromisoformat(entry["created_at"])

                if self.is_expired(created_time):
                    self.delete(key)
                    self._stats.cache_misses += 1
                    return None

                try:
                    file_path = self.cache_dir / entry["filename"]
                    if file_path.exists():
                        df = pd.read_parquet(file_path)
                        self._stats.cache_hits += 1
                        entry["accessed_at"] = datetime.now().isoformat()
                        entry["access_count"] = entry.get("access_count", 0) + 1
                        self._save_index()
                        return df
                except Exception as e:
                    logger.warning(f"Failed to load cached DataFrame: {e}")
                    self.delete(key)

            self._stats.cache_misses += 1
            return None

    def put(self, key: str, value: pd.DataFrame) -> None:
        """Store a DataFrame in the cache."""
        with self._lock:
            try:
                filename = f"{key}.parquet"
                file_path = self.cache_dir / filename
                value.to_parquet(file_path, compression="snappy")

                self._index[key] = {
                    "filename": filename,
                    "created_at": datetime.now().isoformat(),
                    "accessed_at": datetime.now().isoformat(),
                    "access_count": 0,
                    "size_bytes": file_path.stat().st_size,
                }
                self._save_index()
                self.cleanup()

            except Exception as e:
                logger.warning(f"Failed to cache DataFrame: {e}")

    def delete(self, key: str) -> bool:
        """Delete a DataFrame from the cache."""
        with self._lock:
            if key in self._index:
                try:
                    file_path = self.cache_dir / self._index[key]["filename"]
                    if file_path.exists():
                        file_path.unlink()
                    del self._index[key]
                    self._save_index()
                    return True
                except Exception as e:
                    logger.warning(f"Failed to delete cache entry: {e}")
            return False

    def clear(self) -> None:
        """Clear all items from the cache."""
        with self._lock:
            for key in list(self._index.keys()):
                self.delete(key)
            self._index = {}
            self._save_index()

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return key in self._index

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        self._stats.item_count = len(self._index)
        self._stats.total_size_mb = sum(
            entry.get("size_bytes", 0) for entry in self._index.values()
        ) / 1024 / 1024

        if self._index:
            dates = [
                datetime.fromisoformat(entry["created_at"])
                for entry in self._index.values()
            ]
            self._stats.oldest_entry = min(dates)
            self._stats.newest_entry = max(dates)
        else:
            self._stats.oldest_entry = None
            self._stats.newest_entry = None

        return self._stats

    def cleanup(self) -> None:
        """Clean up expired entries and enforce size limits."""
        with self._lock:
            now = datetime.now()
            expired_keys = []

            # Find expired entries
            for key, entry in self._index.items():
                created_time = datetime.fromisoformat(entry["created_at"])
                if self.is_expired(created_time):
                    expired_keys.append(key)

            # Remove expired entries
            for key in expired_keys:
                self.delete(key)

            # Enforce size limit
            total_size = sum(
                entry.get("size_bytes", 0) for entry in self._index.values()
            )
            max_bytes = self.max_size_mb * 1024 * 1024

            if total_size > max_bytes:
                # Sort by access time and remove least recently used
                sorted_entries = sorted(
                    self._index.items(),
                    key=lambda x: x[1].get("accessed_at", x[1]["created_at"])
                )

                while total_size > max_bytes and sorted_entries:
                    key, entry = sorted_entries.pop(0)
                    total_size -= entry.get("size_bytes", 0)
                    self.delete(key)


class PickleCache(BaseCache[Any]):
    """Pickle-based cache with gzip compression.

    This cache uses pickle for serialization and gzip for compression,
    suitable for complex Python objects.

    Parameters
    ----------
    cache_dir : str | Path
        Directory to store cache files.
    compression_level : int, optional
        Gzip compression level (0-9), by default 6.
    **kwargs
        Additional arguments passed to BaseCache.
    """

    def __init__(
        self,
        cache_dir: str | Path,
        compression_level: int = 6,
        **kwargs
    ):
        """Initialize Pickle cache."""
        super().__init__(cache_dir, **kwargs)
        self.compression_level = compression_level
        self._index = {}
        self._lock = threading.Lock()
        self._load_index()

    def _load_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._index = {}

    def _save_index(self):
        """Save cache index to disk atomically."""
        index_file = self.cache_dir / "cache_index.json"
        temp_file = index_file.with_suffix('.json.tmp')

        try:
            # Write to temporary file first
            with open(temp_file, "w") as f:
                json.dump(self._index, f, default=str)
            # Atomic rename
            temp_file.replace(index_file)
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            logger.warning(f"Failed to save cache index: {e}")

    def get(self, key: str) -> Any | None:
        """Retrieve an item from the cache."""
        self._stats.total_requests += 1

        with self._lock:
            if key in self._index:
                entry = self._index[key]
                created_time = datetime.fromisoformat(entry["created_at"])

                if self.is_expired(created_time):
                    self.delete(key)
                    self._stats.cache_misses += 1
                    return None

                try:
                    file_path = self.cache_dir / entry["filename"]
                    if file_path.exists():
                        with gzip.open(file_path, "rb") as f:
                            value = pickle.load(f)
                        self._stats.cache_hits += 1
                        entry["accessed_at"] = datetime.now().isoformat()
                        entry["access_count"] = entry.get("access_count", 0) + 1
                        self._save_index()
                        return value
                except Exception as e:
                    logger.warning(f"Failed to load cached object: {e}")
                    self.delete(key)

            self._stats.cache_misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        """Store an item in the cache."""
        with self._lock:
            try:
                filename = f"{key}.pkl.gz"
                file_path = self.cache_dir / filename

                with gzip.open(file_path, "wb", compresslevel=self.compression_level) as f:
                    pickle.dump(value, f)

                self._index[key] = {
                    "filename": filename,
                    "created_at": datetime.now().isoformat(),
                    "accessed_at": datetime.now().isoformat(),
                    "access_count": 0,
                    "size_bytes": file_path.stat().st_size,
                }
                self._save_index()
                self.cleanup()

            except Exception as e:
                logger.warning(f"Failed to cache object: {e}")

    def delete(self, key: str) -> bool:
        """Delete an item from the cache."""
        with self._lock:
            if key in self._index:
                try:
                    file_path = self.cache_dir / self._index[key]["filename"]
                    if file_path.exists():
                        file_path.unlink()
                    del self._index[key]
                    self._save_index()
                    return True
                except Exception as e:
                    logger.warning(f"Failed to delete cache entry: {e}")
            return False

    def clear(self) -> None:
        """Clear all items from the cache."""
        with self._lock:
            for key in list(self._index.keys()):
                self.delete(key)
            self._index = {}
            self._save_index()

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return key in self._index

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        self._stats.item_count = len(self._index)
        self._stats.total_size_mb = sum(
            entry.get("size_bytes", 0) for entry in self._index.values()
        ) / 1024 / 1024

        if self._index:
            dates = [
                datetime.fromisoformat(entry["created_at"])
                for entry in self._index.values()
            ]
            self._stats.oldest_entry = min(dates)
            self._stats.newest_entry = max(dates)
        else:
            self._stats.oldest_entry = None
            self._stats.newest_entry = None

        return self._stats

    def cleanup(self) -> None:
        """Clean up expired entries and enforce size limits."""
        with self._lock:
            expired_keys = []

            # Find expired entries
            for key, entry in self._index.items():
                created_time = datetime.fromisoformat(entry["created_at"])
                if self.is_expired(created_time):
                    expired_keys.append(key)

            # Remove expired entries
            for key in expired_keys:
                self.delete(key)

            # Enforce size limit
            total_size = sum(
                entry.get("size_bytes", 0) for entry in self._index.values()
            )
            max_bytes = self.max_size_mb * 1024 * 1024

            if total_size > max_bytes:
                # Sort by access time and remove least recently used
                sorted_entries = sorted(
                    self._index.items(),
                    key=lambda x: x[1].get("accessed_at", x[1]["created_at"])
                )

                while total_size > max_bytes and sorted_entries:
                    key, entry = sorted_entries.pop(0)
                    total_size -= entry.get("size_bytes", 0)
                    self.delete(key)