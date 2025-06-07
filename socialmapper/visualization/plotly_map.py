#!/usr/bin/env python3
"""
Plotly Map visualization module for SocialMapper.
Modern interactive mapping using Plotly's Scattermap API.
"""

from typing import Optional, Union, List, Dict, Any, Tuple
import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import os

# Import SocialMapper utilities
try:
    from socialmapper.util import CENSUS_VARIABLE_MAPPING
    from ..map_utils import get_variable_label, calculate_optimal_bins, apply_quantile_classification, choose_appropriate_colormap
except ImportError:
    # Fallback if running standalone
    CENSUS_VARIABLE_MAPPING = {}
    
    def get_variable_label(var):
        return var.replace('_', ' ').title()
    
    def choose_appropriate_colormap(var):
        return 'Viridis'

# Try to import Streamlit plotly events for interactivity
try:
    from streamlit_plotly_mapbox_events import plotly_mapbox_events
    PLOTLY_EVENTS_AVAILABLE = True
except ImportError:
    PLOTLY_EVENTS_AVAILABLE = False

def create_plotly_map(
    census_data: Union[str, gpd.GeoDataFrame],
    variable: str,
    isochrone_data: Optional[Union[str, gpd.GeoDataFrame]] = None,
    poi_data: Optional[gpd.GeoDataFrame] = None,
    title: Optional[str] = None,
    colorscale: str = 'Viridis',
    height: int = 600,
    width: int = 800,
    show_legend: bool = True,
    map_style: str = 'open-street-map',
    enable_events: bool = False
) -> go.Figure:
    """
    Create an interactive Plotly map with census data, isochrones, and POIs.
    
    Args:
        census_data: Path to GeoJSON file or GeoDataFrame with census data
        variable: Census variable to visualize
        isochrone_data: Optional isochrone data
        poi_data: Optional POI data
        title: Map title
        colorscale: Color scheme for the map
        height: Map height in pixels
        width: Map width in pixels
        show_legend: Whether to show the legend
        map_style: Base map style
        enable_events: Whether to enable interactive events (Streamlit only)
        
    Returns:
        Plotly Figure object
    """
    
    # Load and process census data
    if isinstance(census_data, str):
        census_gdf = gpd.read_file(census_data)
    else:
        census_gdf = census_data.copy()
    
    if census_gdf.empty:
        raise ValueError("Census data is empty")
    
    # Ensure data is in WGS84 for mapping
    if census_gdf.crs != "EPSG:4326":
        census_gdf = census_gdf.to_crs("EPSG:4326")
    
    # Convert to regular DataFrame with lat/lon for Plotly
    census_df = census_gdf.copy()
    
    # For lat/lon calculations, use a projected CRS to avoid warnings
    if census_gdf.crs.is_geographic:
        # Use a suitable projected CRS for centroid calculation (Web Mercator)
        census_projected = census_gdf.to_crs("EPSG:3857")
        centroids = census_projected.geometry.centroid.to_crs("EPSG:4326")
        census_df['lat'] = centroids.y
        census_df['lon'] = centroids.x
    else:
        # Already projected or no CRS specified
        census_df['lat'] = census_gdf.geometry.centroid.y
        census_df['lon'] = census_gdf.geometry.centroid.x
    
    # Check if variable is a common name and convert to Census API code if needed
    if variable.lower() in CENSUS_VARIABLE_MAPPING:
        variable = CENSUS_VARIABLE_MAPPING[variable.lower()]
    
    # Validate variable exists in data
    if variable not in census_df.columns:
        available_vars = [col for col in census_df.columns if col not in ['geometry', 'lat', 'lon', 'GEOID']]
        raise ValueError(f"Variable '{variable}' not found. Available: {available_vars}")
    
    # Create the figure
    fig = go.Figure()
    
    # Normalize values for dynamic sizing
    values = census_df[variable].dropna()
    if len(values) > 0:
        min_val, max_val = values.min(), values.max()
        if max_val > min_val:
            normalized_sizes = 8 + (values - min_val) / (max_val - min_val) * 15
        else:
            normalized_sizes = pd.Series([12] * len(values), index=values.index)
    else:
        normalized_sizes = pd.Series([12] * len(census_df), index=census_df.index)
    
    # Add census data layer
    fig.add_trace(go.Scattermap(
        lat=census_df['lat'],
        lon=census_df['lon'],
        mode='markers',
        marker=dict(
            size=normalized_sizes,
            color=census_df[variable],
            colorscale=colorscale,
            colorbar=dict(
                title=get_variable_label(variable),
                x=1.02,
                len=0.8
            ) if show_legend else None,
            opacity=0.7,
            sizemode='diameter',
            showscale=show_legend
        ),
        text=[f"<b>Block Group {getattr(row, 'GEOID', 'Unknown')[-6:]}</b><br>"
              f"📊 {get_variable_label(variable)}: {getattr(row, variable, 'N/A')}<br>"
              f"📍 Location: ({row['lat']:.4f}, {row['lon']:.4f})"
              for _, row in census_df.iterrows()],
        hovertemplate='%{text}<extra></extra>',
        name='Census Data',
        customdata=census_df.to_dict('records')
    ))
    
    # Add isochrone data if provided
    if isochrone_data is not None:
        if isinstance(isochrone_data, str):
            iso_gdf = gpd.read_file(isochrone_data)
        else:
            iso_gdf = isochrone_data.copy()
        
        if not iso_gdf.empty:
            if iso_gdf.crs != "EPSG:4326":
                iso_gdf = iso_gdf.to_crs("EPSG:4326")
            
            # Add isochrone polygons as scatter points along the boundary
            iso_colors = ['rgba(255,100,100,0.3)', 'rgba(255,150,100,0.3)', 
                         'rgba(255,200,100,0.3)', 'rgba(100,255,100,0.3)']
            
            for i, (_, iso_row) in enumerate(iso_gdf.iterrows()):
                color_idx = min(i, len(iso_colors) - 1)
                travel_time = getattr(iso_row, 'travel_time_minutes', f'{(i+1)*5}')
                
                # Get boundary points for visualization
                boundary = iso_row.geometry.boundary
                if hasattr(boundary, 'coords'):
                    coords = list(boundary.coords)
                elif hasattr(boundary, 'geoms'):
                    coords = []
                    for geom in boundary.geoms:
                        coords.extend(list(geom.coords))
                else:
                    continue
                
                if coords:
                    lats, lons = zip(*[(coord[1], coord[0]) for coord in coords[::10]])  # Sample every 10th point
                    
                    fig.add_trace(go.Scattermap(
                        lat=lats,
                        lon=lons,
                        mode='markers',
                        marker=dict(
                            size=4,
                            color=iso_colors[color_idx],
                            opacity=0.6
                        ),
                        text=f"{travel_time} min Travel Time",
                        hovertemplate=f'<b>{travel_time} min</b><br>Travel Time Boundary<extra></extra>',
                        name=f'{travel_time} min Isochrone',
                        showlegend=True
                    ))
    
    # Add POI data if provided
    if poi_data is not None and not poi_data.empty:
        poi_df = poi_data.copy()
        
        if poi_df.crs != "EPSG:4326":
            poi_df = poi_df.to_crs("EPSG:4326")
        
        poi_df['lat'] = poi_df.geometry.y
        poi_df['lon'] = poi_df.geometry.x
        
        # POI styling configuration
        poi_configs = {
            'library': {'color': '#E74C3C', 'emoji': '📚', 'size': 15},
            'school': {'color': '#3498DB', 'emoji': '🏫', 'size': 15},
            'hospital': {'color': '#27AE60', 'emoji': '🏥', 'size': 15},
            'park': {'color': '#16A085', 'emoji': '🌳', 'size': 15},
            'community': {'color': '#8E44AD', 'emoji': '🏛️', 'size': 15}
        }
        
        # Group POIs by type for better visualization
        if 'type' in poi_df.columns:
            for poi_type in poi_df['type'].unique():
                poi_subset = poi_df[poi_df['type'] == poi_type]
                config = poi_configs.get(poi_type, {'color': '#F39C12', 'emoji': '📍', 'size': 12})
                
                fig.add_trace(go.Scattermap(
                    lat=poi_subset['lat'],
                    lon=poi_subset['lon'],
                    mode='markers',
                    marker=dict(
                        size=config['size'],
                        color=config['color'],
                        opacity=0.9
                    ),
                    text=[f"<b>{config['emoji']} {getattr(row, 'name', 'POI')}</b><br>"
                          f"Type: {poi_type.title()}<br>"
                          f"📍 ({row['lat']:.4f}, {row['lon']:.4f})"
                          for _, row in poi_subset.iterrows()],
                    hovertemplate='%{text}<extra></extra>',
                    name=f"{config['emoji']} {poi_type.title()}",
                    customdata=poi_subset.to_dict('records')
                ))
        else:
            # Single POI group if no type column
            fig.add_trace(go.Scattermap(
                lat=poi_df['lat'],
                lon=poi_df['lon'],
                mode='markers',
                marker=dict(
                    size=12,
                    color='#E67E22',
                    opacity=0.9
                ),
                text=[f"<b>📍 {getattr(row, 'name', 'POI')}</b><br>"
                      f"📍 ({row['lat']:.4f}, {row['lon']:.4f})"
                      for _, row in poi_df.iterrows()],
                hovertemplate='%{text}<extra></extra>',
                name="Points of Interest",
                customdata=poi_df.to_dict('records')
            ))
    
    # Update layout
    center_lat = census_df['lat'].mean()
    center_lon = census_df['lon'].mean()
    
    fig.update_layout(
        map=dict(
            style=map_style,
            center=dict(lat=center_lat, lon=center_lon),
            zoom=10
        ),
        height=height,
        width=width,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        title=dict(
            text=title or f"{get_variable_label(variable)} Distribution",
            font=dict(size=16),
            x=0.5
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="black",
            borderwidth=1
        ),
        font=dict(family="Arial, sans-serif", size=12)
    )
    
    return fig

