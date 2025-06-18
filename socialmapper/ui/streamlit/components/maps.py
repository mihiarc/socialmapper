"""Map visualization components for the Streamlit application."""

from typing import Any

import folium
import pandas as pd


def create_folium_map(
    lat: float,
    lon: float,
    isochrone_data: Any | None = None,
    zoom_start: int = 13
) -> folium.Map:
    """Create an interactive folium map with optional isochrone overlay.
    
    Args:
        lat: Latitude for map center
        lon: Longitude for map center
        isochrone_data: Optional GeoJSON data for isochrone overlay
        zoom_start: Initial zoom level
        
    Returns:
        Configured folium Map object
    """
    m = folium.Map(location=[lat, lon], zoom_start=zoom_start)

    # Add center marker
    folium.Marker(
        [lat, lon],
        popup="Analysis Center",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    # Add isochrone if available
    if isochrone_data:
        folium.GeoJson(
            isochrone_data,
            style_function=lambda x: {
                'fillColor': '#3388ff',
                'color': '#3388ff',
                'weight': 2,
                'fillOpacity': 0.3
            }
        ).add_to(m)

    return m


def create_poi_map(
    center_lat: float,
    center_lon: float,
    pois: pd.DataFrame,
    isochrone_data: Any | None = None,
    zoom_start: int = 13
) -> folium.Map:
    """Create a map with POI markers.
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        pois: DataFrame with POI data (must have lat, lon, name columns)
        isochrone_data: Optional isochrone overlay
        zoom_start: Initial zoom level
        
    Returns:
        Configured folium Map object with POI markers
    """
    m = create_folium_map(center_lat, center_lon, isochrone_data, zoom_start)

    # Add POI markers
    for _, poi in pois.iterrows():
        folium.Marker(
            [poi['lat'], poi['lon']],
            popup=poi['name'],
            icon=folium.Icon(color='green', icon='location-dot')
        ).add_to(m)

    return m


def create_custom_location_map(
    locations: list[dict[str, Any]],
    center: tuple[float, float] | None = None,
    zoom_start: int = 10
) -> folium.Map:
    """Create a map showing custom locations.
    
    Args:
        locations: List of location dictionaries with lat, lon, and name
        center: Optional center coordinates, auto-calculated if not provided
        zoom_start: Initial zoom level
        
    Returns:
        Configured folium Map object
    """
    if not locations:
        # Default to US center if no locations
        center = (39.8283, -98.5795) if center is None else center
        return folium.Map(location=center, zoom_start=4)

    # Calculate center from locations if not provided
    if center is None:
        lats = [loc['lat'] for loc in locations]
        lons = [loc['lon'] for loc in locations]
        center = (sum(lats) / len(lats), sum(lons) / len(lons))

    m = folium.Map(location=center, zoom_start=zoom_start)

    # Add markers for each location
    for idx, loc in enumerate(locations):
        folium.Marker(
            [loc['lat'], loc['lon']],
            popup=f"{loc.get('name', f'Location {idx+1}')}",
            icon=folium.Icon(color='blue', icon='map-pin')
        ).add_to(m)

    return m


def create_comparison_map(
    center_lat: float,
    center_lon: float,
    isochrones: dict[str, Any],
    zoom_start: int = 12
) -> folium.Map:
    """Create a map comparing multiple isochrones (e.g., walk/bike/drive).
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        isochrones: Dictionary mapping mode names to isochrone data
        zoom_start: Initial zoom level
        
    Returns:
        Configured folium Map object with multiple isochrones
    """
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)

    # Add center marker
    folium.Marker(
        [center_lat, center_lon],
        popup="Analysis Center",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)

    # Color scheme for different modes
    colors = {
        'walk': '#ff7f00',  # Orange
        'bike': '#4daf4a',  # Green
        'drive': '#377eb8'  # Blue
    }

    # Add each isochrone with different colors
    for mode, data in isochrones.items():
        if data:
            folium.GeoJson(
                data,
                name=mode.capitalize(),
                style_function=lambda x, color=colors.get(mode, '#999'): {
                    'fillColor': color,
                    'color': color,
                    'weight': 2,
                    'fillOpacity': 0.3
                }
            ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    return m


def create_isochrone_map(
    geojson_data: Any,
    pois: list[dict[str, Any]],
    center_lat: float,
    center_lon: float,
    zoom_start: int = 12
) -> folium.Map:
    """Create a map with isochrones and POI markers.
    
    Args:
        geojson_data: GeoJSON data for isochrones
        pois: List of POI dictionaries with lat, lon, name
        center_lat: Center latitude
        center_lon: Center longitude
        zoom_start: Initial zoom level
        
    Returns:
        Configured folium Map object with isochrones and POIs
    """
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)

    # Add isochrone overlay
    if geojson_data:
        folium.GeoJson(
            geojson_data,
            name="Service Areas",
            style_function=lambda x: {
                'fillColor': '#3388ff',
                'color': '#3388ff',
                'weight': 2,
                'fillOpacity': 0.3
            }
        ).add_to(m)

    # Add POI markers
    for poi in pois:
        folium.Marker(
            [poi['lat'], poi['lon']],
            popup=poi['name'],
            tooltip=poi['name'],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

    # Add layer control if we have layers
    if geojson_data:
        folium.LayerControl().add_to(m)

    return m
