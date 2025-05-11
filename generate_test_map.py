#!/usr/bin/env python3
"""
Generate a test folium map for visual inspection.
"""
import os
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point
from socialmapper.visualization import generate_folium_map

# Create a directory for test outputs
os.makedirs("output/test", exist_ok=True)

# Generate sample block group data
# Create a grid of polygons
def create_sample_blockgroups(n_rows=5, n_cols=5):
    gdf_blocks = []
    for i in range(n_rows):
        for j in range(n_cols):
            # Create a square polygon
            x0, y0 = j * 0.01, i * 0.01
            x1, y1 = (j + 1) * 0.01, (i + 1) * 0.01
            
            # Create polygon
            poly = Polygon([
                (x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)
            ])
            
            # Create a unique GEOID
            geoid = f"15000US42{i:02d}{j:02d}0000"
            
            # Add to list - Adding both the human-readable name and the Census API variable name
            gdf_blocks.append({
                "GEOID": geoid,
                "geometry": poly,
                "total_population": np.random.randint(100, 2000),
                "B01003_001E": np.random.randint(100, 2000),  # Same as total_population
                "median_household_income": np.random.randint(25000, 150000),
                "B19013_001E": np.random.randint(25000, 150000),  # Same as median_household_income
                "housing_units": np.random.randint(50, 1000),
                "B25001_001E": np.random.randint(50, 1000)  # Same as housing_units
            })
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(gdf_blocks, crs="EPSG:4326")
    return gdf

# Create sample isochrone data
def create_sample_isochrones(center_point):
    isochrones = []
    
    # Create circular buffers
    for i, radius in enumerate([0.01, 0.02, 0.03]):
        # Create circle
        buffer = center_point.buffer(radius)
        
        # Add to list
        isochrones.append({
            "travel_time_minutes": (i+1) * 5,
            "geometry": buffer
        })
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(isochrones, crs="EPSG:4326")
    return gdf

# Create sample POI data
def create_sample_pois(center_point):
    pois = [{
        "name": "Sample POI",
        "id": "sample_poi_1",
        "type": "library",
        "geometry": center_point
    }]
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(pois, crs="EPSG:4326")
    return gdf

# Generate sample data
center_lon, center_lat = -74.0060, 40.7128  # NYC coordinates
center_point = Point(center_lon, center_lat)

# Create sample datasets
block_groups = create_sample_blockgroups()
isochrones = create_sample_isochrones(center_point)
pois = create_sample_pois(center_point)

# Generate a folium map using total_population
map_obj = generate_folium_map(
    census_data_path=block_groups,
    variable="total_population",  # Use the variable name directly
    isochrone_path=isochrones,
    poi_df=pois,
    title="Sample Test Map - Total Population",
    height=600,
    width=800,
    show_legend=True,
    base_map="OpenStreetMap"
)

# Save the map to an HTML file
output_file = "output/test/sample_folium_map.html"
map_obj.save(output_file)

print(f"Folium map generated and saved to {output_file}")

# Generate a second map with different variable
map_obj2 = generate_folium_map(
    census_data_path=block_groups,
    variable="median_household_income",  # Use the variable name directly
    isochrone_path=isochrones,
    poi_df=pois,
    title="Sample Test Map - Median Household Income",
    height=600,
    width=800,
    show_legend=True,
    base_map="CartoDB positron"  # Different basemap
)

# Save the second map to an HTML file
output_file2 = "output/test/sample_folium_map_income.html"
map_obj2.save(output_file2)

print(f"Second folium map generated and saved to {output_file2}")

# Generate an isochrone-only map
from socialmapper.visualization import generate_folium_isochrone_map

map_obj3 = generate_folium_isochrone_map(
    isochrone_path=isochrones,
    poi_df=pois,
    title="Sample Isochrone Map",
    height=600,
    width=800,
    base_map="OpenStreetMap"
)

# Save the isochrone map to an HTML file
output_file3 = "output/test/sample_isochrone_map.html"
map_obj3.save(output_file3)

print(f"Isochrone map generated and saved to {output_file3}")

print("\nAll maps generated successfully. Open the HTML files in your web browser to view them.") 