#!/usr/bin/env python3
"""
Clustering optimization module for isochrone generation.

This module implements spatial clustering to group nearby POIs and share
road network downloads, significantly improving performance for large jobs.
"""

import logging
import time
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import osmnx as ox
import networkx as nx
from tqdm import tqdm

from ..progress import get_progress_bar

# Setup logging
logger = logging.getLogger(__name__)

class POICluster:
    """Represents a cluster of POIs that can share a road network."""
    
    def __init__(self, cluster_id: int, pois: List[Dict[str, Any]], 
                 centroid: Tuple[float, float], radius_km: float):
        self.cluster_id = cluster_id
        self.pois = pois
        self.centroid = centroid  # (lat, lon)
        self.radius_km = radius_km
        self.network = None
        self.network_crs = None
        
    def __len__(self):
        return len(self.pois)
        
    def get_bounding_box(self, buffer_km: float = 2.0) -> Tuple[float, float, float, float]:
        """Get bounding box for the cluster with buffer."""
        lats = [poi['lat'] for poi in self.pois]
        lons = [poi['lon'] for poi in self.pois]
        
        # Convert buffer to approximate degrees
        buffer_deg = buffer_km / 111.0
        
        min_lat = min(lats) - buffer_deg
        max_lat = max(lats) + buffer_deg
        min_lon = min(lons) - buffer_deg
        max_lon = max(lons) + buffer_deg
        
        return (min_lat, min_lon, max_lat, max_lon)

def calculate_poi_distances(pois: List[Dict[str, Any]]) -> np.ndarray:
    """
    Calculate pairwise distances between POIs in kilometers.
    
    Args:
        pois: List of POI dictionaries with 'lat' and 'lon' keys
        
    Returns:
        Distance matrix in kilometers
    """
    coords = np.array([[poi['lat'], poi['lon']] for poi in pois])
    
    # Convert to radians
    coords_rad = np.radians(coords)
    
    # Haversine distance calculation
    lat1 = coords_rad[:, 0:1]
    lon1 = coords_rad[:, 1:2]
    lat2 = coords_rad[:, 0]
    lon2 = coords_rad[:, 1]
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    # Earth radius in kilometers
    R = 6371.0
    distances = R * c
    
    return distances

def cluster_pois_by_proximity(pois: List[Dict[str, Any]], 
                            max_cluster_radius_km: float = 10.0,
                            min_cluster_size: int = 2) -> List[POICluster]:
    """
    Cluster POIs by geographic proximity using DBSCAN.
    
    Args:
        pois: List of POI dictionaries with 'lat' and 'lon' keys
        max_cluster_radius_km: Maximum radius for clustering in kilometers
        min_cluster_size: Minimum number of POIs to form a cluster
        
    Returns:
        List of POICluster objects
    """
    if len(pois) < min_cluster_size:
        # Not enough POIs to cluster, return individual clusters
        clusters = []
        for i, poi in enumerate(pois):
            cluster = POICluster(
                cluster_id=i,
                pois=[poi],
                centroid=(poi['lat'], poi['lon']),
                radius_km=0.0
            )
            clusters.append(cluster)
        return clusters
    
    # Extract coordinates
    coords = np.array([[poi['lat'], poi['lon']] for poi in pois])
    
    # Normalize coordinates for clustering (approximate)
    # Convert degrees to km (rough approximation)
    coords_km = coords.copy()
    coords_km[:, 0] *= 111.0  # lat to km
    coords_km[:, 1] *= 111.0 * np.cos(np.radians(coords[:, 0].mean()))  # lon to km
    
    # Apply DBSCAN clustering
    clustering = DBSCAN(
        eps=max_cluster_radius_km,
        min_samples=min_cluster_size,
        metric='euclidean'
    ).fit(coords_km)
    
    labels = clustering.labels_
    
    # Group POIs by cluster
    clusters = []
    unique_labels = set(labels)
    
    for label in unique_labels:
        cluster_pois = [pois[i] for i in range(len(pois)) if labels[i] == label]
        
        if label == -1:
            # Noise points (outliers) - create individual clusters
            for i, poi in enumerate(cluster_pois):
                cluster = POICluster(
                    cluster_id=f"outlier_{i}",
                    pois=[poi],
                    centroid=(poi['lat'], poi['lon']),
                    radius_km=0.0
                )
                clusters.append(cluster)
        else:
            # Calculate cluster centroid and radius
            cluster_coords = np.array([[poi['lat'], poi['lon']] for poi in cluster_pois])
            centroid = cluster_coords.mean(axis=0)
            
            # Calculate maximum distance from centroid
            distances = calculate_poi_distances([{'lat': centroid[0], 'lon': centroid[1]}] + cluster_pois)
            radius_km = distances[0, 1:].max()
            
            cluster = POICluster(
                cluster_id=label,
                pois=cluster_pois,
                centroid=(centroid[0], centroid[1]),
                radius_km=radius_km
            )
            clusters.append(cluster)
    
    return clusters

