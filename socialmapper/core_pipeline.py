"""
SocialMapper Core Pipeline: Modular ETL Functions

This module breaks down the monolithic run_socialmapper function into smaller,
focused, testable components following the Single Responsibility Principle.
"""

import os
import json
import csv
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
import geopandas as gpd
from pathlib import Path

# Import configuration and utilities
from .util.invalid_data_tracker import get_global_tracker, reset_global_tracker
from .util import normalize_census_variable, get_readable_census_variables


def setup_pipeline_environment(output_dir: str, export_csv: bool, export_maps: bool, export_isochrones: bool) -> Dict[str, str]:
    """
    Set up the pipeline environment and create necessary directories.
    
    Args:
        output_dir: Base output directory
        export_csv: Whether CSV export is enabled
        export_maps: Whether map export is enabled  
        export_isochrones: Whether isochrone export is enabled
        
    Returns:
        Dictionary of created directory paths
    """
    from .core import setup_directory
    
    # Create base output directory
    setup_directory(output_dir)
    
    directories = {"base": output_dir}
    
    # Create subdirectories only for enabled outputs
    if export_csv:
        csv_dir = os.path.join(output_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)
        directories["csv"] = csv_dir
    
    if export_maps:
        maps_dir = os.path.join(output_dir, "maps")
        os.makedirs(maps_dir, exist_ok=True)
        directories["maps"] = maps_dir
    
    if export_isochrones:
        isochrones_dir = os.path.join(output_dir, "isochrones")
        os.makedirs(isochrones_dir, exist_ok=True)
        directories["isochrones"] = isochrones_dir
    
    # Initialize invalid data tracker for this session
    reset_global_tracker(output_dir)
    
    return directories


