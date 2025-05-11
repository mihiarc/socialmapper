#!/usr/bin/env python3
"""
Functions for generating individual maps (non-paneled).
"""
import geopandas as gpd
import matplotlib
import sys
import os
from typing import Optional, Union, List

# Set the backend for matplotlib based on environment
try:
    # Import our environment detection from progress.py
    from socialmapper.progress import _IN_STREAMLIT
    
    if not _IN_STREAMLIT:
        # We're not in a Streamlit environment, use a non-interactive backend
        matplotlib.use('Agg')
except ImportError:
    # Progress module not available, definitely use a non-interactive backend
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, FancyBboxPatch
from matplotlib.lines import Line2D
from pathlib import Path
from socialmapper.util import CENSUS_VARIABLE_MAPPING, VARIABLE_COLORMAPS
from .map_utils import get_variable_label
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap

# Add the parent directory to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def generate_map(
    census_data_path: Union[str, gpd.GeoDataFrame],
    variable: str,
    output_path: Optional[str] = None,
    title: Optional[str] = None,
    colormap: str = 'GnBu',
    basemap_provider: str = 'OpenStreetMap.Mapnik',
    figsize: tuple = (12, 12),
    dpi: int = 300,
    output_dir: str = "output/maps",
    isochrone_path: Optional[Union[str, gpd.GeoDataFrame]] = None,
    isochrone_only: bool = False,  # Parameter to indicate isochrone-only maps
    poi_df: Optional[gpd.GeoDataFrame] = None,
    show_isochrone: bool = False
) -> str:
    """
    Generate a choropleth map for census data in block groups.
    
    Args:
        census_data_path: Path to the GeoJSON file or GeoDataFrame with census data for block groups
        output_path: Path to save the output map (if not provided, will use output_dir)
        variable: Census variable to visualize
        title: Map title (defaults to a readable version of the variable name)
        colormap: Matplotlib colormap name
        basemap_provider: Contextily basemap provider
        figsize: Figure size (width, height) in inches
        dpi: Output image resolution
        output_dir: Directory to save maps (default: output/maps)
        isochrone_path: Optional path to isochrone GeoJSON/GeoDataFrame to overlay on the map
        isochrone_only: If True, generate a map showing only isochrones without census data
        poi_df: Optional GeoDataFrame containing POI data
        show_isochrone: Whether to display the isochrone boundary on the map
        
    Returns:
        Path to the saved map
    """
    # Check if we're making an isochrone-only map
    if isochrone_only and isochrone_path is not None:
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
    if isinstance(census_data_path, gpd.GeoDataFrame):
        gdf = census_data_path
    else:
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
    
    # Replace extreme negative values (likely invalid data) with NaN
    # Census data like income and housing values shouldn't have extremely negative values
    if variable in ['B19013_001E', 'B25077_001E', 'median_income', 'median_household_income', 'median_home_value']:
        # Replace extreme negative values (common placeholder for missing data) with NaN
        gdf.loc[gdf[variable] < 0, variable] = np.nan
    
    # Replace any NaN values with the minimum positive value to ensure proper rendering
    if gdf[variable].isna().any():
        # For variables that should be positive, find the minimum positive value
        if variable in ['B19013_001E', 'B25077_001E', 'median_income', 'median_household_income', 'median_home_value']:
            positive_values = gdf.loc[gdf[variable] > 0, variable]
            if len(positive_values) > 0:
                min_positive = positive_values.min()
                print(f"Replaced NaN values with minimum positive value: {min_positive}")
                gdf[variable] = gdf[variable].fillna(min_positive)
            else:
                # If no positive values, use a sensible default like 0
                print(f"No positive values found, replacing NaN with 0")
                gdf[variable] = gdf[variable].fillna(0)
        else:
            # For other variables, use the overall minimum
            min_val = gdf[variable].min()
            print(f"Replaced NaN values with minimum: {min_val}")
            gdf[variable] = gdf[variable].fillna(min_val)
    
    # Generate output path if not provided
    if output_path is None:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create a filename based on the variable
        if isinstance(census_data_path, str):
            input_name = Path(census_data_path).stem
        else:
            input_name = "census_data"
        output_path = Path(f"{output_dir}/{input_name}_{variable}_map.png")
    else:
        output_path = Path(output_path)
        # Ensure output directory exists for explicit path too
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set default title if not provided
    if title is None:
        variable_label = get_variable_label(variable)
        
        # Add isochrone information to title if available
        if isochrone_path is not None:
            # Extract POI info from isochrone file name
            if isinstance(isochrone_path, str):
                isochrone_file = Path(isochrone_path).stem
                parts = isochrone_file.split('_')
                location_name = None
                poi_name = None
                travel_time = None
                
                if len(parts) >= 3:
                    if 'amenity' in isochrone_file:
                        # Format typically: location_amenity_type_time
                        location_name = parts[0].title()
                        poi_type = parts[2].replace('-', ' ').title()
                        poi_name = f"{poi_type}"
                
                # Try to extract travel time from filename
                if 'min' in isochrone_file:
                    for part in parts:
                        if 'min' in part:
                            try:
                                travel_time = int(part.replace('min', ''))
                            except ValueError:
                                pass
            else:
                # For GeoDataFrame, try to get travel time from data
                travel_time = None
                if 'travel_time_minutes' in isochrone_path.columns:
                    if not isochrone_path['travel_time_minutes'].empty:
                        travel_time = isochrone_path['travel_time_minutes'].iloc[0]
                
                # Try to get POI info
                location_name = None
                poi_name = None
                if 'poi_name' in isochrone_path.columns and not isochrone_path['poi_name'].empty:
                    poi_name = isochrone_path['poi_name'].iloc[0]
                            
            # Try to get travel time from isochrone data if the file is loaded
            if 'isochrone' in locals():
                for col in isochrone.columns:
                    if 'time' in col.lower() or 'minute' in col.lower():
                        if not isochrone[col].empty:
                            travel_time = isochrone[col].iloc[0]
                            break
            
            # Construct a more descriptive title
            if travel_time and poi_name and location_name:
                display_title = f"{variable_label} Within {travel_time}-Minute Travel of {location_name} {poi_name}"
            elif travel_time and poi_name:
                display_title = f"{variable_label} Within {travel_time}-Minute Travel of {poi_name}"
            elif travel_time:
                display_title = f"{variable_label} Within {travel_time}-Minute Travel Time"
            else:
                display_title = f"{variable_label} Within Accessible Area"
        else:
            display_title = f"{variable_label} by Census Block Group"
    
    # Choose appropriate colormap for the variable
    if variable in VARIABLE_COLORMAPS:
        colormap = VARIABLE_COLORMAPS[variable]
        
    # Reproject to Web Mercator for contextily basemap
    gdf = gdf.to_crs(epsg=3857)
    
    # Create a plot with a nice frame
    fig, ax = plt.subplots(figsize=figsize, facecolor='#f8f8f8')
    fig.tight_layout(pad=3)
    
    # Get data range for coloring
    min_val = gdf[variable].min()
    max_val = gdf[variable].max()
    
    # Create bins for labels
    bins = np.linspace(min_val, max_val, 6)
    
    # Format labels based on magnitude
    magnitude = max(abs(min_val), abs(max_val))
    if magnitude >= 1000:
        labels = [f'{int(bins[i]):,} - {int(bins[i+1]):,}' for i in range(len(bins)-1)]
    else:
        labels = [f'{bins[i]:.1f} - {bins[i+1]:.1f}' for i in range(len(bins)-1)]
    
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
    
    # Add isochrone boundary if provided and if show_isochrone is True
    if isochrone_path is not None and show_isochrone:
        try:
            # Determine the file type and read appropriately
            if isinstance(isochrone_path, str):
                if isochrone_path.lower().endswith('.parquet'):
                    isochrone = gpd.read_parquet(isochrone_path)
                else:
                    isochrone = gpd.read_file(isochrone_path)
            else:
                # isochrone_path is already a GeoDataFrame
                isochrone = isochrone_path
                
            # Ensure the CRS matches our map
            isochrone = isochrone.to_crs(gdf.crs)
            
            # Plot isochrone with a thick, distinctive border
            isochrone.boundary.plot(
                ax=ax,
                color='#3366CC',     # More vibrant blue
                linewidth=2.5,       # Thicker line
                linestyle='-',
                alpha=0.8,
                label=f"{travel_time}-min Travel Time",
                path_effects=[pe.Stroke(linewidth=4, foreground='white'), pe.Normal()]
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
        crs=gdf.crs.to_string(),
        alpha=0.5
    )
    
    # Add margins to the map
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * 0.05
    y_margin = (ylim[1] - ylim[0]) * 0.05
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
    if isochrone_path is not None and show_isochrone and 'isochrone' in locals():
        isochrone_legend = Line2D([0], [0], color='blue', linewidth=2, linestyle='-',
                              label=f"{travel_time}-min Isochrone")
        legend_handles.append(isochrone_legend)
    
    # Add the legend below the map with adjusted size and position
    legend = ax.legend(
        handles=legend_handles,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.05),
        ncol=min(len(labels), 5),
        title=f"{variable_label} by Block Group",
        frameon=True,
        fontsize=14,                  
        title_fontsize=16,
        framealpha=0.9,
        edgecolor='#888888'
    )
    legend.get_frame().set_linewidth(1.0)
    
    # Add title
    if title is None:
        variable_label = get_variable_label(variable)
        
        # Add isochrone information to title if available
        if isochrone_path is not None:
            # Extract POI info from isochrone file name
            if isinstance(isochrone_path, str):
                isochrone_file = Path(isochrone_path).stem
                parts = isochrone_file.split('_')
                location_name = None
                poi_name = None
                travel_time = None
                
                if len(parts) >= 3:
                    if 'amenity' in isochrone_file:
                        # Format typically: location_amenity_type_time
                        location_name = parts[0].title()
                        poi_type = parts[2].replace('-', ' ').title()
                        poi_name = f"{poi_type}"
                
                # Try to extract travel time from filename
                if 'min' in isochrone_file:
                    for part in parts:
                        if 'min' in part:
                            try:
                                travel_time = int(part.replace('min', ''))
                            except ValueError:
                                pass
            else:
                # For GeoDataFrame, try to get travel time from data
                travel_time = None
                if 'travel_time_minutes' in isochrone_path.columns:
                    if not isochrone_path['travel_time_minutes'].empty:
                        travel_time = isochrone_path['travel_time_minutes'].iloc[0]
                
                # Try to get POI info
                location_name = None
                poi_name = None
                if 'poi_name' in isochrone_path.columns and not isochrone_path['poi_name'].empty:
                    poi_name = isochrone_path['poi_name'].iloc[0]
                            
            # Try to get travel time from isochrone data if the file is loaded
            if 'isochrone' in locals():
                for col in isochrone.columns:
                    if 'time' in col.lower() or 'minute' in col.lower():
                        if not isochrone[col].empty:
                            travel_time = isochrone[col].iloc[0]
                            break
            
            # Construct a more descriptive title
            if travel_time and poi_name and location_name:
                display_title = f"{variable_label} Within {travel_time}-Minute Travel of {location_name} {poi_name}"
            elif travel_time and poi_name:
                display_title = f"{variable_label} Within {travel_time}-Minute Travel of {poi_name}"
            elif travel_time:
                display_title = f"{variable_label} Within {travel_time}-Minute Travel Time"
            else:
                display_title = f"{variable_label} Within Accessible Area"
        else:
            display_title = f"{variable_label} by Census Block Group"
    else:
        display_title = title
        
    ax.set_title(display_title, fontsize=28, fontweight='bold', fontfamily='Helvetica Neue', 
               pad=20, color='#333333')
    ax.set_axis_off()
    
    # Add scale bar
    ax.add_artist(ScaleBar(1, dimension='si-length', units='m', location='lower right', rotation='horizontal-only'))
    
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
    isochrone_path: Union[str, gpd.GeoDataFrame],
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
        isochrone_path: Path to isochrone GeoJSON file or GeoDataFrame
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
    if isinstance(isochrone_path, gpd.GeoDataFrame):
        isochrone = isochrone_path
    else:
        try:
            # Determine the file type and read appropriately
            if isinstance(isochrone_path, str):
                if isochrone_path.lower().endswith('.parquet'):
                    isochrone = gpd.read_parquet(isochrone_path)
                else:
                    isochrone = gpd.read_file(isochrone_path)
            else:
                # Must be a GeoDataFrame
                isochrone = isochrone_path
        except Exception as e:
            raise ValueError(f"Error loading isochrone file: {e}")
        
    # Generate output path if not provided
    if output_path is None:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create a filename
        if isinstance(isochrone_path, str):
            input_name = Path(isochrone_path).stem
        else:
            input_name = "isochrone"
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
    ax.add_artist(ScaleBar(1, dimension='si-length', units='m', location='lower right', rotation='horizontal-only'))
    
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