def create_plotly_map_for_streamlit(
    census_data: Union[str, gpd.GeoDataFrame],
    variable: str,
    isochrone_data: Optional[Union[str, gpd.GeoDataFrame]] = None,
    poi_data: Optional[gpd.GeoDataFrame] = None,
    title: Optional[str] = None,
    colorscale: str = 'Viridis',
    height: int = 600,
    width: int = 800,
    enable_events: bool = True,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Create and display a Plotly map in Streamlit with optional event handling.
    
    Returns:
        Dictionary with event data if events are enabled, None otherwise
    """
    fig = create_plotly_map(
        census_data=census_data,
        variable=variable,
        isochrone_data=isochrone_data,
        poi_data=poi_data,
        title=title,
        colorscale=colorscale,
        height=height,
        width=width,
        **kwargs
    )
    
    if enable_events and PLOTLY_EVENTS_AVAILABLE:
        # Use interactive events
        selected_data = plotly_mapbox_events(
            fig,
            click_event=True,
            hover_event=True,
            select_event=True,
            key=f"plotly_map_{variable}"
        )
        return selected_data
    else:
        # Standard Plotly chart
        st.plotly_chart(fig, use_container_width=True)
        return None

def generate_plotly_maps_for_variables(
    census_data: Union[str, gpd.GeoDataFrame],
    variables: List[str],
    isochrone_data: Optional[Union[str, gpd.GeoDataFrame]] = None,
    poi_data: Optional[gpd.GeoDataFrame] = None,
    output_dir: Optional[str] = None,
    use_streamlit: bool = False,
    **kwargs
) -> List[Union[str, go.Figure]]:
    """
    Generate Plotly maps for multiple variables.
    
    Args:
        census_data: Census data source
        variables: List of variables to visualize
        isochrone_data: Optional isochrone data
        poi_data: Optional POI data
        output_dir: Directory to save static images (if not using Streamlit)
        use_streamlit: Whether to display in Streamlit interface
        **kwargs: Additional arguments for map creation
        
    Returns:
        List of file paths (if saving) or Figure objects (if displaying)
    """
    results = []
    
    for variable in variables:
        if use_streamlit:
            # Display in Streamlit
            st.subheader(f"📊 {get_variable_label(variable)}")
            
            selected_data = create_plotly_map_for_streamlit(
                census_data=census_data,
                variable=variable,
                isochrone_data=isochrone_data,
                poi_data=poi_data,
                title=f"{get_variable_label(variable)} Distribution",
                **kwargs
            )
            
            # Handle interaction events
            if selected_data and len(selected_data) > 0:
                with st.expander(f"🎯 Interaction Data for {get_variable_label(variable)}"):
                    st.json(selected_data[-1])
            
            results.append(selected_data)
        
        else:
            # Create figure for export or return
            fig = create_plotly_map(
                census_data=census_data,
                variable=variable,
                isochrone_data=isochrone_data,
                poi_data=poi_data,
                title=f"{get_variable_label(variable)} Distribution",
                **kwargs
            )
            
            if output_dir:
                # Save as HTML
                output_path = os.path.join(output_dir, f"{variable}_plotly_map.html")
                fig.write_html(output_path)
                results.append(output_path)
            else:
                results.append(fig)
    
    return results 