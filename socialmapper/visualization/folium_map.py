#!/usr/bin/env python3
"""
Functions for generating interactive folium maps for Streamlit.
"""
from typing import Optional, Union, List, Dict, Any, Tuple
import folium
import geopandas as gpd
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_folium import folium_static
from branca.colormap import LinearColormap
from folium.plugins import MarkerCluster, Fullscreen, Search, MeasureControl
import os
from pathlib import Path
from socialmapper.util import CENSUS_VARIABLE_MAPPING
from .map_utils import get_variable_label, calculate_optimal_bins, apply_quantile_classification, choose_appropriate_colormap

def generate_folium_map(
    census_data_path: Union[str, gpd.GeoDataFrame],
    variable: str,
    isochrone_path: Optional[Union[str, gpd.GeoDataFrame]] = None,
    poi_df: Optional[gpd.GeoDataFrame] = None,
    title: Optional[str] = None,
    colormap: Optional[str] = None,
    height: int = 600,
    width: int = 800,
    show_legend: bool = True,
    base_map: str = "OpenStreetMap"
) -> folium.Map:
    """
    Generate an interactive folium map for displaying in Streamlit.
    
    Args:
        census_data_path: Path to GeoJSON file or GeoDataFrame with census data
        variable: Census variable to visualize
        isochrone_path: Optional path to isochrone GeoJSON/GeoDataFrame
        poi_df: Optional GeoDataFrame containing POI data
        title: Map title
        colormap: Colormap name (uses folium naming)
        height: Height of the map in pixels
        width: Width of the map in pixels 
        show_legend: Whether to display the legend
        base_map: Base map provider name
        
    Returns:
        Folium map object
    """
    # Helper function to make data JSON-serializable by converting geometries to strings
    def make_serializable(df):
        """Make a dataframe serializable by converting geometry objects to strings."""
        df_clean = df.copy()
        
        # Process each column
        for col in df_clean.columns:
            if col != 'geometry':  # Don't modify the main geometry column
                # Check if column has Shapely geometries
                if df_clean[col].dtype == 'object':
                    # Convert each value in the column if it's a Shapely geometry
                    df_clean[col] = df_clean[col].apply(
                        lambda x: str(x) if hasattr(x, 'geom_type') else x
                    )
        
        return df_clean
    
    # Convert colormap name if specified (matplotlib to folium naming)
    colormap_mapping = {
        'Reds': 'Reds',
        'YlOrRd': 'YlOrRd',
        'Greens': 'Greens',
        'Blues': 'Blues',
        'Purples': 'Purples',
        'BuPu': 'BuPu',
        'GnBu': 'GnBu',
        'YlGnBu': 'YlGnBu',
        'RdYlGn': 'RdYlGn',
        'viridis': 'Viridis',
        'plasma': 'Plasma',
        'inferno': 'Inferno',
        'magma': 'Magma',
        'cividis': 'Cividis'
    }
    
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
    
    # Check if the GeoDataFrame is empty
    if gdf.empty:
        raise ValueError("Census data GeoDataFrame is empty")
    
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
    
    # Ensure data is numeric and handle missing values
    gdf[variable] = pd.to_numeric(gdf[variable], errors='coerce')
    
    # Replace extreme negative values with NaN
    if variable in ['B19013_001E', 'B25077_001E', 'median_income', 'median_household_income', 'median_home_value']:
        gdf.loc[gdf[variable] < 0, variable] = np.nan
    
    # Replace NaN values
    if gdf[variable].isna().any():
        if variable in ['B19013_001E', 'B25077_001E', 'median_income', 'median_household_income', 'median_home_value']:
            positive_values = gdf.loc[gdf[variable] > 0, variable]
            if len(positive_values) > 0:
                min_positive = positive_values.min()
                gdf[variable] = gdf[variable].fillna(min_positive)
            else:
                gdf[variable] = gdf[variable].fillna(0)
        else:
            gdf[variable] = gdf[variable].fillna(gdf[variable].min())
    
    # Ensure GeoDataFrame is in WGS84 (EPSG:4326) for Folium
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    # Calculate center of the map
    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    
    # Choose appropriate colormap if not specified
    if colormap is None:
        mpl_colormap = choose_appropriate_colormap(variable)
        colormap = colormap_mapping.get(mpl_colormap, 'YlOrRd')
    elif colormap in colormap_mapping:
        colormap = colormap_mapping[colormap]
    
    # Create a continuous color map
    # Make sure to use an array of colors, not just a colormap name
    if isinstance(colormap, str):
        # Default to a sequential colormap if the specified one doesn't exist
        default_colors = ['#ffeda0', '#f03b20']
        
        # Try to get color scheme from folium
        try:
            from branca.colormap import linear
            scheme = getattr(linear, colormap, None)
            if scheme is not None:
                colors = scheme.colors
            else:
                colors = default_colors
        except (ImportError, AttributeError):
            colors = default_colors
    else:
        # If colormap is already a list of colors, use it
        colors = colormap
    
    # Create colormap with the colors
    colormap_function = LinearColormap(
        colors=colors,
        vmin=gdf[variable].min(),
        vmax=gdf[variable].max(),
        caption=get_variable_label(variable)
    )
    
    # Create the map
    m = folium.Map(
        location=center,
        zoom_start=10,
        tiles=base_map,
        width=width,
        height=height
    )
    
    # Add fullscreen control
    Fullscreen().add_to(m)
    
    # Add measure control
    MeasureControl(position='topleft', primary_length_unit='meters').add_to(m)
    
    # Calculate optimal bins and color thresholds
    values = gdf[variable].dropna().tolist()
    num_bins = calculate_optimal_bins(values)
    bins, labels = apply_quantile_classification(values, num_bins=num_bins)
    
    # Create a feature group for the census data layer
    census_layer = folium.FeatureGroup(name=f"Census Data: {get_variable_label(variable)}", show=True)
    
    # Create a clean version of the GeoDataFrame with safe values for JSON
    gdf_clean = make_serializable(gdf)
    
    # Create a very minimal version with only the required columns for the choropleth
    gdf_minimal = gdf[[variable, 'GEOID', 'geometry']].copy()
    
    # Add census data choropleth - must be added directly to the map per folium requirements
    choropleth = folium.Choropleth(
        geo_data=gdf_minimal.__geo_interface__,  # Use minimal data to avoid serialization issues
        name=get_variable_label(variable),
        data=gdf_minimal,  # Use minimal data
        columns=["GEOID", variable],
        key_on="feature.properties.GEOID",
        fill_color=colormap,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=get_variable_label(variable),
        highlight=True,
        smooth_factor=1.0
    ).add_to(m)  # Choropleth must be added directly to the map
    
    # Add hover functionality to show data - use only the necessary fields
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["GEOID", variable],
            aliases=["Block Group:", get_variable_label(variable) + ":"],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    )
    
    # Add isochrone if provided
    if isochrone_path is not None:
        if isinstance(isochrone_path, str):
            try:
                isochrone = gpd.read_file(isochrone_path)
            except Exception as e:
                st.warning(f"Could not load isochrone file: {e}")
                isochrone = None
        else:
            isochrone = isochrone_path
            
        if isochrone is not None and not isochrone.empty:
            # Ensure isochrone is in WGS84
            if isochrone.crs is None:
                isochrone = isochrone.set_crs("EPSG:4326")
            elif isochrone.crs != "EPSG:4326":
                isochrone = isochrone.to_crs("EPSG:4326")
            
            # Clean the isochrone data for serialization
            isochrone = make_serializable(isochrone)
                
            # Get travel time values if available
            travel_times = []
            if 'travel_time_minutes' in isochrone.columns:
                travel_times = isochrone['travel_time_minutes'].tolist()
            else:
                # Try to find a column that might contain travel times
                for col in isochrone.columns:
                    if 'time' in col.lower() or 'minute' in col.lower():
                        if isochrone[col].dtype.kind in 'if':  # Is numeric
                            travel_times = isochrone[col].tolist()
                            break
                
            # If we couldn't find travel times, use default values
            if not travel_times:
                travel_times = [5 * (i + 1) for i in range(len(isochrone))]
                
            # Custom colors for isochrones
            iso_colors = ['#00CC0088', '#33CC3388', '#66CC6688', '#99CC9988', '#CCCCCC88']
            
            # Create isochrone feature group so it can be toggled as a whole
            isochrone_group = folium.FeatureGroup(name="Travel Time Isochrones", show=False)
            
            # Add each isochrone to the map with dynamic styling
            for i, (_, row) in enumerate(isochrone.iterrows()):
                color_idx = min(i, len(iso_colors) - 1)
                travel_time = travel_times[i] if i < len(travel_times) else f"Isochrone {i+1}"
                
                folium.GeoJson(
                    row.geometry.__geo_interface__,
                    name=f"{travel_time} min Travel Time",
                    style_function=lambda x, color=iso_colors[color_idx]: {
                        'fillColor': color,
                        'color': '#00000088',
                        'weight': 1.5,
                        'fillOpacity': 0.2
                    },
                    tooltip=f"{travel_time} min Travel Time"
                ).add_to(isochrone_group)
            
            # Add the isochrone group to the map
            isochrone_group.add_to(m)
    
    # Add POIs if provided
    if poi_df is not None and not poi_df.empty:
        # Make a clean copy for processing
        poi_df = poi_df.copy()
        
        # Ensure POI data is in WGS84
        if poi_df.crs is None:
            poi_df = poi_df.set_crs("EPSG:4326")
        elif poi_df.crs != "EPSG:4326":
            poi_df = poi_df.to_crs("EPSG:4326")
        
        # Clean the POI data for serialization
        poi_df = make_serializable(poi_df)
            
        # Create a feature group for POIs
        poi_group = folium.FeatureGroup(name="Points of Interest", show=False)
            
        # Create a marker cluster for POIs
        marker_cluster = MarkerCluster(name="Points of Interest").add_to(poi_group)
        
        # Add each POI to the cluster
        for idx, row in poi_df.iterrows():
            # Get POI name
            poi_name = row.get('name', f"POI {idx}")
            
            # Additional information if available
            info = {}
            for col in poi_df.columns:
                if col not in ['geometry', 'name'] and pd.notna(row[col]):
                    info[col] = row[col]
            
            # Create popup content
            popup_content = f"<b>{poi_name}</b><br>"
            if info:
                for key, value in info.items():
                    popup_content += f"{key.replace('_', ' ').title()}: {value}<br>"
            
            # Add marker
            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=poi_name,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)
        
        # Add the POI group to the map
        poi_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add a title if provided
    if title:
        title_html = f'''
            <h3 align="center" style="font-size:16px; font-family: Arial, sans-serif;">{title}</h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
    
    # Add colormap legend if requested
    if show_legend:
        colormap_function.add_to(m)
        
    return m

def generate_folium_isochrone_map(
    isochrone_path: Union[str, gpd.GeoDataFrame],
    poi_df: Optional[gpd.GeoDataFrame] = None,
    title: Optional[str] = None,
    height: int = 600,
    width: int = 800,
    base_map: str = "OpenStreetMap"
) -> folium.Map:
    """
    Generate an interactive folium map showing just isochrones.
    
    Args:
        isochrone_path: Path to isochrone GeoJSON file or GeoDataFrame
        poi_df: Optional GeoDataFrame containing POI data
        title: Map title
        height: Height of the map in pixels
        width: Width of the map in pixels
        base_map: Base map provider name
        
    Returns:
        Folium map object
    """
    # Helper function to make data JSON-serializable by converting geometries to strings
    def make_serializable(df):
        """Make a dataframe serializable by converting geometry objects to strings."""
        df_clean = df.copy()
        
        # Process each column
        for col in df_clean.columns:
            if col != 'geometry':  # Don't modify the main geometry column
                # Check if column has Shapely geometries
                if df_clean[col].dtype == 'object':
                    # Convert each value in the column if it's a Shapely geometry
                    df_clean[col] = df_clean[col].apply(
                        lambda x: str(x) if hasattr(x, 'geom_type') else x
                    )
        
        return df_clean
    
    # Load isochrone data
    if isinstance(isochrone_path, str):
        try:
            isochrone = gpd.read_file(isochrone_path)
        except Exception as e:
            raise ValueError(f"Error loading isochrone file: {e}")
    else:
        isochrone = isochrone_path
    
    # Check if the GeoDataFrame is empty
    if isochrone.empty:
        raise ValueError("Isochrone GeoDataFrame is empty")
    
    # Ensure GeoDataFrame is in WGS84 (EPSG:4326) for Folium
    if isochrone.crs is None:
        isochrone = isochrone.set_crs("EPSG:4326")
    elif isochrone.crs != "EPSG:4326":
        isochrone = isochrone.to_crs("EPSG:4326")
    
    # Clean the isochrone data for serialization
    isochrone = make_serializable(isochrone)
    
    # Calculate center of the map
    center = [isochrone.geometry.centroid.y.mean(), isochrone.geometry.centroid.x.mean()]
    
    # Create the map
    m = folium.Map(
        location=center,
        zoom_start=10,
        tiles=base_map,
        width=width,
        height=height
    )
    
    # Add fullscreen control
    Fullscreen().add_to(m)
    
    # Add measure control
    MeasureControl(position='topleft', primary_length_unit='meters').add_to(m)
    
    # Get travel time values if available
    travel_times = []
    if 'travel_time_minutes' in isochrone.columns:
        travel_times = isochrone['travel_time_minutes'].tolist()
    else:
        # Try to find a column that might contain travel times
        for col in isochrone.columns:
            if 'time' in col.lower() or 'minute' in col.lower():
                if isochrone[col].dtype.kind in 'if':  # Is numeric
                    travel_times = isochrone[col].tolist()
                    break
        
    # If we couldn't find travel times, use default values
    if not travel_times:
        travel_times = [5 * (i + 1) for i in range(len(isochrone))]
        
    # Custom colors for isochrones
    iso_colors = ['#33CC3388', '#99CC3388', '#FFCC0088', '#FF990088', '#FF000088']
    
    # Create a feature group for isochrones
    isochrone_group = folium.FeatureGroup(name="Travel Time Isochrones", show=True)
    
    # Reverse the order of isochrones so smaller travel times are on top
    isochrone = isochrone.iloc[::-1]
    travel_times = travel_times[::-1] if travel_times else []
    
    # Add each isochrone to the map with dynamic styling
    for i, (_, row) in enumerate(isochrone.iterrows()):
        color_idx = min(i, len(iso_colors) - 1)
        travel_time = travel_times[i] if i < len(travel_times) else f"Isochrone {i+1}"
        
        folium.GeoJson(
            row.geometry.__geo_interface__,
            name=f"{travel_time} min Travel Time",
            style_function=lambda x, color=iso_colors[color_idx]: {
                'fillColor': color,
                'color': '#00000088',
                'weight': 1.5,
                'fillOpacity': 0.3
            },
            tooltip=f"{travel_time} min Travel Time"
        ).add_to(isochrone_group)
    
    # Add the isochrone group to the map
    isochrone_group.add_to(m)
    
    # Add POIs if provided
    if poi_df is not None and not poi_df.empty:
        # Make a clean copy for processing
        poi_df = poi_df.copy()
        
        # Ensure POI data is in WGS84
        if poi_df.crs is None:
            poi_df = poi_df.set_crs("EPSG:4326")
        elif poi_df.crs != "EPSG:4326":
            poi_df = poi_df.to_crs("EPSG:4326")
        
        # Clean the POI data for serialization
        poi_df = make_serializable(poi_df)
        
        # Create a feature group for POIs
        poi_group = folium.FeatureGroup(name="Points of Interest", show=False)
        
        # Add each POI to the map
        for idx, row in poi_df.iterrows():
            # Get POI name
            poi_name = row.get('name', f"POI {idx}")
            
            # Additional information if available
            info = {}
            for col in poi_df.columns:
                if col not in ['geometry', 'name'] and pd.notna(row[col]):
                    info[col] = row[col]
            
            # Create popup content
            popup_content = f"<b>{poi_name}</b><br>"
            if info:
                for key, value in info.items():
                    popup_content += f"{key.replace('_', ' ').title()}: {value}<br>"
            
            # Add marker
            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=poi_name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(poi_group)
        
        # Add the POI group to the map
        poi_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add a title if provided
    if title:
        title_html = f'''
            <h3 align="center" style="font-size:16px; font-family: Arial, sans-serif;">{title}</h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
    return m

