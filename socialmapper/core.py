"""
Core functionality for SocialMapper.

This module contains the main functions for running the socialmapper pipeline
and handling configuration.
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional
import geopandas as gpd
from shapely.geometry import Point

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Check if RunConfig is available
try:
    from .config_models import RunConfig
except ImportError:
    RunConfig = None  # Fallback when model not available

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
    states_found = set()
    
    if file_extension == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Handle different possible JSON formats
        if isinstance(data, list):
            # List of POIs
            for item in data:
                # Check for required fields
                if ('lat' in item and 'lon' in item) or ('latitude' in item and 'longitude' in item):
                    # Extract lat/lon
                    lat = float(item.get('lat', item.get('latitude')))
                    lon = float(item.get('lon', item.get('longitude')))
                    
                    # State is no longer required
                    state = item.get('state')
                    if state:
                        states_found.add(state)
                    
                    poi = {
                        'id': item.get('id', f"custom_{len(pois)}"),
                        'name': item.get('name', f"Custom POI {len(pois)}"),
                        'lat': lat,
                        'lon': lon,
                        'tags': item.get('tags', {})
                    }
                    pois.append(poi)
                else:
                    print(f"Warning: Skipping item missing required coordinates: {item}")
        elif isinstance(data, dict) and 'pois' in data:
            pois = data['pois']
    
    elif file_extension == '.csv':
        # Use newline="" to ensure correct universal newline handling across platforms
        with open(file_path, 'r', newline='') as f:
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
                        if key not in ['id', 'name', 'lat', 'latitude', 'y', 'lon', 'lng', 'longitude', 'x', 'state']:
                            poi['tags'][key] = value
                    
                    pois.append(poi)
                else:
                    print(f"Warning: Skipping row {i+1} - missing required coordinates")
    
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Please provide a JSON or CSV file.")
    
    if not pois:
        raise ValueError(f"No valid coordinates found in {file_path}. Please check the file format.")
    
    return {
        'pois': pois,
        'metadata': {
            'source': 'custom',
            'count': len(pois),
            'file_path': file_path,
            'states': list(states_found)
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
        "maps": "output/maps",
        "csv": "output/csv"  # CSV output directory
    }
    
    for directory in dirs.values():
        os.makedirs(directory, exist_ok=True)
    
    return dirs

def convert_poi_to_geodataframe(poi_data_list):
    """
    Convert a list of POI dictionaries to a GeoDataFrame.
    
    Args:
        poi_data_list: List of POI dictionaries
        
    Returns:
        GeoDataFrame containing POI data
    """
    if not poi_data_list:
        return None
    
    # Extract coordinates and create Point geometries
    geometries = []
    names = []
    ids = []
    types = []
    
    for poi in poi_data_list:
        if 'lat' in poi and 'lon' in poi:
            lat = poi['lat']
            lon = poi['lon']
        elif 'geometry' in poi and 'coordinates' in poi['geometry']:
            # GeoJSON format
            coords = poi['geometry']['coordinates']
            lon, lat = coords[0], coords[1]
        else:
            continue
            
        geometries.append(Point(lon, lat))
        names.append(poi.get('name', poi.get('tags', {}).get('name', poi.get('id', 'Unknown'))))
        ids.append(poi.get('id', ''))
        types.append(poi.get('type', poi.get('tags', {}).get('amenity', 'Unknown')))
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame({
        'name': names,
        'id': ids,
        'type': types,
        'geometry': geometries
    }, crs="EPSG:4326")  # WGS84 is standard for GPS coordinates
    
    return gdf

def run_socialmapper(
    run_config: Optional[RunConfig] = None,
    *,
    geocode_area: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    poi_type: Optional[str] = None,
    poi_name: Optional[str] = None,
    additional_tags: Optional[Dict] = None,
    travel_time: int = 15,
    census_variables: List[str] | None = None,
    api_key: Optional[str] = None,
    output_dirs: Optional[Dict[str, str]] = None,
    custom_coords_path: Optional[str] = None,
    progress_callback: Optional[callable] = None,
    export: bool = True  # Control CSV export
) -> Dict[str, str]:
    """
    Run the full community mapping process.
    
    Args:
        run_config: Optional RunConfig object (takes precedence over other parameters)
        geocode_area: Area to search within (city/town name)
        state: State name or abbreviation
        city: City name (defaults to geocode_area if not provided)
        poi_type: Type of POI (e.g., 'amenity', 'leisure')
        poi_name: Name of POI (e.g., 'library', 'park') 
        additional_tags: Dictionary of additional tags to filter by
        travel_time: Travel time limit in minutes
        census_variables: List of census variables to retrieve
        api_key: Census API key
        output_dirs: Dictionary of output directories
        custom_coords_path: Path to custom coordinates file
        progress_callback: Callback function for progress updates
        export: Boolean to control export of census data to CSV
        
    Returns:
        Dictionary of output file paths
    """
    # Import components here to avoid circular imports
    from .query import build_overpass_query, query_overpass, format_results, create_poi_config
    from .isochrone import create_isochrones_from_poi_list
    from .blockgroups import isochrone_to_block_groups_by_county
    from .census_data import get_census_data_for_block_groups
    from .visualization import generate_maps_for_variables
    from .states import normalize_state, normalize_state_list, StateFormat
    from .util import census_code_to_name, normalize_census_variable
    from .export import export_census_data_to_csv
    from .progress import get_progress_bar

    # Set up output directories
    if not output_dirs:
        output_dirs = setup_directories()
    
    # Merge values from RunConfig if provided
    if run_config is not None and RunConfig is not None:
        custom_coords_path = run_config.custom_coords_path or custom_coords_path
        travel_time = run_config.travel_time if travel_time == 15 else travel_time
        census_variables = census_variables or run_config.census_variables
        api_key = run_config.api_key or api_key
        output_dirs = output_dirs or run_config.output_dirs

    if census_variables is None:
        census_variables = ["total_population"]
    
    # Convert any human-readable names to census codes
    census_codes = [normalize_census_variable(var) for var in census_variables]
    
    result_files = {}
    state_abbreviations = []
    
    # Determine if we're using custom coordinates or querying POIs
    if custom_coords_path:
        # Skip Step 1: Use custom coordinates
        print("\n=== Using Custom Coordinates (Skipping POI Query) ===")
        poi_data = parse_custom_coordinates(custom_coords_path)
        
        # Extract state information from the custom coordinates if available
        if 'metadata' in poi_data and 'states' in poi_data['metadata'] and poi_data['metadata']['states']:
            # Use normalize_state_list to handle different state formats
            state_abbreviations = normalize_state_list(poi_data['metadata']['states'], to_format=StateFormat.ABBREVIATION)
            
            if state_abbreviations:
                print(f"Using states from custom coordinates: {', '.join(state_abbreviations)}")
        
        # Set a name for the output file based on the custom coords file
        file_basename = os.path.basename(custom_coords_path)
        base_filename = f"custom_{os.path.splitext(file_basename)[0]}"
        
        result_files["poi_data"] = poi_data
        
        print(f"Using {len(poi_data['pois'])} custom coordinates from {custom_coords_path}")
        
    else:
        # Step 1: Query POIs
        print("\n=== Step 1: Querying Points of Interest ===")
        if progress_callback:
            progress_callback(1, "Querying Points of Interest")
            
        # Check if we have direct POI parameters
        if geocode_area and poi_type and poi_name:
            # Normalize state to abbreviation if provided
            state_abbr = normalize_state(state, to_format=StateFormat.ABBREVIATION) if state else None
            
            # Use direct parameters to create config
            config = create_poi_config(
                geocode_area=geocode_area,
                state=state_abbr,
                city=city or geocode_area,  # Default to geocode_area if city not provided
                poi_type=poi_type,
                poi_name=poi_name,
                additional_tags=additional_tags
            )
            print(f"Querying OpenStreetMap for: {geocode_area} - {poi_type} - {poi_name}")
        else:
            raise ValueError("POI parameters (geocode_area, poi_type, poi_name) must be provided")
            
        query = build_overpass_query(config)
        raw_results = query_overpass(query)
        poi_data = format_results(raw_results, config)
        
        # Set a name for the output file based on the POI configuration
        poi_type_str = config.get("type", "poi")
        poi_name_str = config.get("name", "custom").replace(" ", "_").lower()
        location = config.get("geocode_area", "").replace(" ", "_").lower()
        
        # Create a base filename component for all outputs
        if location:
            base_filename = f"{location}_{poi_type_str}_{poi_name_str}"
        else:
            base_filename = f"{poi_type_str}_{poi_name_str}"
        
        result_files["poi_data"] = poi_data
        
        print(f"Found {len(poi_data['pois'])} POIs")
        
        # Extract state from config if available
        state_name = config.get("state")
        if state_name:
            # Use normalize_state for more robust state handling
            state_abbr = normalize_state(state_name, to_format=StateFormat.ABBREVIATION)
            if state_abbr and state_abbr not in state_abbreviations:
                state_abbreviations.append(state_abbr)
                print(f"Using state from parameters: {state_name} ({state_abbr})")
    
    # Step 2: Generate isochrones
    print("\n=== Step 2: Generating Isochrones ===")
    if progress_callback:
        progress_callback(2, "Generating travel time areas")
        
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
    if progress_callback:
        progress_callback(3, "Finding census block groups")
        
    block_groups_file = os.path.join(
        output_dirs["block_groups"],
        f"{base_filename}_{travel_time}min_block_groups.geojson"
    )
    
    # Use county-based block group selection
    print("Using county-based block group selection...")
    block_groups = isochrone_to_block_groups_by_county(
        isochrone_path=combined_isochrone_file,
        poi_data=poi_data,
        output_path=block_groups_file,
        api_key=api_key
    )
    result_files["block_groups"] = block_groups_file
    
    # Step 4: Fetch census data for block groups
    print("\n=== Step 4: Fetching Census Data ===")
    if progress_callback:
        progress_callback(4, "Retrieving census data")
    
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
    
    # New step: Export census data to CSV
    if export:
        print("\n=== Step 4b: Exporting Census Data to CSV ===")
        if progress_callback:
            progress_callback(4, "Retrieving census data and exporting to CSV")
        
        csv_file = os.path.join(
            output_dirs["csv"],
            f"{base_filename}_{travel_time}min_census_data.csv"
        )
        
        csv_output = export_census_data_to_csv(
            census_data=census_data,
            poi_data=poi_data,
            output_path=csv_file,
            base_filename=f"{base_filename}_{travel_time}min"
        )
        result_files["csv_data"] = csv_output
        print(f"Exported census data to CSV: {csv_output}")
    
    # Step 5: Generate maps
    print("\n=== Step 5: Generating Maps ===")
    if progress_callback:
        progress_callback(5, "Creating maps")
    
    # Get visualization variables from the census data result
    if hasattr(census_data, 'attrs') and 'variables_for_visualization' in census_data.attrs:
        visualization_variables = census_data.attrs['variables_for_visualization']
    else:
        # Fallback to filtering out known non-visualization variables
        visualization_variables = [var for var in census_codes if var != 'NAME']
    
    # Transform census variable codes to their mapped names for the map generator
    mapped_variables = []
    for var in get_progress_bar(visualization_variables, desc="Processing variables"):
        # Use the mapped name if available, otherwise use the original code
        mapped_name = variable_mapping.get(var, var)
        mapped_variables.append(mapped_name)
    
    # Print what we're mapping in user-friendly language
    readable_var_names = [name.replace('_', ' ').title() for name in mapped_variables]
    print(f"Creating maps for: {', '.join(readable_var_names)}")
    
    # Check if we're dealing with multiple locations spread across states
    use_panels = False
    poi_data_for_map = None
    
    if isinstance(census_data_file, list) and len(census_data_file) > 1:
        # If we have multiple census data files, use panels
        use_panels = True
        
    elif poi_data is not None and 'pois' in poi_data and len(poi_data['pois']) > 1:
        # If we have multiple POIs, check if they're in different states
        # Check if any POIs have a 'state' field
        states = [poi.get('state') for poi in poi_data['pois'] if 'state' in poi]
        if len(states) > 1 and len(set(states)) > 1:
            use_panels = True
            # Convert to list if not already
            if isinstance(census_data_file, str):
                census_data_file = [census_data_file]
            if isinstance(combined_isochrone_file, str):
                combined_isochrone_file = [combined_isochrone_file]
    
    # Prepare POI data for the map generator
    if poi_data:
        if use_panels and 'pois' in poi_data:
            # When using panels, prepare individual POI dicts
            poi_data_list = poi_data['pois']
            # Convert the POI list to a list of GeoDataFrames for panel maps
            if isinstance(poi_data_list, list):
                poi_data_for_map = [convert_poi_to_geodataframe([poi]) for poi in get_progress_bar(poi_data_list, desc="Processing POIs")]
            else:
                poi_data_for_map = convert_poi_to_geodataframe([poi_data_list])
        else:
            # For single map, convert the entire POI list to one GeoDataFrame
            poi_data_for_map = convert_poi_to_geodataframe(poi_data.get('pois', []))

    # Fix for isochrone path handling when it's a list
    isochrone_path_for_map = combined_isochrone_file
    if isinstance(combined_isochrone_file, list) and not use_panels:
        # If we have a list of isochrones but aren't using panels,
        # just use the first isochrone file to avoid the error
        isochrone_path_for_map = combined_isochrone_file[0]

    # Generate maps for each census variable using the mapped names
    map_files = generate_maps_for_variables(
        census_data_path=census_data_file,
        variables=mapped_variables,
        output_dir=output_dirs["maps"],
        basename=f"{base_filename}_{travel_time}min",
        isochrone_path=isochrone_path_for_map,
        poi_df=poi_data_for_map,
        use_panels=use_panels
    )
    result_files["maps"] = map_files
    
    print(f"Generated {len(map_files)} maps")
    
    return result_files 