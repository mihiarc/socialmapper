import folium
import geopandas as gpd
import os

def characterize_population_within_isochrone(
    isochrone_path,
    block_groups_path,
    output_map_path='block_groups_population_map.html',
    map_center=None,
    zoom_start=9
):
    """
    Characterizes the population within a given isochrone by performing a spatial join
    with block group population data and visualizing the result on a map.

    Parameters:
    - isochrone_path (str): Path to the isochrone GeoJSON file.
    - block_groups_path (str): Path to the block groups population GeoJSON file.
    - output_map_path (str): Path where the output HTML map will be saved.
    - map_center (list or tuple): Latitude and longitude to center the map. If None, centers on data.
    - zoom_start (int): Initial zoom level for the map.

    Returns:
    - block_groups_within_isochrone (GeoDataFrame): The result of the spatial join.
    """

    # Load isochrone data
    isochrone = gpd.read_file(isochrone_path)
    print(f"Loaded isochrone data from {isochrone_path}")

    # Load block group population data
    block_groups = gpd.read_file(block_groups_path)
    print(f"Loaded block groups data from {block_groups_path}")

    # Ensure both GeoDataFrames have the same CRS
    if block_groups.crs != isochrone.crs:
        block_groups = block_groups.to_crs(isochrone.crs)
        print("Converted block groups CRS to match isochrone CRS")

    # Perform spatial join to get block groups within the isochrone
    block_groups_within_isochrone = gpd.sjoin(
        block_groups,
        isochrone,
        how='inner',
        predicate='intersects'
    )
    print("Performed spatial join to find block groups within isochrone")

    # Check that the join was successful
    if block_groups_within_isochrone.empty:
        print("No block groups found within the isochrone.")
        return None

    print(block_groups_within_isochrone.head())

    # Determine map center if not provided
    if map_center is None:
        centroid = block_groups_within_isochrone.unary_union.centroid
        map_center = [centroid.y, centroid.x]
        print(f"Map center determined from data: {map_center}")

    # Create a folium map
    m = folium.Map(location=map_center, zoom_start=zoom_start)
    print("Created folium map")

    # Add the block groups to the map with a choropleth layer
    folium.Choropleth(
        geo_data=block_groups_within_isochrone,
        name='Choropleth',
        data=block_groups_within_isochrone,
        columns=['GEOID', 'Population'],
        key_on='feature.properties.GEOID',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Population within Isochrone'
    ).add_to(m)
    print("Added choropleth layer to map")

    # Add layer control and save the map
    folium.LayerControl().add_to(m)
    m.save(output_map_path)
    print(f"Map saved to {output_map_path}")

    return block_groups_within_isochrone

# Paths to your data
isochrone_folder = '/Users/mihiarc/Work/repos/nfs-econ-research/hiking_trails/'
block_groups_path = '/Users/mihiarc/Work/repos/nfs-econ-research/data/nc_block_groups_population.geojson'
output_map_path = '/Users/mihiarc/Work/repos/nfs-econ-research/maps/block_groups_population_map.html'

# Get all GeoJSON files in the isochrone folder
isochrone_paths = [os.path.join(isochrone_folder, f) for f in os.listdir(isochrone_folder) if f.endswith('.geojson')]

if not isochrone_paths:
    raise ValueError(f"No GeoJSON files found in {isochrone_folder}")

# Process the first isochrone as an example
block_groups_within_isochrone = characterize_population_within_isochrone(
    isochrone_path=isochrone_paths[0],
    block_groups_path=block_groups_path,
    output_map_path=output_map_path
)