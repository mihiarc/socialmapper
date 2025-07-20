"""Multi-modal map visualization components for travel time analysis."""

import logging
from typing import Any, Dict, List, Optional

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from ..utils.cache import get_map_base_config

logger = logging.getLogger(__name__)

# Travel mode color scheme
TRAVEL_MODE_COLORS = {
    'walk': '#ff7f00',     # Orange
    'bike': '#4daf4a',     # Green
    'drive': '#377eb8'     # Blue
}

TRAVEL_MODE_ICONS = {
    'walk': '🚶',
    'bike': '🚴',
    'drive': '🚗'
}


@st.fragment
def render_multi_modal_map(
    results_by_mode: Dict[str, Any],
    height: int = 700,
    center_lat: Optional[float] = None,
    center_lon: Optional[float] = None
) -> None:
    """Render a multi-modal travel time map with different colors for each mode.
    
    Args:
        results_by_mode: Dictionary with travel mode as key and analysis results as value
        height: Height of the map in pixels
        center_lat: Override center latitude
        center_lon: Override center longitude
    """
    if not results_by_mode:
        st.warning("No analysis results available for map display")
        return
    
    # Map controls
    st.markdown("### 🗺️ Multi-Modal Travel Time Map")
    
    # Mode toggles
    col1, col2, col3, col4 = st.columns(4)
    
    mode_visibility = {}
    with col1:
        if 'walk' in results_by_mode:
            mode_visibility['walk'] = st.checkbox(
                f"{TRAVEL_MODE_ICONS['walk']} Walking Areas", 
                value=True,
                key="show_walk"
            )
    
    with col2:
        if 'bike' in results_by_mode:
            mode_visibility['bike'] = st.checkbox(
                f"{TRAVEL_MODE_ICONS['bike']} Cycling Areas", 
                value=True,
                key="show_bike"
            )
    
    with col3:
        if 'drive' in results_by_mode:
            mode_visibility['drive'] = st.checkbox(
                f"{TRAVEL_MODE_ICONS['drive']} Driving Areas", 
                value=True,
                key="show_drive"
            )
    
    with col4:
        show_poi_labels = st.checkbox("🏷️ POI Labels", value=True, key="show_multi_poi_labels")
    
    try:
        # Calculate map center from all POIs if not provided
        all_pois = []
        for mode_data in results_by_mode.values():
            all_pois.extend(mode_data.get('pois', []))
        
        if not all_pois:
            st.error("No POI data found in analysis results")
            return
        
        if center_lat is None or center_lon is None:
            center_lat = sum(poi.get('lat', 0) for poi in all_pois) / len(all_pois)
            center_lon = sum(poi.get('lon', 0) for poi in all_pois) / len(all_pois)
        
        # Create base map
        base_config = get_map_base_config()
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=base_config.get('zoom_start', 12),
            tiles="OpenStreetMap"
        )
        
        # Add isochrones for each mode
        layer_control_added = False
        for mode, data in results_by_mode.items():
            if not mode_visibility.get(mode, False):
                continue
                
            isochrones = data.get('isochrones')
            if isochrones is not None and hasattr(isochrones, 'geometry') and not isochrones.empty:
                try:
                    # Convert to GeoJSON
                    isochrone_geojson = isochrones.to_json()
                    
                    # Add to map with mode-specific styling
                    color = TRAVEL_MODE_COLORS.get(mode, '#999999')
                    folium.GeoJson(
                        isochrone_geojson,
                        name=f"{TRAVEL_MODE_ICONS.get(mode, '')} {mode.title()} ({data.get('travel_time', '?')} min)",
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': color,
                            'weight': 2,
                            'fillOpacity': 0.3,
                            'opacity': 0.8
                        },
                        tooltip=f"{mode.title()} Travel Area",
                        popup=folium.Popup(
                            f"""
                            <b>{mode.title()} Travel Area</b><br>
                            POIs Accessible: {data.get('poi_count', 0)}<br>
                            Population: {data.get('total_population', 0):,}<br>
                            Area: {data.get('area_km2', 0):.2f} km²
                            """,
                            max_width=200
                        )
                    ).add_to(m)
                    layer_control_added = True
                    
                except Exception as e:
                    logger.warning(f"Could not add {mode} isochrones to map: {e}")
        
        # Add POI markers (combine all modes, color by travel mode with best access)
        poi_access_by_location = {}
        
        # First pass: collect all POIs and their accessibility by mode
        for mode, data in results_by_mode.items():
            pois = data.get('pois', [])
            for poi in pois:
                lat_lon = (poi.get('lat'), poi.get('lon'))
                if lat_lon not in poi_access_by_location:
                    poi_access_by_location[lat_lon] = {
                        'poi': poi,
                        'modes': []
                    }
                poi_access_by_location[lat_lon]['modes'].append(mode)
        
        # Second pass: add markers colored by best/fastest access
        for location_data in poi_access_by_location.values():
            poi = location_data['poi']
            accessible_modes = location_data['modes']
            
            # Extract POI name
            name = 'Unnamed'
            if 'tags' in poi and isinstance(poi['tags'], dict):
                name = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
            
            # Determine marker color based on fastest/best mode available
            if 'drive' in accessible_modes:
                marker_color = 'blue'
                fastest_mode = 'drive'
            elif 'bike' in accessible_modes:
                marker_color = 'green'
                fastest_mode = 'bike'
            elif 'walk' in accessible_modes:
                marker_color = 'orange'
                fastest_mode = 'walk'
            else:
                marker_color = 'gray'
                fastest_mode = 'none'
            
            # Create popup with accessibility info
            modes_text = ', '.join([f"{TRAVEL_MODE_ICONS.get(m, '')} {m.title()}" for m in accessible_modes])
            popup_text = f"""
            <b>{name}</b><br>
            Accessible by: {modes_text}<br>
            Fastest: {TRAVEL_MODE_ICONS.get(fastest_mode, '')} {fastest_mode.title()}
            """
            
            if show_poi_labels:
                folium.Marker(
                    [poi['lat'], poi['lon']],
                    popup=folium.Popup(popup_text, max_width=250),
                    tooltip=name,
                    icon=folium.Icon(color=marker_color, icon='location-dot')
                ).add_to(m)
        
        # Add layer control if we have multiple layers
        if layer_control_added:
            folium.LayerControl(collapsed=False).add_to(m)
        
        # Display the map with full width
        map_data = st_folium(
            m,
            height=height,
            width=None,  # Use full container width
            returned_objects=["last_object_clicked"],
            key=f"multi_modal_map_{hash(str(results_by_mode.keys()))}"
        )
        
        # Show map interaction info
        if map_data['last_object_clicked']:
            clicked = map_data['last_object_clicked']
            st.info(f"Clicked: {clicked.get('tooltip', 'Map element')} at {clicked.get('lat', '?'):.6f}, {clicked.get('lng', '?'):.6f}")
        
    except Exception as e:
        logger.error(f"Error rendering multi-modal map: {e}", exc_info=True)
        st.error(f"Unable to render map: {str(e)}")
        
        # Show debug information
        with st.expander("🔧 Map Debug Information"):
            st.markdown("**Error Details:**")
            st.code(str(e))
            st.markdown("**Available Data:**")
            for mode, data in results_by_mode.items():
                st.write(f"- {mode}: {len(data.get('pois', []))} POIs, isochrones: {data.get('isochrones') is not None}")


