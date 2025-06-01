#!/usr/bin/env python3
"""
Concurrent Isochrone Processing System.

This module implements high-performance concurrent processing for isochrone
generation with intelligent task scheduling, resource management, and
progress monitoring.

Key Features:
- ThreadPoolExecutor for concurrent network downloads
- ProcessPoolExecutor for CPU-intensive isochrone calculations
- Intelligent task batching and scheduling
- Resource usage monitoring and throttling
- Progress tracking with detailed statistics
"""

import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, Future
from dataclasses import dataclass
import multiprocessing as mp
import psutil
import geopandas as gpd
from queue import Queue, Empty
import os

from .clustering import (
    OptimizedPOICluster, 
    create_optimized_clusters,
    create_isochrone_from_poi_with_network
)
from .cache import ModernNetworkCache, download_and_cache_network
from ..progress import get_progress_bar

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Statistics for concurrent processing performance."""
    total_pois: int
    total_clusters: int
    networks_downloaded: int
    networks_cached: int
    isochrones_generated: int
    failed_isochrones: int
    total_time_seconds: float
    network_download_time_seconds: float
    isochrone_generation_time_seconds: float
    cache_hit_rate: float
    avg_cluster_size: float
    max_concurrent_downloads: int
    max_concurrent_isochrones: int

class ConcurrentIsochroneProcessor:
    """High-performance concurrent processor for isochrone generation."""
    
    def __init__(self, 
                 max_network_workers: int = 8,
                 max_isochrone_workers: Optional[int] = None,
                 cache: Optional[ModernNetworkCache] = None):
        """
        Initialize the concurrent processor.
        
        Args:
            max_network_workers: Maximum concurrent network downloads
            max_isochrone_workers: Maximum concurrent isochrone calculations (defaults to CPU count)
            cache: Network cache instance
        """
        self.max_network_workers = max_network_workers
        self.max_isochrone_workers = max_isochrone_workers or mp.cpu_count()
        self.cache = cache or ModernNetworkCache()
        
        # Performance monitoring
        self._stats = ProcessingStats(
            total_pois=0, total_clusters=0, networks_downloaded=0, networks_cached=0,
            isochrones_generated=0, failed_isochrones=0, total_time_seconds=0.0,
            network_download_time_seconds=0.0, isochrone_generation_time_seconds=0.0,
            cache_hit_rate=0.0, avg_cluster_size=0.0, max_concurrent_downloads=0,
            max_concurrent_isochrones=0
        )
        
        # Resource monitoring
        self._monitor_resources = True
        self._resource_check_interval = 5.0  # seconds
        
    def _monitor_system_resources(self) -> Dict[str, float]:
        """Monitor system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / 1024**3,
                'disk_free_gb': disk.free / 1024**3
            }
        except Exception as e:
            logger.warning(f"Failed to monitor resources: {e}")
            return {}
    
    def _adjust_workers_based_on_resources(self, resources: Dict[str, float]) -> Tuple[int, int]:
        """Adjust worker counts based on system resources."""
        network_workers = self.max_network_workers
        isochrone_workers = self.max_isochrone_workers
        
        # Reduce workers if system is under stress
        if resources.get('cpu_percent', 0) > 90:
            isochrone_workers = max(1, isochrone_workers // 2)
            logger.info(f"High CPU usage, reducing isochrone workers to {isochrone_workers}")
        
        if resources.get('memory_percent', 0) > 85:
            network_workers = max(1, network_workers // 2)
            isochrone_workers = max(1, isochrone_workers // 2)
            logger.info(f"High memory usage, reducing workers to {network_workers}/{isochrone_workers}")
        
        return network_workers, isochrone_workers
    
    def _download_cluster_network(self, cluster: OptimizedPOICluster, 
                                 travel_time_minutes: int) -> Tuple[str, Optional[Any]]:
        """Download network for a cluster (thread-safe)."""
        try:
            bbox = cluster.get_network_bbox(travel_time_minutes)
            network = download_and_cache_network(
                bbox=bbox,
                travel_time_minutes=travel_time_minutes,
                cluster_size=len(cluster),
                cache=self.cache
            )
            
            if network is not None:
                cluster.network = network
                cluster.network_crs = network.graph['crs']
                return cluster.cluster_id, network
            else:
                logger.error(f"Failed to download network for cluster {cluster.cluster_id}")
                return cluster.cluster_id, None
                
        except Exception as e:
            logger.error(f"Error downloading network for cluster {cluster.cluster_id}: {e}")
            return cluster.cluster_id, None
    
    def _generate_cluster_isochrones(self, cluster: OptimizedPOICluster,
                                   travel_time_minutes: int) -> List[gpd.GeoDataFrame]:
        """Generate isochrones for all POIs in a cluster."""
        isochrones = []
        
        if cluster.network is None:
            logger.error(f"No network available for cluster {cluster.cluster_id}")
            return isochrones
        
        for poi in cluster.pois:
            try:
                isochrone_gdf = create_isochrone_from_poi_with_network(
                    poi=poi,
                    network=cluster.network,
                    network_crs=cluster.network_crs,
                    travel_time_minutes=travel_time_minutes
                )
                
                if isochrone_gdf is not None:
                    isochrones.append(isochrone_gdf)
                    self._stats.isochrones_generated += 1
                else:
                    self._stats.failed_isochrones += 1
                    
            except Exception as e:
                logger.error(f"Failed to generate isochrone for POI {poi.get('id', 'unknown')}: {e}")
                self._stats.failed_isochrones += 1
        
        return isochrones
    
    def process_pois_concurrent(self, 
                              pois: List[Dict[str, Any]],
                              travel_time_minutes: int = 15,
                              max_cluster_radius_km: float = 15.0,
                              min_cluster_size: int = 2,
                              progress_callback: Optional[Callable] = None) -> List[gpd.GeoDataFrame]:
        """
        Process POIs concurrently to generate isochrones.
        
        Args:
            pois: List of POI dictionaries
            travel_time_minutes: Travel time limit for isochrones
            max_cluster_radius_km: Maximum clustering radius
            min_cluster_size: Minimum POIs per cluster
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of isochrone GeoDataFrames
        """
        start_time = time.time()
        
        # Initialize stats
        self._stats.total_pois = len(pois)
        
        logger.info(f"Starting concurrent processing of {len(pois)} POIs")
        
        # Step 1: Create optimized clusters
        logger.info("Creating optimized POI clusters...")
        clusters = create_optimized_clusters(
            pois=pois,
            travel_time_minutes=travel_time_minutes,
            max_cluster_radius_km=max_cluster_radius_km,
            min_cluster_size=min_cluster_size
        )
        
        self._stats.total_clusters = len(clusters)
        self._stats.avg_cluster_size = len(pois) / len(clusters) if clusters else 0
        
        logger.info(f"Created {len(clusters)} clusters (avg size: {self._stats.avg_cluster_size:.1f})")
        
        # Step 2: Download networks concurrently
        network_start_time = time.time()
        logger.info("Downloading networks concurrently...")
        
        # Monitor resources and adjust workers
        resources = self._monitor_system_resources()
        network_workers, isochrone_workers = self._adjust_workers_based_on_resources(resources)
        
        self._stats.max_concurrent_downloads = network_workers
        self._stats.max_concurrent_isochrones = isochrone_workers
        
        successful_clusters = []
        
        with ThreadPoolExecutor(max_workers=network_workers) as executor:
            # Submit all network download tasks
            future_to_cluster = {
                executor.submit(self._download_cluster_network, cluster, travel_time_minutes): cluster
                for cluster in clusters
            }
            
            # Process completed downloads with progress tracking
            with get_progress_bar(total=len(clusters), desc="Downloading Networks", unit="cluster") as pbar:
                for future in as_completed(future_to_cluster):
                    cluster = future_to_cluster[future]
                    try:
                        cluster_id, network = future.result()
                        if network is not None:
                            successful_clusters.append(cluster)
                            self._stats.networks_downloaded += 1
                        else:
                            logger.warning(f"Failed to download network for cluster {cluster_id}")
                    except Exception as e:
                        logger.error(f"Network download failed for cluster {cluster.cluster_id}: {e}")
                    
                    pbar.update(1)
                    
                    if progress_callback:
                        progress_callback("network_download", len(successful_clusters), len(clusters))
        
        self._stats.network_download_time_seconds = time.time() - network_start_time
        
        # Get cache statistics
        cache_stats = self.cache.get_cache_stats()
        if cache_stats.total_requests > 0:
            self._stats.cache_hit_rate = cache_stats.cache_hits / cache_stats.total_requests
            self._stats.networks_cached = cache_stats.cache_hits
        
        logger.info(f"Downloaded {len(successful_clusters)} networks "
                   f"(cache hit rate: {self._stats.cache_hit_rate:.1%})")
        
        # Step 3: Generate isochrones concurrently
        isochrone_start_time = time.time()
        logger.info("Generating isochrones concurrently...")
        
        all_isochrones = []
        total_pois_to_process = sum(len(cluster.pois) for cluster in successful_clusters)
        
        with ThreadPoolExecutor(max_workers=isochrone_workers) as executor:
            # Submit isochrone generation tasks
            future_to_cluster = {
                executor.submit(self._generate_cluster_isochrones, cluster, travel_time_minutes): cluster
                for cluster in successful_clusters
            }
            
            # Process completed isochrone generations
            processed_pois = 0
            with get_progress_bar(total=total_pois_to_process, desc="Generating Isochrones", unit="POI") as pbar:
                for future in as_completed(future_to_cluster):
                    cluster = future_to_cluster[future]
                    try:
                        cluster_isochrones = future.result()
                        all_isochrones.extend(cluster_isochrones)
                        processed_pois += len(cluster.pois)
                        pbar.update(len(cluster.pois))
                        
                        if progress_callback:
                            progress_callback("isochrone_generation", processed_pois, total_pois_to_process)
                            
                    except Exception as e:
                        logger.error(f"Isochrone generation failed for cluster {cluster.cluster_id}: {e}")
                        processed_pois += len(cluster.pois)
                        pbar.update(len(cluster.pois))
        
        self._stats.isochrone_generation_time_seconds = time.time() - isochrone_start_time
        self._stats.total_time_seconds = time.time() - start_time
        
        # Log final statistics
        self._log_processing_stats()
        
        return all_isochrones
    
    def _log_processing_stats(self):
        """Log detailed processing statistics."""
        stats = self._stats
        
        logger.info("=== Concurrent Processing Statistics ===")
        logger.info(f"Total POIs processed: {stats.total_pois}")
        logger.info(f"Total clusters created: {stats.total_clusters}")
        logger.info(f"Average cluster size: {stats.avg_cluster_size:.1f}")
        logger.info(f"Networks downloaded: {stats.networks_downloaded}")
        logger.info(f"Networks from cache: {stats.networks_cached}")
        logger.info(f"Cache hit rate: {stats.cache_hit_rate:.1%}")
        logger.info(f"Isochrones generated: {stats.isochrones_generated}")
        logger.info(f"Failed isochrones: {stats.failed_isochrones}")
        logger.info(f"Success rate: {stats.isochrones_generated / stats.total_pois:.1%}")
        logger.info(f"Total processing time: {stats.total_time_seconds:.1f}s")
        logger.info(f"Network download time: {stats.network_download_time_seconds:.1f}s")
        logger.info(f"Isochrone generation time: {stats.isochrone_generation_time_seconds:.1f}s")
        logger.info(f"Max concurrent downloads: {stats.max_concurrent_downloads}")
        logger.info(f"Max concurrent isochrones: {stats.max_concurrent_isochrones}")
        
        # Calculate efficiency metrics
        if stats.total_pois > 0:
            time_per_poi = stats.total_time_seconds / stats.total_pois
            logger.info(f"Average time per POI: {time_per_poi:.2f}s")
            
        if stats.total_clusters > 0:
            downloads_saved = stats.total_pois - stats.networks_downloaded
            savings_percent = (downloads_saved / stats.total_pois) * 100
            logger.info(f"Network downloads saved: {downloads_saved} ({savings_percent:.1f}%)")
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get current processing statistics."""
        return self._stats

# Convenience function for simple concurrent processing
def process_isochrones_concurrent(pois: List[Dict[str, Any]],
                                travel_time_minutes: int = 15,
                                max_cluster_radius_km: float = 15.0,
                                min_cluster_size: int = 2,
                                max_network_workers: int = 8,
                                max_isochrone_workers: Optional[int] = None,
                                cache: Optional[ModernNetworkCache] = None,
                                progress_callback: Optional[Callable] = None) -> List[gpd.GeoDataFrame]:
    """
    Process isochrones concurrently with optimized settings.
    
    Args:
        pois: List of POI dictionaries
        travel_time_minutes: Travel time limit
        max_cluster_radius_km: Maximum clustering radius
        min_cluster_size: Minimum POIs per cluster
        max_network_workers: Maximum concurrent network downloads
        max_isochrone_workers: Maximum concurrent isochrone calculations
        cache: Network cache instance
        progress_callback: Optional progress callback
        
    Returns:
        List of isochrone GeoDataFrames
    """
    processor = ConcurrentIsochroneProcessor(
        max_network_workers=max_network_workers,
        max_isochrone_workers=max_isochrone_workers,
        cache=cache
    )
    
    return processor.process_pois_concurrent(
        pois=pois,
        travel_time_minutes=travel_time_minutes,
        max_cluster_radius_km=max_cluster_radius_km,
        min_cluster_size=min_cluster_size,
        progress_callback=progress_callback
    ) 