import folium
import geopandas as gpd

# Load trail head isochrone
isochrone_path = '/Users/mihiarc/Work/isochrone_ROBBINS BRANCH.geojson'
block_groups_path = '/Users/mihiarc/Work/nc_block_groups_population.geojson'

# Load isochrone data
isochrone = gpd.read_file(isochrone_path)

# Load block group population data
block_groups = gpd.read_file(block_groups_path)

# Ensure both GeoDataFrames have the same CRS
if block_groups.crs != isochrone.crs:
    block_groups = block_groups.to_crs(isochrone.crs)

# Perform spatial join to get block groups within the isochrone
block_groups_within_isochrone = gpd.sjoin(
    block_groups,
    isochrone,
    how='inner',
    predicate='intersects'  # Use 'predicate' instead of deprecated 'op'
)

# check that the join was successful
print(block_groups_within_isochrone.head())

# create a folium map centered on north carolina
map_center = [35.5, -80.0]

# Create a folium map centered on the average coordinates
# map_center = [
#     block_groups_within_isochrone.geometry.centroid.y.mean(),
#     block_groups_within_isochrone.geometry.centroid.x.mean()
# ]
m = folium.Map(location=map_center, zoom_start=9)

# Add the block groups to the map with a choropleth layer
folium.Choropleth(
    geo_data=block_groups_within_isochrone,
    name='choropleth',
    data=block_groups_within_isochrone,
    columns=['GEOID', 'Population'],
    key_on='feature.properties.GEOID',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Population'
).add_to(m)

# Add a layer control panel to the map
folium.LayerControl().add_to(m)

# Save the map to an HTML file
m.save('block_groups_population_map.html')