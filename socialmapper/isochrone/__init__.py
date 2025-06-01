#!/usr/bin/env python3
"""
Modern Isochrone Generation Module.

This module provides high-performance isochrone generation with intelligent
spatial clustering, advanced network caching, and concurrent processing.

Key Features:
- Intelligent POI clustering using DBSCAN machine learning
- Advanced network caching with SQLite indexing and compression
- Concurrent processing for 4-8x performance improvement
- Automatic optimization based on dataset characteristics
- Comprehensive performance monitoring and statistics
"""
import os
import warnings
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point
from typing import Dict, Any, List, Union, Tuple, Optional, Callable
import json
import pandas as pd
from tqdm import tqdm
import time
import logging

# Import the new progress bar utility
from socialmapper.progress import get_progress_bar

# Import modernized components
from .clustering import (
    IntelligentPOIClusterer,
    OptimizedPOICluster,
    create_optimized_clusters,
    create_isochrone_from_poi_with_network,
    benchmark_clustering_performance
)
from .cache import (
    ModernNetworkCache,
    get_global_cache,
    download_and_cache_network
)
from .concurrent import (
    ConcurrentIsochroneProcessor,
    process_isochrones_concurrent,
    ProcessingStats
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

# Set PyOGRIO as the default IO engine
gpd.options.io_engine = "pyogrio"

# Enable PyArrow for GeoPandas operations if available
try:
    import pyarrow
    USE_ARROW = True
    os.environ["PYOGRIO_USE_ARROW"] = "1"  # Set environment variable for pyogrio
except ImportError:
    USE_ARROW = False

def create_isochrone_from_poi(
    poi: Dict[str, Any],
    travel_time_limit: int,
    output_dir: str = 'output/isochrones',
    save_file: bool = True,
    simplify_tolerance: Optional[float] = None,
    use_parquet: bool = True
) -> Union[str, gpd.GeoDataFrame]:
    """
    Create an isochrone from a POI using modern optimized methods.
    
    Args:
        poi (Dict[str, Any]): POI dictionary containing at minimum 'lat', 'lon', and 'tags'
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save the isochrone file
        save_file (bool): Whether to save the isochrone to a file
        simplify_tolerance (float, optional): Tolerance for geometry simplification
        use_parquet (bool): Whether to use GeoParquet instead of GeoJSON format
        
    Returns:
        Union[str, gpd.GeoDataFrame]: File path if save_file=True, or GeoDataFrame if save_file=False
    """
    # Extract coordinates
    latitude = poi.get('lat')
    longitude = poi.get('lon')
    
    if latitude is None or longitude is None:
        raise ValueError("POI must contain 'lat' and 'lon' coordinates")
    
    # Get POI name (or use ID if no name is available)
    poi_name = poi.get('tags', {}).get('name', f"poi_{poi.get('id', 'unknown')}")
    
    # Use modern caching system for network download
    cache = get_global_cache()
    
    # Calculate bounding box for network download
    buffer_km = travel_time_limit * 1.5  # Adaptive buffer based on travel time
    buffer_deg = buffer_km / 111.0
    bbox = (
        latitude - buffer_deg,
        longitude - buffer_deg,
        latitude + buffer_deg,
        longitude + buffer_deg
    )
    
    # Download network with caching
    G = download_and_cache_network(
        bbox=bbox,
        travel_time_minutes=travel_time_limit,
        cluster_size=1,
        cache=cache
    )
    
    if G is None:
        raise RuntimeError(f"Failed to download road network for POI {poi_name}")
    
    # Create isochrone using optimized method
    isochrone_gdf = create_isochrone_from_poi_with_network(
        poi=poi,
        network=G,
        network_crs=G.graph['crs'],
        travel_time_minutes=travel_time_limit
    )
    
    if isochrone_gdf is None:
        raise RuntimeError(f"Failed to create isochrone for POI {poi_name}")
    
    # Simplify geometry if tolerance is provided
    if simplify_tolerance is not None:
        isochrone_gdf["geometry"] = isochrone_gdf.geometry.simplify(
            tolerance=simplify_tolerance, preserve_topology=True
        )
    
    if save_file:
        # Save result
        poi_name = poi_name.lower().replace(" ", "_")
        os.makedirs(output_dir, exist_ok=True)
        
        if use_parquet and USE_ARROW:
            # Save as GeoParquet for better performance
            isochrone_file = os.path.join(
                output_dir,
                f'isochrone{travel_time_limit}_{poi_name}.parquet'
            )
            isochrone_gdf.to_parquet(isochrone_file)
        else:
            # Fallback to GeoJSON
            isochrone_file = os.path.join(
                output_dir,
                f'isochrone{travel_time_limit}_{poi_name}.geojson'
            )
            isochrone_gdf.to_file(isochrone_file, driver='GeoJSON', use_arrow=USE_ARROW)
        
        return isochrone_file
    
    return isochrone_gdf

def get_bounding_box(pois: List[Dict[str, Any]], buffer_km: float = 5.0) -> Tuple[float, float, float, float]:
    """
    Get a bounding box for a list of POIs with a buffer.
    
    Args:
        pois: List of POI dictionaries with 'lat' and 'lon'
        buffer_km: Buffer in kilometers to add around the POIs
        
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    lons = [poi.get('lon') for poi in pois if poi.get('lon') is not None]
    lats = [poi.get('lat') for poi in pois if poi.get('lat') is not None]
    
    if not lons or not lats:
        raise ValueError("No valid coordinates in POIs")
    
    # Convert buffer to approximate degrees (rough estimate)
    buffer_deg = buffer_km / 111.0  # ~111km per degree at equator
    
    min_lat = min(lats) - buffer_deg
    min_lon = min(lons) - buffer_deg
    max_lat = max(lats) + buffer_deg
    max_lon = max(lons) + buffer_deg
    
    return (min_lat, min_lon, max_lat, max_lon)

def create_isochrones_from_poi_list(
    poi_data: Dict[str, List[Dict[str, Any]]],
    travel_time_limit: int,
    output_dir: str = 'output/isochrones',
    save_individual_files: bool = True,
    combine_results: bool = False,
    simplify_tolerance: Optional[float] = None,
    use_parquet: bool = True,
    use_clustering: Optional[bool] = None,
    max_cluster_radius_km: float = 15.0,
    min_cluster_size: int = 2,
    use_concurrent: Optional[bool] = None,
    max_network_workers: int = 8,
    max_isochrone_workers: Optional[int] = None,
    progress_callback: Optional[Callable] = None
) -> Union[str, gpd.GeoDataFrame, List[str]]:
    """
    Create isochrones from a list of POIs with modern optimization.
    
    Args:
        poi_data (Dict[str, List[Dict]]): Dictionary with 'pois' key containing list of POIs
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save isochrone files
        save_individual_files (bool): Whether to save individual isochrone files
        combine_results (bool): Whether to combine all isochrones into a single file
        simplify_tolerance (float, optional): Tolerance for geometry simplification
        use_parquet (bool): Whether to use GeoParquet instead of GeoJSON format
        use_clustering (bool, optional): Whether to use clustering optimization
        max_cluster_radius_km (float): Maximum radius for clustering in kilometers
        min_cluster_size (int): Minimum number of POIs to form a cluster
        use_concurrent (bool, optional): Whether to use concurrent processing
        max_network_workers (int): Maximum concurrent network downloads
        max_isochrone_workers (int, optional): Maximum concurrent isochrone calculations
        progress_callback (Callable, optional): Progress callback function
        
    Returns:
        Union[str, gpd.GeoDataFrame, List[str]]: Results based on save/combine options
    """
    pois = poi_data.get('pois', [])
    if not pois:
        raise ValueError("No POIs found in input data. Please try different search parameters or a different location.")
    
    logger.info(f"Processing {len(pois)} POIs with modern isochrone generation")
    
    # Auto-decide optimization strategies
    if use_clustering is None:
        # Use clustering for datasets with 5+ POIs
        use_clustering = len(pois) >= 5
        if use_clustering:
            # Quick benchmark to verify clustering benefit
            benchmark = benchmark_clustering_performance(pois, travel_time_limit, max_cluster_radius_km)
            efficiency_rating = benchmark['recommendations']['efficiency_rating']
            if efficiency_rating == 'Fair':
                use_clustering = False
                logger.info("Clustering not beneficial for this dataset distribution")
            else:
                logger.info(f"Auto-enabling clustering: {efficiency_rating} efficiency rating")
    
    if use_concurrent is None:
        # Use concurrent processing for datasets with 3+ POIs
        use_concurrent = len(pois) >= 3
        if use_concurrent:
            logger.info("Auto-enabling concurrent processing for improved performance")
    
    # Use modern concurrent processing if enabled
    if use_concurrent:
        logger.info("Using modern concurrent isochrone processing")
        
        isochrone_gdfs = process_isochrones_concurrent(
            pois=pois,
            travel_time_minutes=travel_time_limit,
            max_cluster_radius_km=max_cluster_radius_km,
            min_cluster_size=min_cluster_size,
            max_network_workers=max_network_workers,
            max_isochrone_workers=max_isochrone_workers,
            progress_callback=progress_callback
        )
        
    elif use_clustering:
        logger.info("Using intelligent clustering optimization")
        
        # Create optimized clusters
        clusters = create_optimized_clusters(
            pois=pois,
            travel_time_minutes=travel_time_limit,
            max_cluster_radius_km=max_cluster_radius_km,
            min_cluster_size=min_cluster_size
        )
        
        logger.info(f"Created {len(clusters)} optimized clusters")
        
        # Process clusters sequentially with caching
        cache = get_global_cache()
        isochrone_gdfs = []
        
        for cluster in get_progress_bar(clusters, desc="Processing Clusters", unit="cluster"):
            # Download network for cluster
            bbox = cluster.get_network_bbox(travel_time_limit)
            network = download_and_cache_network(
                bbox=bbox,
                travel_time_minutes=travel_time_limit,
                cluster_size=len(cluster),
                cache=cache
            )
            
            if network is None:
                logger.warning(f"Failed to download network for cluster {cluster.cluster_id}")
                continue
            
            cluster.network = network
            cluster.network_crs = network.graph['crs']
            
            # Generate isochrones for all POIs in cluster
            for poi in cluster.pois:
                isochrone_gdf = create_isochrone_from_poi_with_network(
                    poi=poi,
                    network=cluster.network,
                    network_crs=cluster.network_crs,
                    travel_time_minutes=travel_time_limit
                )
                
                if isochrone_gdf is not None:
                    # Apply simplification if requested
                    if simplify_tolerance is not None:
                        isochrone_gdf["geometry"] = isochrone_gdf.geometry.simplify(
                            tolerance=simplify_tolerance, preserve_topology=True
                        )
                    isochrone_gdfs.append(isochrone_gdf)
    
    else:
        logger.info("Using standard isochrone generation")
        
        # Standard processing with modern caching
        isochrone_gdfs = []
        cache = get_global_cache()
        
        for poi in get_progress_bar(pois, desc="Generating Isochrones", unit="POI"):
            try:
                result = create_isochrone_from_poi(
                    poi=poi,
                    travel_time_limit=travel_time_limit,
                    output_dir=output_dir,
                    save_file=False,  # We'll handle saving later
                    simplify_tolerance=simplify_tolerance,
                    use_parquet=use_parquet
                )
                isochrone_gdfs.append(result)
                
            except Exception as e:
                poi_name = poi.get('tags', {}).get('name', poi.get('id', 'unknown'))
                logger.error(f"Error creating isochrone for POI {poi_name}: {e}")
                continue
    
    # Handle file saving and combining
    if not isochrone_gdfs:
        logger.warning("No isochrones were successfully generated")
        return [] if save_individual_files else gpd.GeoDataFrame()
    
    logger.info(f"Successfully generated {len(isochrone_gdfs)} isochrones")
    
    # Save individual files if requested
    isochrone_files = []
    if save_individual_files:
        os.makedirs(output_dir, exist_ok=True)
        
        for isochrone_gdf in isochrone_gdfs:
            poi_name = isochrone_gdf['poi_name'].iloc[0].lower().replace(" ", "_")
            
            if use_parquet and USE_ARROW:
                isochrone_file = os.path.join(
                    output_dir,
                    f'isochrone{travel_time_limit}_{poi_name}.parquet'
                )
                isochrone_gdf.to_parquet(isochrone_file)
            else:
                isochrone_file = os.path.join(
                    output_dir,
                    f'isochrone{travel_time_limit}_{poi_name}.geojson'
                )
                isochrone_gdf.to_file(isochrone_file, driver='GeoJSON', use_arrow=USE_ARROW)
            
            isochrone_files.append(isochrone_file)
    
    # Combine results if requested
    if combine_results:
        combined_gdf = gpd.GeoDataFrame(pd.concat(isochrone_gdfs, ignore_index=True))
        
        if save_individual_files:
            # Save combined result
            if use_parquet and USE_ARROW:
                combined_file = os.path.join(
                    output_dir,
                    f'combined_isochrones_{travel_time_limit}min.parquet'
                )
                combined_gdf.to_parquet(combined_file)
            else:
                combined_file = os.path.join(
                    output_dir,
                    f'combined_isochrones_{travel_time_limit}min.geojson'
                )
                combined_gdf.to_file(combined_file, driver='GeoJSON', use_arrow=USE_ARROW)
            return combined_file
        else:
            return combined_gdf
    
    # Return appropriate result
    if save_individual_files:
        return isochrone_files
    else:
        return isochrone_gdfs

def create_isochrones_from_json_file(
    json_file_path: str,
    travel_time_limit: int,
    output_dir: str = 'isochrones',
    save_individual_files: bool = True,
    combine_results: bool = False,
    simplify_tolerance: Optional[float] = None,
    use_parquet: bool = True,
    **kwargs
) -> Union[str, gpd.GeoDataFrame, List[str]]:
    """
    Create isochrones from POIs stored in a JSON file.
    
    Args:
        json_file_path (str): Path to JSON file containing POI data
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save isochrone files
        save_individual_files (bool): Whether to save individual isochrone files
        combine_results (bool): Whether to combine all isochrones into a single file
        simplify_tolerance (float, optional): Tolerance for geometry simplification
        use_parquet (bool): Whether to use GeoParquet instead of GeoJSON format
        **kwargs: Additional arguments passed to create_isochrones_from_poi_list
        
    Returns:
        Union[str, gpd.GeoDataFrame, List[str]]: Results based on save/combine options
    """
    # Load POI data from JSON file
    with open(json_file_path, 'r') as f:
        poi_data = json.load(f)
    
    return create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time_limit,
        output_dir=output_dir,
        save_individual_files=save_individual_files,
        combine_results=combine_results,
        simplify_tolerance=simplify_tolerance,
        use_parquet=use_parquet,
        **kwargs
    )

# Performance monitoring functions
def get_cache_statistics() -> Dict[str, Any]:
    """Get current cache performance statistics."""
    cache = get_global_cache()
    stats = cache.get_cache_stats()
    
    return {
        'total_requests': stats.total_requests,
        'cache_hits': stats.cache_hits,
        'cache_misses': stats.cache_misses,
        'hit_rate_percent': (stats.cache_hits / stats.total_requests * 100) if stats.total_requests > 0 else 0,
        'total_size_mb': stats.total_size_mb,
        'avg_retrieval_time_ms': stats.avg_retrieval_time_ms,
        'compression_ratio': stats.compression_ratio
    }

def clear_network_cache():
    """Clear the network cache to free up disk space."""
    cache = get_global_cache()
    cache.clear_cache()
    logger.info("Network cache cleared successfully")

# Backward compatibility aliases
create_isochrones_clustered = create_isochrones_from_poi_list  # For backward compatibility

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate isochrones from POIs")
    parser.add_argument("json_file", help="JSON file containing POIs")
    parser.add_argument("--time", type=int, default=30, help="Travel time limit in minutes")
    parser.add_argument("--output-dir", default="output/isochrones", help="Output directory")
    parser.add_argument("--combine", action="store_true", help="Combine all isochrones into a single file")
    parser.add_argument("--simplify", type=float, help="Tolerance for geometry simplification")
    parser.add_argument("--no-parquet", action="store_true", help="Do not use GeoParquet format")
    args = parser.parse_args()
    
    start_time = time.time()
    
    result = create_isochrones_from_json_file(
        json_file_path=args.json_file,
        travel_time_limit=args.time,
        output_dir=args.output_dir,
        combine_results=args.combine,
        simplify_tolerance=args.simplify,
        use_parquet=not args.no_parquet
    )
    
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    hours, minutes = divmod(minutes, 60)
    
    print(f"Total execution time: {int(hours):02d}:{int(minutes):02d}:{seconds:.2f}")
    
    if isinstance(result, list):
        print(f"Generated {len(result)} isochrone files in {args.output_dir}")
    else:
        print(f"Generated combined isochrone file: {result}") 