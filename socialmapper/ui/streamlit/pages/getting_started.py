"""Getting Started page for the Streamlit application - Fixed version."""

import os
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from typing import Dict, List, Tuple, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Try importing SocialMapper components with fallback
try:
    from socialmapper import SocialMapperBuilder, SocialMapperClient
    SOCIALMAPPER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import SocialMapper components: {e}")
    SOCIALMAPPER_AVAILABLE = False

from ..components.maps import create_poi_map
from ..utils.formatters import format_census_variable
from ..config import CENSUS_VARIABLES, DEFAULT_CENSUS_VARS, POI_TYPES


def render_getting_started_page():
    """Render the Getting Started tutorial page."""
    # Check if SocialMapper is available
    if not SOCIALMAPPER_AVAILABLE:
        st.error("SocialMapper components are not available. Please check your installation.")
        st.code("pip install -e .")
        return
    
    render_header()
    render_input_form()
    render_results()


def render_header():
    """Render the page header and introduction."""
    st.header("Getting Started with SocialMapper")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        Welcome to **SocialMapper**! This tutorial will guide you through a basic accessibility analysis.
        
        **What you'll learn:**
        - 🔍 Search for points of interest (POIs) in any US location
        - ⏱️ Generate travel-time areas (isochrones)
        - 📊 Analyze demographics within accessible areas
        - 📥 Export results for further analysis
        """)
    
    with col2:
        st.metric(
            label="Tutorial Progress",
            value="Step 1 of 6",
            delta="Basic Analysis"
        )
    
    st.info("""
    **Quick Start:** Enter a location below (e.g., "Durham, North Carolina") and click 
    "Run Analysis" to see SocialMapper in action. The analysis will find nearby libraries 
    and show demographic data for the surrounding area.
    """)


def render_input_form():
    """Render the analysis input form."""
    st.subheader("Configure Your Analysis")
    
    with st.form("basic_analysis"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            location = st.text_input(
                "Location",
                value="Durham, North Carolina",
                help="Enter a city and state (e.g., 'San Francisco, California')"
            )
        
        with col2:
            # POI category and type selection
            poi_category = st.selectbox(
                "POI Category",
                options=list(POI_TYPES.keys()),
                index=0
            )
            
            poi_type = st.selectbox(
                "POI Type",
                options=POI_TYPES[poi_category],
                index=0
            )
        
        with col3:
            travel_time = st.slider(
                "Travel Time (minutes)",
                min_value=5,
                max_value=30,
                value=15,
                step=5
            )
            
            travel_mode = st.selectbox(
                "Travel Mode",
                options=["walk", "bike", "drive"],
                index=0
            )
        
        # Census variables selection
        census_variables = st.multiselect(
            "Census Variables to Include",
            options=[(code, name) for code, name in CENSUS_VARIABLES.items()],
            default=[(code, CENSUS_VARIABLES[code]) for code in DEFAULT_CENSUS_VARS],
            format_func=lambda x: x[1]
        )
        
        submitted = st.form_submit_button("🚀 Run Analysis", type="primary")
    
    if submitted:
        handle_form_submission(location, poi_category, poi_type, travel_time, 
                             travel_mode, census_variables)


def handle_form_submission(location: str, poi_category: str, poi_type: str,
                         travel_time: int, travel_mode: str, 
                         census_variables: List[Tuple[str, str]]):
    """Handle form submission and run analysis."""
    # Check for API key
    if not os.environ.get('CENSUS_API_KEY'):
        st.error("Please configure your Census API key in the sidebar first!")
        return
    
    # Validate inputs
    if not location or not location.strip():
        st.error("Please enter a valid location!")
        return
    
    # Extract census variable codes
    census_var_codes = [var[0] for var in census_variables] if census_variables else []
    st.session_state.census_vars = census_var_codes
    
    with st.spinner("Running analysis..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize client
            status_text.text("Initializing SocialMapper...")
            progress_bar.progress(10)
            
            with SocialMapperClient() as client:
                # Build configuration
                status_text.text("Building configuration...")
                progress_bar.progress(20)
                
                # Parse location
                builder = SocialMapperBuilder()
                
                if "," in location:
                    parts = location.split(",", 1)  # Split only on first comma
                    city = parts[0].strip()
                    state = parts[1].strip() if len(parts) > 1 else ""
                    
                    if city and state:
                        builder = builder.with_location(city, state)
                    else:
                        builder = builder.with_location(location)
                else:
                    builder = builder.with_location(location)
                
                # Add other configuration
                config = (
                    builder
                    .with_osm_pois(poi_category, poi_type)
                    .with_travel_time(travel_time)
                    .with_travel_mode(travel_mode)
                    .with_census_variables(*census_var_codes)
                    .build()
                )
                
                # Execute analysis
                status_text.text(f"Searching for {poi_type} locations...")
                progress_bar.progress(40)
                
                result = client.run_analysis(config)
                
                if result.is_ok():
                    status_text.text("Processing results...")
                    progress_bar.progress(80)
                    
                    analysis_result = result.unwrap()
                    
                    # Debug: Log the result structure
                    logger.info(f"Analysis result type: {type(analysis_result)}")
                    logger.info(f"Analysis result attributes: {dir(analysis_result)}")
                    
                    st.session_state.analysis_results = analysis_result
                    st.session_state.analysis_complete = True
                    
                    progress_bar.progress(100)
                    status_text.text("Analysis complete!")
                    st.success("✅ Analysis completed successfully!")
                    st.rerun()
                else:
                    error = result.unwrap_err()
                    st.error(f"Analysis failed: {error}")
                    logger.error(f"Analysis error: {error}")
                    progress_bar.progress(0)
                    status_text.text("")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.exception("Error during analysis")
            progress_bar.progress(0)
            status_text.text("")


def render_results():
    """Render analysis results if available."""
    if not st.session_state.get('analysis_complete') or not st.session_state.get('analysis_results'):
        return
    
    result = st.session_state.analysis_results
    
    st.subheader("Analysis Results")
    
    # Debug info in expander
    with st.expander("Debug Info", expanded=False):
        st.write("Result type:", type(result))
        st.write("Result attributes:", [attr for attr in dir(result) if not attr.startswith('_')])
        if hasattr(result, '__dict__'):
            st.write("Result data:", result.__dict__)
    
    # Display metrics
    render_metrics(result)
    
    # Display map and demographics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_map(result)
    
    with col2:
        render_demographics(result)
    
    # Display POI table
    render_poi_table(result)
    
    # Export options
    render_export_options(result)


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from object with fallback."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def safe_get_dict(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get dictionary value with fallback."""
    try:
        if hasattr(obj, 'get'):
            return obj.get(key, default)
        elif hasattr(obj, key):
            return getattr(obj, key, default)
        else:
            return default
    except Exception:
        return default


