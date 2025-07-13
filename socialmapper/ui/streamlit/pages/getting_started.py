"""Getting Started page for the Streamlit application - Fixed version."""

import logging
import os
import time
from typing import Any

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# Set up logging
logger = logging.getLogger(__name__)

# Try importing SocialMapper components with fallback
try:
    from socialmapper import SocialMapperBuilder, SocialMapperClient
    SOCIALMAPPER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import SocialMapper components: {e}")
    SOCIALMAPPER_AVAILABLE = False

from ..components import (
    create_poi_map,
    dialogs_available,
    render_interactive_map,
    render_live_metrics,
    render_poi_table_fragment,
    show_error_dialog,
    show_help_dialog,
    show_success_dialog,
)
from ..config import CENSUS_VARIABLES, DEFAULT_CENSUS_VARS, POI_TYPES
from ..utils import (
    format_census_variable, 
    get_census_variables, 
    get_poi_types,
    progress_context,
    ProgressTracker,
    run_cached_analysis,
    run_analysis_with_progress
)


def render_getting_started_page():
    """Render the Getting Started tutorial page."""
    # Check if SocialMapper is available
    if not SOCIALMAPPER_AVAILABLE:
        st.error("SocialMapper components are not available. Please check your installation.")
        st.code("pip install -e .")
        return

    # Clear cache if needed (for development/updates)
    if st.button("🔄 Refresh POI Categories", help="Click to reload POI categories from config"):
        st.cache_data.clear()
        st.success("Cache cleared! Page will refresh.")
        st.rerun()

    render_header()
    render_input_form()
    render_results()


def render_header():
    """Render the page header and introduction."""
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        st.header("Getting Started with SocialMapper")
    
    with col2:
        if dialogs_available() and st.button("ℹ️ Help", use_container_width=True):
            show_help_dialog("general")
    
    with col3:
        st.metric(
            label="Progress",
            value="Step 1",
            delta="Basic"
        )

    st.markdown("""
    Welcome to **SocialMapper**! This tutorial will guide you through a basic accessibility analysis.
    
    **What you'll learn:**
    - 🔍 Search for points of interest (POIs) in any US location
    - ⏱️ Generate travel-time areas (isochrones)
    - 📊 Analyze demographics within accessible areas
    - 📥 Export results for further analysis
    """)

    st.info("""
    **Quick Start:** Enter a location below (e.g., "Durham, North Carolina") and click 
    "Run Analysis" to see SocialMapper in action. The analysis will find nearby libraries 
    and show demographic data for the surrounding area.
    """)


