"""Getting Started Tutorial - Interactive Version

This page mirrors the [Getting Started Tutorial](https://mihiarc.github.io/socialmapper/tutorials/getting-started-tutorial/) documentation example,
analyzing library accessibility in Wake County, North Carolina.
"""

import logging
import os
from typing import Any

import pandas as pd
import streamlit as st

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
    dialogs_available,
    render_interactive_map,
    render_live_metrics,
    render_poi_table_fragment,
    show_error_dialog,
    show_success_dialog,
)
from ..utils import (
    ProgressTracker,
    get_census_variables,
    get_poi_types,
    run_analysis_with_progress,
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
        st.header("📚 Getting Started Tutorial")

    with col2:
        if dialogs_available() and st.button("📖 View Tutorial", use_container_width=True):
            st.info("This page mirrors: [Getting Started Tutorial](https://mihiarc.github.io/socialmapper/tutorials/getting-started-tutorial/)")

    with col3:
        if st.button("✅ Mark Complete", use_container_width=True):
            st.session_state.tutorial_progress["Getting Started"] = True
            st.success("Tutorial marked as complete!")
            st.rerun()

    st.markdown("""
    ## Library Accessibility in Wake County, North Carolina
    
    This tutorial introduces the fundamental concepts of SocialMapper through a practical example 
    analyzing library accessibility in Wake County, North Carolina.
    
    ### What You'll Learn
    
    - 🔍 How to search for Points of Interest (POIs) from OpenStreetMap
    - ⏱️ How to generate travel time isochrones  
    - 📊 How to analyze census demographics within reachable areas
    - 📥 How to export and interpret results
    
    ### Tutorial Overview
    
    This tutorial analyzes access to public libraries in Wake County, NC, demonstrating how 
    residents can reach these important community resources within a **15-minute walk**.
    """)

    # Tutorial reference
    with st.expander("📖 Tutorial Reference"):
        st.markdown("""
        This interactive page follows the exact workflow from the [Getting Started Tutorial](https://mihiarc.github.io/socialmapper/tutorials/getting-started-tutorial/):
        
        1. **Location**: Wake County, North Carolina
        2. **POI Type**: amenity=library (OpenStreetMap tags)
        3. **Travel Time**: 15 minutes walking
        4. **Census Variables**: Total population, median household income, median age
        
        The results you see here will match those described in the written tutorial.
        """)


def render_input_form():
    """Render the analysis input form - pre-populated with tutorial values."""
    st.subheader("🔧 Step-by-Step Analysis Configuration")

    # Tutorial guidance
    st.info("""
    💡 **Tutorial Mode**: The form below is pre-populated with the exact values from the 
    getting-started tutorial. You can run the analysis as-is to see the expected results, or 
    modify the values to explore on your own.
    """)

    # Step 1: Define Search Parameters
    st.markdown("### Step 1: Define Search Parameters")
    st.markdown("""
    First, we'll set up the geographic area and points of interest to analyze. The tutorial 
    uses Wake County, North Carolina to find public libraries.
    """)

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

        # Pre-select amenity for tutorial
        default_category_index = list(category_display.values()).index("🏛️ Amenities (Schools, Hospitals, etc.)")
        selected_category_display = st.selectbox(
            "POI Category",
            options=list(category_display.values()),
            index=default_category_index,
            help="Tutorial uses 'amenity' category for libraries"
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

        # Pre-select library for tutorial
        library_index = type_options.index("📚 Library") if "📚 Library" in type_options else 0
        selected_type_display = st.selectbox(
            "POI Type",
            options=type_options,
            index=library_index,
            help="Tutorial searches for libraries"
        )

        # Get the actual type key
        poi_type = category_types[type_options.index(selected_type_display)]

        # Show OSM wiki link for specific POI type
        osm_type_link = f"https://wiki.openstreetmap.org/wiki/Tag:{poi_category}={poi_type}"
        st.caption(f"[📖 Learn about {poi_category}={poi_type}]({osm_type_link})")

    # Step 2: Location and Travel Time
    st.markdown("### Step 2: Set Location and Travel Time")
    st.markdown("Next, specify the geographic area and how far people can travel.")

    with st.form("basic_analysis"):
        col1, col2, col3 = st.columns(3)

        with col1:
            location = st.text_input(
                "Location",
                value="Wake County, North Carolina",
                help="Tutorial analyzes Wake County, NC"
            )

        with col2:
            travel_time = st.slider(
                "Travel Time (minutes)",
                min_value=5,
                max_value=30,
                value=15,
                step=5,
                help="Tutorial uses 15-minute walk"
            )

        with col3:
            travel_mode = st.selectbox(
                "Travel Mode",
                options=["walk", "bike", "drive"],
                index=0,
                help="Walking includes all legally walkable paths (even roads without sidewalks). Each mode uses different speeds and network types."
            )

        # Step 3: Select Census Variables
        st.markdown("### Step 3: Select Census Variables")
        st.markdown("Choose demographic data to analyze within the reachable areas.")

        # Tutorial-specific census variables
        tutorial_vars = [
            ("total_population", "Total Population"),
            ("median_household_income", "Median Household Income"),
            ("median_age", "Median Age")
        ]

        # Get all available census variables
        census_vars = get_census_variables()

        # Pre-select tutorial variables
        default_selections = []
        for var_name, display_name in tutorial_vars:
            # Find the matching census variable by name
            for code, name in census_vars.items():
                if var_name in code.lower() or var_name in name.lower():
                    default_selections.append((code, name))
                    break

        census_variables = st.multiselect(
            "Census Variables",
            options=[(code, name) for code, name in census_vars.items()],
            default=default_selections,
            format_func=lambda x: x[1],
            help="Tutorial uses: Total Population, Median Household Income, Median Age"
        )

        # Step 4: Code Example
        st.markdown("### Step 4: Build and Run the Analysis")
        with st.expander("📝 View Tutorial Code"):
            st.code("""
# Tutorial code from the Getting Started Tutorial
with SocialMapperClient() as client:
    # Build configuration using fluent interface
    config = (SocialMapperBuilder()
        .with_location("Wake County", "North Carolina")
        .with_osm_pois("amenity", "library")
        .with_travel_time(15)
        .with_census_variables(
            "total_population",
            "median_household_income", 
            "median_age"
        )
        .with_exports(csv=True, isochrones=False, maps=True)
        .build()
    )
    
    # Run analysis
    result = client.run_analysis(config)
""", language="python")

        submitted = st.form_submit_button("🚀 Run Tutorial Analysis", type="primary", use_container_width=True)

    if submitted:
        handle_form_submission(location, poi_category, poi_type, travel_time,
                             travel_mode, census_variables)


def handle_form_submission(location: str, poi_category: str, poi_type: str,
                         travel_time: int, travel_mode: str,
                         census_variables: list[tuple[str, str]]):
    """Handle form submission and run analysis."""
    # Validate inputs first
    validation_errors = validate_analysis_inputs(location, poi_category, poi_type, travel_time, travel_mode)
    if validation_errors:
        for error in validation_errors:
            if dialogs_available():
                show_error_dialog("Validation Error", error)
            else:
                st.error(error)
        return

    # Extract census variable codes
    census_var_codes = [var[0] for var in census_variables] if census_variables else ["B01003_001E", "B19013_001E"]
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
            # Use the modern SocialMapper client with proper error handling
            result = execute_analysis_with_client(
                location=location,
                poi_category=poi_category,
                poi_type=poi_type,
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
                handle_analysis_error(error)

        except Exception as e:
            handle_analysis_error(str(e))
            logger.exception("Error during analysis")


def render_results():
    """Render analysis results matching the tutorial format."""
    if not st.session_state.get('analysis_complete') or not st.session_state.get('analysis_results'):
        return

    result = st.session_state.analysis_results

    # Step 5: Understanding the Output
    st.markdown("### Step 5: Understanding the Output")
    st.markdown("""
    The tutorial generates multiple outputs to help understand library accessibility:
    """)

    # Tutorial completion tracker
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📊 Analysis Results")
    with col2:
        if st.button("✅ Complete Tutorial", use_container_width=True):
            st.session_state.tutorial_progress["Getting Started"] = True
            st.success("Tutorial completed! 🎉")
            st.balloons()

    # Tutorial-style results display
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "🗺️ Map", "📊 Data Table", "📥 Export"])

    with tab1:
        st.markdown("#### Key Findings")
        # Display metrics using fragment
        render_live_metrics(result)

        # Tutorial explanation
        st.info("""
        📝 **Tutorial Insights**: The analysis shows how many libraries were found in Wake County 
        and how many census block groups are within a 15-minute walk of these libraries. This helps 
        understand the geographic distribution of library access.
        """)

    with tab2:
        st.markdown("#### Accessibility Map")
        # Use fragment-based interactive map
        render_interactive_map(result)

        st.info("""
        🗺️ **Map Legend**: 
        - 📍 Library locations are marked with pins
        - 🔵 Blue areas show 15-minute walking isochrones
        - Census block groups are color-coded by selected demographic variables
        """)

    with tab3:
        st.markdown("#### Detailed Results")
        # Display POI table using fragment
        render_poi_table_fragment(result)

        st.info("""
        📊 **Data Explanation**: This table shows detailed information for each library including 
        demographics of the population within walking distance. The tutorial CSV export contains 
        even more detailed census data.
        """)

    with tab4:
        st.markdown("#### Export Your Results")
        # Export options
        render_export_options(result)

        st.info("""
        📥 **Export Formats**:
        - **CSV**: Detailed demographic data for further analysis
        - **Maps**: High-resolution images for presentations
        - **GeoJSON**: Geographic data for GIS software
        
        These match the output formats described in the tutorial documentation.
        """)

    # Tutorial completion and next steps
    st.markdown("---")
    st.markdown("### 🎯 Tutorial Complete!")

    col1, col2 = st.columns(2)
    with col1:
        st.success("""
        **Congratulations!** You've completed the Getting Started tutorial and learned:
        - ✅ How to search for POIs using OpenStreetMap
        - ✅ How to generate travel time isochrones
        - ✅ How to analyze census demographics
        - ✅ How to export and interpret results
        """)

    with col2:
        st.info("""
        **Next Steps:**
        - 📍 Try the **Custom POIs** tutorial to upload your own locations
        - 🚴 Explore the **Travel Modes** tutorial for multi-modal analysis
        - 📊 Learn about **ZCTA Analysis** for ZIP code-level insights
        - 📮 Master **Address Geocoding** for precise location analysis
        """)

    # Link to documentation
    st.markdown("""
    📚 **Learn More**: Visit the [full documentation](https://mihiarc.github.io/socialmapper/) 
    for advanced features, API reference, and more examples.
    """)


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
    """Create comprehensive CSV export from analysis results.
    
    Args:
        result: Analysis result object
        
    Returns:
        CSV string ready for download
    """
    import datetime
    from io import StringIO

    import pandas as pd

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

    # Write comprehensive header with metadata
    output.write("# SocialMapper Analysis Results\n")
    output.write(f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write("# Tool: SocialMapper Community Accessibility Analysis\n")
    output.write("#\n")
    output.write("# Analysis Configuration\n")
    for key, value in metadata.items():
        output.write(f"# {key.replace('_', ' ').title()}: {value}\n")
    output.write("#\n")

    # Write summary statistics
    output.write("# Summary Statistics\n")
    output.write(f"# POIs Found: {len(pois)}\n")
    output.write(f"# Area Analyzed: {metadata.get('area_km2', 0):.2f} km²\n")
    output.write(f"# Population Served: {metadata.get('total_population', 0):,}\n")
    output.write("#\n")

    # Write POI data if available
    if pois:
        output.write("\n# Points of Interest Data\n")
        poi_data = []
        for poi in pois:
            if isinstance(poi, dict):
                # Extract name from tags if available
                name = 'Unnamed'
                if 'tags' in poi and isinstance(poi['tags'], dict):
                    name = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
                elif 'name' in poi:
                    name = poi['name']

                # Extract address from tags if available
                address = 'N/A'
                if 'tags' in poi and isinstance(poi['tags'], dict):
                    addr_parts = []
                    for addr_field in ['addr:housenumber', 'addr:street', 'addr:city', 'addr:state']:
                        if poi['tags'].get(addr_field):
                            addr_parts.append(poi['tags'][addr_field])
                    if addr_parts:
                        address = ', '.join(addr_parts)

                poi_data.append({
                    'name': name,
                    'type': poi.get('type', 'Unknown'),
                    'latitude': poi.get('lat', 0),
                    'longitude': poi.get('lon', 0),
                    'distance_km': round(poi.get('distance', 0), 3),
                    'travel_time_min': round(poi.get('travel_time', 0), 1),
                    'address': address,
                    'osm_id': poi.get('id', 'N/A')
                })
            else:
                poi_data.append({
                    'name': safe_get_attr(poi, 'name', 'Unnamed'),
                    'type': safe_get_attr(poi, 'type', 'Unknown'),
                    'latitude': safe_get_attr(poi, 'lat', 0),
                    'longitude': safe_get_attr(poi, 'lon', 0),
                    'distance_km': round(safe_get_attr(poi, 'distance', 0), 3),
                    'travel_time_min': round(safe_get_attr(poi, 'travel_time', 0), 1),
                    'address': safe_get_attr(poi, 'address', 'N/A'),
                    'osm_id': safe_get_attr(poi, 'id', 'N/A')
                })

        poi_df = pd.DataFrame(poi_data)
        # Sort by distance for better usability
        poi_df = poi_df.sort_values('distance_km')
        poi_df.to_csv(output, index=False)

    # Write demographic data if available
    if demographics:
        output.write("\n\n# Demographic Analysis Data\n")
        from ..utils.formatters import format_census_variable

        demo_data = []
        for var_code, value in demographics.items():
            if value is not None:
                formatted = format_census_variable(var_code, value)
                if ': ' in formatted:
                    var_name, display_value = formatted.split(': ', 1)
                else:
                    var_name = var_code
                    display_value = str(value)

                demo_data.append({
                    'census_variable_code': var_code,
                    'variable_name': var_name,
                    'value': value,
                    'formatted_value': display_value
                })

        if demo_data:
            demo_df = pd.DataFrame(demo_data)
            demo_df.to_csv(output, index=False)

    return output.getvalue()


def create_geojson_export(result: Any) -> str:
    """Create GeoJSON export for isochrone and POI data.
    
    Args:
        result: Analysis result object
        
    Returns:
        GeoJSON string ready for download
    """
    import json

    # Extract data
    if isinstance(result, dict):
        pois = result.get('pois', [])
        isochrones = result.get('isochrones')
    else:
        pois = safe_get_attr(result, 'pois', [])
        isochrones = safe_get_attr(result, 'isochrones')

    # Create GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # Add POI features
    for poi in pois:
        if isinstance(poi, dict):
            name = 'Unnamed'
            if 'tags' in poi and isinstance(poi['tags'], dict):
                name = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
            elif 'name' in poi:
                name = poi['name']

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [poi.get('lon', 0), poi.get('lat', 0)]
                },
                "properties": {
                    "name": name,
                    "type": poi.get('type', 'Unknown'),
                    "distance_km": poi.get('distance', 0),
                    "travel_time_min": poi.get('travel_time', 0),
                    "category": "poi"
                }
            }
            geojson["features"].append(feature)

    # Add isochrone features if available
    if isochrones is not None and hasattr(isochrones, 'to_json'):
        try:
            isochrone_geojson = json.loads(isochrones.to_json())
            for feature in isochrone_geojson.get('features', []):
                feature['properties']['category'] = 'isochrone'
                geojson["features"].append(feature)
        except Exception as e:
            logger.warning(f"Could not export isochrones to GeoJSON: {e}")

    return json.dumps(geojson, indent=2)


