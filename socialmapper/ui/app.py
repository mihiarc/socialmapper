"""Streamlit app for SocialMapper."""

import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from pathlib import Path
import yaml
import json
import traceback
from dotenv import load_dotenv
from stqdm import stqdm

# Import the socialmapper modules
from socialmapper import run_socialmapper, setup_directories
from socialmapper.states import state_name_to_abbreviation

# Load environment variables
load_dotenv()

def run_app():
    """Run the Streamlit app."""
    # Set page configuration
    st.set_page_config(
        page_title="SocialMapper",
        page_icon="🧑‍🤝‍🧑",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # App title and description
    st.title("SocialMapper")
    st.markdown("""
                Understand community connections with SocialMapper, an open-source Python tool. Map travel time to key places like schools and parks, then see the demographics of who can access them. Reveal service gaps and gain insights for better community planning in both urban and rural areas.
    """)

    # Create a directory for pages if it doesn't exist
    Path("pages").mkdir(exist_ok=True)

    # Main app sidebar configuration
    st.sidebar.header("Configuration")

    # Input method selection
    input_method = st.sidebar.radio(
        "Select input method:",
        ["OpenStreetMap POI Query", "Custom Coordinates"]
    )

    # Common parameters
    travel_time = st.sidebar.slider(
        "Travel time (minutes)",
        min_value=5,
        max_value=60,
        value=15,
        step=5
    )

    # Census variables selection
    available_variables = {
        'total_population': 'Total Population',
        'median_household_income': 'Median Household Income',
        'median_home_value': 'Median Home Value',
        'median_age': 'Median Age',
        'white_population': 'White Population',
        'black_population': 'Black Population',
        'hispanic_population': 'Hispanic Population',
        'housing_units': 'Housing Units',
        'education_bachelors_plus': 'Education (Bachelor\'s or higher)'
    }

    census_variables = st.sidebar.multiselect(
        "Select census variables to analyze",
        options=list(available_variables.keys()),
        default=['total_population'],
        format_func=lambda x: available_variables[x]
    )

    # Export options 
    export = st.sidebar.checkbox(
        "Export data to CSV",
        value=True,
        help="Export census data to CSV format with block group identifiers and travel distances"
    )

    # API key input
    census_api_key = st.sidebar.text_input(
        "Census API Key (optional if set as environment variable)",
        value=os.environ.get("CENSUS_API_KEY", ""),
        type="password"
    )

    # Main content area based on input method
    if input_method == "OpenStreetMap POI Query":
        st.header("OpenStreetMap POI Query")
        
        # Input fields for POI query
        col1, col2 = st.columns(2)
        with col1:
            geocode_area = st.text_input("Area (City/Town)", "Fuquay-Varina")
            state = st.selectbox("State", [
                "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
                "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
                "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
                "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
                "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
                "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
                "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", 
                "Wisconsin", "Wyoming"
            ], index=32)  # North Carolina as default (index 32)
        
        with col2:
            poi_type = st.selectbox(
                "POI Type",
                ["amenity", "leisure", "shop", "building", "healthcare", "office", "education", "tourism", "natural", "historic", "transportation"]
            )
            
            # Dynamic options based on selected POI type
            poi_options = {
                "amenity": ["library", "school", "hospital", "restaurant", "cafe", "bank", "pharmacy", "police", "fire_station", "place_of_worship", "community_centre", "post_office", "university", "college", "kindergarten", "bar", "fast_food", "pub", "ice_cream", "cinema", "theatre", "marketplace", "bus_station", "fuel", "parking", "atm", "toilet", "charging_station", "doctors", "clinic", "veterinary", "courthouse", "shelter", "social_facility", "arts_centre"],
                "leisure": ["park", "garden", "playground", "sports_centre", "swimming_pool", "fitness_centre", "golf_course", "stadium", "nature_reserve", "track", "pitch", "water_park", "dog_park", "sports_hall", "marina", "beach_resort", "picnic_table", "ice_rink", "miniature_golf", "dance", "bowling_alley", "amusement_arcade", "fishing", "horse_riding", "disc_golf_course", "bird_hide", "sauna", "outdoor_seating"],
                "shop": ["supermarket", "convenience", "clothing", "bakery", "butcher", "hardware", "department_store", "mall", "bicycle", "books", "electronics", "florist", "furniture", "garden_centre", "gift", "greengrocer", "hairdresser", "jewelry", "mobile_phone", "optician", "pet", "shoe", "sports", "stationery", "toy", "alcohol", "beverages", "car", "car_repair", "travel_agency", "laundry", "dry_cleaning", "beauty", "deli", "tobacco", "tea", "coffee", "charity", "art", "music", "computer", "video_games", "kiosk"],
                "building": ["apartments", "house", "retail", "commercial", "office", "school", "hospital", "church", "public", "industrial", "warehouse", "residential", "university", "hotel", "dormitory", "bungalow", "detached", "semidetached_house", "terrace", "farm", "civic", "college", "stadium", "train_station", "transportation", "public_building", "kindergarten", "mosque", "synagogue", "temple", "greenhouse", "barn"],
                "healthcare": ["doctor", "dentist", "hospital", "clinic", "pharmacy", "laboratory", "therapist", "nursing_home", "veterinary", "blood_donation", "alternative", "optometrist", "physiotherapist", "podiatrist", "psychotherapist", "rehabilitation", "speech_therapist", "vaccination_centre", "audiologist", "birthing_center", "counselling", "dialysis", "hospice", "midwife", "nutritionist", "occupational_therapist", "sample_collection", "surgeon"],
                "office": ["government", "insurance", "lawyer", "estate_agent", "accountant", "financial", "travel_agent", "educational_institution", "ngo", "administrative", "advertising_agency", "architect", "association", "company", "consulting", "coworking", "diplomatic", "employment_agency", "energy_supplier", "foundation", "guide", "it", "newspaper", "political_party", "notary", "quango", "religion", "research", "surveyor", "tax", "tax_advisor", "telecommunication", "water_utility"],
                "education": ["school", "university", "college", "kindergarten", "preschool", "primary", "secondary", "high_school", "language_school", "music_school", "driving_school", "art_school", "dance_school", "culinary_school", "trade_school", "adult_education", "library", "research_institute", "training", "technical", "vocational", "special_education", "cram_school", "tutoring_center", "preparatory", "boarding_school"],
                "tourism": ["hotel", "motel", "guest_house", "hostel", "campsite", "caravan_site", "apartment", "attraction", "viewpoint", "museum", "artwork", "gallery", "theme_park", "zoo", "aquarium", "information", "picnic_site", "wilderness_hut", "alpine_hut", "resort", "chalet", "bed_and_breakfast", "trail_riding_station", "cabin", "beach_resort", "hunting_lodge", "water_park"],
                "natural": ["beach", "bay", "cape", "cliff", "crater", "fell", "forest", "grassland", "heath", "hill", "island", "land", "marsh", "mountain", "mountain_range", "peak", "plain", "ridge", "river", "rock", "scree", "scrub", "spring", "stone", "valley", "water", "wetland", "wood", "volcano", "desert", "dune", "glacier", "tree"],
                "historic": ["archaeological_site", "battlefield", "castle", "city_gate", "citywalls", "farm", "fort", "manor", "memorial", "monument", "ruins", "ship", "tomb", "wayside_cross", "wayside_shrine", "wreck", "aircraft", "aqueduct", "building", "cannon", "church", "milestone", "monastery", "pillory", "railway_car", "stone", "tank", "lighthouse", "bridge", "boundary_stone"],
                "transportation": ["bus_station", "train_station", "subway_station", "tram_stop", "ferry_terminal", "airport", "taxi_stand", "bicycle_parking", "car_parking", "car_rental", "charging_station", "fuel", "bicycle_rental", "boat_rental", "motorcycle_parking", "car_sharing", "bicycle_repair_station", "bus_stop", "platform", "railway_halt", "rest_area", "speed_camera", "toll_booth", "bridge", "tunnel"]
            }
            
            # Get default options based on selected type
            default_options = poi_options.get(poi_type, [])
            
            # Allow user to either select from common options or enter custom value
            poi_selection_method = st.radio("POI Selection Method", ["Common Options", "Custom Value"], horizontal=True)
            
            if poi_selection_method == "Common Options" and default_options:
                poi_name = st.selectbox("POI Name", default_options)
            else:
                poi_name = st.text_input("POI Name (Custom)", "library")
        
        # Add a warning for certain POI types
        if poi_type in ["natural", "historic"]:
            st.warning(f"Note: Not all {poi_type} features are available in every location. If no results are found, try a different POI type or location.")
        
        # Advanced options in expander
        with st.expander("Advanced Query Options"):
            tags_input = st.text_area("Additional tags (YAML format):", 
                                    "# Example:\n# operator: Chicago Park District")
            
            try:
                if tags_input.strip() and not tags_input.startswith('#'):
                    additional_tags = yaml.safe_load(tags_input)
                else:
                    additional_tags = {}
            except Exception as e:
                st.error(f"Error parsing tags: {str(e)}")
                additional_tags = {}

    elif input_method == "Custom Coordinates":
        st.header("Custom Coordinates Input")
        
        upload_method = st.radio(
            "Select input format:",
            ["Upload CSV/JSON File", "Manual Entry"]
        )
        
        if upload_method == "Upload CSV/JSON File":
            uploaded_file = st.file_uploader(
                "Upload coordinates file (CSV or JSON)",
                type=["csv", "json"]
            )
            
            if uploaded_file:
                # Make sure the output directory exists before saving
                os.makedirs("output/pois", exist_ok=True)
                
                # Save uploaded file temporarily
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                custom_file_path = f"output/pois/custom_coordinates{file_extension}"
                
                with open(custom_file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                st.success(f"File uploaded successfully: {uploaded_file.name}")
                
                # Preview the file
                if file_extension == ".csv":
                    df = pd.read_csv(custom_file_path)
                    st.dataframe(df.head())
                elif file_extension == ".json":
                    with open(custom_file_path, "r") as f:
                        json_data = json.load(f)
                    st.json(json_data)
        else:
            st.subheader("Enter Coordinates Manually")
            
            # Create a template for manual entry
            if "coordinates" not in st.session_state:
                st.session_state.coordinates = [{"name": "", "lat": "", "lon": "", "state": ""}]
            
            for i, coord in enumerate(st.session_state.coordinates):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.5])
                with col1:
                    coord["name"] = st.text_input(f"Name {i+1}", coord["name"], key=f"name_{i}")
                with col2:
                    coord["lat"] = st.text_input(f"Latitude {i+1}", coord["lat"], key=f"lat_{i}")
                with col3:
                    coord["lon"] = st.text_input(f"Longitude {i+1}", coord["lon"], key=f"lon_{i}")
                with col4:
                    coord["state"] = st.text_input(f"State {i+1}", coord["state"], key=f"state_{i}")
                with col5:
                    if st.button("Clear", key=f"clear_{i}"):
                        st.session_state.coordinates.pop(i)
                        st.rerun()
            
            if st.button("Add Another Location"):
                st.session_state.coordinates.append({"name": "", "lat": "", "lon": "", "state": ""})
                st.rerun()
            
            # Save manual coordinates to a file
            if st.button("Save Coordinates"):
                valid_coords = []
                for coord in st.session_state.coordinates:
                    try:
                        if coord["name"] and coord["lat"] and coord["lon"]:
                            new_coord = {
                                "id": f"manual_{len(valid_coords)}",
                                "name": coord["name"],
                                "lat": float(coord["lat"]),
                                "lon": float(coord["lon"]),
                                "tags": {}
                            }
                            valid_coords.append(new_coord)
                    except (ValueError, TypeError) as e:
                        st.error(f"Error with coordinate {coord['name']}: {str(e)}")
                        
                if valid_coords:
                    # Make sure the output directory exists
                    os.makedirs("output/pois", exist_ok=True)
                    with open("output/pois/custom_coordinates.json", "w") as f:
                        json.dump({"pois": valid_coords}, f)
                    st.success(f"Saved {len(valid_coords)} coordinates")
                else:
                    st.error("No valid coordinates to save")
    # -----------------------------------------------------------------------------
    # Helper: safe session‑state getter/setter
    # -----------------------------------------------------------------------------

    def _get_state(key, default):
        if key not in st.session_state:
            st.session_state[key] = default
        return st.session_state[key]

    # -----------------------------------------------------------------------------
    # UI – ANALYSIS RUNNER
    # -----------------------------------------------------------------------------

    st.header("Analysis")

    run_clicked = st.button(
        "Run SocialMapper Analysis",
        disabled=_get_state("analysis_running", False),
    )

    if run_clicked:
        # ---------------------------------------------------------------------
        # Initialise / reset session counters
        # ---------------------------------------------------------------------
        st.session_state.analysis_running = True
        st.session_state.current_step = 0
        results = None  # will be populated later
        tb_text = None  # to store traceback string if an error occurs

        # Ordered list of high‑level steps
        steps = [
            "Setting up",
            "Processing POIs / coordinates",
            "Generating isochrones",
            "Finding census block groups",
            "Retrieving census data",
            "Creating maps",
        ]

        # Convenience for updating a single placeholder each time
        step_placeholder = st.empty()
        progress_bar = st.progress(0, text="Initialising…")

        def update_step(idx: int, detail: str) -> None:
            """Write step text & advance progress bar."""
            # If the detail message indicates we're in a substep, show the appropriate step
            current_step = idx
            progress_fraction = (idx + 1) / len(steps)
            
            step_description = steps[idx]
            
            # Check if the detail message indicates a sub-task
            if "exporting" in detail.lower() and "csv" in detail.lower():
                # For CSV export substep, use a slightly higher progress percentage 
                # (somewhere between step 4 and 5)
                progress_fraction = (idx + 0.5) / len(steps)
            
            step_placeholder.markdown(
                f"**Step {current_step + 1}/{len(steps)} – {step_description}:** {detail}"
            )
            progress_bar.progress(progress_fraction, text=f"Step {current_step + 1}: {detail}")

        # ------------------------------------------------------------------
        # Long‑running pipeline wrapped in status block
        # ------------------------------------------------------------------
        with st.status("Running SocialMapper analysis…", expanded=True) as status:
            try:
                # STEP 1 – SETUP -----------------------------------------------------------------
                update_step(0, "Creating output directories and loading config")
                
                # Ensure all output directories exist before anything else
                output_dirs = setup_directories()
                
                # STEP 2 – POI / COORD PROCESSING ------------------------------------------------
                if input_method == "OpenStreetMap POI Query":
                    update_step(1, "Querying OpenStreetMap for Points of Interest")
                    
                    # Parse any additional tags if provided
                    additional_tags_dict = None
                    if 'tags_input' in locals() and tags_input.strip() and not tags_input.startswith('#'):
                        try:
                            additional_tags_dict = yaml.safe_load(tags_input)
                        except Exception as e:
                            st.error(f"Error parsing tags: {str(e)}")
                    
                    # Pass POI parameters directly
                    results = run_socialmapper(
                        geocode_area=geocode_area,
                        state=state_name_to_abbreviation(state),
                        city=geocode_area,  # Use geocode_area as city if not specified separately
                        poi_type=poi_type,
                        poi_name=poi_name,
                        additional_tags=additional_tags_dict,
                        travel_time=travel_time,
                        census_variables=census_variables,
                        api_key=census_api_key or None,
                        output_dirs=output_dirs,
                        progress_callback=update_step,
                        export=export
                    )
                else:
                    # Custom coordinate workflows
                    if (
                        upload_method == "Upload CSV/JSON File"
                        and 'uploaded_file' in locals() 
                        and uploaded_file is not None
                    ):
                        update_step(1, "Processing uploaded coordinates")
                        results = run_socialmapper(
                            custom_coords_path=custom_file_path,
                            travel_time=travel_time,
                            census_variables=census_variables,
                            api_key=census_api_key or None,
                            output_dirs=output_dirs,
                            progress_callback=update_step,
                            export=export
                        )
                    elif (
                        upload_method == "Manual Entry"
                        and Path("output/pois/custom_coordinates.json").exists()
                    ):
                        update_step(1, "Processing manually entered coordinates")
                        results = run_socialmapper(
                            custom_coords_path="output/pois/custom_coordinates.json",
                            travel_time=travel_time,
                            census_variables=census_variables,
                            api_key=census_api_key or None,
                            output_dirs=output_dirs,
                            progress_callback=update_step,
                            export=export
                        )
                    else:
                        raise ValueError("No valid coordinates provided – please upload or enter coordinates first.")

                status.update(label="Analysis completed successfully!", state="complete")

            except ValueError as err:
                status.update(label="Analysis failed", state="error")
                if "No POIs found in input data" in str(err):
                    st.error("No Points of Interest found with your search criteria. Please try a different search or location.")
                else:
                    st.error(f"An error occurred: {err}")
                tb_text = traceback.format_exc()
            except Exception as err:
                status.update(label="Analysis failed", state="error")
                st.error(f"An error occurred: {err}")
                tb_text = traceback.format_exc()

            finally:
                st.session_state.analysis_running = False

        # ------------------------------------------------------------------
        # If we captured a traceback, show it *outside* the status container
        # ------------------------------------------------------------------
        if tb_text:
            with st.expander("Show error details"):
                st.code(tb_text)

        # ------------------------------------------------------------------
        # Display results (only if pipeline ran and produced output)
        # ------------------------------------------------------------------
        if results:
            st.header("Results")

            # ---- POIs tab ---------------------------------------------------
            poi_data = results.get("poi_data")
            if poi_data:
                with st.expander("Points of Interest", expanded=True):
                    if isinstance(poi_data, dict) and 'pois' in poi_data:
                        poi_df = pd.DataFrame(poi_data.get("pois", []))
                        if not poi_df.empty:
                            st.dataframe(poi_df)
                        else:
                            st.warning("No POIs found in the results.")
                    elif isinstance(poi_data, str) and os.path.exists(poi_data):
                        # For backward compatibility, if poi_data is a file path
                        with open(poi_data, 'r') as f:
                            poi_json = json.load(f)
                        poi_df = pd.DataFrame(poi_json.get("pois", []))
                        if not poi_df.empty:
                            st.dataframe(poi_df)
                        else:
                            st.warning("No POIs found in the results.")
                    else:
                        st.warning("POI data not found in the expected format.")

            # ---- Maps grid --------------------------------------------------
            map_files = results.get("maps", [])
            if map_files:
                st.subheader("Demographic Maps")
                cols = st.columns(2)
                for i, map_file in enumerate(map_files):
                    if Path(map_file).exists():
                        cols[i % 2].image(map_file, use_container_width=True)
            else:
                st.info("No maps were generated by this run.")

            # ---- CSV export --------------------------------------------------
            csv_path = results.get("csv_data")
            if csv_path and Path(csv_path).exists():
                st.subheader("Census Data Export")
                st.success(f"Census data with travel distances exported to CSV")
                with st.expander("Preview CSV data"):
                    csv_df = pd.read_csv(csv_path)
                    st.dataframe(csv_df.head(10))
                
                # Provide download button
                with open(csv_path, "rb") as file:
                    st.download_button(
                        label="Download CSV data",
                        data=file,
                        file_name=os.path.basename(csv_path),
                        mime="text/csv"
                    )

    # Display about section and links to other pages
    st.sidebar.markdown("---")
    st.sidebar.header("Navigation")
    st.sidebar.markdown("[Documentation](https://github.com/mihiarc/socialmapper)")

    with st.expander("About SocialMapper"):
        st.markdown("""
    # 🏘️ SocialMapper: Explore Your Community Connections. 🏘️

    SocialMapper is an open-source Python toolkit that helps you understand how people connect with the important places in their community. Imagine taking a key spot like your local community center or school and seeing exactly what areas are within a certain travel time – whether it's a quick walk or a longer drive. SocialMapper does just that.

    But it doesn't stop at travel time. SocialMapper also shows you the characteristics of the people who live within these accessible areas, like how many people live there and what the average income is. This helps you see who can easily reach vital community resources and identify any gaps in access.

    Whether you're looking at bustling city neighborhoods or more spread-out rural areas, SocialMapper provides clear insights for making communities better, planning services, and ensuring everyone has good access to the places that matter.

    With plans to expand and explore our connection to the natural world, SocialMapper is a tool for understanding people, places, and the environment around us.

    Discover the connections in your community with SocialMapper – where location brings understanding.

    ## Features

    - **Finding Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
    - **Generating Travel Time Areas** - Create isochrones showing areas reachable within a certain travel time
    - **Identifying Census Block Groups** - Determine which census block groups intersect with these areas
    - **Retrieving Demographic Data** - Pull census data for the identified areas
    - **Visualizing Results** - Generate maps showing the demographic variables around the POIs

        
        For more information, visit the [GitHub repository](https://github.com/mihiarc/socialmapper).
        """)

if __name__ == "__main__":
    run_app() 