def generate_folium_map_for_streamlit(
    census_data_path: Union[str, gpd.GeoDataFrame],
    variable: str,
    isochrone_path: Optional[Union[str, gpd.GeoDataFrame]] = None,
    poi_df: Optional[gpd.GeoDataFrame] = None,
    title: Optional[str] = None,
    colormap: Optional[str] = None,
    height: int = 600,
    width: int = 800,
    show_legend: bool = True,
    base_map: str = "OpenStreetMap",
    isochrone_only: bool = False
) -> None:
    """
    Generate an interactive folium map and display it in Streamlit.
    
    Args:
        census_data_path: Path to GeoJSON file or GeoDataFrame with census data
        variable: Census variable to visualize
        isochrone_path: Optional path to isochrone GeoJSON/GeoDataFrame
        poi_df: Optional GeoDataFrame containing POI data
        title: Map title
        colormap: Colormap name
        height: Height of the map in pixels
        width: Width of the map in pixels
        show_legend: Whether to display the legend
        base_map: Base map provider name
        isochrone_only: Whether to display only isochrones without census data
    """
    if isochrone_only and isochrone_path is not None:
        map_obj = generate_folium_isochrone_map(
            isochrone_path=isochrone_path,
            poi_df=poi_df,
            title=title,
            height=height,
            width=width,
            base_map=base_map
        )
    else:
        map_obj = generate_folium_map(
            census_data_path=census_data_path,
            variable=variable,
            isochrone_path=isochrone_path,
            poi_df=poi_df,
            title=title,
            colormap=colormap,
            height=height,
            width=width,
            show_legend=show_legend,
            base_map=base_map
        )
    
    # Display the map in Streamlit
    folium_static(map_obj, width=width, height=height)

