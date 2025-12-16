#!/usr/bin/env python3
"""Modern Intelligent Spatial Clustering Engine for Isochrone Generation.

This module implements advanced POI clustering using machine learning algorithms
to optimize network downloads and processing for large-scale isochrone generation.

Key Features:
- DBSCAN clustering with haversine distance metric
- Intelligent cluster sizing based on travel time requirements
- Advanced spatial optimization algorithms
- Performance monitoring and benchmarking
"""

# Setup logging
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
from shapely.geometry import Point
from sklearn.cluster import DBSCAN

from ..constants import (
    EFFICIENCY_EXCELLENT_THRESHOLD,
    EFFICIENCY_GOOD_THRESHOLD,
    MAX_CYCLING_SPEED_KPH,
    MAX_WALKING_SPEED_KPH,
    MIN_POLYGON_POINTS,
    NORMAL_CYCLING_SPEED_KPH,
    NORMAL_WALKING_SPEED_KPH,
    RURAL_CLUSTER_SPAN_KM,
    SUBURBAN_CLUSTER_SPAN_KM,
)
from .travel_modes import TravelMode, get_default_speed, get_highway_speeds, get_network_type

logger = logging.getLogger(__name__)


@dataclass
class ClusterMetrics:
    """Performance metrics for clustering operations."""

    total_pois: int
    num_clusters: int
    avg_cluster_size: float
    max_cluster_size: int
    min_cluster_size: int
    clustering_time_seconds: float
    network_downloads_saved: int
    estimated_time_savings_percent: float


class IntelligentPOIClusterer:
    """Advanced POI clustering using machine learning algorithms."""

    def __init__(self, max_cluster_radius_km: float = 15.0, min_cluster_size: int = 2):
        """Initialize the intelligent clusterer.

        Parameters
        ----------
        max_cluster_radius_km : float, optional
            Maximum radius for clustering in kilometers, by default 15.0.
        min_cluster_size : int, optional
            Minimum number of POIs to form a cluster, by default 2.
        """
        self.max_cluster_radius_km = max_cluster_radius_km
        self.min_cluster_size = min_cluster_size
        self._lock = threading.Lock()

    def cluster_pois(self, pois: list[dict], travel_time_minutes: int = 15) -> list[list[dict]]:
        """Cluster POIs using DBSCAN with geographic distance.

        Parameters
        ----------
        pois : list of dict
            List of POI dictionaries with 'lat' and 'lon' keys.
        travel_time_minutes : int, optional
            Travel time limit to adjust clustering parameters,
            by default 15.

        Returns
        -------
        list of list of dict
            List of POI clusters (each cluster is a list of POIs).
        """
        start_time = time.time()

        if len(pois) <= 1:
            return [pois]

        # Extract coordinates
        coords = np.array([[poi["lat"], poi["lon"]] for poi in pois])

        # Adjust clustering radius based on travel time
        # Larger travel times allow for larger clusters
        adjusted_radius = min(
            self.max_cluster_radius_km, self.max_cluster_radius_km * (travel_time_minutes / 15.0)
        )

        # Use DBSCAN clustering with haversine metric
        # eps in radians for haversine distance
        eps_radians = adjusted_radius / 6371.0  # Earth radius in km

        clustering = DBSCAN(
            eps=eps_radians, min_samples=self.min_cluster_size, metric="haversine"
        ).fit(np.radians(coords))

        # Group POIs by cluster
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(pois[idx])

        # Handle noise points (label = -1) as individual clusters
        result = []
        for label, cluster_pois in clusters.items():
            if label == -1:  # Noise points
                result.extend([[poi] for poi in cluster_pois])
            else:
                result.append(cluster_pois)

        time.time() - start_time

        # Log clustering results
        num_clusters = len(result)
        network_downloads_saved = len(pois) - num_clusters
        savings_percent = (network_downloads_saved / len(pois)) * 100 if len(pois) > 0 else 0

        logger.info(
            f"Clustered {len(pois)} POIs into {num_clusters} clusters "
            f"(saved {network_downloads_saved} downloads, {savings_percent:.1f}% reduction)"
        )

        return result

    def get_cluster_metrics(self, pois: list[dict], clusters: list[list[dict]]) -> ClusterMetrics:
        """Calculate detailed metrics for clustering performance."""
        cluster_sizes = [len(cluster) for cluster in clusters]

        return ClusterMetrics(
            total_pois=len(pois),
            num_clusters=len(clusters),
            avg_cluster_size=np.mean(cluster_sizes) if cluster_sizes else 0,
            max_cluster_size=max(cluster_sizes) if cluster_sizes else 0,
            min_cluster_size=min(cluster_sizes) if cluster_sizes else 0,
            clustering_time_seconds=0,  # Set externally
            network_downloads_saved=len(pois) - len(clusters),
            estimated_time_savings_percent=(
                ((len(pois) - len(clusters)) / len(pois) * 100) if len(pois) > 0 else 0
            ),
        )


