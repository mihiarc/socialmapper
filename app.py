import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from pathlib import Path
import yaml
import json
from dotenv import load_dotenv

# Import the community mapper modules
from community_mapper import (
    run_community_mapper,
    parse_custom_coordinates,
    setup_directories,
    load_poi_config
)

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Community Mapper",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("Community Mapper")
st.markdown("""
This application helps you analyze demographics around community resources using:
1. Points of Interest (POIs) from OpenStreetMap
2. Travel time isochrones around those POIs
3. Census block groups and demographic data
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
    default=['total_population', 'median_household_income'],
    format_func=lambda x: available_variables[x]
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
        state = st.text_input("State", "North Carolina")
    
    with col2:
        poi_type = st.selectbox(
            "POI Type",
            ["amenity", "leisure", "shop", "building", "healthcare", "office"]
        )
        poi_name = st.text_input("POI Name", "library")
    
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

    # Create temporary config file
    config = {
        "geocode_area": geocode_area,
        "state": state,
        "city": geocode_area,
        "type": poi_type,
        "name": poi_name
    }
    
    if additional_tags:
        config["tags"] = additional_tags
    
    config_path = "temp_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

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
            # Save uploaded file temporarily
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            temp_file_path = f"temp_coordinates{file_extension}"
            
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            st.success(f"File uploaded successfully: {uploaded_file.name}")
            
            # Preview the file
            if file_extension == ".csv":
                df = pd.read_csv(temp_file_path)
                st.dataframe(df.head())
            elif file_extension == ".json":
                with open(temp_file_path, "r") as f:
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
                if st.button("Remove", key=f"remove_{i}"):
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
                    if coord["name"] and coord["lat"] and coord["lon"] and coord["state"]:
                        valid_coords.append({
                            "id": f"manual_{len(valid_coords)}",
                            "name": coord["name"],
                            "lat": float(coord["lat"]),
                            "lon": float(coord["lon"]),
                            "state": coord["state"],
                            "tags": {}
                        })
                except (ValueError, TypeError) as e:
                    st.error(f"Error with coordinate {coord['name']}: {str(e)}")
                    
            if valid_coords:
                with open("temp_coordinates.json", "w") as f:
                    json.dump({"pois": valid_coords}, f)
                st.success(f"Saved {len(valid_coords)} coordinates")
            else:
                st.error("No valid coordinates to save")

# Run analysis button
st.header("Analysis")
if st.button("Run Community Mapper Analysis"):
    with st.spinner("Running analysis..."):
        try:
            # Setup output directories
            output_dirs = setup_directories()
            
            # Determine which method to use
            if input_method == "OpenStreetMap POI Query":
                # Run with OSM query
                results = run_community_mapper(
                    config_path=config_path,
                    travel_time=travel_time,
                    census_variables=census_variables,
                    api_key=census_api_key if census_api_key else None,
                    output_dirs=output_dirs
                )
            else:  # Custom Coordinates
                if upload_method == "Upload CSV/JSON File" and uploaded_file:
                    # Run with uploaded file
                    results = run_community_mapper(
                        custom_coords_path=temp_file_path,
                        travel_time=travel_time,
                        census_variables=census_variables,
                        api_key=census_api_key if census_api_key else None,
                        output_dirs=output_dirs
                    )
                elif upload_method == "Manual Entry" and os.path.exists("temp_coordinates.json"):
                    # Run with manually entered coordinates
                    results = run_community_mapper(
                        custom_coords_path="temp_coordinates.json",
                        travel_time=travel_time,
                        census_variables=census_variables,
                        api_key=census_api_key if census_api_key else None,
                        output_dirs=output_dirs
                    )
                else:
                    st.error("No valid coordinates provided")
                    st.stop()
                    
            st.success("Analysis completed successfully!")
            
            # Display results
            st.header("Results")
            
            # POIs tab
            if os.path.exists(results.get("poi_file", "")):
                with st.expander("Points of Interest", expanded=True):
                    with open(results["poi_file"], "r") as f:
                        poi_data = json.load(f)
                    
                    # Convert to DataFrame for display
                    poi_list = poi_data.get("pois", [])
                    if poi_list:
                        poi_df = pd.DataFrame(poi_list)
                        st.dataframe(poi_df)
                    else:
                        st.warning("No POIs found in the results")
            
            # Maps display
            st.subheader("Demographic Maps")
            map_files = results.get("map_files", [])
            
            if map_files:
                # Display maps in a grid
                cols = st.columns(2)
                for i, map_file in enumerate(map_files):
                    if os.path.exists(map_file):
                        cols[i % 2].image(map_file)
            else:
                st.warning("No maps were generated")
                
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")

# Display about section and links to other pages
st.sidebar.markdown("---")
st.sidebar.header("Navigation")
st.sidebar.markdown("[Examples](./01_Examples)")
st.sidebar.markdown("[Documentation](https://github.com/mihiarc/community-mapper)")

with st.expander("About Community Mapper"):
    st.markdown("""
    ## Community Mapper
    
    A Python toolkit for mapping community resources and analyzing demographic data around them.
    
    ### Overview
    
    Community Mapper integrates several geospatial analysis tools to help understand the demographics 
    of areas around community amenities. It provides an end-to-end pipeline for:
    
    1. **Finding Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
    2. **Generating Travel Time Areas** - Create isochrones showing areas reachable within a certain travel time
    3. **Identifying Census Block Groups** - Determine which census block groups intersect with these areas
    4. **Retrieving Demographic Data** - Pull census data for the identified areas
    5. **Visualizing Results** - Generate maps showing the demographic variables around the POIs
    
    ### Get Started
    
    1. Select your input method (OpenStreetMap or Custom Coordinates)
    2. Configure your parameters
    3. Run the analysis
    4. Explore the results
    
    For more information, visit the [GitHub repository](https://github.com/mihiarc/community-mapper).
    """) 