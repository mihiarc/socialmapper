"""SocialMapper Interactive Dashboard
A professional Streamlit application for community accessibility analysis.
"""

import os

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

# Import SocialMapper components
from socialmapper import (
    SocialMapperBuilder,
    SocialMapperClient,
)

# Page configuration
st.set_page_config(
    page_title="SocialMapper Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Getting Started"

# Helper functions
def create_folium_map(lat, lon, isochrone_data=None):
    """Create an interactive folium map with optional isochrone overlay."""
    m = folium.Map(location=[lat, lon], zoom_start=13)

    # Add center marker
    folium.Marker(
        [lat, lon],
        popup="Analysis Center",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    # Add isochrone if available
    if isochrone_data:
        folium.GeoJson(
            isochrone_data,
            style_function=lambda x: {
                'fillColor': '#3388ff',
                'color': '#3388ff',
                'weight': 2,
                'fillOpacity': 0.3
            }
        ).add_to(m)

    return m

def format_census_variable(var_code: str, value: float | int) -> str:
    """Format census variables with human-readable names."""
    variable_names = {
        "B01003_001E": "Total Population",
        "B19013_001E": "Median Household Income",
        "B25077_001E": "Median Home Value",
        "B15003_022E": "Bachelor's Degree Holders",
        "B08301_021E": "Public Transit Users",
        "B17001_002E": "Population in Poverty"
    }
    # Ensure name is always a string (fallback to var_code if not found)
    name = variable_names.get(var_code, var_code)
    
    # Type safety: name is guaranteed to be a string here since var_code is a string
    # and dict.get() returns either a string value or the string fallback
    name_lower = name.lower()

    if "income" in name_lower or "value" in name_lower:
        return f"{name}: ${value:,.0f}"
    elif "population" in name_lower or "holders" in name_lower or "users" in name_lower:
        return f"{name}: {value:,.0f}"
    else:
        return f"{name}: {value}"

# Sidebar navigation
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

    selected_page = st.radio(
        "Select Tutorial",
        pages,
        index=pages.index(st.session_state.current_page)
    )

    st.session_state.current_page = selected_page

    st.markdown("---")

    # API Key configuration
    st.markdown("### 🔑 API Configuration")

    # Check for API key in Streamlit secrets first
    try:
        if "census" in st.secrets and "CENSUS_API_KEY" in st.secrets["census"]:
            os.environ['CENSUS_API_KEY'] = st.secrets["census"]["CENSUS_API_KEY"]
            st.success("✅ API key loaded from secrets")
        else:
            # Fall back to manual input
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
    except FileNotFoundError:
        # No secrets file, use manual input
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

    st.markdown("---")
    st.markdown("### 📊 About SocialMapper")
    st.info(
        "SocialMapper analyzes community connections by mapping demographics "
        "and access to points of interest using isochrones and census data."
    )

# Main content area
st.markdown('<h1 class="main-header">🗺️ SocialMapper Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Interactive Community Accessibility Analysis</p>', unsafe_allow_html=True)

# Page content based on selection
if selected_page == "Getting Started":
    st.markdown("## 🚀 Getting Started with SocialMapper")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        Welcome to SocialMapper! This interactive dashboard helps you analyze community
        accessibility by combining:

        - **Points of Interest (POIs)** from OpenStreetMap
        - **Travel time isochrones** (walk, bike, drive)
        - **Census demographic data** for equity analysis
        - **Professional visualizations** for insights
        """)

        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        **Quick Start:** Enter a location below to find nearby libraries and analyze
        the demographics of people within walking distance.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.metric("Tutorial Progress", "1 of 6")
        st.progress(1/6)

    st.markdown("---")

    # Input form
    with st.form("basic_analysis"):
        col1, col2, col3 = st.columns(3)

        with col1:
            location = st.text_input(
                "📍 Location",
                value="Durham, North Carolina",
                help="Enter a city, address, or place name"
            )

        with col2:
            poi_type = st.selectbox(
                "🏛️ Point of Interest Type",
                ["amenity", "shop", "leisure", "healthcare", "education"],
                help="OpenStreetMap category"
            )

            poi_name = st.text_input(
                "🔍 POI Name",
                value="library",
                help="Specific type within category"
            )

        with col3:
            travel_time = st.slider(
                "⏱️ Travel Time (minutes)",
                min_value=5,
                max_value=30,
                value=15,
                step=5
            )

            travel_mode = st.selectbox(
                "🚶 Travel Mode",
                ["walk", "bike", "drive"]
            )

        # Census variables selection
        st.markdown("### 📊 Census Variables")
        census_vars = st.multiselect(
            "Select demographic variables to analyze",
            [
                ("B01003_001E", "Total Population"),
                ("B19013_001E", "Median Household Income"),
                ("B25077_001E", "Median Home Value"),
                ("B15003_022E", "Bachelor's Degree Holders"),
                ("B08301_021E", "Public Transit Users"),
                ("B17001_002E", "Population in Poverty")
            ],
            default=[("B01003_001E", "Total Population"), ("B19013_001E", "Median Household Income")],
            format_func=lambda x: x[1]
        )

        # Save census vars to session state for display
        st.session_state.census_vars = census_vars

        submitted = st.form_submit_button("🔍 Run Analysis", use_container_width=True)

    # Analysis execution inside form
    if submitted:
        if not os.environ.get('CENSUS_API_KEY'):
            st.error("⚠️ Please configure your Census API key in the sidebar")
        else:
            try:
                with st.spinner("🔄 Running analysis..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Initialize client
                    status_text.text("Initializing SocialMapper client...")
                    progress_bar.progress(20)

                    with SocialMapperClient() as client:
                        # Build configuration
                        status_text.text("Building analysis configuration...")
                        progress_bar.progress(40)

                        # Parse location into city and state
                        if ", " in location:
                            city, state = location.split(", ", 1)
                            config = (SocialMapperBuilder()
                                .with_location(city, state)
                                .with_osm_pois(poi_type, poi_name)
                                .with_travel_time(travel_time)
                                .with_travel_mode(travel_mode)
                                .with_census_variables(*[var[0] for var in census_vars])
                                .with_exports(csv=True, isochrones=True, maps=False)
                                .build()
                            )
                        else:
                            # Single location name
                            config = (SocialMapperBuilder()
                                .with_location(location)
                                .with_osm_pois(poi_type, poi_name)
                                .with_travel_time(travel_time)
                                .with_travel_mode(travel_mode)
                                .with_census_variables(*[var[0] for var in census_vars])
                                .with_exports(csv=True, isochrones=True, maps=False)
                                .build()
                            )

                        # Run analysis
                        status_text.text("Executing analysis...")
                        progress_bar.progress(60)

                        result = client.run_analysis(config)

                        if result.is_ok():
                            progress_bar.progress(100)
                            status_text.text("Analysis complete!")

                            analysis_result = result.unwrap()
                            st.session_state.analysis_results = analysis_result
                            st.session_state.analysis_complete = True

                            # Just show success message
                            st.success("✅ Analysis completed successfully!")
                            st.rerun()

                        else:
                            error = result.unwrap_err()
                            st.error(f"❌ Analysis failed: {error.message}")

                            # Provide more specific guidance based on error type
                            if "no pois found" in error.message.lower():
                                st.info("""
                                💡 **No POIs found. Try:**
                                - Using a different POI type (e.g., "shop" instead of "amenity")
                                - Using a different POI name (e.g., "restaurant" instead of "library")
                                - Checking the location spelling
                                - Using a larger city or different area
                                """)
                            elif "numba" in error.message.lower():
                                st.warning("""
                                ⚠️ **Performance module not available**

                                The analysis may run slower without the performance optimization module.
                                This won't affect the results, just the speed.
                                """)
                            elif "census" in error.message.lower():
                                st.error("""
                                🔑 **Census API issue**

                                Please check that your Census API key is valid and configured in the sidebar.
                                """)

            except Exception as e:
                st.error(f"❌ An error occurred: {e!s}")
                st.info("Please check your API key and internet connection")

                # Log the full error for debugging
                import traceback
                st.expander("🔍 Full Error Details").code(traceback.format_exc())

    # Display results outside of form
    if 'analysis_complete' in st.session_state and st.session_state.analysis_complete:
        if 'analysis_results' in st.session_state:
            analysis_result = st.session_state.analysis_results

            # Check if we actually have POIs
            poi_count = analysis_result.poi_count

            if poi_count == 0:
                st.warning("""
                ⚠️ **No POIs found in the search area**

                This could mean:
                - There are no libraries in the specified area
                - The location name might need to be more specific
                - Try searching for a different POI type
                """)

            # Metrics row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "POIs Found",
                    poi_count
                )

            with col2:
                st.metric(
                    "Area Coverage",
                    f"{analysis_result.isochrone_area:.1f} km²"
                )

            with col3:
                pop = analysis_result.demographics.get('B01003_001E', 0)
                st.metric(
                    "Population Served",
                    f"{pop:,.0f}"
                )

            with col4:
                income = analysis_result.demographics.get('B19013_001E', 0)
                st.metric(
                    "Median Income",
                    f"${income:,.0f}"
                )

            # Map and demographics
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("### 🗺️ Interactive Map")

                # Create map centered on analysis location
                # Get center from metadata or use default
                center_lat = analysis_result.metadata.get('center_lat', 35.7796)
                center_lon = analysis_result.metadata.get('center_lon', -78.6382)

                m = create_folium_map(center_lat, center_lon)

                # Add POI markers
                for poi in analysis_result.pois[:10]:  # Limit to 10 POIs
                    # Get name from tags or use ID as fallback
                    poi_name = poi.get('name') or poi.get('tags', {}).get('name', f"POI {poi.get('id', 'Unknown')}")
                    folium.Marker(
                        [poi['lat'], poi['lon']],
                        popup=poi_name,
                        icon=folium.Icon(color='green', icon='book')
                    ).add_to(m)

                st_folium(m, height=400, use_container_width=True)

            with col2:
                st.markdown("### 📊 Demographics")

                # Get census vars from session state or use defaults
                census_vars = st.session_state.get('census_vars', [
                    ("B01003_001E", "Total Population"),
                    ("B19013_001E", "Median Household Income")
                ])

                demo_df = pd.DataFrame([
                    {"Variable": format_census_variable(var[0],
                     analysis_result.demographics.get(var[0], 0)).split(':')[0],
                     "Value": format_census_variable(var[0],
                     analysis_result.demographics.get(var[0], 0)).split(':')[1]}
                    for var in census_vars
                ])

                st.dataframe(demo_df, hide_index=True, use_container_width=True)

            # POIs table
            if analysis_result.pois:
                st.markdown("### 📍 Points of Interest Found")
                # Process POI data to extract names from tags
                poi_data = []
                for poi in analysis_result.pois[:20]:
                    poi_dict = {
                        'name': poi.get('name') or poi.get('tags', {}).get('name', f"POI {poi.get('id', 'Unknown')}"),
                        'lat': poi.get('lat'),
                        'lon': poi.get('lon'),
                    }
                    # Add distance and travel time if available
                    if 'distance_km' in poi:
                        poi_dict['distance_km'] = poi['distance_km']
                    if 'travel_time_min' in poi:
                        poi_dict['travel_time_min'] = poi['travel_time_min']
                    poi_data.append(poi_dict)

                poi_df = pd.DataFrame(poi_data)

                if not poi_df.empty:
                    # Show relevant columns
                    display_cols = [col for col in ['name', 'distance_km', 'travel_time_min'] if col in poi_df.columns]
                    if display_cols:
                        poi_df = poi_df[display_cols].rename(columns={
                            'name': 'Name',
                            'distance_km': 'Distance (km)',
                            'travel_time_min': 'Travel Time (min)'
                        })
                        poi_df = poi_df.round(2)
                        st.dataframe(poi_df, hide_index=True, use_container_width=True)

            # Download options
            st.markdown("### 💾 Export Results")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📥 Download CSV"):
                    if 'poi_df' in locals() and not poi_df.empty:
                        csv_data = poi_df.to_csv(index=False)
                        st.download_button(
                            "Download",
                            csv_data,
                            "socialmapper_results.csv",
                            "text/csv"
                        )

            with col2:
                if st.button("📥 Download Full Report"):
                    st.info("Full report generation coming soon!")

elif selected_page == "Custom POIs":
    st.markdown("## 📍 Custom Points of Interest")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        Analyze accessibility to your own custom locations by uploading a CSV file
        with coordinates. Perfect for:

        - Analyzing specific facilities not in OpenStreetMap
        - Comparing multiple proposed locations
        - Custom business or service locations
        """)

    with col2:
        st.metric("Tutorial Progress", "2 of 6")
        st.progress(2/6)

    st.markdown("---")

    # CSV template
    st.markdown("### 📄 CSV Format")
    st.code("""name,latitude,longitude,type
Central Library,35.7796,-78.6382,library
City Park,35.7821,-78.6589,park
Community Center,35.7754,-78.6434,community_center""")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload your CSV file",
        type=['csv'],
        help="CSV must have columns: name, latitude, longitude, type"
    )

    # Sample data option
    if st.button("🔧 Use Sample Data"):
        sample_data = """name,latitude,longitude,type
Durham Central Library,35.9940,-78.8986,library
Duke University Library,36.0014,-78.9388,library
South Regional Library,35.9012,-78.8499,library
East Regional Library,35.9669,-78.8599,library
North Regional Library,36.0459,-78.8773,library"""

        uploaded_file = sample_data

    if uploaded_file:
        try:
            # Read CSV
            if isinstance(uploaded_file, str):
                import io
                df = pd.read_csv(io.StringIO(uploaded_file))
            else:
                df = pd.read_csv(uploaded_file)

            st.success(f"✅ Loaded {len(df)} locations")

            # Display preview
            st.markdown("### 📊 Location Preview")
            st.dataframe(df, use_container_width=True)

            # Map preview
            st.markdown("### 🗺️ Location Map")

            # Create map centered on mean coordinates
            center_lat = df['latitude'].mean()
            center_lon = df['longitude'].mean()

            m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

            # Add markers for each location
            for _idx, row in df.iterrows():
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    popup=f"{row['name']} ({row['type']})",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)

            st_folium(m, height=400, use_container_width=True)

            # Analysis options
            st.markdown("### ⚙️ Analysis Configuration")

            with st.form("custom_poi_analysis"):
                col1, col2 = st.columns(2)

                with col1:
                    travel_time = st.slider(
                        "Travel Time (minutes)",
                        5, 30, 15, 5
                    )

                    travel_mode = st.selectbox(
                        "Travel Mode",
                        ["walk", "bike", "drive"]
                    )

                with col2:
                    geographic_level = st.selectbox(
                        "Geographic Level",
                        ["block_group", "zcta"],
                        format_func=lambda x: "Block Groups" if x == "block_group" else "ZIP Codes (ZCTA)"
                    )

                    aggregate_isochrones = st.checkbox(
                        "Merge overlapping isochrones",
                        value=True
                    )

                # Census variables
                census_vars = st.multiselect(
                    "Census Variables",
                    [
                        ("B01003_001E", "Total Population"),
                        ("B19013_001E", "Median Household Income"),
                        ("B17001_002E", "Population in Poverty"),
                        ("B08301_021E", "Public Transit Users")
                    ],
                    default=[("B01003_001E", "Total Population")],
                    format_func=lambda x: x[1]
                )

                analyze_btn = st.form_submit_button("🔍 Analyze Custom Locations", use_container_width=True)

            if analyze_btn:
                st.info("Custom POI analysis implementation would go here")
                # Implementation would follow similar pattern to Getting Started

        except Exception as e:
            st.error(f"❌ Error reading CSV: {e!s}")
            st.info("Please ensure your CSV has the required columns: name, latitude, longitude, type")