class OptimizedPOICluster:
    """Represents an optimized cluster of POIs with advanced spatial algorithms."""

    def __init__(self, cluster_id: int | str, pois: list[dict[str, Any]]):
        self.cluster_id = cluster_id
        self.pois = pois
        self.centroid = self._calculate_centroid()
        self.radius_km = self._calculate_radius()
        self.network = None
        self.network_crs = None
        self.bbox = self._calculate_bbox()

    def _calculate_centroid(self) -> tuple[float, float]:
        """Calculate the geographic centroid of the cluster."""
        if not self.pois:
            return (0.0, 0.0)

        lats = [poi["lat"] for poi in self.pois]
        lons = [poi["lon"] for poi in self.pois]
        return (np.mean(lats), np.mean(lons))

    def _calculate_radius(self) -> float:
        """Calculate the maximum radius from centroid to any POI."""
        if len(self.pois) <= 1:
            return 0.0

        centroid_lat, centroid_lon = self.centroid
        max_distance = 0.0

        for poi in self.pois:
            distance = self._haversine_distance(centroid_lat, centroid_lon, poi["lat"], poi["lon"])
            max_distance = max(max_distance, distance)

        return max_distance

    def _calculate_bbox(self) -> tuple[float, float, float, float]:
        """Calculate bounding box (min_lat, min_lon, max_lat, max_lon)."""
        if not self.pois:
            return (0.0, 0.0, 0.0, 0.0)

        lats = [poi["lat"] for poi in self.pois]
        lons = [poi["lon"] for poi in self.pois]

        return (min(lats), min(lons), max(lats), max(lons))

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate haversine distance between two points in kilometers."""
        earth_radius_km = 6371.0  # Earth radius in kilometers

        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        return earth_radius_km * c

    def get_network_bbox(
        self, travel_time_minutes: int, buffer_km: float = 2.0
    ) -> tuple[float, float, float, float]:
        """Get optimized bounding box for network download.

        Parameters
        ----------
        travel_time_minutes : int
            Travel time limit in minutes.
        buffer_km : float, optional
            Base buffer in kilometers, by default 2.0.

        Returns
        -------
        tuple of (float, float, float, float)
            Bounding box tuple (min_lat, min_lon, max_lat, max_lon).
        """
        min_lat, min_lon, max_lat, max_lon = self.bbox

        # Calculate buffer based on travel time
        # For rural areas, we need much larger buffers to ensure complete network
        # Base calculation: assume 60 km/h average speed for driving
        speed_km_per_min = 1.0  # 60 km/h = 1 km/min
        distance_buffer = travel_time_minutes * speed_km_per_min

        # Add extra buffer for sparse networks (rural areas)
        # Use latitude as a proxy for rural/urban (higher latitudes often more rural in US)
        # Also consider the span of the cluster
        lat_span = max_lat - min_lat
        lon_span = max_lon - min_lon
        cluster_span_km = max(lat_span * 111, lon_span * 111)  # Rough conversion to km

        # If cluster span is large, it's likely rural - increase buffer
        rural_multiplier = 1.0
        if cluster_span_km > RURAL_CLUSTER_SPAN_KM:  # Large cluster span suggests rural area
            rural_multiplier = 2.0
        elif cluster_span_km > SUBURBAN_CLUSTER_SPAN_KM:
            rural_multiplier = 1.5

        # Final buffer calculation
        # Minimum buffer should be substantial for reliability
        adaptive_buffer = max(
            buffer_km + distance_buffer * rural_multiplier,
            travel_time_minutes * 1.5,  # At least 1.5x travel time in km
            20.0  # Minimum 20km buffer for any scenario
        )

        # Convert buffer to approximate degrees
        # Account for longitude compression at higher latitudes
        avg_lat = (min_lat + max_lat) / 2
        lat_buffer_deg = adaptive_buffer / 111.0
        lon_buffer_deg = adaptive_buffer / (111.0 * abs(np.cos(np.radians(avg_lat))))

        return (
            min_lat - lat_buffer_deg,
            min_lon - lon_buffer_deg,
            max_lat + lat_buffer_deg,
            max_lon + lon_buffer_deg,
        )

    def __len__(self):
        """Return the number of POIs in this cluster."""
        return len(self.pois)

    def __repr__(self):
        """Return string representation of the cluster."""
        return f"OptimizedPOICluster(id={self.cluster_id}, pois={len(self.pois)}, radius={self.radius_km:.2f}km)"


def create_optimized_clusters(
    pois: list[dict[str, Any]],
    travel_time_minutes: int = 15,
    max_cluster_radius_km: float = 15.0,
    min_cluster_size: int = 2,
) -> list[OptimizedPOICluster]:
    """Create optimized POI clusters using intelligent spatial algorithms.

    Parameters
    ----------
    pois : list of dict
        List of POI dictionaries with 'lat' and 'lon' keys.
    travel_time_minutes : int, optional
        Travel time limit for isochrone generation, by default 15.
    max_cluster_radius_km : float, optional
        Maximum clustering radius in kilometers, by default 15.0.
    min_cluster_size : int, optional
        Minimum POIs per cluster, by default 2.

    Returns
    -------
    list of OptimizedPOICluster
        List of OptimizedPOICluster objects.
    """
    if not pois:
        return []

    # Use intelligent clusterer
    clusterer = IntelligentPOIClusterer(
        max_cluster_radius_km=max_cluster_radius_km, min_cluster_size=min_cluster_size
    )

    poi_clusters = clusterer.cluster_pois(pois, travel_time_minutes)

    # Convert to OptimizedPOICluster objects
    optimized_clusters = []
    for i, cluster_pois in enumerate(poi_clusters):
        cluster = OptimizedPOICluster(cluster_id=i, pois=cluster_pois)
        optimized_clusters.append(cluster)

    return optimized_clusters


def download_network_for_cluster(
    cluster: OptimizedPOICluster,
    travel_time_minutes: int,
    network_buffer_km: float = 2.0,
    travel_mode: TravelMode = TravelMode.DRIVE,
) -> bool:
    """Download and prepare road network for an optimized cluster.

    Parameters
    ----------
    cluster : OptimizedPOICluster
        OptimizedPOICluster to download network for.
    travel_time_minutes : int
        Travel time limit in minutes.
    network_buffer_km : float, optional
        Additional buffer around cluster, by default 2.0.
    travel_mode : TravelMode, optional
        Mode of travel (walk, bike, drive), by default TravelMode.DRIVE.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    try:
        # Get network type, default speed, and highway speeds for travel mode
        network_type = get_network_type(travel_mode)
        default_speed = get_default_speed(travel_mode)
        highway_speeds = get_highway_speeds(travel_mode)

        if len(cluster.pois) == 1:
            # Single POI - use point-based download with larger buffer for rural areas
            poi = cluster.pois[0]
            # Increase buffer for single POIs to avoid truncation
            distance_m = max(
                travel_time_minutes * 2000,  # Assume 2km/min max speed
                30000  # Minimum 30km buffer
            ) + network_buffer_km * 1000

            graph = ox.graph_from_point(
                (poi["lat"], poi["lon"]),
                network_type=network_type,
                dist=distance_m,
            )
        else:
            # Multiple POIs - use optimized bounding box with improved rural handling
            min_lat, min_lon, max_lat, max_lon = cluster.get_network_bbox(
                travel_time_minutes, network_buffer_km
            )

            # OSMnx expects bbox as (left, bottom, right, top) = (min_lon, min_lat, max_lon, max_lat)
            osm_bbox = (min_lon, min_lat, max_lon, max_lat)
            graph = ox.graph_from_bbox(bbox=osm_bbox, network_type=network_type)

        # Add speeds and travel times with mode-specific defaults
        # OSMnx will use:
        # 1. Existing maxspeed tags from OSM data
        # 2. Highway-type-specific speeds we provide
        # 3. Mean of observed speeds for unmapped highway types
        # 4. Fallback speed as last resort
        graph = ox.add_edge_speeds(graph, hwy_speeds=highway_speeds, fallback=default_speed)
        graph = ox.add_edge_travel_times(graph)

        # Apply mode-specific speed adjustments for more realistic isochrones
        if travel_mode == TravelMode.WALK:
            # For walking, ensure speeds don't exceed reasonable walking speeds
            for _u, _v, data in graph.edges(data=True):
                if "speed_kph" in data and data["speed_kph"] > MAX_WALKING_SPEED_KPH:
                    data["speed_kph"] = NORMAL_WALKING_SPEED_KPH
                    data["travel_time"] = data["length"] / (data["speed_kph"] * 1000 / 3600)
        elif travel_mode == TravelMode.BIKE:
            # For biking, cap speeds to reasonable cycling speeds
            for _u, _v, data in graph.edges(data=True):
                if "speed_kph" in data and data["speed_kph"] > MAX_CYCLING_SPEED_KPH:
                    data["speed_kph"] = NORMAL_CYCLING_SPEED_KPH
                    data["travel_time"] = data["length"] / (data["speed_kph"] * 1000 / 3600)

        graph = ox.project_graph(graph)

        # Store network in cluster
        cluster.network = graph
        cluster.network_crs = graph.graph["crs"]

        # Log speed statistics for debugging
        speeds = [data.get("speed_kph", 0) for u, v, data in graph.edges(data=True)]
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            min_speed = min(speeds)
            max_speed = max(speeds)
            logger.info(
                f"Network speeds for {travel_mode.value} mode - "
                f"avg: {avg_speed:.1f} km/h, min: {min_speed:.1f} km/h, max: {max_speed:.1f} km/h"
            )

        logger.debug(
            f"Downloaded network for cluster {cluster.cluster_id}: "
            f"{len(graph.nodes)} nodes, {len(graph.edges)} edges"
        )

        return True

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid data when downloading network for cluster {cluster.cluster_id}: {e}")
        return False
    except nx.NetworkXError as e:
        logger.error(f"NetworkX error for cluster {cluster.cluster_id}: {e}")
        return False
    except (OSError, ConnectionError) as e:
        logger.error(f"Network/IO error downloading network for cluster {cluster.cluster_id}: {e}")
        return False