def render_input_form():
    """Render the analysis input form."""
    st.subheader("Configure Your Analysis")
    
    # Add info about OpenStreetMap
    with st.expander("ℹ️ About OpenStreetMap Data", expanded=False):
        st.markdown("""
        SocialMapper uses **OpenStreetMap (OSM)** data to find points of interest. OSM is a 
        collaborative project to create a free editable map of the world.
        
        **Key Points:**
        - 🗺️ Data quality varies by location - urban areas typically have better coverage
        - 🏷️ POIs are categorized using a tagging system (e.g., `amenity=library`)
        - 🔄 Data is constantly updated by the community
        - 📍 Some businesses may be missing or have outdated information
        
        **Learn More:**
        - [OpenStreetMap Wiki](https://wiki.openstreetmap.org/)
        - [Map Features Guide](https://wiki.openstreetmap.org/wiki/Map_features)
        - [Contribute to OSM](https://www.openstreetmap.org/fixthemap)
        """)

    # POI Selection outside form for dynamic updates  
    st.markdown("#### Select Points of Interest")
    col1, col2 = st.columns(2)
    
    with col1:
        # POI category and type selection (using cached data)
        poi_types = get_poi_types()
        
        # Create user-friendly category names
        category_display = {
            "amenity": "🏛️ Amenities (Schools, Hospitals, etc.)",
            "shop": "🛒 Shopping",
            "leisure": "🌳 Leisure & Recreation", 
            "public_transport": "🚇 Public Transport",
            "railway": "🚂 Railway Stations"
        }
        
        # Category selection with friendly names
        selected_category_display = st.selectbox(
            "POI Category",
            options=list(category_display.values()),
            index=0,
            help="Select the category of places you want to find"
        )
        
        # Add OSM wiki link for the selected category
        osm_category_links = {
            "amenity": "https://wiki.openstreetmap.org/wiki/Key:amenity",
            "shop": "https://wiki.openstreetmap.org/wiki/Key:shop", 
            "leisure": "https://wiki.openstreetmap.org/wiki/Key:leisure",
            "public_transport": "https://wiki.openstreetmap.org/wiki/Key:public_transport",
            "railway": "https://wiki.openstreetmap.org/wiki/Key:railway"
        }
        
        # Get the actual category key
        poi_category = next(k for k, v in category_display.items() if v == selected_category_display)
        
        # Show OSM wiki link for category
        if poi_category in osm_category_links:
            st.caption(f"[📖 Learn more about {poi_category} tags]({osm_category_links[poi_category]})")
    
    with col2:
        # Create user-friendly POI type names
        type_display = {
            # Amenity types
            "library": "📚 Library",
            "school": "🏫 School", 
            "hospital": "🏥 Hospital",
            "community_centre": "🏛️ Community Center",
            "pharmacy": "💊 Pharmacy",
            "clinic": "🏥 Clinic",
            "doctors": "👨‍⚕️ Doctor's Office",
            "university": "🎓 University",
            "kindergarten": "🧒 Kindergarten",
            "bank": "🏦 Bank",
            "post_office": "📮 Post Office",
            "police": "👮 Police Station",
            "fire_station": "🚒 Fire Station",
            "parking": "🅿️ Parking",
            # Shop types
            "supermarket": "🛒 Supermarket",
            "convenience": "🏪 Convenience Store",
            "mall": "🏬 Shopping Mall",
            "grocery": "🥬 Grocery Store",
            "department_store": "🏢 Department Store",
            "bakery": "🥖 Bakery",
            "butcher": "🥩 Butcher",
            # Leisure types
            "park": "🌳 Park",
            "playground": "🛝 Playground",
            "sports_centre": "⚽ Sports Center",
            "swimming_pool": "🏊 Swimming Pool",
            "fitness_centre": "💪 Fitness Center",
            "stadium": "🏟️ Stadium",
            "garden": "🌺 Garden",
            # Transport types
            "station": "🚉 Station",
            "stop_position": "🚏 Transit Stop",
            "platform": "🚊 Platform",
            "halt": "🛤️ Train Halt",
            "tram_stop": "🚋 Tram Stop"
        }
        
        # Get display names for current category
        category_types = poi_types[poi_category]
        type_options = [type_display.get(t, t.replace('_', ' ').title()) for t in category_types]
        
        # Type selection with friendly names
        selected_type_display = st.selectbox(
            "POI Type",
            options=type_options,
            index=0,
            help=f"Specific type within {poi_category} category"
        )
        
        # Get the actual type key
        poi_type = category_types[type_options.index(selected_type_display)]
        
        # Show OSM wiki link for specific POI type
        osm_type_link = f"https://wiki.openstreetmap.org/wiki/Tag:{poi_category}={poi_type}"
        st.caption(f"[📖 Learn about {poi_category}={poi_type}]({osm_type_link})")

    # Now the form with remaining parameters
    st.markdown("#### Configure Analysis Parameters")
    with st.form("basic_analysis"):
        col1, col2, col3 = st.columns(3)

        with col1:
            location = st.text_input(
                "Location",
                value="Durham, North Carolina",
                help="Enter a city and state (e.g., 'San Francisco, California')"
            )

        with col2:
            travel_time = st.slider(
                "Travel Time (minutes)",
                min_value=5,
                max_value=30,
                value=15,
                step=5
            )

        with col3:
            travel_mode = st.selectbox(
                "Travel Mode",
                options=["walk", "bike", "drive"],
                index=0,
                help="Walking includes all legally walkable paths (even roads without sidewalks). Each mode uses different speeds and network types."
            )

        # Census variables selection (using cached data)
        census_vars = get_census_variables()
        census_variables = st.multiselect(
            "Census Variables to Include",
            options=[(code, name) for code, name in census_vars.items()],
            default=[(code, census_vars[code]) for code in DEFAULT_CENSUS_VARS if code in census_vars],
            format_func=lambda x: x[1]
        )

        submitted = st.form_submit_button("🚀 Run Analysis", type="primary")

    if submitted:
        handle_form_submission(location, poi_category, poi_type, travel_time,
                             travel_mode, census_variables)


