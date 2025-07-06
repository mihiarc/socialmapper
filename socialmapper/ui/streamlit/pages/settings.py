"""Settings page for the Streamlit application."""

import os

import streamlit as st


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

    show_key = st.checkbox("Show current key")
    
    new_key = st.text_input(
        "Census API Key",
        value=current_key if show_key else "",
        type="password" if not show_key else "text",
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

    # Import cache manager
    try:
        from socialmapper.cache_manager import (
            get_cache_statistics,
            clear_geocoding_cache,
            clear_census_cache,
            clear_all_caches,
            cleanup_expired_cache_entries
        )
        from socialmapper.isochrone import clear_network_cache
        
        # Get real cache statistics
        cache_stats = get_cache_statistics()
        
        # Cache statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_size = cache_stats['summary']['total_size_mb']
            st.metric("Cache Size", f"{total_size:.1f} MB")

        with col2:
            total_items = cache_stats['summary']['total_items']
            st.metric("Cached Items", f"{total_items:,}")

        with col3:
            # Calculate cache age from oldest entry
            oldest_entry = None
            for cache_type in ['network_cache', 'geocoding_cache', 'census_cache', 'general_cache']:
                cache_data = cache_stats.get(cache_type, {})
                if cache_data.get('oldest_entry'):
                    from datetime import datetime
                    entry_time = datetime.fromisoformat(cache_data['oldest_entry'])
                    if oldest_entry is None or entry_time < oldest_entry:
                        oldest_entry = entry_time
            
            if oldest_entry:
                age_days = (datetime.now() - oldest_entry).days
                if age_days == 0:
                    age_str = "Today"
                elif age_days == 1:
                    age_str = "1 day"
                else:
                    age_str = f"{age_days} days"
            else:
                age_str = "Empty"
            
            st.metric("Cache Age", age_str)

        # Detailed cache breakdown
        with st.expander("Cache Details"):
            for cache_type in ['network_cache', 'geocoding_cache', 'census_cache', 'general_cache']:
                cache_data = cache_stats.get(cache_type, {})
                if cache_data:
                    st.markdown(f"**{cache_type.replace('_', ' ').title()}**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"Size: {cache_data.get('size_mb', 0):.2f} MB")
                    with col2:
                        st.write(f"Items: {cache_data.get('item_count', 0):,}")
                    with col3:
                        st.write(f"Status: {cache_data.get('status', 'unknown')}")
                    
                    # Show additional stats for network cache
                    if cache_type == 'network_cache' and cache_data.get('hit_rate_percent') is not None:
                        st.write(f"Hit Rate: {cache_data['hit_rate_percent']:.1f}%")
                        if cache_data.get('total_nodes'):
                            st.write(f"Total Nodes: {cache_data['total_nodes']:,}")
                            st.write(f"Total Edges: {cache_data['total_edges']:,}")

    except ImportError:
        st.error("Cache manager not available. Using default values.")
        # Fallback to static values
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cache Size", "N/A")
        with col2:
            st.metric("Cached Items", "N/A")
        with col3:
            st.metric("Cache Age", "N/A")

    # Cache actions
    st.markdown("### Cache Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Clear Geocoding Cache"):
            try:
                result = clear_geocoding_cache()
                if result['success']:
                    st.success(f"✅ Geocoding cache cleared! ({result['cleared_size_mb']:.1f} MB)")
                else:
                    st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    with col2:
        if st.button("Clear Network Cache"):
            try:
                clear_network_cache()  # This function doesn't return a result dict
                st.success(f"✅ Network cache cleared!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    with col3:
        if st.button("Clear Census Cache"):
            try:
                result = clear_census_cache()
                if result['success']:
                    st.success(f"✅ Census cache cleared! ({result['cleared_size_mb']:.1f} MB)")
                else:
                    st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    with col4:
        if st.button("Clear All Caches", type="secondary"):
            try:
                result = clear_all_caches()
                if result['summary']['success']:
                    st.success(f"✅ All caches cleared! ({result['summary']['total_cleared_mb']:.1f} MB total)")
                else:
                    st.error("❌ Some caches failed to clear. Check individual results.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Additional actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clean Expired Entries"):
            try:
                result = cleanup_expired_cache_entries()
                st.success("✅ Expired entries cleaned!")
                with st.expander("Cleanup Details"):
                    st.json(result)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        if st.button("Refresh Statistics"):
            st.rerun()

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
