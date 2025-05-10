#!/usr/bin/env python3
"""
Functions for creating paneled maps with multiple locations.
"""
import os
import math
import warnings
import geopandas as gpd
import matplotlib

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
import contextily as cx
import numpy as np
import pandas as pd
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.patches import Patch
from socialmapper.util import CENSUS_VARIABLE_MAPPING, add_north_arrow
from socialmapper.visualization.map_utils import get_variable_label, calculate_optimal_bins, apply_quantile_classification, choose_appropriate_colormap

def generate_paneled_isochrone_map(
    isochrone_paths,
    output_path=None,
    title=None,
    basemap_provider='OpenStreetMap.Mapnik',
    figsize=(15, 10),
    dpi=150,
    output_dir='output/maps',
    poi_dfs=None,
    max_panels_per_figure=6
):
    """
    Generate a paneled map showing multiple isochrones.
    
    Args:
        isochrone_paths (list): List of paths to GeoJSON isochrone files
        output_path (str, optional): Path to save the output map. If None, will be auto-generated
        title (str, optional): Title for the map
        basemap_provider (str, optional): Basemap provider for contextily
        figsize (tuple, optional): Figure size in inches (width, height)
        dpi (int, optional): DPI for the figure
        output_dir (str, optional): Directory to save the output map
        poi_dfs (list, optional): List of GeoDataFrames with POIs to plot on the maps
        max_panels_per_figure (int, optional): Maximum number of panels per figure
        
    Returns:
        str: Path to the saved map
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output path if not provided
    if output_path is None:
        # Extract common prefix from isochrone paths
        paths = [os.path.basename(p) for p in isochrone_paths]
        common_prefix = os.path.commonprefix(paths)
        if not common_prefix:
            common_prefix = "paneled_isochrones"
        output_path = os.path.join(output_dir, f"{common_prefix}_map.png")
    
    # Calculate number of figures needed
    num_figures = math.ceil(len(isochrone_paths) / max_panels_per_figure)
    saved_paths = []
    
    # Loop through figures
    for fig_idx in range(num_figures):
        start_idx = fig_idx * max_panels_per_figure
        end_idx = min((fig_idx + 1) * max_panels_per_figure, len(isochrone_paths))
        curr_paths = isochrone_paths[start_idx:end_idx]
        
        # Calculate grid dimensions
        num_panels = len(curr_paths)
        if num_panels <= 2:
            nrows, ncols = 1, num_panels
        elif num_panels <= 4:
            nrows, ncols = 2, 2
        else:
            nrows = math.ceil(num_panels / 3)
            ncols = min(3, math.ceil(num_panels / nrows))
        
        # Create figure
        fig, axes = plt.subplots(nrows, ncols, figsize=figsize, constrained_layout=True)
        
        # If there's only one panel, axes is not a list
        if num_panels == 1:
            axes = np.array([axes])
        
        # Flatten axes for easier iteration
        axes = axes.flatten()
        
        # Set figure title if provided
        if title and num_figures == 1:
            fig.suptitle(title, fontsize=16)
        elif title:
            fig.suptitle(f"{title} (Part {fig_idx+1}/{num_figures})", fontsize=16)
        
        # Iterate through isochrone paths and axes
        for i, (iso_path, ax) in enumerate(zip(curr_paths, axes)):
            try:
                # Read isochrone data
                isochrone = gpd.read_file(iso_path)
                
                # Skip if empty
                if isochrone.empty:
                    ax.set_axis_off()
                    ax.text(0.5, 0.5, f"No data for {os.path.basename(iso_path)}", 
                            horizontalalignment='center', verticalalignment='center')
                    continue
                
                # Ensure CRS is in Web Mercator for basemap
                if isochrone.crs is None:
                    warnings.warn(f"No CRS found for {iso_path}, assuming EPSG:4326")
                    isochrone.set_crs(epsg=4326, inplace=True)
                
                if isochrone.crs.to_string() != 'EPSG:3857':
                    isochrone = isochrone.to_crs(epsg=3857)
                
                # Add location name as title for each panel
                location_name = os.path.basename(iso_path).replace('_isochrones.geojson', '')
                location_name = location_name.replace('_', ' ').title()
                ax.set_title(location_name)
                
                # Plot isochrones with distinctive borders
                colors = ['#1a9641', '#a6d96a', '#ffffbf', '#fdae61', '#d7191c']
                for idx, (_, iso) in enumerate(isochrone.iterrows()):
                    color_idx = min(idx, len(colors) - 1)
                    ax.fill(iso.geometry.exterior.xy[0], iso.geometry.exterior.xy[1], 
                            color=colors[color_idx], alpha=0.5, 
                            edgecolor='black', linewidth=1)
                
                # Add POIs if provided
                if poi_dfs and i < len(poi_dfs) and poi_dfs[i] is not None:
                    poi_df = poi_dfs[i]
                    if not poi_df.empty and poi_df.crs.to_string() != 'EPSG:3857':
                        poi_df = poi_df.to_crs(epsg=3857)
                    
                    poi_df.plot(ax=ax, marker='o', color='blue', markersize=50, alpha=0.7)
                
                # Add basemap
                try:
                    cx.add_basemap(ax, source=basemap_provider)
                except Exception as e:
                    print(f"Warning: Could not add basemap: {e}")
                
                # Add scale bar
                ax.add_artist(ScaleBar(1, location='lower right', dimension='si-length', 
                                      frameon=True, border_pad=0.5))
                
                # Add north arrow
                add_north_arrow(ax, position='upper right', scale=0.1)
                
                # Remove axis ticks
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_frame_on(True)
                
            except Exception as e:
                print(f"Error processing {iso_path}: {e}")
                ax.set_axis_off()
                ax.text(0.5, 0.5, f"Error loading isochrone data", 
                        horizontalalignment='center', verticalalignment='center')
        
        # Hide unused axes
        for j in range(i + 1, len(axes)):
            axes[j].set_axis_off()
        
        # Create output path for this figure
        if num_figures > 1:
            curr_output_path = output_path.replace('.png', f'_part{fig_idx+1}.png')
        else:
            curr_output_path = output_path
        
        # Save figure
        plt.savefig(curr_output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        saved_paths.append(curr_output_path)
    
    return saved_paths[0] if len(saved_paths) == 1 else saved_paths

def generate_paneled_census_map(
    census_data_paths,
    variable,
    output_path=None,
    title=None,
    colormap=None,
    basemap_provider='OpenStreetMap.Mapnik',
    figsize=(15, 10),
    dpi=150,
    output_dir='output/maps',
    isochrone_paths=None,
    poi_dfs=None,
    max_panels_per_figure=6
):
    """
    Generate a paneled map showing census data for multiple locations.
    
    Args:
        census_data_paths (list): List of paths to GeoJSON census data files
        variable (str): Census variable to map
        output_path (str, optional): Path to save the output map. If None, will be auto-generated
        title (str, optional): Title for the map
        colormap (str, optional): Matplotlib colormap to use
        basemap_provider (str, optional): Basemap provider for contextily
        figsize (tuple, optional): Figure size in inches (width, height)
        dpi (int, optional): DPI for the figure
        output_dir (str, optional): Directory to save the output map
        isochrone_paths (list, optional): List of paths to GeoJSON isochrone files
        poi_dfs (list, optional): List of GeoDataFrames with POIs to plot on the maps
        max_panels_per_figure (int, optional): Maximum number of panels per figure
        
    Returns:
        str: Path to the saved map
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if variable is a common name and convert to Census API code if needed
    if variable.lower() in CENSUS_VARIABLE_MAPPING:
        variable_code = CENSUS_VARIABLE_MAPPING[variable.lower()]
    else:
        variable_code = variable
    
    # Get variable label
    variable_label = get_variable_label(variable_code)
    
    # Choose colormap if not provided
    if colormap is None:
        colormap = choose_appropriate_colormap(variable)
    
    # Generate output path if not provided
    if output_path is None:
        # Extract common prefix from census data paths
        paths = [os.path.basename(p) for p in census_data_paths]
        common_prefix = os.path.commonprefix(paths)
        if not common_prefix:
            common_prefix = "paneled_census"
        output_path = os.path.join(output_dir, f"{common_prefix}_{variable}_map.png")
    
    # Prepare a common min/max for consistent color scaling
    all_values = []
    processed_census_dfs = []
    
    # Read and process all census data first
    for census_path in census_data_paths:
        try:
            # Read census data
            census_df = gpd.read_file(census_path)
            
            # Skip if empty
            if census_df.empty:
                processed_census_dfs.append(None)
                continue
            
            # Ensure CRS is in Web Mercator for basemap
            if census_df.crs is None:
                warnings.warn(f"No CRS found for {census_path}, assuming EPSG:4326")
                census_df.set_crs(epsg=4326, inplace=True)
            
            if census_df.crs.to_string() != 'EPSG:3857':
                census_df = census_df.to_crs(epsg=3857)
            
            # Check if variable exists in dataframe
            if variable_code not in census_df.columns:
                # Check if we have a common name instead
                if variable.lower() in CENSUS_VARIABLE_MAPPING:
                    variable_code = CENSUS_VARIABLE_MAPPING[variable.lower()]
                    if variable_code not in census_df.columns:
                        print(f"Warning: Variable {variable} ({variable_code}) not found in {census_path}")
                        processed_census_dfs.append(None)
                        continue
                else:
                    # Try to find derived variables
                    if variable.lower() == 'poverty_rate':
                        if 'B17001_002E' in census_df.columns and 'B17001_001E' in census_df.columns:
                            census_df[variable] = census_df['B17001_002E'] / census_df['B17001_001E'] * 100
                            variable_code = variable
                        else:
                            print(f"Warning: Cannot calculate poverty_rate for {census_path}")
                            processed_census_dfs.append(None)
                            continue
                    elif variable.lower() == 'homeownership_rate':
                        if 'B25003_002E' in census_df.columns and 'B25003_001E' in census_df.columns:
                            census_df[variable] = census_df['B25003_002E'] / census_df['B25003_001E'] * 100
                            variable_code = variable
                        else:
                            print(f"Warning: Cannot calculate homeownership_rate for {census_path}")
                            processed_census_dfs.append(None)
                            continue
                    elif variable.lower() == 'vacant_rate':
                        if 'B25002_003E' in census_df.columns and 'B25002_001E' in census_df.columns:
                            census_df[variable] = census_df['B25002_003E'] / census_df['B25002_001E'] * 100
                            variable_code = variable
                        else:
                            print(f"Warning: Cannot calculate vacant_rate for {census_path}")
                            processed_census_dfs.append(None)
                            continue
                    elif variable.lower() == 'bachelors_or_higher':
                        bachelors_vars = ['B15003_022E', 'B15003_023E', 'B15003_024E', 'B15003_025E']
                        if all(var in census_df.columns for var in bachelors_vars) and 'B15003_001E' in census_df.columns:
                            census_df[variable] = census_df[bachelors_vars].sum(axis=1) / census_df['B15003_001E'] * 100
                            variable_code = variable
                        else:
                            print(f"Warning: Cannot calculate bachelors_or_higher for {census_path}")
                            processed_census_dfs.append(None)
                            continue
                    else:
                        print(f"Warning: Variable {variable} not found in {census_path}")
                        processed_census_dfs.append(None)
                        continue
            
            # Ensure variable is numeric
            if not np.issubdtype(census_df[variable_code].dtype, np.number):
                try:
                    census_df[variable_code] = pd.to_numeric(census_df[variable_code], errors='coerce')
                except Exception as e:
                    print(f"Warning: Could not convert {variable_code} to numeric in {census_path}: {e}")
                    processed_census_dfs.append(None)
                    continue
            
            # Special handling for income, home value and population
            if 'median' in variable.lower() and 'income' in variable.lower():
                # Replace 0 and -666666666 (Census null value) with NaN
                census_df[variable_code] = census_df[variable_code].replace([0, -666666666], np.nan)
            elif 'home_value' in variable.lower() or 'median' in variable.lower() and 'value' in variable.lower():
                # Replace 0 and -666666666 (Census null value) with NaN
                census_df[variable_code] = census_df[variable_code].replace([0, -666666666], np.nan)
            elif 'population' in variable.lower():
                # Replace negative values with NaN
                census_df[variable_code] = census_df[variable_code].replace([0, -666666666], np.nan)
                census_df.loc[census_df[variable_code] < 0, variable_code] = np.nan
            
            # Collect values for colorscale calculation
            all_values.extend(census_df[variable_code].dropna().tolist())
            
            # Store processed dataframe
            processed_census_dfs.append(census_df)
            
        except Exception as e:
            print(f"Error processing {census_path}: {e}")
            processed_census_dfs.append(None)
    
    # If no valid data was found, return early
    if not all_values:
        print("No valid data found for variable:", variable)
        return None
    
    # Calculate optimal number of bins
    num_bins = calculate_optimal_bins(all_values)
    
    # Apply classification
    bins, labels = apply_quantile_classification(all_values, num_bins=num_bins)
    
    # Calculate number of figures needed
    num_figures = math.ceil(len(census_data_paths) / max_panels_per_figure)
    saved_paths = []
    
    # Loop through figures
    for fig_idx in range(num_figures):
        start_idx = fig_idx * max_panels_per_figure
        end_idx = min((fig_idx + 1) * max_panels_per_figure, len(census_data_paths))
        curr_paths = census_data_paths[start_idx:end_idx]
        curr_dfs = processed_census_dfs[start_idx:end_idx]
        
        # Calculate grid dimensions
        num_panels = len(curr_paths)
        if num_panels <= 2:
            nrows, ncols = 1, num_panels
        elif num_panels <= 4:
            nrows, ncols = 2, 2
        else:
            nrows = math.ceil(num_panels / 3)
            ncols = min(3, math.ceil(num_panels / nrows))
        
        # Create figure
        fig, axes = plt.subplots(nrows, ncols, figsize=figsize, constrained_layout=True)
        
        # If there's only one panel, axes is not a list
        if num_panels == 1:
            axes = np.array([axes])
        
        # Flatten axes for easier iteration
        axes = axes.flatten()
        
        # Set figure title if provided
        if title and num_figures == 1:
            full_title = f"{title}: {variable_label}"
            fig.suptitle(full_title, fontsize=16)
        elif title:
            full_title = f"{title}: {variable_label} (Part {fig_idx+1}/{num_figures})"
            fig.suptitle(full_title, fontsize=16)
        else:
            fig.suptitle(variable_label, fontsize=16)
        
        # Create norm and colormap for consistent coloring
        import matplotlib.colors as colors
        norm = colors.BoundaryNorm(bins, 256)
        cmap = plt.colormaps.get(colormap, len(bins) - 1)
        
        # Iterate through census paths, processed dataframes, and axes
        for i, (census_path, census_df, ax) in enumerate(zip(curr_paths, curr_dfs, axes)):
            try:
                # Skip if no data
                if census_df is None:
                    ax.set_axis_off()
                    ax.text(0.5, 0.5, f"No data for {os.path.basename(census_path)}", 
                            horizontalalignment='center', verticalalignment='center')
                    continue
                
                # Add location name as title for each panel
                location_name = os.path.basename(census_path).replace('_blockgroups.geojson', '')
                location_name = location_name.replace('_census.geojson', '')
                location_name = location_name.replace('_', ' ').title()
                ax.set_title(location_name)
                
                # Plot census data with consistent coloring
                census_df.plot(column=variable_code, ax=ax, cmap=cmap, norm=norm, 
                               linewidth=0.5, edgecolor='#333333', alpha=0.75)
                
                # Add isochrones if provided
                if isochrone_paths and i < len(isochrone_paths) and isochrone_paths[i] is not None:
                    try:
                        iso_path = isochrone_paths[i]
                        isochrone = gpd.read_file(iso_path)
                        
                        if not isochrone.empty:
                            if isochrone.crs is None:
                                isochrone.set_crs(epsg=4326, inplace=True)
                            
                            if isochrone.crs.to_string() != 'EPSG:3857':
                                isochrone = isochrone.to_crs(epsg=3857)
                            
                            # Create a different line style for each isochrone time
                            # Ensure geometries are for line plotting
                            for idx, (_, iso) in enumerate(isochrone.iterrows()):
                                ax.plot(*iso.geometry.exterior.xy, 
                                        color='black', linewidth=2, linestyle=['solid', 'dashed', 'dotted'][idx % 3])
                    except Exception as e:
                        print(f"Warning: Could not add isochrones from {iso_path}: {e}")
                
                # Add POIs if provided
                if poi_dfs and i < len(poi_dfs) and poi_dfs[i] is not None:
                    try:
                        poi_df = poi_dfs[i]
                        if not poi_df.empty:
                            if poi_df.crs.to_string() != 'EPSG:3857':
                                poi_df = poi_df.to_crs(epsg=3857)
                            
                            poi_df.plot(ax=ax, marker='*', color='red', markersize=80, alpha=0.7)
                    except Exception as e:
                        print(f"Warning: Could not add POIs: {e}")
                
                # Add basemap
                try:
                    cx.add_basemap(ax, source=basemap_provider)
                except Exception as e:
                    print(f"Warning: Could not add basemap: {e}")
                
                # Add scale bar
                ax.add_artist(ScaleBar(1, location='lower right', dimension='si-length', 
                                      frameon=True, border_pad=0.5))
                
                # Add north arrow
                add_north_arrow(ax, position='upper right', scale=0.1)
                
                # Remove axis ticks
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_frame_on(True)
                
            except Exception as e:
                print(f"Error processing {census_path}: {e}")
                ax.set_axis_off()
                ax.text(0.5, 0.5, f"Error loading census data", 
                        horizontalalignment='center', verticalalignment='center')
        
        # Hide unused axes
        for j in range(i + 1, len(axes)):
            axes[j].set_axis_off()
        
        # Create a unified legend for the figure
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        
        # Add legend with custom labels
        if len(labels) <= 5:
            legend_kwargs = {'loc': 'lower center', 'bbox_to_anchor': (0.5, -0.15), 
                             'ncol': len(labels), 'frameon': True}
        else:
            legend_kwargs = {'loc': 'lower center', 'bbox_to_anchor': (0.5, -0.2), 
                             'ncol': min(len(labels), 3), 'frameon': True}
        
        legend_patches = []
        for i, label in enumerate(labels):
            color_idx = i / (len(labels) - 1) if len(labels) > 1 else 0.5
            color = cmap(color_idx)
            legend_patches.append(Patch(color=color, label=label))
        
        fig.legend(handles=legend_patches, **legend_kwargs)
        
        # Create output path for this figure
        if num_figures > 1:
            curr_output_path = output_path.replace('.png', f'_part{fig_idx+1}.png')
        else:
            curr_output_path = output_path
        
        # Save figure
        plt.savefig(curr_output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        saved_paths.append(curr_output_path)
    
    return saved_paths[0] if len(saved_paths) == 1 else saved_paths 