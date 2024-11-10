import geopandas as gpd
import pandas as pd
import os

STATE = '37'

# Load census block group boundaries
file_path = '/Users/mihiarc/Work/data/'
shapefile_path = os.path.join(file_path, 'spatial-boundaries/cb_2023_us_bg_500k/cb_2023_us_bg_500k.shp')
block_groups = gpd.read_file(shapefile_path)

# Ensure 'STATEFP' is a string
block_groups['STATEFP'] = block_groups['STATEFP'].astype(str)

# Filter block groups in North Carolina
block_groups = block_groups[block_groups['STATEFP'] == STATE]

# Read in the population data for North Carolina block groups
df = pd.read_csv('nc_block_groups_population.csv')

# Ensure 'GEOID' and 'Block_Group_ID' are strings with leading zeros
block_groups['GEOID'] = block_groups['GEOID'].astype(str)
df['Block_Group_ID'] = df['Block_Group_ID'].astype(str).str.zfill(12)

# Merge the population data with the block group geometries
block_groups = block_groups.merge(df, left_on='GEOID', right_on='Block_Group_ID', how='left')

# Check for missing values after merge
missing_values = block_groups.isnull().sum()
print("Missing values after merge:\n", missing_values)

# Handle missing values if necessary (e.g., fill with 0 or drop)
# block_groups = block_groups.dropna(subset=['population'])

# Ensure geometries are valid
block_groups = block_groups[~block_groups.is_empty]
block_groups = block_groups[block_groups.is_valid]

# Set CRS to WGS84
block_groups = block_groups.to_crs(epsg=4326)

# Save the merged data to a GeoJSON file
block_groups.to_file('nc_block_groups_population.geojson', driver='GeoJSON')
print('Data saved to nc_block_groups_population.geojson')