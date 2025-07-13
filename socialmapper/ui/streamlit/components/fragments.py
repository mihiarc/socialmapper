"""Fragment-based components for improved performance."""

import logging
from typing import Any, Optional

import streamlit as st
from streamlit_folium import st_folium

from ..utils import get_map_base_config
from .maps import create_poi_map

logger = logging.getLogger(__name__)


@st.fragment
def render_interactive_map(
    analysis_result: dict[str, Any],
    height: int = 600,
    update_interval: Optional[int] = None
) -> None:
    """Render an interactive map as a fragment that can update independently.
    
    This fragment allows the map to be rerun without rerunning the entire app,
    improving performance when users interact with map controls.
    
    Args:
        analysis_result: Analysis results containing POI and isochrone data
        height: Height of the map in pixels
        update_interval: If set, auto-refresh the map at this interval (seconds)
    """
    # Get base map configuration
    base_config = get_map_base_config()
    
    # Add map controls in the fragment
    col1, col2 = st.columns(2)
    
    with col1:
        show_isochrone = st.checkbox("Show Travel Time Area", value=True)
    
    with col2:
        show_poi_labels = st.checkbox("Show POI Labels", value=True)
    
    # Create the map with current settings
    try:
        # Extract data from analysis result
        if not analysis_result or not isinstance(analysis_result, dict):
            raise ValueError("Invalid analysis result data")
            
        pois = analysis_result.get('pois', [])
        if not pois:
            raise ValueError("No POI data found in analysis results")
            
        # Convert POI list to DataFrame format expected by create_poi_map
        import pandas as pd
        
        # Transform POI data to include name from tags
        processed_pois = []
        for poi in pois:
            processed_poi = poi.copy()
            # Extract name from tags, with fallback
            if 'tags' in poi and isinstance(poi['tags'], dict):
                processed_poi['name'] = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
            else:
                processed_poi['name'] = f"Unnamed {poi.get('type', 'POI')}"
            processed_pois.append(processed_poi)
        
        poi_df = pd.DataFrame(processed_pois)
        
        # Ensure required columns exist
        required_cols = ['lat', 'lon', 'name']
        missing_cols = [col for col in required_cols if col not in poi_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required POI data columns: {missing_cols}")
        
        # Check for isochrone data to determine map bounds (always check, regardless of toggle)
        isochrones = analysis_result.get('isochrones')
        isochrone_data = None
        isochrone_bounds = None
        center_lat = poi_df['lat'].mean()  # Default fallback
        center_lon = poi_df['lon'].mean()  # Default fallback
        
        logger.info(f"Fragment - Show isochrone: {show_isochrone}")
        logger.info(f"Fragment - Isochrones type: {type(isochrones)}")
        logger.info(f"Fragment - Analysis result keys: {list(analysis_result.keys()) if isinstance(analysis_result, dict) else 'Not a dict'}")
        
        # Calculate bounds and center from isochrone if available (for proper zoom)
        if isochrones is not None and hasattr(isochrones, 'geometry') and not isochrones.empty:
            logger.info(f"Fragment - Processing isochrones for map bounds, shape: {isochrones.shape}")
            try:
                # Calculate isochrone bounds for map extent (always do this for proper zoom)
                minx, miny, maxx, maxy = isochrones.total_bounds
                isochrone_bounds = [[miny, minx], [maxy, maxx]]
                
                # Use isochrone centroid as map center instead of POI center
                isochrone_centroid = isochrones.geometry.centroid.iloc[0]
                center_lat = isochrone_centroid.y
                center_lon = isochrone_centroid.x
                logger.info(f"Fragment - Using isochrone center: ({center_lat:.6f}, {center_lon:.6f})")
                
                # Only convert to GeoJSON if we need to show the isochrone overlay
                if show_isochrone:
                    isochrone_data = isochrones.to_json() if hasattr(isochrones, 'to_json') else None
                    logger.info(f"Fragment - Successfully converted to GeoJSON: {isochrone_data is not None}")
                
            except Exception as e:
                logger.warning(f"Could not process isochrones: {e}")
        else:
            logger.info("Fragment - No valid isochrones found, using POI center")
        
        # Create the map
        map_obj = create_poi_map(
            center_lat=center_lat,
            center_lon=center_lon,
            pois=poi_df,
            isochrone_data=isochrone_data,
            isochrone_bounds=isochrone_bounds,
            zoom_start=base_config.get('zoom_start', 12),
            tiles="OpenStreetMap",
            show_poi_labels=show_poi_labels
        )
        
        # Display the map with full width
        st_folium(
            map_obj,
            height=height,
            width=None,  # None means use full container width
            returned_objects=["last_object_clicked"],
            key=f"map_{id(analysis_result)}"
        )
        
    except Exception as e:
        logger.error(f"Error rendering map: {e}", exc_info=True)
        
        # Import error dialog if available
        try:
            from .dialogs import show_error_dialog, dialogs_available
            if dialogs_available():
                show_error_dialog(
                    "Map Rendering Failed",
                    f"Error details: {str(e)}\n\nThis could be due to:\n"
                    f"- Invalid analysis data format\n"
                    f"- Missing required map data (POIs or isochrones)\n"
                    f"- Folium/mapping library issues\n"
                    f"- Browser compatibility problems"
                )
            else:
                st.error(f"Unable to render map: {str(e)}")
        except ImportError:
            st.error(f"Unable to render map: {str(e)}")
            
        # Add troubleshooting info
        with st.expander("🔧 Map Troubleshooting"):
            st.markdown("""
            **Possible solutions:**
            1. **Refresh the page** and try the analysis again
            2. **Check your data**: Ensure the analysis completed successfully
            3. **Try a different location** or POI type
            4. **Disable browser extensions** that might interfere with maps
            5. **Clear browser cache** and reload the page
            
            **Technical details:**
            - Error type: `{type(e).__name__}`
            - Error message: `{str(e)}`
            
            **Debug information:**
            - Analysis result type: `{type(analysis_result).__name__}`
            - Has POI data: `{bool(analysis_result.get('pois', []) if isinstance(analysis_result, dict) else False)}`
            - POI count: `{len(analysis_result.get('pois', [])) if isinstance(analysis_result, dict) else 'N/A'}`
            """)
            
        # Add a retry button
        if st.button("🔄 Retry Map Rendering"):
            st.rerun()


@st.fragment(run_every=30)  # Auto-refresh every 30 seconds
def render_live_metrics(analysis_result: dict[str, Any]) -> None:
    """Render metrics that can update independently.
    
    This fragment displays key metrics and can auto-refresh to show
    the latest data without rerunning the entire app.
    
    Args:
        analysis_result: Analysis results containing metrics
    """
    if not analysis_result:
        return
    
    # Extract metrics with safe defaults
    poi_count = analysis_result.get('poi_count', 0)
    population = analysis_result.get('total_population', 0)
    area_km2 = analysis_result.get('area_km2', 0)
    census_units = analysis_result.get('census_units_analyzed', 0)
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="POIs Found",
            value=f"{poi_count:,}",
            delta=None,
            help="Number of points of interest found in the search area"
        )
    
    with col2:
        st.metric(
            label="Population",
            value=f"{population:,}",
            delta=None,
            help="Total population within the travel time area"
        )
    
    with col3:
        st.metric(
            label="Area",
            value=f"{area_km2:.1f} km²",
            delta=None,
            help="Total area covered by the travel time isochrone"
        )
    
    with col4:
        st.metric(
            label="Census Units",
            value=f"{census_units:,}",
            delta=None,
            help="Number of census block groups analyzed"
        )
    
    # Add timestamp
    import datetime
    st.caption(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")


@st.fragment
def render_demographic_charts(
    analysis_result: dict[str, Any],
    census_vars: list[str]
) -> None:
    """Render demographic charts as a fragment.
    
    This allows demographic visualizations to update independently
    when users change chart settings.
    
    Args:
        analysis_result: Analysis results containing demographic data
        census_vars: List of census variable codes to display
    """
    if not analysis_result or not census_vars:
        st.info("No demographic data to display. Select census variables to analyze.")
        return
    
    # Chart type selector
    chart_type = st.radio(
        "Chart Type",
        options=["Bar Chart", "Pie Chart", "Table"],
        horizontal=True
    )
    
    # Get demographic data
    demographics = analysis_result.get('demographics', {})
    
    if chart_type == "Bar Chart":
        import pandas as pd
        import plotly.express as px
        
        # Prepare data for bar chart
        data = []
        for var_code in census_vars:
            if var_code in demographics:
                data.append({
                    'Variable': var_code,
                    'Value': demographics[var_code]
                })
        
        if data:
            df = pd.DataFrame(data)
            fig = px.bar(
                df,
                x='Variable',
                y='Value',
                title="Demographic Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for selected variables")
    
    elif chart_type == "Pie Chart":
        # Pie chart implementation
        st.info("Pie chart visualization coming soon!")
    
    else:  # Table
        # Display as table
        table_data = {}
        for var_code in census_vars:
            if var_code in demographics:
                table_data[var_code] = demographics[var_code]
        
        if table_data:
            import pandas as pd
            df = pd.DataFrame.from_dict(table_data, orient='index', columns=['Value'])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data available for selected variables")


@st.fragment
def render_poi_table_fragment(
    analysis_result: dict[str, Any],
    page_size: int = 10
) -> None:
    """Render POI table as a fragment with pagination.
    
    This allows the POI table to have its own pagination without
    rerunning the entire app.
    
    Args:
        analysis_result: Analysis results containing POI data
        page_size: Number of POIs to show per page
    """
    pois = analysis_result.get('pois', [])
    
    if not pois:
        st.info("No POIs found in the analysis area.")
        return
    
    # Pagination controls
    total_pages = (len(pois) + page_size - 1) // page_size
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1
    )
    
    # Calculate indices
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(pois))
    
    # Display current page of POIs
    st.write(f"Showing POIs {start_idx + 1} to {end_idx} of {len(pois)}")
    
    # Create table data
    table_data = []
    for poi in pois[start_idx:end_idx]:
        # Extract name from tags if available
        name = 'Unnamed'
        if 'tags' in poi and isinstance(poi['tags'], dict):
            name = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
        elif 'name' in poi:
            name = poi['name']
        
        # Extract address from tags if available
        address = 'N/A'
        if 'tags' in poi and isinstance(poi['tags'], dict):
            # Try different address fields from OSM tags
            addr_parts = []
            if poi['tags'].get('addr:housenumber'):
                addr_parts.append(poi['tags']['addr:housenumber'])
            if poi['tags'].get('addr:street'):
                addr_parts.append(poi['tags']['addr:street'])
            if poi['tags'].get('addr:city'):
                addr_parts.append(poi['tags']['addr:city'])
            if addr_parts:
                address = ' '.join(addr_parts)
        
        table_data.append({
            'Name': name,
            'Type': poi.get('type', 'Unknown'),
            'Distance': f"{poi.get('distance', 0):.2f} km",
            'Address': address
        })
    
    if table_data:
        import pandas as pd
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Page navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if page > 1:
            if st.button("← Previous"):
                st.rerun()
    
    with col2:
        st.write(f"Page {page} of {total_pages}")
    
    with col3:
        if page < total_pages:
            if st.button("Next →"):
                st.rerun()