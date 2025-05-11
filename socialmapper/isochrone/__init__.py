#!/usr/bin/env python3
"""
Module to generate isochrones from Points of Interest (POIs).
"""
import os
import warnings
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point
from typing import Dict, Any, List, Union, Tuple, Optional
import json
import pandas as pd
from tqdm import tqdm
from socialmapper.progress import get_progress_bar
import time
import logging
from rtree import index
import multiprocessing
from functools import partial
import concurrent.futures
import alphashape

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

# Global graph cache
class GraphCache:
    """
    Cache for network graphs to avoid redundant downloads.
    Uses R-tree spatial indexing to efficiently find graphs that cover a given point.
    """
    def __init__(self, max_cache_size=10):
        """
        Initialize the graph cache.
        
        Args:
            max_cache_size: Maximum number of graphs to keep in cache
        """
        self.cache = {}  # Maps graph_id to (graph, bounds)
        self.idx = index.Index()  # R-tree for spatial indexing
        self.graph_id_counter = 0
        self.max_cache_size = max_cache_size
        self.access_times = {}  # For LRU cache eviction
        
    def add_graph(self, graph, bounds):
        """
        Add a graph to the cache.
        
        Args:
            graph: NetworkX graph
            bounds: (min_x, min_y, max_x, max_y) bounds of the graph
        
        Returns:
            graph_id: ID of the cached graph
        """
        # If cache is full, remove least recently used graph
        if len(self.cache) >= self.max_cache_size:
            oldest_id = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_id]
            del self.access_times[oldest_id]
            self.idx.delete(oldest_id, bounds)
            logger.info(f"Cache full - removed graph {oldest_id}")
        
        graph_id = self.graph_id_counter
        self.graph_id_counter += 1
        
        self.cache[graph_id] = (graph, bounds)
        self.idx.insert(graph_id, bounds)
        self.access_times[graph_id] = time.time()
        
        logger.info(f"Added graph {graph_id} to cache with bounds {bounds}")
        return graph_id
    
    def get_graph_for_point(self, lat, lon, dist_meters):
        """
        Find a cached graph that covers the given point.
        
        Args:
            lat: Latitude
            lon: Longitude
            dist_meters: Required distance in meters from point
            
        Returns:
            graph or None if no suitable graph found
        """
        # Approximate conversion from meters to degrees (rough estimate)
        buffer_deg = dist_meters / 111000.0  # ~111km per degree at equator
        
        # Define search bounds
        search_bounds = (
            lon - buffer_deg, 
            lat - buffer_deg, 
            lon + buffer_deg, 
            lat + buffer_deg
        )
        
        # Check if any cached graph fully contains the search bounds
        for graph_id in self.idx.intersection(search_bounds):
            _, graph_bounds = self.cache[graph_id]
            
            # Check if the graph bounds fully contain the search bounds
            if (graph_bounds[0] <= search_bounds[0] and
                graph_bounds[1] <= search_bounds[1] and
                graph_bounds[2] >= search_bounds[2] and
                graph_bounds[3] >= search_bounds[3]):
                
                # Update access time for LRU
                self.access_times[graph_id] = time.time()
                logger.info(f"Cache hit - using graph {graph_id} for point ({lat}, {lon})")
                return self.cache[graph_id][0]
        
        logger.info(f"Cache miss - no suitable graph found for point ({lat}, {lon})")
        return None
    
    def clear(self):
        """Clear the cache completely"""
        self.cache = {}
        self.idx = index.Index()
        self.graph_id_counter = 0
        self.access_times = {}
        logger.info("Graph cache cleared")

# Initialize global graph cache
graph_cache = GraphCache(max_cache_size=10)

