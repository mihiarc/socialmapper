#!/usr/bin/env python3
"""Simple disk-based caching for network graphs.

Uses diskcache for simple, reliable, and thread-safe caching of OSM network
graphs used in isochrone generation.
"""

import atexit
import hashlib
import logging
import os
from pathlib import Path

import diskcache as dc
import networkx as nx
import osmnx as ox

from ..constants import (
    MAX_CYCLING_SPEED_KPH,
    MAX_WALKING_SPEED_KPH,
    NORMAL_CYCLING_SPEED_KPH,
    NORMAL_WALKING_SPEED_KPH,
    US_CANADA_BORDER_LAT,
)
from .travel_modes import TravelMode, get_default_speed, get_highway_speeds, get_network_type

logger = logging.getLogger(__name__)

# Global cache instance (thread-safe, managed by diskcache)
_cache: dc.Cache | None = None


def _cleanup_cache():
    """Cleanup function to close global cache on exit."""
    global _cache
    if _cache is not None:
        try:
            _cache.close()
            logger.debug("Closed global network cache")
        except (OSError, dc.Timeout) as e:
            logger.warning(f"Error closing cache on exit: {e}")


# Register cleanup handler
atexit.register(_cleanup_cache)


def _validate_cached_network(network: nx.MultiDiGraph) -> bool:
    """Validate that cached network is not corrupted.

    Parameters
    ----------
    network : nx.MultiDiGraph
        Network graph to validate.

    Returns
    -------
    bool
        True if network is valid, False otherwise.
    """
    try:
        if not isinstance(network, nx.MultiDiGraph):
            logger.warning("Cached network is not a MultiDiGraph")
            return False
        if len(network.nodes) == 0:
            logger.warning("Cached network has no nodes")
            return False
        if 'crs' not in network.graph:
            logger.warning("Cached network missing CRS information")
            return False
        return True
    except (AttributeError, TypeError, KeyError) as e:
        logger.warning(f"Network validation failed: {e}")
        return False


def get_cache() -> dc.Cache:
    """Get or create global cache instance.

    Uses environment variables for configuration:
    - SOCIALMAPPER_CACHE_DIR: Base cache directory (default: 'cache')
    - SOCIALMAPPER_CACHE_SIZE_GB: Cache size limit in GB (default: 5)

    Returns
    -------
    dc.Cache
        Thread-safe disk cache instance.
    """
    global _cache
    if _cache is None:
        # Use environment variables for configuration
        base_cache_dir = os.environ.get('SOCIALMAPPER_CACHE_DIR', 'cache')
        cache_dir = Path(base_cache_dir) / 'networks'
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Configure cache size from environment
        size_gb = int(os.environ.get('SOCIALMAPPER_CACHE_SIZE_GB', '5'))
        size_limit = size_gb * 1024**3  # Convert GB to bytes

        logger.info(f"Initializing network cache: dir={cache_dir}, size_limit={size_gb}GB")

        # diskcache handles thread safety, size limits, eviction automatically
        _cache = dc.Cache(str(cache_dir), size_limit=size_limit)
    return _cache


def _generate_cache_key(
    bbox: tuple[float, float, float, float],
    network_type: str,
    travel_time_minutes: int,
    country: str | None = None,
) -> str:
    """Generate unique cache key for network parameters.

    Parameters
    ----------
    bbox : tuple[float, float, float, float]
        Bounding box (min_lat, min_lon, max_lat, max_lon).
    network_type : str
        Type of network ('drive', 'walk', 'bike').
    travel_time_minutes : int
        Travel time in minutes.
    country : str, optional
        ISO 3166-1 alpha-2 country code.

    Returns
    -------
    str
        SHA-256 hash of parameters.
    """
    # Round bbox to reduce cache fragmentation
    rounded_bbox = tuple(round(coord, 4) for coord in bbox)
    country_str = f"_{country}" if country else ""
    key_data = f"{rounded_bbox}_{network_type}_{travel_time_minutes}{country_str}"
    return hashlib.sha256(key_data.encode()).hexdigest()


