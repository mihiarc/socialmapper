"""Travel Modes comparison page for the Streamlit application."""

import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, Any


def render_travel_modes_page():
    """Render the Travel Modes tutorial page."""
    st.header("Travel Mode Comparison")
    
    st.markdown("""
    Compare accessibility across different modes of transportation to understand how travel 
    options affect access to community resources.
    
    **What you'll learn:**
    - 🚶 Walking accessibility (5 km/h)
    - 🚴 Biking accessibility (15 km/h) 
    - 🚗 Driving accessibility (city speeds)
    - 📊 Comparative analysis and equity insights
    """)
    
    # Configuration form
    st.subheader("Configure Multi-Modal Analysis")
    
    with st.form("travel_mode_analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input(
                "Location",
                value="Chapel Hill, North Carolina"
            )
            
            poi_type = st.selectbox(
                "POI Type",
                options=["park", "library", "hospital", "school"]
            )
        
        with col2:
            travel_time = st.slider(
                "Travel Time (minutes)",
                min_value=5,
                max_value=30,
                value=15
            )
            
            modes = st.multiselect(
                "Travel Modes to Compare",
                options=["walk", "bike", "drive"],
                default=["walk", "bike", "drive"]
            )
        
        submitted = st.form_submit_button("Compare Travel Modes")
    
    if submitted:
        with st.spinner("Running multi-modal analysis..."):
            # Placeholder for actual analysis
            st.info("Travel mode comparison analysis coming soon!")
            
            # Sample visualization
            st.subheader("📊 Accessibility Comparison")
            
            # Create sample data
            sample_data = pd.DataFrame({
                'Mode': ['Walk', 'Bike', 'Drive'],
                'POIs Accessible': [3, 8, 15],
                'Population Served': [5000, 12000, 25000],
                'Area (km²)': [2.5, 7.8, 18.5]
            })
            
            # Bar chart
            fig = px.bar(
                sample_data,
                x='Mode',
                y='POIs Accessible',
                color='Mode',
                title='POIs Accessible by Travel Mode'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrics comparison
            st.subheader("🎯 Key Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Walking Coverage",
                    "2.5 km²",
                    help="Area accessible within 15 minutes walking"
                )
            
            with col2:
                st.metric(
                    "Biking Advantage",
                    "+5 POIs",
                    delta_color="normal",
                    help="Additional POIs accessible by bike vs walking"
                )
            
            with col3:
                st.metric(
                    "Driving Reach",
                    "5x larger",
                    help="Area coverage compared to walking"
                )
            
            # Equity insights
            st.subheader("⚖️ Equity Insights")
            st.info("""
            **Key Findings:**
            - 30% of the population lacks vehicle access
            - Walking-only access covers essential services for 5,000 residents
            - Bike infrastructure improvements could serve 7,000 additional residents
            """)