"""
Cache implementations for census data.

Provides multiple caching strategies:
- In-memory cache with LRU eviction
- File-based cache for persistence
- No-op cache for testing/disabled caching
"""

import json
import pickle
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any, Dict
from collections import OrderedDict

from ..domain.entities import CacheEntry


class InMemoryCacheProvider:
    """
    Thread-safe in-memory cache with LRU eviction.
    
    Uses OrderedDict for efficient LRU implementation and provides
    automatic expiration of cached entries.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize cache with maximum size.
        
        Args:
            max_size: Maximum number of entries to store
        """
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()  # Reentrant lock for thread safety
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Retrieve a cached entry.
        
        Args:
            key: Cache key
            
        Returns:
            CacheEntry if found and not expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
            
            # Check if expired
            if entry.is_expired:
                # Remove expired entry
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return entry
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Store data in cache with optional TTL.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        with self._lock:
            # Calculate expiration time
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)  # Mark as most recently used
            
            # Evict oldest entries if over max size
            while len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
    
    def delete(self, key: str) -> None:
        """
        Remove an entry from cache.
        
        Args:
            key: Cache key to remove
        """
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values()
                if entry.is_expired
            )
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "max_size": self._max_size,
                "utilization": total_entries / self._max_size if self._max_size > 0 else 0
            }


class FileCacheProvider:
    """
    File-based cache with persistence across application restarts.
    
    Stores cache entries as pickle files in a designated directory.
    Provides automatic cleanup of expired entries.
    """
    
    def __init__(self, cache_dir: str, max_files: int = 10000):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_files: Maximum number of cache files to maintain
        """
        self._cache_dir = Path(cache_dir)
        self._max_files = max_files
        self._lock = threading.RLock()
        
        # Create cache directory if it doesn't exist
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Retrieve a cached entry from file.
        
        Args:
            key: Cache key
            
        Returns:
            CacheEntry if found and not expired, None otherwise
        """
        cache_file = self._get_cache_file_path(key)
        
        with self._lock:
            if not cache_file.exists():
                return None
            
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                # Check if expired
                if entry.is_expired:
                    # Remove expired file
                    cache_file.unlink(missing_ok=True)
                    return None
                
                # Update access time
                cache_file.touch()
                return entry
                
            except (pickle.PickleError, OSError, EOFError):
                # Remove corrupted file
                cache_file.unlink(missing_ok=True)
                return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Store data in file cache.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        cache_file = self._get_cache_file_path(key)
        
        with self._lock:
            # Calculate expiration time
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            try:
                # Write to temporary file first, then rename (atomic operation)
                temp_file = cache_file.with_suffix('.tmp')
                with open(temp_file, 'wb') as f:
                    pickle.dump(entry, f)
                
                temp_file.rename(cache_file)
                
                # Cleanup old files if over limit
                self._cleanup_old_files()
                
            except (pickle.PickleError, OSError) as e:
                # Clean up temporary file if it exists
                temp_file.unlink(missing_ok=True)
                raise RuntimeError(f"Failed to write cache file: {e}")
    
    def delete(self, key: str) -> None:
        """
        Remove an entry from file cache.
        
        Args:
            key: Cache key to remove
        """
        cache_file = self._get_cache_file_path(key)
        with self._lock:
            cache_file.unlink(missing_ok=True)
    
    def clear(self) -> None:
        """Clear all cached files."""
        with self._lock:
            for cache_file in self._cache_dir.glob("*.cache"):
                cache_file.unlink(missing_ok=True)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache files.
        
        Returns:
            Number of files removed
        """
        removed_count = 0
        
        with self._lock:
            for cache_file in self._cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if entry.is_expired:
                        cache_file.unlink()
                        removed_count += 1
                        
                except (pickle.PickleError, OSError):
                    # Remove corrupted files
                    cache_file.unlink(missing_ok=True)
                    removed_count += 1
        
        return removed_count
    
    def _get_cache_file_path(self, key: str) -> Path:
        """Generate file path for cache key."""
        # Create a safe filename from the key
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"{key_hash}.cache"
    
    def _cleanup_old_files(self) -> None:
        """Remove oldest cache files if over the limit."""
        cache_files = list(self._cache_dir.glob("*.cache"))
        
        if len(cache_files) <= self._max_files:
            return
        
        # Sort by modification time (oldest first)
        cache_files.sort(key=lambda f: f.stat().st_mtime)
        
        # Remove oldest files
        files_to_remove = len(cache_files) - self._max_files
        for cache_file in cache_files[:files_to_remove]:
            cache_file.unlink(missing_ok=True)


class NoOpCacheProvider:
    """
    No-operation cache provider for testing or disabled caching.
    
    Implements the cache interface but doesn't actually store anything.
    Useful for testing or when caching is disabled.
    """
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Always returns None (no cache hit)."""
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Does nothing (no-op)."""
        pass
    
    def delete(self, key: str) -> None:
        """Does nothing (no-op)."""
        pass
    
    def clear(self) -> None:
        """Does nothing (no-op)."""
        pass


class HybridCacheProvider:
    """
    Hybrid cache that combines in-memory and file-based caching.
    
    Uses in-memory cache for fast access and file cache for persistence.
    Automatically promotes frequently accessed items to memory cache.
    """
    
    def __init__(
        self, 
        memory_cache_size: int = 100,
        file_cache_dir: Optional[str] = None,
        file_cache_max_files: int = 10000
    ):
        """
        Initialize hybrid cache.
        
        Args:
            memory_cache_size: Size of in-memory cache
            file_cache_dir: Directory for file cache (None to disable)
            file_cache_max_files: Maximum files in file cache
        """
        self._memory_cache = InMemoryCacheProvider(memory_cache_size)
        
        if file_cache_dir:
            self._file_cache: Optional[FileCacheProvider] = FileCacheProvider(
                file_cache_dir, file_cache_max_files
            )
        else:
            self._file_cache = None
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Get from memory cache first, then file cache.
        
        Promotes file cache hits to memory cache.
        """
        # Try memory cache first
        entry = self._memory_cache.get(key)
        if entry is not None:
            return entry
        
        # Try file cache if available
        if self._file_cache is not None:
            entry = self._file_cache.get(key)
            if entry is not None:
                # Promote to memory cache
                remaining_ttl = None
                if entry.expires_at:
                    remaining_seconds = (entry.expires_at - datetime.now()).total_seconds()
                    if remaining_seconds > 0:
                        remaining_ttl = int(remaining_seconds)
                
                self._memory_cache.set(key, entry.data, remaining_ttl)
                return entry
        
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Store in both memory and file cache."""
        # Always store in memory cache
        self._memory_cache.set(key, data, ttl)
        
        # Store in file cache if available
        if self._file_cache is not None:
            self._file_cache.set(key, data, ttl)
    
    def delete(self, key: str) -> None:
        """Delete from both caches."""
        self._memory_cache.delete(key)
        if self._file_cache is not None:
            self._file_cache.delete(key)
    
    def clear(self) -> None:
        """Clear both caches."""
        self._memory_cache.clear()
        if self._file_cache is not None:
            self._file_cache.clear()
    
    def cleanup_expired(self) -> int:
        """Cleanup expired entries from both caches."""
        memory_removed = self._memory_cache.cleanup_expired()
        file_removed = 0
        
        if self._file_cache is not None:
            file_removed = self._file_cache.cleanup_expired()
        
        return memory_removed + file_removed 