def validate_analysis_inputs(location: str, poi_category: str, poi_type: str,
                           travel_time: int, travel_mode: str) -> list[str]:
    """Validate analysis inputs and return list of errors."""
    errors = []

    # Validate location
    if not location or not location.strip():
        errors.append("Please enter a valid location (e.g., 'Durham, North Carolina')")
    elif "," not in location:
        errors.append("Location should include city and state (e.g., 'Durham, North Carolina')")

    # Validate POI parameters
    if not poi_category or not poi_type:
        errors.append("Please select a valid POI category and type")

    # Validate travel time
    if not isinstance(travel_time, int) or travel_time < 5 or travel_time > 60:
        errors.append("Travel time must be between 5 and 60 minutes")

    # Validate travel mode
    if travel_mode not in ["walk", "bike", "drive"]:
        errors.append("Travel mode must be one of: walk, bike, drive")

    # Check for Census API key (warn but don't block)
    if not os.environ.get('CENSUS_API_KEY'):
        errors.append("Census API key is recommended for demographic analysis. Configure it in Settings.")

    return errors


def execute_analysis_with_client(location: str, poi_category: str, poi_type: str,
                               travel_time: int, travel_mode: str, census_vars: list[str],
                               progress_callback: callable) -> dict[str, Any]:
    """Execute analysis using the modern SocialMapper client."""
    try:
        # Report progress: Step 1
        progress_callback(1, "Initializing analysis configuration")

        # Use the modern SocialMapper client
        with SocialMapperClient() as client:
            # Report progress: Step 2
            progress_callback(2, f"Searching for {poi_type} in {location}")

            # Execute analysis using the client's analyze method
            result = client.analyze(
                location=location,
                poi_type=poi_category,
                poi_name=poi_type,
                travel_time=travel_time,
                census_variables=census_vars
            )

            # Handle Result type from modern API
            if hasattr(result, 'is_ok') and result.is_ok():
                # Report progress: Step 3
                progress_callback(3, "Processing POI and isochrone data")

                analysis_result = result.unwrap()

                # Report progress: Step 4
                progress_callback(4, "Analyzing census demographics")

                # Convert AnalysisResult to dictionary format expected by UI
                result_dict = {
                    'poi_count': analysis_result.poi_count,
                    'total_population': sum(analysis_result.demographics.values()) if analysis_result.demographics else 0,
                    'area_km2': analysis_result.isochrone_area,
                    'census_units_analyzed': analysis_result.census_units_analyzed,
                    'pois': analysis_result.pois,
                    'demographics': analysis_result.demographics,
                    'isochrones': analysis_result.isochrones,  # Pass through the isochrone GeoDataFrame
                    'metadata': analysis_result.metadata
                }

                # Report progress: Step 5
                progress_callback(5, "Generating final analysis report")

                return {
                    'success': True,
                    'data': result_dict
                }
            else:
                # Handle error result
                error = result.unwrap_err() if hasattr(result, 'unwrap_err') else result
                error_msg = str(error)
                logger.error(f"Analysis failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

    except Exception as e:
        logger.error(f"Client analysis failed: {e}")
        # Fallback to cached analysis method
        try:
            progress_callback(2, f"Falling back to cached analysis for {poi_type} in {location}")

            fallback_result = run_analysis_with_progress(
                location=location,
                poi_type=poi_category,
                poi_name=poi_type,
                travel_time=travel_time,
                travel_mode=travel_mode,
                census_vars=census_vars,
                progress_callback=progress_callback
            )

            return fallback_result

        except Exception as fallback_error:
            logger.error(f"Fallback analysis also failed: {fallback_error}")
            return {
                'success': False,
                'error': f"Analysis failed: {e!s}. Fallback also failed: {fallback_error!s}"
            }


def handle_analysis_error(error: str):
    """Handle analysis errors with appropriate UI feedback."""
    logger.error(f"Analysis error: {error}")

    # Categorize error and provide specific guidance
    if "api key" in error.lower():
        if dialogs_available():
            show_error_dialog(
                "Census API Key Required",
                "Please configure your Census API key in the Settings page to use demographic features."
            )
        else:
            st.error("Please configure your Census API key in the Settings page!")
    elif "no pois found" in error.lower() or "no poi" in error.lower():
        if dialogs_available():
            show_error_dialog(
                "No Points of Interest Found",
                "No POIs were found for your search criteria.\n\n"
                "Try:\n"
                "• Different POI type or location\n"
                "• Check location spelling\n"
                "• Increase travel time\n"
                "• Try a larger city nearby"
            )
        else:
            st.error("No POIs found. Try a different location or POI type.")
    elif "network" in error.lower() or "connection" in error.lower():
        if dialogs_available():
            show_error_dialog(
                "Network Error",
                "Network connection issue occurred.\n\n"
                "Try:\n"
                "• Check your internet connection\n"
                "• Wait a moment and try again\n"
                "• Try a different location"
            )
        else:
            st.error("Network error. Please check your connection and try again.")
    elif dialogs_available():
        show_error_dialog("Analysis Failed", f"Error: {error}")
    else:
        st.error(f"Analysis failed: {error}")


def render_export_options(result: Any):
    """Render enhanced export/download options."""
    st.subheader("📥 Export Options")

    # Export format selection
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Download CSV", type="secondary", use_container_width=True):
            try:
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
                    help="Download analysis results as CSV with POI and demographic data"
                )
                st.success("CSV data ready for download!")
            except Exception as e:
                st.error(f"CSV export error: {e!s}")
                logger.error(f"CSV export error: {e}")

    with col2:
        if st.button("🗺️ Download GeoJSON", type="secondary", use_container_width=True):
            try:
                import datetime

                # Create GeoJSON data
                geojson_data = create_geojson_export(result)

                # Generate filename with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"socialmapper_geospatial_{timestamp}.geojson"

                # Offer download
                st.download_button(
                    label="📥 Download GeoJSON File",
                    data=geojson_data,
                    file_name=filename,
                    mime="application/geo+json",
                    help="Download POI locations and isochrones as GeoJSON for GIS software"
                )
                st.success("GeoJSON data ready for download!")
            except Exception as e:
                st.error(f"GeoJSON export error: {e!s}")
                logger.error(f"GeoJSON export error: {e}")

    with col3:
        if st.button("📊 Generate Report", type="secondary", use_container_width=True):
            try:
                # Create comprehensive report
                report_data = create_analysis_report(result)

                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"socialmapper_report_{timestamp}.md"

                st.download_button(
                    label="📥 Download Report",
                    data=report_data,
                    file_name=filename,
                    mime="text/markdown",
                    help="Download comprehensive analysis report in Markdown format"
                )
                st.success("Analysis report ready for download!")
            except Exception as e:
                st.error(f"Report generation error: {e!s}")
                logger.error(f"Report generation error: {e}")

    # Export information
    with st.expander("ℹ️ Export Format Information"):
        st.markdown("""
        **CSV Format:**
        - Contains POI data with coordinates, names, distances
        - Includes demographic analysis results
        - Compatible with Excel, Google Sheets, and data analysis tools
        
        **GeoJSON Format:**
        - Spatial data format for GIS applications
        - Contains POI locations as points
        - Includes isochrone boundaries (if available)
        - Compatible with QGIS, ArcGIS, and web mapping libraries
        
        **Analysis Report:**
        - Comprehensive summary in Markdown format
        - Includes methodology, results, and interpretations
        - Can be converted to PDF or HTML
        """)


