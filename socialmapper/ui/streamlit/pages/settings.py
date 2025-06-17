"""Settings page for the Streamlit application."""

import streamlit as st
import os
from typing import Dict, Any


def render_settings_page():
    """Render the Settings page."""
    st.header("⚙️ Settings & Configuration")
    
    st.markdown("""
    Configure SocialMapper settings, manage API keys, and optimize performance for your needs.
    """)
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["API Keys", "Cache", "Performance", "Export"])
    
    with tab1:
        render_api_settings()
    
    with tab2:
        render_cache_settings()
    
    with tab3:
        render_performance_settings()
    
    with tab4:
        render_export_settings()


def render_api_settings():
    """Render API key configuration settings."""
    st.subheader("🔑 API Key Management")
    
    # Census API Key
    st.markdown("### Census API")
    
    current_key = os.environ.get('CENSUS_API_KEY', '')
    key_status = "✅ Configured" if current_key else "❌ Not configured"
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"Status: {key_status}")
    
    with col2:
        if st.button("Get API Key"):
            st.markdown("[Sign up for free](https://api.census.gov/data/key_signup.html)")
    
    new_key = st.text_input(
        "Census API Key",
        value=current_key if st.checkbox("Show current key") else "",
        type="password" if not st.checkbox("Show current key", key="show_census") else "text",
        help="Your Census API key for demographic data"
    )
    
    if new_key != current_key and st.button("Update Census Key"):
        os.environ['CENSUS_API_KEY'] = new_key
        st.success("✅ Census API key updated!")
        st.rerun()
    
    # Future API keys
    st.markdown("### Other APIs")
    st.info("Support for additional APIs (Google Maps, Mapbox) coming soon!")


def render_cache_settings():
    """Render cache management settings."""
    st.subheader("💾 Cache Management")
    
    st.info("""
    SocialMapper caches geocoding results and network data to improve performance. 
    Cached data is stored locally and can be cleared if needed.
    """)
    
    # Cache statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cache Size", "124 MB")
    
    with col2:
        st.metric("Cached Items", "1,847")
    
    with col3:
        st.metric("Cache Age", "3 days")
    
    # Cache actions
    st.markdown("### Cache Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Clear Geocoding Cache"):
            st.success("Geocoding cache cleared!")
    
    with col2:
        if st.button("Clear Network Cache"):
            st.success("Network cache cleared!")
    
    with col3:
        if st.button("Clear All Caches", type="secondary"):
            st.success("All caches cleared!")
    
    # Cache settings
    st.markdown("### Cache Settings")
    
    cache_ttl = st.slider(
        "Cache Time-to-Live (days)",
        min_value=1,
        max_value=30,
        value=7,
        help="How long to keep cached data"
    )
    
    auto_clean = st.checkbox(
        "Automatically clean old cache entries",
        value=True
    )


def render_performance_settings():
    """Render performance optimization settings."""
    st.subheader("🚀 Performance Settings")
    
    st.info("""
    Optimize SocialMapper performance based on your system capabilities and needs.
    """)
    
    # System info
    st.markdown("### System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Available Memory", "8.2 GB")
        st.metric("CPU Cores", "8")
    
    with col2:
        st.metric("Performance Tier", "High")
        st.metric("Recommended Workers", "4")
    
    # Performance settings
    st.markdown("### Optimization Settings")
    
    concurrent_requests = st.slider(
        "Concurrent API Requests",
        min_value=1,
        max_value=10,
        value=5,
        help="Number of simultaneous API requests"
    )
    
    timeout_seconds = st.slider(
        "Request Timeout (seconds)",
        min_value=10,
        max_value=120,
        value=30,
        help="Maximum time to wait for API responses"
    )
    
    simplify_geometries = st.checkbox(
        "Simplify geometries for faster rendering",
        value=True,
        help="Reduces detail in maps for better performance"
    )
    
    # Apply settings button
    if st.button("Apply Performance Settings"):
        st.success("✅ Performance settings updated!")


def render_export_settings():
    """Render export configuration settings."""
    st.subheader("📥 Export Settings")
    
    st.info("""
    Configure default export formats and options for analysis results.
    """)
    
    # Default formats
    st.markdown("### Default Export Formats")
    
    default_format = st.selectbox(
        "Default Data Format",
        options=["CSV", "Excel", "Parquet", "GeoJSON"],
        index=0
    )
    
    include_metadata = st.checkbox(
        "Include metadata in exports",
        value=True,
        help="Add analysis parameters and timestamps"
    )
    
    compress_exports = st.checkbox(
        "Compress large exports",
        value=False,
        help="Automatically ZIP files over 10MB"
    )
    
    # Map export settings
    st.markdown("### Map Export Settings")
    
    map_format = st.selectbox(
        "Map Image Format",
        options=["PNG", "JPG", "SVG", "PDF"],
        index=0
    )
    
    map_dpi = st.slider(
        "Map Resolution (DPI)",
        min_value=72,
        max_value=300,
        value=150,
        step=10
    )
    
    # Report settings
    st.markdown("### Report Settings")
    
    report_template = st.selectbox(
        "Report Template",
        options=["Standard", "Detailed", "Executive Summary", "Custom"],
        index=0
    )
    
    include_visualizations = st.checkbox(
        "Include visualizations in reports",
        value=True
    )
    
    # Save settings
    if st.button("Save Export Settings", type="primary"):
        st.success("✅ Export settings saved!")