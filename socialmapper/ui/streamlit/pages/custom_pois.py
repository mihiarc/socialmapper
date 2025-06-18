"""Custom POIs page for the Streamlit application."""

import logging
import tempfile
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.ui.streamlit.components.maps import create_isochrone_map
from socialmapper.ui.streamlit.config import CENSUS_VARIABLES, DEFAULT_CENSUS_VARS, TRAVEL_MODES
from socialmapper.ui.streamlit.utils import format_number

logger = logging.getLogger(__name__)


def render_custom_pois_page():
    """Render the Custom POIs tutorial page."""
    st.header("Custom Points of Interest")

    st.markdown("""
    This tutorial demonstrates how to analyze accessibility for your own custom locations, 
    such as specific addresses, facilities, or points of interest not available in OpenStreetMap.
    
    **What you'll learn:**
    - 📤 Upload custom location data via CSV
    - 🗺️ Visualize custom points on a map
    - 🔍 Analyze accessibility from these locations
    - 📊 Compare multiple custom locations
    """)

    # Initialize session state for this page
    if 'custom_poi_data' not in st.session_state:
        st.session_state.custom_poi_data = None
    if 'custom_analysis_results' not in st.session_state:
        st.session_state.custom_analysis_results = None

    # File upload section
    st.subheader("Upload Custom Locations")

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="CSV should have columns: name, lat (or latitude), lon (or longitude)"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            # Normalize column names - handle different variations
            column_mapping = {
                'latitude': 'lat',
                'longitude': 'lon',
                'long': 'lon',
                'lng': 'lon'
            }
            df.columns = [column_mapping.get(col.lower(), col.lower()) for col in df.columns]

            # Validate columns
            required_cols = ['name', 'lat', 'lon']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if not missing_cols:
                # Clean data - remove any rows with missing coordinates
                df = df.dropna(subset=['lat', 'lon'])

                # Validate coordinate ranges
                invalid_coords = df[
                    (df['lat'] < -90) | (df['lat'] > 90) |
                    (df['lon'] < -180) | (df['lon'] > 180)
                ]

                if len(invalid_coords) > 0:
                    st.error(f"Found {len(invalid_coords)} rows with invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180.")
                    st.dataframe(invalid_coords)
                    return

                st.success(f"✅ Loaded {len(df)} valid locations")
                st.session_state.custom_poi_data = df

                # Preview data
                st.subheader("Location Preview")
                st.dataframe(df.head(10))

                # Map preview
                with st.expander("📍 Preview Locations on Map", expanded=True):
                    center_lat = df['lat'].mean()
                    center_lon = df['lon'].mean()

                    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

                    # Add markers for each POI
                    for idx, row in df.iterrows():
                        folium.Marker(
                            location=[row['lat'], row['lon']],
                            popup=row['name'],
                            tooltip=row['name'],
                            icon=folium.Icon(color='red', icon='info-sign')
                        ).add_to(m)

                    # Fit bounds to show all markers
                    sw = [df['lat'].min(), df['lon'].min()]
                    ne = [df['lat'].max(), df['lon'].max()]
                    m.fit_bounds([sw, ne])

                    st_folium(m, height=400, returned_objects=[])

                # Analysis configuration
                st.subheader("Configure Analysis")

                with st.form("custom_analysis"):
                    col1, col2 = st.columns(2)

                    with col1:
                        travel_time = st.slider(
                            "Travel Time (minutes)",
                            min_value=5,
                            max_value=30,
                            value=10,
                            help="How far can people travel from these locations?"
                        )

                        travel_mode = st.selectbox(
                            "Travel Mode",
                            options=list(TRAVEL_MODES.keys()),
                            format_func=lambda x: f"{TRAVEL_MODES[x]['icon']} {TRAVEL_MODES[x]['name']}"
                        )

                    with col2:
                        # Census variable selection
                        st.markdown("**Select Census Variables:**")
                        selected_vars = []
                        for var_code, var_name in CENSUS_VARIABLES.items():
                            if st.checkbox(
                                var_name,
                                value=var_code in DEFAULT_CENSUS_VARS,
                                key=f"custom_census_{var_code}"
                            ):
                                selected_vars.append(var_code)

                    # Add export options
                    st.markdown("**Export Options:**")
                    col3, col4 = st.columns(2)
                    with col3:
                        export_csv = st.checkbox("Export CSV", value=True)
                        export_maps = st.checkbox("Generate Maps", value=True)
                    with col4:
                        export_isochrones = st.checkbox("Export Isochrones", value=False)

                    submitted = st.form_submit_button("🚀 Run Analysis", type="primary")

                    if submitted:
                        if not selected_vars:
                            st.error("Please select at least one census variable")
                        else:
                            run_custom_poi_analysis(
                                df, travel_time, travel_mode, selected_vars,
                                export_csv, export_maps, export_isochrones
                            )
            else:
                st.error(f"❌ CSV must contain columns: {', '.join(required_cols)}")
                st.error(f"Found columns: {', '.join(df.columns)}")
                st.info("💡 Tip: Column names are case-insensitive. You can use 'latitude/longitude' or 'lat/lon'")

        except Exception as e:
            st.error(f"Error reading file: {e!s}")
            logger.exception("Error reading custom POI file")

    # Show results if available
    if st.session_state.custom_analysis_results:
        display_custom_analysis_results()

    # Example template
    with st.expander("📋 Download Example Template"):
        example_df = pd.DataFrame({
            'name': ['Central Library', 'City Park', 'Community Center'],
            'lat': [35.7796, 35.7821, 35.7754],
            'lon': [-78.6382, -78.6589, -78.6434],
            'type': ['library', 'park', 'community_center'],
            'address': ['300 N Salisbury St', '520 E Whitaker Mill Rd', '108 E Morgan St']
        })

        csv = example_df.to_csv(index=False)
        st.download_button(
            label="Download Template CSV",
            data=csv,
            file_name="custom_locations_template.csv",
            mime="text/csv"
        )

        st.info("""
        💡 **CSV Format Tips:**
        - Required columns: `name`, `lat` (or `latitude`), `lon` (or `longitude`)
        - Optional columns: `type`, `address`, `description`
        - Coordinates should be in decimal degrees (e.g., 35.7796, -78.6382)
        - For US Census data, ensure coordinates are within the United States
        """)