def get_network_graph(latitude, longitude, dist_meters, simplify=True):
    """
    Get a road network graph, using cache if available.
    
    Args:
        latitude: Latitude of the center point
        longitude: Longitude of the center point
        dist_meters: Required distance in meters from point
        simplify: Whether to simplify the graph topology (reduces complexity, may slightly affect accuracy)
        
    Returns:
        NetworkX graph
    """
    # Try to get a cached graph first
    G = graph_cache.get_graph_for_point(latitude, longitude, dist_meters)
    
    if G is not None:
        return G
    
    # No suitable graph in cache, download a new one
    # Download with extra buffer to make it more reusable
    buffer_factor = 1.5  # 50% larger area to improve cache reuse
    download_dist = dist_meters * buffer_factor
    
    # Record start time for performance measurement
    start_time = time.time()
    
    try:
        G = ox.graph_from_point(
            (latitude, longitude),
            network_type='drive',
            dist=download_dist
        )
        
        # Record time spent downloading
        download_time = time.time() - start_time
        logger.info(f"Downloaded new network graph in {download_time:.2f} seconds")
        
        # Log the original graph size 
        num_nodes_original = len(G.nodes)
        num_edges_original = len(G.edges)
        logger.info(f"Original graph size: {num_nodes_original} nodes, {num_edges_original} edges")
        
        # Simplify the graph if requested
        if simplify:
            try:
                simplify_start = time.time()
                # Check if the graph is already simplified
                is_simplified = G.graph.get('simplified', False)
                
                if not is_simplified:
                    G = ox.simplify_graph(G)
                    simplify_time = time.time() - simplify_start
                    
                    # Log the simplified graph size and time
                    num_nodes_simplified = len(G.nodes)
                    num_edges_simplified = len(G.edges)
                    node_reduction = (1 - num_nodes_simplified / num_nodes_original) * 100 if num_nodes_original > 0 else 0
                    edge_reduction = (1 - num_edges_simplified / num_edges_original) * 100 if num_edges_original > 0 else 0
                    
                    logger.info(f"Simplified graph in {simplify_time:.2f} seconds")
                    logger.info(f"Simplified graph size: {num_nodes_simplified} nodes ({node_reduction:.1f}% reduction), "
                                f"{num_edges_simplified} edges ({edge_reduction:.1f}% reduction)")
                else:
                    logger.info("Graph is already simplified, skipping simplification")
            except Exception as e:
                logger.warning(f"Graph simplification failed: {e}. Continuing with original graph.")
        
        # Add speeds and travel times
        G = ox.add_edge_speeds(G, fallback=50)
        G = ox.add_edge_travel_times(G)
        G = ox.project_graph(G)
        
        # Calculate the bounds of the graph
        nodes = pd.DataFrame(
            {data['x']: data['y'] for _, data in G.nodes(data=True)}.items(),
            columns=['x', 'y']
        )
        
        if not nodes.empty:
            min_x, min_y = nodes['x'].min(), nodes['y'].min()
            max_x, max_y = nodes['x'].max(), nodes['y'].max()
            
            # Convert to lon/lat
            graph_crs = G.graph['crs']
            bounds_gdf = gpd.GeoDataFrame(
                geometry=[Point(min_x, min_y), Point(max_x, max_y)],
                crs=graph_crs
            ).to_crs('EPSG:4326')
            
            min_lon, min_lat = bounds_gdf.iloc[0].geometry.x, bounds_gdf.iloc[0].geometry.y
            max_lon, max_lat = bounds_gdf.iloc[1].geometry.x, bounds_gdf.iloc[1].geometry.y
            
            # Add to cache
            bounds = (min_lon, min_lat, max_lon, max_lat)
            graph_cache.add_graph(G, bounds)
        
        return G
    except Exception as e:
        logger.error(f"Error downloading road network: {e}")
        raise

