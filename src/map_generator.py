#!/usr/bin/env python3
"""
Module to generate maps from census data for block groups that intersect with isochrones.
"""
import argparse
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from pathlib import Path
from typing import Optional, List

# Mapping of common names to Census API variable codes
CENSUS_VARIABLE_MAPPING = {
    'population': 'B01003_001E',
    'median_income': 'B19013_001E',
    'median_age': 'B01002_001E',
    'households': 'B11001_001E',
    'housing_units': 'B25001_001E',
    'median_home_value': 'B25077_001E'
}

def get_variable_label(variable: str) -> str:
    """Convert Census variable codes to readable labels"""
    reverse_mapping = {v: k.replace('_', ' ').title() for k, v in CENSUS_VARIABLE_MAPPING.items()}
    return reverse_mapping.get(variable, variable)

def generate_map(
    census_data_path: str,
    output_path: Optional[str] = None,
    variable: str = 'B01003_001E',  # Default to total population
    title: Optional[str] = None,
    colormap: str = 'RdPu',
    basemap_provider: str = 'OpenStreetMap.Mapnik',
    figsize: tuple = (12, 12),
    dpi: int = 300,
    output_dir: str = "output/maps",
    isochrone_path: Optional[str] = None,
    isochrone_only: bool = False  # New parameter to indicate isochrone-only maps
) -> str:
    """
    Generate a choropleth map for census data in block groups.
    
    Args:
        census_data_path: Path to the GeoJSON file with census data for block groups
        output_path: Path to save the output map (if not provided, will use output_dir)
        variable: Census variable to visualize (can be a Census API code like 'B01003_001E' or
                 a common name like 'population', see CENSUS_VARIABLE_MAPPING)
        title: Map title (defaults to a readable version of the variable name)
        colormap: Matplotlib colormap name
        basemap_provider: Contextily basemap provider
        figsize: Figure size (width, height) in inches
        dpi: Output image resolution
        output_dir: Directory to save maps (default: output/maps)
        isochrone_path: Optional path to isochrone GeoJSON to overlay on the map
        isochrone_only: If True, generate a map showing only isochrones without census data
        
    Returns:
        Path to the saved map
    """
    # Check if we're making an isochrone-only map
    if isochrone_only and isochrone_path:
        return generate_isochrone_map(
            isochrone_path=isochrone_path,
            output_path=output_path,
            title=title,
            basemap_provider=basemap_provider,
            figsize=figsize,
            dpi=dpi,
            output_dir=output_dir
        )
        
    # Check if variable is a common name and convert to Census API code if needed
    if variable.lower() in CENSUS_VARIABLE_MAPPING:
        variable = CENSUS_VARIABLE_MAPPING[variable.lower()]
    
    # Load the census data
    try:
        gdf = gpd.read_file(census_data_path)
    except Exception as e:
        raise ValueError(f"Error loading census data file: {e}")
    
    # Check if variable exists in the data
    if variable not in gdf.columns:
        available_vars = [col for col in gdf.columns if col not in ['geometry', 'GEOID', 'STATE', 'COUNTY', 'TRACT', 'BLKGRP']]
        raise ValueError(f"Variable '{variable}' not found in census data. Available variables: {available_vars}")
    
    # Ensure data is numeric
    gdf[variable] = pd.to_numeric(gdf[variable], errors='coerce')
    
    # Generate output path if not provided
    if output_path is None:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        input_name = Path(census_data_path).stem
        output_path = Path(f"{output_dir}/{input_name}_{variable}_map.png")
    else:
        output_path = Path(output_path)
        # Ensure output directory exists for explicit path too
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set default title if not provided
    if title is None:
        variable_label = get_variable_label(variable)
        title = f"{variable_label} by Census Block Group"
    
    # Reproject to Web Mercator for contextily basemap
    gdf = gdf.to_crs(epsg=3857)
    
    # Create a plot with a nice frame
    fig, ax = plt.subplots(figsize=figsize, facecolor='#f8f8f8')
    fig.tight_layout(pad=3)
    
    # Add a border to the figure
    fig.patch.set_linewidth(1)
    fig.patch.set_edgecolor('#dddddd')
    
    # Create bins for the choropleth
    min_val = gdf[variable].min()
    max_val = gdf[variable].max()
    
    # Round to appropriate precision based on magnitude
    magnitude = max(abs(min_val), abs(max_val))
    if magnitude >= 1000:
        # Round to nearest hundred
        rounding = -2
    elif magnitude >= 100:
        # Round to nearest ten
        rounding = -1
    else:
        # Round to units
        rounding = 0
    
    # Create 5 bins
    bins = np.linspace(min_val, max_val, 6)
    bins = np.round(bins, rounding)
    
    # Format labels based on magnitude
    if magnitude >= 1000:
        labels = [f'{int(bins[i]):,} - {int(bins[i+1]):,}' for i in range(len(bins)-1)]
    else:
        labels = [f'{bins[i]:.1f} - {bins[i+1]:.1f}' for i in range(len(bins)-1)]
    
    # Create a colormap and normalization
    norm = BoundaryNorm(bins, plt.get_cmap(colormap).N)
    
    # Plot the choropleth
    gdf.plot(
        column=variable,
        cmap=colormap,
        linewidth=0.5,
        edgecolor='white',
        legend=False,
        alpha=0.7,
        ax=ax,
        norm=norm
    )
    
    # Add isochrone boundary if provided
    if isochrone_path:
        try:
            # Determine the file type and read appropriately
            if isochrone_path.lower().endswith('.parquet'):
                isochrone = gpd.read_parquet(isochrone_path)
            else:
                isochrone = gpd.read_file(isochrone_path)
                
            # Ensure the CRS matches our map
            isochrone = isochrone.to_crs(gdf.crs)
            
            # Plot isochrone with a thick, distinctive border
            isochrone.boundary.plot(
                ax=ax,
                color='blue',
                linewidth=2.0,
                linestyle='-',
                alpha=0.7,
                label='Isochrone Boundary'
            )
            
            # Add the isochrone to the title if not custom title provided
            if title is None:
                # Try to get the travel time from the isochrone if available
                travel_time = None
                for col in isochrone.columns:
                    if 'time' in col.lower() or 'minute' in col.lower():
                        if not isochrone[col].empty:
                            travel_time = isochrone[col].iloc[0]
                            break
                
                variable_label = get_variable_label(variable)
                if travel_time:
                    title = f"{variable_label} within {travel_time}-minute Travel Time"
                else:
                    title = f"{variable_label} within Travel Time Area"
            
        except Exception as e:
            print(f"Warning: Could not load isochrone file: {e}")
    
    # Add basemap
    provider = getattr(ctx.providers, basemap_provider.split('.')[0])
    for component in basemap_provider.split('.')[1:]:
        provider = getattr(provider, component)
        
    ctx.add_basemap(
        ax,
        source=provider,
        crs=gdf.crs.to_string()
    )
    
    # Add margins to the map
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * 0.05  # 5% margin
    y_margin = (ylim[1] - ylim[0]) * 0.05  # 5% margin
    ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
    ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)
    
    # Create legend patches
    legend_handles = [
        Patch(
            facecolor=plt.get_cmap(colormap)(norm(bins[i])),
            edgecolor='white',
            label=labels[i]
        ) for i in range(len(labels))
    ]
    
    # Add isochrone to legend if it was displayed
    if isochrone_path and 'isochrone' in locals():
        isochrone_legend = Line2D([0], [0], color='blue', linewidth=2, linestyle='-',
                              label='Isochrone Boundary')
        legend_handles.append(isochrone_legend)
    
    # Add the legend below the map
    legend = ax.legend(
        handles=legend_handles,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.1),
        ncol=min(len(labels), 3),
        title=get_variable_label(variable),
        frameon=True,
        fontsize='medium',
        title_fontsize='large',
        framealpha=0.9,
        edgecolor='#cccccc'
    )
    legend.get_frame().set_linewidth(0.5)
    
    # Add title
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_axis_off()
    
    # Add a rectangular frame around the map area
    border_width = 2.0
    border_color = 'black'
    
    # Get the current axis limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # Draw rectangle border around the map
    rect = Rectangle(
        (xlim[0], ylim[0]),
        width=xlim[1]-xlim[0],
        height=ylim[1]-ylim[0],
        fill=False,
        edgecolor=border_color,
        linewidth=border_width,
        zorder=1000  # Ensure it's on top
    )
    ax.add_patch(rect)
    
    # Save the map
    plt.savefig(output_path, bbox_inches='tight', dpi=dpi)
    plt.close(fig)
    
    print(f"Map saved to {output_path}")
    return str(output_path)