def handle_form_submission(location: str, poi_category: str, poi_type: str,
                         travel_time: int, travel_mode: str,
                         census_variables: list[tuple[str, str]]):
    """Handle form submission and run analysis."""
    # Check for API key
    if not os.environ.get('CENSUS_API_KEY'):
        if dialogs_available():
            show_error_dialog(
                "Census API Key Required",
                "Please configure your Census API key in the Settings page to use demographic features."
            )
        else:
            st.error("Please configure your Census API key in the sidebar first!")
        return

    # Validate inputs
    if not location or not location.strip():
        if dialogs_available():
            show_error_dialog("Invalid Location", "Please enter a valid location (e.g., 'Durham, North Carolina')")
        else:
            st.error("Please enter a valid location!")
        return

    # Extract census variable codes
    census_var_codes = [var[0] for var in census_variables] if census_variables else []
    st.session_state.census_vars = census_var_codes

    # Define real analysis steps
    steps = [
        "Initializing analysis configuration",
        f"Searching for {poi_type} in {location}",
        "Processing POI and isochrone data", 
        "Analyzing census demographics",
        "Generating final analysis report"
    ]
    
    # Use real progress tracking
    tracker = ProgressTracker(len(steps), "Running Analysis")
    
    def progress_callback(step: int, message: str):
        """Update progress from the analysis function."""
        tracker.update(step, message)
    
    with tracker:
        try:
            # Run analysis with real-time progress updates
            result = run_analysis_with_progress(
                location=location,
                poi_type=poi_category,
                poi_name=poi_type,
                travel_time=travel_time,
                travel_mode=travel_mode,
                census_vars=census_var_codes,
                progress_callback=progress_callback
            )
            
            if result['success']:
                
                # Extract the analysis data
                analysis_result = result['data']

                # Debug: Log the result structure
                logger.info(f"Analysis result type: {type(analysis_result)}")
                if isinstance(analysis_result, dict):
                    logger.info(f"Analysis result keys: {analysis_result.keys()}")

                st.session_state.analysis_results = analysis_result
                st.session_state.analysis_complete = True
                
                # Show success dialog if available
                if dialogs_available() and isinstance(analysis_result, dict):
                    show_success_dialog(analysis_result)
                else:
                    st.success("✅ Analysis completed successfully!")
                    st.rerun()
            else:
                error = result.get('error', 'Unknown error')
                if dialogs_available():
                    show_error_dialog("Analysis Failed", error)
                else:
                    st.error(f"Analysis failed: {error}")
                logger.error(f"Analysis error: {error}")

        except Exception as e:
            if dialogs_available():
                show_error_dialog("An error occurred", str(e))
            else:
                st.error(f"An error occurred: {e!s}")
            logger.exception("Error during analysis")


