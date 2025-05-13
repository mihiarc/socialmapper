#!/usr/bin/env python3
"""
Diagnostic script to debug the empty dataframe issue in the export process.
This script traces the data flow through the SocialMapper pipeline to identify
where data might be getting lost.
"""

import os
import sys
import pandas as pd
import geopandas as gpd
import json
from pathlib import Path

# Ensure we can import from socialmapper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from socialmapper.query import build_overpass_query, query_overpass, format_results, create_poi_config
from socialmapper.isochrone import create_isochrones_from_poi_list
from socialmapper.blockgroups import isochrone_to_block_groups_by_county
from socialmapper.distance import add_travel_distances
from socialmapper.census import get_census_data_for_block_groups
from socialmapper.export import export_census_data_to_csv
from socialmapper.util import census_code_to_name
from socialmapper.states import normalize_state, StateFormat

def print_dataframe_info(name, df):
    """Print diagnostic information about a dataframe."""
    print(f"\n=== {name} ===")
    
    if df is None:
        print(f"ERROR: {name} is None!")
        return
        
    if df.empty:
        print(f"ERROR: {name} is empty!")
        return
        
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Print the first row as a sample
    if len(df) > 0:
        print("\nSample row (first row):")
        sample_row = df.iloc[0].to_dict()
        for k, v in sample_row.items():
            if k != 'geometry':  # Skip geometry as it's verbose
                print(f"  {k}: {v}")
        
        # For GeoDataFrames, print geometry type
        if isinstance(df, gpd.GeoDataFrame) and 'geometry' in df.columns:
            print(f"Geometry type: {df.geometry.iloc[0].geom_type}")
    
    print(f"Memory usage: {df.memory_usage().sum() / 1024:.2f} KB")

