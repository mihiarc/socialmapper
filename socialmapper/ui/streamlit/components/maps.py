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
    m = folium.Map(
        location=[lat, lon], 
        zoom_start=zoom_start,
        scrollWheelZoom=False,
        doubleClickZoom=True,
        touchZoom=True,
        boxZoom=True,
        keyboard=True,
        zoomControl=True
    )

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
    isochrone_bounds: list[list[float]] | None = None,
    zoom_start: int = 13,
    tiles: str = "OpenStreetMap",
    show_poi_labels: bool = True
) -> folium.Map:
    """Create a map with POI markers and locked zoom.
    
    The map has scroll wheel zoom disabled to prevent accidental zoom changes.
    Users can still zoom using:
    - Zoom control buttons (+/- in top-left)
    - Double-click to zoom in
    - Shift+drag to zoom to area (box zoom)
    - Keyboard +/- keys
    - Touch gestures on mobile
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        pois: DataFrame with POI data (must have lat, lon, name columns)
        isochrone_data: Optional isochrone overlay
        isochrone_bounds: Optional bounds [[south, west], [north, east]] for map extent
        zoom_start: Initial zoom level (used if no bounds provided)
        tiles: Map tile style
        show_poi_labels: Whether to show POI labels
        
    Returns:
        Configured folium Map object with POI markers and zoom controls
    """
    # Create base map with specified tiles and disabled scroll wheel zoom
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=zoom_start, 
        tiles=tiles,
        scrollWheelZoom=False,  # Disable mouse wheel zoom
        doubleClickZoom=True,   # Keep double-click zoom enabled
        touchZoom=True,         # Keep touch zoom for mobile
        boxZoom=True,           # Keep box zoom (shift+drag)
        keyboard=True,          # Keep keyboard zoom (+/- keys)
        zoomControl=True        # Show zoom control buttons
    )
    
    # Add isochrone if available
    if isochrone_data:
        folium.GeoJson(
            isochrone_data,
            style_function=lambda x: {
                'fillColor': '#3388ff',
                'color': '#3388ff', 
                'weight': 2,
                'fillOpacity': 0.3
            },
            tooltip="Travel Time Area"
        ).add_to(m)
    
    # Fit map to isochrone bounds if available, otherwise use default zoom
    if isochrone_bounds:
        # Add small padding to bounds for better visualization
        south, west = isochrone_bounds[0]
        north, east = isochrone_bounds[1]
        
        # Add 5% padding around the bounds
        lat_padding = (north - south) * 0.05
        lon_padding = (east - west) * 0.05
        
        padded_bounds = [
            [south - lat_padding, west - lon_padding],
            [north + lat_padding, east + lon_padding]
        ]
        
        m.fit_bounds(padded_bounds)

    # Add POI markers
    for _, poi in pois.iterrows():
        popup_text = poi['name'] if show_poi_labels else f"POI ({poi.get('type', 'Unknown')})"
        tooltip_text = poi['name'] if show_poi_labels else None
        
        folium.Marker(
            [poi['lat'], poi['lon']],
            popup=popup_text,
            tooltip=tooltip_text,
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
        return folium.Map(
            location=center, 
            zoom_start=4,
            scrollWheelZoom=False,
            doubleClickZoom=True,
            touchZoom=True,
            boxZoom=True,
            keyboard=True,
            zoomControl=True
        )

    # Calculate center from locations if not provided
    if center is None:
        lats = [loc['lat'] for loc in locations]
        lons = [loc['lon'] for loc in locations]
        center = (sum(lats) / len(lats), sum(lons) / len(lons))

    m = folium.Map(
        location=center, 
        zoom_start=zoom_start,
        scrollWheelZoom=False,
        doubleClickZoom=True,
        touchZoom=True,
        boxZoom=True,
        keyboard=True,
        zoomControl=True
    )

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
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=zoom_start,
        scrollWheelZoom=False,
        doubleClickZoom=True,
        touchZoom=True,
        boxZoom=True,
        keyboard=True,
        zoomControl=True
    )

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
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=zoom_start,
        scrollWheelZoom=False,
        doubleClickZoom=True,
        touchZoom=True,
        boxZoom=True,
        keyboard=True,
        zoomControl=True
    )

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
