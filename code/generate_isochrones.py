import os
import warnings
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point

# Suppress the FutureWarning for now (optional)
warnings.filterwarnings("ignore", category=FutureWarning)

travel_time_limit = 30  # in minutes

# Define a list of trail names
trail_names = ["EAST FORK TRAIL", 
               "FALLS BRANCH TRAIL", 
               "HICKORY BRANCH",
               "CORNELIUS CREEK",
               "DOUBLE ARCH",
               "LITTLE GREEN",
               "CEDAR POINT TIDELANDS NRT",
               "LOOKING GLASS ROCK",
               "MOUNT YONAH"]

# Load NF trail heads
geofile = os.path.join('hiking-trails', 'trail_heads_08.geojson')
try:
    nfs_trails = gpd.read_file(geofile)
except FileNotFoundError:
    print("File not found. Please check the file path.")
    raise

# Ensure the GeoDataFrame is in EPSG:4326 (WGS84)
nfs_trails = nfs_trails.to_crs(epsg=4326)

for trail_name in trail_names:
    # Filter the trail_starts GeoDataFrame for the trail
    current_trail = nfs_trails[nfs_trails['TRAIL_NAME'] == trail_name]

    # Check if the trail exists
    if current_trail.empty:
        print(f"Trail '{trail_name}' not found in the dataset.")
        continue  # Skip to the next trail

    # Get the first point geometry
    trail_head_point = current_trail.geometry.iloc[0]

    # Extract latitude and longitude
    latitude = trail_head_point.y
    longitude = trail_head_point.x

    # Print trail name and starting point
    print(trail_name)
    print(f"Latitude: {latitude}, Longitude: {longitude}")

    # Download the road network around the trail head location
    # Note: OSMnx expects (lat, lon) for the point
    G = ox.graph_from_point((latitude, longitude), network_type='drive', dist=travel_time_limit * 1000)

    # Add edge speeds and travel times
    ox.add_edge_speeds(G)
    ox.add_edge_travel_times(G)

    # Project the graph to UTM (for accurate distance calculations)
    G = ox.project_graph(G)

    # Project the trail head point to match the graph's CRS
    trail_head_geom = gpd.GeoSeries([trail_head_point], crs='EPSG:4326').to_crs(G.graph['crs'])
    trail_head_proj = trail_head_geom.geometry.iloc[0]

    # Get the nearest node to the trail head location in the graph
    trail_head_node = ox.nearest_nodes(
        G, X=trail_head_proj.x, Y=trail_head_proj.y
    )

    # Convert travel time limit to seconds
    travel_time_limit_sec = travel_time_limit * 60

    # Find nodes reachable within the travel time limit
    subgraph = nx.ego_graph(
        G, trail_head_node, radius=travel_time_limit_sec, distance='travel_time'
    )

    # Extract the geometries of the nodes in the subgraph
    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]

    # Create a GeoDataFrame of the nodes
    nodes_gdf = gpd.GeoDataFrame(geometry=node_points, crs=G.graph['crs'])

    # Create an isochrone polygon (convex hull)
    isochrone = nodes_gdf.unary_union.convex_hull

    # Sanitize trail_name to create a valid filename
    safe_trail_name = trail_name.replace(" ", "_").replace("'", "").replace('"', '').replace("/", "_")

    # Save the isochrone to a new file
    isochrone_file = os.path.join('hiking-trails', 
                                  'isochrones', 
                                  f'isochrone_{safe_trail_name}.geojson')
    isochrone_gdf = gpd.GeoDataFrame(geometry=[isochrone], crs=G.graph['crs'])
    isochrone_gdf.to_file(isochrone_file, driver='GeoJSON')
    print(f"Isochrone saved to {isochrone_file}")