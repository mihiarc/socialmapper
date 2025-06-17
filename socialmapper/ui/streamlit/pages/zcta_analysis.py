"""ZCTA Analysis page for the Streamlit application."""

import streamlit as st
from typing import List, Dict, Any


def render_zcta_analysis_page():
    """Render the ZCTA Analysis tutorial page."""
    st.header("ZIP Code Tabulation Area (ZCTA) Analysis")
    
    st.markdown("""
    Analyze accessibility at the ZIP code level using Census ZIP Code Tabulation Areas (ZCTAs).
    This is useful for regional planning and understanding broader geographic patterns.
    
    **What you'll learn:**
    - 📮 Working with ZIP codes and ZCTAs
    - 🗺️ Regional accessibility analysis
    - 📊 Comparing Block Group vs ZCTA data
    - 📈 Aggregated demographic insights
    """)
    
    # Educational content
    with st.expander("📚 Understanding ZCTAs vs ZIP Codes"):
        st.markdown("""
        **Key Differences:**
        - **ZIP Codes**: Postal delivery routes that can change
        - **ZCTAs**: Statistical areas that approximate ZIP codes for census data
        - **Block Groups**: Smaller units (600-3,000 people) for detailed analysis
        
        **When to use ZCTAs:**
        - Regional planning studies
        - Comparing multiple ZIP code areas
        - When Block Group detail isn't needed
        """)
    
    # Analysis form
    st.subheader("Configure ZCTA Analysis")
    
    with st.form("zcta_analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            zcta_codes = st.text_area(
                "ZIP Codes (one per line)",
                value="27701\n27705\n27707",
                help="Enter ZIP codes to analyze"
            )
            
            poi_type = st.selectbox(
                "POI Type",
                options=["library", "hospital", "school", "park"]
            )
        
        with col2:
            analysis_type = st.radio(
                "Analysis Type",
                options=["Individual ZCTAs", "Combined Region"],
                help="Analyze each ZCTA separately or as one region"
            )
            
            include_demographics = st.checkbox(
                "Include demographic analysis",
                value=True
            )
        
        submitted = st.form_submit_button("Analyze ZCTAs")
    
    if submitted:
        zcta_list = [z.strip() for z in zcta_codes.split('\n') if z.strip()]
        
        with st.spinner(f"Analyzing {len(zcta_list)} ZCTAs..."):
            # Placeholder for actual analysis
            st.info("ZCTA analysis coming soon!")
            
            # Sample results
            st.subheader("📊 ZCTA Analysis Results")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("ZCTAs Analyzed", len(zcta_list))
            
            with col2:
                st.metric("Total Population", "45,230")
            
            with col3:
                st.metric("POIs Found", "12")
            
            # Comparison table
            st.subheader("ZCTA Comparison")
            
            st.markdown("""
            | ZCTA | Population | POIs | Median Income | Access Score |
            |------|------------|------|---------------|--------------|
            | 27701 | 15,420 | 5 | $48,500 | 85% |
            | 27705 | 18,330 | 4 | $65,200 | 72% |
            | 27707 | 11,480 | 3 | $52,100 | 68% |
            """)
            
            # Regional insights
            st.subheader("🎯 Regional Insights")
            st.info("""
            **Key Findings:**
            - ZCTA 27701 has the best access to libraries (5 within region)
            - Income disparities correlate with POI access
            - Consider new facility in 27707 to improve equity
            """)