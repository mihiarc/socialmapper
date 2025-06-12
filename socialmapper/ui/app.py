"""Streamlit app for SocialMapper."""

import json
import os
import traceback
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import the socialmapper modules
from socialmapper.core import run_socialmapper
from socialmapper.query import create_poi_config, query_pois
from socialmapper.states import state_name_to_abbreviation

# Get the Census API key from secrets
census_api_key = st.secrets["census"]["CENSUS_API_KEY"]

# Load environment variables
load_dotenv()


def search_pois(geocode_area, state, poi_type, poi_name, additional_tags=None):
    """Search for POIs and return results for user selection."""
    try:
        # Create the configuration dictionary that query_pois expects
        config = create_poi_config(
            geocode_area=geocode_area,
            state=state_name_to_abbreviation(state),
            city=geocode_area,
            poi_type=poi_type,
            poi_name=poi_name,
            additional_tags=additional_tags or {},
        )

        # Call query_pois with the config dictionary
        poi_results = query_pois(config)

        if poi_results and "pois" in poi_results and len(poi_results["pois"]) > 0:
            return poi_results["pois"]
        else:
            return []
    except Exception as e:
        st.error(f"Error searching for POIs: {str(e)}")
        return []


def run_app():
    """Run the Streamlit app."""
    # Set page configuration
    st.set_page_config(
        page_title="SocialMapper",
        page_icon="🧑‍🤝‍🧑",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # App title and description
    st.title("SocialMapper")
    st.markdown(
        """
                Understand community connections with SocialMapper, an open-source Python tool. Map travel time to key places like schools and parks, then see the demographics of who can access them. Reveal service gaps and gain insights for better community planning in both urban and rural areas.
    """
    )

    # Create a directory for pages if it doesn't exist
    Path("pages").mkdir(exist_ok=True)

    # Create tabbed interface
    tab1, tab2 = st.tabs(["📍 Single POI Analysis", "📊 Bulk POI Analysis"])

    # ==========================================
    # TAB 1: SINGLE POI ANALYSIS
    # ==========================================
    with tab1:
        st.header("Single POI Analysis")
        st.markdown("Select a specific point of interest to analyze travel times and demographics.")

        # Common parameters in sidebar
        st.sidebar.header("Analysis Configuration")

        travel_time = st.sidebar.slider(
            "Travel time (minutes)",
            min_value=5,
            max_value=60,
            value=15,
            step=5,
            key="single_travel_time",
        )

        # Geographic level selection
        geographic_level = st.sidebar.selectbox(
            "Geographic Analysis Level",
            ["block-group", "zcta"],
            format_func=lambda x: (
                "Census Block Groups" if x == "block-group" else "ZIP Code Tabulation Areas"
            ),
            help="Choose the geographic unit for analysis. Block groups are smaller and more granular, while ZCTAs approximate ZIP code areas.",
        )

        # Census variables selection
        available_variables = {
            "total_population": "Total Population",
            "median_household_income": "Median Household Income",
            "median_home_value": "Median Home Value",
            "median_age": "Median Age",
            "white_population": "White Population",
            "black_population": "Black Population",
            "hispanic_population": "Hispanic Population",
            "housing_units": "Housing Units",
            "education_bachelors_plus": "Education (Bachelor's or higher)",
        }

        census_variables = st.sidebar.multiselect(
            "Select census variables to analyze",
            options=list(available_variables.keys()),
            default=["total_population"],
            format_func=lambda x: available_variables[x],
        )

        # Export options
        st.sidebar.subheader("Output Options")
        export_csv = st.sidebar.checkbox(
            "Export data to CSV",
            value=True,
            help="Export census data to CSV format with geographic identifiers and travel distances",
        )

        export_maps = st.sidebar.checkbox(
            "Generate maps", value=True, help="Generate map visualizations for each census variable"
        )

        # Map type selection
        if export_maps:
            map_type = st.sidebar.radio(
                "Map Type:",
                ["Interactive (Plotly)", "Static"],
                index=0,
                help="Interactive maps can be explored in the browser. Static maps can be downloaded.",
            )
            use_interactive_maps = map_type == "Interactive (Plotly)"
        else:
            use_interactive_maps = False

        # POI Selection Methods
        st.subheader("Select Your Point of Interest")

        poi_method = st.radio(
            "How would you like to select your POI?",
            ["🔍 Search for POIs", "📍 Enter Address/Name Directly"],
            horizontal=True,
        )

        if poi_method == "🔍 Search for POIs":
            # POI Search Interface
            col1, col2 = st.columns(2)

            with col1:
                geocode_area = st.text_input("Area (City/Town)", value="Corvallis")
                state = st.selectbox(
                    "State",
                    [
                        "Alabama",
                        "Alaska",
                        "Arizona",
                        "Arkansas",
                        "California",
                        "Colorado",
                        "Connecticut",
                        "Delaware",
                        "Florida",
                        "Georgia",
                        "Hawaii",
                        "Idaho",
                        "Illinois",
                        "Indiana",
                        "Iowa",
                        "Kansas",
                        "Kentucky",
                        "Louisiana",
                        "Maine",
                        "Maryland",
                        "Massachusetts",
                        "Michigan",
                        "Minnesota",
                        "Mississippi",
                        "Missouri",
                        "Montana",
                        "Nebraska",
                        "Nevada",
                        "New Hampshire",
                        "New Jersey",
                        "New Mexico",
                        "New York",
                        "North Carolina",
                        "North Dakota",
                        "Ohio",
                        "Oklahoma",
                        "Oregon",
                        "Pennsylvania",
                        "Rhode Island",
                        "South Carolina",
                        "South Dakota",
                        "Tennessee",
                        "Texas",
                        "Utah",
                        "Vermont",
                        "Virginia",
                        "Washington",
                        "West Virginia",
                        "Wisconsin",
                        "Wyoming",
                    ],
                    index=36,
                )  # Oregon is at index 36

            with col2:
                poi_type = st.selectbox(
                    "POI Type",
                    ["amenity", "shop", "highway", "leisure", "education", "transportation"],
                )

                # Dynamic options based on selected POI type
                poi_options = {
                    "amenity": [
                        "library",
                        "school",
                        "hospital",
                        "restaurant",
                        "bank",
                        "pharmacy",
                        "place_of_worship",
                        "bar",
                        "fast_food",
                        "pub",
                        "parking",
                    ],
                    "natural": ["wood", "beach", "water"],
                    "shop": ["supermarket", "convenience", "clothes", "bakery"],
                    "highway": ["path", "footway"],
                }

                # Get default options based on selected type
                default_options = poi_options.get(poi_type, [])

                # Allow user to either select from common options or enter custom value
                poi_selection_method = st.radio(
                    "POI Selection Method", ["Common Options", "Custom Value"], horizontal=True
                )

                if poi_selection_method == "Common Options" and default_options:
                    poi_name = st.selectbox("POI Name", default_options)
                else:
                    poi_name = st.text_input("POI Name (Custom)", "library")

            # Search button
            if st.button("🔍 Search for POIs", type="primary"):
                if not geocode_area or not poi_type or not poi_name:
                    st.error("Please fill in all required fields: Area, POI Type, and POI Name.")
                else:
                    with st.spinner("Searching for POIs..."):
                        poi_list = search_pois(geocode_area, state, poi_type, poi_name)

                        if poi_list:
                            st.session_state.poi_search_results = poi_list
                            st.success(f"Found {len(poi_list)} POIs matching your criteria!")
                        else:
                            st.warning(
                                "No POIs found with your search criteria. Try different parameters."
                            )

            # Display search results and allow selection
            if "poi_search_results" in st.session_state and st.session_state.poi_search_results:
                st.subheader("Select a POI from Search Results")

                # Helper function to extract POI name with fallbacks
                def get_poi_name(poi):
                    if "name" in poi and poi["name"]:
                        return poi["name"]
                    tags = poi.get("tags", {})
                    if "name" in tags and tags["name"]:
                        return tags["name"]
                    if "brand" in tags and tags["brand"]:
                        return tags["brand"]
                    if "operator" in tags and tags["operator"]:
                        return tags["operator"]
                    return "Unnamed Location"

                # Helper function to get POI type with emoji
                def get_poi_type_display(poi):
                    tags = poi.get("tags", {})
                    poi_type = (
                        tags.get("amenity")
                        or tags.get("shop")
                        or tags.get("leisure")
                        or tags.get("highway")
                        or poi.get("type", "unknown")
                    )

                    type_emojis = {
                        "library": "📚 Library",
                        "school": "🏫 School",
                        "hospital": "🏥 Hospital",
                        "restaurant": "🍽️ Restaurant",
                        "bank": "🏦 Bank",
                        "pharmacy": "💊 Pharmacy",
                        "place_of_worship": "⛪ Place of Worship",
                        "bar": "🍻 Bar",
                        "fast_food": "🍔 Fast Food",
                        "pub": "🍺 Pub",
                        "parking": "🅿️ Parking",
                        "supermarket": "🛒 Supermarket",
                        "convenience": "🏪 Convenience Store",
                        "park": "🌳 Park",
                        "university": "🎓 University",
                    }

                    return type_emojis.get(poi_type, f"📍 {poi_type.replace('_', ' ').title()}")

                # Helper function to get address info
                def get_address_info(poi):
                    tags = poi.get("tags", {})
                    address_parts = []

                    if "addr:housenumber" in tags and "addr:street" in tags:
                        address_parts.append(f"{tags['addr:housenumber']} {tags['addr:street']}")
                    elif "addr:full" in tags:
                        address_parts.append(tags["addr:full"])
                    elif "addr:street" in tags:
                        address_parts.append(tags["addr:street"])

                    if "addr:city" in tags:
                        address_parts.append(tags["addr:city"])

                    return ", ".join(address_parts) if address_parts else None

                # Display POIs in a nice format
                for i, poi in enumerate(st.session_state.poi_search_results):
                    with st.container():
                        col1, col2 = st.columns([5, 1])

                        with col1:
                            # POI name and type
                            poi_name = get_poi_name(poi)
                            poi_type_display = get_poi_type_display(poi)

                            st.markdown(f"### {poi_name}")
                            st.markdown(f"**{poi_type_display}**")

                            # Address if available
                            address = get_address_info(poi)
                            if address:
                                st.markdown(f"📍 {address}")

                            # Coordinates
                            lat, lon = poi.get("lat", 0), poi.get("lon", 0)
                            st.markdown(f"🗺️ Coordinates: `{lat:.4f}, {lon:.4f}`")

                            # Additional useful tags
                            tags = poi.get("tags", {})
                            useful_info = []

                            if "operator" in tags and tags["operator"] != poi_name:
                                useful_info.append(f"Operator: {tags['operator']}")
                            if "opening_hours" in tags:
                                useful_info.append(f"Hours: {tags['opening_hours']}")
                            if "phone" in tags:
                                useful_info.append(f"Phone: {tags['phone']}")
                            if "website" in tags:
                                useful_info.append(f"Website: {tags['website']}")

                            if useful_info:
                                st.markdown("**Additional Info:**")
                                for info in useful_info:
                                    st.markdown(f"• {info}")

                        with col2:
                            st.markdown("")  # spacing
                            if st.button(
                                "✅ Select",
                                key=f"select_poi_{i}",
                                type="primary",
                                use_container_width=True,
                            ):
                                st.session_state.selected_poi = poi
                                st.success(f"Selected: {poi_name}")
                                st.rerun()

                        st.markdown("---")  # Visual separator between POIs

        else:
            # Direct address/name entry
            st.subheader("Enter POI Details Directly")

            col1, col2 = st.columns(2)

            with col1:
                direct_name = st.text_input(
                    "POI Name or Address", placeholder="e.g., Central Library, 123 Main St"
                )
                direct_lat = st.number_input("Latitude", format="%.6f", value=44.5646)

            with col2:
                direct_type = st.text_input(
                    "POI Type", value="library", placeholder="e.g., library, school, park"
                )
                direct_lon = st.number_input("Longitude", format="%.6f", value=-123.2620)

            if st.button("Use This POI", type="primary"):
                if direct_name and direct_lat and direct_lon:
                    st.session_state.selected_poi = {
                        "name": direct_name,
                        "lat": direct_lat,
                        "lon": direct_lon,
                        "type": direct_type,
                        "tags": {"amenity": direct_type},
                    }
                    st.success(f"Selected: {direct_name}")
                else:
                    st.error("Please fill in all required fields.")

        # Show selected POI and run analysis
        if "selected_poi" in st.session_state:
            st.subheader("🎯 Selected POI")
            selected = st.session_state.selected_poi

            # Use the same helper functions for consistent formatting
            def get_poi_name(poi):
                if "name" in poi and poi["name"]:
                    return poi["name"]
                tags = poi.get("tags", {})
                if "name" in tags and tags["name"]:
                    return tags["name"]
                if "brand" in tags and tags["brand"]:
                    return tags["brand"]
                if "operator" in tags and tags["operator"]:
                    return tags["operator"]
                return "Unnamed Location"

            def get_poi_type_display(poi):
                tags = poi.get("tags", {})
                poi_type = (
                    tags.get("amenity")
                    or tags.get("shop")
                    or tags.get("leisure")
                    or tags.get("highway")
                    or poi.get("type", "unknown")
                )

                type_emojis = {
                    "library": "📚 Library",
                    "school": "🏫 School",
                    "hospital": "🏥 Hospital",
                    "restaurant": "🍽️ Restaurant",
                    "bank": "🏦 Bank",
                    "pharmacy": "💊 Pharmacy",
                    "place_of_worship": "⛪ Place of Worship",
                    "bar": "🍻 Bar",
                    "fast_food": "🍔 Fast Food",
                    "pub": "🍺 Pub",
                    "parking": "🅿️ Parking",
                    "supermarket": "🛒 Supermarket",
                    "convenience": "🏪 Convenience Store",
                    "park": "🌳 Park",
                    "university": "🎓 University",
                }

                return type_emojis.get(poi_type, f"📍 {poi_type.replace('_', ' ').title()}")

            poi_name = get_poi_name(selected)
            poi_type_display = get_poi_type_display(selected)

            col1, col2 = st.columns([4, 1])
            with col1:
                with st.container():
                    st.markdown(f"**{poi_name}**")
                    st.markdown(f"{poi_type_display}")
                    lat, lon = selected.get("lat", 0), selected.get("lon", 0)
                    st.markdown(f"🗺️ `{lat:.4f}, {lon:.4f}`")

            with col2:
                if st.button("🗑️ Clear", use_container_width=True):
                    del st.session_state.selected_poi
                    st.rerun()

            # Run Analysis Button
            if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
                # Create temporary coordinate file
                temp_coords = {"pois": [selected]}
                os.makedirs("output/pois", exist_ok=True)
                temp_file = "output/pois/selected_poi.json"
                with open(temp_file, "w") as f:
                    json.dump(temp_coords, f)

                # Run analysis
                with st.status("Running SocialMapper analysis...", expanded=True) as status:
                    try:
                        results = run_socialmapper(
                            custom_coords_path=temp_file,
                            travel_time=travel_time,
                            geographic_level=geographic_level,
                            census_variables=census_variables,
                            api_key=census_api_key,
                            export_csv=export_csv,
                            export_maps=export_maps,
                            use_interactive_maps=use_interactive_maps,
                        )

                        status.update(label="Analysis completed successfully!", state="complete")
                        st.session_state.single_poi_results = results

                    except Exception as e:
                        status.update(label="Analysis failed", state="error")
                        st.error(f"An error occurred: {str(e)}")
                        st.subheader("Error Details:")
                        st.code(traceback.format_exc())

            # Display results if available
            if "single_poi_results" in st.session_state:
                display_results(st.session_state.single_poi_results)

    # ==========================================
    # TAB 2: BULK POI ANALYSIS
    # ==========================================
    with tab2:
        st.header("Bulk POI Analysis")
        st.markdown(
            "Analyze multiple POIs at once - useful for research and comprehensive analysis."
        )

        # Input method selection
        input_method = st.radio(
            "Select input method:",
            ["OpenStreetMap POI Query", "Custom Coordinates"],
            help="Choose how to specify your POIs for analysis",
        )

        # Common parameters for bulk analysis
        col1, col2 = st.columns(2)

        with col1:
            bulk_travel_time = st.slider(
                "Travel time (minutes)",
                min_value=5,
                max_value=60,
                value=15,
                step=5,
                key="bulk_travel_time",
            )

            bulk_geographic_level = st.selectbox(
                "Geographic Analysis Level",
                ["block-group", "zcta"],
                format_func=lambda x: (
                    "Census Block Groups" if x == "block-group" else "ZIP Code Tabulation Areas"
                ),
                help="Choose the geographic unit for analysis. Block groups are smaller and more granular, while ZCTAs approximate ZIP code areas.",
                key="bulk_geo_level",
            )

        with col2:
            bulk_census_variables = st.multiselect(
                "Select census variables to analyze",
                options=list(available_variables.keys()),
                default=["total_population"],
                format_func=lambda x: available_variables[x],
                key="bulk_census_vars",
            )

        # Export options for bulk analysis
        st.subheader("Output Options")
        col1, col2 = st.columns(2)

        with col1:
            bulk_export_csv = st.checkbox(
                "Export data to CSV",
                value=True,
                help="Export census data to CSV format",
                key="bulk_csv",
            )

        with col2:
            bulk_export_maps = st.checkbox(
                "Generate maps",
                value=False,
                help="Generate map visualizations (only for first POI in bulk mode)",
                key="bulk_maps",
            )

        # Input method specific UI
        if input_method == "OpenStreetMap POI Query":
            handle_osm_query_bulk(
                bulk_travel_time,
                bulk_geographic_level,
                bulk_census_variables,
                bulk_export_csv,
                bulk_export_maps,
            )
        else:
            handle_custom_coordinates_bulk(
                bulk_travel_time,
                bulk_geographic_level,
                bulk_census_variables,
                bulk_export_csv,
                bulk_export_maps,
            )


def handle_osm_query_bulk(
    bulk_travel_time,
    bulk_geographic_level,
    bulk_census_variables,
    bulk_export_csv,
    bulk_export_maps,
):
    """Handle OpenStreetMap POI query for bulk analysis."""
    st.subheader("OpenStreetMap POI Query")

    # Input fields for POI query
    col1, col2 = st.columns(2)
    with col1:
        geocode_area = st.text_input("Area (City/Town)", value="Corvallis", key="bulk_area")
        state = st.selectbox(
            "State",
            [
                "Alabama",
                "Alaska",
                "Arizona",
                "Arkansas",
                "California",
                "Colorado",
                "Connecticut",
                "Delaware",
                "Florida",
                "Georgia",
                "Hawaii",
                "Idaho",
                "Illinois",
                "Indiana",
                "Iowa",
                "Kansas",
                "Kentucky",
                "Louisiana",
                "Maine",
                "Maryland",
                "Massachusetts",
                "Michigan",
                "Minnesota",
                "Mississippi",
                "Missouri",
                "Montana",
                "Nebraska",
                "Nevada",
                "New Hampshire",
                "New Jersey",
                "New Mexico",
                "New York",
                "North Carolina",
                "North Dakota",
                "Ohio",
                "Oklahoma",
                "Oregon",
                "Pennsylvania",
                "Rhode Island",
                "South Carolina",
                "South Dakota",
                "Tennessee",
                "Texas",
                "Utah",
                "Vermont",
                "Virginia",
                "Washington",
                "West Virginia",
                "Wisconsin",
                "Wyoming",
            ],
            index=36,
            key="bulk_state",
        )  # Oregon is at index 36

    with col2:
        poi_type = st.selectbox(
            "POI Type",
            ["amenity", "shop", "highway", "leisure", "education", "transportation"],
            key="bulk_poi_type",
        )

        # Dynamic options based on selected POI type
        poi_options = {
            "amenity": [
                "library",
                "school",
                "hospital",
                "restaurant",
                "bank",
                "pharmacy",
                "place_of_worship",
                "bar",
                "fast_food",
                "pub",
                "parking",
            ],
            "natural": ["wood", "beach", "water"],
            "shop": ["supermarket", "convenience", "clothes", "bakery"],
            "highway": ["path", "footway"],
        }

        # Get default options based on selected type
        default_options = poi_options.get(poi_type, [])

        # Allow user to either select from common options or enter custom value
        poi_selection_method = st.radio(
            "POI Selection Method",
            ["Common Options", "Custom Value"],
            horizontal=True,
            key="bulk_poi_method",
        )

        if poi_selection_method == "Common Options" and default_options:
            poi_name = st.selectbox("POI Name", default_options, key="bulk_poi_name")
        else:
            poi_name = st.text_input("POI Name (Custom)", "library", key="bulk_poi_name_custom")

    # Advanced options
    with st.expander("Advanced Options"):
        max_poi_count = st.slider(
            "Maximum number of POIs to analyze",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            help="Limit the number of POIs to analyze to prevent performance issues. If more POIs are found, a random sample will be used.",
            key="bulk_max_poi_count",
        )

    # Run bulk analysis
    if st.button("🚀 Run Bulk Analysis", type="primary"):
        if not geocode_area or not poi_type or not poi_name:
            st.error("Please fill in all required fields: Area, POI Type, and POI Name.")
        else:
            run_bulk_analysis_osm(
                geocode_area,
                state,
                poi_type,
                poi_name,
                max_poi_count,
                bulk_travel_time,
                bulk_geographic_level,
                bulk_census_variables,
                bulk_export_csv,
                bulk_export_maps,
            )


def handle_custom_coordinates_bulk(
    bulk_travel_time,
    bulk_geographic_level,
    bulk_census_variables,
    bulk_export_csv,
    bulk_export_maps,
):
    """Handle custom coordinates input for bulk analysis."""
    st.subheader("Custom Coordinates Input")

    upload_method = st.radio(
        "Select input format:", ["Upload CSV/JSON File", "Manual Entry"], key="bulk_upload_method"
    )

    if upload_method == "Upload CSV/JSON File":
        uploaded_file = st.file_uploader(
            "Upload coordinates file (CSV or JSON)", type=["csv", "json"], key="bulk_file_upload"
        )

        if uploaded_file:
            # Process uploaded file
            handle_uploaded_file_bulk(
                uploaded_file,
                bulk_travel_time,
                bulk_geographic_level,
                bulk_census_variables,
                bulk_export_csv,
                bulk_export_maps,
            )

    else:
        # Manual entry for bulk
        handle_manual_entry_bulk(
            bulk_travel_time,
            bulk_geographic_level,
            bulk_census_variables,
            bulk_export_csv,
            bulk_export_maps,
        )


def handle_uploaded_file_bulk(
    uploaded_file,
    bulk_travel_time,
    bulk_geographic_level,
    bulk_census_variables,
    bulk_export_csv,
    bulk_export_maps,
):
    """Process uploaded file for bulk analysis."""
    # Make sure the output directory exists before saving
    os.makedirs("output/pois", exist_ok=True)

    # Save uploaded file temporarily
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    custom_file_path = f"output/pois/bulk_custom_coordinates{file_extension}"

    with open(custom_file_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    st.success(f"File uploaded successfully: {uploaded_file.name}")

    # Preview the file
    if file_extension == ".csv":
        df = pd.read_csv(custom_file_path)
        st.dataframe(df.head())

        if st.button("🚀 Run Bulk Analysis", type="primary"):
            run_bulk_analysis_custom(
                custom_file_path,
                bulk_travel_time,
                bulk_geographic_level,
                bulk_census_variables,
                bulk_export_csv,
                bulk_export_maps,
            )

    elif file_extension == ".json":
        with open(custom_file_path, "r") as f:
            json_data = json.load(f)

        # Show data preview
        with st.expander("Preview JSON data", expanded=True):
            st.json(json_data[:3] if isinstance(json_data, list) else json_data)

        # Field mapping for JSON
        handle_json_field_mapping(
            json_data,
            custom_file_path,
            bulk_travel_time,
            bulk_geographic_level,
            bulk_census_variables,
            bulk_export_csv,
            bulk_export_maps,
        )


def handle_json_field_mapping(
    json_data,
    custom_file_path,
    bulk_travel_time,
    bulk_geographic_level,
    bulk_census_variables,
    bulk_export_csv,
    bulk_export_maps,
):
    """Handle field mapping for JSON files."""
    if isinstance(json_data, dict) and "pois" in json_data:
        # Already in correct format
        if st.button("🚀 Run Bulk Analysis", type="primary", key="bulk_run_json_direct"):
            run_bulk_analysis_custom(
                custom_file_path,
                bulk_travel_time,
                bulk_geographic_level,
                bulk_census_variables,
                bulk_export_csv,
                bulk_export_maps,
            )

    elif isinstance(json_data, list) and json_data:
        # List of POIs, need to check structure
        sample_poi = json_data[0]

        if "lat" in sample_poi and "lon" in sample_poi:
            # Coordinates exist, can proceed
            st.info("JSON structure looks good for analysis.")

            # Optional field mapping
            name_field = st.selectbox(
                "Name field (optional):",
                ["None"] + list(sample_poi.keys()),
                key="bulk_json_name_field",
            )

            type_field = st.selectbox(
                "Type field (optional):",
                ["None"] + list(sample_poi.keys()),
                key="bulk_json_type_field",
            )

            if st.button("🚀 Run Bulk Analysis", type="primary", key="bulk_run_json_mapped"):
                name_field_val = None if name_field == "None" else name_field
                type_field_val = None if type_field == "None" else type_field
                run_bulk_analysis_custom(
                    custom_file_path,
                    bulk_travel_time,
                    bulk_geographic_level,
                    bulk_census_variables,
                    bulk_export_csv,
                    bulk_export_maps,
                    name_field_val,
                    type_field_val,
                )
        else:
            st.error("JSON file must contain 'lat' and 'lon' fields for each POI.")


def handle_manual_entry_bulk(
    bulk_travel_time,
    bulk_geographic_level,
    bulk_census_variables,
    bulk_export_csv,
    bulk_export_maps,
):
    """Handle manual coordinate entry for bulk analysis."""
    st.subheader("Manual Coordinate Entry")

    # Initialize session state for coordinates
    if "bulk_coordinates" not in st.session_state:
        st.session_state.bulk_coordinates = [{"name": "", "lat": "", "lon": "", "state": ""}]

    for i, coord in enumerate(st.session_state.bulk_coordinates):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        with col1:
            coord["name"] = st.text_input(f"POI Name {i+1}", coord["name"], key=f"bulk_name_{i}")
        with col2:
            coord["lat"] = st.text_input(f"Latitude {i+1}", coord["lat"], key=f"bulk_lat_{i}")
        with col3:
            coord["lon"] = st.text_input(f"Longitude {i+1}", coord["lon"], key=f"bulk_lon_{i}")
        with col4:
            coord["state"] = st.text_input(f"State {i+1}", coord["state"], key=f"bulk_state_{i}")
        with col5:
            if st.button("Clear", key=f"bulk_clear_{i}"):
                st.session_state.bulk_coordinates.pop(i)
                st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Another Location", key="bulk_add_location"):
            st.session_state.bulk_coordinates.append(
                {"name": "", "lat": "", "lon": "", "state": ""}
            )
            st.rerun()

    with col2:
        if st.button("🚀 Run Bulk Analysis", type="primary", key="bulk_run_manual"):
            # Validate and save coordinates
            valid_coords = []
            for coord in st.session_state.bulk_coordinates:
                try:
                    if coord["name"] and coord["lat"] and coord["lon"]:
                        new_coord = {
                            "id": f"manual_{len(valid_coords)}",
                            "name": coord["name"],
                            "lat": float(coord["lat"]),
                            "lon": float(coord["lon"]),
                            "tags": {},
                        }
                        valid_coords.append(new_coord)
                except (ValueError, TypeError) as e:
                    st.error(f"Error with coordinate {coord['name']}: {str(e)}")

            if valid_coords:
                # Save coordinates and run analysis
                os.makedirs("output/pois", exist_ok=True)
                coord_file = "output/pois/bulk_manual_coordinates.json"
                with open(coord_file, "w") as f:
                    json.dump({"pois": valid_coords}, f)

                run_bulk_analysis_custom(
                    coord_file,
                    bulk_travel_time,
                    bulk_geographic_level,
                    bulk_census_variables,
                    bulk_export_csv,
                    bulk_export_maps,
                )
            else:
                st.error("No valid coordinates to analyze")


def run_bulk_analysis_osm(
    geocode_area,
    state,
    poi_type,
    poi_name,
    max_poi_count,
    bulk_travel_time,
    bulk_geographic_level,
    bulk_census_variables,
    bulk_export_csv,
    bulk_export_maps,
):
    """Run bulk analysis for OpenStreetMap POI query."""
    with st.status("Running SocialMapper bulk analysis...", expanded=True) as status:
        try:
            results = run_socialmapper(
                geocode_area=geocode_area,
                state=state_name_to_abbreviation(state),
                city=geocode_area,
                poi_type=poi_type,
                poi_name=poi_name,
                travel_time=bulk_travel_time,
                geographic_level=bulk_geographic_level,
                census_variables=bulk_census_variables,
                api_key=census_api_key,
                export_csv=bulk_export_csv,
                export_maps=bulk_export_maps,
                use_interactive_maps=True,
                max_poi_count=max_poi_count,
            )

            status.update(label="Bulk analysis completed successfully!", state="complete")
            st.session_state.bulk_results = results

        except Exception as e:
            status.update(label="Bulk analysis failed", state="error")
            st.error(f"An error occurred: {str(e)}")
            st.subheader("Error Details:")
            st.code(traceback.format_exc())


def run_bulk_analysis_custom(
    custom_file_path,
    bulk_travel_time,
    bulk_geographic_level,
    bulk_census_variables,
    bulk_export_csv,
    bulk_export_maps,
    name_field=None,
    type_field=None,
):
    """Run bulk analysis for custom coordinates."""
    with st.status("Running SocialMapper bulk analysis...", expanded=True) as status:
        try:
            results = run_socialmapper(
                custom_coords_path=custom_file_path,
                travel_time=bulk_travel_time,
                geographic_level=bulk_geographic_level,
                census_variables=bulk_census_variables,
                api_key=census_api_key,
                export_csv=bulk_export_csv,
                export_maps=bulk_export_maps,
                use_interactive_maps=True,
                name_field=name_field,
                type_field=type_field,
            )

            status.update(label="Bulk analysis completed successfully!", state="complete")
            st.session_state.bulk_results = results

        except Exception as e:
            status.update(label="Bulk analysis failed", state="error")
            st.error(f"An error occurred: {str(e)}")
            st.subheader("Error Details:")
            st.code(traceback.format_exc())


def display_results(results):
    """Display analysis results."""
    if not results:
        return

    st.header("Analysis Results")

    # ---- POIs section ---------------------------------------------------
    poi_data = results.get("poi_data")
    if poi_data:
        with st.expander("Points of Interest", expanded=True):
            if isinstance(poi_data, dict) and "pois" in poi_data:
                poi_df = pd.DataFrame(poi_data.get("pois", []))
                if not poi_df.empty:
                    # Handle potential Polygon serialization issues
                    display_df = poi_df.copy()
                    for col in display_df.columns:
                        if display_df[col].dtype == "object":
                            # Convert any complex objects to string representation
                            display_df[col] = display_df[col].astype(str)
                    st.dataframe(display_df)
                else:
                    st.warning("No POIs found in the results.")
            else:
                st.warning("POI data not found in the expected format.")

    # ---- Interactive Maps (if available) ---------------------
    interactive_maps_available = results.get("interactive_maps_available", False)
    if interactive_maps_available:
        st.subheader("Interactive Maps")
        st.info(
            "Explore these interactive maps - you can zoom, pan, and click on features to see more information."
        )

    # ---- Static Maps grid (if available) ----------------------------
    map_files = results.get("maps", [])
    if map_files:
        st.subheader("Demographic Maps")
        if any(Path(map_file).exists() for map_file in map_files):
            cols = st.columns(2)
            for i, map_file in enumerate(map_files):
                if Path(map_file).exists():
                    cols[i % 2].image(map_file, use_container_width=True)
                    # Add download button for each map
                    with cols[i % 2]:
                        with open(map_file, "rb") as file:
                            st.download_button(
                                label=f"Download {os.path.basename(map_file)}",
                                data=file,
                                file_name=os.path.basename(map_file),
                                mime="image/png",
                                key=f"download_map_{i}",
                            )
        else:
            st.info("No static maps were generated. Interactive maps are being used instead.")

    # ---- CSV export --------------------------------------------------
    csv_path = results.get("csv_data")
    if csv_path and Path(csv_path).exists():
        st.subheader("Census Data Export")
        st.success("Census data with travel distances exported to CSV")
        with st.expander("Preview CSV data"):
            csv_df = pd.read_csv(csv_path)
            st.dataframe(csv_df.head(10))

        # Provide download button
        with open(csv_path, "rb") as file:
            st.download_button(
                label="Download CSV data",
                data=file,
                file_name=os.path.basename(csv_path),
                mime="text/csv",
                key="download_csv",
            )

    # Show bulk results if available
    if "bulk_results" in st.session_state:
        st.markdown("---")
        display_results(st.session_state.bulk_results)

    # Display about section and links
    st.sidebar.markdown("---")
    st.sidebar.header("Navigation")
    st.sidebar.markdown("[Documentation](https://github.com/mihiarc/socialmapper)")

    with st.expander("About SocialMapper"):
        st.markdown(
            """
        # 🏘️ SocialMapper: Explore Your Community Connections. 🏘️

        SocialMapper is an open-source Python toolkit that helps you understand how people connect with the important places in their community. Imagine taking a key spot like your local community center or school and seeing exactly what areas are within a certain travel time – whether it's a quick walk or a longer drive. SocialMapper does just that.

        But it doesn't stop at travel time. SocialMapper also shows you the characteristics of the people who live within these accessible areas, like how many people live there and what the average income is. This helps you see who can easily reach vital community resources and identify any gaps in access.

        Whether you're looking at bustling city neighborhoods or more spread-out rural areas, SocialMapper provides clear insights for making communities better, planning services, and ensuring everyone has good access to the places that matter.

        With plans to expand and explore our connection to the natural world, SocialMapper is a tool for understanding people, places, and the environment around us.

        Discover the connections in your community with SocialMapper – where location brings understanding.

        ## Features

        - **Finding Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
        - **Generating Travel Time Areas** - Create isochrones showing areas reachable within a certain travel time
        - **Identifying Geographic Units** - Determine which census units intersect with these areas (Block Groups or ZIP Code Tabulation Areas)
        - **Retrieving Demographic Data** - Pull census data for the identified areas
        - **Visualizing Results** - Generate maps showing the demographic variables around the POIs

        For more information, visit the [GitHub repository](https://github.com/mihiarc/socialmapper).
        """
        )


if __name__ == "__main__":
    run_app()