def extract_poi_data(
    custom_coords_path: Optional[str] = None,
    geocode_area: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    poi_type: Optional[str] = None,
    poi_name: Optional[str] = None,
    additional_tags: Optional[Dict] = None,
    name_field: Optional[str] = None,
    type_field: Optional[str] = None,
    max_poi_count: Optional[int] = None
) -> Tuple[Dict[str, Any], str, List[str], bool]:
    """
    Extract POI data from either custom coordinates or OpenStreetMap.
    
    Returns:
        Tuple of (poi_data, base_filename, state_abbreviations, sampled_pois)
    """
    from .core import parse_custom_coordinates
    from .query import build_overpass_query, query_overpass, format_results, create_poi_config
    from .states import normalize_state, normalize_state_list, StateFormat
    from urllib.error import URLError
    
    state_abbreviations = []
    sampled_pois = False
    
    if custom_coords_path:
        print("\n=== Using Custom Coordinates (Skipping POI Query) ===")
        poi_data = parse_custom_coordinates(custom_coords_path, name_field, type_field)
        
        # Extract state information from the custom coordinates if available
        if 'metadata' in poi_data and 'states' in poi_data['metadata'] and poi_data['metadata']['states']:
            state_abbreviations = normalize_state_list(poi_data['metadata']['states'], to_format=StateFormat.ABBREVIATION)
            
            if state_abbreviations:
                print(f"Using states from custom coordinates: {', '.join(state_abbreviations)}")
        
        # Set a name for the output file based on the custom coords file
        file_basename = os.path.basename(custom_coords_path)
        base_filename = f"custom_{os.path.splitext(file_basename)[0]}"
        
        # Apply POI limit if specified
        if max_poi_count and 'pois' in poi_data and len(poi_data['pois']) > max_poi_count:
            original_count = len(poi_data['pois'])
            poi_data['pois'] = random.sample(poi_data['pois'], max_poi_count)
            poi_data['poi_count'] = len(poi_data['pois'])
            print(f"Sampled {max_poi_count} POIs from {original_count} total POIs")
            sampled_pois = True
            
            # Add sampling info to metadata
            if 'metadata' not in poi_data:
                poi_data['metadata'] = {}
            poi_data['metadata']['sampled'] = True
            poi_data['metadata']['original_count'] = original_count
            
        print(f"Using {len(poi_data['pois'])} custom coordinates from {custom_coords_path}")
        
    else:
        # Query POIs from OpenStreetMap
        print("\n=== Querying Points of Interest ===")
        
        if not (geocode_area and poi_type and poi_name):
            raise ValueError("Missing required POI parameters: geocode_area, poi_type, and poi_name are required")
            
        # Normalize state to abbreviation if provided
        state_abbr = normalize_state(state, to_format=StateFormat.ABBREVIATION) if state else None
        
        # Create POI configuration
        config = create_poi_config(
            geocode_area=geocode_area,
            state=state_abbr,
            city=city or geocode_area,
            poi_type=poi_type,
            poi_name=poi_name,
            additional_tags=additional_tags
        )
        print(f"Querying OpenStreetMap for: {geocode_area} - {poi_type} - {poi_name}")
        
        # Execute query with error handling
        query = build_overpass_query(config)
        try:
            raw_results = query_overpass(query)
        except (URLError, OSError) as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                raise ValueError(
                    "Unable to connect to OpenStreetMap API. This could be due to:\n"
                    "- Temporary API outage\n"
                    "- Network connectivity issues\n"
                    "- Rate limiting\n\n"
                    "Please try:\n"
                    "1. Waiting a few minutes and trying again\n"
                    "2. Checking your internet connection\n"
                    "3. Using a different POI type or location"
                ) from e
            else:
                raise ValueError(f"Error querying OpenStreetMap: {error_msg}") from e
                
        poi_data = format_results(raw_results, config)
        
        # Generate base filename from POI configuration
        poi_type_str = config.get("type", "poi")
        poi_name_str = config.get("name", "custom").replace(" ", "_").lower()
        location = config.get("geocode_area", "").replace(" ", "_").lower()
        
        if location:
            base_filename = f"{location}_{poi_type_str}_{poi_name_str}"
        else:
            base_filename = f"{poi_type_str}_{poi_name_str}"
        
        # Apply POI limit if specified
        if max_poi_count and 'pois' in poi_data and len(poi_data['pois']) > max_poi_count:
            original_count = len(poi_data['pois'])
            poi_data['pois'] = random.sample(poi_data['pois'], max_poi_count)
            poi_data['poi_count'] = len(poi_data['pois'])
            print(f"Sampled {max_poi_count} POIs from {original_count} total POIs")
            sampled_pois = True
            
            # Add sampling info to metadata
            if 'metadata' not in poi_data:
                poi_data['metadata'] = {}
            poi_data['metadata']['sampled'] = True
            poi_data['metadata']['original_count'] = original_count
        
        print(f"Found {len(poi_data['pois'])} POIs")
        
        # Extract state from config if available
        state_name = config.get("state")
        if state_name:
            state_abbr = normalize_state(state_name, to_format=StateFormat.ABBREVIATION)
            if state_abbr and state_abbr not in state_abbreviations:
                state_abbreviations.append(state_abbr)
                print(f"Using state from parameters: {state_name} ({state_abbr})")
    
    # Validate that we have POIs to process
    if not poi_data or 'pois' not in poi_data or not poi_data['pois']:
        raise ValueError("No POIs found to analyze. Please try different search criteria or check your input data.")
    
    return poi_data, base_filename, state_abbreviations, sampled_pois


