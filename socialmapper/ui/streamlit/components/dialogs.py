"""Modal dialog components using st.dialog."""

import streamlit as st
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


@st.dialog("ℹ️ Help & Documentation")
def show_help_dialog(topic: str = "general") -> None:
    """Show help dialog for various topics.
    
    Args:
        topic: Help topic to display
    """
    help_content = {
        "general": {
            "title": "Getting Started with SocialMapper",
            "content": """
            SocialMapper helps you analyze community accessibility to essential services.
            
            **Quick Start:**
            1. Enter a location (e.g., "Durham, North Carolina")
            2. Select a POI type (e.g., libraries, schools, parks)
            3. Choose travel time and mode
            4. Click "Run Analysis" to see results
            
            **Features:**
            - 🗺️ Interactive maps with isochrones
            - 📊 Demographic analysis
            - 📥 Export results in multiple formats
            - 🚴 Multi-modal travel analysis
            """
        },
        "poi_types": {
            "title": "Understanding POI Types",
            "content": """
            **Points of Interest (POIs)** are locations from OpenStreetMap:
            
            **Amenities:** Libraries, schools, hospitals, parks
            **Shops:** Grocery stores, pharmacies, retail
            **Leisure:** Recreation centers, sports facilities
            **Healthcare:** Clinics, dentists, specialists
            **Education:** Universities, colleges, training
            
            Each category contains specific types you can search for.
            """
        },
        "travel_modes": {
            "title": "Travel Mode Information",
            "content": """
            **Travel modes** determine how isochrones are calculated:
            
            🚶 **Walk:** Uses pedestrian paths and sidewalks
            - Speed: ~5 km/h
            - Includes all walkable paths
            
            🚴 **Bike:** Uses bike lanes and roads
            - Speed: ~15 km/h  
            - Avoids highways
            
            🚗 **Drive:** Uses road network
            - Speed: Varies by road type
            - Respects one-way streets
            """
        }
    }
    
    info = help_content.get(topic, help_content["general"])
    st.markdown(f"### {info['title']}")
    st.markdown(info['content'])
    
    if st.button("Close", type="primary"):
        st.rerun()


@st.dialog("⚙️ Analysis Settings")
def show_settings_dialog() -> dict[str, Any]:
    """Show settings dialog for analysis configuration.
    
    Returns:
        Dictionary of selected settings
    """
    st.markdown("### Configure Analysis Parameters")
    
    # Advanced settings
    with st.expander("Advanced Settings", expanded=True):
        buffer_distance = st.slider(
            "Buffer Distance (meters)",
            min_value=100,
            max_value=1000,
            value=500,
            step=50,
            help="Extra distance around isochrones for census data"
        )
        
        network_type = st.selectbox(
            "Network Type",
            options=["all", "walk", "bike", "drive"],
            index=0,
            help="OSM network type to use"
        )
        
        simplify_tolerance = st.slider(
            "Simplification Tolerance",
            min_value=0,
            max_value=100,
            value=50,
            help="Higher values create simpler (less detailed) isochrones"
        )
    
    # Export settings
    st.markdown("### Export Settings")
    export_formats = st.multiselect(
        "Export Formats",
        options=["CSV", "Parquet", "GeoJSON", "Excel"],
        default=["CSV"],
        help="Select formats for data export"
    )
    
    include_metadata = st.checkbox(
        "Include Metadata",
        value=True,
        help="Add analysis parameters to exports"
    )
    
    # Save settings
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Settings", type="primary"):
            settings = {
                "buffer_distance": buffer_distance,
                "network_type": network_type,
                "simplify_tolerance": simplify_tolerance,
                "export_formats": export_formats,
                "include_metadata": include_metadata
            }
            st.session_state.analysis_settings = settings
            st.success("Settings saved!")
            st.rerun()
    
    with col2:
        if st.button("Cancel"):
            st.rerun()
    
    return {}


@st.dialog("✅ Analysis Complete")
def show_success_dialog(results: dict[str, Any]) -> None:
    """Show success dialog with analysis summary.
    
    Args:
        results: Analysis results to summarize
    """
    st.success("Analysis completed successfully!")
    
    # Summary metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("POIs Found", results.get("poi_count", 0))
        st.metric("Population", f"{results.get('total_population', 0):,}")
    
    with col2:
        st.metric("Area", f"{results.get('area_km2', 0):.1f} km²")
        st.metric("Census Units", results.get("census_units_analyzed", 0))
    
    # Next steps
    st.markdown("### Next Steps")
    st.markdown("""
    - 📊 Explore the demographic data
    - 🗺️ Interact with the map
    - 📥 Export your results
    - 🔄 Run another analysis
    """)
    
    if st.button("Continue", type="primary"):
        st.rerun()


