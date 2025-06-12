"""
Core functionality for SocialMapper.

This module provides the main API entry point for SocialMapper, delegating
to the modular pipeline components for actual implementation.

The pipeline follows ETL best practices with clear separation of concerns:
- Extract: POI data from custom files or OpenStreetMap
- Transform: Generate isochrones, validate coordinates, integrate census data
- Load: Export to CSV, generate maps, create reports
"""

from typing import Dict, List, Optional, Any

# Import pipeline components
from .pipeline import (
    setup_pipeline_environment,
    extract_poi_data,
    validate_poi_coordinates,
    generate_isochrones,
    integrate_census_data,
    export_pipeline_outputs,
    generate_final_report,
    PipelineOrchestrator,
    PipelineConfig
)

# Import for backward compatibility
from .pipeline.helpers import convert_poi_to_geodataframe, setup_directory
from .pipeline.extraction import parse_custom_coordinates

# Check if RunConfig is available
try:
    from .config_models import RunConfig
except ImportError:
    RunConfig = None  # Fallback when model not available


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
    geographic_level: str = "block-group",
    census_variables: List[str] | None = None,
    api_key: Optional[str] = None,
    output_dir: str = "output",
    custom_coords_path: Optional[str] = None,
    export_csv: bool = True,
    export_maps: bool = False,
    export_isochrones: bool = False,
    use_interactive_maps: bool = True,
    map_backend: str = "plotly",
    name_field: Optional[str] = None,
    type_field: Optional[str] = None,
    max_poi_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full community mapping process using modular pipeline functions.
    
    This function maintains backward compatibility while using the new
    modular pipeline architecture internally.
    
    Args:
        run_config: Optional RunConfig object (takes precedence over other parameters)
        geocode_area: Area to search within (city/town name)
        state: State name or abbreviation
        city: City name (defaults to geocode_area if not provided)
        poi_type: Type of POI (e.g., 'amenity', 'leisure')
        poi_name: Name of POI (e.g., 'library', 'park') 
        additional_tags: Dictionary of additional tags to filter by
        travel_time: Travel time limit in minutes
        geographic_level: Geographic unit for analysis: 'block-group' or 'zcta'
        census_variables: List of census variables to retrieve
        api_key: Census API key
        output_dir: Output directory for all files
        custom_coords_path: Path to custom coordinates file
        export_csv: Boolean to control export of census data to CSV
        export_maps: Boolean to control generation of maps
        export_isochrones: Boolean to control export of isochrones
        use_interactive_maps: Boolean to control whether to use interactive maps (Streamlit)
        map_backend: Which map backend to use ('plotly')
        name_field: Field name to use for POI name from custom coordinates
        type_field: Field name to use for POI type from custom coordinates
        max_poi_count: Maximum number of POIs to process (if None, uses all POIs)
        
    Returns:
        Dictionary of output file paths and metadata
    """
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
    
    # Option 1: Use the new orchestrator for cleaner code
    # This provides better error handling and stage management
    config = PipelineConfig(
        geocode_area=geocode_area,
        state=state,
        city=city,
        poi_type=poi_type,
        poi_name=poi_name,
        additional_tags=additional_tags,
        custom_coords_path=custom_coords_path,
        name_field=name_field,
        type_field=type_field,
        max_poi_count=max_poi_count,
        travel_time=travel_time,
        geographic_level=geographic_level,
        census_variables=census_variables,
        api_key=api_key,
        output_dir=output_dir,
        export_csv=export_csv,
        export_maps=export_maps,
        export_isochrones=export_isochrones,
        use_interactive_maps=use_interactive_maps,
        map_backend=map_backend
    )
    
    orchestrator = PipelineOrchestrator(config)
    return orchestrator.run()
    
    # Option 2: Direct function calls (keeping original flow)
    # Uncomment below and comment out the orchestrator code above
    # to use the original sequential approach
    
    # # Phase 1: Setup Pipeline Environment
    # directories = setup_pipeline_environment(
    #     output_dir=output_dir,
    #     export_csv=export_csv,
    #     export_maps=export_maps,
    #     export_isochrones=export_isochrones
    # )
    # 
    # # Phase 2: Extract POI Data
    # poi_data, base_filename, state_abbreviations, sampled_pois = extract_poi_data(
    #     custom_coords_path=custom_coords_path,
    #     geocode_area=geocode_area,
    #     state=state,
    #     city=city,
    #     poi_type=poi_type,
    #     poi_name=poi_name,
    #     additional_tags=additional_tags,
    #     name_field=name_field,
    #     type_field=type_field,
    #     max_poi_count=max_poi_count
    # )
    # 
    # # Phase 3: Validate POI Coordinates
    # validate_poi_coordinates(poi_data)
    # 
    # # Phase 4: Generate Isochrones
    # isochrone_gdf = generate_isochrones(
    #     poi_data=poi_data,
    #     travel_time=travel_time,
    #     state_abbreviations=state_abbreviations
    # )
    # 
    # # Phase 5: Integrate Census Data
    # geographic_units_gdf, census_data_gdf, census_codes = integrate_census_data(
    #     isochrone_gdf=isochrone_gdf,
    #     census_variables=census_variables,
    #     api_key=api_key,
    #     poi_data=poi_data,
    #     geographic_level=geographic_level
    # )
    # 
    # # Phase 6: Export Pipeline Outputs
    # result_files = export_pipeline_outputs(
    #     census_data_gdf=census_data_gdf,
    #     poi_data=poi_data,
    #     isochrone_gdf=isochrone_gdf,
    #     base_filename=base_filename,
    #     travel_time=travel_time,
    #     directories=directories,
    #     export_csv=export_csv,
    #     export_maps=export_maps,
    #     use_interactive_maps=use_interactive_maps,
    #     census_codes=census_codes,
    #     geographic_level=geographic_level
    # )
    # 
    # # Phase 7: Generate Final Report and Return Results
    # result = generate_final_report(
    #     poi_data=poi_data,
    #     sampled_pois=sampled_pois,
    #     result_files=result_files,
    #     base_filename=base_filename,
    #     travel_time=travel_time
    # )
    # 
    # # Add the processed data to the result for backward compatibility
    # result.update({
    #     "isochrones": isochrone_gdf,
    #     "geographic_units": geographic_units_gdf,
    #     "block_groups": geographic_units_gdf,  # Keep for backward compatibility
    #     "census_data": census_data_gdf
    # })
    # 
    # return result


# Export the main function and key utilities for backward compatibility
__all__ = [
    'run_socialmapper',
    'parse_custom_coordinates',
    'convert_poi_to_geodataframe',
    'setup_directory'
]