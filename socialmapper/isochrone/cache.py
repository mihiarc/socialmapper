#!/usr/bin/env python3
"""
Advanced Network Caching System for Isochrone Generation.

This module implements high-performance network caching with SQLite indexing,
compression, and intelligent cache management to dramatically reduce network
download times for isochrone generation.

Key Features:
- SQLite database for fast spatial indexing
- Gzip compression for storage efficiency
- Intelligent cache eviction policies
- Concurrent access support
- Network overlap detection and optimization
"""

import pickle
import hashlib
import sqlite3
import gzip
import json
import time
import threading
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Union
import numpy as np
import networkx as nx
import osmnx as ox
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

@dataclass
class NetworkMetadata:
    """Metadata for cached network graphs."""
    bbox: Tuple[float, float, float, float]  # (min_lat, min_lon, max_lat, max_lon)
    network_type: str
    created_at: float
    file_size: int
    node_count: int
    edge_count: int
    cache_key: str
    travel_time_minutes: int
    cluster_size: int

@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    total_size_mb: float
    avg_retrieval_time_ms: float
    compression_ratio: float

class ModernNetworkCache:
    """High-performance network caching with SQLite index and compression."""
    
    def __init__(self, cache_dir: str = "cache/networks", max_cache_size_gb: float = 5.0):
        """
        Initialize the modern network cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_cache_size_gb: Maximum cache size in gigabytes
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size_gb * 1024**3
        self.db_path = self.cache_dir / "cache_index.db"
        self._lock = threading.Lock()
        self._stats = CacheStats(0, 0, 0, 0.0, 0.0, 0.0)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for cache indexing."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS networks (
                    cache_key TEXT PRIMARY KEY,
                    bbox_minlat REAL, bbox_minlon REAL, bbox_maxlat REAL, bbox_maxlon REAL,
                    network_type TEXT,
                    created_at REAL,
                    file_size INTEGER,
                    node_count INTEGER,
                    edge_count INTEGER,
                    file_path TEXT,
                    travel_time_minutes INTEGER,
                    cluster_size INTEGER,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL
                )
            """)
            
            # Create spatial index for efficient bbox queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_bbox 
                ON networks (bbox_minlat, bbox_minlon, bbox_maxlat, bbox_maxlon)
            """)
            
            # Create index for cache management
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_access 
                ON networks (last_accessed, file_size)
            """)
            
            conn.commit()
    
    def _generate_cache_key(self, bbox: Tuple[float, float, float, float], 
                          network_type: str, travel_time_minutes: int) -> str:
        """Generate unique cache key for network parameters."""
        # Round bbox to reduce cache fragmentation
        rounded_bbox = tuple(round(coord, 4) for coord in bbox)
        key_data = f"{rounded_bbox}_{network_type}_{travel_time_minutes}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _get_file_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.pkl.gz"
    
    def _compress_network(self, network: nx.MultiDiGraph) -> bytes:
        """Compress network graph using gzip."""
        pickled_data = pickle.dumps(network, protocol=pickle.HIGHEST_PROTOCOL)
        return gzip.compress(pickled_data, compresslevel=6)
    
    def _decompress_network(self, compressed_data: bytes) -> nx.MultiDiGraph:
        """Decompress network graph."""
        pickled_data = gzip.decompress(compressed_data)
        return pickle.loads(pickled_data)
    
    def _calculate_bbox_overlap(self, bbox1: Tuple[float, float, float, float],
                              bbox2: Tuple[float, float, float, float]) -> float:
        """Calculate overlap percentage between two bounding boxes."""
        min_lat1, min_lon1, max_lat1, max_lon1 = bbox1
        min_lat2, min_lon2, max_lat2, max_lon2 = bbox2
        
        # Calculate intersection
        inter_min_lat = max(min_lat1, min_lat2)
        inter_min_lon = max(min_lon1, min_lon2)
        inter_max_lat = min(max_lat1, max_lat2)
        inter_max_lon = min(max_lon1, max_lon2)
        
        if inter_min_lat >= inter_max_lat or inter_min_lon >= inter_max_lon:
            return 0.0  # No overlap
        
        # Calculate areas
        inter_area = (inter_max_lat - inter_min_lat) * (inter_max_lon - inter_min_lon)
        bbox1_area = (max_lat1 - min_lat1) * (max_lon1 - min_lon1)
        
        return inter_area / bbox1_area if bbox1_area > 0 else 0.0
    
    def find_overlapping_networks(self, bbox: Tuple[float, float, float, float],
                                network_type: str, travel_time_minutes: int,
                                min_overlap: float = 0.8) -> List[NetworkMetadata]:
        """Find cached networks that significantly overlap with requested bbox."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM networks 
                WHERE network_type = ? 
                AND travel_time_minutes >= ?
                AND bbox_minlat <= ? AND bbox_maxlat >= ?
                AND bbox_minlon <= ? AND bbox_maxlon >= ?
            """, (
                network_type, 
                travel_time_minutes * 0.8,  # Allow smaller travel times
                bbox[2], bbox[0],  # max_lat >= min_lat and min_lat <= max_lat
                bbox[3], bbox[1]   # max_lon >= min_lon and min_lon <= max_lon
            ))
            
            overlapping = []
            for row in cursor.fetchall():
                cached_bbox = (row[1], row[2], row[3], row[4])  # min_lat, min_lon, max_lat, max_lon
                overlap = self._calculate_bbox_overlap(bbox, cached_bbox)
                
                if overlap >= min_overlap:
                    metadata = NetworkMetadata(
                        bbox=cached_bbox,
                        network_type=row[5],
                        created_at=row[6],
                        file_size=row[7],
                        node_count=row[8],
                        edge_count=row[9],
                        cache_key=row[0],
                        travel_time_minutes=row[11],
                        cluster_size=row[12]
                    )
                    overlapping.append(metadata)
            
            return overlapping
    
    def get_network(self, bbox: Tuple[float, float, float, float],
                   network_type: str = 'drive',
                   travel_time_minutes: int = 15) -> Optional[nx.MultiDiGraph]:
        """
        Retrieve network from cache or return None if not found.
        
        Args:
            bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
            network_type: Type of network ('drive', 'walk', etc.)
            travel_time_minutes: Travel time requirement
            
        Returns:
            Network graph or None if not cached
        """
        start_time = time.time()
        
        with self._lock:
            self._stats.total_requests += 1
        
        # First try exact match
        cache_key = self._generate_cache_key(bbox, network_type, travel_time_minutes)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_path, node_count, edge_count FROM networks 
                    WHERE cache_key = ?
                """, (cache_key,))
                
                row = cursor.fetchone()
                if row:
                    file_path = Path(row[0])
                    if file_path.exists():
                        # Load and decompress network
                        with open(file_path, 'rb') as f:
                            compressed_data = f.read()
                        
                        network = self._decompress_network(compressed_data)
                        
                        # Update access statistics
                        conn.execute("""
                            UPDATE networks 
                            SET access_count = access_count + 1, last_accessed = ?
                            WHERE cache_key = ?
                        """, (time.time(), cache_key))
                        conn.commit()
                        
                        retrieval_time = (time.time() - start_time) * 1000
                        with self._lock:
                            self._stats.cache_hits += 1
                            self._stats.avg_retrieval_time_ms = (
                                (self._stats.avg_retrieval_time_ms * (self._stats.cache_hits - 1) + retrieval_time) 
                                / self._stats.cache_hits
                            )
                        
                        logger.debug(f"Cache hit for {cache_key}: {row[1]} nodes, {row[2]} edges")
                        return network
        
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
        
        # Try overlapping networks
        overlapping = self.find_overlapping_networks(bbox, network_type, travel_time_minutes)
        if overlapping:
            # Use the largest overlapping network
            best_match = max(overlapping, key=lambda x: x.node_count)
            try:
                file_path = self._get_file_path(best_match.cache_key)
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        compressed_data = f.read()
                    
                    network = self._decompress_network(compressed_data)
                    
                    retrieval_time = (time.time() - start_time) * 1000
                    with self._lock:
                        self._stats.cache_hits += 1
                        self._stats.avg_retrieval_time_ms = (
                            (self._stats.avg_retrieval_time_ms * (self._stats.cache_hits - 1) + retrieval_time) 
                            / self._stats.cache_hits
                        )
                    
                    logger.debug(f"Cache hit (overlap) for {best_match.cache_key}")
                    return network
            
            except Exception as e:
                logger.error(f"Error loading overlapping network: {e}")
        
        with self._lock:
            self._stats.cache_misses += 1
        
        return None
    
    def store_network(self, network: nx.MultiDiGraph, bbox: Tuple[float, float, float, float],
                     network_type: str = 'drive', travel_time_minutes: int = 15,
                     cluster_size: int = 1) -> bool:
        """
        Store network in cache with compression.
        
        Args:
            network: Network graph to cache
            bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
            network_type: Type of network
            travel_time_minutes: Travel time requirement
            cluster_size: Number of POIs this network serves
            
        Returns:
            True if stored successfully
        """
        try:
            cache_key = self._generate_cache_key(bbox, network_type, travel_time_minutes)
            file_path = self._get_file_path(cache_key)
            
            # Compress and save network
            compressed_data = self._compress_network(network)
            
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
            
            # Calculate compression ratio
            original_size = len(pickle.dumps(network, protocol=pickle.HIGHEST_PROTOCOL))
            compression_ratio = len(compressed_data) / original_size
            
            # Store metadata in database
            metadata = NetworkMetadata(
                bbox=bbox,
                network_type=network_type,
                created_at=time.time(),
                file_size=len(compressed_data),
                node_count=len(network.nodes),
                edge_count=len(network.edges),
                cache_key=cache_key,
                travel_time_minutes=travel_time_minutes,
                cluster_size=cluster_size
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO networks 
                    (cache_key, bbox_minlat, bbox_minlon, bbox_maxlat, bbox_maxlon,
                     network_type, created_at, file_size, node_count, edge_count,
                     file_path, travel_time_minutes, cluster_size, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_key, bbox[0], bbox[1], bbox[2], bbox[3],
                    network_type, metadata.created_at, metadata.file_size,
                    metadata.node_count, metadata.edge_count, str(file_path),
                    travel_time_minutes, cluster_size, time.time()
                ))
                conn.commit()
            
            # Update statistics
            with self._lock:
                self._stats.compression_ratio = (
                    (self._stats.compression_ratio * self._stats.cache_hits + compression_ratio) 
                    / (self._stats.cache_hits + 1)
                )
            
            logger.debug(f"Cached network {cache_key}: {metadata.node_count} nodes, "
                        f"{metadata.edge_count} edges, {compression_ratio:.2f} compression")
            
            # Check if cache cleanup is needed
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing network in cache: {e}")
            return False
    
    def _cleanup_if_needed(self):
        """Clean up cache if it exceeds size limit."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl.gz"))
            
            if total_size > self.max_cache_size:
                logger.info(f"Cache size {total_size / 1024**3:.2f}GB exceeds limit, cleaning up...")
                
                # Get files sorted by last access time and size
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT cache_key, file_path, file_size, last_accessed, access_count
                        FROM networks 
                        ORDER BY last_accessed ASC, access_count ASC
                    """)
                    
                    removed_size = 0
                    target_size = self.max_cache_size * 0.8  # Clean to 80% of limit
                    
                    for row in cursor.fetchall():
                        if total_size - removed_size <= target_size:
                            break
                        
                        cache_key, file_path, file_size = row[0], row[1], row[2]
                        
                        # Remove file and database entry
                        Path(file_path).unlink(missing_ok=True)
                        conn.execute("DELETE FROM networks WHERE cache_key = ?", (cache_key,))
                        
                        removed_size += file_size
                    
                    conn.commit()
                    
                logger.info(f"Removed {removed_size / 1024**3:.2f}GB from cache")
                
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
    
    def get_cache_stats(self) -> CacheStats:
        """Get current cache statistics."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl.gz"))
            
            with self._lock:
                stats = CacheStats(
                    total_requests=self._stats.total_requests,
                    cache_hits=self._stats.cache_hits,
                    cache_misses=self._stats.cache_misses,
                    total_size_mb=total_size / 1024**2,
                    avg_retrieval_time_ms=self._stats.avg_retrieval_time_ms,
                    compression_ratio=self._stats.compression_ratio
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return CacheStats(0, 0, 0, 0.0, 0.0, 0.0)
    
    def clear_cache(self):
        """Clear all cached networks."""
        try:
            # Remove all cache files
            for file_path in self.cache_dir.glob("*.pkl.gz"):
                file_path.unlink()
            
            # Clear database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM networks")
                conn.commit()
            
            # Reset statistics
            with self._lock:
                self._stats = CacheStats(0, 0, 0, 0.0, 0.0, 0.0)
            
            logger.info("Cache cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

# Global cache instance
_global_cache = None
_cache_lock = threading.Lock()

def get_global_cache() -> ModernNetworkCache:
    """Get or create global cache instance."""
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = ModernNetworkCache()
    
    return _global_cache

def download_and_cache_network(bbox: Tuple[float, float, float, float],
                             network_type: str = 'drive',
                             travel_time_minutes: int = 15,
                             cluster_size: int = 1,
                             cache: Optional[ModernNetworkCache] = None) -> Optional[nx.MultiDiGraph]:
    """
    Download network and store in cache, or retrieve from cache if available.
    
    Args:
        bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
        network_type: Type of network to download
        travel_time_minutes: Travel time requirement
        cluster_size: Number of POIs this network will serve
        cache: Cache instance to use (uses global cache if None)
        
    Returns:
        Network graph or None if download failed
    """
    if cache is None:
        cache = get_global_cache()
    
    # Try to get from cache first
    network = cache.get_network(bbox, network_type, travel_time_minutes)
    if network is not None:
        return network
    
    # Download new network
    try:
        logger.info(f"Downloading network for bbox {bbox}")
        
        min_lat, min_lon, max_lat, max_lon = bbox
        # OSMnx expects bbox as (left, bottom, right, top) = (min_lon, min_lat, max_lon, max_lat)
        osm_bbox = (min_lon, min_lat, max_lon, max_lat)
        G = ox.graph_from_bbox(
            bbox=osm_bbox,
            network_type=network_type
        )
        
        # Add speeds and travel times
        G = ox.add_edge_speeds(G, fallback=50)
        G = ox.add_edge_travel_times(G)
        G = ox.project_graph(G)
        
        # Store in cache
        cache.store_network(G, bbox, network_type, travel_time_minutes, cluster_size)
        
        logger.info(f"Downloaded and cached network: {len(G.nodes)} nodes, {len(G.edges)} edges")
        return G
        
    except Exception as e:
        logger.error(f"Failed to download network for bbox {bbox}: {e}")
        return None 