def generate_isochrone_map(
    isochrone_path: str,
    output_path: Optional[str] = None,
    title: Optional[str] = None,
    basemap_provider: str = 'OpenStreetMap.Mapnik',
    figsize: tuple = (12, 12),
    dpi: int = 300,
    output_dir: str = "output/maps"
) -> str:
    """
    Generate a map showing just isochrones without census data.
    
    Args:
        isochrone_path: Path to isochrone GeoJSON file
        output_path: Path to save the output map (if not provided, will use output_dir)
        title: Map title (defaults to "Travel Time Isochrones")
        basemap_provider: Contextily basemap provider
        figsize: Figure size (width, height) in inches
        dpi: Output image resolution
        output_dir: Directory to save maps (default: output/maps)
        
    Returns:
        Path to the saved map
    """
    # Load the isochrone
    try:
        # Determine the file type and read appropriately
        if isochrone_path.lower().endswith('.parquet'):
            isochrone = gpd.read_parquet(isochrone_path)
        else:
            isochrone = gpd.read_file(isochrone_path)
    except Exception as e:
        raise ValueError(f"Error loading isochrone file: {e}")
        
    # Generate output path if not provided
    if output_path is None:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        input_name = Path(isochrone_path).stem
        output_path = Path(f"{output_dir}/{input_name}_isochrone_map.png")
    else:
        output_path = Path(output_path)
        # Ensure output directory exists for explicit path too
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set default title if not provided
    if title is None:
        # Try to get the travel time from the isochrone if available
        travel_time = None
        for col in isochrone.columns:
            if 'time' in col.lower() or 'minute' in col.lower():
                if not isochrone[col].empty:
                    travel_time = isochrone[col].iloc[0]
                    break
        
        if travel_time:
            title = f"{travel_time}-minute Travel Time Isochrones"
        else:
            title = "Travel Time Isochrones"
    
    # Reproject to Web Mercator for contextily basemap
    isochrone = isochrone.to_crs(epsg=3857)
    
    # Create a plot with a nice frame
    fig, ax = plt.subplots(figsize=figsize, facecolor='#f8f8f8')
    fig.tight_layout(pad=3)
    
    # Add a border to the figure
    fig.patch.set_linewidth(1)
    fig.patch.set_edgecolor('#dddddd')
    
    # Plot isochrone with a thick, distinctive border and filled area
    isochrone.plot(
        ax=ax,
        color='skyblue',
        alpha=0.4,
        edgecolor='blue',
        linewidth=2.0
    )
    
    # Add basemap
    provider = getattr(ctx.providers, basemap_provider.split('.')[0])
    for component in basemap_provider.split('.')[1:]:
        provider = getattr(provider, component)
        
    ctx.add_basemap(
        ax,
        source=provider,
        crs=isochrone.crs.to_string()
    )
    
    # Add margins to the map
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * 0.05  # 5% margin
    y_margin = (ylim[1] - ylim[0]) * 0.05  # 5% margin
    ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
    ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)
    
    # Create legend specifically for isochrones
    legend_handles = [
        Patch(
            facecolor='skyblue',
            edgecolor='blue',
            linewidth=2.0,
            alpha=0.4,
            label='Travel Time Area'
        )
    ]
    
    # Add the legend below the map
    legend = ax.legend(
        handles=legend_handles,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.1),
        frameon=True,
        fontsize='medium',
        framealpha=0.9,
        edgecolor='#cccccc'
    )
    legend.get_frame().set_linewidth(0.5)
    
    # Add title
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_axis_off()
    
    # Add a rectangular frame around the map area
    border_width = 2.0
    border_color = 'black'
    
    # Get the current axis limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # Draw rectangle border around the map
    rect = Rectangle(
        (xlim[0], ylim[0]),
        width=xlim[1]-xlim[0],
        height=ylim[1]-ylim[0],
        fill=False,
        edgecolor=border_color,
        linewidth=border_width,
        zorder=1000  # Ensure it's on top
    )
    ax.add_patch(rect)
    
    # Save the map
    plt.savefig(output_path, bbox_inches='tight', dpi=dpi)
    plt.close(fig)
    
    print(f"Isochrone map saved to {output_path}")
    return str(output_path)

