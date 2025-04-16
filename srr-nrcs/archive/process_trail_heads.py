import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString

import os

# Set the project root directory
file_path = '/Users/mihiarc/Work/data/'

# load national forest boundaries
forest_boundary = gpd.read_file(
    file_path + 'spatial-boundaries/nfs-layers/FS Admin Boundaries/S_USA.AdministrativeForest.shp')

# select only Region 8
forest_boundary_region_8 = forest_boundary[forest_boundary['REGION'] == '08']

# drop El Yunque National Forest, PR
forest_boundary_region_8 = forest_boundary_region_8[
    forest_boundary_region_8['FORESTNAME'] != 'El Yunque National Forest']

# load NF trails
shapefile = os.path.join(file_path, 'spatial-boundaries', 'nfs-layers', 'FS Hiking Trails', 'S_USA.TrailNFS_Publish.shp')
try:
    nfs_trails = gpd.read_file(shapefile)
except FileNotFoundError:
    print("Shapefile not found. Please check the file path.")
    raise

# # clip to the region 8 boundary
nfs_trails = gpd.clip(nfs_trails, forest_boundary_region_8)

# select desired variables
nfs_trails_filtered = nfs_trails[['ADMIN_ORG', 'TRAIL_CN', 'TRAIL_NAME', 'TRAIL_NO', 'TRAIL_TYPE',
                         'BMP', 'EMP', 'SEGMENT_LE', 'GIS_MILES', 'SHAPE_LEN', 'geometry']].copy()

# create new columns for region, forest, and ranger district
# ADMIN_ORG format: '080101' where each code is two digits
nfs_trails_filtered['REGION'] = nfs_trails_filtered['ADMIN_ORG'].str[:2]
nfs_trails_filtered['FOREST'] = nfs_trails_filtered['ADMIN_ORG'].str[2:4]
nfs_trails_filtered['RANGER_DISTRICT'] = nfs_trails_filtered['ADMIN_ORG'].str[4:]

# filter trails in region 8, TERRA trail type, and GIS_MILES <= 5
REGION_CODE = '08'
MAX_TRAIL_LENGTH = 5

filtered_trails = nfs_trails_filtered[
    (nfs_trails_filtered['REGION'] == REGION_CODE) &
    (nfs_trails_filtered['TRAIL_TYPE'] == 'TERRA') &
    (nfs_trails_filtered['GIS_MILES'] <= MAX_TRAIL_LENGTH)
].copy()

# Group by 'TRAIL_NAME' and get the index of the minimum 'GIS_MILES' for each group
min_gis_miles_idx = filtered_trails.groupby('TRAIL_NAME')['GIS_MILES'].idxmin()

# Use the indices to filter
filtered_trails = filtered_trails.loc[min_gis_miles_idx]

# drop if missing geometry
filtered_trails = filtered_trails.dropna(subset=['geometry'])

# keep only singe line geometries
filtered_trails = filtered_trails[filtered_trails['geometry'].apply(lambda x: isinstance(x, LineString))]

# Convert to projected CRS before extracting coordinates
filtered_trails = filtered_trails.to_crs(epsg=3857)

# Function to extract the starting point of a trail
def get_starting_point(geometry):
    """
    Extracts the starting point of a LineString geometry.

    Parameters:
        geometry (shapely.geometry.LineString): The geometry from which to extract the starting point.

    Returns:
        tuple: The coordinates of the starting point, or None if the geometry is not a LineString.
    """
    if isinstance(geometry, LineString):
        return geometry.coords[0]
    else:
        return None

# Apply the function to create a new column with the starting point
filtered_trails['starting_point'] = filtered_trails['geometry'].apply(get_starting_point)

# Make a copy called 'trail_starts'
trail_starts = filtered_trails.copy()
# Drop rows where 'starting_point' is None
trail_starts['starting_point'] = trail_starts['starting_point'].apply(lambda x: Point(x) if x else None)
trail_starts = trail_starts.dropna(subset=['starting_point'])

# drop the 'geometry' column
trail_starts = trail_starts.drop(columns='geometry')

# Set 'starting_point' as the active geometry column
trail_starts = gpd.GeoDataFrame(trail_starts, geometry='starting_point', crs=filtered_trails.crs)

# rename starting_point to geometry
trail_starts = trail_starts.rename(columns={'starting_point': 'geometry'})

# drop duplicates based on starting point
trail_starts = trail_starts.drop_duplicates(subset=['geometry'])

# Save the GeoDataFrame to GeoJSON
output_file = os.path.join(file_path, 'trail_starts.geojson')
trail_starts.to_file(output_file, driver='GeoJSON')

# Confirm the file was saved
if os.path.exists(output_file):
    print(f"File saved successfully at {output_file}")
else:
    print("Failed to save the GeoJSON file.")