def validate_poi_coordinates(poi_data: Dict[str, Any]) -> None:
    """
    Validate POI coordinates using Pydantic validation.
    
    Args:
        poi_data: POI data dictionary
        
    Raises:
        ValueError: If no valid coordinates are found
    """
    from .util.coordinate_validation import validate_poi_coordinates as validate_coords
    
    print("\n=== Validating POI Coordinates ===")
    
    # Extract POIs from poi_data for validation
    pois_to_validate = poi_data['pois'] if isinstance(poi_data, dict) else poi_data
    
    # Validate coordinates
    validation_result = validate_coords(pois_to_validate)
    
    if validation_result.total_valid == 0:
        raise ValueError(f"No valid POI coordinates found. All {validation_result.total_input} POIs failed validation.")
    
    if validation_result.total_invalid > 0:
        print(f"⚠️  Coordinate Validation Warning: {validation_result.total_invalid} out of {validation_result.total_input} POIs have invalid coordinates")
        print(f"   Valid POIs: {validation_result.total_valid} ({validation_result.success_rate:.1f}%)")
        
        # Log invalid POIs for user review
        invalid_tracker = get_global_tracker()
        for invalid_poi in validation_result.invalid_coordinates:
            invalid_tracker.add_invalid_point(
                invalid_poi['data'],
                f"Coordinate validation failed: {invalid_poi['error']}",
                "coordinate_validation"
            )


def generate_isochrones(poi_data: Dict[str, Any], travel_time: int, state_abbreviations: List[str]) -> gpd.GeoDataFrame:
    """
    Generate isochrones for the POI data.
    
    Args:
        poi_data: POI data dictionary
        travel_time: Travel time in minutes
        state_abbreviations: List of state abbreviations
        
    Returns:
        GeoDataFrame containing isochrones
    """
    from .isochrone import create_isochrones_from_poi_list
    from .progress import get_progress_bar
    
    print(f"\n=== Generating {travel_time}-Minute Isochrones ===")
    
    # Generate isochrones with progress tracking
    with get_progress_bar(total=len(poi_data['pois']), desc="🗺️  Generating Isochrones", unit="POI") as pbar:
        isochrone_gdf = create_isochrones_from_poi_list(
            poi_data['pois'],
            travel_time=travel_time,
            states=state_abbreviations,
            progress_callback=lambda: pbar.update(1)
        )
    
    if isochrone_gdf is None or isochrone_gdf.empty:
        raise ValueError("Failed to generate isochrones. This could be due to network issues or invalid POI locations.")
    
    print(f"Generated {len(isochrone_gdf)} isochrone(s)")
    return isochrone_gdf


