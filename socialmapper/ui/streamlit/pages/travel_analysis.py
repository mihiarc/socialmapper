"""Travel Time Analysis - Deep dive into isochrone and accessibility analytics."""

import logging
from typing import Any, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ..components.dialogs import show_error_dialog, dialogs_available
from ..components.fragments import render_live_metrics
from ..config import POI_TYPES, CENSUS_VARIABLES
from ..utils.cache import run_cached_analysis, get_poi_types

logger = logging.getLogger(__name__)

def main():
    """Main function for the Travel Analysis page."""
    
    # Header section
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        st.title("🗺️ Travel Time Analysis")
    
    with col2:
        if st.button("ℹ️ Help", use_container_width=True):
            st.info("Compare multiple travel modes and analyze accessibility metrics")
    
    with col3:
        st.metric(
            label="Analysis Type",
            value="Multi-Modal",
            delta="Advanced"
        )

    st.markdown("""
    **Deep dive into travel accessibility and isochrone analytics**

    Compare multiple travel modes, analyze population coverage, and explore detailed accessibility metrics 
    for points of interest in your selected area.
    """)

    # Configuration section in main content area
    st.header("📋 Analysis Configuration")
    
    # Create configuration columns
    config_col1, config_col2 = st.columns(2)
    
    with config_col1:
        st.subheader("📍 Location")
        location = st.text_input(
            "Enter Location",
            value="Durham, North Carolina",
            help="Format: 'City, State' or 'City, State Abbreviation'"
        )
    
    with config_col2:
        st.subheader("🎯 Points of Interest")
        poi_types = get_poi_types()
        
        # Category selection
        category_display_names = {
            "amenity": "🏛️ Amenities (libraries, schools, hospitals)",
            "shop": "🛍️ Shopping (stores, markets, pharmacies)",
            "leisure": "🏃 Recreation (parks, sports, entertainment)",
            "public_transport": "🚌 Public Transport (stations, stops)",
            "railway": "🚂 Railway (stations, rail stops)"
        }
        
        selected_category_display = st.selectbox(
            "POI Category",
            options=list(category_display_names.values()),
            index=0
        )
        
        # Find the actual category key
        poi_category = None
        for key, display_name in category_display_names.items():
            if display_name == selected_category_display:
                poi_category = key
                break
        
        # POI type selection
        if poi_category:
            poi_options = poi_types.get(poi_category, [])
            selected_poi = st.selectbox(
                "POI Type",
                options=poi_options,
                index=0 if poi_options else None
            )
        else:
            selected_poi = None
            st.error("Please select a valid POI category")
    
    # Travel configuration section
    st.markdown("---")
    config_col3, config_col4 = st.columns(2)
    
    with config_col3:
        st.subheader("🚶 Travel Modes")
        travel_modes = st.multiselect(
            "Select modes to compare",
            options=["walk", "bike", "drive"],
            default=["walk", "drive"],
            help="Select multiple modes for comparison analysis"
        )
    
    with config_col4:
        st.subheader("⏱️ Travel Time")
        travel_time = st.slider(
            "Maximum Travel Time (minutes)",
            min_value=5,
            max_value=60,
            value=15,
            step=5,
            help="Maximum travel time for isochrone generation"
        )
    
    # Advanced options in expandable section
    with st.expander("⚙️ Advanced Options"):
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            max_pois = st.slider(
                "Maximum POIs to analyze",
                min_value=1,
                max_value=20,
                value=10,
                help="Limit POIs for faster analysis"
            )
            
            show_performance = st.checkbox(
                "Show performance metrics",
                value=True,
                help="Display processing times and cache statistics"
            )
        
        with adv_col2:
            enable_clustering = st.checkbox(
                "Enable intelligent clustering",
                value=True,
                help="Use advanced clustering for better performance"
            )

    # Main analysis section
    st.markdown("---")
    if location and selected_poi and travel_modes:
        if st.button("🚀 Run Multi-Modal Analysis", type="primary", use_container_width=True):
            with st.spinner("Running comprehensive travel time analysis..."):
                # Store results for each travel mode
                results_by_mode = {}
                analysis_errors = []
            
                # Run analysis for each selected travel mode
                for mode in travel_modes:
                    try:
                        result = run_cached_analysis(
                            location=location,
                            poi_type=poi_category,
                            poi_name=selected_poi,
                            travel_time=travel_time,
                            travel_mode=mode,
                            census_vars=["B01003_001E", "B19013_001E", "B25077_001E"]
                        )
                    
                    if result.get('success'):
                        results_by_mode[mode] = result['data']
                    else:
                        analysis_errors.append(f"{mode.title()}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    analysis_errors.append(f"{mode.title()}: {str(e)}")
                    logger.error(f"Analysis failed for {mode}: {e}")
            
            # Display results if we have any successful analyses
            if results_by_mode:
                st.success(f"✅ Analysis completed for {len(results_by_mode)} travel mode(s)")
                
                # Store results in session state for persistence
                st.session_state.travel_analysis_results = results_by_mode
                st.session_state.travel_analysis_config = {
                    'location': location,
                    'poi_category': poi_category,
                    'poi_name': selected_poi,
                    'travel_time': travel_time,
                    'travel_modes': travel_modes
                }
                
            else:
                st.error("❌ Analysis failed for all travel modes")
                if analysis_errors:
                    for error in analysis_errors:
                        st.error(error)

# Display results if available
if hasattr(st.session_state, 'travel_analysis_results') and st.session_state.travel_analysis_results:
    results = st.session_state.travel_analysis_results
    config = st.session_state.travel_analysis_config
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Summary metrics at the top
    st.subheader("📈 Summary Metrics")
    
    # Create summary comparison table
    summary_data = []
    for mode, data in results.items():
        summary_data.append({
            'Travel Mode': mode.title(),
            'POIs Found': data.get('poi_count', 0),
            'Population Served': f"{data.get('total_population', 0):,}",
            'Area Coverage (km²)': f"{data.get('area_km2', 0):.2f}",
            'Census Units': data.get('census_units_analyzed', 0)
        })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Multi-modal comparison charts
    st.subheader("📊 Travel Mode Comparison")
    
    # Create comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        # POI accessibility comparison
        poi_counts = [results[mode].get('poi_count', 0) for mode in results.keys()]
        mode_names = [mode.title() for mode in results.keys()]
        
        fig_poi = px.bar(
            x=mode_names,
            y=poi_counts,
            title="POIs Accessible by Travel Mode",
            labels={'x': 'Travel Mode', 'y': 'Number of POIs'},
            color=mode_names,
            color_discrete_map={
                'Walk': '#ff7f00',
                'Bike': '#4daf4a', 
                'Drive': '#377eb8'
            }
        )
        fig_poi.update_layout(showlegend=False)
        st.plotly_chart(fig_poi, use_container_width=True)
    
    with col2:
        # Population coverage comparison
        populations = [results[mode].get('total_population', 0) for mode in results.keys()]
        
        fig_pop = px.bar(
            x=mode_names,
            y=populations,
            title="Population Served by Travel Mode",
            labels={'x': 'Travel Mode', 'y': 'Population'},
            color=mode_names,
            color_discrete_map={
                'Walk': '#ff7f00',
                'Bike': '#4daf4a',
                'Drive': '#377eb8'
            }
        )
        fig_pop.update_layout(showlegend=False)
        st.plotly_chart(fig_pop, use_container_width=True)
    
    # Area coverage comparison
    areas = [results[mode].get('area_km2', 0) for mode in results.keys()]
    
    fig_area = px.pie(
        values=areas,
        names=mode_names,
        title="Coverage Area by Travel Mode (km²)",
        color_discrete_map={
            'Walk': '#ff7f00',
            'Bike': '#4daf4a',
            'Drive': '#377eb8'
        }
    )
    st.plotly_chart(fig_area, use_container_width=True)
    
    # Detailed POI Analysis
    st.subheader("🎯 POI Details by Travel Mode")
    
    # Create tabs for each travel mode
    mode_tabs = st.tabs([f"{mode.title()} Mode" for mode in results.keys()])
    
    for i, (mode, data) in enumerate(results.items()):
        with mode_tabs[i]:
            pois = data.get('pois', [])
            
            if pois:
                # Create POI details table
                poi_details = []
                for poi in pois:
                    # Extract name from tags
                    name = 'Unnamed'
                    if 'tags' in poi and isinstance(poi['tags'], dict):
                        name = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
                    
                    # Extract address
                    address = 'N/A'
                    if 'tags' in poi and isinstance(poi['tags'], dict):
                        addr_parts = []
                        if poi['tags'].get('addr:housenumber'):
                            addr_parts.append(poi['tags']['addr:housenumber'])
                        if poi['tags'].get('addr:street'):
                            addr_parts.append(poi['tags']['addr:street'])
                        if addr_parts:
                            address = ' '.join(addr_parts)
                    
                    poi_details.append({
                        'Name': name,
                        'Type': poi.get('type', 'Unknown'),
                        'Latitude': f"{poi.get('lat', 0):.6f}",
                        'Longitude': f"{poi.get('lon', 0):.6f}",
                        'Address': address
                    })
                
                poi_df = pd.DataFrame(poi_details)
                st.dataframe(poi_df, use_container_width=True, hide_index=True)
                
                # Show demographics for this mode
                demographics = data.get('demographics', {})
                if demographics:
                    st.markdown("**📊 Demographics in Travel Area**")
                    dem_col1, dem_col2, dem_col3 = st.columns(3)
                    
                    with dem_col1:
                        pop = demographics.get('B01003_001E', 0)
                        st.metric("Total Population", f"{pop:,.0f}" if pop else "N/A")
                    
                    with dem_col2:
                        income = demographics.get('B19013_001E', 0)
                        st.metric("Median Income", f"${income:,.0f}" if income else "N/A")
                    
                    with dem_col3:
                        home_value = demographics.get('B25077_001E', 0)
                        st.metric("Median Home Value", f"${home_value:,.0f}" if home_value else "N/A")
            else:
                st.warning(f"No POIs found for {mode} mode within {travel_time} minutes")
    
    # Multi-modal interactive map
    from ..components.multi_modal_map import (
        render_multi_modal_map, 
        render_travel_time_comparison,
        render_accessibility_insights
    )
    
    # Render the enhanced multi-modal map
    render_multi_modal_map(results, height=700)
    
    # Travel time comparison analysis
    render_travel_time_comparison(results, config['travel_time'])
    
    # Accessibility insights and recommendations
    render_accessibility_insights(results)
    
    # Performance metrics (if enabled)
    if show_performance and hasattr(st.session_state, 'travel_analysis_config'):
        st.subheader("⚡ Performance Metrics")
        
        with st.expander("View detailed performance information"):
            st.markdown("**Analysis Configuration:**")
            config_info = st.session_state.travel_analysis_config
            
            st.json({
                'Location': config_info['location'],
                'POI Category': config_info['poi_category'],
                'POI Type': config_info['poi_name'],
                'Travel Time': f"{config_info['travel_time']} minutes",
                'Travel Modes': config_info['travel_modes'],
                'Total Modes Analyzed': len(results),
                'Cache Status': 'Enabled'
            })

else:
    # Show instructions when no analysis has been run
    st.info("""
    👈 **Configure your analysis in the sidebar and click 'Run Multi-Modal Analysis' to get started**
    
    **Features:**
    - 🚶‍♂️ Compare walk, bike, and drive accessibility
    - 📊 Detailed population and demographic analysis  
    - 🗺️ Interactive travel time maps
    - 📈 Performance metrics and optimization insights
    - 📥 Export capabilities for further analysis
    """)
    
    # Sample visualization to show capabilities
    st.subheader("📊 Sample Analysis")
    st.markdown("*Example of what your analysis will look like:*")
    
    # Create sample charts
    sample_modes = ['Walk', 'Bike', 'Drive']
    sample_pois = [3, 8, 15]
    sample_population = [2500, 8900, 25000]
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_sample = px.bar(
            x=sample_modes,
            y=sample_pois,
            title="Sample: POIs Accessible by Travel Mode",
            color=sample_modes,
            color_discrete_map={
                'Walk': '#ff7f00',
                'Bike': '#4daf4a',
                'Drive': '#377eb8'
            }
        )
        fig_sample.update_layout(showlegend=False)
        st.plotly_chart(fig_sample, use_container_width=True)
    
    with col2:
        fig_sample2 = px.bar(
            x=sample_modes,
            y=sample_population,
            title="Sample: Population Served by Travel Mode",
            color=sample_modes,
            color_discrete_map={
                'Walk': '#ff7f00',
                'Bike': '#4daf4a',
                'Drive': '#377eb8'
            }
        )
        fig_sample2.update_layout(showlegend=False)
        st.plotly_chart(fig_sample2, use_container_width=True)