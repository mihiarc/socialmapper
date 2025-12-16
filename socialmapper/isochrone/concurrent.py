#!/usr/bin/env python3
"""Concurrent Isochrone Processing System.

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

import copy
import logging
import multiprocessing as mp
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import diskcache as dc
import geopandas as gpd
import psutil

from ..constants import (
    HIGH_CPU_USAGE_THRESHOLD,
    HIGH_MEMORY_USAGE_THRESHOLD,
    MIN_ISOCHRONE_AREA_KM2,
    MIN_NETWORK_NODES,
    MIN_TRAVEL_TIME_FOR_NETWORK_VALIDATION,
    NETWORK_MAX_RETRIES,
)
from ..progress import get_progress_bar
from .cache import download_and_cache_network, get_cache, get_cache_stats
from .clustering import (
    OptimizedPOICluster,
    create_isochrone_from_poi_with_network,
    create_optimized_clusters,
)
from .travel_modes import TravelMode

logger = logging.getLogger(__name__)


def _generate_cluster_isochrones_worker(
    cluster: OptimizedPOICluster,
    travel_time_minutes: int,
    travel_mode: TravelMode = TravelMode.DRIVE,
) -> list[gpd.GeoDataFrame]:
    """Worker function for ProcessPoolExecutor to generate isochrones.

    This is a module-level function that can be pickled for
    multiprocessing.

    Parameters
    ----------
    cluster : OptimizedPOICluster
        The cluster to process.
    travel_time_minutes : int
        Travel time limit.
    travel_mode : TravelMode, optional
        Mode of travel, by default TravelMode.DRIVE.

    Returns
    -------
    list of gpd.GeoDataFrame
        List of isochrone GeoDataFrames.
    """
    isochrones = []

    if cluster.network is None:
        return isochrones

    for poi in cluster.pois:
        try:
            # Create a deep copy of the network to avoid shared state issues
            network_copy = copy.deepcopy(cluster.network)

            isochrone_gdf = create_isochrone_from_poi_with_network(
                poi=poi,
                network=network_copy,
                network_crs=cluster.network_crs,
                travel_time_minutes=travel_time_minutes,
                travel_mode=travel_mode,
            )

            if isochrone_gdf is not None:
                # Validate isochrone size for rural areas
                area_km2 = isochrone_gdf.geometry[0].area / 1_000_000  # Convert to km²

                # Expected minimum area based on travel time (very rough estimate)
                min_expected_area = (travel_time_minutes / 30) * 100

                if area_km2 < min_expected_area and area_km2 < MIN_ISOCHRONE_AREA_KM2:
                    logger.warning(
                        f"Suspiciously small isochrone for POI {poi.get('id', 'unknown')}: "
                        f"{area_km2:.1f} km² (expected > {min_expected_area:.0f} km²)"
                    )

                isochrones.append(isochrone_gdf)

        except (ValueError, KeyError, TypeError) as e:
            logger.error(
                f"Data error generating isochrone for POI {poi.get('id', 'unknown')}: {e}"
            )
        except (OSError, ConnectionError) as e:
            logger.error(
                f"Network/IO error generating isochrone for POI {poi.get('id', 'unknown')}: {e}"
            )

    return isochrones


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

    def __init__(
        self,
        max_network_workers: int = 8,
        max_isochrone_workers: int | None = None,
        cache: dc.Cache | None = None,
    ):
        """Initialize the concurrent processor.

        Parameters
        ----------
        max_network_workers : int, optional
            Maximum concurrent network downloads, by default 8.
        max_isochrone_workers : int or None, optional
            Maximum concurrent isochrone calculations (defaults to CPU
            count), by default None.
        cache : dc.Cache or None, optional
            Network cache instance, by default None.
        """
        self.max_network_workers = max_network_workers
        self.max_isochrone_workers = max_isochrone_workers or mp.cpu_count()
        self.cache = cache or get_cache()

        # Performance monitoring
        self._stats = ProcessingStats(
            total_pois=0,
            total_clusters=0,
            networks_downloaded=0,
            networks_cached=0,
            isochrones_generated=0,
            failed_isochrones=0,
            total_time_seconds=0.0,
            network_download_time_seconds=0.0,
            isochrone_generation_time_seconds=0.0,
            cache_hit_rate=0.0,
            avg_cluster_size=0.0,
            max_concurrent_downloads=0,
            max_concurrent_isochrones=0,
        )

        # Resource monitoring
        self._monitor_resources = True
        self._resource_check_interval = 5.0  # seconds

    def _monitor_system_resources(self) -> dict[str, float]:
        """Monitor system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1024**3,
                "disk_free_gb": disk.free / 1024**3,
            }
        except (OSError, AttributeError, psutil.Error) as e:
            logger.warning(f"Failed to monitor resources: {e}")
            return {}

    def _adjust_workers_based_on_resources(self, resources: dict[str, float]) -> tuple[int, int]:
        """Adjust worker counts based on system resources."""
        network_workers = self.max_network_workers
        isochrone_workers = self.max_isochrone_workers

        # Reduce workers if system is under stress
        if resources.get("cpu_percent", 0) > HIGH_CPU_USAGE_THRESHOLD:
            isochrone_workers = max(1, isochrone_workers // 2)
            logger.info(f"High CPU usage, reducing isochrone workers to {isochrone_workers}")

        if resources.get("memory_percent", 0) > HIGH_MEMORY_USAGE_THRESHOLD:
            network_workers = max(1, network_workers // 2)
            isochrone_workers = max(1, isochrone_workers // 2)
            logger.info(
                f"High memory usage, reducing workers to {network_workers}/{isochrone_workers}"
            )

        return network_workers, isochrone_workers

    def _download_cluster_network(
        self,
        cluster: OptimizedPOICluster,
        travel_time_minutes: int,
        travel_mode: TravelMode = TravelMode.DRIVE,
        retry_count: int = 0,
    ) -> tuple[str, Any | None]:
        """Download network for a cluster (thread-safe) with retry logic.

        Parameters
        ----------
        cluster : OptimizedPOICluster
            The cluster to download network for.
        travel_time_minutes : int
            Travel time limit.
        travel_mode : TravelMode, optional
            Mode of travel, by default TravelMode.DRIVE.
        retry_count : int, optional
            Current retry attempt number, by default 0.

        Returns
        -------
        tuple of (str, Any or None)
            Tuple of (cluster_id, network graph or None).
        """
        try:
            # Get bbox with potentially increased buffer on retry
            buffer_multiplier = 1.0 + (retry_count * 0.5)  # Increase buffer by 50% per retry
            bbox = cluster.get_network_bbox(
                travel_time_minutes,
                buffer_km=2.0 * buffer_multiplier
            )

            network = download_and_cache_network(
                bbox=bbox,
                travel_time_minutes=travel_time_minutes,
                cluster_size=len(cluster),
                cache=self.cache,
                travel_mode=travel_mode,
            )

            if network is not None:
                # Validate network size for rural areas
                if len(network.nodes) < MIN_NETWORK_NODES and travel_time_minutes >= MIN_TRAVEL_TIME_FOR_NETWORK_VALIDATION:
                    logger.warning(
                        f"Small network for cluster {cluster.cluster_id}: "
                        f"{len(network.nodes)} nodes for {travel_time_minutes} min travel"
                    )
                    # Retry with larger buffer if this is the first attempt
                    if retry_count < NETWORK_MAX_RETRIES:
                        # Exponential backoff: 1s, 2s, 4s...
                        wait_time = 2 ** retry_count
                        logger.info(f"Retrying network download with larger buffer after {wait_time}s (attempt {retry_count + 1})")
                        time.sleep(wait_time)
                        return self._download_cluster_network(
                            cluster, travel_time_minutes, travel_mode, retry_count + 1
                        )

                cluster.network = network
                cluster.network_crs = network.graph["crs"]
                return cluster.cluster_id, network
            else:
                logger.error(f"Failed to download network for cluster {cluster.cluster_id}")
                return cluster.cluster_id, None

        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Data error downloading network for cluster {cluster.cluster_id}: {e}")
            return cluster.cluster_id, None
        except (OSError, ConnectionError) as e:
            logger.error(f"Network error downloading cluster {cluster.cluster_id}: {e}")
            # Retry on network error if we haven't exceeded retry limit
            if retry_count < NETWORK_MAX_RETRIES:
                # Exponential backoff on errors
                wait_time = 2 ** retry_count
                logger.info(f"Retrying after error with {wait_time}s backoff (attempt {retry_count + 1})")
                time.sleep(wait_time)
                return self._download_cluster_network(
                    cluster, travel_time_minutes, travel_mode, retry_count + 1
                )
            return cluster.cluster_id, None

    def _generate_cluster_isochrones(
        self,
        cluster: OptimizedPOICluster,
        travel_time_minutes: int,
        travel_mode: TravelMode = TravelMode.DRIVE,
    ) -> list[gpd.GeoDataFrame]:
        """Generate isochrones for all POIs in a cluster."""
        isochrones = []

        if cluster.network is None:
            logger.error(f"No network available for cluster {cluster.cluster_id}")
            return isochrones

        for poi in cluster.pois:
            try:
                # Instead of deep copying entire network, create isochrone directly
                # The isochrone function only reads from the network, doesn't modify it
                # This avoids expensive deep copy operations
                isochrone_gdf = create_isochrone_from_poi_with_network(
                    poi=poi,
                    network=cluster.network,  # Use original network (read-only)
                    network_crs=cluster.network_crs,
                    travel_time_minutes=travel_time_minutes,
                    travel_mode=travel_mode,
                )

                if isochrone_gdf is not None:
                    # Validate isochrone size for quality control
                    # Use EPSG:5070 (Conus Albers) for accurate area calculation in CONUS
                    # This replaces EPSG:3857 which distorts areas by 32-140% at US latitudes
                    area_km2 = isochrone_gdf.to_crs("EPSG:5070").geometry[0].area / 1_000_000  # Convert to km²

                    # Expected minimum area based on travel time and mode
                    # These are conservative estimates to catch obvious errors
                    if travel_mode == TravelMode.DRIVE:
                        # For driving, expect larger areas
                        min_expected_area = (travel_time_minutes / 30) * 50  # At least 50 km² per 30 min
                    elif travel_mode == TravelMode.BIKE:
                        min_expected_area = (travel_time_minutes / 30) * 20  # At least 20 km² per 30 min
                    else:  # WALK
                        min_expected_area = (travel_time_minutes / 30) * 5  # At least 5 km² per 30 min

                    if area_km2 < min_expected_area:
                        logger.warning(
                            f"Small isochrone detected for POI {poi.get('id', 'unknown')}: "
                            f"{area_km2:.1f} km² (expected > {min_expected_area:.0f} km² for {travel_mode.value})"
                        )
                        # Mark for potential retry with larger network
                        isochrone_gdf["needs_validation"] = True
                    else:
                        isochrone_gdf["needs_validation"] = False

                    isochrones.append(isochrone_gdf)
                    self._stats.isochrones_generated += 1
                else:
                    self._stats.failed_isochrones += 1

            except (ValueError, KeyError, TypeError) as e:
                logger.error(
                    f"Data error generating isochrone for POI {poi.get('id', 'unknown')}: {e}"
                )
                self._stats.failed_isochrones += 1
            except (OSError, ConnectionError) as e:
                logger.error(
                    f"Network/IO error generating isochrone for POI {poi.get('id', 'unknown')}: {e}"
                )
                self._stats.failed_isochrones += 1

        return isochrones

    def process_pois_concurrent(
        self,
        pois: list[dict[str, Any]],
        travel_time_minutes: int = 15,
        max_cluster_radius_km: float = 15.0,
        min_cluster_size: int = 2,
        progress_callback: Callable | None = None,
        travel_mode: TravelMode = TravelMode.DRIVE,
    ) -> list[gpd.GeoDataFrame]:
        """Process POIs concurrently to generate isochrones.

        Parameters
        ----------
        pois : list of dict
            List of POI dictionaries.
        travel_time_minutes : int, optional
            Travel time limit for isochrones, by default 15.
        max_cluster_radius_km : float, optional
            Maximum clustering radius, by default 15.0.
        min_cluster_size : int, optional
            Minimum POIs per cluster, by default 2.
        progress_callback : Callable or None, optional
            Optional callback for progress updates, by default None.
        travel_mode : TravelMode, optional
            Mode of travel (walk, bike, drive), by default
            TravelMode.DRIVE.

        Returns
        -------
        list of gpd.GeoDataFrame
            List of isochrone GeoDataFrames.
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
            min_cluster_size=min_cluster_size,
        )

        self._stats.total_clusters = len(clusters)
        self._stats.avg_cluster_size = len(pois) / len(clusters) if clusters else 0

        logger.info(
            f"Created {len(clusters)} clusters (avg size: {self._stats.avg_cluster_size:.1f})"
        )

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
                executor.submit(
                    self._download_cluster_network, cluster, travel_time_minutes, travel_mode
                ): cluster
                for cluster in clusters
            }

            # Process completed downloads with progress tracking
            with get_progress_bar(
                total=len(clusters), desc="Downloading Networks", unit="cluster"
            ) as pbar:
                for future in as_completed(future_to_cluster):
                    cluster = future_to_cluster[future]
                    try:
                        cluster_id, network = future.result()
                        if network is not None:
                            successful_clusters.append(cluster)
                            self._stats.networks_downloaded += 1
                        else:
                            logger.warning(f"Failed to download network for cluster {cluster_id}")
                    except (ValueError, KeyError, TypeError) as e:
                        logger.error(
                            f"Data error in network download for cluster {cluster.cluster_id}: {e}"
                        )
                    except (OSError, ConnectionError, TimeoutError) as e:
                        logger.error(
                            f"Network error downloading cluster {cluster.cluster_id}: {e}"
                        )

                    pbar.update(1)

                    if progress_callback:
                        progress_callback(
                            "network_download", len(successful_clusters), len(clusters)
                        )

        self._stats.network_download_time_seconds = time.time() - network_start_time

        # Get cache statistics
        cache_stats = get_cache_stats()
        # Note: diskcache doesn't track hits/misses, so we just log cache size
        logger.debug(f"Cache contains {cache_stats['count']} networks, {cache_stats['size_mb']:.2f} MB")

        logger.info(
            f"Downloaded {len(successful_clusters)} networks "
            f"(cache hit rate: {self._stats.cache_hit_rate:.1%})"
        )

        # Step 3: Generate isochrones using ProcessPoolExecutor for CPU-intensive work
        isochrone_start_time = time.time()
        logger.info("Generating isochrones concurrently using process pool...")

        all_isochrones = []
        total_pois_to_process = sum(len(cluster.pois) for cluster in successful_clusters)

        # Use ThreadPoolExecutor (ProcessPoolExecutor requires pickleable objects
        # which is complex with network graphs and shapely geometries)
        with ThreadPoolExecutor(max_workers=isochrone_workers) as executor:
            # Submit isochrone generation tasks
            future_to_cluster = {
                executor.submit(
                    self._generate_cluster_isochrones, cluster, travel_time_minutes, travel_mode
                ): cluster
                for cluster in successful_clusters
            }

            # Process completed isochrone generations
            processed_pois = 0
            with get_progress_bar(
                total=total_pois_to_process, desc="Generating Isochrones", unit="POI"
            ) as pbar:
                for future in as_completed(future_to_cluster):
                    cluster = future_to_cluster[future]
                    try:
                        cluster_isochrones = future.result()
                        all_isochrones.extend(cluster_isochrones)
                        processed_pois += len(cluster.pois)
                        pbar.update(len(cluster.pois))

                        if progress_callback:
                            progress_callback(
                                "isochrone_generation", processed_pois, total_pois_to_process
                            )

                    except (ValueError, KeyError, TypeError) as e:
                        logger.error(
                            f"Data error generating isochrones for cluster {cluster.cluster_id}: {e}"
                        )
                        processed_pois += len(cluster.pois)
                        pbar.update(len(cluster.pois))
                    except (OSError, ConnectionError, TimeoutError) as e:
                        logger.error(
                            f"Network/IO error generating isochrones for cluster {cluster.cluster_id}: {e}"
                        )
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
def process_isochrones_concurrent(
    pois: list[dict[str, Any]],
    travel_time_minutes: int = 15,
    max_cluster_radius_km: float = 15.0,
    min_cluster_size: int = 2,
    max_network_workers: int = 8,
    max_isochrone_workers: int | None = None,
    cache: dc.Cache | None = None,
    progress_callback: Callable | None = None,
    travel_mode: TravelMode = TravelMode.DRIVE,
) -> list[gpd.GeoDataFrame]:
    """Process isochrones concurrently with optimized settings.

    Parameters
    ----------
    pois : list of dict
        List of POI dictionaries.
    travel_time_minutes : int, optional
        Travel time limit, by default 15.
    max_cluster_radius_km : float, optional
        Maximum clustering radius, by default 15.0.
    min_cluster_size : int, optional
        Minimum POIs per cluster, by default 2.
    max_network_workers : int, optional
        Maximum concurrent network downloads, by default 8.
    max_isochrone_workers : int or None, optional
        Maximum concurrent isochrone calculations, by default None.
    cache : dc.Cache or None, optional
        Network cache instance, by default None.
    progress_callback : Callable or None, optional
        Optional progress callback, by default None.
    travel_mode : TravelMode, optional
        Mode of travel (walk, bike, drive), by default
        TravelMode.DRIVE.

    Returns
    -------
    list of gpd.GeoDataFrame
        List of isochrone GeoDataFrames.
    """
    processor = ConcurrentIsochroneProcessor(
        max_network_workers=max_network_workers,
        max_isochrone_workers=max_isochrone_workers,
        cache=cache,
    )

    return processor.process_pois_concurrent(
        pois=pois,
        travel_time_minutes=travel_time_minutes,
        max_cluster_radius_km=max_cluster_radius_km,
        min_cluster_size=min_cluster_size,
        progress_callback=progress_callback,
        travel_mode=travel_mode,
    )