def create_analysis_report(result: Any) -> str:
    """Create a comprehensive analysis report in Markdown format.
    
    Args:
        result: Analysis result object
        
    Returns:
        Markdown formatted report string
    """
    import datetime

    from ..utils.formatters import format_census_variable

    # Extract data
    if isinstance(result, dict):
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

    # Generate report
    report = f"""# SocialMapper Accessibility Analysis Report

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Tool:** SocialMapper Community Accessibility Analysis

## Executive Summary

This report presents the results of an accessibility analysis for **{metadata['poi_name']}** locations in **{metadata['location']}** using a **{metadata['travel_time']}-minute {metadata['travel_mode']}** travel time threshold.

### Key Findings

- **{metadata['poi_count']} {metadata['poi_name']} locations** found within the travel time area
- **{metadata['area_km2']:.2f} km²** total area analyzed
- **{metadata['total_population']:,} people** served within the accessible area
- **{metadata['census_units_analyzed']} census units** included in demographic analysis

## Analysis Configuration

| Parameter | Value |
|-----------|-------|
| Location | {metadata['location']} |
| POI Category | {metadata['poi_type']} |
| POI Type | {metadata['poi_name']} |
| Travel Time | {metadata['travel_time']} minutes |
| Travel Mode | {metadata['travel_mode'].title()} |
| Analysis Date | {datetime.datetime.now().strftime('%Y-%m-%d')} |

## Demographic Analysis

The following demographic characteristics were analyzed for the accessible area:

"""

    # Add demographic data
    if demographics:
        for var_code, value in demographics.items():
            if value is not None:
                formatted = format_census_variable(var_code, value)
                if ': ' in formatted:
                    var_name, display_value = formatted.split(': ', 1)
                    report += f"- **{var_name}:** {display_value}\n"
    else:
        report += "No demographic data available for this analysis.\n"

    # Add POI details
    report += f"""
## Points of Interest Details

A total of **{len(pois)} {metadata['poi_name']} locations** were identified within the {metadata['travel_time']}-minute travel area.

"""

    if pois:
        report += "### Top 10 Closest Locations\n\n"
        report += "| Name | Distance (km) | Travel Time (min) |\n"
        report += "|------|---------------|-------------------|\n"

        # Sort POIs by distance and show top 10
        sorted_pois = sorted(pois, key=lambda x: x.get('distance', 0))[:10]

        for poi in sorted_pois:
            if isinstance(poi, dict):
                name = 'Unnamed'
                if 'tags' in poi and isinstance(poi['tags'], dict):
                    name = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
                elif 'name' in poi:
                    name = poi['name']

                distance = poi.get('distance', 0)
                travel_time = poi.get('travel_time', 0)
                report += f"| {name} | {distance:.2f} | {travel_time:.1f} |\n"

    # Add methodology
    report += f"""
## Methodology

This analysis was conducted using SocialMapper, an open-source toolkit for community accessibility analysis.

### Data Sources

- **Points of Interest:** OpenStreetMap (OSM) database
- **Demographic Data:** U.S. Census Bureau American Community Survey (ACS)
- **Travel Networks:** OpenStreetMap road and path networks
- **Travel Time Calculation:** OSMnx routing engine

### Analysis Process

1. **Location Geocoding:** The specified location was geocoded to obtain geographic coordinates
2. **POI Discovery:** OpenStreetMap was queried for {metadata['poi_name']} locations in the area
3. **Isochrone Generation:** Travel time areas were calculated using {metadata['travel_mode']} routing
4. **Demographic Analysis:** Census data was retrieved for areas within the travel time threshold
5. **Results Compilation:** POI and demographic data were aggregated and analyzed

### Limitations

- Analysis is limited to locations present in OpenStreetMap
- Travel times are estimates based on network analysis and may not reflect real-world conditions
- Demographic data is based on census estimates and may not reflect current conditions
- Analysis assumes optimal travel conditions without considering traffic, weather, or other factors

## Interpretation

### Accessibility Assessment

The analysis found **{metadata['poi_count']} {metadata['poi_name']} locations** accessible within a **{metadata['travel_time']}-minute {metadata['travel_mode']}** from the specified location. This represents the baseline accessibility for this service type in the area.

### Service Coverage

The accessible area covers **{metadata['area_km2']:.2f} km²** and serves approximately **{metadata['total_population']:,} people**. This provides insight into the population that has reasonable access to these services.

### Recommendations

Based on this analysis, consider the following:

1. **Service Gaps:** Areas with longer travel times may indicate service gaps
2. **Population Density:** High-population areas with limited access may benefit from additional services
3. **Transportation:** Consider how different travel modes affect accessibility
4. **Equity:** Analyze demographic patterns to identify potential equity issues

## Data Export

This analysis can be exported in multiple formats:

- **CSV:** Detailed POI and demographic data for further analysis
- **GeoJSON:** Spatial data for use in GIS applications
- **Report:** This comprehensive summary document

---

*Report generated by SocialMapper - Open Source Community Accessibility Analysis*
"""

    return report