def run_custom_poi_analysis(df: pd.DataFrame, travel_time: int, travel_mode: str,
                           census_vars: list[str], export_csv: bool, export_maps: bool,
                           export_isochrones: bool):
    """Run analysis on custom POI data."""
    try:
        # Create a temporary file to store the custom POI data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df.to_csv(tmp_file, index=False)
            temp_csv_path = tmp_file.name

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Initializing analysis...")
        progress_bar.progress(10)

        # Run analysis using SocialMapperClient
        with SocialMapperClient() as client:
            # Build configuration
            config = (SocialMapperBuilder()
                .with_custom_pois(temp_csv_path)
                .with_travel_time(travel_time)
                .with_travel_mode(travel_mode)
                .with_census_variables(*[k for k, v in CENSUS_VARIABLES.items() if k in census_vars])
                .with_exports(
                    csv=export_csv,
                    maps=export_maps,
                    isochrones=export_isochrones
                )
                .build()
            )

            status_text.text(f"Analyzing {len(df)} custom locations...")
            progress_bar.progress(30)

            # Execute analysis
            result = client.run_analysis(config)

            if result.is_ok():
                status_text.text("Processing results...")
                progress_bar.progress(80)

                analysis_result = result.unwrap()
                st.session_state.custom_analysis_results = {
                    'result': analysis_result,
                    'poi_data': df,
                    'travel_time': travel_time,
                    'travel_mode': travel_mode,
                    'census_vars': census_vars
                }

                progress_bar.progress(100)
                status_text.text("Analysis complete!")
                st.success("✅ Analysis completed successfully!")
                st.rerun()
            else:
                error = result.unwrap_err()
                st.error(f"❌ Analysis failed: {error.message}")
                logger.error(f"Custom POI analysis error: {error}")

                # Provide helpful error messages
                if "census" in str(error.message).lower():
                    st.info("💡 Tip: Ensure your coordinates are within the United States for census data integration.")
                elif "coordinate" in str(error.message).lower():
                    st.info("💡 Tip: Check that all coordinates are valid decimal degrees.")

                progress_bar.progress(0)
                status_text.text("")

        # Clean up temporary file
        Path(temp_csv_path).unlink(missing_ok=True)

    except Exception as e:
        st.error(f"An error occurred: {e!s}")
        logger.exception("Error during custom POI analysis")
        if 'progress_bar' in locals():
            progress_bar.progress(0)
        if 'status_text' in locals():
            status_text.text("")


