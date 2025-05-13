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
# Import the new progress bar utility
from socialmapper.progress import get_progress_bar
import time
import logging

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
    
    # Download and prepare road network
    try:
        G = ox.graph_from_point(
            (latitude, longitude),
            network_type='drive',
            dist=travel_time_limit * 1000  # Convert minutes to meters for initial area
        )
    except Exception as e:
        logger.error(f"Error downloading road network: {e}")
        raise
    
    # Add speeds and travel times with fallback values
    G = ox.add_edge_speeds(G, fallback=50)  # 50 km/h as default fallback speed which is 31 mph
    G = ox.add_edge_travel_times(G)
    G = ox.project_graph(G)
    
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
    
    # Use convex hull to create the isochrone polygon
    isochrone = nodes_gdf.unary_union.convex_hull
    
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

def create_isochrones_from_poi_list(
    poi_data: Dict[str, List[Dict[str, Any]]],
    travel_time_limit: int,
    output_dir: str = 'output/isochrones',
    save_individual_files: bool = True,
    combine_results: bool = False,
    simplify_tolerance: Optional[float] = None,
    use_parquet: bool = True
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
        
    Returns:
        Union[str, gpd.GeoDataFrame, List[str]]:
            - Combined file path if combine_results=True and save_individual_files=True
            - Combined GeoDataFrame if combine_results=True and save_individual_files=False
            - List of file paths if save_individual_files=True and combine_results=False
    """
    pois = poi_data.get('pois', [])
    if not pois:
        raise ValueError("No POIs found in input data. Please try different search parameters or a different location. POIs like 'natural=forest' may not exist in all areas.")
    
    isochrone_files = []
    isochrone_gdfs = []
    
    # Use the new progress bar utility
    for poi in get_progress_bar(pois, desc="Downloading Road Networks", unit="POI"):
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
    
    if combine_results:
        if isochrone_gdfs or not save_individual_files:
            # If we have GeoDataFrames (or didn't save individual files), combine them
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
    use_parquet: bool = True
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
        use_parquet=use_parquet
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