"""ZCTA Analysis page for the Streamlit application."""

import pandas as pd
import streamlit as st
from pathlib import Path

from socialmapper import SocialMapperBuilder, SocialMapperClient, get_census_system
from socialmapper.api.builder import GeographicLevel
from socialmapper.api.result_types import Ok, Err

from ..components.maps import create_folium_map, create_poi_map
from ..config import POI_TYPES, TRAVEL_MODES


def render_zcta_analysis_page():
    """Render the ZCTA Analysis tutorial page."""
    st.header("📮 ZIP Code Analysis (ZCTA)")

    st.markdown("""
    Analyze demographics and accessibility using ZIP Code Tabulation Areas (ZCTAs) - 
    statistical areas that approximate ZIP code boundaries. Perfect for regional analysis
    and business planning.
    
    **Why use ZCTAs?**
    - 🎯 Familiar to everyone (based on ZIP codes)
    - ⚡ Faster processing (fewer units than block groups)
    - 📊 Great for regional/business analysis
    - 🗺️ Clear choropleth visualizations
    """)

    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs([
        "ZCTA Overview", 
        "Demographic Analysis",
        "Accessibility Analysis",
        "Comparison Tool"
    ])

    with tab1:
        render_zcta_overview()

    with tab2:
        render_demographic_analysis()

    with tab3:
        render_accessibility_analysis()

    with tab4:
        render_comparison_tool()