def create_isochrone_from_poi(
    poi: Dict[str, Any],
    travel_time_limit: int,
    output_dir: str = 'output/isochrones',
    save_file: bool = True,
    simplify_tolerance: Optional[float] = None,
    use_parquet: bool = True,
    simplify_graph: bool = True,
    use_alpha_shape: bool = True,
    alpha: float = 0.5
) -> Union[str, gpd.GeoDataFrame]:
    """
    Create an isochrone from a POI.
    
    Args:
        poi (Dict[str, Any]): POI dictionary containing at minimum 'lat', 'lon', and 'tags'
            poi is generated from the query.py module based on a poi_config.yaml file
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save the isochrone file
        save_file (bool): Whether to save the isochrone to a file
        simplify_tolerance (float, optional): Tolerance for geometry simplification
            If provided, geometries will be simplified to improve performance
        use_parquet (bool): Whether to use GeoParquet instead of GeoJSON format
        simplify_graph (bool): Whether to simplify the road network graph 
            (reduces computation time but may slightly affect accuracy)
        use_alpha_shape (bool): Whether to use alpha shapes (concave hull) instead of convex hull
            for more accurate isochrones that better follow the road network shape
        alpha (float): Alpha value for alpha shape generation
            Default is 0.5 which works well for most road networks
            Lower values (0.001-0.1) create more detailed shapes
            Higher values may result in empty shapes (test showed empty for α>0.5)
        
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
    
    # Download and prepare road network using the caching mechanism
    # Convert travel time to approximate distance (assuming ~50 km/h average speed)
    dist_meters = travel_time_limit * 60 * (50/3.6)  # minutes * seconds * meters per second
    
    try:
        # Use cached graph if available, otherwise download new one
        G = get_network_graph(latitude, longitude, dist_meters, simplify=simplify_graph)
    except Exception as e:
        logger.error(f"Error getting road network: {e}")
        raise
    
    # Create point from coordinates
    poi_point = Point(longitude, latitude)
    poi_geom = gpd.GeoSeries(
        [poi_point],
        crs='EPSG:4326'
    ).to_crs(G.graph['crs'])
    poi_proj = poi_geom.geometry.iloc[0]
    
    # Find nearest node and reachable area
    poi_node = ox.nearest_nodes(
        G,
        X=poi_proj.x,
        Y=poi_proj.y
    )
    
    # Generate subgraph based on travel time
    subgraph = nx.ego_graph(
        G,
        poi_node,
        radius=travel_time_limit * 60,  # Convert minutes to seconds
        distance='travel_time'
    )
    
    # Create isochrone
    node_points = [Point((data['x'], data['y'])) 
                  for node, data in subgraph.nodes(data=True)]
    nodes_gdf = gpd.GeoDataFrame(geometry=node_points, crs=G.graph['crs'])
    
    if use_alpha_shape and len(node_points) > 10:  # Need at least 10 points for alpha shape
        try:
            # Extract coordinates for alpha shape
            point_coords = [(p.x, p.y) for p in node_points]
            
            # Adjust alpha parameter based on point density and distribution
            # Based on testing, alpha values > 0.5 often produce empty shapes 
            # for real-world road networks
            adjusted_alpha = min(alpha, 0.5)  # Cap at 0.5
            
            # Use progressively smaller alpha for denser point sets
            if len(point_coords) < 100:
                adjusted_alpha = min(adjusted_alpha, 0.3)
            elif len(point_coords) < 1000:
                adjusted_alpha = min(adjusted_alpha, 0.2)
            elif len(point_coords) > 10000:
                adjusted_alpha = min(adjusted_alpha, 0.05)
            
            # Calculate the alpha shape (concave hull)
            alpha_start = time.time()
            alpha_shape = alphashape.alphashape(point_coords, alpha=adjusted_alpha)
            alpha_time = time.time() - alpha_start
            
            logger.debug(f"Generated alpha shape (α={adjusted_alpha}) in {alpha_time:.3f}s")
            
            # Check if the result is a valid non-empty polygon
            is_valid_shape = (alpha_shape and
                              alpha_shape.is_valid and
                              not alpha_shape.is_empty and
                              alpha_shape.geom_type in ['Polygon', 'MultiPolygon'])
            
            if is_valid_shape:
                isochrone = alpha_shape
                logger.debug(f"Using alpha shape with {len(point_coords)} points")
            else:
                # Try with an even smaller alpha value if the initial one failed
                if adjusted_alpha > 0.01 and alpha_shape.is_empty:
                    logger.warning(f"Alpha shape with α={adjusted_alpha} produced empty result, trying with α=0.01")
                    alpha_shape = alphashape.alphashape(point_coords, alpha=0.01)
                    
                    if alpha_shape and alpha_shape.is_valid and not alpha_shape.is_empty:
                        isochrone = alpha_shape
                        logger.debug(f"Using alpha shape with α=0.01 and {len(point_coords)} points")
                    else:
                        # Fallback to convex hull if alpha shape generation fails
                        logger.warning(f"Alpha shape generation failed or produced empty result, falling back to convex hull")
                        isochrone = nodes_gdf.unary_union.convex_hull
                else:
                    # Fallback to convex hull
                    logger.warning(f"Alpha shape generation with α={adjusted_alpha} produced {alpha_shape.geom_type}, falling back to convex hull")
                    isochrone = nodes_gdf.unary_union.convex_hull
        except Exception as e:
            # Fallback to convex hull if alpha shape generation fails
            logger.warning(f"Alpha shape generation failed: {e}, falling back to convex hull")
            isochrone = nodes_gdf.unary_union.convex_hull
    else:
        # Use convex hull if alpha shape is not requested or we have too few points
        isochrone = nodes_gdf.unary_union.convex_hull
        if use_alpha_shape and len(node_points) <= 10:
            logger.warning(f"Too few points ({len(node_points)}) for alpha shape, using convex hull")
    
    # Create GeoDataFrame with the isochrone
    isochrone_gdf = gpd.GeoDataFrame(
        geometry=[isochrone],
        crs=G.graph['crs']
    )
    
    # Convert to WGS84 for standard output
    isochrone_gdf = isochrone_gdf.to_crs('EPSG:4326')
    
    # Simplify geometry if tolerance is provided
    if simplify_tolerance is not None:
        isochrone_gdf["geometry"] = isochrone_gdf.geometry.simplify(
            tolerance=simplify_tolerance, preserve_topology=True
        )
    
    # Add metadata
    isochrone_gdf['poi_id'] = poi.get('id', 'unknown')
    isochrone_gdf['poi_name'] = poi_name
    isochrone_gdf['travel_time_minutes'] = travel_time_limit
    isochrone_gdf['method'] = 'alpha_shape' if use_alpha_shape and len(node_points) > 10 else 'convex_hull'
    
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
        Tuple of (min_x, min_y, max_x, max_y)
    """
    lons = [poi.get('lon') for poi in pois if poi.get('lon') is not None]
    lats = [poi.get('lat') for poi in pois if poi.get('lat') is not None]
    
    if not lons or not lats:
        raise ValueError("No valid coordinates in POIs")
    
    # Convert buffer to approximate degrees (rough estimate)
    buffer_deg = buffer_km / 111.0  # ~111km per degree at equator
    
    min_x = min(lons) - buffer_deg
    min_y = min(lats) - buffer_deg
    max_x = max(lons) + buffer_deg
    max_y = max(lats) + buffer_deg
    
    return (min_x, min_y, max_x, max_y)