def render_metrics(result: Any):
    """Render key metrics from the analysis."""
    col1, col2, col3, col4 = st.columns(4)
    
    # Safely extract POIs
    pois = safe_get_attr(result, 'pois', [])
    if not isinstance(pois, list):
        pois = []
    
    # Safely extract metadata
    metadata = safe_get_attr(result, 'metadata', {})
    if not isinstance(metadata, dict):
        metadata = {}
    
    # Safely extract demographics
    demographics = safe_get_attr(result, 'demographics', {})
    if not isinstance(demographics, dict):
        demographics = {}
    
    with col1:
        st.metric(
            label="POIs Found",
            value=len(pois),
            help="Number of points of interest within the travel time area"
        )
    
    with col2:
        area_km2 = safe_get_dict(metadata, 'area_km2', 0)
        st.metric(
            label="Area Coverage",
            value=f"{float(area_km2):.1f} km²",
            help="Total area covered by the isochrone"
        )
    
    with col3:
        total_pop = safe_get_dict(demographics, 'B01003_001E', 0)
        st.metric(
            label="Population Served",
            value=f"{int(total_pop):,}",
            help="Total population within the accessible area"
        )
    
    with col4:
        from socialmapper.census.utils import format_monetary_value
        
        median_income = safe_get_dict(demographics, 'B19013_001E', None)
        st.metric(
            label="Median Income",
            value=format_monetary_value(median_income, 'B19013_001E'),
            help="Median household income in the area"
        )


