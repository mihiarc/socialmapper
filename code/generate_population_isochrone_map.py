import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import osmnx as ox
import networkx as nx
import contextily as ctx
from matplotlib.colors import BoundaryNorm
import numpy as np
from matplotlib.patches import Patch
from shapely.ops import transform
from pyproj import Transformer

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='osmnx')

# trail_name = 'LINVILLE FALLS'

# # Filter the trail_starts GeoDataFrame for the trail
# current_trail = trail_starts[trail_starts['TRAIL_NAME'] == trail_name]
# # set the crs for use in open street map
# current_trail.crs = 'EPSG:4326'

# starting_point = current_trail.iloc[0]['starting_point']

# # setup the trail head coordinates
# trail_head_coords = (starting_point[1], starting_point[0])

# G = ox.graph_from_point(trail_head_coords, network_type='drive', dist=dist)

# Define your travel time limit in minutes
travel_time_limit = 45
average_speed_mph = 60
average_speed_kmh = average_speed_mph * 1.60934  # Convert to km/h
average_speed_ms = average_speed_kmh * (1000 / 3600)  # Convert to m/s
dist = average_speed_ms * travel_time_limit * 60  # Calculate distance

file_path = '/Users/mihiarc/Work/data/'
# load the census data
nc_block_groups = gpd.read_file(file_path + 'census_blockgroup_data.geojson')
# load the trail heads GeoDataFrame
trail_heads = gpd.read_file('/Users/mihiarc/Work/repos/nfs-econ-research/hiking_trails/trail_heads_08.geojson')
# define trail head manually
trail_name = 'LINVILLE FALLS'

current_trail = trail_heads[trail_heads['TRAIL_NAME'] == trail_name]
current_trail.crs = 'EPSG:3857'

# starting point come from the trail heads GeoDataFrame
starting_point = current_trail.iloc[0]['geometry']
trail_head_coords = (starting_point[1], starting_point[0])
# starting_point = gpd.GeoSeries([Point(starting_point)], crs=current_trail.crs)

# Define the starting point for the isochrone




G = ox.graph_from_point(trail_head_coords, network_type='drive', dist=dist)

# Add edge speeds and travel times
ox.routing.add_edge_speeds(G)
ox.routing.add_edge_travel_times(G)

# Get the nearest node to the trail head location in the graph
trail_head_node = ox.nearest_nodes(
        G, X=starting_point.geometry.x.iloc[0], Y=starting_point.geometry.y.iloc[0]
    )

# Convert travel time limit to seconds
travel_time_limit_sec = travel_time_limit * 60

# Find nodes reachable within the travel time limit
subgraph = nx.ego_graph(
        G, trail_head_node, radius=travel_time_limit_sec, distance='travel_time'
    )

# Extract the geometries of the nodes in the subgraph
node_points = [
        Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)
    ]

# Create a GeoDataFrame of the nodes
nodes_gdf = gpd.GeoDataFrame(geometry=node_points, crs=G.graph['crs'])

# Create an isochrone polygon (convex hull)
isochrone = nodes_gdf.unary_union.convex_hull

# Convert the road network to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)

# Filter the edges that intersect with the isochrone polygon
roads_in_isochrone = edges[edges.intersects(isochrone)]
roads_in_isochrone = roads_in_isochrone.simplify(tolerance=10)

# Reproject nc_block_groups to EPSG:3857
nc_block_groups = nc_block_groups.to_crs(epsg=3857)

# Reproject isochrone to EPSG:3857
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
isochrone_proj = transform(transformer.transform, isochrone)

# Filter block groups within the isochrone polygon
block_groups_isochrone = nc_block_groups[nc_block_groups.within(isochrone_proj)]

# Create a GeoDataFrame with the isochrone polygon
isochrone_gdf = gpd.GeoDataFrame(geometry=[isochrone_proj], crs=nc_block_groups.crs)

# Plot the block groups and isochrone
fig, ax = plt.subplots(figsize=(10, 10))
block_groups_isochrone.boundary.plot(ax=ax, color='blue', label='Census Block Groups')
isochrone_gdf.boundary.plot(ax=ax, color='red', label='45-min Isochrone')

# Reproject the GeoDataFrame
block_groups_isochrone = block_groups_isochrone.to_crs(epsg=3857)

# Create the plot
fig, ax = plt.subplots(figsize=(10, 10))

# add markers for trail head and cities
# trail_head.plot(ax=ax, color='blue', markersize=50, edgecolor='red', linewidth=0.75, label='Linville Falls, NC')

# Plot the block groups, using population data for choropleth
cmap = 'cool'  # colormap
block_groups_isochrone.plot(
    column='Population',
    cmap=cmap,
    linewidth=0.5,
    edgecolor='white',
    legend=False,  # We'll add a custom legend
    alpha=0.7,     # Adjust transparency
    ax=ax
)

# Zoom out by adjusting the extent
xlim = ax.get_xlim()
ylim = ax.get_ylim()
x_margin = (xlim[1] - xlim[0]) * 0.2  # 20% margin
y_margin = (ylim[1] - ylim[0]) * 0.2  # 20% margin
ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)

# Create a union of the block group geometries
trail_union = block_groups_isochrone.unary_union

# Create a custom legend
min_pop = block_groups_isochrone['Population'].min()
max_pop = block_groups_isochrone['Population'].max()
bins = np.linspace(min_pop, max_pop, 5)
bins = np.round(bins, -2)  # Round to nearest hundred for cleaner labels
labels = [f'{int(bins[i]):,} - {int(bins[i+1]):,}' for i in range(len(bins)-1)]

# Create a colormap and normalization
norm = BoundaryNorm(bins, plt.get_cmap(cmap).N)

# Create legend patches
legend_handles = [
    Patch(
        facecolor=plt.get_cmap(cmap)(norm(bins[i])),
        edgecolor='white',
        label=labels[i]
    ) for i in range(len(labels))
]

# Add the legend below the map
ax.legend(
    handles=legend_handles,
    loc='lower center',
    ncol=len(labels) + 1,
    title='Census Block Group Population',
    framealpha=1,
    fontsize='medium',
    title_fontsize='large'
)

# Add a title on the map
ax.text(
    0.5, 0.95,  # Coordinates in axis fraction (0.5 is center, 0.95 is near the top)
    'Population within 45 Minutes of \nLinville Falls Trail',  # Title text
    fontsize=22,
    color='darkblue',
    ha='center',  # Horizontal alignment
    va='top',  # Vertical alignment
    bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.5'),  # Optional: Add background
    transform=ax.transAxes  # Use axis fraction for positioning
)

ax.set_axis_off()

# Add basemap
ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik,
    crs=block_groups_isochrone.crs.to_string()
)

# Display the plot
plt.show()