def run_diagnostic_test(
    geocode_area="Fuquay-Varina",
    state="NC",
    poi_type="amenity",
    poi_name="library",
    travel_time=15,
    census_variables=["total_population", "median_household_income"],
    api_key=None,
    output_dir="test_output/debug"
):
    """
    Run a diagnostic test through the SocialMapper pipeline to identify where data might be getting lost.
    
    Args:
        geocode_area: Area to search (e.g., city name)
        state: State abbreviation
        poi_type: Type of POI (e.g., 'amenity')
        poi_name: Name of POI (e.g., 'library')
        travel_time: Travel time in minutes
        census_variables: List of census variables to retrieve
        api_key: Census API key (optional, will use environment variable if not provided)
        output_dir: Directory to save debug outputs
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Query POIs
    print("\n=== STEP 1: Querying POIs ===")
    config = create_poi_config(
        geocode_area=geocode_area,
        state=state,
        city=geocode_area,
        poi_type=poi_type,
        poi_name=poi_name
    )
    
    query = build_overpass_query(config)
    print(f"Overpass Query: {query[:100]}... (truncated)")
    
    raw_results = query_overpass(query)
    poi_data = format_results(raw_results, config)
    
    # Print POI data summary
    print(f"Found {len(poi_data.get('pois', []))} POIs")
    if len(poi_data.get('pois', [])) > 0:
        print("First POI:")
        first_poi = poi_data['pois'][0]
        for k, v in first_poi.items():
            if k != 'tags':  # Skip tags as they can be verbose
                print(f"  {k}: {v}")
    
    # Save POI data for inspection
    with open(os.path.join(output_dir, "poi_data.json"), "w") as f:
        json.dump(poi_data, f, indent=2)
    
    # Create a base filename for outputs
    poi_type_str = poi_type.replace(" ", "_").lower()
    poi_name_str = poi_name.replace(" ", "_").lower()
    location = geocode_area.replace(" ", "_").lower()
    base_filename = f"{location}_{poi_type_str}_{poi_name_str}"
    
    # Step 2: Generate isochrones
    print("\n=== STEP 2: Generating Isochrones ===")
    isochrone_gdf = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir=output_dir,
        save_individual_files=True,  # Save individual files for debugging
        combine_results=True  # Combine isochrones
    )
    
    if isinstance(isochrone_gdf, str):
        print(f"WARNING: create_isochrones_from_poi_list returned a file path: {isochrone_gdf}")
        # Handle both GeoJSON and Parquet files
        if isochrone_gdf.endswith('.parquet'):
            try:
                import pyarrow.parquet as pq
                table = pq.read_table(isochrone_gdf)
                isochrone_gdf = gpd.GeoDataFrame.from_arrow(table)
                print("Successfully loaded Parquet file using pyarrow")
            except Exception as e:
                print(f"ERROR: Failed to load Parquet file with pyarrow: {e}")
                # Try an alternative method
                try:
                    isochrone_gdf = gpd.read_parquet(isochrone_gdf)
                    print("Successfully loaded Parquet file using gpd.read_parquet")
                except Exception as e2:
                    print(f"ERROR: Failed to load Parquet file with gpd.read_parquet: {e2}")
                    # Create a minimal GeoDataFrame to continue the test
                    isochrone_gdf = gpd.GeoDataFrame()
        else:
            try:
                isochrone_gdf = gpd.read_file(isochrone_gdf)
                print("Successfully loaded GeoJSON file")
            except Exception as e:
                print(f"ERROR: Failed to load GeoJSON file: {e}")
                # Create a minimal GeoDataFrame to continue the test
                isochrone_gdf = gpd.GeoDataFrame()
    
    print_dataframe_info("Isochrone GeoDataFrame", isochrone_gdf)
    
    # Save isochrone data for inspection
    isochrone_file = os.path.join(output_dir, f"{base_filename}_isochrones.geojson")
    if not isochrone_gdf.empty:
        isochrone_gdf.to_file(isochrone_file, driver="GeoJSON")
        print(f"Saved isochrone data to {isochrone_file}")
    
    # Step 3: Find intersecting block groups
    print("\n=== STEP 3: Finding Intersecting Block Groups ===")
    block_groups_file = os.path.join(output_dir, f"{base_filename}_block_groups.geojson")
    
    block_groups_gdf = isochrone_to_block_groups_by_county(
        isochrone_path=isochrone_gdf,
        poi_data=poi_data,
        output_path=block_groups_file,
        api_key=api_key
    )
    
    print_dataframe_info("Block Groups GeoDataFrame", block_groups_gdf)
    
    # Step 4: Calculate travel distances
    print("\n=== STEP 4: Calculating Travel Distances ===")
    travel_distances_file = os.path.join(output_dir, f"{base_filename}_travel_distances.geojson")
    
    block_groups_with_distances = add_travel_distances(
        block_groups_gdf=block_groups_gdf,
        poi_data=poi_data,
        output_path=travel_distances_file
    )
    
    print_dataframe_info("Block Groups with Distances GeoDataFrame", block_groups_with_distances)
    
    # Step 5: Fetch census data
    print("\n=== STEP 5: Fetching Census Data ===")
    census_codes = census_variables  # For simplicity in this test
    
    census_data_file = os.path.join(output_dir, f"{base_filename}_census_data.geojson")
    
    # Create variable mapping
    variable_mapping = {code: census_code_to_name(code) for code in census_codes}
    
    census_data_gdf = get_census_data_for_block_groups(
        geojson_path=block_groups_with_distances,
        variables=census_codes,
        output_path=census_data_file,
        variable_mapping=variable_mapping,
        api_key=api_key
    )
    
    print_dataframe_info("Census Data GeoDataFrame", census_data_gdf)
    
    # Check geometry columns in census data
    if not census_data_gdf.empty and 'geometry' in census_data_gdf.columns:
        print("\nGeometry validation in census data:")
        print(f"  Has valid geometries: {census_data_gdf.geometry.is_valid.all()}")
        print(f"  Contains None geometries: {census_data_gdf.geometry.isna().any()}")
    
    # Step 6: Export to CSV (the problem area)
    print("\n=== STEP 6: Exporting to CSV ===")
    
    # Dump the first row of census_data_gdf to a JSON file for inspection
    if not census_data_gdf.empty:
        row_dict = {
            col: str(census_data_gdf.iloc[0][col]) 
            for col in census_data_gdf.columns 
            if col != 'geometry'
        }
        with open(os.path.join(output_dir, "census_data_first_row.json"), "w") as f:
            json.dump(row_dict, f, indent=2)
    
    # Dump the poi_data structure to a separate file
    with open(os.path.join(output_dir, "poi_data_for_export.json"), "w") as f:
        if isinstance(poi_data, dict):
            # Convert any GeoSeries or complex objects to strings
            simplified_poi = {}
            for k, v in poi_data.items():
                if k == 'pois':
                    simplified_poi[k] = [
                        {sk: str(sv) if not isinstance(sv, (str, int, float, bool, type(None), dict, list)) else sv 
                         for sk, sv in poi.items()}
                        for poi in v
                    ]
                else:
                    simplified_poi[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None), dict, list)) else v
            json.dump(simplified_poi, f, indent=2)
        else:
            json.dump({"error": "poi_data is not a dictionary"}, f)
    
    csv_file = os.path.join(output_dir, f"{base_filename}_census_data.csv")
    
    try:
        # Verbose version of export function to debug the issue
        print("\nDEBUG: Starting export_census_data_to_csv function")
        print(f"Census data is None? {census_data_gdf is None}")
        if census_data_gdf is not None:
            print(f"Census data is empty? {census_data_gdf.empty}")
            if not census_data_gdf.empty:
                print(f"Census data shape: {census_data_gdf.shape}")
                print(f"Census data has GEOID column? {'GEOID' in census_data_gdf.columns}")
        
        print(f"POI data is None? {poi_data is None}")
        if poi_data is not None and isinstance(poi_data, dict):
            print(f"POI data has 'pois' key? {'pois' in poi_data}")
            if 'pois' in poi_data:
                print(f"POI data has {len(poi_data['pois'])} POIs")
        
        csv_output = export_census_data_to_csv(
            census_data=census_data_gdf,
            poi_data=poi_data,
            output_path=csv_file,
            base_filename=f"{base_filename}_{travel_time}min"
        )
        
        print(f"CSV export completed successfully to: {csv_output}")
        
        # Check if the file exists and has content
        if os.path.exists(csv_output):
            file_size = os.path.getsize(csv_output)
            print(f"CSV file size: {file_size} bytes")
            
            if file_size > 0:
                # Read and print the CSV content
                csv_df = pd.read_csv(csv_output)
                print_dataframe_info("Exported CSV DataFrame", csv_df)
            else:
                print("WARNING: CSV file is empty (0 bytes)")
    except Exception as e:
        print(f"ERROR during CSV export: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Diagnostic Test Complete ===")
    print(f"All debug files saved to: {output_dir}")
    return {
        "poi_data": poi_data,
        "isochrone_gdf": isochrone_gdf,
        "block_groups_gdf": block_groups_gdf,
        "block_groups_with_distances": block_groups_with_distances,
        "census_data_gdf": census_data_gdf
    }

if __name__ == "__main__":
    # Get Census API key from environment variable if available
    api_key = os.environ.get("CENSUS_API_KEY")
    
    # Run the diagnostic test
    results = run_diagnostic_test(
        geocode_area="Fuquay-Varina",
        state="NC",
        poi_type="amenity",
        poi_name="library",
        travel_time=15,
        census_variables=["total_population", "median_household_income", "median_age"],
        api_key=api_key,
        output_dir="test_output/export_debug"
    )
    
    print("\n=== Summary ===")
    print(f"POI Data: {'✓' if results['poi_data'] and len(results['poi_data'].get('pois', [])) > 0 else '✗'}")
    print(f"Isochrones: {'✓' if not results['isochrone_gdf'].empty else '✗'}")
    print(f"Block Groups: {'✓' if not results['block_groups_gdf'].empty else '✗'}")
    print(f"Block Groups w/ Distances: {'✓' if not results['block_groups_with_distances'].empty else '✗'}")
    print(f"Census Data: {'✓' if not results['census_data_gdf'].empty else '✗'}") 