def process_poi_for_parallel(
    poi: Dict[str, Any],
    index: int,
    travel_time_limit: int,
    output_dir: str,
    save_individual_files: bool,
    simplify_tolerance: Optional[float],
    use_parquet: bool,
    total: int
) -> Union[str, gpd.GeoDataFrame]:
    """
    Process a single POI for parallel execution.
    
    Args:
        poi: POI dictionary
        index: Index of this POI in the batch (for logging)
        travel_time_limit: Travel time limit in minutes
        output_dir: Directory to save isochrone files
        save_individual_files: Whether to save individual isochrone files
        simplify_tolerance: Tolerance for geometry simplification
        use_parquet: Whether to use GeoParquet
        total: Total number of POIs in the batch
        
    Returns:
        File path or GeoDataFrame depending on save_individual_files
    """
    poi_name = poi.get('tags', {}).get('name', poi.get('id', 'unknown'))
    
    try:
        result = create_isochrone_from_poi(
            poi=poi,
            travel_time_limit=travel_time_limit,
            output_dir=output_dir,
            save_file=save_individual_files,
            simplify_tolerance=simplify_tolerance,
            use_parquet=use_parquet
        )
        
        # Log progress but avoid using tqdm.write which is not thread-safe
        logger.info(f"[{index+1}/{total}] Created isochrone for POI: {poi_name}")
        return result
    except Exception as e:
        logger.error(f"Error creating isochrone for POI {poi_name}: {e}")
        return None

