#!/usr/bin/env python3
"""
Map coordinator module for creating multiple maps based on a set of variables.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import geopandas as gpd

# Add the parent directory to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.util import CENSUS_VARIABLE_MAPPING
from .single_map import generate_map, generate_isochrone_map
from .panel_map import generate_paneled_isochrone_map, generate_paneled_census_map

def generate_maps_for_variables(
    census_data_path: str,
    variables: List[str],
    output_dir: str = "output/maps",
    basename: Optional[str] = None,
    isochrone_path: Optional[str] = None,
    include_isochrone_only_map: bool = True,
    poi_df: Optional[gpd.GeoDataFrame] = None,
    use_panels: bool = False,
    **kwargs
) -> List[str]:
    """
    Generate multiple maps for different census variables from the same data.
    
    Args:
        census_data_path: Path to the GeoJSON file with census data for block groups
        variables: List of Census API variables to visualize
        output_dir: Directory to save maps (default: output/maps)
        basename: Base filename to use for output files (default: derived from input file)
        isochrone_path: Optional path to isochrone GeoJSON to overlay on the maps
        include_isochrone_only_map: Whether to generate an isochrone-only map
        poi_df: Optional GeoDataFrame containing POI data
        use_panels: Whether to generate paneled maps (requires list inputs)
        **kwargs: Additional keyword arguments to pass to the map generation functions
        
    Returns:
        List of paths to the saved maps
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Derive basename from input file if not provided
    if basename is None:
        basename = Path(census_data_path).stem
    
    # Normalize variables (convert human-readable names to Census API codes if needed)
    normalized_variables = []
    for var in variables:
        if var.lower() in CENSUS_VARIABLE_MAPPING:
            normalized_variables.append(CENSUS_VARIABLE_MAPPING[var.lower()])
        else:
            normalized_variables.append(var)
    
    output_paths = []
    
    # Generate isochrone-only map if requested
    if include_isochrone_only_map and isochrone_path:
        isochrone_map_path = os.path.join(output_dir, f"{basename}_isochrone_map.png")
        isochrone_result = generate_isochrone_map(
            isochrone_path=isochrone_path,
            output_path=isochrone_map_path,
            poi_df=poi_df,
            **{k: v for k, v in kwargs.items() if k in ['title', 'basemap_provider', 'figsize', 'dpi']}
        )
        output_paths.append(isochrone_result)
    
    # Generate maps for each variable
    if use_panels:
        # When using panels, we expect lists of paths, not single paths
        if not isinstance(census_data_path, list):
            census_data_path = [census_data_path]
        
        if isochrone_path is not None and not isinstance(isochrone_path, list):
            isochrone_path = [isochrone_path] * len(census_data_path)
        
        if poi_df is not None and not isinstance(poi_df, list):
            poi_df = [poi_df] * len(census_data_path)
        
        # Generate a panel for each variable
        for variable in normalized_variables:
            output_path = os.path.join(output_dir, f"{basename}_{variable}_panel_map.png")
            result = generate_paneled_census_map(
                census_data_paths=census_data_path,
                variable=variable,
                output_path=output_path,
                isochrone_paths=isochrone_path,
                poi_dfs=poi_df,
                **{k: v for k, v in kwargs.items() if k in [
                    'title', 'colormap', 'basemap_provider', 'figsize', 'dpi', 'max_panels_per_figure'
                ]}
            )
            
            if isinstance(result, list):
                output_paths.extend(result)
            else:
                output_paths.append(result)
    else:
        # Standard approach with individual maps per variable
        for variable in normalized_variables:
            output_path = os.path.join(output_dir, f"{basename}_{variable}_map.png")
            result = generate_map(
                census_data_path=census_data_path,
                variable=variable,
                output_path=output_path,
                isochrone_path=isochrone_path,
                poi_df=poi_df,
                **{k: v for k, v in kwargs.items() if k in [
                    'title', 'colormap', 'basemap_provider', 'figsize', 'dpi', 'show_isochrone'
                ]}
            )
            output_paths.append(result)
    
    return output_paths 