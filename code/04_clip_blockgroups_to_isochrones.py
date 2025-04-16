import geopandas as gpd
import pandas as pd
import os
import glob
from shapely.strtree import STRtree

# Load census block group boundaries
file_path = '/Users/mihiarc/Work/data/'
shapefile_path = os.path.join(file_path, 'spatial-boundaries/cb_2023_us_bg_500k/cb_2023_us_bg_500k.shp')
block_groups = gpd.read_file(shapefile_path)

# Ensure 'GEOID' is a string
block_groups['GEOID'] = block_groups['GEOID'].astype(str).str.zfill(12)

# Read in the population data for block groups
df = pd.read_csv('/Users/mihiarc/Work/repos/nfs-econ-research/tables/block_groups_population.csv')

# Ensure 'Block_Group_ID' is a string with leading zeros
df['Block_Group_ID'] = df['Block_Group_ID'].astype(str).str.zfill(12)

# Merge the population data with the block group geometries
block_groups = block_groups.merge(df, left_on='GEOID', right_on='Block_Group_ID', how='left')

# Check for missing values after merge
missing_values = block_groups.isnull().sum()
print("Missing values after merge:\n", missing_values)

# print non missing values
non_missing_values = block_groups.notnull().sum()
print("Non missing values after merge:\n", non_missing_values)

# Handle missing values if necessary (e.g., fill with 0 or drop)
# block_groups = block_groups.dropna(subset=['population'])

# Ensure geometries are valid
block_groups = block_groups[~block_groups.is_empty]
block_groups = block_groups[block_groups.is_valid]

# Set CRS to WGS84
block_groups = block_groups.to_crs(epsg=4326)

# Build a spatial index for block groups
block_groups_sindex = block_groups.sindex

# Initialize an empty list to store filtered block groups
filtered_block_groups = []

# Path to isochrone polygons
isochrone_folder = 'hiking_trails/isochrones'
isochrone_files = glob.glob(os.path.join(isochrone_folder, '*.geojson'))

# Loop over each isochrone polygon
for isochrone_file in isochrone_files:
    # Read the isochrone polygon
    isochrone = gpd.read_file(isochrone_file)

    # Ensure geometries are valid
    isochrone = isochrone[~isochrone.is_empty]
    isochrone = isochrone[isochrone.is_valid]

    # Ensure CRS matches
    if isochrone.crs != 'EPSG:4326':
        isochrone = isochrone.to_crs(epsg=4326)

    # Get the isochrone polygon geometry
    isochrone_polygon = isochrone.unary_union

    # Get the bounding box of the isochrone polygon
    bbox = isochrone_polygon.bounds  # (minx, miny, maxx, maxy)

    # Use the spatial index to find block groups that might intersect the isochrone polygon
    possible_matches_index = list(block_groups_sindex.intersection(bbox))
    possible_matches = block_groups.iloc[possible_matches_index]

    # Further filter block groups within the bounding box
    precise_matches = possible_matches[possible_matches.geometry.within(isochrone_polygon)]

    # Copy the result to avoid SettingWithCopyWarning
    block_groups_within = precise_matches.copy()

    # Get the hiking trail name from the file name (without extension)
    hiking_trail_name = os.path.splitext(os.path.basename(isochrone_file))[0]

    # Assign the hiking trail name to the filtered block groups
    block_groups_within['hiking_trail'] = hiking_trail_name

    # Append to the list
    filtered_block_groups.append(block_groups_within)

# Concatenate all filtered block groups
if filtered_block_groups:
    all_filtered_block_groups = pd.concat(filtered_block_groups, ignore_index=True)

    # Save the output for efficient reading and writing
    # Save as GeoPackage
    output_file = 'block_group_population_near_trails.gpkg'
    all_filtered_block_groups.to_file(output_file, driver='GPKG')
    print(f'Data saved to {output_file}')
else:
    print('No block groups found within any isochrone polygons.')