def download_and_cache_network(
    bbox: tuple[float, float, float, float],
    network_type: str = "drive",
    travel_time_minutes: int = 15,
    cluster_size: int = 1,
    cache: dc.Cache | None = None,
    travel_mode: TravelMode | None = None,
    restrict_to_country: str | None = None,
) -> nx.MultiDiGraph | None:
    """Download network and cache it, or retrieve from cache if available.

    Parameters
    ----------
    bbox : tuple[float, float, float, float]
        Bounding box (min_lat, min_lon, max_lat, max_lon).
    network_type : str, optional
        Type of network to download (deprecated, use travel_mode).
    travel_time_minutes : int, optional
        Travel time requirement in minutes.
    cluster_size : int, optional
        Number of POIs this network will serve (unused, kept for API compatibility).
    cache : dc.Cache, optional
        Cache instance to use (uses global cache if None).
    travel_mode : TravelMode, optional
        Travel mode (walk, bike, drive).
    restrict_to_country : str, optional
        ISO 3166-1 alpha-2 country code (e.g., 'US' for United States).

    Returns
    -------
    nx.MultiDiGraph | None
        Network graph or None if download failed.

    Examples
    --------
    >>> bbox = (48.0, -116.0, 49.0, -115.0)
    >>> network = download_and_cache_network(bbox, travel_mode=TravelMode.DRIVE)
    """
    if cache is None:
        cache = get_cache()

    # Handle travel mode vs network type
    if travel_mode is not None:
        network_type = get_network_type(travel_mode)
        default_speed = get_default_speed(travel_mode)
        highway_speeds = get_highway_speeds(travel_mode)
    else:
        # Legacy support - default to drive mode
        travel_mode = TravelMode.DRIVE
        network_type = "drive"
        default_speed = 50.0
        highway_speeds = get_highway_speeds(TravelMode.DRIVE)

    # Generate cache key
    cache_key = _generate_cache_key(bbox, network_type, travel_time_minutes, restrict_to_country)

    # Check cache first
    cached_network = cache.get(cache_key)
    if cached_network is not None:
        # Validate cached network before returning
        if _validate_cached_network(cached_network):
            logger.debug(f"Cache hit for network {cache_key}")
            return cached_network
        else:
            # Invalid cached data - remove and re-download
            logger.warning(f"Removing invalid cached network {cache_key}")
            cache.delete(cache_key)

    # Download new network
    try:
        country_info = f" (country={restrict_to_country})" if restrict_to_country else ""
        logger.info(f"Downloading network for bbox {bbox} with network_type={network_type}{country_info}")

        min_lat, min_lon, max_lat, max_lon = bbox
        # OSMnx expects bbox as (left, bottom, right, top) = (min_lon, min_lat, max_lon, max_lat)
        osm_bbox = (min_lon, min_lat, max_lon, max_lat)

        # Download network
        graph = ox.graph_from_bbox(bbox=osm_bbox, network_type=network_type)

        # Apply country restriction if specified
        if restrict_to_country == "US":
            # Simple latitude-based filter for US-Canada border (49th parallel)
            edges_to_remove = []
            for u, v, key, _data in graph.edges(keys=True, data=True):
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                # Check if either node is north of 49°N (in Canada)
                if u_data.get('y', 0) > US_CANADA_BORDER_LAT or v_data.get('y', 0) > US_CANADA_BORDER_LAT:
                    edges_to_remove.append((u, v, key))

            # Remove cross-border edges and isolated nodes
            for u, v, key in edges_to_remove:
                if graph.has_edge(u, v, key):
                    graph.remove_edge(u, v, key)

            nodes_to_remove = [node for node in graph.nodes() if graph.degree(node) == 0]
            graph.remove_nodes_from(nodes_to_remove)

            if edges_to_remove:
                logger.info(f"Filtered network to US only: removed {len(edges_to_remove)} cross-border edges and {len(nodes_to_remove)} isolated nodes")

        # Add speeds and travel times
        graph = ox.add_edge_speeds(graph, hwy_speeds=highway_speeds, fallback=default_speed)
        graph = ox.add_edge_travel_times(graph)

        # Apply mode-specific speed adjustments
        if travel_mode == TravelMode.WALK:
            for _u, _v, data in graph.edges(data=True):
                if "speed_kph" in data and data["speed_kph"] > MAX_WALKING_SPEED_KPH:
                    data["speed_kph"] = NORMAL_WALKING_SPEED_KPH
                    data["travel_time"] = data["length"] / (data["speed_kph"] * 1000 / 3600)
        elif travel_mode == TravelMode.BIKE:
            for _u, _v, data in graph.edges(data=True):
                if "speed_kph" in data and data["speed_kph"] > MAX_CYCLING_SPEED_KPH:
                    data["speed_kph"] = NORMAL_CYCLING_SPEED_KPH
                    data["travel_time"] = data["length"] / (data["speed_kph"] * 1000 / 3600)

        graph = ox.project_graph(graph)

        # Log speed statistics
        speeds = [data.get("speed_kph", 0) for u, v, data in graph.edges(data=True)]
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            logger.info(
                f"Network speeds for {travel_mode.value} mode - "
                f"avg: {avg_speed:.1f} km/h, nodes: {len(graph.nodes)}, edges: {len(graph.edges)}"
            )

        # Store in cache (diskcache handles compression automatically)
        cache.set(cache_key, graph)
        logger.info(f"Cached network {cache_key}")

        return graph

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid data when downloading network for bbox {bbox}: {e}")
        return None
    except nx.NetworkXError as e:
        logger.error(f"NetworkX error for bbox {bbox}: {e}")
        return None
    except (OSError, ConnectionError) as e:
        logger.error(f"Network/IO error downloading network for bbox {bbox}: {e}")
        return None


def get_cache_stats() -> dict:
    """Get cache statistics.

    Returns
    -------
    dict
        Cache statistics including size and volume.

    Examples
    --------
    >>> stats = get_cache_stats()
    >>> print(f"Cache size: {stats['size_mb']:.2f} MB")
    """
    cache = get_cache()
    return {
        "size_mb": cache.volume() / 1024**2,
        "count": len(cache),
    }


def clear_cache():
    """Clear all cached networks.

    Examples
    --------
    >>> clear_cache()
    """
    cache = get_cache()
    cache.clear()
    logger.info("Cache cleared successfully")


# Compatibility aliases for existing code
get_global_cache = get_cache
