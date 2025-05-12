#!/usr/bin/env python3
"""
Script to collect county data from the cache directory and bundle it into 
a single file for inclusion in the socialmapper package.

This enables spatial index operations without requiring API calls.
"""

import os
import shutil
import glob
import geopandas as gpd
from pathlib import Path

# Define paths
ROOT_DIR = Path(__file__).parent.parent
CACHE_DIR = ROOT_DIR / "cache"
OUTPUT_DIR = ROOT_DIR / "socialmapper" / "counties" / "data"

def main():
    """Bundle county data from cache into package data directory."""
    print("Bundling county geospatial data...")
    
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Find all county geojson files in the cache
    county_files = sorted(glob.glob(str(CACHE_DIR / "counties_*.geojson")))
    
    if not county_files:
        print("No county data found in cache. Run the application first to cache county data.")
        return
    
    print(f"Found {len(county_files)} county data files.")
    
    # Load and combine all county data
    counties_list = []
    for county_file in county_files:
        file_name = os.path.basename(county_file)
        print(f"Processing {file_name}...")
        try:
            gdf = gpd.read_file(county_file)
            counties_list.append(gdf)
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
    
    if not counties_list:
        print("No valid county data found. Exiting.")
        return
    
    # Combine all county dataframes
    print("Combining county data...")
    combined_counties = gpd.GeoDataFrame(pd.concat(counties_list, ignore_index=True))
    
    # Save as parquet for smaller file size and faster loading
    output_parquet = OUTPUT_DIR / "us_counties.parquet"
    print(f"Saving combined data to {output_parquet}...")
    combined_counties.to_parquet(output_parquet)
    
    # Also save as geojson for compatibility
    output_geojson = OUTPUT_DIR / "us_counties.geojson"
    print(f"Saving GeoJSON version to {output_geojson}...")
    combined_counties.to_file(output_geojson, driver="GeoJSON")
    
    print("County data bundling complete!")

if __name__ == "__main__":
    import pandas as pd
    main() 