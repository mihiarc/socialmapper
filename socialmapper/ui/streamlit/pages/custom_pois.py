"""Custom POIs page for the Streamlit application."""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any


def render_custom_pois_page():
    """Render the Custom POIs tutorial page."""
    st.header("Custom Points of Interest")
    
    st.markdown("""
    This tutorial demonstrates how to analyze accessibility for your own custom locations, 
    such as specific addresses, facilities, or points of interest not available in OpenStreetMap.
    
    **What you'll learn:**
    - 📤 Upload custom location data via CSV
    - 🗺️ Visualize custom points on a map
    - 🔍 Analyze accessibility from these locations
    - 📊 Compare multiple custom locations
    """)
    
    # File upload section
    st.subheader("Upload Custom Locations")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="CSV should have columns: name, lat, lon"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            required_cols = ['name', 'lat', 'lon']
            if all(col in df.columns for col in required_cols):
                st.success(f"✅ Loaded {len(df)} locations")
                
                # Preview data
                st.subheader("Location Preview")
                st.dataframe(df.head(10))
                
                # Map preview
                if st.button("Preview on Map"):
                    st.info("Map preview coming soon!")
                
                # Analysis configuration
                st.subheader("Configure Analysis")
                
                with st.form("custom_analysis"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        travel_time = st.slider(
                            "Travel Time (minutes)",
                            min_value=5,
                            max_value=30,
                            value=15
                        )
                    
                    with col2:
                        travel_mode = st.selectbox(
                            "Travel Mode",
                            options=["walk", "bike", "drive"]
                        )
                    
                    submitted = st.form_submit_button("Run Analysis")
                    
                    if submitted:
                        st.info("Custom POI analysis coming soon!")
            else:
                st.error(f"CSV must contain columns: {', '.join(required_cols)}")
                st.error(f"Found columns: {', '.join(df.columns)}")
                
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
    
    # Example template
    with st.expander("📋 Download Example Template"):
        example_df = pd.DataFrame({
            'name': ['Location 1', 'Location 2', 'Location 3'],
            'lat': [35.9940, 36.0014, 35.9131],
            'lon': [-78.8986, -78.9382, -79.0558]
        })
        
        csv = example_df.to_csv(index=False)
        st.download_button(
            label="Download Template CSV",
            data=csv,
            file_name="custom_locations_template.csv",
            mime="text/csv"
        )