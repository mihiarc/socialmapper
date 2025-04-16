import os
import warnings
import logging

logging.basicConfig(level=logging.ERROR)
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point
from typing import Union, List, Tuple

# Suppress the FutureWarning for now (optional)
warnings.filterwarnings("ignore", category=FutureWarning)

def sanitize_name(name: str) -> str:
    """Sanitize a name to be filesystem-safe."""
    return (name.replace(" ", "_")
                .replace("'", "")
                .replace('"', '')
                .replace("/", "_"))

def create_isochrone_for_trail(
    trail_name: str,
    geofile: gpd.GeoDataFrame,
    travel_time_limit: int,
    output_dir: str = 'hiking-trails/isochrones'
) -> str:
    """
    Process a single trail and create its isochrone.

    Args:
        trail_name (str): The name of the trail to process.
        nfs_trails (gpd.GeoDataFrame): GeoDataFrame containing trail data.
        travel_time_limit (int): Travel time limit in minutes.
        output_dir (str): Directory to save the isochrone file.

    Returns:
        str: The file path of the created isochrone GeoJSON file.
    """

    # First load the GeoJSON file into a GeoDataFrame
    gdf = gpd.read_file(geofile)
    
    # Filter for the trail
    current_trail = gdf[gdf['TRAIL_NAME'] == trail_name]

    if current_trail.empty:
        raise ValueError(f"Trail '{trail_name}' not found in the dataset. Try using function create_isochrone_from_coords() instead.")

    # Get trail head coordinates
    trail_head_point = current_trail.geometry.iloc[0]
    latitude, longitude = trail_head_point.y, trail_head_point.x

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

    # Project trail head to match graph CRS
    trail_head_geom = gpd.GeoSeries(
        [trail_head_point],
        crs='EPSG:4326'
    ).to_crs(G.graph['crs'])
    trail_head_proj = trail_head_geom.geometry.iloc[0]

    # Find nearest node and reachable area
    trail_head_node = ox.nearest_nodes(
        G,
        X=trail_head_proj.x,
        Y=trail_head_proj.y
    )

    subgraph = nx.ego_graph(
        G,
        trail_head_node,
        radius=travel_time_limit * 60,
        distance='travel_time'
    )

    # Create isochrone
    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
    nodes_gdf = gpd.GeoDataFrame(geometry=node_points, crs=G.graph['crs'])
    isochrone = nodes_gdf.unary_union.convex_hull

    # Save result
    safe_trail_name = sanitize_name(trail_name)
    safe_trail_name = safe_trail_name.lower()
    os.makedirs(output_dir, exist_ok=True)
    isochrone_file = os.path.join(
        output_dir,
        f'isochrone{travel_time_limit}_{safe_trail_name}.geojson'
    )

    isochrone_gdf = gpd.GeoDataFrame(
        geometry=[isochrone],
        crs=G.graph['crs']
    )
    isochrone_gdf.to_file(isochrone_file, driver='GeoJSON')

    return isochrone_file

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
    trail_head_point = Point(longitude, latitude)
    trail_head_geom = gpd.GeoSeries(
        [trail_head_point],
        crs='EPSG:4326'
    ).to_crs(G.graph['crs'])
    trail_head_proj = trail_head_geom.geometry.iloc[0]

    # Find nearest node and reachable area
    trail_head_node = ox.nearest_nodes(
        G,
        X=trail_head_proj.x,
        Y=trail_head_proj.y
    )

    subgraph = nx.ego_graph(
        G,
        trail_head_node,
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


# Example: Create isochrone from coordinates
# isochrone_file = create_isochrone_from_coords(
#     coords=(34.981, -83.262),
#     name='Holcomb Creek Falls',
#     travel_time_limit=60
# )

# Example: Create isochrone for a specific trail
# isochrone_file = create_isochrone_for_trail(
#     trail_name='LINVILLE FALLS',
#     geofile='hiking-trails/trail_heads_08.geojson',
#     travel_time_limit=30
# )

isochrone_file = create_isochrone_for_trail(
    trail_name='LINVILLE FALLS',
    geofile='hiking_trails/trail_heads_08.geojson',
    travel_time_limit=45
)

# isochrone_file = create_isochrone_for_trail(
#     trail_name='LINVILLE FALLS',
#     geofile='hiking-trails/trail_heads_08.geojson',
#     travel_time_limit=60
# )

# isochrone_file = create_isochrone_for_trail(
#     trail_name='FALLS BRANCH TRAIL',
#     geofile='hiking-trails/trail_heads_08.geojson',
#     travel_time_limit=30
# )

# isochrone_file = create_isochrone_for_trail(
#     trail_name='FALLS BRANCH TRAIL',
#     geofile='hiking-trails/trail_heads_08.geojson',
#     travel_time_limit=45
# )
# isochrone_file = create_isochrone_for_trail(
#     trail_name='FALLS BRANCH TRAIL',
#     geofile='hiking-trails/trail_heads_08.geojson',
#     travel_time_limit=60
# )