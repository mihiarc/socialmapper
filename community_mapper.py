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
import csv
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
    state_name_to_abbreviation,
    census_code_to_name,
    normalize_census_variable,
    CENSUS_VARIABLE_MAPPING
)

def parse_custom_coordinates(file_path: str) -> Dict:
    """
    Parse a custom coordinates file (JSON or CSV) into the POI format expected by the isochrone generator.
    
    Args:
        file_path: Path to the custom coordinates file
        
    Returns:
        Dictionary containing POI data in the format expected by the isochrone generator
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    pois = []
    
    if file_extension == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Handle different possible JSON formats
        if isinstance(data, list):
            # List of POIs
            for item in data:
                if 'lat' in item and 'lon' in item:
                    poi = {
                        'id': item.get('id', f"custom_{len(pois)}"),
                        'name': item.get('name', f"Custom POI {len(pois)}"),
                        'lat': float(item['lat']),
                        'lon': float(item['lon']),
                        'tags': item.get('tags', {})
                    }
                    pois.append(poi)
                elif 'latitude' in item and 'longitude' in item:
                    poi = {
                        'id': item.get('id', f"custom_{len(pois)}"),
                        'name': item.get('name', f"Custom POI {len(pois)}"),
                        'lat': float(item['latitude']),
                        'lon': float(item['longitude']),
                        'tags': item.get('tags', {})
                    }
                    pois.append(poi)
        elif isinstance(data, dict) and 'pois' in data:
            # Already in expected format
            pois = data['pois']
    
    elif file_extension == '.csv':
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                # Try to find lat/lon in different possible column names
                lat = None
                lon = None
                
                for lat_key in ['lat', 'latitude', 'y']:
                    if lat_key in row:
                        lat = float(row[lat_key])
                        break
                
                for lon_key in ['lon', 'lng', 'longitude', 'x']:
                    if lon_key in row:
                        lon = float(row[lon_key])
                        break
                
                if lat is not None and lon is not None:
                    poi = {
                        'id': row.get('id', f"custom_{i}"),
                        'name': row.get('name', f"Custom POI {i}"),
                        'lat': lat,
                        'lon': lon,
                        'tags': {}
                    }
                    
                    # Add any additional columns as tags
                    for key, value in row.items():
                        if key not in ['id', 'name', 'lat', 'latitude', 'y', 'lon', 'lng', 'longitude', 'x']:
                            poi['tags'][key] = value
                    
                    pois.append(poi)
    
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Please provide a JSON or CSV file.")
    
    if not pois:
        raise ValueError(f"No valid coordinates found in {file_path}. Please check the file format.")
    
    return {
        'pois': pois,
        'metadata': {
            'source': 'custom',
            'count': len(pois),
            'file_path': file_path
        }
    }

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
    
    parser.add_argument('--config', type=str, required=False, 
                        help='Path to POI configuration YAML file')
    parser.add_argument('--custom-coords', type=str,
                        help='Path to custom JSON or CSV file with latitude/longitude coordinates (skips POI query)')
    parser.add_argument('--travel-time', type=int, default=15,
                        help='Travel time limit in minutes (default: 15)')
    parser.add_argument('--census-variables', type=str, nargs='+',
                        default=['total_population', 'median_household_income'],
                        help='Census variables to retrieve (default: total_population and median_household_income)')
    parser.add_argument('--api-key', type=str,
                        help='Census API key (optional if set as CENSUS_API_KEY environment variable)')
    parser.add_argument('--list-variables', action='store_true',
                        help='List available census variables and exit')
    
    args = parser.parse_args()
    
    # If --list-variables is specified, print the variables and exit
    if args.list_variables:
        print("\nAvailable Census Variables:")
        print("=" * 50)
        for code, name in sorted(CENSUS_VARIABLE_MAPPING.items()):
            print(f"{name:<25} {code}")
        print("\nUsage example: --census-variables total_population median_household_income")
        exit(0)
        
    # Make sure either --config or --custom-coords is provided
    if not args.config and not args.custom_coords:
        parser.error("Either --config or --custom-coords must be provided")
    
    return args

def run_community_mapper(
    config_path: Optional[str] = None,
    travel_time: int = 15,
    census_variables: List[str] = None,
    api_key: Optional[str] = None,
    output_dirs: Optional[Dict[str, str]] = None,
    custom_coords_path: Optional[str] = None
) -> Dict[str, str]:
    """
    Run the complete community mapping pipeline.
    
    Args:
        config_path: Path to POI configuration YAML file (required if custom_coords_path is None)
        travel_time: Travel time limit in minutes
        census_variables: List of Census API variables to retrieve
        api_key: Census API key (optional if set as environment variable)
        output_dirs: Dictionary of output directories
        custom_coords_path: Path to custom coordinates file (skips POI query if provided)
        
    Returns:
        Dictionary of output file paths
    """
    
    # Convert any human-readable names to census codes
    census_codes = [normalize_census_variable(var) for var in census_variables]
    
    if output_dirs is None:
        output_dirs = setup_directories()
        
    result_files = {}
    
    # Determine if we're using custom coordinates or querying POIs
    if custom_coords_path:
        # Skip Step 1: Use custom coordinates
        print("\n=== Using Custom Coordinates (Skipping POI Query) ===")
        poi_data = parse_custom_coordinates(custom_coords_path)
        
        # Set a name for the output file based on the custom coords file
        file_basename = os.path.basename(custom_coords_path)
        base_filename = f"custom_{os.path.splitext(file_basename)[0]}"
        
        # Save the parsed coordinates in the expected format
        poi_file = os.path.join(output_dirs["pois"], f"{base_filename}.json")
        save_json(poi_data, poi_file)
        result_files["poi_data"] = poi_file
        
        print(f"Using {len(poi_data['pois'])} custom coordinates from {custom_coords_path}")
        print(f"Saved formatted POI data to {poi_file}")
        
    else:
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
    
    # Get state from config and convert to state abbreviation
    state_fips = None
    if config_path and "state" in (config := load_poi_config(config_path)):
        state_name = config.get("state")
        state_abbr = state_name_to_abbreviation(state_name)
        if state_abbr:
            state_fips = [state_abbr]
            print(f"Using state from config file: {state_name} ({state_abbr})")
    
    block_groups = isochrone_to_block_groups(
        isochrone_path=combined_isochrone_file,
        state_fips=state_fips,
        output_path=block_groups_file,
        api_key=api_key
    )
    result_files["block_groups"] = block_groups_file
    
    # Step 4: Fetch census data for block groups
    print("\n=== Step 4: Fetching Census Data ===")
    
    # Create a human-readable mapping for the census variables
    variable_mapping = {code: census_code_to_name(code) for code in census_codes}
    
    census_data_file = os.path.join(
        output_dirs["census_data"],
        f"{base_filename}_{travel_time}min_census_data.geojson"
    )
    
    census_data = get_census_data_for_block_groups(
        geojson_path=block_groups_file,
        variables=census_codes,
        output_path=census_data_file,
        variable_mapping=variable_mapping,
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
        visualization_variables = [var for var in census_codes if var != 'NAME']
        print(f"No visualization variables attribute found, filtering out 'NAME': {visualization_variables}")
    
    # Transform census variable codes to their mapped names for the map generator
    mapped_variables = []
    for var in visualization_variables:
        # Use the mapped name if available, otherwise use the original code
        mapped_name = variable_mapping.get(var, var)
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
        travel_time=args.travel_time,
        census_variables=args.census_variables,
        api_key=args.api_key,
        output_dirs=output_dirs,
        custom_coords_path=args.custom_coords
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