def create_isochrone_from_poi_with_network(
    poi: dict[str, Any],
    network: nx.MultiDiGraph,
    network_crs: str,
    travel_time_minutes: int,
    travel_mode: TravelMode = TravelMode.DRIVE,
) -> gpd.GeoDataFrame | None:
    """Create isochrone for a POI using pre-downloaded network.

    Parameters
    ----------
    poi : dict
        POI dictionary with 'lat' and 'lon'.
    network : nx.MultiDiGraph
        Pre-downloaded road network.
    network_crs : str
        CRS of the network.
    travel_time_minutes : int
        Travel time limit in minutes.
    travel_mode : TravelMode, optional
        Mode of travel (walk, bike, drive), by default TravelMode.DRIVE.

    Returns
    -------
    gpd.GeoDataFrame or None
        GeoDataFrame with isochrone or None if failed.
    """
    try:
        # Import validation utilities
        from ..validators import _validate_coordinates_strict

        # Validate POI coordinates
        lat = poi.get("lat")
        lon = poi.get("lon")

        if lat is None or lon is None:
            logger.error(f"POI {poi.get('id', 'unknown')} missing lat/lon coordinates")
            return None

        try:
            lat, lon = _validate_coordinates_strict(lat, lon)
        except (ValueError, TypeError) as e:
            logger.error(
                f"POI {poi.get('id', 'unknown')} has invalid coordinates: lat={lat}, lon={lon} - {e}"
            )
            return None

        # Create point from validated coordinates
        poi_point = Point(lon, lat)

        # Use PyProj transformer directly to avoid single-point GeoSeries transformation
        # This bypasses the problematic GeoPandas to_crs() call that triggers the NumPy warning
        import pyproj

        transformer = pyproj.Transformer.from_crs("EPSG:4326", network_crs, always_xy=True)

        # Transform the single point directly using PyProj (avoiding NumPy array operations)
        poi_x_proj, poi_y_proj = transformer.transform(poi_point.x, poi_point.y)

        # Find nearest node using the transformed coordinates
        poi_node = ox.nearest_nodes(network, X=poi_x_proj, Y=poi_y_proj)

        # Generate subgraph based on travel time
        subgraph = nx.ego_graph(
            network,
            poi_node,
            radius=travel_time_minutes * 60,  # Convert to seconds
            distance="travel_time",
        )

        if len(subgraph.nodes) == 0:
            logger.warning(f"No reachable nodes for POI {poi.get('id', 'unknown')}")
            return None

        # Calculate distance statistics using Dijkstra's algorithm
        # Get shortest paths by travel time to all reachable nodes
        paths_by_time = nx.single_source_dijkstra_path_length(
            network,
            poi_node,
            cutoff=travel_time_minutes * 60,  # seconds
            weight="travel_time"
        )

        # Calculate actual distances along shortest paths
        distances_m = []
        for target_node in paths_by_time:
            if target_node != poi_node:
                try:
                    # Get shortest path (sequence of nodes)
                    path = nx.shortest_path(
                        network,
                        poi_node,
                        target_node,
                        weight="travel_time"
                    )

                    # Sum edge lengths along the path
                    total_distance = 0.0
                    for i in range(len(path) - 1):
                        # Get edge data between consecutive nodes
                        edge_data = network.get_edge_data(path[i], path[i+1])
                        # Handle multi-edges by taking the shortest length
                        if edge_data and isinstance(edge_data, dict):
                            # If multiple edges exist, get the minimum length
                            min_length = min(
                                e.get("length", 0) for e in edge_data.values()
                            )
                            total_distance += min_length

                    if total_distance > 0:
                        distances_m.append(total_distance)
                except (nx.NetworkXNoPath, KeyError):
                    # Skip nodes that can't be reached or have missing data
                    continue

        # Calculate distance statistics
        if distances_m:
            min_distance_m = min(distances_m)
            max_distance_m = max(distances_m)
            avg_distance_m = sum(distances_m) / len(distances_m)

            # Convert to kilometers
            min_distance_km = min_distance_m / 1000.0
            max_distance_km = max_distance_m / 1000.0
            avg_distance_km = avg_distance_m / 1000.0

            # Calculate median and standard deviation
            import numpy as np
            median_distance_km = np.median(distances_m) / 1000.0
            std_dev_km = np.std(distances_m) / 1000.0 if len(distances_m) > 1 else 0.0
        else:
            # Default values if no distances calculated
            min_distance_km = 0.0
            max_distance_km = 0.0
            avg_distance_km = 0.0
            median_distance_km = 0.0
            std_dev_km = 0.0

        # Create isochrone polygon from reachable nodes
        node_points = [Point((data["x"], data["y"])) for node, data in subgraph.nodes(data=True)]

        if len(node_points) < MIN_POLYGON_POINTS:
            logger.warning(
                f"Insufficient nodes ({len(node_points)}) to create polygon for POI {poi.get('id', 'unknown')}"
            )
            return None

        # Create GeoDataFrame from node points
        nodes_gdf = gpd.GeoDataFrame(geometry=node_points, crs=network_crs)

        # Use convex hull to create the isochrone polygon
        isochrone = nodes_gdf.union_all().convex_hull

        # Create result GeoDataFrame
        isochrone_gdf = gpd.GeoDataFrame(geometry=[isochrone], crs=network_crs).to_crs("EPSG:4326")

        # Add metadata
        isochrone_gdf["poi_id"] = poi.get("id", "unknown")
        isochrone_gdf["poi_name"] = poi.get("tags", {}).get(
            "name", f"poi_{poi.get('id', 'unknown')}"
        )
        isochrone_gdf["travel_time_minutes"] = travel_time_minutes
        isochrone_gdf["travel_mode"] = travel_mode.value

        # Add distance statistics
        isochrone_gdf["min_distance_km"] = min_distance_km
        isochrone_gdf["max_distance_km"] = max_distance_km
        isochrone_gdf["avg_distance_km"] = avg_distance_km
        isochrone_gdf["median_distance_km"] = median_distance_km
        isochrone_gdf["std_dev_distance_km"] = std_dev_km
        isochrone_gdf["reachable_nodes"] = len(subgraph.nodes)
        isochrone_gdf["analyzed_paths"] = len(distances_m)

        # Log distance statistics for debugging
        logger.info(
            f"Distance stats for {poi.get('id', 'unknown')} at {travel_time_minutes} min: "
            f"min={min_distance_km:.2f}km, max={max_distance_km:.2f}km, "
            f"avg={avg_distance_km:.2f}km, nodes={len(subgraph.nodes)}"
        )

        return isochrone_gdf

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid data when creating isochrone for POI {poi.get('id', 'unknown')}: {e}")
        return None
    except nx.NetworkXError as e:
        logger.error(f"NetworkX error creating isochrone for POI {poi.get('id', 'unknown')}: {e}")
        return None
    except (OSError, ConnectionError) as e:
        logger.error(f"Network/IO error creating isochrone for POI {poi.get('id', 'unknown')}: {e}")
        return None


