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
from matplotlib.patches import Patch, FancyBboxPatch
from matplotlib.lines import Line2D
from pathlib import Path
from typing import Optional, List
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.path as mpath
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap

# Mapping of common names to Census API variable codes
CENSUS_VARIABLE_MAPPING = {
    'population': 'B01003_001E',
    'median_income': 'B19013_001E',
    'median_age': 'B01002_001E',
    'households': 'B11001_001E',
    'housing_units': 'B25001_001E',
    'median_home_value': 'B25077_001E'
}

# Variable-specific color schemes
VARIABLE_COLORMAPS = {
    'B01003_001E': 'viridis',      # Population - blues/greens
    'B19013_001E': 'plasma',       # Income - yellows/purples
    'B25077_001E': 'inferno',      # Home value - oranges/reds
    'B01002_001E': 'cividis'       # Age - yellows/blues
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
    isochrone_only: bool = False,  # New parameter to indicate isochrone-only maps
    poi_df: Optional[gpd.GeoDataFrame] = None
) -> str:
    """
    Generate a choropleth map for census data in block groups.
    
    Args:
        census_data_path: Path to the GeoJSON file with census data for block groups
        output_path: Path to save the output map (if not provided, will use output_dir)
        variable: Census variable to visualize
        title: Map title (defaults to a readable version of the variable name)
        colormap: Matplotlib colormap name
        basemap_provider: Contextily basemap provider
        figsize: Figure size (width, height) in inches
        dpi: Output image resolution
        output_dir: Directory to save maps (default: output/maps)
        isochrone_path: Optional path to isochrone GeoJSON to overlay on the map
        isochrone_only: If True, generate a map showing only isochrones without census data
        poi_df: Optional GeoDataFrame containing POI data
        
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
            output_dir=output_dir,
            poi_df=poi_df
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
        # Try to map from Census API code to human-readable name
        variable_mapped = None
        for human_readable, census_code in CENSUS_VARIABLE_MAPPING.items():
            if census_code.lower() == variable.lower():
                # Try the human readable version (e.g., 'total_population')
                if human_readable in gdf.columns:
                    variable_mapped = human_readable
                    break
                
                # Try the title case version (e.g., 'Total Population')
                title_case = human_readable.replace('_', ' ').title()
                if title_case in gdf.columns:
                    variable_mapped = title_case
                    break
                
        if variable_mapped:
            variable = variable_mapped
        else:
            available_vars = [col for col in gdf.columns if col not in ['geometry', 'GEOID', 'STATE', 'COUNTY', 'TRACT', 'BLKGRP']]
            raise ValueError(f"Variable '{variable}' not found in census data. Available variables: {available_vars}")
    
    # Ensure data is numeric
    gdf[variable] = pd.to_numeric(gdf[variable], errors='coerce')
    
    # Add diagnostics
    print(f"Variable: {variable}")
    print(f"Data min: {gdf[variable].min()}, max: {gdf[variable].max()}")
    print(f"Data has NaN values: {gdf[variable].isna().any()}")
    
    # Replace any NaN values with the minimum to ensure proper rendering
    if gdf[variable].isna().any():
        min_val = gdf[variable].min()
        gdf[variable] = gdf[variable].fillna(min_val)
        print(f"Replaced NaN values with minimum: {min_val}")
    
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
    
    # Choose appropriate colormap for the variable
    if variable in VARIABLE_COLORMAPS:
        colormap = VARIABLE_COLORMAPS[variable]
        
    # Reproject to Web Mercator for contextily basemap
    gdf = gdf.to_crs(epsg=3857)
    
    # Create a plot with a nice frame
    fig, ax = plt.subplots(figsize=figsize, facecolor='#f8f8f8')
    fig.tight_layout(pad=3)
    
    # Add a border to the figure
    fig.patch.set_linewidth(1)
    fig.patch.set_edgecolor('#dddddd')
    
    # Get data range for coloring
    min_val = gdf[variable].min()
    max_val = gdf[variable].max()
    
    print(f"Variable: {variable}")
    print(f"Data min: {min_val}, max: {max_val}")
    print(f"Using colormap: {colormap}")
    
    # Create bins for labels
    bins = np.linspace(min_val, max_val, 6)
    
    # Format labels based on magnitude
    magnitude = max(abs(min_val), abs(max_val))
    if magnitude >= 1000:
        labels = [f'{int(bins[i]):,} - {int(bins[i+1]):,}' for i in range(len(bins)-1)]
    else:
        labels = [f'{bins[i]:.1f} - {bins[i+1]:.1f}' for i in range(len(bins)-1)]
        
    # Print debug info
    print(f"Created {len(labels)} labels for legend")
    
    # Simple direct coloring approach without using GeoPandas plot
    for idx, row in gdf.iterrows():
        # Normalize the value between 0 and 1 for colormap
        value = row[variable]
        norm_value = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
        # Clip to ensure in valid range
        norm_value = max(0, min(1, norm_value))
        
        # Get color from colormap and use it to fill polygon
        color = plt.get_cmap(colormap)(norm_value)
        
        # Handle MultiPolygon vs Polygon
        try:
            if row.geometry.geom_type == 'MultiPolygon':
                for polygon in row.geometry.geoms:
                    ax.fill(*polygon.exterior.xy, color=color, alpha=0.8, 
                         linewidth=0.7, edgecolor='#404040')
            else:
                ax.fill(*row.geometry.exterior.xy, color=color, alpha=0.8, 
                     linewidth=0.7, edgecolor='#404040')
        except Exception as e:
            print(f"Error filling polygon: {e}")
    
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
                color='#3366CC',     # More vibrant blue
                linewidth=2.5,       # Thicker line
                linestyle='-',
                alpha=0.8,
                label='15-min Travel Time',
                path_effects=[pe.Stroke(linewidth=4, foreground='white'), pe.Normal()]  # Add outline
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
        
    # Use a more muted basemap by default if not explicitly specified
    if basemap_provider == 'OpenStreetMap.Mapnik':
        # Use CartoDB Positron as a cleaner alternative
        provider = ctx.providers.CartoDB.Positron
        
    ctx.add_basemap(
        ax,
        source=provider,
        crs=gdf.crs.to_string(),
        alpha=0.7  # Reduce basemap intensity
    )
    
    # Add margins to the map
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * 0.05  # 5% margin
    y_margin = (ylim[1] - ylim[0]) * 0.05  # 5% margin
    ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
    ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)
    
    # Create legend patches
    legend_handles = []
    for i in range(len(labels)):
        # Calculate the appropriate norm value based on bin position
        norm_value = i / (len(labels))
        legend_handles.append(
            Patch(
                facecolor=plt.get_cmap(colormap)(norm_value),
                edgecolor='white',
                label=labels[i]
            )
        )
    
    # Add isochrone to legend if it was displayed
    if isochrone_path and 'isochrone' in locals():
        isochrone_legend = Line2D([0], [0], color='blue', linewidth=2, linestyle='-',
                              label='Isochrone Boundary')
        legend_handles.append(isochrone_legend)
    
    # Add the legend below the map
    legend = ax.legend(
        handles=legend_handles,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.15),  # Push down slightly
        ncol=min(len(labels), 3),
        title=get_variable_label(variable),
        frameon=True,
        fontsize=11,
        title_fontsize=13,
        framealpha=0.9,
        edgecolor='#888888'
    )
    legend.get_frame().set_linewidth(1.0)
    
    # Add title
    ax.set_title(title, fontsize=18, fontweight='bold', fontfamily='Helvetica Neue', 
               pad=20, color='#333333')
    ax.set_axis_off()
    
    # Add a more elegant border with rounded corners
    rect = FancyBboxPatch(
        (xlim[0], ylim[0]),
        width=xlim[1]-xlim[0],
        height=ylim[1]-ylim[0],
        boxstyle="round,pad=0",
        fill=False,
        edgecolor='#222222',
        linewidth=2.5,
        zorder=1000
    )
    ax.add_patch(rect)
    
    # Add scale bar
    ax.add_artist(ScaleBar(1, dimension='si-length', units='m', location='lower right'))
    
    # Add north arrow
    x, y = xlim[1] - x_margin/2, ylim[1] - y_margin/2
    ax.annotate('N', xy=(x, y), xytext=(x, y-5000),
               arrowprops=dict(facecolor='black', width=5, headwidth=15),
               ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Add POI markers on isochrone maps
    if poi_df is not None:
        for idx, row in poi_df.iterrows():
            ax.plot(row.geometry.x, row.geometry.y, 'o', color='red', 
                    markersize=10, markeredgecolor='black', markeredgewidth=1.5)
            ax.annotate(row['name'], xy=(row.geometry.x, row.geometry.y), 
                       xytext=(10, 10), textcoords="offset points",
                       fontsize=10, fontweight='bold', 
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Add attribution text
    fig.text(0.01, 0.01, 
            "Data: U.S. Census Bureau ACS 5-Year Estimates & OpenStreetMap",
            ha='left', va='bottom', fontsize=8, color='#666666')
    
    # Create gradient background
    gradient = np.linspace(0, 1, 100).reshape(-1, 1)
    gradient_cmap = LinearSegmentedColormap.from_list('', ['#f8f9fa', '#e9ecef'])
    ax_bg = fig.add_axes([0, 0, 1, 1], zorder=-1)
    ax_bg.imshow(gradient, cmap=gradient_cmap, interpolation='bicubic', aspect='auto')
    ax_bg.axis('off')
    
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
    output_dir: str = "output/maps",
    poi_df: Optional[gpd.GeoDataFrame] = None
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
        poi_df: Optional GeoDataFrame containing POI data
        
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
    
    # Plot isochrone with a thick, distinctive border
    isochrone.boundary.plot(
        ax=ax,
        color='#3366CC',     # More vibrant blue
        linewidth=2.5,       # Thicker line
        linestyle='-',
        alpha=0.8,
        label='15-min Travel Time',
        path_effects=[pe.Stroke(linewidth=4, foreground='white'), pe.Normal()]  # Add outline
    )
    
    # Add basemap
    provider = getattr(ctx.providers, basemap_provider.split('.')[0])
    for component in basemap_provider.split('.')[1:]:
        provider = getattr(provider, component)
        
    # Use a more muted basemap by default if not explicitly specified
    if basemap_provider == 'OpenStreetMap.Mapnik':
        # Use CartoDB Positron as a cleaner alternative
        provider = ctx.providers.CartoDB.Positron
        
    ctx.add_basemap(
        ax,
        source=provider,
        crs=isochrone.crs.to_string(),
        alpha=0.7  # Reduce basemap intensity
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
    ax.set_title(title, fontsize=18, fontweight='bold', fontfamily='Helvetica Neue', 
               pad=20, color='#333333')
    ax.set_axis_off()
    
    # Add a more elegant border with rounded corners
    rect = FancyBboxPatch(
        (xlim[0], ylim[0]),
        width=xlim[1]-xlim[0],
        height=ylim[1]-ylim[0],
        boxstyle="round,pad=0",
        fill=False,
        edgecolor='#222222',
        linewidth=2.5,
        zorder=1000
    )
    ax.add_patch(rect)
    
    # Add scale bar
    ax.add_artist(ScaleBar(1, dimension='si-length', units='m', location='lower right'))
    
    # Add north arrow
    x, y = xlim[1] - x_margin/2, ylim[1] - y_margin/2
    ax.annotate('N', xy=(x, y), xytext=(x, y-5000),
               arrowprops=dict(facecolor='black', width=5, headwidth=15),
               ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Add POI markers on isochrone maps
    if poi_df is not None:
        for idx, row in poi_df.iterrows():
            ax.plot(row.geometry.x, row.geometry.y, 'o', color='red', 
                    markersize=10, markeredgecolor='black', markeredgewidth=1.5)
            ax.annotate(row['name'], xy=(row.geometry.x, row.geometry.y), 
                       xytext=(10, 10), textcoords="offset points",
                       fontsize=10, fontweight='bold', 
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Add attribution text
    fig.text(0.01, 0.01, 
            "Data: U.S. Census Bureau ACS 5-Year Estimates & OpenStreetMap",
            ha='left', va='bottom', fontsize=8, color='#666666')
    
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
    poi_df: Optional[gpd.GeoDataFrame] = None,
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
        poi_df: Optional GeoDataFrame containing POI data
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
                poi_df=poi_df,
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
                poi_df=poi_df,
                **kwargs
            )
            output_paths.append(saved_path)
        except Exception as e:
            print(f"Error generating map for variable '{variable}': {e}")
    
    return output_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate maps from census data for block groups")
    parser.add_argument("--census-data", help="Path to GeoJSON file with census data for block groups")
    parser.add_argument("--variable", help="Census variable to visualize")
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