@st.dialog("❌ Error")
def show_error_dialog(error_message: str, details: Optional[str] = None) -> None:
    """Show error dialog with details.
    
    Args:
        error_message: Main error message
        details: Optional detailed error information
    """
    st.error(error_message)
    
    if details:
        with st.expander("Error Details"):
            st.code(details)
    
    st.markdown("### Troubleshooting")
    st.markdown("""
    Common issues:
    - **Invalid location:** Try "City, State" format
    - **No POIs found:** Try a larger travel time or different POI type
    - **API errors:** Check your Census API key in Settings
    - **Network issues:** Check your internet connection
    """)
    
    # GitHub issue reporting section
    st.markdown("### 🐛 Report a Bug")
    st.markdown("""
    If this error persists, please help us improve SocialMapper by reporting it on GitHub:
    
    **Steps to report:**
    1. Click the link below to open a new GitHub issue
    2. Describe what you were trying to do
    3. Include the error message and any steps to reproduce
    4. Add any relevant details about your system/browser
    """)
    
    # Create GitHub issue URL with pre-filled template
    import urllib.parse
    
    issue_title = f"Error: {error_message[:50]}..."
    issue_body = f"""**Error Message:**
{error_message}

**Error Details:**
{details if details else 'No additional details provided'}

**Steps to Reproduce:**
1. [Describe what you were doing when the error occurred]
2. [Add any specific settings or inputs used]

**Environment:**
- Browser: [Please specify]
- Operating System: [Please specify]
- SocialMapper Version: [Latest from main branch]

**Additional Context:**
[Add any other context about the problem here]
"""
    
    github_url = f"https://github.com/mihiarc/socialmapper/issues/new?title={urllib.parse.quote(issue_title)}&body={urllib.parse.quote(issue_body)}&labels=bug,streamlit-app"
    
    st.markdown(f"[🔗 **Report this issue on GitHub**]({github_url})")
    
    st.info("💡 **Tip:** GitHub issues help the entire community! Your report might help other users experiencing similar problems.")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Try Again", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("Get Help"):
            show_help_dialog("general")
    
    with col3:
        if st.button("Copy Error"):
            # Copy error details to clipboard (if supported by browser)
            error_text = f"Error: {error_message}\n\nDetails: {details if details else 'None'}"
            st.code(error_text)
            st.caption("Copy the text above to share with support")


@st.dialog("📊 Export Options")
def show_export_dialog(data: Any, filename_base: str = "socialmapper_export") -> None:
    """Show export dialog with format options.
    
    Args:
        data: Data to export
        filename_base: Base filename for exports
    """
    import datetime
    import pandas as pd
    
    st.markdown("### Export Your Analysis")
    
    # Format selection
    export_format = st.radio(
        "Select Export Format",
        options=["CSV", "Excel", "Parquet", "GeoJSON"],
        horizontal=True
    )
    
    # Additional options
    include_timestamp = st.checkbox("Include timestamp in filename", value=True)
    include_metadata = st.checkbox("Include analysis metadata", value=True)
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
    filename = f"{filename_base}_{timestamp}.{export_format.lower()}" if timestamp else f"{filename_base}.{export_format.lower()}"
    
    st.info(f"Filename: {filename}")
    
    # Export button
    if st.button("Export", type="primary"):
        try:
            # Convert data based on format
            if export_format == "CSV":
                output = data.to_csv(index=False) if hasattr(data, 'to_csv') else str(data)
                mime = "text/csv"
            elif export_format == "Excel":
                # Would need to implement Excel export
                output = "Excel export not yet implemented"
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif export_format == "Parquet":
                # Would need to implement Parquet export
                output = "Parquet export not yet implemented"
                mime = "application/octet-stream"
            else:  # GeoJSON
                # Would need to implement GeoJSON export
                output = "GeoJSON export not yet implemented"
                mime = "application/geo+json"
            
            st.download_button(
                label=f"Download {export_format}",
                data=output,
                file_name=filename,
                mime=mime
            )
            
            st.success("Export ready for download!")
            
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    if st.button("Cancel"):
        st.rerun()


@st.dialog("🔄 Processing")
def show_progress_dialog(task_name: str = "Processing") -> None:
    """Show progress dialog for long-running tasks.
    
    Args:
        task_name: Name of the current task
    """
    st.markdown(f"### {task_name}")
    
    # Progress bar
    progress = st.progress(0)
    status_text = st.empty()
    
    # Simulate progress (in real use, this would be updated by the task)
    import time
    steps = [
        "Initializing...",
        "Loading data...",
        "Processing...",
        "Analyzing...",
        "Finalizing..."
    ]
    
    for i, step in enumerate(steps):
        progress.progress((i + 1) / len(steps))
        status_text.text(step)
        time.sleep(0.5)
    
    st.success("Complete!")
    
    if st.button("Continue", type="primary"):
        st.rerun()


# Utility function to check if dialogs are available
def dialogs_available() -> bool:
    """Check if st.dialog is available in current Streamlit version."""
    return hasattr(st, 'dialog')