def integrate_census_data(
    isochrone_gdf: gpd.GeoDataFrame,
    census_variables: List[str],
    api_key: Optional[str],
    state_abbreviations: List[str]
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, List[str]]:
    """
    Integrate census data with isochrones.
    
    Args:
        isochrone_gdf: Isochrone GeoDataFrame
        census_variables: List of census variables
        api_key: Census API key
        state_abbreviations: List of state abbreviations
        
    Returns:
        Tuple of (block_groups_gdf, census_data_gdf, census_codes)
    """
    from .census import get_streaming_census_manager
    from .util import census_code_to_name
    from .progress import get_progress_bar
    
    print(f"\n=== Integrating Census Data ===")
    
    # Convert any human-readable names to census codes
    census_codes = [normalize_census_variable(var) for var in census_variables]
    
    # Display human-readable names for requested census variables
    readable_names = get_readable_census_variables(census_codes)
    print(f"Requesting census data for: {', '.join(readable_names)}")
    
    # Get census manager
    census_manager = get_streaming_census_manager()
    
    # Get block groups that intersect with isochrones
    with get_progress_bar(total=len(state_abbreviations), desc="🏛️  Finding Block Groups", unit="state") as pbar:
        block_groups_gdf = census_manager.get_block_groups_for_isochrones(
            isochrone_gdf=isochrone_gdf,
            states=state_abbreviations,
            api_key=api_key
        )
        pbar.update(len(state_abbreviations))
    
    if block_groups_gdf is None or block_groups_gdf.empty:
        raise ValueError("No census block groups found intersecting with isochrones.")
    
    print(f"Found {len(block_groups_gdf)} intersecting census block groups")
    
    # Calculate travel distances in memory
    from .distance import add_travel_distances
    block_groups_with_distances = add_travel_distances(
        block_groups_gdf=block_groups_gdf,
        poi_data=poi_data
    )
    
    print(f"Calculated travel distances for {len(block_groups_with_distances)} block groups")
    
    # Create variable mapping for human-readable names
    variable_mapping = {code: census_code_to_name(code) for code in census_codes}
    
    # Fetch census data using streaming
    geoids = block_groups_with_distances['GEOID'].tolist()
    
    with get_progress_bar(total=len(geoids), desc="📊 Integrating Census Data", unit="block") as pbar:
        census_data = census_manager.get_census_data(
            geoids=geoids,
            variables=census_codes,
            api_key=api_key
        )
        pbar.update(len(geoids) // 2)
        
        # Merge census data with block groups
        census_data_gdf = block_groups_with_distances.copy()
        
        # Add census variables to the GeoDataFrame
        for _, row in census_data.iterrows():
            geoid = row['GEOID']
            var_code = row['variable_code']
            value = row['value']
            
            # Find matching block group and add the variable
            mask = census_data_gdf['GEOID'] == geoid
            if mask.any():
                census_data_gdf.loc[mask, var_code] = value
        
        pbar.update(len(geoids) // 2)
    
    # Apply variable mapping
    if variable_mapping:
        census_data_gdf = census_data_gdf.rename(columns=variable_mapping)
    
    # Set visualization attributes
    variables_for_viz = [var for var in census_codes if var != 'NAME']
    census_data_gdf.attrs['variables_for_visualization'] = variables_for_viz
    
    print(f"Retrieved census data for {len(census_data_gdf)} block groups")
    
    return block_groups_gdf, census_data_gdf, census_codes


def export_pipeline_outputs(
    census_data_gdf: gpd.GeoDataFrame,
    poi_data: Dict[str, Any],
    isochrone_gdf: gpd.GeoDataFrame,
    base_filename: str,
    travel_time: int,
    directories: Dict[str, str],
    export_csv: bool,
    export_maps: bool,
    use_interactive_maps: bool,
    census_codes: List[str]
) -> Dict[str, Any]:
    """
    Export pipeline outputs (CSV, maps, etc.).
    
    Args:
        census_data_gdf: Census data GeoDataFrame
        poi_data: POI data dictionary
        isochrone_gdf: Isochrone GeoDataFrame
        base_filename: Base filename for outputs
        travel_time: Travel time in minutes
        directories: Dictionary of output directories
        export_csv: Whether to export CSV
        export_maps: Whether to export maps
        use_interactive_maps: Whether to use interactive maps
        census_codes: List of census codes
        
    Returns:
        Dictionary of result files and metadata
    """
    from .export import export_census_data_to_csv
    from .visualization import generate_maps_for_variables
    from .core import convert_poi_to_geodataframe
    from .util import census_code_to_name
    from .progress import get_progress_bar
    from pathlib import Path
    
    result_files = {}
    export_count = 0
    
    # Export census data to CSV (optional)
    if export_csv:
        print("\n=== Exporting Census Data to CSV ===")
        
        csv_file = os.path.join(
            directories["csv"],
            f"{base_filename}_{travel_time}min_census_data.csv"
        )
        
        csv_output = export_census_data_to_csv(
            census_data=census_data_gdf,
            poi_data=poi_data,
            output_path=csv_file,
            base_filename=f"{base_filename}_{travel_time}min"
        )
        result_files["csv_data"] = csv_output
        print(f"Exported census data to CSV: {csv_output}")
        export_count += 1
    
    # Generate maps (optional)
    if export_maps:
        print("\n=== Generating Maps ===")
        
        # Get visualization variables
        if hasattr(census_data_gdf, 'attrs') and 'variables_for_visualization' in census_data_gdf.attrs:
            visualization_variables = census_data_gdf.attrs['variables_for_visualization']
        else:
            visualization_variables = [var for var in census_codes if var != 'NAME']
        
        # Transform census variable codes to mapped names for the map generator
        variable_mapping = {code: census_code_to_name(code) for code in census_codes}
        mapped_variables = []
        for var in get_progress_bar(visualization_variables, desc="Processing variables"):
            mapped_name = variable_mapping.get(var, var)
            mapped_variables.append(mapped_name)
        
        # Print what we're mapping in user-friendly language
        readable_var_names = [name.replace('_', ' ').title() for name in mapped_variables]
        print(f"Creating maps for: {', '.join(readable_var_names)}")
        
        # Prepare POI data for the map generator
        poi_data_for_map = None
        if poi_data and 'pois' in poi_data and len(poi_data['pois']) > 0:
            # Always use just the first POI for mapping
            first_poi = poi_data['pois'][0]
            poi_data_for_map = convert_poi_to_geodataframe([first_poi])
            print(f"Note: Only mapping the first POI: {first_poi.get('name', 'Unknown')}")

        # Determine which map backend to use
        use_plotly_maps = use_interactive_maps
        
        # Generate maps for each census variable
        map_files = generate_maps_for_variables(
            census_data_path=census_data_gdf,
            variables=mapped_variables,
            output_dir=directories["base"],
            basename=f"{base_filename}_{travel_time}min",
            isochrone_path=isochrone_gdf,
            poi_df=poi_data_for_map,
            use_panels=False,
            use_plotly=use_plotly_maps
        )
        result_files["maps"] = map_files
        
        if use_interactive_maps:
            print("Interactive maps displayed in Streamlit")
        else:
            print(f"Generated {len(map_files)} static maps")
        export_count += 1
    else:
        if not export_maps:
            print("\n=== Processing Complete ===")
            print("✅ Census data processed successfully!")
            print("📄 CSV export is the primary output - all intermediate files processed in memory for efficiency")
            if export_csv:
                print("💾 Use export_maps=True to generate visualization maps")
    
    return result_files


def generate_final_report(
    poi_data: Dict[str, Any],
    sampled_pois: bool,
    result_files: Dict[str, Any],
    base_filename: str,
    travel_time: int
) -> Dict[str, Any]:
    """
    Generate final pipeline report and summary.
    
    Args:
        poi_data: POI data dictionary
        sampled_pois: Whether POIs were sampled
        result_files: Dictionary of result files
        base_filename: Base filename
        travel_time: Travel time in minutes
        
    Returns:
        Final result dictionary
    """
    from .progress import get_progress_tracker
    
    # Print processing summary
    tracker = get_progress_tracker()
    tracker.print_summary()
    
    # Generate invalid data report if any issues were found
    invalid_tracker = get_global_tracker()
    invalid_summary = invalid_tracker.get_summary()
    if (invalid_summary['total_invalid_points'] > 0 or 
        invalid_summary['total_invalid_clusters'] > 0 or 
        invalid_summary['total_processing_errors'] > 0):
        
        print("\n=== Invalid Data Report ===")
        invalid_tracker.print_summary()
        
        # Save detailed invalid data report
        try:
            report_files = invalid_tracker.save_invalid_data_report(
                filename_prefix=f"{base_filename}_{travel_time}min_invalid_data"
            )
            print(f"📋 Detailed invalid data report saved to: {', '.join(report_files)}")
            result_files["invalid_data_reports"] = report_files
        except Exception as e:
            print(f"⚠️  Warning: Could not save invalid data report: {e}")
    
    # Build final result dictionary
    result = {
        "poi_data": poi_data,
        "interactive_maps_available": True  # Always true for Plotly
    }
    
    # Add CSV path if applicable
    if "csv_data" in result_files:
        result["csv_data"] = result_files["csv_data"]
    
    # Add maps if applicable
    if "maps" in result_files:
        result["maps"] = result_files["maps"]
    else:
        result["maps"] = []
    
    # Add sampling information if POIs were sampled
    if sampled_pois:
        result["sampled_pois"] = True
        result["original_poi_count"] = poi_data.get('metadata', {}).get('original_count', 0)
        result["sampled_poi_count"] = len(poi_data.get('pois', []))
    
    # Add invalid data reports if any were generated
    if "invalid_data_reports" in result_files:
        result["invalid_data_reports"] = result_files["invalid_data_reports"]
        result["invalid_data_summary"] = invalid_summary
    
    return result 