def generate_maps_for_variables(
    census_data_path: str,
    variables: List[str],
    output_dir: str = "output/maps",
    basename: Optional[str] = None,
    isochrone_path: Optional[str] = None,
    include_isochrone_only_map: bool = True,  # New parameter to generate isochrone-only map
    **kwargs
) -> List[str]:
    """
    Generate maps for multiple census variables.
    
    Args:
        census_data_path: Path to the GeoJSON file with census data
        variables: List of census variables to visualize
        output_dir: Directory to save maps (default: output/maps)
        basename: Base filename (defaults to input filename)
        isochrone_path: Optional path to isochrone GeoJSON to overlay on the map
        include_isochrone_only_map: If True and isochrone_path is provided, also generate a map showing just isochrones
        **kwargs: Additional arguments to pass to generate_map()
        
    Returns:
        List of paths to saved maps
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    if basename is None:
        basename = Path(census_data_path).stem
    
    output_paths = []
    
    # Generate isochrone-only map if requested
    if include_isochrone_only_map and isochrone_path:
        try:
            isochrone_output_path = Path(output_dir) / f"{basename}_isochrone_map.png"
            saved_path = generate_map(
                census_data_path=census_data_path,  # This won't be used 
                output_path=str(isochrone_output_path),
                isochrone_path=isochrone_path,
                isochrone_only=True,  # Flag to generate isochrone-only map
                **kwargs
            )
            output_paths.append(saved_path)
        except Exception as e:
            print(f"Error generating isochrone-only map: {e}")
    
    # Generate maps for each census variable
    for variable in variables:
        # Note: Variables should already be filtered upstream in community_mapper.py
        output_path = Path(output_dir) / f"{basename}_{variable}_map.png"
        
        try:
            saved_path = generate_map(
                census_data_path=census_data_path,
                output_path=str(output_path),
                variable=variable,
                output_dir=output_dir,
                isochrone_path=isochrone_path,
                isochrone_only=False,  # Regular census variable map
                **kwargs
            )
            output_paths.append(saved_path)
        except Exception as e:
            print(f"Error generating map for variable '{variable}': {e}")
    
    return output_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate maps from census data for block groups")
    parser.add_argument("--census-data", help="Path to GeoJSON file with census data for block groups")
    parser.add_argument("--variable", default="B01003_001E", 
                      help="Census variable to visualize (can be a Census API code like 'B01003_001E' or a common name like 'population')")
    parser.add_argument("--output", help="Output PNG file path")
    parser.add_argument("--output-dir", default="output/maps", help="Directory to save maps (default: output/maps)")
    parser.add_argument("--title", help="Map title")
    parser.add_argument("--colormap", default="RdPu", help="Matplotlib colormap name")
    parser.add_argument("--basemap", default="OpenStreetMap.Mapnik", help="Contextily basemap provider")
    parser.add_argument("--dpi", type=int, default=300, help="Output image resolution")
    parser.add_argument("--isochrone", help="Path to isochrone GeoJSON file to overlay on the map")
    parser.add_argument("--isochrone-only", action="store_true", help="Generate map showing only isochrones without census data")
    
    args = parser.parse_args()
    
    # Check if this is an isochrone-only map request
    if args.isochrone_only and args.isochrone:
        if not args.census_data:
            # We can create isochrone-only map with a dummy census_data path
            args.census_data = "dummy_path"  # Not actually used

    # Ensure required parameters are provided
    if not args.isochrone_only and not args.census_data:
        parser.error("--census-data is required unless --isochrone-only is specified")
    
    if args.isochrone_only and not args.isochrone:
        parser.error("--isochrone is required when --isochrone-only is specified")
    
    generate_map(
        census_data_path=args.census_data,
        output_path=args.output,
        variable=args.variable,
        title=args.title,
        colormap=args.colormap,
        basemap_provider=args.basemap,
        dpi=args.dpi,
        output_dir=args.output_dir,
        isochrone_path=args.isochrone,
        isochrone_only=args.isochrone_only
    ) 