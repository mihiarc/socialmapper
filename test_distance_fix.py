#!/usr/bin/env python3
"""
Test script to verify fix for distance calculation
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import os
from socialmapper.distance import add_travel_distances, calculate_distance
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create output directory if it doesn't exist
os.makedirs("test_output", exist_ok=True)

def test_distance_calculation_direct():
    """Test distance calculation directly"""
    # Test direct calculation between two points
    point1 = Point(-84.45, 38.25)  # POI
    point2 = Point(-84.5, 38.2)    # Centroid
    
    try:
        distance = calculate_distance(point1, point2)
        print(f"\nDirect distance calculation: {distance} km")
    except Exception as e:
        print(f"Error in direct distance calculation: {e}")

def test_distance_calculation():
    """Test the fixed distance calculation with various POI formats"""
    
    # Create a sample block group dataset
    block_groups = gpd.GeoDataFrame(
        {
            "GEOID": ["212219703012", "212219703022", "212219801001"],
            "geometry": [
                Point(-84.5, 38.2).buffer(0.1),
                Point(-84.6, 38.3).buffer(0.1),
                Point(-84.7, 38.4).buffer(0.1)
            ]
        },
        crs="EPSG:4326"
    )
    
    # Create sample POIs with different coordinate formats
    pois = [
        # POI with direct coordinates
        {
            "id": "poi_1",
            "name": "POI with direct coordinates",
            "lon": -84.45,
            "lat": 38.25,
            "travel_time_minutes": 15
        },
        # POI with coordinates in properties
        {
            "id": "poi_2",
            "name": "POI with coordinates in properties",
            "properties": {
                "lon": -84.55,
                "lat": 38.15
            },
            "travel_time_minutes": 15
        },
        # POI with longitude/latitude naming
        {
            "id": "poi_3",
            "name": "POI with longitude/latitude",
            "longitude": -84.65,
            "latitude": 38.35,
            "travel_time_minutes": 15
        }
    ]
    
    # Calculate distances using the fixed function
    result = add_travel_distances(block_groups, pois)
    
    # Print results
    print("\nDistance calculation results:")
    print(result[["GEOID", "poi_id", "travel_distance_km", "travel_distance_miles"]])
    
    # Save results to CSV for inspection
    result.to_csv("test_output/distance_calculation_test.csv", index=False)
    print("\nSaved results to test_output/distance_calculation_test.csv")

def debug_distance_module():
    """Debug the distance module by inspecting the code and intermediate values"""
    # Get a sample block group
    block_group = gpd.GeoDataFrame(
        {
            "GEOID": ["212219703012"],
            "geometry": [Point(-84.5, 38.2).buffer(0.1)]
        },
        crs="EPSG:4326"
    )
    
    # Sample POI
    poi = {
        "id": "poi_debug",
        "name": "Debug POI",
        "lon": -84.45,
        "lat": 38.25
    }
    
    # Create POI point
    poi_point = Point(poi["lon"], poi["lat"])
    print(f"\nPOI point: {poi_point}")
    
    # Get block group centroid
    bg_projected = block_group.copy().to_crs("EPSG:5070")
    centroid = bg_projected.geometry.centroid.iloc[0]
    print(f"Block group centroid: {centroid}")
    
    # Convert to WGS84 for debugging
    centroid_wgs84 = gpd.GeoDataFrame(geometry=[centroid], crs="EPSG:5070").to_crs("EPSG:4326").geometry.iloc[0]
    print(f"Centroid in WGS84: {centroid_wgs84}")
    
    # Try manual distance calculation
    points_gdf = gpd.GeoDataFrame(
        geometry=[poi_point, centroid_wgs84],
        crs="EPSG:4326"
    )
    
    points_projected = points_gdf.to_crs("EPSG:5070")
    print(f"\nProjected POI point: {points_projected.geometry.iloc[0]}")
    print(f"Projected centroid: {points_projected.geometry.iloc[1]}")
    
    # Calculate distance manually
    try:
        distance_meters = points_projected.iloc[0].geometry.distance(points_projected.iloc[1].geometry)
        distance_km = distance_meters / 1000
        print(f"\nManually calculated distance: {distance_km} km")
    except Exception as e:
        print(f"Error in manual distance calculation: {e}")

if __name__ == "__main__":
    print("\n=== Testing Direct Distance Calculation ===")
    test_distance_calculation_direct()
    
    print("\n=== Debugging Distance Module ===")
    debug_distance_module()
    
    print("\n=== Testing Full Distance Calculation ===")
    test_distance_calculation()
    
    print("\nTest complete.") 