def render_results():
    """Render analysis results if available."""
    if not st.session_state.get('analysis_complete') or not st.session_state.get('analysis_results'):
        return

    result = st.session_state.analysis_results

    st.subheader("Analysis Results")

    # Debug info in expander
    with st.expander("Debug Info", expanded=False):
        st.write("Result type:", type(result))
        st.write("Result attributes:", [attr for attr in dir(result) if not attr.startswith('_')])
        if hasattr(result, '__dict__'):
            st.write("Result data:", result.__dict__)

    # Display metrics using fragment
    render_live_metrics(result)

    # Display map
    # Use fragment-based interactive map
    render_interactive_map(result)

    # Display POI table using fragment
    render_poi_table_fragment(result)

    # Export options
    render_export_options(result)


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from object with fallback."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def safe_get_dict(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get dictionary value with fallback."""
    try:
        if hasattr(obj, 'get'):
            return obj.get(key, default)
        elif hasattr(obj, key):
            return getattr(obj, key, default)
        else:
            return default
    except Exception:
        return default


def render_metrics(result: Any):
    """Render key metrics from the analysis."""
    col1, col2, col3, col4 = st.columns(4)

    # Safely extract POIs
    pois = safe_get_attr(result, 'pois', [])
    if not isinstance(pois, list):
        pois = []

    # Safely extract metadata
    metadata = safe_get_attr(result, 'metadata', {})
    if not isinstance(metadata, dict):
        metadata = {}

    # Safely extract demographics
    demographics = safe_get_attr(result, 'demographics', {})
    if not isinstance(demographics, dict):
        demographics = {}

    with col1:
        st.metric(
            label="POIs Found",
            value=len(pois),
            help="Number of points of interest within the travel time area"
        )

    with col2:
        area_km2 = safe_get_dict(metadata, 'area_km2', 0)
        st.metric(
            label="Area Coverage",
            value=f"{float(area_km2):.1f} km²",
            help="Total area covered by the isochrone"
        )

    with col3:
        total_pop = safe_get_dict(demographics, 'B01003_001E', 0)
        st.metric(
            label="Population Served",
            value=f"{int(total_pop):,}",
            help="Total population within the accessible area"
        )

    with col4:
        from socialmapper.census.utils import format_monetary_value

        median_income = safe_get_dict(demographics, 'B19013_001E', None)
        st.metric(
            label="Median Income",
            value=format_monetary_value(median_income, 'B19013_001E'),
            help="Median household income in the area"
        )





def render_poi_table(result: Any):
    """Render the POI table."""
    st.subheader("🏢 Points of Interest")

    try:
        pois = safe_get_attr(result, 'pois', [])

        if pois and isinstance(pois, list):
            poi_data = []
            for poi in pois[:20]:  # Show first 20
                if isinstance(poi, dict):
                    tags = poi.get('tags', {}) if isinstance(poi.get('tags'), dict) else {}
                    poi_data.append({
                        "Name": tags.get('name', 'Unnamed'),
                        "Distance (m)": round(float(poi.get('distance', 0))),
                        "Travel Time (min)": round(float(poi.get('travel_time', 0)))
                    })

            if poi_data:
                df_pois = pd.DataFrame(poi_data)

                # Sort by distance
                df_pois = df_pois.sort_values('Distance (m)')

                st.dataframe(
                    df_pois,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Distance (m)": st.column_config.NumberColumn(format="%d m"),
                        "Travel Time (min)": st.column_config.NumberColumn(format="%d min")
                    }
                )

                if len(pois) > 20:
                    st.info(f"Showing 20 of {len(pois)} POIs found")
            else:
                st.info("No POI data to display")
        else:
            st.info("No POIs found in this area")

    except Exception as e:
        st.error(f"Error displaying POIs: {e!s}")
        logger.exception("POI table rendering error")


