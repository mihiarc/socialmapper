"""ZCTA Analysis Tutorial - Interactive Version.

This page mirrors the [ZCTA Analysis Tutorial](https://mihiarc.github.io/socialmapper/tutorials/zcta-analysis-tutorial/) documentation example,
demonstrating ZIP Code Tabulation Area (ZCTA) analysis for regional demographic patterns.
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from socialmapper import SocialMapperBuilder, SocialMapperClient, get_census_system
from socialmapper.api.builder import GeographicLevel

from ..config import POI_TYPES, TRAVEL_MODES

# Set up logging
logger = logging.getLogger(__name__)


def render_zcta_analysis_page():
    """Render the ZCTA Analysis tutorial page."""
    st.header("📮 ZCTA Analysis Tutorial")

    st.markdown("""
    This tutorial explores demographic analysis using ZIP Code Tabulation Areas (ZCTAs),
    which are statistical geographic units that approximate ZIP code delivery areas.
    
    **What you'll learn:**
    - 📚 What ZCTAs are and why they're useful
    - 🔍 How to fetch ZCTA boundaries and census data
    - 📊 Comparing ZCTA vs block group analysis
    - ⚡ Batch processing for large-scale analysis
    - 🗺️ Creating choropleth maps to visualize ZCTA demographics
    
    *This tutorial mirrors the documentation example: analyzing library accessibility in Wake County at the ZCTA level.*
    """)

    # Tutorial steps matching the documentation
    with st.container():
        st.info("""
        💡 **Tutorial Steps:**
        1. Understanding ZCTAs - Learn what they are and when to use them
        2. Basic Operations - Fetch ZCTAs for states and specific locations
        3. Census Data Analysis - Retrieve demographic data for ZCTAs
        4. Full Pipeline Demo - Run complete analysis with choropleth maps
        5. Compare with Block Groups - See the trade-offs in action
        """)

    # Create tabs for tutorial steps
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Understanding ZCTAs",
        "🔧 Basic Operations",
        "📊 Census Data",
        "🗺️ Full Analysis",
        "🔍 Comparison"
    ])

    with tab1:
        render_understanding_zctas()

    with tab2:
        render_basic_operations()

    with tab3:
        render_census_data_analysis()

    with tab4:
        render_full_analysis()

    with tab5:
        render_comparison_tool()


def render_understanding_zctas():
    """Step 1: Understanding ZCTAs - Educational content."""
    st.subheader("📮 Understanding ZIP Code Tabulation Areas (ZCTAs)")

    st.markdown("""
    ZCTAs are statistical areas created by the Census Bureau that approximate
    the geographic areas covered by US Postal Service ZIP codes.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **🎯 Why use ZCTAs?**
        • Familiar to most people (everyone knows ZIP codes)
        • Larger than block groups = faster processing
        • Good for regional/neighborhood-level analysis
        • Useful for business and marketing analysis
        
        **📏 Size & Coverage:**
        • Population: ~5,000-50,000 people
        • Count: ~33,000 ZCTAs nationwide
        • Updates: Every 10 years with census
        """)

    with col2:
        st.success("""
        **⚡ When to choose ZCTAs vs Block Groups:**
        
        **ZCTAs are best for:**
        • Regional analysis, marketing, service areas
        • Business market analysis
        • Mail-based service delivery
        • Faster processing needs
        
        **Block Groups are best for:**
        • Precise local analysis
        • Walkability studies
        • Environmental justice analysis
        """)

    # Visual comparison table
    st.markdown("### 📊 ZCTA vs Block Group Comparison")

    comparison_df = pd.DataFrame({
        'Aspect': ['Size', 'Precision', 'Processing', 'Familiarity', 'Use Case'],
        'Block Groups': ['~600-3000 people', 'Very High', 'Slower', 'Technical', 'Local analysis'],
        'ZCTAs': ['~5000-50000 people', 'Moderate', 'Faster', 'Everyone knows', 'Regional trends']
    })

    st.dataframe(comparison_df.set_index('Aspect'), use_container_width=True)

def render_basic_operations():
    """Step 2: Basic ZCTA Operations - Demonstrate fetching and exploring ZCTAs."""
    st.subheader("🔧 Basic ZCTA Operations")

    st.markdown("""
    Let's explore basic operations with ZCTAs using the census system.
    These operations form the foundation for more complex analyses.
    """)

    # Operation selection
    operation = st.radio(
        "Choose an operation:",
        ["Fetch ZCTAs for a state", "Find ZCTA for a specific location", "Get ZCTA download URLs"],
        horizontal=True
    )

    if operation == "Fetch ZCTAs for a state":
        render_state_zctas()
    elif operation == "Find ZCTA for a specific location":
        render_point_lookup()
    else:
        render_zcta_urls()


def render_state_zctas():
    """Fetch ZCTAs for a selected state."""
    st.markdown("### 🗺️ Fetch ZCTAs for a State")

    state_fips = {
        "Alabama": "01", "Alaska": "02", "Arizona": "04", "Arkansas": "05",
        "California": "06", "Colorado": "08", "Connecticut": "09", "Delaware": "10",
        "Florida": "12", "Georgia": "13", "Hawaii": "15", "Idaho": "16",
        "Illinois": "17", "Indiana": "18", "Iowa": "19", "Kansas": "20",
        "Kentucky": "21", "Louisiana": "22", "Maine": "23", "Maryland": "24",
        "Massachusetts": "25", "Michigan": "26", "Minnesota": "27", "Mississippi": "28",
        "Missouri": "29", "Montana": "30", "Nebraska": "31", "Nevada": "32",
        "New Hampshire": "33", "New Jersey": "34", "New Mexico": "35", "New York": "36",
        "North Carolina": "37", "North Dakota": "38", "Ohio": "39", "Oklahoma": "40",
        "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44", "South Carolina": "45",
        "South Dakota": "46", "Tennessee": "47", "Texas": "48", "Utah": "49",
        "Vermont": "50", "Virginia": "51", "Washington": "53", "West Virginia": "54",
        "Wisconsin": "55", "Wyoming": "56"
    }

    selected_state = st.selectbox(
        "Select a state to explore",
        options=list(state_fips.keys()),
        index=list(state_fips.keys()).index("North Carolina")
    )

    if st.button("Fetch ZCTAs", key="fetch_state_zctas"):
        with st.spinner(f"Fetching ZCTAs for {selected_state}..."):
            try:
                census_system = get_census_system()
                fips_code = state_fips[selected_state]

                zctas = census_system.get_zctas_for_state(fips_code)

                if not zctas.empty:
                    st.success(f"✅ Found {len(zctas)} ZCTAs in {selected_state}")

                    # Show sample ZCTAs
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total ZCTAs", len(zctas))
                    with col2:
                        st.metric("Sample ZCTAs", ", ".join(zctas.head(3)['GEOID'].astype(str)))
                    with col3:
                        total_pop = zctas['POP100'].sum() if 'POP100' in zctas.columns else "N/A"
                        st.metric("Total Population", f"{total_pop:,}" if isinstance(total_pop, (int, float)) else total_pop)

                    # Show data preview
                    with st.expander("View ZCTA Data"):
                        display_cols = ['GEOID', 'NAME', 'POP100', 'HU100', 'AREALAND']
                        available_cols = [col for col in display_cols if col in zctas.columns]
                        st.dataframe(zctas[available_cols].head(10))

                    # Show variable definitions
                    with st.expander("📖 ZCTA Variable Definitions"):
                        st.markdown("""
                        **Column Definitions:**
                        
                        - **GEOID**: Geographic identifier (5-digit ZCTA code)
                        - **ZCTA5/ZCTA5CE**: ZIP Code Tabulation Area 5-digit code
                        - **NAME**: Official ZCTA name (usually "ZCTA5 XXXXX")
                        - **POP100**: Total population count from 2020 Census
                        - **HU100**: Total housing units from 2020 Census
                        - **AREALAND**: Land area in square meters
                        - **AREAWATER**: Water area in square meters
                        - **CENTLAT**: Latitude of the ZCTA centroid
                        - **CENTLON**: Longitude of the ZCTA centroid
                        - **STATEFP**: State FIPS code
                        - **geometry**: Polygon geometry defining ZCTA boundaries
                        
                        **Area Conversions:**
                        - Square meters to square miles: divide by 2,589,988
                        - Square meters to square kilometers: divide by 1,000,000
                        - Square meters to acres: divide by 4,047
                        
                        **Notes:**
                        - ZCTAs approximate USPS ZIP code delivery areas
                        - Some ZIP codes may not have corresponding ZCTAs
                        - ZCTAs are updated every 10 years with the census
                        """)

                    # Download options
                    st.subheader("📥 Download ZCTA Data")
                    col1, col2 = st.columns(2)

                    with col1:
                        # Download as CSV (without geometry for simplicity)
                        csv_data = zctas[available_cols].to_csv(index=False)
                        st.download_button(
                            label="Download as CSV",
                            data=csv_data,
                            file_name=f"zctas_{selected_state.lower().replace(' ', '_')}.csv",
                            mime="text/csv"
                        )

                    with col2:
                        # Show total stats with area conversion
                        if 'AREALAND' in zctas.columns:
                            total_area_sq_miles = zctas['AREALAND'].sum() / 2589988
                            st.metric("Total Land Area", f"{total_area_sq_miles:,.0f} sq miles")
                else:
                    st.warning("No ZCTAs found for this state")

            except Exception as e:
                st.error(f"Error fetching ZCTAs: {e!s}")
                st.info("💡 This might be due to API limits or network issues")


def render_point_lookup():
    """Find ZCTA for a specific coordinate."""
    st.markdown("### 📍 Find ZCTA for a Location")

    col1, col2 = st.columns(2)

    with col1:
        # Pre-populate with Raleigh, NC coordinates from tutorial
        lat = st.number_input("Latitude", value=35.7796, format="%.4f")

    with col2:
        lon = st.number_input("Longitude", value=-78.6382, format="%.4f")

    if st.button("Find ZCTA", key="find_zcta_for_point"):
        with st.spinner("Looking up ZCTA..."):
            try:
                census_system = get_census_system()
                zcta_code = census_system.get_zcta_for_point(lat, lon)

                st.success(f"📍 Point ({lat}, {lon}) is in ZCTA: **{zcta_code}**")

                # Additional info
                with st.expander("ℹ️ About this ZCTA"):
                    st.markdown(f"""
                    **ZCTA {zcta_code}**
                    - This is the ZIP Code Tabulation Area containing your coordinates
                    - You can now use this ZCTA code for demographic analysis
                    - Try it in the Census Data tab!
                    """)

            except Exception as e:
                st.error(f"Error finding ZCTA: {e!s}")
                st.info("💡 Make sure the coordinates are within the United States")


def render_zcta_urls():
    """Show ZCTA data download URLs."""
    st.markdown("### 🗂️ ZCTA Data URLs")

    st.info("""
    Get direct download links for ZCTA shapefiles. These are useful for:
    - Bulk data processing
    - GIS software integration
    - Custom analysis workflows
    """)

    year = st.selectbox("Select year", [2020, 2019, 2018], index=0)

    if st.button("Get Download URLs", key="get_zcta_urls"):
        try:
            census_system = get_census_system()
            urls = census_system.get_zcta_urls(year=year)

            st.success(f"✅ Found {len(urls)} download links for {year}")

            for name, url in urls.items():
                st.markdown(f"**{name}**: [{url}]({url})")

        except Exception as e:
            st.error(f"Error getting URLs: {e!s}")


def render_census_data_analysis():
    """Step 3: ZCTA Census Data Analysis."""
    st.subheader("📊 ZCTA Census Data Analysis")

    st.markdown("""
    Fetch and analyze census demographic data for specific ZCTAs.
    This demonstrates how to retrieve key demographic variables for ZIP code areas.
    """)

    # Pre-populate with example ZCTAs from tutorial
    st.info("""
    📍 **Tutorial Example**: We'll analyze ZCTAs in the Raleigh-Charlotte area:
    - 27601, 27605, 27609 (Raleigh)
    - 28202, 28204 (Charlotte)
    """)

    # Pre-populate with tutorial example ZCTAs
    zcta_input = st.text_area(
        "Enter ZCTAs to analyze",
        value="27601, 27605, 27609, 28202, 28204",
        help="Enter 5-digit ZIP codes/ZCTAs (comma-separated or one per line)",
        height=100
    )

    # Parse input
    zctas_to_analyze = []
    if zcta_input:
        # Handle both comma-separated and line-separated
        zctas_raw = zcta_input.replace('\n', ',').split(',')
        zctas_to_analyze = [z.strip() for z in zctas_raw if z.strip()]

    if zctas_to_analyze:
        max_display = 5
        st.info(f"📍 Ready to analyze {len(zctas_to_analyze)} ZCTAs: {', '.join(zctas_to_analyze[:max_display])}{'...' if len(zctas_to_analyze) > max_display else ''}")

        # Census variable selection matching tutorial
        st.markdown("### 📊 Census Variables")

        # Use the same variables as the tutorial
        census_vars = {
            "Total Population": "B01003_001E",
            "Median Household Income": "B19013_001E",
            "Median Age": "B01002_001E",
            "Owner-Occupied Housing": "B25003_002E",
            "Renter-Occupied Housing": "B25003_003E"
        }

        st.info("""
        📊 **Selected Variables** (matching tutorial):
        - Population, Income, Age, Housing Tenure
        - Results will include calculated % Owner Occupied
        """)

        selected_vars = st.multiselect(
            "Choose variables to analyze",
            options=list(census_vars.keys()),
            default=["Total Population", "Median Household Income", "Median Age"]
        )

        if st.button("Analyze Demographics", type="primary", key="analyze_zcta_demographics"):
            if selected_vars:
                with st.spinner("Fetching census data..."):
                    try:
                        census_system = get_census_system()

                        # Get variable codes
                        var_codes = [census_vars[v] for v in selected_vars]

                        # Fetch census data
                        census_data = census_system.get_zcta_census_data(
                            geoids=zctas_to_analyze[:20],  # Limit to 20 for demo
                            variables=var_codes
                        )

                        if not census_data.empty:
                            st.success(f"✅ Retrieved {len(census_data)} data points")

                            # Transform data for display
                            analysis_results = transform_census_data(
                                census_data,
                                zctas_to_analyze[:20],
                                var_codes,
                                selected_vars
                            )

                            if analysis_results:
                                # Display results in tutorial format
                                st.markdown("### 📋 ZCTA Demographics Summary")
                                st.markdown("---")

                                # Create formatted table header
                                header = "| ZCTA | Population | Med Income | % Owner Occ |"
                                separator = "|------|------------|------------|-------------|"

                                # Build table rows
                                rows = []
                                for result in analysis_results:
                                    zcta = result.get('ZCTA', 'N/A')
                                    pop = f"{result.get('Total Population', 0):,}" if result.get('Total Population') else 'N/A'
                                    income = f"${result.get('Median Household Income', 0):,}" if result.get('Median Household Income') else 'N/A'
                                    owner_pct = f"{result.get('% Owner Occupied', 0):.1f}%" if result.get('% Owner Occupied') else 'N/A'

                                    rows.append(f"| {zcta} | {pop} | {income} | {owner_pct} |")

                                # Display formatted table
                                table_content = "\n".join([header, separator] + rows)
                                st.markdown(table_content)
                                st.markdown("---")

                                # Also create DataFrame for download
                                df_results = pd.DataFrame(analysis_results)

                                # Download option
                                csv = df_results.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Results as CSV",
                                    data=csv,
                                    file_name="zcta_demographics.csv",
                                    mime="text/csv"
                                )
                        else:
                            st.warning("No census data retrieved. This might be due to API limits.")

                    except Exception as e:
                        st.error(f"Error analyzing demographics: {e!s}")
            else:
                st.warning("Please select at least one census variable")


def render_full_analysis():
    """Step 4: Full SocialMapper Pipeline with ZCTA Analysis."""
    st.subheader("🗺️ Full ZCTA Analysis with Choropleth Maps")

    st.markdown("""
    This demonstrates the full SocialMapper pipeline at the ZCTA level,
    including automated choropleth map generation. We'll replicate the tutorial
    example: analyzing library accessibility in Wake County.
    """)

    # Tutorial replication notice
    st.success("""
    🎯 **Tutorial Replication**: This analysis matches the example in
    `examples/tutorials/04_zipcode_analysis.py`, using the same parameters
    and generating the same types of outputs.
    """)

    # Check for previous results in session state
    if 'zcta_analysis_results' in st.session_state and st.session_state.zcta_analysis_results:
        with st.expander("📋 Previous Analysis Results", expanded=False):
            st.markdown("**Click to view and download results from previous analyses:**")

            for key, data in st.session_state.zcta_analysis_results.items():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.text(f"📍 {data['location']} - {data['poi_type']} ({data['travel_time']} min {data['travel_mode']})")

                with col2:
                    st.text(f"🕐 {data['timestamp'].strftime('%H:%M')}")

                with col3:
                    if st.button("View", key=f"view_{key}"):
                        st.session_state.current_zcta_result = data['result']
                        st.session_state.show_previous_result = True

    # Location input
    col1, col2 = st.columns(2)

    with col1:
        location = st.text_input(
            "Location (City or County)",
            value="Wake County",
            help="Enter a city or county name"
        )

    with col2:
        state = st.text_input(
            "State",
            value="North Carolina",
            help="Enter the full state name"
        )

    # POI selection
    poi_category = st.selectbox(
        "POI Category",
        options=list(POI_TYPES.keys()),
        format_func=lambda x: x.title()
    )

    poi_type = st.selectbox(
        "POI Type",
        options=POI_TYPES[poi_category],
        format_func=lambda x: x.replace('_', ' ').title()
    )

    # Analysis parameters
    col1, col2, col3 = st.columns(3)

    with col1:
        travel_time = st.slider(
            "Travel Time (minutes)",
            min_value=5,
            max_value=30,
            value=15,
            step=5
        )

    with col2:
        travel_mode = st.selectbox(
            "Travel Mode",
            options=list(TRAVEL_MODES.keys()),
            format_func=lambda x: f"{TRAVEL_MODES[x]['icon']} {TRAVEL_MODES[x]['name']}",
            help="Walking includes all legally walkable paths (even roads without sidewalks). Biking respects one-way streets. Driving follows all traffic rules."
        )

    with col3:
        enable_maps = st.checkbox("Generate choropleth maps", value=True)

    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        max_pois = st.slider(
            "Maximum POIs to analyze",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Limiting POIs speeds up ZCTA analysis. Increase for more comprehensive coverage."
        )

    # Census variables for choropleth
    if enable_maps:
        st.subheader("Map Variables")
        map_variables = st.multiselect(
            "Select variables for choropleth maps",
            options=["total_population", "median_household_income", "median_age"],
            default=["total_population", "median_household_income"],
            help="These variables will be visualized on the choropleth maps"
        )
    else:
        map_variables = []

    # Run analysis
    if st.button("Run ZCTA Analysis", type="primary", key="run_zcta_accessibility"):
        # Add warning about processing time
        with st.container():
            st.info("""
            ⏱️ **Note**: ZCTA analysis can take 30-60 seconds as it:
            - Queries OpenStreetMap for POIs
            - Fetches ZIP code boundaries from Census
            - Calculates travel time areas
            - Retrieves demographic data
            
            Please be patient while the analysis completes...
            """)

        with st.spinner("🔍 Finding POIs and fetching ZCTA boundaries... (this may take a minute)"):
            try:
                with SocialMapperClient() as client:
                    # Build configuration
                    config = (SocialMapperBuilder()
                        .with_location(location, state)
                        .with_osm_pois(poi_category, poi_type)
                        .with_travel_time(travel_time)
                        .with_travel_mode(travel_mode)
                        .with_geographic_level(GeographicLevel.ZCTA)  # Pass the enum, not string
                        .with_census_variables(*map_variables)
                        .with_exports(csv=True, maps=enable_maps, isochrones=False)
                        .limit_pois(max_pois)  # Limit POIs for faster ZCTA processing
                        .build()
                    )

                    # Run analysis
                    result = client.run_analysis(config)

                    if result.is_err():
                        error = result.unwrap_err()
                        st.error(f"❌ Analysis failed: {error.message}")
                        return

                    # Get successful result
                    analysis_result = result.unwrap()

                    # Display results
                    st.success("✅ ZCTA analysis complete!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("POIs Found", analysis_result.poi_count)
                    with col2:
                        st.metric("ZCTAs Analyzed", analysis_result.census_units_analyzed)
                    with col3:
                        travel_desc = f"{travel_time} min {TRAVEL_MODES[travel_mode]['name'].lower()}"
                        st.metric("Travel Time", travel_desc)

                    # Store results in session state
                    if 'zcta_analysis_results' not in st.session_state:
                        st.session_state.zcta_analysis_results = {}

                    analysis_key = f"{location}_{poi_type}_{travel_mode}_{travel_time}"
                    st.session_state.zcta_analysis_results[analysis_key] = {
                        'result': analysis_result,
                        'location': location,
                        'poi_type': poi_type,
                        'travel_mode': travel_mode,
                        'travel_time': travel_time,
                        'timestamp': pd.Timestamp.now()
                    }

                    # Show generated files with download links using fragment
                    @st.fragment
                    def show_download_section():
                        if hasattr(analysis_result, 'files_generated') and analysis_result.files_generated:
                            st.subheader("📁 Download Results")

                            # Check if files_generated is the new structure from IOManager
                            if isinstance(analysis_result.files_generated, dict) and any(isinstance(v, list) for v in analysis_result.files_generated.values()):
                                # New structure with categories
                                for category, files in analysis_result.files_generated.items():
                                    if category == 'maps':  # Skip maps - handled separately
                                        continue

                                    if files:  # Only show if there are files
                                        st.markdown(f"#### 📁 {category.replace('_', ' ').title()}")
                                        for file_info in files:
                                            file_path = Path(file_info['path'])
                                            if file_path.exists():
                                                with open(file_path, 'rb') as f:
                                                    file_data = f.read()

                                                # Determine MIME type
                                                mime_types = {
                                                    '.csv': 'text/csv',
                                                    '.parquet': 'application/octet-stream',
                                                    '.geoparquet': 'application/octet-stream',
                                                    '.geojson': 'application/geo+json',
                                                    '.json': 'application/json',
                                                    '.png': 'image/png',
                                                    '.html': 'text/html'
                                                }

                                                file_ext = file_path.suffix.lower()
                                                mime_type = mime_types.get(file_ext, 'application/octet-stream')

                                                # Create user-friendly label based on file type
                                                file_type_labels = {
                                                    'csv': '📊 Data',
                                                    'isochrone': '🗺️ Travel Areas',
                                                    'geoparquet': '🗺️ Geographic Data',
                                                    'geojson': '🗺️ GeoJSON',
                                                    'json': '📄 Summary'
                                                }

                                                type_label = file_type_labels.get(file_info.get('type', ''), '📎 File')
                                                label = f"{type_label} - {file_info['filename']}"

                                                st.download_button(
                                                    label=f"Download {label}",
                                                    data=file_data,
                                                    file_name=file_info['filename'],
                                                    mime=mime_type,
                                                    key=f"download_{category}_{file_info['filename']}_{analysis_key}"
                                                )
                            else:
                                # Legacy structure for backward compatibility
                                for file_type, file_path in analysis_result.files_generated.items():
                                    file_path_obj = Path(file_path)

                                    # Handle directories (like 'maps') separately
                                    if file_path_obj.exists() and file_path_obj.is_dir():
                                        if file_type == 'maps':
                                            # Maps are handled in the separate maps section below
                                            continue
                                        else:
                                            # For other directories, show files inside
                                            st.markdown(f"#### 📁 {file_type.replace('_', ' ').title()}")
                                            dir_files = list(file_path_obj.glob("*"))
                                            for dir_file in dir_files:
                                                if dir_file.is_file():
                                                    with open(dir_file, 'rb') as f:
                                                        file_data = f.read()
                                                    st.download_button(
                                                        label=f"Download {dir_file.name}",
                                                        data=file_data,
                                                        file_name=dir_file.name,
                                                        mime='application/octet-stream',
                                                        key=f"download_{file_type}_{dir_file.name}_{analysis_key}"
                                                    )

                                    # Skip directories and only process files
                                    elif file_path_obj.exists() and file_path_obj.is_file():
                                        # Read file content for download
                                        with open(file_path_obj, 'rb') as f:
                                            file_data = f.read()

                                        # Determine MIME type
                                        mime_types = {
                                            '.csv': 'text/csv',
                                            '.parquet': 'application/octet-stream',
                                            '.geojson': 'application/geo+json',
                                            '.json': 'application/json',
                                            '.png': 'image/png',
                                            '.html': 'text/html'
                                        }

                                        file_ext = file_path_obj.suffix.lower()
                                        mime_type = mime_types.get(file_ext, 'application/octet-stream')

                                        # Create user-friendly label
                                        file_labels = {
                                            'census_data': '📊 Census Data (CSV)',
                                            'poi_data': '📍 POI Locations (CSV)',
                                            'isochrones': '🗺️ Travel Areas (GeoJSON)',
                                            'combined_data': '📋 Complete Dataset (Parquet)',
                                            'summary': '📄 Analysis Summary (JSON)'
                                        }

                                        label = file_labels.get(file_type, f"📎 {file_type.replace('_', ' ').title()}")

                                        # Create download button
                                        st.download_button(
                                            label=f"Download {label}",
                                            data=file_data,
                                            file_name=file_path_obj.name,
                                            mime=mime_type,
                                            key=f"download_{file_type}_{analysis_key}"
                                        )

                    # Call the fragment function
                    show_download_section()

                    # Check for maps
                    @st.fragment
                    def show_maps_section():
                        if enable_maps:
                            map_files = []

                            # Check if using new IOManager structure
                            if hasattr(analysis_result, 'files_generated') and isinstance(analysis_result.files_generated, dict):
                                if 'maps' in analysis_result.files_generated and isinstance(analysis_result.files_generated['maps'], list):
                                    # New structure - extract map file info
                                    for file_info in analysis_result.files_generated['maps']:
                                        if 'zcta' in file_info['filename'] or travel_mode in file_info.get('travel_mode', ''):
                                            map_path = Path(file_info['path'])
                                            if map_path.exists():
                                                map_files.append(map_path)
                                # Legacy structure - check if maps is a directory path
                                elif 'maps' in analysis_result.files_generated:
                                    map_dir = Path(analysis_result.files_generated['maps'])
                                    if map_dir.exists() and map_dir.is_dir():
                                        # Look for maps with current travel mode in filename
                                        map_files = list(map_dir.glob(f"*{travel_mode}*.png"))
                                        if not map_files:  # Fallback to zcta maps
                                            map_files = list(map_dir.glob("*zcta*.png"))

                            # Fallback to default directory if no maps found
                            if not map_files:
                                map_dir = Path("output/maps")
                                if map_dir.exists() and map_dir.is_dir():
                                    map_files = list(map_dir.glob(f"*{travel_mode}*.png"))
                                    if not map_files:
                                        map_files = list(map_dir.glob("*zcta*.png"))

                            if map_files:
                                st.subheader("🗺️ Generated Choropleth Maps")
                                st.info("""
                                ZCTA choropleth maps visualize:
                                - Population density by ZIP code area
                                - Income distribution patterns
                                - Travel distance to nearest POIs
                                - Accessibility coverage areas
                                """)

                                # Display maps in columns
                                for i, map_file in enumerate(sorted(map_files)):
                                    with st.expander(f"📍 {map_file.stem.replace('_', ' ').title()}", expanded=True):
                                        # Display the map image
                                        st.image(str(map_file), use_container_width=True)

                                        # Add download button
                                        with open(map_file, 'rb') as f:
                                            map_data = f.read()

                                        st.download_button(
                                            label=f"💾 Download {map_file.name}",
                                            data=map_data,
                                            file_name=map_file.name,
                                            mime="image/png",
                                            key=f"download_map_{i}_{analysis_key}"
                                        )

                    # Call the fragment function
                    show_maps_section()

                    # Store in session state for comparison
                    if 'zcta_results' not in st.session_state:
                        st.session_state.zcta_results = {}

                    analysis_key = f"{location}_{poi_type}_{travel_mode}"
                    st.session_state.zcta_results[analysis_key] = {
                        'result': analysis_result,
                        'params': {
                            'location': location,
                            'poi_type': poi_type,
                            'travel_time': travel_time,
                            'travel_mode': travel_mode
                        }
                    }

            except Exception as e:
                st.error(f"❌ Unexpected error: {e!s}")
                st.info("💡 Check your internet connection and Census API key")


def render_comparison_tool():
    """Render ZCTA vs Block Group comparison tool."""
    st.subheader("🔍 ZCTA vs Block Group Comparison")

    st.markdown("""
    Compare the same analysis using ZCTAs versus block groups to understand the 
    trade-offs between speed and precision.
    """)

    # Comparison table
    comparison_data = {
        "Aspect": ["Population Size", "Geographic Units", "Processing Speed", "Precision", "Best For"],
        "Block Groups": ["600-3,000 people", "~220,000 nationwide", "Slower", "Very High", "Local analysis"],
        "ZCTAs": ["5,000-50,000 people", "~33,000 nationwide", "Faster", "Moderate", "Regional analysis"]
    }

    df_comparison = pd.DataFrame(comparison_data)
    st.table(df_comparison.set_index("Aspect"))

    # Interactive comparison
    st.subheader("Run Comparative Analysis")

    col1, col2 = st.columns(2)

    with col1:
        comp_location = st.text_input(
            "Location for comparison",
            value="Durham",
            key="comp_location"
        )
        comp_state = st.text_input(
            "State",
            value="North Carolina",
            key="comp_state"
        )

    with col2:
        comp_poi = st.selectbox(
            "POI Type",
            options=["library", "hospital", "school", "park"],
            key="comp_poi"
        )
        comp_time = st.slider(
            "Travel time (min)",
            5, 30, 15,
            key="comp_time"
        )

    if st.button("🎯 Compare Geographic Levels", type="primary", key="run_comparison"):
        st.markdown("### 📊 Comparison Results")

        # Create placeholders for timing
        timing_placeholder = st.empty()

        # Create two columns for results
        col_zcta, col_bg = st.columns(2)

        # Track timing
        results = {}

        with col_zcta:
            st.markdown("#### 🏦 ZCTA Analysis")
            with st.spinner("Running ZCTA analysis..."):
                zcta_result = run_comparison_analysis(
                    comp_location, comp_state, comp_poi, comp_time,
                    GeographicLevel.ZCTA, "ZCTA"
                )
                if zcta_result:
                    results['zcta'] = zcta_result

        with col_bg:
            st.markdown("#### 📍 Block Group Analysis")
            with st.spinner("Running Block Group analysis..."):
                bg_result = run_comparison_analysis(
                    comp_location, comp_state, comp_poi, comp_time,
                    GeographicLevel.BLOCK_GROUP, "Block Group"
                )
                if bg_result:
                    results['bg'] = bg_result

        # Show timing comparison if both succeeded
        COMPARISON_COUNT = 2
        if len(results) == COMPARISON_COUNT:
            with timing_placeholder.container():
                st.success("🏆 **Performance Comparison**")
                speed_ratio = results['bg']['time'] / results['zcta']['time']
                st.metric(
                    "Speed Improvement",
                    f"{speed_ratio:.1f}x faster",
                    help="ZCTA analysis compared to block group analysis"
                )


def run_comparison_analysis(location, state, poi_type, travel_time, geo_level, label):
    """Run analysis for comparison with specified geographic level."""
    try:
        import time
        start_time = time.time()

        with SocialMapperClient() as client:
            config = (SocialMapperBuilder()
                .with_location(location, state)
                .with_osm_pois("amenity", poi_type)
                .with_travel_time(travel_time)
                .with_geographic_level(geo_level)
                .with_census_variables("total_population")
                .build()
            )

            result = client.run_analysis(config)

            elapsed = time.time() - start_time

            if result.is_ok():
                analysis = result.unwrap()
                st.success(f"✅ {label} Complete")
                st.metric("Processing Time", f"{elapsed:.1f} seconds")
                st.metric("Geographic Units", analysis.census_units_analyzed)
                st.metric("POIs Found", analysis.poi_count)
            else:
                st.error(f"❌ {label} failed: {result.unwrap_err().message}")

    except Exception as e:
        st.error(f"Error in {label} analysis: {e!s}")


def transform_census_data(census_data, zctas, var_codes, var_names):
    """Transform census data into tutorial format with calculated metrics."""
    results = []

    # Process each ZCTA like the tutorial
    for zcta in zctas:
        zcta_data = census_data[census_data['GEOID'] == zcta]

        if not zcta_data.empty:
            # Initialize data dict
            data_dict = {'ZCTA': zcta}

            # Extract values for each variable (matching tutorial logic)
            for _, row in zcta_data.iterrows():
                var_code = row['variable_code']
                value = row['value']

                if var_code == 'B01003_001E':
                    data_dict['Total Population'] = int(value) if value else 0
                elif var_code == 'B19013_001E':
                    data_dict['Median Household Income'] = int(value) if value else 0
                elif var_code == 'B25003_002E':
                    data_dict['Owner-Occupied Housing'] = int(value) if value else 0
                elif var_code == 'B25003_003E':
                    data_dict['Renter-Occupied Housing'] = int(value) if value else 0

            # Calculate % Owner Occupied (matching tutorial)
            owner = data_dict.get('Owner-Occupied Housing', 0)
            renter = data_dict.get('Renter-Occupied Housing', 0)
            total_occupied = owner + renter

            if total_occupied > 0:
                data_dict['% Owner Occupied'] = round((owner / total_occupied) * 100, 1)
            else:
                data_dict['% Owner Occupied'] = None

            results.append(data_dict)

    return results
