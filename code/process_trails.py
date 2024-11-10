import os
import geopandas as gpd
from shapely.geometry import Point

# filter trails in region 8, TERRA trail type, and GIS_MILES <= 5
REGION_CODE = '08'
MAX_TRAIL_LENGTH = 5

# load NF trails
file_path = '/Users/mihiarc/Work/data/'
shapefile = os.path.join(file_path, 'spatial-boundaries', 'nfs-layers', 'FS Hiking Trails', 'S_USA.TrailNFS_Publish.shp')
try:
    nfs_trails = gpd.read_file(shapefile)
except FileNotFoundError:
    print("Shapefile not found. Please check the file path.")
    raise

# select desired variables
nfs_trails_filtered = nfs_trails[['ADMIN_ORG',
                                  'TRAIL_CN', 'TRAIL_NAME', 'TRAIL_NO', 'TRAIL_TYPE',
                                  'BMP', 'EMP', 'SEGMENT_LE', 'GIS_MILES', 'SHAPE_LEN', 
                                  'geometry']].copy()

# create new columns for region, forest, and ranger district
# ADMIN_ORG format: '080101' where each code is two digits
nfs_trails_filtered['REGION'] = nfs_trails_filtered['ADMIN_ORG'].str[:2]
nfs_trails_filtered['FOREST'] = nfs_trails_filtered['ADMIN_ORG'].str[2:4]
nfs_trails_filtered['RANGER_DISTRICT'] = nfs_trails_filtered['ADMIN_ORG'].str[4:]

# Remove invalid geometries
nfs_trails_filtered = nfs_trails_filtered[nfs_trails_filtered.is_valid]

filtered_trails = nfs_trails_filtered[
    (nfs_trails_filtered['REGION'] == REGION_CODE) &
    (nfs_trails_filtered['TRAIL_TYPE'] == 'TERRA') &
    (nfs_trails_filtered['GIS_MILES'] <= MAX_TRAIL_LENGTH)
].copy()

# Drop rows with missing 'GIS_MILES' or 'TRAIL_NAME'
filtered_trails = filtered_trails.dropna(subset=['GIS_MILES', 'TRAIL_NAME'])

# Group by 'TRAIL_NAME' and get the index of the minimum 'GIS_MILES' for each group
min_gis_miles_idx = filtered_trails.groupby('TRAIL_NAME')['GIS_MILES'].idxmin()

# Use the indices to filter
filtered_trails = filtered_trails.loc[min_gis_miles_idx]

# drop if missing geometry
filtered_trails = filtered_trails.dropna(subset=['geometry'])

# Remove invalid geometries
filtered_trails = filtered_trails[filtered_trails.is_valid]

# Keep only LineString geometries
filtered_trails = filtered_trails[filtered_trails.geometry.type == 'LineString']

# Function to extract the starting point of a trail
def get_starting_point(geometry):
    try:
        if geometry.geom_type == 'LineString':
            return geometry.coords[0]
    except (AttributeError, IndexError, TypeError):
        pass
    return None

# Apply the function to create a new column with the starting point
filtered_trails['starting_point'] = filtered_trails['geometry'].apply(get_starting_point)

# Drop rows where starting_point is None
filtered_trails = filtered_trails.dropna(subset=['starting_point'])

# make a copy called 'trail_starts' and convert 'starting_point' to a Point object
trail_starts = filtered_trails.copy()
trail_starts['geometry'] = trail_starts['starting_point'].apply(Point)

# Drop the 'starting_point' column to avoid serialization issues
trail_starts = trail_starts.drop(columns=['starting_point'])

# Ensure the output directory exists
output_file = os.path.join(file_path, 
                           'spatial-boundaries', 
                           'nfs-layers', 
                           f'trail_heads_{REGION_CODE}.geojson')
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Save the filtered trails to a geojson file if not empty
if not trail_starts.empty:
    trail_starts.to_file(output_file, driver='GeoJSON')
    print(f"Filtered trails saved to {output_file}")
else:
    print("No trails meet the criteria. No file was saved.")