def benchmark_clustering_performance(
    pois: list[dict[str, Any]], travel_time_minutes: int = 15, max_cluster_radius_km: float = 15.0
) -> dict[str, Any]:
    """Benchmark clustering performance and provide optimization recommendations.

    Parameters
    ----------
    pois : list of dict
        List of POI dictionaries.
    travel_time_minutes : int, optional
        Travel time limit, by default 15.
    max_cluster_radius_km : float, optional
        Maximum clustering radius, by default 15.0.

    Returns
    -------
    dict
        Dictionary with performance metrics and recommendations.
    """
    start_time = time.time()

    # Test different clustering parameters
    clusterer = IntelligentPOIClusterer(
        max_cluster_radius_km=max_cluster_radius_km, min_cluster_size=2
    )

    clusters = clusterer.cluster_pois(pois, travel_time_minutes)
    clustering_time = time.time() - start_time

    # Calculate metrics
    metrics = clusterer.get_cluster_metrics(pois, clusters)
    metrics.clustering_time_seconds = clustering_time

    # Performance analysis
    total_downloads_original = len(pois)
    total_downloads_optimized = len(clusters)
    time_savings_estimate = (
        total_downloads_original - total_downloads_optimized
    ) * 30  # 30s per download estimate

    return {
        "metrics": metrics,
        "performance": {
            "original_downloads": total_downloads_original,
            "optimized_downloads": total_downloads_optimized,
            "downloads_saved": total_downloads_original - total_downloads_optimized,
            "estimated_time_savings_seconds": time_savings_estimate,
            "clustering_overhead_seconds": clustering_time,
            "net_time_savings_seconds": time_savings_estimate - clustering_time,
        },
        "recommendations": {
            "optimal_radius_km": max_cluster_radius_km,
            "efficiency_rating": (
                "Excellent"
                if metrics.estimated_time_savings_percent > EFFICIENCY_EXCELLENT_THRESHOLD
                else "Good"
                if metrics.estimated_time_savings_percent > EFFICIENCY_GOOD_THRESHOLD
                else "Fair"
            ),
        },
    }
