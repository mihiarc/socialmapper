"""Theme detection and management utilities."""

import streamlit as st
from typing import Literal, Optional


def get_current_theme() -> Optional[Literal["light", "dark"]]:
    """Get the current theme from Streamlit context.
    
    Returns:
        "light" or "dark" if theme is detected, None otherwise
    """
    try:
        # Try to access theme through session state or query params
        if 'theme' in st.session_state:
            return st.session_state.theme
        
        # Try experimental get_query_params
        if hasattr(st, 'experimental_get_query_params'):
            params = st.experimental_get_query_params()
            if 'theme' in params:
                return params['theme'][0]
        
        # For now, default to light theme
        # Theme detection API may vary by Streamlit version
        return "light"
    except Exception:
        pass
    return "light"


def apply_theme_class() -> str:
    """Apply theme class based on current theme.
    
    Returns:
        CSS class string for the current theme
    """
    theme = get_current_theme()
    return "dark-theme" if theme == "dark" else "light-theme"


def get_theme_colors() -> dict[str, str]:
    """Get color palette based on current theme.
    
    Returns:
        Dictionary of color values for the current theme
    """
    theme = get_current_theme()
    
    if theme == "dark":
        return {
            "primary": "#4dabf7",
            "secondary": "#66d9ef",
            "background": "#0e1117",
            "surface": "#262730",
            "text": "#fafafa",
            "text_secondary": "#aaaaaa",
            "success": "#8fce8f",
            "error": "#ce8f8f",
            "warning": "#f1c40f",
            "info": "#4dabf7",
            "border": "#464646"
        }
    else:
        return {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "background": "#ffffff",
            "surface": "#f0f2f6",
            "text": "#262730",
            "text_secondary": "#666666",
            "success": "#155724",
            "error": "#721c24",
            "warning": "#856404",
            "info": "#004085",
            "border": "#dee2e6"
        }


def get_map_style() -> str:
    """Get appropriate map tile style based on theme.
    
    Returns:
        Map tile provider name
    """
    theme = get_current_theme()
    return "CartoDB dark_matter" if theme == "dark" else "CartoDB positron"


def theme_metric_card(label: str, value: str, delta: Optional[str] = None) -> str:
    """Create a themed metric card HTML.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        
    Returns:
        HTML string for the metric card
    """
    colors = get_theme_colors()
    theme_class = apply_theme_class()
    
    delta_html = f'<div style="color: {colors["text_secondary"]}; font-size: 0.9rem;">{delta}</div>' if delta else ''
    
    return f"""
    <div class="metric-card {theme_class}" style="
        background-color: {colors['surface']};
        border: 1px solid {colors['border']};
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    ">
        <div style="color: {colors['text_secondary']}; font-size: 0.9rem; margin-bottom: 0.25rem;">
            {label}
        </div>
        <div style="color: {colors['text']}; font-size: 1.5rem; font-weight: bold;">
            {value}
        </div>
        {delta_html}
    </div>
    """


def theme_info_box(content: str, type: Literal["info", "success", "warning", "error"] = "info") -> str:
    """Create a themed info box HTML.
    
    Args:
        content: Box content
        type: Type of info box
        
    Returns:
        HTML string for the info box
    """
    colors = get_theme_colors()
    theme_class = apply_theme_class()
    
    color_map = {
        "info": colors["info"],
        "success": colors["success"],
        "warning": colors["warning"],
        "error": colors["error"]
    }
    
    border_color = color_map.get(type, colors["info"])
    
    return f"""
    <div class="info-box {theme_class}" style="
        background-color: {colors['surface']};
        border-left: 4px solid {border_color};
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    ">
        <div style="color: {colors['text']};">
            {content}
        </div>
    </div>
    """