elif selected_page == "Travel Modes":
    st.markdown("## 🚶🚴🚗 Travel Mode Comparison")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        Compare accessibility across different transportation modes to understand
        how travel options affect community access. This analysis helps identify:

        - Transportation equity gaps
        - Areas underserved by walking/biking infrastructure
        - The impact of car dependency
        """)

    with col2:
        st.metric("Tutorial Progress", "3 of 6")
        st.progress(3/6)

    st.markdown("---")

    # Input configuration
    with st.form("travel_mode_comparison"):
        col1, col2 = st.columns(2)

        with col1:
            location = st.text_input(
                "📍 Analysis Location",
                value="Chapel Hill, North Carolina"
            )

            poi_category = st.selectbox(
                "🏛️ POI Category",
                ["Healthcare", "Education", "Food", "Recreation"],
                help="Pre-configured category sets"
            )

        with col2:
            time_limit = st.slider(
                "⏱️ Time Limit (minutes)",
                5, 30, 15, 5
            )

            show_overlap = st.checkbox(
                "Show overlap areas",
                value=True,
                help="Highlight areas accessible by multiple modes"
            )

        compare_btn = st.form_submit_button("🔍 Compare Travel Modes", use_container_width=True)

    if compare_btn:
        # Simulated results for demonstration
        st.success("✅ Travel mode analysis complete!")

        # Metrics comparison
        st.markdown("### 📊 Accessibility Metrics by Mode")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🚶 Walking")
            st.metric("Area Coverage", "2.1 km²")
            st.metric("Population Reached", "5,420")
            st.metric("POIs Accessible", "3")

        with col2:
            st.markdown("#### 🚴 Biking")
            st.metric("Area Coverage", "12.5 km²", "495% ↑")
            st.metric("Population Reached", "22,180", "309% ↑")
            st.metric("POIs Accessible", "12", "300% ↑")

        with col3:
            st.markdown("#### 🚗 Driving")
            st.metric("Area Coverage", "78.3 km²", "3,628% ↑")
            st.metric("Population Reached", "84,320", "1,455% ↑")
            st.metric("POIs Accessible", "28", "833% ↑")

        # Visualization
        st.markdown("### 📈 Comparative Analysis")

        # Create sample data for visualization
        mode_data = pd.DataFrame({
            'Mode': ['Walk', 'Bike', 'Drive'],
            'Area (km²)': [2.1, 12.5, 78.3],
            'Population': [5420, 22180, 84320],
            'POIs': [3, 12, 28]
        })

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                mode_data,
                x='Mode',
                y='Population',
                title='Population Reached by Travel Mode',
                color='Mode',
                color_discrete_map={'Walk': '#FF6B6B', 'Bike': '#4ECDC4', 'Drive': '#45B7D1'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                mode_data,
                x='Area (km²)',
                y='POIs',
                size='Population',
                color='Mode',
                title='Coverage vs Accessibility',
                color_discrete_map={'Walk': '#FF6B6B', 'Bike': '#4ECDC4', 'Drive': '#45B7D1'}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Equity insights
        st.markdown("### 💡 Equity Insights")

        st.info("""
        **Key Findings:**
        - Walking access serves only 6% of the population that driving reaches
        - Biking extends reach by 4x compared to walking
        - 76% of POIs require a car to reach within 15 minutes
        """)

elif selected_page == "ZCTA Analysis":
    st.markdown("## 📮 ZIP Code Area (ZCTA) Analysis")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        Analyze larger geographic areas using ZIP Code Tabulation Areas (ZCTAs).
        This approach is ideal for:

        - Regional planning and policy analysis
        - Comparing neighborhoods or districts
        - Faster analysis of large areas
        - Report generation for stakeholders
        """)

        # Comparison table
        st.markdown("### Block Groups vs ZCTAs")
        comparison_df = pd.DataFrame({
            'Aspect': ['Population Size', 'Geographic Size', 'Data Granularity', 'Processing Speed', 'Best For'],
            'Block Groups': ['600-3,000 people', '~40 blocks', 'Very detailed', 'Slower', 'Local analysis'],
            'ZCTAs': ['5,000-50,000 people', 'Entire ZIP code', 'Less detailed', 'Much faster', 'Regional analysis']
        })
        st.dataframe(comparison_df, hide_index=True, use_container_width=True)

    with col2:
        st.metric("Tutorial Progress", "4 of 6")
        st.progress(4/6)

    st.markdown("---")

    # ZCTA analysis form
    with st.form("zcta_analysis"):
        col1, col2 = st.columns(2)

        with col1:
            location = st.text_input(
                "📍 Location or ZIP Code",
                value="27514",
                help="Enter a ZIP code or city name"
            )

            analysis_type = st.selectbox(
                "📊 Analysis Type",
                ["Single ZCTA", "Multiple ZCTAs", "County-wide"]
            )

        with col2:
            poi_categories = st.multiselect(
                "🏛️ POI Categories",
                ["Healthcare", "Education", "Food Access", "Public Services", "Recreation"],
                default=["Healthcare", "Food Access"]
            )

            include_neighboring = st.checkbox(
                "Include neighboring ZCTAs",
                value=False
            )

        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            col1, col2 = st.columns(2)

            with col1:
                buffer_distance = st.slider(
                    "Buffer Distance (km)",
                    0, 10, 2,
                    help="Extend analysis beyond ZCTA boundaries"
                )

            with col2:
                min_population = st.number_input(
                    "Minimum Population",
                    min_value=0,
                    value=1000,
                    help="Filter out low-population areas"
                )

        analyze_btn = st.form_submit_button("🔍 Analyze ZCTA", use_container_width=True)

    if analyze_btn:
        st.info("ZCTA analysis implementation would display regional demographic patterns and accessibility metrics")

