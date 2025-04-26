#!/usr/bin/env python3
"""
Community Mapper: End-to-end script for mapping community resources and demographics

This script ties together all components of the community-mapper project:
1. Query OpenStreetMap for Points of Interest (POIs)
2. Generate isochrones (travel time polygons) around those POIs
3. Find census block groups that intersect with the isochrones
4. Get demographic data for those block groups
5. Generate maps visualizing the demographic data
"""

import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

# Import components from the src modules
from src.query import (
    load_poi_config,
    build_overpass_query,
    query_overpass,
    format_results,
    save_json
)
from src.isochrone import (
    create_isochrones_from_poi_list
)
from src.blockgroups import (
    isochrone_to_block_groups
)
from src.census_data import (
    get_census_data_for_block_groups
)
from src.map_generator import (
    generate_maps_for_variables
)
from src.util import (
    state_name_to_abbreviation
)

def setup_directories() -> Dict[str, str]:
    """
    Create directories for output files.
    
    Returns:
        Dictionary of directory paths
    """
    dirs = {
        "output": "output",
        "pois": "output/pois",
        "isochrones": "output/isochrones",
        "block_groups": "output/block_groups",
        "census_data": "output/census_data",
        "maps": "output/maps"
    }
    
    for path in dirs.values():
        Path(path).mkdir(parents=True, exist_ok=True)
        
    return dirs

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Community Mapper: End-to-end tool for mapping community resources and demographics')
    
    parser.add_argument('--config', type=str, required=True, 
                        help='Path to POI configuration YAML file')
    parser.add_argument('--state', type=str, required=False, nargs='+',
                        help='State FIPS code(s) or abbreviation(s) (e.g., KS or 20). If not provided, uses state from config file.')
    parser.add_argument('--travel-time', type=int, default=15,
                        help='Travel time limit in minutes (default: 15)')
    parser.add_argument('--census-variables', type=str, nargs='+',
                        default=['B01003_001E', 'B19013_001E'],
                        help='Census variables to retrieve (default: population and income)')
    parser.add_argument('--api-key', type=str,
                        help='Census API key (optional if set as CENSUS_API_KEY environment variable)')
    
    return parser.parse_args()