def create_csv_export(result: Any) -> str:
    """Create CSV export from analysis results.
    
    Args:
        result: Analysis result object
        
    Returns:
        CSV string ready for download
    """
    import pandas as pd
    from io import StringIO
    
    # Extract data based on result type
    if isinstance(result, dict):
        # Handle dictionary results
        pois = result.get('pois', [])
        demographics = result.get('demographics', {})
        metadata = {
            'location': result.get('location', 'Unknown'),
            'poi_type': result.get('poi_type', 'Unknown'),
            'poi_name': result.get('poi_name', 'Unknown'),
            'travel_time': result.get('travel_time', 0),
            'travel_mode': result.get('travel_mode', 'Unknown'),
            'poi_count': result.get('poi_count', len(pois)),
            'total_population': result.get('total_population', 0),
            'area_km2': result.get('area_km2', 0),
            'census_units_analyzed': result.get('census_units_analyzed', 0)
        }
    else:
        # Handle object results
        pois = safe_get_attr(result, 'pois', [])
        demographics = safe_get_attr(result, 'demographics', {})
        metadata = {
            'location': safe_get_attr(result, 'location', 'Unknown'),
            'poi_type': safe_get_attr(result, 'poi_type', 'Unknown'),
            'poi_name': safe_get_attr(result, 'poi_name', 'Unknown'),
            'travel_time': safe_get_attr(result, 'travel_time', 0),
            'travel_mode': safe_get_attr(result, 'travel_mode', 'Unknown'),
            'poi_count': len(pois),
            'total_population': safe_get_attr(result, 'total_population', 0),
            'area_km2': safe_get_attr(result, 'area_km2', 0),
            'census_units_analyzed': safe_get_attr(result, 'census_units_analyzed', 0)
        }
    
    # Create output buffer
    output = StringIO()
    
    # Write metadata section
    output.write("# SocialMapper Analysis Results\n")
    output.write(f"# Generated: {pd.Timestamp.now()}\n")
    output.write("#\n")
    output.write("# Metadata\n")
    for key, value in metadata.items():
        output.write(f"# {key}: {value}\n")
    output.write("#\n")
    
    # Write POI data if available
    if pois:
        output.write("\n# Points of Interest\n")
        poi_data = []
        for poi in pois:
            if isinstance(poi, dict):
                poi_data.append({
                    'name': poi.get('name', 'Unnamed'),
                    'type': poi.get('type', 'Unknown'),
                    'lat': poi.get('lat', 0),
                    'lon': poi.get('lon', 0),
                    'distance_km': poi.get('distance', 0),
                    'address': poi.get('address', 'N/A')
                })
            else:
                poi_data.append({
                    'name': safe_get_attr(poi, 'name', 'Unnamed'),
                    'type': safe_get_attr(poi, 'type', 'Unknown'),
                    'lat': safe_get_attr(poi, 'lat', 0),
                    'lon': safe_get_attr(poi, 'lon', 0),
                    'distance_km': safe_get_attr(poi, 'distance', 0),
                    'address': safe_get_attr(poi, 'address', 'N/A')
                })
        
        poi_df = pd.DataFrame(poi_data)
        poi_df.to_csv(output, index=False)
    
    # Write demographic data if available
    if demographics:
        output.write("\n# Demographic Data\n")
        demo_data = [{'variable': k, 'value': v} for k, v in demographics.items()]
        demo_df = pd.DataFrame(demo_data)
        demo_df.to_csv(output, index=False)
    
    return output.getvalue()


def render_export_options(result: Any):
    """Render export/download options."""
    st.subheader("📥 Export Options")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Download CSV", type="secondary"):
            try:
                import pandas as pd
                from io import StringIO
                import datetime
                
                # Create CSV data
                csv_data = create_csv_export(result)
                
                # Generate filename with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"socialmapper_analysis_{timestamp}.csv"
                
                # Offer download
                st.download_button(
                    label="📥 Download CSV File",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Download analysis results as CSV"
                )
                st.success("CSV data ready for download!")
            except Exception as e:
                st.error(f"Export error: {e!s}")
                logger.error(f"CSV export error: {e}")

    with col2:
        if st.button("📄 Generate Full Report", type="secondary"):
            st.info("Report generation will be implemented soon!")