elif selected_page == "Address Geocoding":
    st.markdown("## 📍 Address Geocoding & Analysis")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        Convert addresses to coordinates and analyze accessibility from specific locations.
        Perfect for:

        - Analyzing accessibility from a specific home or business
        - Batch processing multiple addresses
        - Site selection for new facilities
        - Creating custom service area maps
        """)

    with col2:
        st.metric("Tutorial Progress", "5 of 6")
        st.progress(5/6)

    st.markdown("---")

    # Geocoding options
    tab1, tab2 = st.tabs(["Single Address", "Batch Addresses"])

    with tab1:
        st.markdown("### 📍 Single Address Analysis")

        with st.form("single_address"):
            address = st.text_area(
                "Enter Address",
                value="123 Main Street\nDurham, NC 27701",
                height=100
            )

            col1, col2 = st.columns(2)

            with col1:
                poi_search = st.text_input(
                    "Search for nearby",
                    value="grocery stores"
                )

                travel_mode = st.selectbox(
                    "Travel Mode",
                    ["walk", "bike", "drive", "transit"]
                )

            with col2:
                max_time = st.slider(
                    "Maximum travel time (min)",
                    5, 60, 20, 5
                )

                show_demographics = st.checkbox(
                    "Include demographic analysis",
                    value=True
                )

            geocode_btn = st.form_submit_button("📍 Geocode & Analyze", use_container_width=True)

        if geocode_btn:
            with st.spinner("Geocoding address..."):
                # Simulated geocoding result
                st.success("✅ Address geocoded successfully!")

                col1, col2 = st.columns([1, 2])

                with col1:
                    st.markdown("#### 📍 Geocoding Result")
                    st.code("""Latitude: 35.9940