def run_community_mapper(
    config_path: str,
    state_fips: List[str] = None,
    travel_time: int = 15,
    census_variables: List[str] = None,
    api_key: Optional[str] = None,
    output_dirs: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Run the complete community mapping pipeline.
    
    Args:
        config_path: Path to POI configuration YAML file
        state_fips: List of state FIPS codes or abbreviations (optional)
        travel_time: Travel time limit in minutes
        census_variables: List of Census API variables to retrieve
        api_key: Census API key (optional if set as environment variable)
        output_dirs: Dictionary of output directories
        
    Returns:
        Dictionary of output file paths
    """
    if census_variables is None:
        census_variables = ['B01003_001E', 'B19013_001E']  # Default: population and median income
        
    if output_dirs is None:
        output_dirs = setup_directories()
        
    result_files = {}
    
    # Step 1: Query POIs
    print("\n=== Step 1: Querying Points of Interest ===")
    config = load_poi_config(config_path)
    query = build_overpass_query(config)
    
    print(f"Querying OpenStreetMap for: {config.get('geocode_area', '')} - {config.get('type', '')} - {config.get('name', '')}")
    raw_results = query_overpass(query)
    poi_data = format_results(raw_results)
    
    # Set a name for the output file based on the POI configuration
    poi_type = config.get("type", "poi")
    poi_name = config.get("name", "custom").replace(" ", "_").lower()
    location = config.get("geocode_area", "").replace(" ", "_").lower()
    
    # Create a base filename component for all outputs
    if location:
        base_filename = f"{location}_{poi_type}_{poi_name}"
    else:
        base_filename = f"{poi_type}_{poi_name}"
    
    # Use the base filename for POI data
    poi_file = os.path.join(output_dirs["pois"], f"{base_filename}.json")
    
    save_json(poi_data, poi_file)
    result_files["poi_data"] = poi_file
    
    print(f"Found {len(poi_data['pois'])} POIs")
    
    # Step 2: Generate isochrones
    print("\n=== Step 2: Generating Isochrones ===")
    combined_isochrone_file = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir=output_dirs["isochrones"],
        save_individual_files=True,
        combine_results=True
    )
    result_files["isochrone"] = combined_isochrone_file
    
    print(f"Isochrones generated and saved to {combined_isochrone_file}")
    
    # Step 3: Find intersecting block groups
    print("\n=== Step 3: Finding Intersecting Census Block Groups ===")
    block_groups_file = os.path.join(
        output_dirs["block_groups"],
        f"{base_filename}_{travel_time}min_block_groups.geojson"
    )
    
    block_groups = isochrone_to_block_groups(
        isochrone_path=combined_isochrone_file,
        state_fips=state_fips,
        output_path=block_groups_file,
        api_key=api_key
    )
    result_files["block_groups"] = block_groups_file
    
    print(f"Found {len(block_groups)} intersecting block groups")
    
    # Step 4: Fetch census data for block groups
    print("\n=== Step 4: Fetching Census Data ===")
    
    # Create a more readable mapping for the census variables
    variable_mapping = {
        'B01003_001E': 'total_population',
        'B19013_001E': 'median_household_income',
        'B25077_001E': 'median_home_value',
        'B01002_001E': 'median_age',
        'B02001_002E': 'white_population',
        'B02001_003E': 'black_population',
        'B11001_001E': 'households',
        'B25001_001E': 'housing_units'
    }
    
    # Keep only the mappings for variables we're actually using
    active_variable_mapping = {var: variable_mapping.get(var, var) 
                              for var in census_variables if var in variable_mapping}
    
    census_data_file = os.path.join(
        output_dirs["census_data"],
        f"{base_filename}_{travel_time}min_census_data.geojson"
    )
    
    census_data = get_census_data_for_block_groups(
        geojson_path=block_groups_file,
        variables=census_variables,
        output_path=census_data_file,
        variable_mapping=active_variable_mapping,
        api_key=api_key
    )
    result_files["census_data"] = census_data_file
    
    # Step 5: Generate maps
    print("\n=== Step 5: Generating Maps ===")
    
    # Get visualization variables from the census data result
    if hasattr(census_data, 'attrs') and 'variables_for_visualization' in census_data.attrs:
        visualization_variables = census_data.attrs['variables_for_visualization']
        print(f"Using variables for visualization from census data: {visualization_variables}")
    else:
        # Fallback to filtering out known non-visualization variables
        visualization_variables = [var for var in census_variables if var != 'NAME']
        print(f"No visualization variables attribute found, filtering out 'NAME': {visualization_variables}")
    
    # Transform census variable codes to their mapped names for the map generator
    mapped_variables = []
    for var in visualization_variables:
        # Use the mapped name if available, otherwise use the original code
        mapped_name = active_variable_mapping.get(var, var)
        mapped_variables.append(mapped_name)
    
    # Generate maps for each census variable using the mapped names
    map_files = generate_maps_for_variables(
        census_data_path=census_data_file,
        variables=mapped_variables,
        output_dir=output_dirs["maps"],
        basename=f"{base_filename}_{travel_time}min",
        isochrone_path=combined_isochrone_file
    )
    result_files["maps"] = map_files
    
    print(f"Generated {len(map_files)} maps")
    
    return result_files

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup output directories
    output_dirs = setup_directories()
    
    # Print banner
    print("=" * 80)
    print("Community Mapper: End-to-end tool for mapping community resources")
    print("=" * 80)
    
    # Run the pipeline
    results = run_community_mapper(
        config_path=args.config,
        state_fips=args.state,
        travel_time=args.travel_time,
        census_variables=args.census_variables,
        api_key=args.api_key,
        output_dirs=output_dirs
    )
    
    # Print summary
    print("\n=== Community Mapping Complete ===")
    print(f"POI Data: {results['poi_data']}")
    print(f"Isochrone: {results['isochrone']}")
    print(f"Block Groups: {results['block_groups']}")
    print(f"Census Data: {results['census_data']}")
    print(f"Maps: {len(results['maps'])} files generated in {output_dirs['maps']}")
    print("\nUse these maps to analyze community resources and demographics!")

if __name__ == "__main__":
    main() 