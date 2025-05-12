#!/usr/bin/env python3
"""
Test script to debug POI coordinate extraction issue
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import json
import os

# Create a directory for test output if it doesn't exist
os.makedirs("test_output", exist_ok=True)

def debug_poi_data():
    """
    Debug function to examine POI data format and how coordinates are stored
    """
    # Sample block group for testing
    block_group = gpd.GeoDataFrame(
        {
            "GEOID": ["212219703012"],
            "geometry": [Point(-84.5, 38.2).buffer(0.1)]
        }, 
        crs="EPSG:4326"
    )
    
    # Create a test POI with coordinates
    poi_with_direct_coords = {
        "id": "test1",
        "name": "Test POI 1",
        "lon": -84.45,
        "lat": 38.25,
        "travel_time_minutes": 15
    }
    
    # Create a test POI with geometry
    poi_with_geometry = {
        "id": "test2",
        "name": "Test POI 2",
        "geometry": Point(-84.48, 38.22),
        "travel_time_minutes": 15
    }
    
    # Create a test POI with coordinates array
    poi_with_coords_array = {
        "id": "test3",
        "name": "Test POI 3",
        "coordinates": [-84.47, 38.23],
        "travel_time_minutes": 15
    }
    
    # Create a POI structure similar to what might be causing the issue
    poi_problematic = {
        "id": "test4",
        "name": "Test POI 4",
        # No direct coordinate fields
        "properties": {
            "lon": -84.46,
            "lat": 38.24
        },
        "travel_time_minutes": 15
    }
    
    # Test and report on each POI type
    test_poi_extraction([poi_with_direct_coords], "direct_coords")
    test_poi_extraction([poi_with_geometry], "geometry")
    test_poi_extraction([poi_with_coords_array], "coords_array")
    test_poi_extraction([poi_problematic], "problematic")
    
    # Test potential fix for problematic POIs
    fixed_pois = fix_poi_coordinates([poi_problematic])
    test_poi_extraction(fixed_pois, "fixed")

def test_poi_extraction(pois, label):
    """
    Test extraction of POI coordinates from different formats
    """
    print(f"\n--- Testing {label} POI format ---")
    poi_points = []
    
    print(f"POI example: {json.dumps(pois[0], default=str)}")
    
    for poi in pois:
        if 'lon' in poi and 'lat' in poi:
            poi_points.append(Point(poi['lon'], poi['lat']))
            print(f"Found direct lon/lat: {poi['lon']}, {poi['lat']}")
        elif 'geometry' in poi and hasattr(poi['geometry'], 'x') and hasattr(poi['geometry'], 'y'):
            poi_points.append(Point(poi['geometry'].x, poi['geometry'].y))
            print(f"Found geometry: {poi['geometry'].x}, {poi['geometry'].y}")
        elif 'coordinates' in poi:
            coords = poi['coordinates']
            if isinstance(coords, list) and len(coords) >= 2:
                poi_points.append(Point(coords[0], coords[1]))
                print(f"Found coordinates array: {coords[0]}, {coords[1]}")
        elif 'properties' in poi and 'lon' in poi['properties'] and 'lat' in poi['properties']:
            # Additional check for coordinates in properties
            props = poi['properties']
            poi_points.append(Point(props['lon'], props['lat']))
            print(f"Found properties lon/lat: {props['lon']}, {props['lat']}")
        else:
            print(f"No coordinates found in POI {poi.get('id', 'unknown')}")
    
    print(f"Extracted {len(poi_points)} points")
    return poi_points

def fix_poi_coordinates(pois):
    """
    Fix POI coordinates by promoting them to the top level
    """
    fixed_pois = []
    
    for poi in pois:
        poi_copy = dict(poi)  # Create a copy to avoid modifying original
        
        # Check if coordinates are in properties
        if 'properties' in poi:
            props = poi['properties']
            if 'lon' in props and 'lat' in props:
                poi_copy['lon'] = props['lon']
                poi_copy['lat'] = props['lat']
                print(f"Promoted coordinates from properties for POI {poi.get('id', 'unknown')}")
        
        # Add more extraction methods as needed
        
        fixed_pois.append(poi_copy)
    
    return fixed_pois

def write_fix_recommendations():
    """
    Write recommendations for fixing the POI coordinate issue
    """
    recommendations = """
# Recommended Fixes for POI Coordinate Issue

## Option 1: Update the distance module to check more locations for coordinates

Add additional checks in `add_travel_distances` function to look for coordinates in more places:

```python
# In the loop that extracts POI points
for poi in pois:
    if 'lon' in poi and 'lat' in poi:
        poi_points.append(Point(poi['lon'], poi['lat']))
    elif 'geometry' in poi and hasattr(poi['geometry'], 'x') and hasattr(poi['geometry'], 'y'):
        poi_points.append(Point(poi['geometry'].x, poi['geometry'].y))
    elif 'coordinates' in poi:
        coords = poi['coordinates']
        if isinstance(coords, list) and len(coords) >= 2:
            poi_points.append(Point(coords[0], coords[1]))
    elif 'properties' in poi and 'lon' in poi['properties'] and 'lat' in poi['properties']:
        # Additional check for coordinates in properties
        props = poi['properties']
        poi_points.append(Point(props['lon'], props['lat']))
    # Add more checks as needed
```

## Option 2: Pre-process POI data before passing to distance module

Before calling `add_travel_distances`, ensure all POIs have coordinates at the top level:

```python
def preprocess_poi_data(pois):
    processed_pois = []
    
    for poi in pois:
        poi_copy = dict(poi)
        
        # Check if coordinates are in properties
        if 'properties' in poi and 'lon' not in poi:
            props = poi['properties']
            if 'lon' in props and 'lat' in props:
                poi_copy['lon'] = props['lon']
                poi_copy['lat'] = props['lat']
        
        # Check if coordinates are in geometry
        elif 'geometry' in poi and 'lon' not in poi:
            geom = poi['geometry']
            if hasattr(geom, 'x') and hasattr(geom, 'y'):
                poi_copy['lon'] = geom.x
                poi_copy['lat'] = geom.y
        
        processed_pois.append(poi_copy)
    
    return processed_pois

# Then before calling add_travel_distances:
processed_pois = preprocess_poi_data(pois)
result = add_travel_distances(block_groups_gdf, processed_pois)
```

## Option 3: Debug where POI data is being loaded/created

Check the code that loads or creates the POI data:
1. Look for functions that read POI data from files or databases
2. Check how POI geometries are converted to dictionaries
3. Consider adding print statements to display POI structure right before distance calculation
"""
    
    with open("test_output/poi_coordinate_fix_recommendations.md", "w") as f:
        f.write(recommendations)
    print("\nWrote recommendations to test_output/poi_coordinate_fix_recommendations.md")

if __name__ == "__main__":
    debug_poi_data()
    write_fix_recommendations()
    print("\nTest complete. Check the output above for POI coordinate extraction results.") 