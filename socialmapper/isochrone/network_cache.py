#!/usr/bin/env python3
"""
Network caching module for improved isochrone performance.

This module provides caching mechanisms to avoid redundant network downloads
when processing multiple POIs in the same area.
"""

import os
import pickle
import hashlib
import time
import logging
from typing import Dict, Any, Optional, Tuple
import networkx as nx
import osmnx as ox
from shapely.geometry import Point
import geopandas as gpd

logger = logging.getLogger(__name__)

class NetworkCache:
    """
    Cache for street networks to avoid redundant downloads.
    """
    
    def __init__(self, cache_dir: str = "cache/networks", max_cache_size: int = 100):
        """
        Initialize network cache.
        
        Args:
            cache_dir: Directory to store cached networks
            max_cache_size: Maximum number of networks to cache
        """
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.cache_index = {}
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load existing cache index
        self._load_cache_index()
    
    def _load_cache_index(self):
        """Load cache index from disk."""
        index_path = os.path.join(self.cache_dir, "cache_index.pkl")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'rb') as f:
                    self.cache_index = pickle.load(f)
                logger.info(f"Loaded cache index with {len(self.cache_index)} entries")
            except Exception as e:
                logger.warning(f"Error loading cache index: {e}")
                self.cache_index = {}
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        index_path = os.path.join(self.cache_dir, "cache_index.pkl")
        try:
            with open(index_path, 'wb') as f:
                pickle.dump(self.cache_index, f)
        except Exception as e:
            logger.warning(f"Error saving cache index: {e}")
    
    def _get_cache_key(self, lat: float, lon: float, dist: int, network_type: str = "drive") -> str:
        """
        Generate cache key for network parameters.
        
        Args:
            lat: Latitude
            lon: Longitude  
            dist: Distance in meters
            network_type: Type of network
            
        Returns:
            Cache key string
        """
        # Round coordinates to reduce cache fragmentation
        lat_rounded = round(lat, 4)  # ~11m precision
        lon_rounded = round(lon, 4)  # ~11m precision
        
        key_string = f"{lat_rounded}_{lon_rounded}_{dist}_{network_type}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_network(self, lat: float, lon: float, dist: int, network_type: str = "drive") -> Optional[nx.MultiDiGraph]:
        """
        Get network from cache if available.
        
        Args:
            lat: Latitude
            lon: Longitude
            dist: Distance in meters
            network_type: Type of network
            
        Returns:
            Cached network or None if not found
        """
        cache_key = self._get_cache_key(lat, lon, dist, network_type)
        
        if cache_key not in self.cache_index:
            return None
        
        cache_info = self.cache_index[cache_key]
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if not os.path.exists(cache_file):
            # Remove stale index entry
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                network = pickle.load(f)
            
            # Update access time
            cache_info['last_accessed'] = time.time()
            cache_info['access_count'] += 1
            self._save_cache_index()
            
            logger.info(f"Retrieved network from cache: {len(network.nodes)} nodes, {len(network.edges)} edges")
            return network
            
        except Exception as e:
            logger.warning(f"Error loading cached network: {e}")
            # Remove corrupted cache entry
            try:
                os.remove(cache_file)
                del self.cache_index[cache_key]
                self._save_cache_index()
            except Exception:
                pass
            return None
    
    def store_network(self, network: nx.MultiDiGraph, lat: float, lon: float, dist: int, network_type: str = "drive"):
        """
        Store network in cache.
        
        Args:
            network: Network to cache
            lat: Latitude
            lon: Longitude
            dist: Distance in meters
            network_type: Type of network
        """
        cache_key = self._get_cache_key(lat, lon, dist, network_type)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            # Check if we need to clean up old entries
            if len(self.cache_index) >= self.max_cache_size:
                self._cleanup_cache()
            
            # Store network
            with open(cache_file, 'wb') as f:
                pickle.dump(network, f)
            
            # Update index
            self.cache_index[cache_key] = {
                'lat': lat,
                'lon': lon,
                'dist': dist,
                'network_type': network_type,
                'created': time.time(),
                'last_accessed': time.time(),
                'access_count': 1,
                'nodes': len(network.nodes),
                'edges': len(network.edges)
            }
            
            self._save_cache_index()
            logger.info(f"Stored network in cache: {len(network.nodes)} nodes, {len(network.edges)} edges")
            
        except Exception as e:
            logger.warning(f"Error storing network in cache: {e}")
    
    def _cleanup_cache(self):
        """Remove least recently used cache entries."""
        if len(self.cache_index) < self.max_cache_size:
            return
        
        # Sort by last accessed time
        sorted_entries = sorted(
            self.cache_index.items(),
            key=lambda x: x[1]['last_accessed']
        )
        
        # Remove oldest entries
        entries_to_remove = len(self.cache_index) - self.max_cache_size + 10  # Remove extra for buffer
        
        for i in range(min(entries_to_remove, len(sorted_entries))):
            cache_key, cache_info = sorted_entries[i]
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                del self.cache_index[cache_key]
            except Exception as e:
                logger.warning(f"Error removing cache entry {cache_key}: {e}")
        
        logger.info(f"Cleaned up {entries_to_remove} cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = 0
        total_nodes = 0
        total_edges = 0
        
        for cache_info in self.cache_index.values():
            total_nodes += cache_info.get('nodes', 0)
            total_edges += cache_info.get('edges', 0)
        
        # Calculate disk usage
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    filepath = os.path.join(self.cache_dir, filename)
                    total_size += os.path.getsize(filepath)
        except Exception:
            total_size = 0
        
        return {
            'entries': len(self.cache_index),
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'disk_usage_mb': total_size / (1024 * 1024),
            'cache_dir': self.cache_dir
        }
    
    def clear_cache(self):
        """Clear all cached networks."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, filename))
            
            self.cache_index = {}
            self._save_cache_index()
            logger.info("Cache cleared")
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")

# Global cache instance
_network_cache = None

def get_network_cache() -> NetworkCache:
    """Get the global network cache instance."""
    global _network_cache
    if _network_cache is None:
        _network_cache = NetworkCache()
    return _network_cache

def download_network_with_cache(
    lat: float, 
    lon: float, 
    dist: int, 
    network_type: str = "drive"
) -> nx.MultiDiGraph:
    """
    Download network with caching support.
    
    Args:
        lat: Latitude
        lon: Longitude
        dist: Distance in meters
        network_type: Type of network
        
    Returns:
        Street network graph
    """
    cache = get_network_cache()
    
    # Try to get from cache first
    network = cache.get_network(lat, lon, dist, network_type)
    if network is not None:
        return network
    
    # Download network
    logger.info(f"Downloading network for ({lat}, {lon}) with distance {dist}m")
    network = ox.graph_from_point(
        (lat, lon),
        network_type=network_type,
        dist=dist
    )
    
    # Store in cache
    cache.store_network(network, lat, lon, dist, network_type)
    
    return network 