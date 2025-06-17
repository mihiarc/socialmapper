"""Main Streamlit application orchestrator."""

import streamlit as st
from .config import PAGE_CONFIG, PAGES
from .styles import get_custom_css
from .components.sidebar import render_sidebar
from .pages import (
    render_getting_started_page,
    render_custom_pois_page,
    render_travel_modes_page,
    render_zcta_analysis_page,
    render_address_geocoding_page,
    render_batch_analysis_page,
    render_settings_page
)


def initialize_session_state():
    """Initialize session state variables."""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Getting Started"
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'census_vars' not in st.session_state:
        st.session_state.census_vars = []


def main():
    """Main application entry point."""
    # Configure page
    st.set_page_config(**PAGE_CONFIG)
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Main content area header
    st.markdown('<h1 class="main-header">🗺️ SocialMapper Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Interactive Community Accessibility Analysis</p>', unsafe_allow_html=True)
    
    # Route to appropriate page
    page_renderers = {
        "Getting Started": render_getting_started_page,
        "Custom POIs": render_custom_pois_page,
        "Travel Modes": render_travel_modes_page,
        "ZCTA Analysis": render_zcta_analysis_page,
        "Address Geocoding": render_address_geocoding_page,
        "Batch Analysis": render_batch_analysis_page,
        "Settings": render_settings_page
    }
    
    # Render selected page
    if selected_page in page_renderers:
        page_renderers[selected_page]()
    else:
        st.error(f"Page '{selected_page}' not found!")


if __name__ == "__main__":
    main()