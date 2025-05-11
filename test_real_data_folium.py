#!/usr/bin/env python3
"""
Test script to generate folium maps using real socialmapper output data.
This is useful for testing the visualization functionality with actual data.
"""
import os
import geopandas as gpd
from socialmapper.visualization import (
    generate_folium_map,
    generate_folium_isochrone_map
)

# Path to existing output files from a previous socialmapper run
CENSUS_DATA_PATH = "output/custom_trail_heads_test_15min_census_data.geojson"
ISOCHRONES_PATH = "output/custom_trail_heads_test_15min_isochrones.geojson"

# Create a directory for test outputs
os.makedirs("output/folium_test", exist_ok=True)

# Load the data
print("Loading real data from previous socialmapper run...")
census_data = gpd.read_file(CENSUS_DATA_PATH)
isochrones = gpd.read_file(ISOCHRONES_PATH)

# Extract POIs from isochrones data
print(f"Loaded {len(census_data)} census block groups and {len(isochrones)} isochrones")

# Create POI data from the isochrones
poi_list = []
for idx, row in isochrones.iterrows():
    # Use the centroid of each isochrone as the POI location
    centroid = row.geometry.centroid
    
    poi_list.append({
        "name": row['poi_name'],
        "id": str(row['poi_id']),
        "geometry": centroid
    })

# Convert to GeoDataFrame
poi_gdf = gpd.GeoDataFrame(poi_list, crs=isochrones.crs)
print(f"Created {len(poi_gdf)} POI points from isochrones")

# Generate a folium map showing total population
print("Generating population map...")
pop_map = generate_folium_map(
    census_data_path=census_data,
    variable="B01003_001E",  # Total population
    isochrone_path=isochrones,
    poi_df=poi_gdf,
    title="Total Population by Block Group with Isochrones",
    height=700,
    width=1000,
    show_legend=True,
    base_map="OpenStreetMap"
)

# Save the map to an HTML file
output_pop_file = "output/folium_test/real_data_population_map.html"
pop_map.save(output_pop_file)
print(f"Population map saved to {output_pop_file}")

# Generate a map with median household income
print("Generating income map...")
income_map = generate_folium_map(
    census_data_path=census_data,
    variable="B19013_001E",  # Median household income
    isochrone_path=isochrones,
    poi_df=poi_gdf,
    title="Median Household Income by Block Group with Isochrones",
    height=700,
    width=1000,
    show_legend=True,
    base_map="CartoDB positron"
)

# Save the map to an HTML file
output_income_file = "output/folium_test/real_data_income_map.html"
income_map.save(output_income_file)
print(f"Income map saved to {output_income_file}")

# Generate an isochrone-only map
print("Generating isochrone-only map...")
isochrone_map = generate_folium_isochrone_map(
    isochrone_path=isochrones,
    poi_df=poi_gdf,
    title="Trail Heads with 15-Minute Travel Time Isochrones",
    height=700,
    width=1000,
    base_map="OpenStreetMap"
)

# Save the isochrone map to an HTML file
output_isochrone_file = "output/folium_test/real_data_isochrone_map.html"
isochrone_map.save(output_isochrone_file)
print(f"Isochrone map saved to {output_isochrone_file}")

print("\nAll maps generated successfully. Open the HTML files in your web browser to view them.")
print(f"1. Population Map: {output_pop_file}")
print(f"2. Income Map: {output_income_file}")
print(f"3. Isochrone Map: {output_isochrone_file}") 