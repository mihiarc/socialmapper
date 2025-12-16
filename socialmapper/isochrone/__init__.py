#!/usr/bin/env python3
"""Modern Isochrone Generation Module.

This module provides high-performance isochrone generation with intelligent
spatial clustering, advanced network caching, and concurrent processing.

Key Features:
- Intelligent POI clustering using DBSCAN machine learning
- Advanced network caching with SQLite indexing and compression
- Concurrent processing for 4-8x performance improvement
- Automatic optimization based on dataset characteristics
- Comprehensive performance monitoring and statistics
"""

import json
import logging
import os
import time
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional, Union

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
from shapely.geometry import Point

# Import the new progress bar utility
from socialmapper.progress import get_progress_bar

from ..constants import MIN_CLUSTERING_POI_COUNT, MIN_CONCURRENT_POI_COUNT
from .cache import (
    clear_cache,
    download_and_cache_network,
    get_cache,
    get_cache_stats,
    get_global_cache,
)

# Import modernized components
from .clustering import (
    IntelligentPOIClusterer,
    OptimizedPOICluster,
    benchmark_clustering_performance,
    create_isochrone_from_poi_with_network,
    create_optimized_clusters,
)
from .concurrent import ConcurrentIsochroneProcessor, ProcessingStats, process_isochrones_concurrent
from .travel_modes import TravelMode, get_travel_mode_config

