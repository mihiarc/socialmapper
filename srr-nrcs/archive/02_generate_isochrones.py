import os
import warnings
import logging
import yaml

logging.basicConfig(level=logging.ERROR)
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point
from typing import Union, List, Tuple

# Suppress the FutureWarning for now (optional)
warnings.filterwarnings("ignore", category=FutureWarning)

def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def sanitize_name(name: str) -> str:
    """Sanitize a name to be filesystem-safe."""
    return (name.replace(" ", "_")
                .replace("'", "")
                .replace('"', '')
                .replace("/", "_"))

def create_isochrone_from_coords(
    coords: Tuple[float, float],
    name: str,
    travel_time_limit: int,
    output_dir: str = 'hiking-trails/isochrones'
) -> str:
    """Create isochrone from latitude/longitude coordinates."""
    latitude, longitude = coords

    # Download and prepare road network
    G = ox.graph_from_point(
        (latitude, longitude),
        network_type='drive',
        dist=travel_time_limit * 1000
    )

    # Add speeds and times
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

    subgraph = nx.ego_graph(
        G,
        poi_node,
        radius=travel_time_limit * 60,
        distance='travel_time'
    )

    # Create isochrone
    node_points = [Point((data['x'], data['y']))
                   for node, data in subgraph.nodes(data=True)]
    nodes_gdf = gpd.GeoDataFrame(geometry=node_points, crs=G.graph['crs'])
    isochrone = nodes_gdf.unary_union.convex_hull

    # Save result
    safe_name = sanitize_name(name)
    safe_name = safe_name.lower()
    os.makedirs(output_dir, exist_ok=True)
    isochrone_file = os.path.join(
        output_dir,
        f'isochrone{travel_time_limit}_{safe_name}.geojson'
    )

    isochrone_gdf = gpd.GeoDataFrame(
        geometry=[isochrone],
        crs=G.graph['crs']
    )
    isochrone_gdf.to_file(isochrone_file, driver='GeoJSON')

    return isochrone_file

def main():
    # Load configuration
    config = load_config()
    
    # Get point of interest details
    poi = config['point_of_interest']
    coords = (poi['latitude'], poi['longitude'])
    name = poi['name']
    
    # Get isochrone settings
    settings = config['isochrone_settings']
    output_dir = settings['output_dir']
    
    # Generate isochrones for each time limit
    for time_limit in settings['travel_time_limits']:
        isochrone_file = create_isochrone_from_coords(
            coords=coords,
            name=name,
            travel_time_limit=time_limit,
            output_dir=output_dir
        )
        print(f"Created {time_limit}-minute isochrone: {isochrone_file}")

if __name__ == "__main__":
    main()