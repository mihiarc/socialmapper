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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    progress_callback: Optional[callable] = None,
    export_csv: bool = True,
    export_maps: bool = False,
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
        progress_callback: Callback function for progress updates
        export_csv: Boolean to control export of census data to CSV
        export_maps: Boolean to control generation of maps
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
    from .census import get_census_database, CensusDataManager
    from .visualization import generate_maps_for_variables
    from .states import normalize_state, normalize_state_list, StateFormat
    from .util import census_code_to_name, normalize_census_variable, get_readable_census_variables
    from .export import export_census_data_to_csv
    from .progress import get_progress_bar, _IN_STREAMLIT

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

    # Set up output directory
    setup_directory(output_dir)
    
    # Create subdirectories for different output types
    subdirs = ["isochrones", "block_groups", "census_data", "maps", "pois", "csv"]
    for subdir in subdirs:
        subdir_path = os.path.join(output_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
    
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
    sampled_pois = False  # Flag to indicate if POIs were sampled
    
    # Determine if we're using custom coordinates or querying POIs
    if custom_coords_path:
        # Skip Step 1: Use custom coordinates
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
    
    # Step 2: Generate isochrones (always needed for analysis)
    print("\n=== Step 2: Generating Isochrones ===")
    if progress_callback:
        progress_callback(2, "Downloading Road Networks")
    
    # Validate that we have POIs to process
    if not poi_data or 'pois' not in poi_data or not poi_data['pois']:
        raise ValueError("No POIs found to analyze. Please try different search criteria or check your input data.")
    
    # Always process in memory, no GeoJSON export
    isochrone_gdf = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir=output_dir,
        save_individual_files=False,
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
    
    # Step 3: Find intersecting block groups
    print("\n=== Step 3: Finding Intersecting Census Block Groups ===")
    if progress_callback:
        progress_callback(3, "Finding census block groups")
    
    # Process block groups in memory using new API
    db = get_census_database()
    
    # Determine states to search from POI data
    from .census import get_counties_from_pois
    counties = get_counties_from_pois(poi_data['pois'], include_neighbors=False)
    state_fips = list(set([county[0] for county in counties]))
    
    # Find intersecting block groups
    block_groups_gdf = db.find_intersecting_block_groups(
        geometry=isochrone_gdf,
        state_fips=state_fips,
        selection_mode="intersect"
    )
    
    print(f"Found {len(block_groups_gdf)} intersecting block groups")
    
    # Step 4: Calculate travel distances
    print("\n=== Step 4: Calculating Travel Distances ===")
    if progress_callback:
        progress_callback(4, "Calculating travel distances")
    
    # Calculate travel distances in memory
    block_groups_with_distances = add_travel_distances(
        block_groups_gdf=block_groups_gdf,
        poi_data=poi_data,
        output_path=None  # No file output
    )
    
    print(f"Calculated travel distances for {len(block_groups_with_distances)} block groups")
    
    # Step 5: Fetch census data
    print("\n=== Step 5: Fetching Census Data ===")
    if progress_callback:
        progress_callback(5, "Retrieving census data")
    
    # Create variable mapping for human-readable names
    variable_mapping = {code: census_code_to_name(code) for code in census_codes}
    
    # Display human-readable names for requested census variables
    readable_names = get_readable_census_variables(census_codes)
    print(f"Requesting census data for: {', '.join(readable_names)}")
    
    # Get census data in memory using new API
    data_manager = CensusDataManager(db)
    
    # Get GEOIDs from block groups
    geoids = block_groups_with_distances['GEOID'].tolist()
    
    # Fetch census data
    census_data = data_manager.get_or_fetch_census_data(
        geoids=geoids,
        variables=census_codes,
        api_key=api_key
    )
    
    # Create view and get as GeoDataFrame
    view_name = data_manager.create_census_view(geoids, census_codes)
    census_data_gdf = data_manager.get_view_as_geodataframe(view_name)
    
    # Apply variable mapping
    if variable_mapping:
        census_data_gdf = census_data_gdf.rename(columns=variable_mapping)
    
    # Set visualization attributes
    variables_for_viz = [var for var in census_codes if var != 'NAME']
    census_data_gdf.attrs['variables_for_visualization'] = variables_for_viz
    
    print(f"Retrieved census data for {len(census_data_gdf)} block groups")
    
    # Step 6: Export census data to CSV (optional)
    if export_csv:
        print("\n=== Step 6: Exporting Census Data to CSV ===")
        if progress_callback:
            progress_callback(6, "Exporting census data to CSV")
        
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
    
    # Step 7: Generate maps (optional)
    if export_maps:
        print("\n=== Step 7: Generating Maps ===")
        if progress_callback:
            progress_callback(7, "Creating maps")
        
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
    else:
        print("\n=== Skipping Map Generation (use --export-maps to enable) ===")
    
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
    
    return result 