def generate_folium_panel_map(
    census_data_paths: List[Union[str, gpd.GeoDataFrame]],
    variable: str,
    isochrone_paths: Optional[List[Union[str, gpd.GeoDataFrame]]] = None,
    poi_dfs: Optional[List[gpd.GeoDataFrame]] = None,
    titles: Optional[List[str]] = None,
    colormap: Optional[str] = None,
    height: int = 500,
    width: int = 800,
    show_legend: bool = True,
    base_map: str = "OpenStreetMap"
) -> None:
    """
    Generate multiple interactive folium maps and display them in Streamlit.
    
    Args:
        census_data_paths: List of paths to GeoJSON files or GeoDataFrames with census data
        variable: Census variable to visualize
        isochrone_paths: Optional list of paths to isochrone GeoJSON/GeoDataFrames
        poi_dfs: Optional list of GeoDataFrames containing POI data
        titles: Optional list of map titles
        colormap: Colormap name
        height: Height of each map in pixels
        width: Width of each map in pixels
        show_legend: Whether to display the legend
        base_map: Base map provider name
    """
    # Ensure we have synchronized lists
    n_maps = len(census_data_paths)
    
    if isochrone_paths is None:
        isochrone_paths = [None] * n_maps
    elif len(isochrone_paths) < n_maps:
        isochrone_paths.extend([None] * (n_maps - len(isochrone_paths)))
    
    if poi_dfs is None:
        poi_dfs = [None] * n_maps
    elif len(poi_dfs) < n_maps:
        poi_dfs.extend([None] * (n_maps - len(poi_dfs)))
    
    if titles is None:
        titles = [f"Map {i+1}" for i in range(n_maps)]
    elif len(titles) < n_maps:
        titles.extend([f"Map {i+1+len(titles)}" for i in range(n_maps - len(titles))])
    
    # Create a tab for each map
    tabs = st.tabs(titles)
    
    # Generate a map for each tab
    for i, tab in enumerate(tabs):
        with tab:
            if i < n_maps:
                generate_folium_map_for_streamlit(
                    census_data_path=census_data_paths[i],
                    variable=variable,
                    isochrone_path=isochrone_paths[i] if i < len(isochrone_paths) else None,
                    poi_df=poi_dfs[i] if i < len(poi_dfs) else None,
                    title=titles[i] if i < len(titles) else None,
                    colormap=colormap,
                    height=height,
                    width=width,
                    show_legend=show_legend,
                    base_map=base_map
                ) 