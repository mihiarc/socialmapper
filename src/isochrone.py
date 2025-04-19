#!/usr/bin/env python3
"""
Module to generate isochrones from Points of Interest (POIs).
"""
import os
import logging
import warnings
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point
from typing import Dict, Any, List, Tuple, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

def sanitize_name(name: str) -> str:
    """Sanitize a name to be filesystem-safe."""
    return (name.replace(" ", "_")
                .replace("'", "")
                .replace('"', '')
                .replace("/", "_"))

def create_isochrone_from_poi(
    poi: Dict[str, Any],
    travel_time_limit: int,
    output_dir: str = 'isochrones',
    save_file: bool = True
) -> Union[str, gpd.GeoDataFrame]:
    """
    Create an isochrone from a POI.
    
    Args:
        poi (Dict[str, Any]): POI dictionary containing at minimum 'lat', 'lon', and 'tags'
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save the isochrone file
        save_file (bool): Whether to save the isochrone to a file
        
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
    
    # Add speeds and travel times
    G = ox.add_edge_speeds(G)
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
    
    # Convert to WGS84 for standard GeoJSON output
    isochrone_gdf = isochrone_gdf.to_crs('EPSG:4326')
    
    # Add metadata
    isochrone_gdf['poi_id'] = poi.get('id', 'unknown')
    isochrone_gdf['poi_name'] = poi_name
    isochrone_gdf['travel_time_minutes'] = travel_time_limit
    
    if save_file:
        # Save result
        safe_name = sanitize_name(poi_name)
        safe_name = safe_name.lower()
        os.makedirs(output_dir, exist_ok=True)
        isochrone_file = os.path.join(
            output_dir,
            f'isochrone{travel_time_limit}_{safe_name}.geojson'
        )
        
        isochrone_gdf.to_file(isochrone_file, driver='GeoJSON')
        return isochrone_file
    
    return isochrone_gdf

def create_isochrones_from_poi_list(
    poi_data: Dict[str, List[Dict[str, Any]]],
    travel_time_limit: int,
    output_dir: str = 'isochrones',
    save_individual_files: bool = True,
    combine_results: bool = False
) -> Union[str, gpd.GeoDataFrame, List[str]]:
    """
    Create isochrones from a list of POIs.
    
    Args:
        poi_data (Dict[str, List[Dict]]): Dictionary with 'pois' key containing list of POIs
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save isochrone files
        save_individual_files (bool): Whether to save individual isochrone files
        combine_results (bool): Whether to combine all isochrones into a single file
        
    Returns:
        Union[str, gpd.GeoDataFrame, List[str]]:
            - Combined GeoJSON file path if combine_results=True and save_individual_files=True
            - Combined GeoDataFrame if combine_results=True and save_individual_files=False
            - List of file paths if save_individual_files=True and combine_results=False
    """
    pois = poi_data.get('pois', [])
    if not pois:
        raise ValueError("No POIs found in input data")
    
    isochrone_files = []
    isochrone_gdfs = []
    
    for poi in pois:
        try:
            result = create_isochrone_from_poi(
                poi=poi,
                travel_time_limit=travel_time_limit,
                output_dir=output_dir,
                save_file=save_individual_files
            )
            
            if save_individual_files:
                isochrone_files.append(result)
            else:
                isochrone_gdfs.append(result)
                
            logger.info(f"Created isochrone for POI: {poi.get('tags', {}).get('name', poi.get('id', 'unknown'))}")
        except Exception as e:
            logger.error(f"Error creating isochrone for POI {poi.get('id', 'unknown')}: {e}")
    
    if combine_results:
        if isochrone_gdfs or not save_individual_files:
            # If we have GeoDataFrames (or didn't save individual files), combine them
            combined_gdf = gpd.GeoDataFrame(pd.concat(isochrone_gdfs, ignore_index=True))
            
            if save_individual_files:
                # Save combined result
                combined_file = os.path.join(
                    output_dir,
                    f'combined_isochrones_{travel_time_limit}min.geojson'
                )
                combined_gdf.to_file(combined_file, driver='GeoJSON')
                return combined_file
            else:
                return combined_gdf
        else:
            # We need to load the individual files and combine them
            gdfs = [gpd.read_file(file) for file in isochrone_files]
            combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
            
            # Save combined result
            combined_file = os.path.join(
                output_dir,
                f'combined_isochrones_{travel_time_limit}min.geojson'
            )
            combined_gdf.to_file(combined_file, driver='GeoJSON')
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
    combine_results: bool = False
) -> Union[str, gpd.GeoDataFrame, List[str]]:
    """
    Create isochrones from a JSON file containing POIs.
    
    Args:
        json_file_path (str): Path to JSON file containing POIs
        travel_time_limit (int): Travel time limit in minutes
        output_dir (str): Directory to save isochrone files
        save_individual_files (bool): Whether to save individual isochrone files
        combine_results (bool): Whether to combine all isochrones into a single file
        
    Returns:
        Union[str, gpd.GeoDataFrame, List[str]]: See create_isochrones_from_poi_list
    """
    try:
        with open(json_file_path, 'r') as f:
            poi_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        raise
    
    return create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time_limit,
        output_dir=output_dir,
        save_individual_files=save_individual_files,
        combine_results=combine_results
    )

# Add missing import
import json
import pandas as pd

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate isochrones from POIs")
    parser.add_argument("json_file", help="JSON file containing POIs")
    parser.add_argument("--time", type=int, default=30, help="Travel time limit in minutes")
    parser.add_argument("--output-dir", default="isochrones", help="Output directory")
    parser.add_argument("--combine", action="store_true", help="Combine all isochrones into a single file")
    args = parser.parse_args()
    
    result = create_isochrones_from_json_file(
        json_file_path=args.json_file,
        travel_time_limit=args.time,
        output_dir=args.output_dir,
        combine_results=args.combine
    )
    
    if isinstance(result, list):
        print(f"Generated {len(result)} isochrone files in {args.output_dir}")
    else:
        print(f"Generated combined isochrone file: {result}") 