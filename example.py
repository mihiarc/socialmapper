#!/usr/bin/env python3
"""
Example script demonstrating the full poi_query workflow from POI retrieval to census analysis.
"""
import json
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import environment setup utilities
from setup_env import create_directories, activate_venv

# Import poi_query functionalities
from poi_query import (
    # Query functionality
    load_poi_config, # This is where the user define their POI query
    build_overpass_query,
    query_overpass,
    format_results,
    save_json,
    
    # Isochrone functionality
    create_isochrone_from_poi,
    create_isochrones_from_poi_list,
    create_isochrones_from_json_file,
    
    # Census block group functionality
    get_census_block_groups,
    load_isochrone,
    find_intersecting_block_groups,
    isochrone_to_block_groups,
    
    # Census data functionality
    load_block_groups,
    get_census_data_for_block_groups,
    get_variable_metadata,
    merge_census_data
)

def full_pipeline(config_file, travel_times, state_fips, census_variables=None):
    """
    Run the full pipeline from POI query to census block group analysis.
    
    Args:
        config_file: Path to YAML configuration file for POI query
        travel_times: List of travel times in minutes
        state_fips: List of state FIPS codes for census data
        census_variables: List of census variables to fetch (default population only)
    """
    print("="*80)
    print("FULL PIPELINE WORKFLOW")
    print("="*80)
    
    # Step 1: Load configuration and query POIs
    print("\nStep 1: Querying Points of Interest...")
    config = load_poi_config(config_file)
    query = build_overpass_query(config)
    
    print(f"Searching for: {config.get('type', '')} {config.get('tags', {})}")
    print(f"In area: {config.get('city', '')}, {config.get('state', '')}")
    
    raw_results = query_overpass(query)
    poi_data = format_results(raw_results)
    output_json = f"results/pois_{config.get('type', 'custom')}.json"
    save_json(poi_data, output_json)
    
    print(f"Found {len(poi_data.get('pois', []))} POIs")
    print(f"Saved POI data to {output_json}")
    
    # Step 2: Generate isochrones for each POI and travel time
    print("\nStep 2: Generating isochrones...")
    all_isochrone_files = []
    
    for poi in poi_data.get('pois', []):
        poi_name = poi.get('tags', {}).get('name', f"poi_{poi.get('id', 'unknown')}")
        print(f"Processing POI: {poi_name}")
        
        for time in travel_times:
            isochrone_file = create_isochrone_from_poi(
                poi=poi,
                travel_time_limit=time,
                output_dir='isochrones',
                save_file=True
            )
            all_isochrone_files.append(isochrone_file)
            print(f"  - Created {time}-minute isochrone: {isochrone_file}")
    
    # Step 3: Find census block groups for each isochrone
    print("\nStep 3: Finding census block groups in isochrones...")
    # Load environment variables (for Census API key)
    load_dotenv()
    
    block_group_files = []
    
    for isochrone_file in all_isochrone_files:
        # Extract info from filename for output naming
        isochrone_name = Path(isochrone_file).stem
        output_file = f"results/block_groups_{isochrone_name}.geojson"
        
        print(f"Processing isochrone: {isochrone_file}")
        result = isochrone_to_block_groups(
            isochrone_path=isochrone_file,
            state_fips=state_fips,
            output_path=output_file
        )
        
        print(f"  - Found {len(result)} intersecting block groups")
        print(f"  - Saved results to {output_file}")
        
        block_group_files.append(output_file)
    
    # Step 4: Fetch census data for block groups (new step)
    print("\nStep 4: Fetching census data for block groups...")
    
    # Default to population if no variables specified
    if not census_variables:
        census_variables = ['B01003_001E']  # Total population
        
    # Define a mapping for variable names for better readability
    variable_mapping = {
        'B01003_001E': 'total_population',
        'NAME': 'census_name'
    }
    
    enriched_files = []
    
    for block_group_file in block_group_files:
        # Create output filename for enriched data
        file_stem = Path(block_group_file).stem
        enriched_file = f"results/{file_stem}_with_census_data.geojson"
        
        print(f"Fetching census data for: {block_group_file}")
        
        # Fetch and merge census data
        enriched_data = get_census_data_for_block_groups(
            geojson_path=block_group_file,
            variables=census_variables,
            output_path=enriched_file,
            variable_mapping=variable_mapping
        )
        
        print(f"  - Added census data to {len(enriched_data)} block groups")
        print(f"  - Saved enriched data to {enriched_file}")
        
        enriched_files.append(enriched_file)
    
    print("\nFull pipeline completed successfully!")
    return {
        "poi_file": output_json,
        "isochrone_files": all_isochrone_files,
        "block_group_files": block_group_files,
        "enriched_files": enriched_files
    }