def download_network_for_cluster(cluster: POICluster, 
                                travel_time_limit: int,
                                network_buffer_km: float = 5.0) -> bool:
    """
    Download and prepare road network for a cluster of POIs.
    
    Args:
        cluster: POICluster object to download network for
        travel_time_limit: Travel time limit in minutes
        network_buffer_km: Additional buffer around cluster for network download
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if len(cluster.pois) == 1:
            # Single POI - use point-based download
            poi = cluster.pois[0]
            G = ox.graph_from_point(
                (poi['lat'], poi['lon']),
                network_type='drive',
                dist=travel_time_limit * 1000 + network_buffer_km * 1000
            )
        else:
            # Multiple POIs - use bounding box download
            bbox = cluster.get_bounding_box(buffer_km=network_buffer_km)
            min_lat, min_lon, max_lat, max_lon = bbox
            
            G = ox.graph_from_bbox(
                bbox=(min_lon, min_lat, max_lon, max_lat),  # (left, bottom, right, top)
                network_type='drive'
            )
        
        # Add speeds and travel times
        G = ox.add_edge_speeds(G, fallback=50)
        G = ox.add_edge_travel_times(G)
        G = ox.project_graph(G)
        
        # Store network in cluster
        cluster.network = G
        cluster.network_crs = G.graph['crs']
        
        return True
        
    except Exception as e:
        logger.error(f"Error downloading network for cluster {cluster.cluster_id}: {e}")
        return False

def create_isochrone_from_poi_with_network(poi: Dict[str, Any],
                                         network: nx.MultiDiGraph,
                                         network_crs: str,
                                         travel_time_limit: int) -> gpd.GeoDataFrame:
    """
    Create isochrone from POI using pre-downloaded network.
    
    Args:
        poi: POI dictionary with 'lat' and 'lon'
        network: Pre-downloaded OSMnx network graph
        network_crs: CRS of the network
        travel_time_limit: Travel time limit in minutes
        
    Returns:
        GeoDataFrame with isochrone geometry
    """
    # Create point from coordinates
    poi_point = Point(poi['lon'], poi['lat'])
    poi_geom = gpd.GeoSeries([poi_point], crs='EPSG:4326').to_crs(network_crs)
    poi_proj = poi_geom.geometry.iloc[0]
    
    # Find nearest node
    poi_node = ox.nearest_nodes(
        network,
        X=poi_proj.x,
        Y=poi_proj.y
    )
    
    # Generate subgraph based on travel time
    subgraph = nx.ego_graph(
        network,
        poi_node,
        radius=travel_time_limit * 60,  # Convert minutes to seconds
        distance='travel_time'
    )
    
    # Create isochrone
    node_points = [Point((data['x'], data['y'])) 
                  for node, data in subgraph.nodes(data=True)]
    nodes_gdf = gpd.GeoDataFrame(geometry=node_points, crs=network_crs)
    
    # Use convex hull to create the isochrone polygon
    isochrone = nodes_gdf.unary_union.convex_hull
    
    # Create GeoDataFrame with the isochrone
    isochrone_gdf = gpd.GeoDataFrame(
        geometry=[isochrone],
        crs=network_crs
    )
    
    # Convert to WGS84 for standard output
    isochrone_gdf = isochrone_gdf.to_crs('EPSG:4326')
    
    # Add metadata
    poi_name = poi.get('tags', {}).get('name', f"poi_{poi.get('id', 'unknown')}")
    isochrone_gdf['poi_id'] = poi.get('id', 'unknown')
    isochrone_gdf['poi_name'] = poi_name
    isochrone_gdf['travel_time_minutes'] = travel_time_limit
    
    return isochrone_gdf

def create_isochrones_clustered(poi_data: Dict[str, List[Dict[str, Any]]],
                              travel_time_limit: int,
                              max_cluster_radius_km: float = 10.0,
                              min_cluster_size: int = 2,
                              network_buffer_km: float = 5.0,
                              simplify_tolerance: Optional[float] = None) -> List[gpd.GeoDataFrame]:
    """
    Create isochrones using clustering optimization.
    
    Args:
        poi_data: Dictionary with 'pois' key containing list of POIs
        travel_time_limit: Travel time limit in minutes
        max_cluster_radius_km: Maximum radius for clustering in kilometers
        min_cluster_size: Minimum number of POIs to form a cluster
        network_buffer_km: Additional buffer around clusters for network download
        simplify_tolerance: Optional tolerance for geometry simplification
        
    Returns:
        List of GeoDataFrame objects with isochrone geometries
    """
    pois = poi_data.get('pois', [])
    if not pois:
        raise ValueError("No POIs found in input data")
    
    # Step 1: Cluster POIs by proximity
    logger.info(f"Clustering {len(pois)} POIs...")
    clusters = cluster_pois_by_proximity(
        pois, 
        max_cluster_radius_km=max_cluster_radius_km,
        min_cluster_size=min_cluster_size
    )
    
    logger.info(f"Created {len(clusters)} clusters")
    for i, cluster in enumerate(clusters):
        logger.info(f"Cluster {i}: {len(cluster)} POIs, radius: {cluster.radius_km:.2f} km")
    
    # Step 2: Download networks for each cluster
    successful_clusters = []
    for cluster in get_progress_bar(clusters, desc="Downloading Networks", unit="cluster"):
        if download_network_for_cluster(cluster, travel_time_limit, network_buffer_km):
            successful_clusters.append(cluster)
        else:
            logger.warning(f"Failed to download network for cluster {cluster.cluster_id}")
    
    # Step 3: Generate isochrones using shared networks
    isochrone_gdfs = []
    total_pois = sum(len(cluster) for cluster in successful_clusters)
    
    with tqdm(total=total_pois, desc="Generating Isochrones", unit="POI") as pbar:
        for cluster in successful_clusters:
            for poi in cluster.pois:
                try:
                    isochrone_gdf = create_isochrone_from_poi_with_network(
                        poi=poi,
                        network=cluster.network,
                        network_crs=cluster.network_crs,
                        travel_time_limit=travel_time_limit
                    )
                    
                    # Apply simplification if requested
                    if simplify_tolerance is not None:
                        isochrone_gdf["geometry"] = isochrone_gdf.geometry.simplify(
                            tolerance=simplify_tolerance, preserve_topology=True
                        )
                    
                    isochrone_gdfs.append(isochrone_gdf)
                    
                except Exception as e:
                    poi_name = poi.get('tags', {}).get('name', poi.get('id', 'unknown'))
                    logger.error(f"Error creating isochrone for POI {poi_name}: {e}")
                
                pbar.update(1)
    
    return isochrone_gdfs

def benchmark_clustering_performance(poi_data: Dict[str, List[Dict[str, Any]]],
                                   travel_time_limit: int,
                                   max_cluster_radius_km: float = 10.0) -> Dict[str, Any]:
    """
    Benchmark the performance improvement from clustering.
    
    Args:
        poi_data: Dictionary with 'pois' key containing list of POIs
        travel_time_limit: Travel time limit in minutes
        max_cluster_radius_km: Maximum radius for clustering in kilometers
        
    Returns:
        Dictionary with benchmark results
    """
    pois = poi_data.get('pois', [])
    
    # Analyze clustering potential
    clusters = cluster_pois_by_proximity(pois, max_cluster_radius_km=max_cluster_radius_km)
    
    total_pois = len(pois)
    total_clusters = len(clusters)
    clustered_pois = sum(len(cluster) for cluster in clusters if len(cluster) > 1)
    single_poi_clusters = sum(1 for cluster in clusters if len(cluster) == 1)
    
    # Calculate potential savings
    network_downloads_original = total_pois
    network_downloads_optimized = total_clusters
    download_reduction = network_downloads_original - network_downloads_optimized
    reduction_percentage = (download_reduction / network_downloads_original) * 100
    
    # Estimate time savings (assuming network download takes 2-5 seconds per POI)
    estimated_time_savings_min = download_reduction * 2 / 60  # minutes
    estimated_time_savings_max = download_reduction * 5 / 60  # minutes
    
    results = {
        'total_pois': total_pois,
        'total_clusters': total_clusters,
        'clustered_pois': clustered_pois,
        'single_poi_clusters': single_poi_clusters,
        'network_downloads_original': network_downloads_original,
        'network_downloads_optimized': network_downloads_optimized,
        'download_reduction': download_reduction,
        'reduction_percentage': reduction_percentage,
        'estimated_time_savings_min_seconds': estimated_time_savings_min * 60,
        'estimated_time_savings_max_seconds': estimated_time_savings_max * 60,
        'cluster_details': [
            {
                'cluster_id': cluster.cluster_id,
                'poi_count': len(cluster),
                'radius_km': cluster.radius_km,
                'centroid': cluster.centroid
            }
            for cluster in clusters
        ]
    }
    
    return results 