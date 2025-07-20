"""SocialMapper Streamlit Application - Tutorial-Based Interactive Demo

This application serves as an interactive demonstration of SocialMapper's capabilities,
transforming the comprehensive documentation examples into hands-on learning experiences.
Each page mirrors a tutorial from the [online documentation](https://mihiarc.github.io/socialmapper/tutorials/) with the same workflows, parameters,
and expected outputs.
"""

import logging
import traceback
from typing import Any, Dict, Optional

import streamlit as st

from .config import PAGE_CONFIG, TUTORIAL_PAGES
from .pages import (
    render_address_geocoding_page,
    render_custom_pois_page,
    render_getting_started_page,
    render_travel_modes_page,
    render_zcta_analysis_page,
)
from .styles import get_custom_css

# Set up logging
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize all required session state variables with proper defaults."""
    try:
        # Core application state
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Welcome"
        if 'analysis_complete' not in st.session_state:
            st.session_state.analysis_complete = False
        if 'census_vars' not in st.session_state:
            st.session_state.census_vars = []
        
        # Tutorial progress tracking
        if 'tutorial_progress' not in st.session_state:
            st.session_state.tutorial_progress = {
                "Getting Started": False,
                "Custom POIs": False,
                "Travel Modes": False,
                "ZCTA Analysis": False,
                "Address Geocoding": False
            }
        
        # Navigation and UI state
        if 'navigation_mode' not in st.session_state:
            st.session_state.navigation_mode = None
        if 'page_config_set' not in st.session_state:
            st.session_state.page_config_set = False
        if 'error_state' not in st.session_state:
            st.session_state.error_state = None
        
        # User preferences
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {
                'theme': 'auto',
                'show_debug': False,
                'auto_refresh': True
            }
            
        logger.info("Session state initialization completed")
        
    except Exception as e:
        logger.error(f"Session state initialization failed: {e}")


def setup_page_config():
    """Configure Streamlit page settings with error handling."""
    try:
        if not st.session_state.page_config_set:
            st.set_page_config(**PAGE_CONFIG)
            st.session_state.page_config_set = True
            logger.info("Page configuration set successfully")
    except Exception as e:
        logger.warning(f"Page config already set or failed: {e}")
        # Page config can only be set once, so this is expected on reruns


def detect_navigation_capability() -> str:
    """Detect available navigation capabilities and return the best option."""
    try:
        # Check for modern navigation (Streamlit 1.28+)
        if hasattr(st, 'navigation') and callable(getattr(st, 'navigation')):
            logger.info("Modern navigation (st.navigation) detected")
            return 'modern'
        
        # Fallback to traditional sidebar navigation
        logger.info("Using traditional sidebar navigation")
        return 'traditional'
        
    except Exception as e:
        logger.error(f"Error detecting navigation capability: {e}")
        return 'traditional'


def handle_global_error(error: Exception, context: str = "Unknown") -> None:
    """Global error handler with user-friendly messages."""
    error_id = f"{context}_{hash(str(error)) % 10000}"
    
    # Log the full error for debugging
    logger.error(f"Global error [{error_id}] in {context}: {error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Store error in session state for debugging
    st.session_state.error_state = {
        'error_id': error_id,
        'context': context,
        'message': str(error),
        'type': type(error).__name__
    }
    
    # Display user-friendly error message
    st.error(f"""
    ❌ **Application Error** (ID: {error_id})
    
    An error occurred in {context}. Please try refreshing the page.
    
    **What you can try:**
    - Refresh the page
    - Clear your browser cache
    - Try a different browser
    
    **Error Details:** {str(error)[:200]}{'...' if len(str(error)) > 200 else ''}
    """)


def render_welcome_screen():
    """Render the welcome screen that introduces the tutorial sequence."""
    st.markdown("""
    # 🗺️ Welcome to SocialMapper Interactive Tutorials
    
    **Learn community accessibility analysis through hands-on experience**
    
    This interactive application transforms the SocialMapper documentation examples into 
    guided tutorials. Each page mirrors the written tutorials with the same datasets, 
    parameters, and expected outputs.
    
    ## 📚 Tutorial Learning Path
    
    Follow these tutorials in sequence to build your SocialMapper expertise:
    """)
    
    # Tutorial progress indicators
    col1, col2 = st.columns([3, 1])
    
    with col1:
        for i, (page_key, page_info) in enumerate(TUTORIAL_PAGES.items(), 1):
            completed = st.session_state.tutorial_progress.get(page_key, False)
            status_icon = "✅" if completed else "📖"
            
            st.markdown(f"""
            ### {status_icon} {i}. {page_info['title']}
            **{page_info['description']}**
            
            📄 *Mirrors:* {page_info['doc_reference']}
            """)
    
    with col2:
        st.markdown("### 🎯 Quick Start")
        if st.button("🚀 Begin Tutorial 1", type="primary", use_container_width=True, key="welcome_begin_tutorial"):
            st.session_state.current_page = "Getting Started"
            st.rerun()
        
        st.markdown("### 📖 Resources")
        st.markdown("""
        - [📚 Documentation](https://mihiarc.github.io/socialmapper/)
        - [💻 GitHub Repository](https://github.com/mihiarc/socialmapper)
        - [🔑 Get Census API Key](https://api.census.gov/data/key_signup.html)
        """)
    
    st.markdown("---")
    st.info("""
    💡 **Tip**: Each tutorial uses the exact same parameters and datasets as the written 
    documentation. You can cross-reference between the interactive app and the tutorials 
    at any time.
    """)


def render_tutorial_navigation():
    """Render tutorial navigation in the sidebar."""
    with st.sidebar:
        st.markdown("## 🧭 Tutorial Navigation")
        
        # Navigation using buttons for better control
        current = st.session_state.get('current_page', 'Welcome')
        
        # Home button
        if st.button("🏠 Welcome", 
                    use_container_width=True,
                    type="primary" if current == "Welcome" else "secondary",
                    key="nav_welcome"):
            st.session_state.current_page = "Welcome"
            st.rerun()
        
        st.markdown("### 📚 Tutorials")
        
        # Tutorial buttons
        for page_name, page_info in TUTORIAL_PAGES.items():
            button_type = "primary" if current == page_name else "secondary"
            if st.button(f"{page_info['icon']} {page_name}", 
                        use_container_width=True,
                        type=button_type,
                        key=f"nav_{page_name.replace(' ', '_').lower()}"):
                st.session_state.current_page = page_name
                st.rerun()
        
        # Progress indicator
        st.markdown("### 📊 Progress")
        completed_count = sum(st.session_state.tutorial_progress.values())
        total_count = len(TUTORIAL_PAGES)
        progress = completed_count / total_count
        
        st.progress(progress)
        st.caption(f"{completed_count}/{total_count} tutorials completed")
        
        # Tutorial info
        if st.session_state.current_page in TUTORIAL_PAGES:
            page_info = TUTORIAL_PAGES[st.session_state.current_page]
            st.markdown("### 📖 Current Tutorial")
            st.info(f"""
            **{page_info['title']}**
            
            {page_info['description']}
            
            📄 *Mirrors:* {page_info['doc_reference']}
            """)
        
        st.markdown("---")
        
        # API Key configuration
        render_api_key_section()


def render_api_key_section():
    """Render the API key configuration section."""
    import os
    
    st.markdown("### 🔑 API Configuration")

    # Check for API key in various sources
    api_key_configured = False

    # 1. Check Streamlit secrets
    try:
        if "census" in st.secrets and "CENSUS_API_KEY" in st.secrets["census"]:
            os.environ['CENSUS_API_KEY'] = st.secrets["census"]["CENSUS_API_KEY"]
            st.success("✅ API key loaded from secrets")
            api_key_configured = True
    except (FileNotFoundError, KeyError):
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


def safe_page_render(page_func, page_name: str):
    """Safely render a page with error handling."""
    try:
        page_func()
    except Exception as e:
        handle_global_error(e, f"tutorial_{page_name.lower().replace(' ', '_')}")


def main_modern():
    """Modern application with st.navigation."""
    try:
        # Apply custom CSS
        st.markdown(get_custom_css(), unsafe_allow_html=True)
        
        # Define pages for navigation
        pages = [
            st.Page(render_welcome_screen, title="🏠 Welcome", url_path="welcome"),
            st.Page(render_getting_started_page, title="🚀 Getting Started", url_path="getting-started"),
            st.Page(render_custom_pois_page, title="📍 Custom POIs", url_path="custom-pois"),
            st.Page(render_travel_modes_page, title="🚴 Travel Modes", url_path="travel-modes"),
            st.Page(render_zcta_analysis_page, title="📊 ZCTA Analysis", url_path="zcta-analysis"),
            st.Page(render_address_geocoding_page, title="📮 Address Geocoding", url_path="address-geocoding"),
        ]
        
        # Create navigation
        nav = st.navigation(pages, position="sidebar")
        nav.run()
        
    except Exception as e:
        handle_global_error(e, "modern_navigation")


def main_traditional():
    """Traditional application with sidebar navigation."""
    try:
        # Apply custom CSS
        st.markdown(get_custom_css(), unsafe_allow_html=True)

        # Render sidebar navigation
        render_tutorial_navigation()

        # Main content area
        if st.session_state.current_page == "Welcome":
            render_welcome_screen()
        else:
            # Tutorial page renderers
            page_renderers = {
                "Getting Started": render_getting_started_page,
                "Custom POIs": render_custom_pois_page,
                "Travel Modes": render_travel_modes_page,
                "ZCTA Analysis": render_zcta_analysis_page,
                "Address Geocoding": render_address_geocoding_page,
            }

            # Render selected page with error handling
            if st.session_state.current_page in page_renderers:
                safe_page_render(page_renderers[st.session_state.current_page], st.session_state.current_page)
            else:
                st.error(f"Tutorial '{st.session_state.current_page}' not found!")
                st.info("Available tutorials: " + ", ".join(page_renderers.keys()))
            
    except Exception as e:
        handle_global_error(e, "traditional_navigation")


def main():
    """Main application entry point with robust error handling and navigation detection."""
    try:
        # Initialize session state first
        initialize_session_state()
        
        # Setup page configuration
        setup_page_config()
        
        # Detect and cache navigation capability
        if st.session_state.navigation_mode is None:
            st.session_state.navigation_mode = detect_navigation_capability()
        
        # Route to appropriate navigation mode
        if st.session_state.navigation_mode == 'modern':
            main_modern()
        else:
            main_traditional()
            
    except Exception as e:
        handle_global_error(e, "main_application")


if __name__ == "__main__":
    main()