def examples():
    """Run the individual examples (for reference)."""
    print("="*80)
    print("INDIVIDUAL COMPONENT EXAMPLES")
    print("="*80)
    
    # Example 1: Generate isochrones from a JSON file
    print("\nExample 1: Generating isochrones from JSON file...")
    try:
        isochrone_files = create_isochrones_from_json_file(
            json_file_path='output.json',
            travel_time_limit=30,
            output_dir='isochrones',
            save_individual_files=True,
            combine_results=False
        )
        print(f"Created {len(isochrone_files)} individual isochrone files")
    except FileNotFoundError:
        print("File 'output.json' not found. Skipping this example.")

    # Example 2: Generate a single combined isochrone from a JSON file
    print("\nExample 2: Generating combined isochrone from JSON file...")
    try:
        combined_file = create_isochrones_from_json_file(
            json_file_path='output.json',
            travel_time_limit=45,
            output_dir='isochrones',
            save_individual_files=False,
            combine_results=True
        )
        print(f"Created combined isochrone file: {combined_file}")
    except FileNotFoundError:
        print("File 'output.json' not found. Skipping this example.")

    # Example 3: Process census block groups for an existing isochrone
    print("\nExample 3: Finding block groups for an isochrone...")
    # Check if we have any isochrone files from previous steps
    isochrone_dir = Path('isochrones')
    if isochrone_dir.exists() and any(isochrone_dir.glob('*.geojson')):
        isochrone_file = next(isochrone_dir.glob('*.geojson'))
        
        try:
            # Load environment variables (for Census API key)
            load_dotenv()
            
            output_file = f"results/block_groups_example.geojson"
            result = isochrone_to_block_groups(
                isochrone_path=str(isochrone_file),
                state_fips=["20"],  # Kansas as an example
                output_path=output_file
            )
            print(f"Found {len(result)} intersecting block groups")
            print(f"Saved results to {output_file}")
            
            # Example 4: Fetch census data for block groups (new example)
            print("\nExample 4: Fetching census data for block groups...")
            
            if Path(output_file).exists():
                # Define variables to fetch
                variables = ['B01003_001E', 'B19013_001E']  # Population and median household income
                
                # Define variable mapping for readability
                mapping = {
                    'B01003_001E': 'total_population',
                    'B19013_001E': 'median_household_income',
                    'NAME': 'census_name'
                }
                
                enriched_file = f"results/block_groups_example_with_census_data.geojson"
                
                enriched_data = get_census_data_for_block_groups(
                    geojson_path=output_file,
                    variables=variables,
                    output_path=enriched_file,
                    variable_mapping=mapping
                )
                
                print(f"Added census data to {len(enriched_data)} block groups")
                print(f"Saved enriched data to {enriched_file}")
                
                # Show some statistics
                if 'total_population' in enriched_data.columns:
                    total_pop = enriched_data['total_population'].astype(float).sum()
                    print(f"Total population in these block groups: {total_pop:,.0f}")
                
                if 'median_household_income' in enriched_data.columns:
                    avg_income = enriched_data['median_household_income'].astype(float).mean()
                    print(f"Average median household income: ${avg_income:,.2f}")
            
        except Exception as e:
            print(f"Error processing examples: {e}")
    else:
        print("No isochrone files found. Skipping these examples.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run POI query pipeline examples")
    parser.add_argument("--config", help="Path to POI configuration YAML file")
    parser.add_argument("--times", type=int, nargs="+", default=[15, 30], 
                        help="Travel times in minutes")
    parser.add_argument("--states", nargs="+", default=["20"], 
                        help="State FIPS codes for census data")
    parser.add_argument("--census-variables", nargs="+", 
                        help="Census variables to fetch (defaults to population)")
    parser.add_argument("--examples-only", action="store_true",
                        help="Run only the individual examples, not the full pipeline")
    
    args = parser.parse_args()
    
    # Ensure we have required directories
    create_directories()
    
    # Ensure we're running in the virtual environment
    activate_venv()
    
    # Run the appropriate function based on args
    if args.examples_only:
        examples()
    elif args.config:
        full_pipeline(args.config, args.times, args.states, args.census_variables)
    else:
        print("Please provide a config file path with --config or use --examples-only.")
        print("Example usage:")
        print("  python example.py --config poi_config.yaml --times 15 30 --states 20 08")
        print("  python example.py --config poi_config.yaml --census-variables B01003_001E B19013_001E")
        print("  python example.py --examples-only") 