def render_map(result: Any):
    """Render the interactive map with POIs."""
    st.subheader("📍 Interactive Map")
    
    try:
        metadata = safe_get_attr(result, 'metadata', {})
        pois = safe_get_attr(result, 'pois', [])
        
        if not isinstance(metadata, dict):
            metadata = {}
        if not isinstance(pois, list):
            pois = []
        
        center_lat = safe_get_dict(metadata, 'center_lat', 39.8283)
        center_lon = safe_get_dict(metadata, 'center_lon', -98.5795)
        
        # Create POI dataframe
        poi_data = []
        for poi in pois[:20]:  # Limit to 20 POIs
            if isinstance(poi, dict):
                tags = poi.get('tags', {}) if isinstance(poi.get('tags'), dict) else {}
                poi_data.append({
                    'name': tags.get('name', 'Unnamed POI'),
                    'lat': float(poi.get('lat', 0)),
                    'lon': float(poi.get('lon', 0))
                })
        
        if poi_data:
            poi_df = pd.DataFrame(poi_data)
            
            # Get isochrone data safely
            isochrone = safe_get_attr(result, 'isochrone', None)
            
            # Create map with POIs
            m = create_poi_map(
                center_lat, center_lon, 
                poi_df,
                isochrone
            )
            
            st_folium(m, height=400, width=700)
        else:
            st.info("No POI data available to display on map")
            
    except Exception as e:
        st.error(f"Error rendering map: {str(e)}")
        logger.exception("Map rendering error")


def render_demographics(result: Any):
    """Render demographic information."""
    st.subheader("📊 Demographics")
    
    try:
        demographics = safe_get_attr(result, 'demographics', {})
        census_vars = st.session_state.get('census_vars', [])
        
        if demographics and census_vars:
            demo_data = []
            for var_code in census_vars:
                if var_code in demographics:
                    value = demographics[var_code]
                    try:
                        formatted = format_census_variable(var_code, value)
                        parts = formatted.split(":", 1)
                        if len(parts) == 2:
                            demo_data.append({
                                "Metric": parts[0].strip(), 
                                "Value": parts[1].strip()
                            })
                    except Exception as e:
                        logger.warning(f"Error formatting census variable {var_code}: {e}")
            
            if demo_data:
                df_demo = pd.DataFrame(demo_data)
                st.dataframe(df_demo, use_container_width=True, hide_index=True)
            else:
                st.info("No demographic data available")
        else:
            st.info("No demographic data available")
            
    except Exception as e:
        st.error(f"Error displaying demographics: {str(e)}")
        logger.exception("Demographics rendering error")


def render_poi_table(result: Any):
    """Render the POI table."""
    st.subheader("🏢 Points of Interest")
    
    try:
        pois = safe_get_attr(result, 'pois', [])
        
        if pois and isinstance(pois, list):
            poi_data = []
            for poi in pois[:20]:  # Show first 20
                if isinstance(poi, dict):
                    tags = poi.get('tags', {}) if isinstance(poi.get('tags'), dict) else {}
                    poi_data.append({
                        "Name": tags.get('name', 'Unnamed'),
                        "Distance (m)": round(float(poi.get('distance', 0))),
                        "Travel Time (min)": round(float(poi.get('travel_time', 0)))
                    })
            
            if poi_data:
                df_pois = pd.DataFrame(poi_data)
                
                # Sort by distance
                df_pois = df_pois.sort_values('Distance (m)')
                
                st.dataframe(
                    df_pois,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Distance (m)": st.column_config.NumberColumn(format="%d m"),
                        "Travel Time (min)": st.column_config.NumberColumn(format="%d min")
                    }
                )
                
                if len(pois) > 20:
                    st.info(f"Showing 20 of {len(pois)} POIs found")
            else:
                st.info("No POI data to display")
        else:
            st.info("No POIs found in this area")
            
    except Exception as e:
        st.error(f"Error displaying POIs: {str(e)}")
        logger.exception("POI table rendering error")


def render_export_options(result: Any):
    """Render export/download options."""
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Download CSV", type="secondary"):
            try:
                # TODO: Implement actual CSV export
                st.info("CSV export will be implemented soon!")
            except Exception as e:
                st.error(f"Export error: {str(e)}")
    
    with col2:
        if st.button("📄 Generate Full Report", type="secondary"):
            st.info("Report generation will be implemented soon!")