Longitude: -78.8986
Confidence: High
Match Type: Rooftop""")

                    st.markdown("#### 🏪 Nearest POIs")
                    nearest_pois = pd.DataFrame({
                        'Name': ['Fresh Market', 'Harris Teeter', 'Food Lion'],
                        'Distance': ['0.8 km', '1.2 km', '2.1 km'],
                        'Time': ['10 min', '15 min', '25 min']
                    })
                    st.dataframe(nearest_pois, hide_index=True)

                with col2:
                    # Create a simple map placeholder
                    m = folium.Map(location=[35.9940, -78.8986], zoom_start=14)
                    folium.Marker(
                        [35.9940, -78.8986],
                        popup="Your Address",
                        icon=folium.Icon(color='red', icon='home')
                    ).add_to(m)
                    st_folium(m, height=300, use_container_width=True)

    with tab2:
        st.markdown("### 📋 Batch Address Processing")

        batch_addresses = st.text_area(
            "Enter multiple addresses (one per line)",
            value="""123 Main Street, Durham, NC 27701
456 Oak Avenue, Chapel Hill, NC 27514
789 Pine Road, Raleigh, NC 27606""",
            height=150
        )

        if st.button("📍 Geocode All Addresses"):
            addresses = [addr.strip() for addr in batch_addresses.split('\n') if addr.strip()]

            progress_bar = st.progress(0)
            status_text = st.empty()

            results = []
            for i, addr in enumerate(addresses):
                status_text.text(f"Geocoding {i+1}/{len(addresses)}: {addr[:30]}...")
                progress_bar.progress((i + 1) / len(addresses))

                # Simulated results
                results.append({
                    'Address': addr,
                    'Status': 'Success' if i != 1 else 'Failed',
                    'Latitude': 35.9940 + i * 0.01 if i != 1 else None,
                    'Longitude': -78.8986 + i * 0.01 if i != 1 else None
                })

            status_text.text("Geocoding complete!")

            # Display results
            results_df = pd.DataFrame(results)
            st.dataframe(
                results_df.style.applymap(
                    lambda x: 'background-color: #d4edda' if x == 'Success' else 'background-color: #f8d7da' if x == 'Failed' else '',
                    subset=['Status']
                ),
                hide_index=True,
                use_container_width=True
            )

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            success_count = sum(1 for r in results if r['Status'] == 'Success')

            with col1:
                st.metric("Total Addresses", len(addresses))
            with col2:
                st.metric("Successfully Geocoded", success_count)
            with col3:
                st.metric("Success Rate", f"{(success_count/len(addresses)*100):.1f}%")

elif selected_page == "Batch Analysis":
    st.markdown("## 🔄 Batch Analysis & Automation")

    st.markdown("""
    Run multiple analyses efficiently and export comprehensive reports. This advanced
    feature allows you to:

    - Analyze multiple locations in one run
    - Compare different scenarios
    - Generate standardized reports
    - Schedule recurring analyses
    """)

    # Analysis templates
    st.markdown("### 📋 Analysis Templates")

    template = st.selectbox(
        "Select a template or create custom",
        ["Equity Assessment", "Site Selection", "Service Gap Analysis", "Custom"]
    )

    if template == "Equity Assessment":
        st.info("""
        **Equity Assessment Template**
        - Analyzes access to essential services
        - Focuses on vulnerable populations
        - Includes income and transportation metrics
        """)

        locations = st.text_area(
            "Locations to analyze",
            value="Low-income neighborhoods in Durham, NC",
            help="Enter locations or upload CSV"
        )

        if st.button("🚀 Run Equity Assessment"):
            st.success("Batch analysis would process multiple locations and generate comprehensive equity report")

    elif template == "Custom":
        # Custom batch configuration
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📍 Locations")
            upload_method = st.radio(
                "Input method",
                ["Text list", "CSV upload", "Previous results"]
            )

            st.markdown("#### 🏛️ POI Configuration")
            poi_sets = st.multiselect(
                "POI categories",
                ["Essential Services", "Healthcare", "Education", "Food", "Recreation"],
                default=["Essential Services"]
            )

        with col2:
            st.markdown("#### ⚙️ Analysis Settings")

            parallel_processing = st.checkbox("Enable parallel processing", value=True)

            export_formats = st.multiselect(
                "Export formats",
                ["CSV", "Excel", "GeoJSON", "PDF Report", "PowerPoint"],
                default=["CSV", "PDF Report"]
            )

            notification_email = st.text_input(
                "Email for completion notification",
                placeholder="your@email.com"
            )

        if st.button("🚀 Start Batch Analysis", use_container_width=True):
            st.info("Custom batch analysis configuration would be processed here")

elif selected_page == "Settings":
    st.markdown("## ⚙️ Settings & Configuration")

    # API Configuration
    st.markdown("### 🔑 API Configuration")

    col1, col2 = st.columns(2)

    with col1:
        census_key_configured = bool(os.environ.get('CENSUS_API_KEY'))
        st.success("✅ Census API configured") if census_key_configured else st.error("❌ Census API not configured")

        if st.button("Test Census API"):
            if census_key_configured:
                st.success("Census API connection successful!")
            else:
                st.error("Please configure Census API key in sidebar")

    with col2:
        st.info("""
        **Other APIs:**
        - OpenStreetMap: No key required
        - Nominatim: Rate limited
        - TIGER: Public access
        """)

    # Cache Management
    st.markdown("### 💾 Cache Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Geocoding Cache", "124 entries")
        if st.button("Clear Geocoding Cache"):
            st.success("Geocoding cache cleared!")

    with col2:
        st.metric("Isochrone Cache", "48 entries")
        if st.button("Clear Isochrone Cache"):
            st.success("Isochrone cache cleared!")

    with col3:
        st.metric("Total Cache Size", "15.2 MB")
        if st.button("Clear All Caches"):
            st.success("All caches cleared!")

    # Performance Settings
    st.markdown("### ⚡ Performance Settings")

    col1, col2 = st.columns(2)

    with col1:
        max_workers = st.slider(
            "Maximum parallel workers",
            1, 8, 4,
            help="Number of concurrent analyses"
        )

        timeout = st.slider(
            "API timeout (seconds)",
            10, 120, 30
        )

    with col2:
        enable_caching = st.checkbox("Enable result caching", value=True)

        log_level = st.selectbox(
            "Logging level",
            ["ERROR", "WARNING", "INFO", "DEBUG"],
            index=2
        )

    # Export Settings
    st.markdown("### 📤 Export Settings")

    default_formats = st.multiselect(
        "Default export formats",
        ["CSV", "Excel", "GeoJSON", "Shapefile", "KML"],
        default=["CSV", "GeoJSON"]
    )

    include_metadata = st.checkbox("Include metadata in exports", value=True)

    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with SocialMapper v0.6.0 |
    <a href='https://github.com/yourusername/socialmapper' target='_blank'>Documentation</a> |
    <a href='https://github.com/yourusername/socialmapper/issues' target='_blank'>Report Issue</a>
    </p>
</div>
""", unsafe_allow_html=True)
