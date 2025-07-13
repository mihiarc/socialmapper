"""Main Streamlit application with modern navigation."""

import streamlit as st

from .config import PAGE_CONFIG
from .pages import (
    render_address_geocoding_page,
    render_batch_analysis_page,
    render_custom_pois_page,
    render_getting_started_page,
    render_settings_page,
    render_travel_modes_page,
    render_zcta_analysis_page,
)
from .pages.travel_analysis_simple import main as render_travel_analysis_page
from .styles import get_custom_css


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


def setup_page_config():
    """Configure the Streamlit page."""
    # Create a copy of PAGE_CONFIG and modify for modern app
    config = PAGE_CONFIG.copy()
    config["initial_sidebar_state"] = "collapsed"  # Collapse sidebar for top nav
    st.set_page_config(**config)


def render_header():
    """Render the main header."""
    # Header with theme detection
    theme_class = "light-theme"  # Default
    try:
        if hasattr(st, 'context') and hasattr(st.context, 'theme'):
            theme = st.context.theme
            # Check different possible theme attributes
            if hasattr(theme, 'base'):
                theme_class = "dark-theme" if theme.base == "dark" else "light-theme"
            elif hasattr(theme, 'primaryColor'):
                # Fallback: detect based on primary color brightness
                theme_class = "light-theme"
    except Exception:
        # If theme detection fails, use default
        pass
    
    st.markdown(
        f'<div class="{theme_class}">'
        '<h1 class="main-header">🗺️ SocialMapper Dashboard</h1>'
        '<p class="sub-header">Interactive Community Accessibility Analysis</p>'
        '</div>',
        unsafe_allow_html=True
    )


def main():
    """Main application entry point with top navigation."""
    # Configure page
    setup_page_config()
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Define pages for navigation
    pages = {
        "getting_started": {
            "title": "🚀 Getting Started",
            "func": render_getting_started_page
        },
        "travel_analysis": {
            "title": "🗺️ Travel Analysis",
            "func": render_travel_analysis_page
        },
        "custom_pois": {
            "title": "📍 Custom POIs",
            "func": render_custom_pois_page
        },
        "travel_modes": {
            "title": "🚴 Travel Modes",
            "func": render_travel_modes_page
        },
        "zcta_analysis": {
            "title": "📊 ZCTA Analysis",
            "func": render_zcta_analysis_page
        },
        "address_geocoding": {
            "title": "📮 Address Geocoding",
            "func": render_address_geocoding_page
        },
        "batch_analysis": {
            "title": "📦 Batch Analysis",
            "func": render_batch_analysis_page
        },
        "settings": {
            "title": "⚙️ Settings",
            "func": render_settings_page
        }
    }
    
    # Create top navigation using st.navigation
    nav = st.navigation(
        pages=[
            st.Page(page["func"], title=page["title"], url_path=key)
            for key, page in pages.items()
        ],
        position="top"
    )
    
    # Run the selected page
    nav.run()


# Alternative implementation using tabs (fallback for older Streamlit versions)
def main_with_tabs():
    """Main application entry point with tab-based navigation."""
    # Configure page
    setup_page_config()
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Create tabs for navigation
    tabs = st.tabs([
        "🚀 Getting Started",
        "📍 Custom POIs",
        "🚴 Travel Modes",
        "📊 ZCTA Analysis",
        "📮 Address Geocoding",
        "📦 Batch Analysis",
        "⚙️ Settings"
    ])
    
    # Render content in each tab
    with tabs[0]:
        render_getting_started_page()
    
    with tabs[1]:
        render_custom_pois_page()
    
    with tabs[2]:
        render_travel_modes_page()
    
    with tabs[3]:
        render_zcta_analysis_page()
    
    with tabs[4]:
        render_address_geocoding_page()
    
    with tabs[5]:
        render_batch_analysis_page()
    
    with tabs[6]:
        render_settings_page()


if __name__ == "__main__":
    # Try to use st.navigation (Streamlit 2025+)
    try:
        main()
    except AttributeError:
        # Fallback to tab-based navigation for older versions
        main_with_tabs()