def create_isochrones_from_poi_list(
    poi_data: Dict[str, List[Dict[str, Any]]],
    travel_time_limit: int,
    output_dir: str = 'output/isochrones',
    save_individual_files: bool = True,
    combine_results: bool = False,
    simplify_tolerance: Optional[float] = None,
    use_parquet: bool = True,
    n_jobs: int = 1,  # Number of parallel jobs to run
    simplify_graph: bool = True,  # Whether to simplify the graph topology
    use_alpha_shape: bool = True,  # Whether to use alpha shapes
    alpha: float = 0.5  # Alpha value for alpha shape generation
) -> Union[str, gpd.GeoDataFrame, List[str]]:
    """
    Create isochrones from a list of POIs.
    
    Args:
        poi_data (Dict[str, List[Dict]]): Dictionary with 'pois' key containing list of POIs
            poi_data is generated from the query.py module based on a poi_config.yaml file
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save isochrone files
        save_individual_files (bool): Whether to save individual isochrone files
        combine_results (bool): Whether to combine all isochrones into a single file
        simplify_tolerance (float, optional): Tolerance for geometry simplification
        use_parquet (bool): Whether to use GeoParquet instead of GeoJSON format
        n_jobs (int): Number of parallel jobs to run
            n_jobs=1: Sequential processing (no parallelism)
            n_jobs=-1: Use all available CPU cores
            n_jobs>1: Use specified number of CPU cores
        simplify_graph (bool): Whether to simplify the road network graph topology
            (reduces computation time but may slightly affect accuracy)
        use_alpha_shape (bool): Whether to use alpha shapes (concave hull) instead of convex hull
        alpha (float): Alpha value for alpha shape generation (higher = smoother shapes)
        
    Returns:
        Union[str, gpd.GeoDataFrame, List[str]]:
            - Combined file path if combine_results=True and save_individual_files=True
            - Combined GeoDataFrame if combine_results=True and save_individual_files=False
            - List of file paths if save_individual_files=True and combine_results=False
    """
    pois = poi_data.get('pois', [])
    if not pois:
        raise ValueError("No POIs found in input data. Please try different search parameters or a different location. POIs like 'natural=forest' may not exist in all areas.")
    
    # Use all available CPU cores if n_jobs is -1
    if n_jobs == -1:
        n_jobs = multiprocessing.cpu_count()
    
    # Log parallel processing configuration
    if n_jobs > 1:
        logger.info(f"Processing {len(pois)} POIs using {n_jobs} parallel workers")
    
    isochrone_files = []
    isochrone_gdfs = []
    
    # Process POIs either sequentially or in parallel
    if n_jobs <= 1:
        # Sequential processing with progress bar
        for poi in get_progress_bar(pois, desc="Generating isochrones", unit="POI"):
            poi_name = poi.get('tags', {}).get('name', poi.get('id', 'unknown'))
            try:
                result = create_isochrone_from_poi(
                    poi=poi,
                    travel_time_limit=travel_time_limit,
                    output_dir=output_dir,
                    save_file=save_individual_files,
                    simplify_tolerance=simplify_tolerance,
                    use_parquet=use_parquet,
                    simplify_graph=simplify_graph,
                    use_alpha_shape=use_alpha_shape,
                    alpha=alpha
                )
                
                if save_individual_files:
                    isochrone_files.append(result)
                else:
                    isochrone_gdfs.append(result)
                    
                # Use tqdm.write instead of logger to avoid messing up the progress bar
                tqdm.write(f"Created isochrone for POI: {poi_name}")
            except Exception as e:
                tqdm.write(f"Error creating isochrone for POI {poi_name}: {e}")
                logger.error(f"Error creating isochrone for POI {poi.get('id', 'unknown')}: {e}")
                # Continue with next POI instead of failing
                continue
    else:
        # Parallel processing using ThreadPoolExecutor
        # We use threads instead of processes because the network I/O is the bottleneck,
        # and this allows us to share the graph cache between threads
        process_func = partial(
            process_poi_for_parallel,
            travel_time_limit=travel_time_limit,
            output_dir=output_dir,
            save_individual_files=save_individual_files,
            simplify_tolerance=simplify_tolerance,
            use_parquet=use_parquet,
            total=len(pois)
        )
        
        # Create a progress bar that will be updated by the main thread
        pbar = tqdm(total=len(pois), desc="Generating isochrones", unit="POI")
        
        # Process POIs in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_jobs) as executor:
            # Submit all tasks and get future objects
            future_to_index = {
                executor.submit(process_func, poi, i): i 
                for i, poi in enumerate(pois)
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                pbar.update(1)  # Update progress bar
                
                try:
                    result = future.result()
                    if result is not None:
                        if save_individual_files:
                            isochrone_files.append(result)
                        else:
                            isochrone_gdfs.append(result)
                except Exception as e:
                    logger.error(f"Exception in worker thread: {e}")
        
        pbar.close()
    
    # Combine results if requested (same logic as before)
    if combine_results:
        if isochrone_gdfs or not save_individual_files:
            # If we have GeoDataFrames (or didn't save individual files), combine them
            if isochrone_gdfs:
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
            else:
                logger.warning("No isochrones were successfully generated")
                return [] if save_individual_files else gpd.GeoDataFrame()
        else:
            # We need to load the individual files and combine them
            gdfs = []
            
            # Get a spatial bounding box for all the files if possible
            bbox = None
            if all(file.endswith('.geojson') for file in isochrone_files):
                try:
                    # Get the bbox of the first file to initialize
                    first_gdf = gpd.read_file(isochrone_files[0], engine="pyogrio", use_arrow=USE_ARROW)
                    total_bounds = list(first_gdf.total_bounds)
                    
                    # Expand bbox for each subsequent file
                    for file in isochrone_files[1:]:
                        try:
                            bounds = gpd.read_file(
                                file, 
                                engine="pyogrio", 
                                use_arrow=USE_ARROW,
                                bbox_expand=0.1  # Read a bit more to ensure we get bounds
                            ).total_bounds
                            total_bounds[0] = min(total_bounds[0], bounds[0])
                            total_bounds[1] = min(total_bounds[1], bounds[1])
                            total_bounds[2] = max(total_bounds[2], bounds[2])
                            total_bounds[3] = max(total_bounds[3], bounds[3])
                        except Exception:
                            # If we can't get bounds, skip this optimization
                            pass
                    
                    bbox = tuple(total_bounds)
                    logger.info(f"Using bounding box for optimized reads: {bbox}")
                except Exception as e:
                    logger.warning(f"Could not determine bounding box for optimization: {e}")
            
            for file in get_progress_bar(isochrone_files, desc="Loading isochrones", unit="file"):
                if file.endswith('.parquet'):
                    gdfs.append(gpd.read_parquet(file))
                else:
                    # For GeoJSON files, use bbox if available
                    if bbox:
                        gdfs.append(gpd.read_file(
                            file, 
                            engine="pyogrio", 
                            use_arrow=USE_ARROW,
                            bbox=bbox
                        ))
                    else:
                        gdfs.append(gpd.read_file(file, engine="pyogrio", use_arrow=USE_ARROW))
            
            combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
            
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
    n_jobs: int = 1,  # Number of parallel jobs to run
    simplify_graph: bool = True,  # Whether to simplify the graph topology
    use_alpha_shape: bool = True,  # Whether to use alpha shapes
    alpha: float = 0.5  # Alpha value for alpha shape generation
) -> Union[str, gpd.GeoDataFrame, List[str]]:
    """
    Create isochrones from a JSON file containing POIs.
    
    Args:
        json_file_path (str): Path to JSON file containing POIs
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save isochrone files
        save_individual_files (bool): Whether to save individual isochrone files
        combine_results (bool): Whether to combine all isochrones into a single file
        simplify_tolerance (float, optional): Tolerance for geometry simplification
        use_parquet (bool): Whether to use GeoParquet instead of GeoJSON format
        n_jobs (int): Number of parallel jobs to run
            n_jobs=1: Sequential processing (no parallelism)
            n_jobs=-1: Use all available CPU cores
            n_jobs>1: Use specified number of CPU cores
        simplify_graph (bool): Whether to simplify the road network graph topology
            (reduces computation time but may slightly affect accuracy)
        use_alpha_shape (bool): Whether to use alpha shapes (concave hull) instead of convex hull
        alpha (float): Alpha value for alpha shape generation (higher = smoother shapes)
        
    Returns:
        Union[str, gpd.GeoDataFrame, List[str]]: See create_isochrones_from_poi_list
    """
    try:
        with open(json_file_path, 'r') as f:
            poi_data = json.load(f)
        tqdm.write(f"Loaded {len(poi_data.get('pois', []))} POIs from {json_file_path}")
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        raise
    
    return create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time_limit,
        output_dir=output_dir,
        save_individual_files=save_individual_files,
        combine_results=combine_results,
        simplify_tolerance=simplify_tolerance,
        use_parquet=use_parquet,
        n_jobs=n_jobs,
        simplify_graph=simplify_graph,
        use_alpha_shape=use_alpha_shape,
        alpha=alpha
    )

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
    parser.add_argument("--jobs", "-j", type=int, default=1, 
                      help="Number of parallel jobs to run (default=1, -1=all cores)")
    parser.add_argument("--no-simplify-graph", action="store_true", 
                      help="Disable graph topology simplification")
    parser.add_argument("--no-alpha-shape", action="store_true",
                      help="Use convex hull instead of alpha shapes (concave hull)")
    parser.add_argument("--alpha", type=float, default=0.5,
                      help="Alpha value for alpha shape generation (default=0.5)")
    args = parser.parse_args()
    
    start_time = time.time()
    
    result = create_isochrones_from_json_file(
        json_file_path=args.json_file,
        travel_time_limit=args.time,
        output_dir=args.output_dir,
        combine_results=args.combine,
        simplify_tolerance=args.simplify,
        use_parquet=not args.no_parquet,
        n_jobs=args.jobs,
        simplify_graph=not args.no_simplify_graph,
        use_alpha_shape=not args.no_alpha_shape,
        alpha=args.alpha
    )
    
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    hours, minutes = divmod(minutes, 60)
    
    print(f"Total execution time: {int(hours):02d}:{int(minutes):02d}:{seconds:.2f}")
    
    if isinstance(result, list):
        print(f"Generated {len(result)} isochrone files in {args.output_dir}")
    else:
        print(f"Generated combined isochrone file: {result}") 