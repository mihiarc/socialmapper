"""
Core functionality for SocialMapper.

This module contains the main functions for running the socialmapper pipeline
and handling configuration.
"""

import os
import json
import csv
import logging
from typing import Dict, List, Optional, Any
import geopandas as gpd
from shapely.geometry import Point
import random
from urllib.error import URLError

# Configure basic logging
logging.basicConfig(level=logging.CRITICAL, format="%(asctime)s - %(levelname)s - %(message)s")

# Check if PyArrow is available
try:
    import pyarrow
    USE_ARROW = True
except ImportError:
    USE_ARROW = False

# Check if RunConfig is available
try:
    from .config_models import RunConfig
except ImportError:
    RunConfig = None  # Fallback when model not available

# Import invalid data tracker
from .util.invalid_data_tracker import get_global_tracker, reset_global_tracker

def parse_custom_coordinates(file_path: str, name_field: str = None, type_field: str = None, preserve_original: bool = True) -> Dict:
    """
    Parse a custom coordinates file (JSON or CSV) into the POI format expected by the isochrone generator.
    
    Args:
        file_path: Path to the custom coordinates file
        name_field: Field name to use for the POI name (if different from 'name')
        type_field: Field name to use for the POI type (if different from 'type')
        preserve_original: Whether to preserve original properties in tags
        
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
                    
                    # Use user-specified field for name if provided
                    if name_field and name_field in item:
                        name = item.get(name_field)
                    else:
                        name = item.get('name', f"Custom POI {len(pois)}")
                    
                    # Use user-specified field for type if provided
                    poi_type = None
                    if type_field and type_field in item:
                        poi_type = item.get(type_field)
                    else:
                        poi_type = item.get('type', 'custom')
                    
                    # Create tags dict and preserve original properties if requested
                    tags = item.get('tags', {})
                    if preserve_original and 'original_properties' in item:
                        tags.update(item['original_properties'])
                    
                    poi = {
                        'id': item.get('id', f"custom_{len(pois)}"),
                        'name': name,
                        'type': poi_type,
                        'lat': lat,
                        'lon': lon,
                        'tags': tags
                    }
                    
                    # If preserve_original is True, keep all original properties
                    if preserve_original:
                        for key, value in item.items():
                            if key not in ['id', 'name', 'lat', 'lon', 'tags', 'type', 'state']:
                                poi['tags'][key] = value
                    
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
                    # Use user-specified field for name if provided
                    if name_field and name_field in row:
                        name = row.get(name_field)
                    else:
                        name = row.get('name', f"Custom POI {i}")
                    
                    # Use user-specified field for type if provided
                    poi_type = None
                    if type_field and type_field in row:
                        poi_type = row.get(type_field)
                    else:
                        poi_type = row.get('type', 'custom')
                    
                    poi = {
                        'id': row.get('id', f"custom_{i}"),
                        'name': name,
                        'type': poi_type,
                        'lat': lat,
                        'lon': lon,
                        'tags': {}
                    }
                    
                    # Add any additional columns as tags
                    for key, value in row.items():
                        if key not in ['id', 'name', 'lat', 'latitude', 'y', 'lon', 'lng', 'longitude', 'x', 'state', 'type']:
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

def setup_directory(output_dir: str = "output") -> str:
    """
    Create a single output directory.
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        The output directory path
    """
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

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
        
        # Check for type directly in the POI data first, then fallback to tags
        if 'type' in poi:
            types.append(poi.get('type'))
        else:
            types.append(poi.get('tags', {}).get('amenity', 'Unknown'))
    
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
    output_dir: str = "output",
    custom_coords_path: Optional[str] = None,
    export_csv: bool = True,
    export_maps: bool = False,
    export_isochrones: bool = False,
    use_interactive_maps: bool = True,
    name_field: Optional[str] = None,
    type_field: Optional[str] = None,
    max_poi_count: Optional[int] = None
) -> Dict[str, Any]:
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
        output_dir: Output directory for all files
        custom_coords_path: Path to custom coordinates file
        export_csv: Boolean to control export of census data to CSV
        export_maps: Boolean to control generation of maps
        export_isochrones: Boolean to control export of isochrones
        use_interactive_maps: Boolean to control whether to use interactive folium maps (Streamlit)
        name_field: Field name to use for POI name from custom coordinates
        type_field: Field name to use for POI type from custom coordinates
        max_poi_count: Maximum number of POIs to process (if None, uses all POIs)
        
    Returns:
        Dictionary of output file paths and metadata
    """
    # Import components here to avoid circular imports
    from .query import build_overpass_query, query_overpass, format_results, create_poi_config
    from .isochrone import create_isochrones_from_poi_list
    from .distance import add_travel_distances
    from .census import get_streaming_census_manager
    from .visualization import generate_maps_for_variables
    from .states import normalize_state, normalize_state_list, StateFormat
    from .util import census_code_to_name, normalize_census_variable, get_readable_census_variables
    from .export import export_census_data_to_csv
    from .progress import (
        get_progress_bar, _IN_STREAMLIT, 
        track_stage, ProcessingStage,
        get_progress_tracker
    )

    # Initialize streamlit_folium_available flag
    streamlit_folium_available = False
    if _IN_STREAMLIT and use_interactive_maps:
        try:
            import folium
            from streamlit_folium import folium_static
            streamlit_folium_available = True
            print("Using interactive Folium maps for Streamlit")
        except ImportError:
            streamlit_folium_available = False
            print("Warning: streamlit-folium package not available, falling back to static maps")

    # Start modern progress tracking
    tracker = get_progress_tracker()
    
    # Initialize invalid data tracker for this session
    reset_global_tracker(output_dir)
    invalid_tracker = get_global_tracker()
    
    # Quick setup without progress tracking (too fast to need it)
    setup_directory(output_dir)
    
    # Create subdirectories only for enabled outputs
    if export_csv:
        csv_dir = os.path.join(output_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)
    
    if export_maps:
        maps_dir = os.path.join(output_dir, "maps")
        os.makedirs(maps_dir, exist_ok=True)
    
    if export_isochrones:
        isochrones_dir = os.path.join(output_dir, "isochrones")
        os.makedirs(isochrones_dir, exist_ok=True)
    
    # Merge values from RunConfig if provided
    if run_config is not None and RunConfig is not None:
        custom_coords_path = run_config.custom_coords_path or custom_coords_path
        travel_time = run_config.travel_time if travel_time == 15 else travel_time
        census_variables = census_variables or run_config.census_variables
        api_key = run_config.api_key or api_key
        # Use output_dir from run_config if available
        if hasattr(run_config, 'output_dir') and run_config.output_dir:
            output_dir = run_config.output_dir

    if census_variables is None:
        census_variables = ["total_population"]
    
    # Convert any human-readable names to census codes
    census_codes = [normalize_census_variable(var) for var in census_variables]
    
    result_files = {}
    state_abbreviations = []
    sampled_pois = False
    
    # POI Processing (quick, no progress tracking needed)
    if custom_coords_path:
        print("\n=== Using Custom Coordinates (Skipping POI Query) ===")
        poi_data = parse_custom_coordinates(custom_coords_path, name_field, type_field)
        
        # Extract state information from the custom coordinates if available
        if 'metadata' in poi_data and 'states' in poi_data['metadata'] and poi_data['metadata']['states']:
            # Use normalize_state_list to handle different state formats
            state_abbreviations = normalize_state_list(poi_data['metadata']['states'], to_format=StateFormat.ABBREVIATION)
            
            if state_abbreviations:
                print(f"Using states from custom coordinates: {', '.join(state_abbreviations)}")
        
        # Set a name for the output file based on the custom coords file
        file_basename = os.path.basename(custom_coords_path)
        base_filename = f"custom_{os.path.splitext(file_basename)[0]}"
        
        # Apply POI limit if specified
        if max_poi_count and 'pois' in poi_data and len(poi_data['pois']) > max_poi_count:
            original_count = len(poi_data['pois'])
            # Sample a subset of POIs
            poi_data['pois'] = random.sample(poi_data['pois'], max_poi_count)
            # Update the POI count
            poi_data['poi_count'] = len(poi_data['pois'])
            print(f"Sampled {max_poi_count} POIs from {original_count} total POIs")
            sampled_pois = True
            # Add sampling info to metadata
            if 'metadata' not in poi_data:
                poi_data['metadata'] = {}
            poi_data['metadata']['sampled'] = True
            poi_data['metadata']['original_count'] = original_count
            
        result_files["poi_data"] = poi_data
        print(f"Using {len(poi_data['pois'])} custom coordinates from {custom_coords_path}")
        
    else:
        # Query POIs from OpenStreetMap (quick, no progress tracking needed)
        print("\n=== Querying Points of Interest ===")
            
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
            
            query = build_overpass_query(config)
            try:
                raw_results = query_overpass(query)
            except (URLError, OSError) as e:
                # Handle connection issues
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
            
            # Set a name for the output file based on the POI configuration
            poi_type_str = config.get("type", "poi")
            poi_name_str = config.get("name", "custom").replace(" ", "_").lower()
            location = config.get("geocode_area", "").replace(" ", "_").lower()
            
            # Create a base filename component for all outputs
            if location:
                base_filename = f"{location}_{poi_type_str}_{poi_name_str}"
            else:
                base_filename = f"{poi_type_str}_{poi_name_str}"
            
            # Apply POI limit if specified
            if max_poi_count and 'pois' in poi_data and len(poi_data['pois']) > max_poi_count:
                original_count = len(poi_data['pois'])
                # Sample a subset of POIs
                poi_data['pois'] = random.sample(poi_data['pois'], max_poi_count)
                # Update the POI count
                poi_data['poi_count'] = len(poi_data['pois'])
                print(f"Sampled {max_poi_count} POIs from {original_count} total POIs")
                sampled_pois = True
                # Add sampling info to metadata
                if 'metadata' not in poi_data:
                    poi_data['metadata'] = {}
                poi_data['metadata']['sampled'] = True
                poi_data['metadata']['original_count'] = original_count
            
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

    # Validate that we have POIs to process
    if not poi_data or 'pois' not in poi_data or not poi_data['pois']:
        raise ValueError("No POIs found to analyze. Please try different search criteria or check your input data.")

    # Validate POI coordinates using Pydantic before processing
    from .util.coordinate_validation import validate_poi_coordinates
    
    print("\n=== Validating POI Coordinates ===")
    
    # Extract POIs from poi_data for validation
    pois_to_validate = poi_data['pois'] if isinstance(poi_data, dict) else poi_data
    
    # Validate coordinates
    validation_result = validate_poi_coordinates(pois_to_validate)
    
    if validation_result.total_valid == 0:
        raise ValueError(f"No valid POI coordinates found. All {validation_result.total_input} POIs failed validation.")
    
    if validation_result.total_invalid > 0:
        print(f"⚠️  Coordinate Validation Warning: {validation_result.total_invalid} out of {validation_result.total_input} POIs have invalid coordinates")
        print(f"   Valid POIs: {validation_result.total_valid} ({validation_result.success_rate:.1f}%)")
        
        # Log invalid POIs for user review
        for invalid_poi in validation_result.invalid_coordinates:
            invalid_tracker.add_invalid_point(
                invalid_poi['data'],
                f"Coordinate validation failed: {invalid_poi['error']}",
                "input_validation"
            )
    
    # Update poi_data with only valid coordinates
    valid_pois = [poi.to_dict() for poi in validation_result.valid_coordinates]
    if isinstance(poi_data, dict):
        poi_data['pois'] = valid_pois
        # Update metadata if it exists
        if 'metadata' in poi_data:
            poi_data['metadata']['original_count'] = validation_result.total_input
            poi_data['metadata']['valid_count'] = validation_result.total_valid
            poi_data['metadata']['invalid_count'] = validation_result.total_invalid
    else:
        poi_data = valid_pois
    
    print(f"✅ Proceeding with {validation_result.total_valid} validated POI coordinates")

    # Phase 1: Isochrone Generation (with progress tracking)
    print("\n=== Generating Isochrones ===")
    isochrone_gdf = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir=output_dir,
        save_individual_files=export_isochrones,
        combine_results=True,
        use_parquet=True  # Use parquet format for internal processing
    )
    
    # If the function returned a file path, load the GeoDataFrame from it
    if isinstance(isochrone_gdf, str):
        try:
            isochrone_gdf = gpd.read_parquet(isochrone_gdf)
        except Exception as e:
            print(f"Warning: Error loading isochrones from parquet: {e}")
            # Alternative method using pyarrow
            try:
                import pyarrow.parquet as pq
                table = pq.read_table(isochrone_gdf)
                isochrone_gdf = gpd.GeoDataFrame.from_arrow(table)
            except Exception as e2:
                print(f"Critical error loading isochrones: {e2}")
                raise ValueError("Failed to load isochrone data")
    
    print(f"Generated isochrones for {len(isochrone_gdf)} locations")

    # Phase 2: Census Integration (with progress tracking)
    print("\n=== Integrating Census Data ===")
    
    # Process block groups in memory using new API
    census_manager = get_streaming_census_manager()
    
    # Determine states to search from POI data
    from .census import get_counties_from_pois
    counties = get_counties_from_pois(poi_data['pois'], include_neighbors=False)
    state_fips = list(set([county[:2] for county in counties]))
    
    # Progress bar 3: Finding census block groups
    with get_progress_bar(total=len(state_fips), desc="🏛️ Finding Census Block Groups", unit="state") as pbar:
        # Find intersecting block groups
        block_groups_gdf = census_manager.get_block_groups(state_fips)
        pbar.update(len(state_fips))
        
        # Filter to intersecting block groups
        from shapely.geometry import Point
        # Create a union of all isochrones for intersection testing
        isochrone_union = isochrone_gdf.geometry.union_all()
        intersecting_mask = block_groups_gdf.geometry.intersects(isochrone_union)
        block_groups_gdf = block_groups_gdf[intersecting_mask]
    
    print(f"Found {len(block_groups_gdf)} intersecting block groups")
    
    # Calculate travel distances in memory
    block_groups_with_distances = add_travel_distances(
        block_groups_gdf=block_groups_gdf,
        poi_data=poi_data
    )
    
    print(f"Calculated travel distances for {len(block_groups_with_distances)} block groups")
    
    # Create variable mapping for human-readable names
    variable_mapping = {code: census_code_to_name(code) for code in census_codes}
    
    # Display human-readable names for requested census variables
    readable_names = get_readable_census_variables(census_codes)
    print(f"Requesting census data for: {', '.join(readable_names)}")
    
    # Progress bar 4: Integrating census data
    geoids = block_groups_with_distances['GEOID'].tolist()
    
    with get_progress_bar(total=len(geoids), desc="📊 Integrating Census Data", unit="block") as pbar:
        # Fetch census data using streaming
        census_data = census_manager.get_census_data(
            geoids=geoids,
            variables=census_codes,
            api_key=api_key
        )
        pbar.update(len(geoids) // 2)  # Update halfway through fetch
        
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
        
        pbar.update(len(geoids) // 2)  # Complete the progress bar
    
    # Apply variable mapping
    if variable_mapping:
        census_data_gdf = census_data_gdf.rename(columns=variable_mapping)
    
    # Set visualization attributes
    variables_for_viz = [var for var in census_codes if var != 'NAME']
    census_data_gdf.attrs['variables_for_visualization'] = variables_for_viz
    
    print(f"Retrieved census data for {len(census_data_gdf)} block groups")

    # Export & Visualization (quick, no progress tracking needed)
    export_count = 0
    
    # Export census data to CSV (optional)
    if export_csv:
        print("\n=== Exporting Census Data to CSV ===")
        
        csv_dir = os.path.join(output_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)
        
        csv_file = os.path.join(
            csv_dir,
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
            # Fallback to filtering out known non-visualization variables
            visualization_variables = [var for var in census_codes if var != 'NAME']
        
        # Transform census variable codes to mapped names for the map generator
        mapped_variables = []
        for var in get_progress_bar(visualization_variables, desc="Processing variables"):
            # Use the mapped name if available, otherwise use the original code
            mapped_name = variable_mapping.get(var, var)
            mapped_variables.append(mapped_name)
        
        # Print what we're mapping in user-friendly language
        readable_var_names = [name.replace('_', ' ').title() for name in mapped_variables]
        print(f"Creating maps for: {', '.join(readable_var_names)}")
        
        # Prepare POI data for the map generator
        if poi_data:
            if 'pois' in poi_data and len(poi_data['pois']) > 0:
                # Always use just the first POI for mapping
                first_poi = poi_data['pois'][0]
                poi_data_for_map = convert_poi_to_geodataframe([first_poi])
                print(f"Note: Only mapping the first POI: {first_poi.get('name', 'Unknown')}")
            else:
                poi_data_for_map = None

        # Generate maps for each census variable
        map_files = generate_maps_for_variables(
            census_data_path=census_data_gdf,  # Always pass the GeoDataFrame directly
            variables=mapped_variables,
            output_dir=output_dir,
            basename=f"{base_filename}_{travel_time}min",
            isochrone_path=isochrone_gdf,  # Always pass the GeoDataFrame directly
            poi_df=poi_data_for_map,
            use_panels=False,
            use_folium=streamlit_folium_available and use_interactive_maps
        )
        result_files["maps"] = map_files
        
        # Flag to indicate if folium maps are available and being displayed
        result_files["folium_maps_available"] = streamlit_folium_available and use_interactive_maps
        
        if streamlit_folium_available and use_interactive_maps:
            print("Interactive maps displayed in Streamlit")
        else:
            print(f"Generated {len(map_files)} static maps")
        export_count += 1
    else:
        if not export_maps and not export_isochrones:
            print("\n=== Processing Complete ===")
            print("✅ Census data processed successfully!")
            print("📄 CSV export is the primary output - all intermediate files processed in memory for efficiency")
            if export_csv:
                print("💾 Use export_maps=True to generate visualization maps")
                print("💾 Use export_isochrones=True to save individual isochrone files")
        else:
            print("\n=== Skipping Map Generation (use export_maps=True to enable) ===")
    
    # Print processing summary
    tracker.print_summary()
    
    # Generate invalid data report if any issues were found
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
    
    # Return a dictionary of output paths and metadata
    result = {
        "poi_data": poi_data,
        "isochrones": isochrone_gdf,
        "block_groups": block_groups_gdf,
        "census_data": census_data_gdf,
        "maps": map_files if export_maps else [],
        "folium_maps_available": streamlit_folium_available and use_interactive_maps
    }
    
    # Add CSV path if applicable
    if export_csv and "csv_data" in result_files:
        result["csv_data"] = result_files["csv_data"]
    
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