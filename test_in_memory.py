#!/usr/bin/env python3
"""
Test script to verify in-memory processing without writing intermediate files.
"""
import os
import sys
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import tempfile
import json
from socialmapper.core import run_socialmapper

def create_sample_coords_file():
    """Create a temporary file with sample coordinates in Florida."""
    # Create sample data
    coords_data = {
        "pois": [
            {
                "id": 0,
                "name": "Test POI",
                "lat": 28.3852,
                "lon": -81.5639,
                "address": "123 Test St, Orlando, FL",
                "type": "test"
            }
        ],
        "metadata": {
            "states": ["FL"],
            "source": "test"
        }
    }
    
    # Create a temporary file
    fd, temp_path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(coords_data, f)
    
    return temp_path

def main():
    print("=== Testing In-Memory Processing ===")
    
    # Create temporary test data
    coords_file = create_sample_coords_file()
    print(f"Created temporary coordinates file: {coords_file}")
    
    try:
        # Run socialmapper with in-memory processing (no file outputs)
        result = run_socialmapper(
            custom_coords_path=coords_file,
            travel_time=5,  # Short travel time for faster test
            census_variables=["total_population"],  # Just one variable for simplicity
            export_csv=True,  # We want the CSV output
            export_geojson=False,  # Don't export GeoJSON files
            export_maps=False  # Don't generate maps
        )
        
        print("\n=== Test Results ===")
        print(f"CSV file created: {os.path.exists(result.get('csv_data', ''))}")
        
        # Check that other files aren't created
        isochrone_file = result.get('isochrone', '')
        block_groups_file = result.get('block_groups', '')
        census_data_file = result.get('census_data', '')
        
        print(f"Isochrone file exists: {os.path.exists(isochrone_file) if isochrone_file else False}")
        print(f"Block groups file exists: {os.path.exists(block_groups_file) if block_groups_file else False}")
        print(f"Census data file exists: {os.path.exists(census_data_file) if census_data_file else False}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(coords_file):
            os.remove(coords_file)
            print(f"Removed temporary file: {coords_file}")
    
    print("\n=== Test Complete ===")
    
if __name__ == "__main__":
    main() 