# Setup logging
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
    poi: dict[str, Any],
    travel_time_limit: int,
    output_dir: str = "output/isochrones",
    save_file: bool = True,
    simplify_tolerance: float | None = None,
    use_parquet: bool = True,
    travel_mode: TravelMode = TravelMode.DRIVE,
    restrict_to_country: str | None = None,
) -> str | gpd.GeoDataFrame:
    """Create an isochrone from a POI using modern optimized methods.

    Parameters
    ----------
    poi : dict
        POI dictionary containing at minimum 'lat', 'lon', and 'tags'.
    travel_time_limit : int
        Travel time limit in minutes.
    output_dir : str, optional
        Directory to save the isochrone file, by default
        "output/isochrones".
    save_file : bool, optional
        Whether to save the isochrone to a file, by default True.
    simplify_tolerance : float or None, optional
        Tolerance for geometry simplification, by default None.
    use_parquet : bool, optional
        Whether to use GeoParquet instead of GeoJSON format,
        by default True.
    travel_mode : TravelMode, optional
        Mode of travel (walk, bike, drive), by default TravelMode.DRIVE.
    restrict_to_country : str or None, optional
        ISO 3166-1 alpha-2 country code (e.g., 'US') to restrict
        roads to that country only, by default None.

    Returns
    -------
    str or gpd.GeoDataFrame
        File path if save_file=True, or GeoDataFrame if save_file=False.
    """
    # Extract coordinates
    latitude = poi.get("lat")
    longitude = poi.get("lon")

    if latitude is None or longitude is None:
        raise ValueError("POI must contain 'lat' and 'lon' coordinates")

    # Get POI name (or use ID if no name is available)
    poi_name = poi.get("tags", {}).get("name", f"poi_{poi.get('id', 'unknown')}")

    # Use modern caching system for network download
    cache = get_global_cache()

    # Calculate bounding box for network download
    buffer_km = travel_time_limit * 1.5  # Adaptive buffer based on travel time
    buffer_deg = buffer_km / 111.0
    bbox = (
        latitude - buffer_deg,
        longitude - buffer_deg,
        latitude + buffer_deg,
        longitude + buffer_deg,
    )

    # Download network with caching
    graph = download_and_cache_network(
        bbox=bbox,
        travel_time_minutes=travel_time_limit,
        cluster_size=1,
        cache=cache,
        travel_mode=travel_mode,
        restrict_to_country=restrict_to_country,
    )

    if graph is None:
        raise RuntimeError(f"Failed to download road network for POI {poi_name}")

    # Create isochrone using optimized method
    isochrone_gdf = create_isochrone_from_poi_with_network(
        poi=poi,
        network=graph,
        network_crs=graph.graph["crs"],
        travel_time_minutes=travel_time_limit,
        travel_mode=travel_mode,
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
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if use_parquet and USE_ARROW:
            # Save as GeoParquet for better performance
            isochrone_file = Path(output_dir) / f"isochrone{travel_time_limit}_{poi_name}.parquet"
            isochrone_gdf.to_parquet(isochrone_file)
        else:
            # Fallback to GeoJSON
            isochrone_file = Path(output_dir) / f"isochrone{travel_time_limit}_{poi_name}.geojson"
            isochrone_gdf.to_file(isochrone_file, driver="GeoJSON", use_arrow=USE_ARROW)

        return isochrone_file

    return isochrone_gdf


def get_bounding_box(
    pois: list[dict[str, Any]], buffer_km: float = 5.0
) -> tuple[float, float, float, float]:
    """Get a bounding box for a list of POIs with a buffer.

    Parameters
    ----------
    pois : list of dict
        List of POI dictionaries with 'lat' and 'lon'.
    buffer_km : float, optional
        Buffer in kilometers to add around the POIs, by default 5.0.

    Returns
    -------
    tuple of (float, float, float, float)
        Tuple of (min_lat, min_lon, max_lat, max_lon).
    """
    lons = [poi.get("lon") for poi in pois if poi.get("lon") is not None]
    lats = [poi.get("lat") for poi in pois if poi.get("lat") is not None]

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
    poi_data: dict[str, list[dict[str, Any]]],
    travel_time_limit: int,
    output_dir: str = "output/isochrones",
    save_individual_files: bool = True,
    combine_results: bool = False,
    simplify_tolerance: float | None = None,
    use_parquet: bool = True,
    use_clustering: bool | None = None,
    max_cluster_radius_km: float = 15.0,
    min_cluster_size: int = 2,
    use_concurrent: bool | None = None,
    max_network_workers: int = 8,
    max_isochrone_workers: int | None = None,
    progress_callback: Callable | None = None,
    travel_mode: TravelMode = TravelMode.DRIVE,
) -> str | gpd.GeoDataFrame | list[str]:
    """Create isochrones from a list of POIs with modern optimization.

    Parameters
    ----------
    poi_data : dict
        Dictionary with 'pois' key containing list of POIs.
    travel_time_limit : int
        Travel time limit in minutes.
    output_dir : str, optional
        Directory to save isochrone files, by default
        "output/isochrones".
    save_individual_files : bool, optional
        Whether to save individual isochrone files, by default True.
    combine_results : bool, optional
        Whether to combine all isochrones into a single file,
        by default False.
    simplify_tolerance : float or None, optional
        Tolerance for geometry simplification, by default None.
    use_parquet : bool, optional
        Whether to use GeoParquet instead of GeoJSON format,
        by default True.
    use_clustering : bool or None, optional
        Whether to use clustering optimization, by default None.
    max_cluster_radius_km : float, optional
        Maximum radius for clustering in kilometers, by default 15.0.
    min_cluster_size : int, optional
        Minimum number of POIs to form a cluster, by default 2.
    use_concurrent : bool or None, optional
        Whether to use concurrent processing, by default None.
    max_network_workers : int, optional
        Maximum concurrent network downloads, by default 8.
    max_isochrone_workers : int or None, optional
        Maximum concurrent isochrone calculations, by default None.
    progress_callback : Callable or None, optional
        Progress callback function, by default None.
    travel_mode : TravelMode, optional
        Mode of travel (walk, bike, drive), by default
        TravelMode.DRIVE.

    Returns
    -------
    str or gpd.GeoDataFrame or list of str
        Results based on save/combine options.
    """
    pois = poi_data.get("pois", [])
    if not pois:
        raise ValueError(
            "No POIs found in input data. Please try different search parameters or a different location."
        )

    logger.info(f"Processing {len(pois)} POIs with modern isochrone generation")

    # Auto-decide optimization strategies
    if use_clustering is None:
        # Use clustering for datasets with 5+ POIs
        use_clustering = len(pois) >= MIN_CLUSTERING_POI_COUNT
        if use_clustering:
            # Quick benchmark to verify clustering benefit
            benchmark = benchmark_clustering_performance(
                pois, travel_time_limit, max_cluster_radius_km
            )
            efficiency_rating = benchmark["recommendations"]["efficiency_rating"]
            if efficiency_rating == "Fair":
                use_clustering = False
                logger.info("Clustering not beneficial for this dataset distribution")
            else:
                logger.info(f"Auto-enabling clustering: {efficiency_rating} efficiency rating")

    if use_concurrent is None:
        # Use concurrent processing for datasets with 3+ POIs
        use_concurrent = len(pois) >= MIN_CONCURRENT_POI_COUNT
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
            progress_callback=progress_callback,
            travel_mode=travel_mode,
        )

    elif use_clustering:
        logger.info("Using intelligent clustering optimization")

        # Create optimized clusters
        clusters = create_optimized_clusters(
            pois=pois,
            travel_time_minutes=travel_time_limit,
            max_cluster_radius_km=max_cluster_radius_km,
            min_cluster_size=min_cluster_size,
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
                cache=cache,
                travel_mode=travel_mode,
            )

            if network is None:
                logger.warning(f"Failed to download network for cluster {cluster.cluster_id}")
                continue

            cluster.network = network
            cluster.network_crs = network.graph["crs"]

            # Generate isochrones for all POIs in cluster
            for poi in cluster.pois:
                isochrone_gdf = create_isochrone_from_poi_with_network(
                    poi=poi,
                    network=cluster.network,
                    network_crs=cluster.network_crs,
                    travel_time_minutes=travel_time_limit,
                    travel_mode=travel_mode,
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
                    use_parquet=use_parquet,
                    travel_mode=travel_mode,
                )
                isochrone_gdfs.append(result)

            except (ValueError, KeyError, TypeError, nx.NetworkXError, ox._errors.InsufficientResponseError) as e:
                poi_name = poi.get("tags", {}).get("name", poi.get("id", "unknown"))
                logger.error(f"Error creating isochrone for POI {poi_name}: {e}")
                continue
            except OSError as e:
                poi_name = poi.get("tags", {}).get("name", poi.get("id", "unknown"))
                logger.error(f"Network/file error creating isochrone for POI {poi_name}: {e}")
                continue

    # Handle file saving and combining
    if not isochrone_gdfs:
        logger.warning("No isochrones were successfully generated")
        # When combine_results is True, we should return an empty GeoDataFrame, not a list
        if combine_results and not save_individual_files:
            return gpd.GeoDataFrame()
        return [] if save_individual_files else gpd.GeoDataFrame()

    logger.info(f"Successfully generated {len(isochrone_gdfs)} isochrones")

    # Save individual files if requested
    isochrone_files = []
    if save_individual_files:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for isochrone_gdf in isochrone_gdfs:
            poi_name = isochrone_gdf["poi_name"].iloc[0].lower().replace(" ", "_")

            if use_parquet and USE_ARROW:
                isochrone_file = Path(output_dir) / f"isochrone{travel_time_limit}_{poi_name}.parquet"
                isochrone_gdf.to_parquet(isochrone_file)
            else:
                isochrone_file = Path(output_dir) / f"isochrone{travel_time_limit}_{poi_name}.geojson"
                isochrone_gdf.to_file(isochrone_file, driver="GeoJSON", use_arrow=USE_ARROW)

            isochrone_files.append(isochrone_file)

    # Combine results if requested
    if combine_results:
        combined_gdf = gpd.GeoDataFrame(pd.concat(isochrone_gdfs, ignore_index=True))

        if save_individual_files:
            # Save combined result
            if use_parquet and USE_ARROW:
                combined_file = Path(output_dir) / f"combined_isochrones_{travel_time_limit}min.parquet"
                combined_gdf.to_parquet(combined_file)
            else:
                combined_file = Path(output_dir) / f"combined_isochrones_{travel_time_limit}min.geojson"
                combined_gdf.to_file(combined_file, driver="GeoJSON", use_arrow=USE_ARROW)
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
    output_dir: str = "isochrones",
    save_individual_files: bool = True,
    combine_results: bool = False,
    simplify_tolerance: float | None = None,
    use_parquet: bool = True,
    **kwargs,
) -> str | gpd.GeoDataFrame | list[str]:
    """Create isochrones from POIs stored in a JSON file.

    Parameters
    ----------
    json_file_path : str
        Path to JSON file containing POI data.
    travel_time_limit : int
        Travel time limit in minutes.
    output_dir : str, optional
        Directory to save isochrone files, by default "isochrones".
    save_individual_files : bool, optional
        Whether to save individual isochrone files, by default True.
    combine_results : bool, optional
        Whether to combine all isochrones into a single file,
        by default False.
    simplify_tolerance : float, optional
        Tolerance for geometry simplification, by default None.
    use_parquet : bool, optional
        Whether to use GeoParquet instead of GeoJSON format,
        by default True.
    **kwargs : dict
        Additional arguments passed to create_isochrones_from_poi_list.

    Returns
    -------
    str or gpd.GeoDataFrame or list of str
        Results based on save/combine options.
    """
    # Load POI data from JSON file
    with Path(json_file_path).open() as f:
        poi_data = json.load(f)

    return create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time_limit,
        output_dir=output_dir,
        save_individual_files=save_individual_files,
        combine_results=combine_results,
        simplify_tolerance=simplify_tolerance,
        use_parquet=use_parquet,
        **kwargs,
    )


# Performance monitoring functions
def get_cache_statistics() -> dict[str, Any]:
    """Get current cache performance statistics."""
    return get_cache_stats()


def clear_network_cache():
    """Clear the network cache to free up disk space."""
    clear_cache()


# Backward compatibility aliases
create_isochrones_clustered = create_isochrones_from_poi_list  # For backward compatibility

if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Generate isochrones from POIs")
    parser.add_argument("json_file", help="JSON file containing POIs")
    parser.add_argument("--time", type=int, default=30, help="Travel time limit in minutes")
    parser.add_argument("--output-dir", default="output/isochrones", help="Output directory")
    parser.add_argument(
        "--combine", action="store_true", help="Combine all isochrones into a single file"
    )
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
        use_parquet=not args.no_parquet,
    )

    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    hours, minutes = divmod(minutes, 60)

    print(f"Total execution time: {int(hours):02d}:{int(minutes):02d}:{seconds:.2f}")

    if isinstance(result, list):
        print(f"Generated {len(result)} isochrone files in {args.output_dir}")
    else:
        print(f"Generated combined isochrone file: {result}")