def display_custom_analysis_results():
    """Display the results of custom POI analysis."""
    results_data = st.session_state.custom_analysis_results
    result = results_data['result']
    poi_data = results_data['poi_data']
    travel_time = results_data['travel_time']
    travel_mode = results_data['travel_mode']
    census_vars = results_data['census_vars']

    st.subheader("📊 Analysis Results")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("POIs Analyzed", format_number(result.poi_count))

    with col2:
        st.metric("Census Units", format_number(result.census_units_analyzed))

    with col3:
        if hasattr(result, 'total_population_served'):
            st.metric("Population Served", format_number(result.total_population_served))
        else:
            st.metric("Travel Time", f"{travel_time} min")

    with col4:
        mode_info = TRAVEL_MODES.get(travel_mode, {})
        st.metric("Travel Mode", f"{mode_info.get('icon', '')} {mode_info.get('name', travel_mode)}")

    # Results tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map", "📊 Demographics", "📍 POI Details", "💾 Export"])

    with tab1:
        # Interactive map with results
        st.markdown("### Service Area Coverage")

        # Try to show a generated map image if available
        if result.files_generated:
            map_files = []
            for file_type, file_path in result.files_generated.items():
                if 'map' in str(file_type).lower() and Path(file_path).is_dir():
                    map_files.extend([f for f in Path(file_path).glob("*.png") if f.is_file()])

            if map_files:
                # Show the accessibility map by default, or the first available map
                accessibility_map = next((f for f in map_files if 'accessibility' in f.name), None)
                selected_map = accessibility_map or map_files[0]

                # Map selector
                if len(map_files) > 1:
                    map_options = {}
                    for f in map_files:
                        if 'accessibility' in f.name:
                            label = "Accessibility Overview"
                        elif 'distance' in f.name:
                            label = "Distance to POIs"
                        elif 'b01003' in f.name.lower():
                            label = "Population Density"
                        elif 'b19013' in f.name.lower():
                            label = "Median Income"
                        elif 'b25077' in f.name.lower():
                            label = "Home Values"
                        elif 'b01002' in f.name.lower():
                            label = "Median Age"
                        else:
                            label = f.stem
                        map_options[label] = f

                    selected_label = st.selectbox(
                        "Select map to preview:",
                        options=list(map_options.keys()),
                        index=0
                    )
                    selected_map = map_options[selected_label]

                # Display the selected map
                st.image(str(selected_map), caption=f"{selected_label if len(map_files) > 1 else 'Analysis Map'}", use_container_width=True)
                st.caption(f"Travel mode: {travel_mode} | Travel time: {travel_time} minutes")

        # Fallback to interactive map
        elif hasattr(result, 'geojson_data') and result.geojson_data:
            try:
                map_obj = create_isochrone_map(
                    result.geojson_data,
                    poi_data.to_dict('records'),
                    center_lat=poi_data['lat'].mean(),
                    center_lon=poi_data['lon'].mean()
                )
                st_folium(map_obj, height=500, returned_objects=[])
            except:
                st.info("Map visualization not available.")
        else:
            st.info("Map visualization will be available after analysis completes.")

    with tab2:
        # Demographics summary
        st.markdown("### Census Data Summary")

        # Try to load and display the actual census data
        census_csv_path = None
        if result.files_generated:
            for file_type, file_path in result.files_generated.items():
                if 'census' in str(file_type).lower() and str(file_path).endswith('.csv'):
                    census_csv_path = file_path
                    break

        if census_csv_path and Path(census_csv_path).exists():
            try:
                # Load the census data
                census_df = pd.read_csv(census_csv_path)

                # Display summary statistics
                st.markdown("#### Summary Statistics")

                # Create summary for each census variable
                summary_data = []
                for var_code in census_vars:
                    var_name = CENSUS_VARIABLES.get(var_code, var_code)
                    if var_code in census_df.columns:
                        col_data = census_df[var_code].dropna()
                        if len(col_data) > 0:
                            summary_data.append({
                                'Variable': var_name,
                                'Total Population/Units': format_number(col_data.sum()) if 'population' in var_name.lower() else len(col_data),
                                'Average': format_number(col_data.mean()),
                                'Median': format_number(col_data.median()),
                                'Min': format_number(col_data.min()),
                                'Max': format_number(col_data.max())
                            })

                if summary_data:
                    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

                # Show sample of detailed data
                st.markdown("#### Sample Census Block Groups")

                # Select columns to display
                display_cols = ['geoid', 'travel_distance_km', 'nearest_poi_name'] + [col for col in census_vars if col in census_df.columns]

                # Format the data for display
                display_df = census_df[display_cols].head(10).copy()

                # Rename columns for better readability
                column_renames = {
                    'geoid': 'Census Block Group',
                    'travel_distance_km': 'Distance (km)',
                    'nearest_poi_name': 'Nearest POI'
                }
                for var_code in census_vars:
                    if var_code in display_df.columns:
                        column_renames[var_code] = CENSUS_VARIABLES.get(var_code, var_code)

                display_df = display_df.rename(columns=column_renames)

                # Format numeric columns
                for col in display_df.columns:
                    if 'Distance' in col:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                    elif any(term in col for term in ['Population', 'Income', 'Value', 'Age']):
                        display_df[col] = display_df[col].apply(lambda x: format_number(x) if pd.notna(x) else "N/A")

                st.dataframe(display_df, use_container_width=True)

                # Show total coverage
                st.markdown("#### Coverage Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Block Groups Analyzed", format_number(len(census_df)))
                with col2:
                    avg_distance = census_df['travel_distance_km'].mean()
                    st.metric("Average Distance", f"{avg_distance:.1f} km")
                with col3:
                    if 'B01003_001E' in census_df.columns:
                        total_pop = census_df['B01003_001E'].sum()
                        st.metric("Total Population Served", format_number(total_pop))

            except Exception as e:
                st.error(f"Error loading census data: {e!s}")
                st.info("Census data summary not available.")
        else:
            st.info("Detailed demographic data will be available in the exported CSV file after analysis.")

    with tab3:
        # POI details table
        st.markdown("### Custom POI Locations")

        # Enhanced POI data with analysis info
        poi_display = poi_data.copy()

        # Add any additional columns from the original data
        optional_cols = ['type', 'address', 'description']
        display_cols = ['name', 'lat', 'lon'] + [col for col in optional_cols if col in poi_display.columns]

        st.dataframe(poi_display[display_cols], use_container_width=True)

        # Show coverage area for each POI if available
        if result.poi_count > 1:
            st.info(f"Each location has a {travel_time}-minute {travel_mode} isochrone showing its service area.")

    with tab4:
        # Export options
        st.markdown("### Download Results")

        if result.files_generated:
            for file_type, file_path in result.files_generated.items():
                path_obj = Path(file_path)
                # Skip directories
                if path_obj.exists() and path_obj.is_file():
                    with open(file_path, 'rb') as f:
                        file_data = f.read()

                    file_name = path_obj.name
                    mime_type = 'text/csv' if str(file_path).endswith('.csv') else 'application/octet-stream'

                    st.download_button(
                        label=f"Download {file_type.replace('_', ' ').title()}",
                        data=file_data,
                        file_name=file_name,
                        mime=mime_type
                    )
                elif path_obj.exists() and path_obj.is_dir():
                    # For directories, show the files inside with download buttons
                    st.markdown(f"#### 📁 {file_type.replace('_', ' ').title()}")
                    dir_files = sorted([f for f in path_obj.glob("*") if f.is_file()])

                    if dir_files:
                        # Create columns for better layout
                        cols = st.columns(2)
                        for idx, file in enumerate(dir_files):
                            col = cols[idx % 2]
                            with col:
                                with open(file, 'rb') as f:
                                    file_data = f.read()

                                # Determine mime type based on file extension
                                if file.suffix.lower() == '.png':
                                    mime_type = 'image/png'
                                elif file.suffix.lower() == '.jpg' or file.suffix.lower() == '.jpeg':
                                    mime_type = 'image/jpeg'
                                elif file.suffix.lower() == '.svg':
                                    mime_type = 'image/svg+xml'
                                elif file.suffix.lower() == '.geojson':
                                    mime_type = 'application/geo+json'
                                else:
                                    mime_type = 'application/octet-stream'

                                # Create a more user-friendly label
                                if 'map' in str(file_type).lower():
                                    # Parse the filename to create a better label
                                    file_stem = file.stem
                                    if '_map' in file_stem:
                                        label = file_stem.split('_map')[0].split('_')[-1].upper()
                                        if label in ['B01003', 'B19013', 'B25077', 'B01002']:
                                            # Census variable codes - make them more readable
                                            census_labels = {
                                                'B01003': 'Population',
                                                'B19013': 'Income',
                                                'B25077': 'Home Value',
                                                'B01002': 'Age'
                                            }
                                            label = census_labels.get(label, label)
                                        label = f"📊 {label} Map"
                                    elif 'distance' in file_stem:
                                        label = "📏 Distance Map"
                                    elif 'accessibility' in file_stem:
                                        label = "♿ Accessibility Map"
                                    else:
                                        label = f"🗺️ {file.stem}"
                                else:
                                    label = file.name

                                st.download_button(
                                    label=label,
                                    data=file_data,
                                    file_name=file.name,
                                    mime=mime_type,
                                    key=f"download_{file_type}_{file.name}"
                                )

        # Analysis summary
        with st.expander("📋 Analysis Summary"):
            st.json({
                "poi_count": result.poi_count,
                "census_units_analyzed": result.census_units_analyzed,
                "travel_time_minutes": travel_time,
                "travel_mode": travel_mode,
                "census_variables": [CENSUS_VARIABLES.get(v, v) for v in census_vars],
                "files_generated": list(result.files_generated.keys()) if result.files_generated else []
            })