def render_zcta_overview():
    """Render ZCTA overview and educational content."""
    st.subheader("Understanding ZCTAs")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **What are ZCTAs?**
        
        ZIP Code Tabulation Areas are statistical geographic units created by the 
        U.S. Census Bureau that approximate USPS ZIP code delivery areas.
        
        **Key Facts:**
        - Cover 5,000-50,000 people
        - Updated every 10 years
        - ~33,000 ZCTAs nationwide
        """)

    with col2:
        st.success("""
        **Best Use Cases:**
        
        ✅ Business market analysis
        ✅ Service area planning
        ✅ Regional demographic trends
        ✅ Mail-based outreach
        ✅ Franchise territory planning
        """)

    # State lookup demo
    st.subheader("🔍 Explore ZCTAs by State")
    
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
                st.error(f"Error fetching ZCTAs: {str(e)}")
                st.info("💡 This might be due to API limits or network issues")


def render_demographic_analysis():
    """Render ZCTA demographic analysis section."""
    st.subheader("📊 ZCTA Demographic Analysis")

    st.markdown("""
    Analyze demographic data for specific ZCTAs. This is useful for:
    - Market analysis for business planning
    - Understanding regional demographic patterns
    - Comparing multiple ZIP code areas
    """)

    # Input method selection
    input_method = st.radio(
        "How would you like to specify ZCTAs?",
        ["Enter ZCTAs manually", "Upload CSV file"],
        horizontal=True
    )

    zctas_to_analyze = []

    if input_method == "Enter ZCTAs manually":
        zcta_input = st.text_area(
            "Enter ZCTAs (one per line or comma-separated)",
            value="27601,27605,27609",
            help="Enter 5-digit ZIP codes/ZCTAs"
        )
        
        # Parse input
        if zcta_input:
            # Handle both comma-separated and line-separated
            zctas_raw = zcta_input.replace('\n', ',').split(',')
            zctas_to_analyze = [z.strip() for z in zctas_raw if z.strip()]
    
    else:  # Upload CSV
        uploaded_file = st.file_uploader(
            "Upload CSV with ZCTAs",
            type="csv",
            help="CSV should have a 'zcta' or 'zip' column"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                # Look for ZCTA column
                zcta_col = None
                for col in ['zcta', 'ZCTA', 'zip', 'ZIP', 'zipcode', 'ZIPCODE']:
                    if col in df.columns:
                        zcta_col = col
                        break
                
                if zcta_col:
                    zctas_to_analyze = df[zcta_col].astype(str).str.strip().tolist()
                    st.success(f"✅ Loaded {len(zctas_to_analyze)} ZCTAs from file")
                else:
                    st.error("CSV must contain a 'zcta' or 'zip' column")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    if zctas_to_analyze:
        st.info(f"📍 Ready to analyze {len(zctas_to_analyze)} ZCTAs: {', '.join(zctas_to_analyze[:5])}{'...' if len(zctas_to_analyze) > 5 else ''}")

        # Census variable selection
        st.subheader("Select Census Variables")
        
        census_vars = {
            "Total Population": "B01003_001E",
            "Median Household Income": "B19013_001E",
            "Median Age": "B01002_001E",
            "Owner-Occupied Housing": "B25003_002E",
            "Renter-Occupied Housing": "B25003_003E",
            "Bachelor's Degree or Higher": "B15003_022E",
            "Population in Poverty": "B17001_002E",
            "Median Home Value": "B25077_001E"
        }
        
        # Show variable descriptions
        with st.expander("📊 Census Variable Descriptions"):
            st.markdown("""
            **Available Variables:**
            
            - **Total Population** (B01003_001E): Total count of all people living in the ZCTA
            - **Median Household Income** (B19013_001E): The middle value of all household incomes in the ZCTA (half earn more, half earn less)
            - **Median Age** (B01002_001E): The middle age of all residents (half are older, half are younger)
            - **Owner-Occupied Housing** (B25003_002E): Number of housing units occupied by the owner
            - **Renter-Occupied Housing** (B25003_003E): Number of housing units occupied by renters
            - **Bachelor's Degree or Higher** (B15003_022E): Population 25+ with at least a bachelor's degree
            - **Population in Poverty** (B17001_002E): Number of people living below the federal poverty line
            - **Median Home Value** (B25077_001E): The middle value of owner-occupied homes
            
            **Data Source:** American Community Survey (ACS) 5-Year Estimates
            
            **Notes:**
            - Income and home values are in dollars
            - Some ZCTAs may have missing data due to small populations
            - Margin of error information available in ACS documentation
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
                                # Display results
                                df_results = pd.DataFrame(analysis_results)
                                
                                # Format numeric columns
                                for col in df_results.columns:
                                    if col != 'ZCTA' and df_results[col].dtype in ['int64', 'float64']:
                                        if 'Income' in col or 'Value' in col:
                                            df_results[col] = df_results[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
                                        elif 'Population' in col or 'Housing' in col:
                                            df_results[col] = df_results[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
                                
                                st.dataframe(df_results, use_container_width=True)
                                
                                # Download option
                                csv = df_results.to_csv(index=False)
                                st.download_button(
                                    label="Download Results as CSV",
                                    data=csv,
                                    file_name="zcta_demographics.csv",
                                    mime="text/csv"
                                )
                        else:
                            st.warning("No census data retrieved. This might be due to API limits.")
                            
                    except Exception as e:
                        st.error(f"Error analyzing demographics: {str(e)}")
            else:
                st.warning("Please select at least one census variable")


def render_accessibility_analysis():
    """Render ZCTA-level accessibility analysis."""
    st.subheader("🗺️ ZCTA Accessibility Analysis")

    st.markdown("""
    Analyze accessibility to points of interest at the ZCTA level. This creates
    choropleth maps showing which ZIP code areas have the best access to essential services.
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
                                else:
                                    # Legacy structure - check if maps is a directory path
                                    if 'maps' in analysis_result.files_generated:
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
                st.error(f"❌ Unexpected error: {str(e)}")
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

    if st.button("Compare Geographic Levels", type="primary"):
        # Create two columns for results
        col_zcta, col_bg = st.columns(2)
        
        with col_zcta:
            st.info("🏛️ **ZCTA Analysis**")
            with st.spinner("Running ZCTA analysis..."):
                run_comparison_analysis(
                    comp_location, comp_state, comp_poi, comp_time,
                    GeographicLevel.ZCTA, "ZCTA"
                )
        
        with col_bg:
            st.info("📍 **Block Group Analysis**")
            with st.spinner("Running Block Group analysis..."):
                run_comparison_analysis(
                    comp_location, comp_state, comp_poi, comp_time,
                    GeographicLevel.BLOCK_GROUP, "Block Group"
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
        st.error(f"Error in {label} analysis: {str(e)}")


def transform_census_data(census_data, zctas, var_codes, var_names):
    """Transform census data into a format suitable for display."""
    results = []
    
    # Create mapping of var codes to names
    var_map = dict(zip(var_codes, var_names))
    
    for zcta in zctas:
        zcta_data = census_data[census_data['GEOID'] == zcta]
        
        if not zcta_data.empty:
            row = {'ZCTA': zcta}
            
            for _, data in zcta_data.iterrows():
                var_code = data['variable_code']
                value = data['value']
                
                if var_code in var_map:
                    var_name = var_map[var_code]
                    row[var_name] = float(value) if value else None
            
            # Calculate any derived metrics
            if 'Owner-Occupied Housing' in row and 'Renter-Occupied Housing' in row:
                owner = row.get('Owner-Occupied Housing', 0) or 0
                renter = row.get('Renter-Occupied Housing', 0) or 0
                total = owner + renter
                if total > 0:
                    row['% Owner Occupied'] = round((owner / total) * 100, 1)
            
            results.append(row)
    
    return results