@st.fragment  
def render_travel_time_comparison(
    results_by_mode: Dict[str, Any],
    travel_time_limit: int
) -> None:
    """Render detailed travel time comparison charts.
    
    Args:
        results_by_mode: Dictionary with travel mode results
        travel_time_limit: Maximum travel time used in analysis
    """
    st.markdown("### ⏱️ Travel Time Analysis")
    
    if not results_by_mode:
        st.warning("No travel time data available")
        return
    
    # Create comparison metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🚶 Walking**")
        if 'walk' in results_by_mode:
            walk_data = results_by_mode['walk']
            st.metric(
                "POIs Accessible",
                walk_data.get('poi_count', 0),
                help=f"Number of POIs reachable within {travel_time_limit} minutes walking"
            )
            st.metric(
                "Population Served", 
                f"{walk_data.get('total_population', 0):,}",
                help="Population within walking travel area"
            )
        else:
            st.info("Walking analysis not available")
    
    with col2:
        st.markdown("**🚴 Cycling**")
        if 'bike' in results_by_mode:
            bike_data = results_by_mode['bike']
            st.metric(
                "POIs Accessible",
                bike_data.get('poi_count', 0),
                help=f"Number of POIs reachable within {travel_time_limit} minutes cycling"
            )
            st.metric(
                "Population Served",
                f"{bike_data.get('total_population', 0):,}",
                help="Population within cycling travel area"
            )
        else:
            st.info("Cycling analysis not available")
    
    with col3:
        st.markdown("**🚗 Driving**")
        if 'drive' in results_by_mode:
            drive_data = results_by_mode['drive']
            st.metric(
                "POIs Accessible",
                drive_data.get('poi_count', 0),
                help=f"Number of POIs reachable within {travel_time_limit} minutes driving"
            )
            st.metric(
                "Population Served",
                f"{drive_data.get('total_population', 0):,}",
                help="Population within driving travel area"
            )
        else:
            st.info("Driving analysis not available")
    
    # Efficiency comparison
    st.markdown("### 📊 Mode Efficiency Comparison")
    
    # Calculate efficiency metrics
    efficiency_data = []
    for mode, data in results_by_mode.items():
        poi_count = data.get('poi_count', 0)
        population = data.get('total_population', 0)
        area = data.get('area_km2', 0)
        
        # Calculate density metrics
        poi_density = poi_count / area if area > 0 else 0
        pop_density = population / area if area > 0 else 0
        
        efficiency_data.append({
            'Mode': f"{TRAVEL_MODE_ICONS.get(mode, '')} {mode.title()}",
            'POI Density (per km²)': f"{poi_density:.2f}",
            'Pop Density (per km²)': f"{pop_density:.0f}",
            'Coverage Area (km²)': f"{area:.2f}",
            'POI/Population Ratio': f"{poi_count/population*1000:.2f} per 1K" if population > 0 else "N/A"
        })
    
    if efficiency_data:
        efficiency_df = pd.DataFrame(efficiency_data)
        st.dataframe(efficiency_df, use_container_width=True, hide_index=True)


