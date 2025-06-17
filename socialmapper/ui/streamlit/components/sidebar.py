"""Sidebar navigation component for the Streamlit application."""

import os
import streamlit as st
from typing import List, Optional


def render_sidebar() -> str:
    """Render the sidebar navigation and return the selected page.
    
    Returns:
        The name of the selected page
    """
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        pages = [
            "Getting Started",
            "Custom POIs",
            "Travel Modes",
            "ZCTA Analysis",
            "Address Geocoding",
            "Batch Analysis",
            "Settings"
        ]
        
        # Initialize current page if not set
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Getting Started"
        
        selected_page = st.radio(
            "Select Tutorial",
            pages,
            index=pages.index(st.session_state.current_page)
        )
        
        st.session_state.current_page = selected_page
        
        st.markdown("---")
        
        # API Key configuration
        render_api_key_section()
        
        st.markdown("---")
        st.markdown("### 📊 About SocialMapper")
        st.info(
            "SocialMapper analyzes community connections by mapping demographics "
            "and access to points of interest using isochrones and census data."
        )
        
        return selected_page


def render_api_key_section():
    """Render the API key configuration section."""
    st.markdown("### 🔑 API Configuration")
    
    # Check for API key in various sources
    api_key_configured = False
    
    # 1. Check Streamlit secrets
    try:
        if "census" in st.secrets and "CENSUS_API_KEY" in st.secrets["census"]:
            os.environ['CENSUS_API_KEY'] = st.secrets["census"]["CENSUS_API_KEY"]
            st.success("✅ API key loaded from secrets")
            api_key_configured = True
    except FileNotFoundError:
        pass
    
    # 2. Check environment variable
    if not api_key_configured and os.environ.get('CENSUS_API_KEY'):
        st.success("✅ API key loaded from environment")
        api_key_configured = True
    
    # 3. Manual input
    if not api_key_configured:
        census_api_key = st.text_input(
            "Census API Key",
            type="password",
            help="Get your free API key at https://api.census.gov/data/key_signup.html"
        )
        
        if census_api_key:
            os.environ['CENSUS_API_KEY'] = census_api_key
            st.success("API key configured!")
        else:
            st.warning("Census API key required for demographic data")


def get_page_icon(page_name: str) -> str:
    """Get the appropriate icon for a page.
    
    Args:
        page_name: Name of the page
        
    Returns:
        Emoji icon for the page
    """
    icons = {
        "Getting Started": "🚀",
        "Custom POIs": "📍",
        "Travel Modes": "🚶‍♂️",
        "ZCTA Analysis": "📮",
        "Address Geocoding": "🏠",
        "Batch Analysis": "📊",
        "Settings": "⚙️"
    }
    return icons.get(page_name, "📄")