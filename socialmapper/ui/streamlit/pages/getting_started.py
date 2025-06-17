"""Getting Started page for the Streamlit application."""

import os
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from typing import Dict, List, Tuple, Any

from socialmapper import SocialMapperBuilder, SocialMapperClient
from ..components.maps import create_poi_map
from ..utils.formatters import format_census_variable
from ..config import CENSUS_VARIABLES, DEFAULT_CENSUS_VARS, POI_TYPES


def render_getting_started_page():
    """Render the Getting Started tutorial page."""
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
    
    # Extract census variable codes
    census_var_codes = [var[0] for var in census_variables]
    st.session_state.census_vars = census_var_codes
    
    with st.spinner("Running analysis..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize client
            status_text.text("Initializing SocialMapper...")
            progress_bar.progress(10)
            
            client = SocialMapperClient()
            
            # Build configuration
            status_text.text("Building configuration...")
            progress_bar.progress(20)
            
            # Parse location
            if "," in location:
                parts = location.split(",")
                city = parts[0].strip()
                state = parts[1].strip()
                
                config = (
                    SocialMapperBuilder()
                    .with_location(city=city, state=state)
                    .with_poi_search(poi_category, poi_type)
                    .with_travel_time(travel_time, travel_mode)
                    .with_census_variables(census_var_codes)
                    .build()
                )
            else:
                config = (
                    SocialMapperBuilder()
                    .with_location(address=location)
                    .with_poi_search(poi_category, poi_type)
                    .with_travel_time(travel_time, travel_mode)
                    .with_census_variables(census_var_codes)
                    .build()
                )
            
            # Execute analysis
            status_text.text(f"Searching for {poi_type} locations...")
            progress_bar.progress(40)
            
            result = client.analyze(config)
            
            if result.is_ok():
                status_text.text("Processing results...")
                progress_bar.progress(80)
                
                analysis_result = result.unwrap()
                st.session_state.analysis_results = analysis_result
                st.session_state.analysis_complete = True
                
                progress_bar.progress(100)
                status_text.text("Analysis complete!")
                st.success("✅ Analysis completed successfully!")
                st.rerun()
            else:
                error = result.unwrap_err()
                st.error(f"Analysis failed: {error}")
                progress_bar.progress(0)
                status_text.text("")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            progress_bar.progress(0)
            status_text.text("")


def render_results():
    """Render analysis results if available."""
    if not st.session_state.get('analysis_complete') or not st.session_state.get('analysis_results'):
        return
    
    result = st.session_state.analysis_results
    
    st.subheader("Analysis Results")
    
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


def render_metrics(result: Any):
    """Render key metrics from the analysis."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="POIs Found",
            value=len(result.pois) if hasattr(result, 'pois') else 0,
            help="Number of points of interest within the travel time area"
        )
    
    with col2:
        area_km2 = result.metadata.get('area_km2', 0) if hasattr(result, 'metadata') else 0
        st.metric(
            label="Area Coverage",
            value=f"{area_km2:.1f} km²",
            help="Total area covered by the isochrone"
        )
    
    with col3:
        total_pop = result.demographics.get('B01003_001E', 0) if hasattr(result, 'demographics') else 0
        st.metric(
            label="Population Served",
            value=f"{total_pop:,.0f}",
            help="Total population within the accessible area"
        )
    
    with col4:
        median_income = result.demographics.get('B19013_001E', 0) if hasattr(result, 'demographics') else 0
        st.metric(
            label="Median Income",
            value=f"${median_income:,.0f}",
            help="Median household income in the area"
        )


def render_map(result: Any):
    """Render the interactive map with POIs."""
    st.subheader("📍 Interactive Map")
    
    if hasattr(result, 'metadata') and hasattr(result, 'pois'):
        center_lat = result.metadata.get('center_lat', 39.8283)
        center_lon = result.metadata.get('center_lon', -98.5795)
        
        # Create POI dataframe
        poi_df = pd.DataFrame([
            {
                'name': poi.get('tags', {}).get('name', 'Unnamed POI'),
                'lat': poi['lat'],
                'lon': poi['lon']
            }
            for poi in result.pois[:20]  # Limit to 20 POIs
        ])
        
        # Create map with POIs
        m = create_poi_map(
            center_lat, center_lon, 
            poi_df,
            result.isochrone if hasattr(result, 'isochrone') else None
        )
        
        st_folium(m, height=400, width=700)
    else:
        st.info("Map data not available")


def render_demographics(result: Any):
    """Render demographic information."""
    st.subheader("📊 Demographics")
    
    if hasattr(result, 'demographics') and st.session_state.get('census_vars'):
        demo_data = []
        for var_code in st.session_state.census_vars:
            if var_code in result.demographics:
                value = result.demographics[var_code]
                formatted = format_census_variable(var_code, value)
                demo_data.append({"Metric": formatted.split(":")[0], "Value": formatted.split(":")[1].strip()})
        
        if demo_data:
            df_demo = pd.DataFrame(demo_data)
            st.dataframe(df_demo, use_container_width=True, hide_index=True)
        else:
            st.info("No demographic data available")
    else:
        st.info("No demographic data available")


def render_poi_table(result: Any):
    """Render the POI table."""
    st.subheader("🏢 Points of Interest")
    
    if hasattr(result, 'pois') and result.pois:
        poi_data = []
        for poi in result.pois[:20]:  # Show first 20
            tags = poi.get('tags', {})
            poi_data.append({
                "Name": tags.get('name', 'Unnamed'),
                "Distance (m)": round(poi.get('distance', 0)),
                "Travel Time (min)": round(poi.get('travel_time', 0))
            })
        
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
        
        if len(result.pois) > 20:
            st.info(f"Showing 20 of {len(result.pois)} POIs found")
    else:
        st.info("No POIs found in this area")


def render_export_options(result: Any):
    """Render export/download options."""
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Download CSV", type="secondary"):
            # TODO: Implement CSV export
            st.info("CSV export will be implemented soon!")
    
    with col2:
        if st.button("📄 Generate Full Report", type="secondary"):
            st.info("Report generation will be implemented soon!")