@st.fragment
def render_accessibility_insights(
    results_by_mode: Dict[str, Any]
) -> None:
    """Render accessibility insights and recommendations.
    
    Args:
        results_by_mode: Dictionary with travel mode results
    """
    st.markdown("### 💡 Accessibility Insights")
    
    if not results_by_mode:
        st.warning("No data available for insights")
        return
    
    insights = []
    
    # Analyze coverage differences
    if len(results_by_mode) > 1:
        poi_counts = {mode: data.get('poi_count', 0) for mode, data in results_by_mode.items()}
        max_mode = max(poi_counts, key=poi_counts.get)
        min_mode = min(poi_counts, key=poi_counts.get)
        
        if poi_counts[max_mode] > poi_counts[min_mode]:
            difference = poi_counts[max_mode] - poi_counts[min_mode]
            insights.append({
                'type': 'coverage',
                'icon': '📈',
                'title': 'Coverage Gap Identified',
                'message': f"{max_mode.title()} provides access to {difference} more POIs than {min_mode}",
                'recommendation': f"Consider improving {min_mode} infrastructure to increase accessibility"
            })
    
    # Analyze population efficiency
    for mode, data in results_by_mode.items():
        poi_count = data.get('poi_count', 0)
        population = data.get('total_population', 0)
        
        if poi_count > 0 and population > 0:
            people_per_poi = population / poi_count
            if people_per_poi > 5000:
                insights.append({
                    'type': 'efficiency',
                    'icon': '⚠️',
                    'title': f'{mode.title()} May Be Under-served',
                    'message': f"Each accessible POI serves {people_per_poi:.0f} people",
                    'recommendation': "Consider additional POI locations to improve service coverage"
                })
            elif people_per_poi < 1000:
                insights.append({
                    'type': 'efficiency',
                    'icon': '✅',
                    'title': f'{mode.title()} Shows Good Coverage',
                    'message': f"Each POI serves {people_per_poi:.0f} people - good accessibility",
                    'recommendation': "Current coverage level is well-distributed"
                })
    
    # Display insights
    if insights:
        for insight in insights:
            with st.container():
                st.markdown(f"""
                **{insight['icon']} {insight['title']}**
                
                {insight['message']}
                
                *💭 Recommendation: {insight['recommendation']}*
                """)
                st.markdown("---")
    else:
        st.info("🔍 Run analysis with multiple travel modes to see accessibility insights")