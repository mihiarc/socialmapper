import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path

st.set_page_config(
    page_title="SocialMapper - Examples",
    page_icon="🗺️",
    layout="wide"
)

st.title("SocialMapper - Examples")
st.markdown("""
This page provides examples of how to use the SocialMapper tool for different scenarios.
You can explore these examples to understand what's possible and then apply similar approaches to your own projects.
""")

# Check if example files exist, if not display a message
examples_dir = Path("examples")
example_csv = examples_dir / "streamlit_example.csv"
example_json = examples_dir / "streamlit_example.json"

if not example_csv.exists() or not example_json.exists():
    st.warning("Example files not found. Please create the example files in the examples directory.")
    st.stop()

# Example Use Cases
st.header("Example Use Cases")

with st.expander("1. Analyzing Library Access", expanded=True):
    st.markdown("""
    ### Analyzing Access to Libraries
    
    Libraries are essential community resources that provide access to information, technology, and educational programs.
    
    #### Example Configuration:
    - **POI Type**: `amenity`
    - **POI Name**: `library`
    - **Travel Time**: 15 minutes
    - **Census Variables**: 
      - Total Population
      - Median Household Income
      - Education (Bachelor's or higher)
    
    #### Questions this analysis can answer:
    - How many people live within a 15-minute travel time of libraries?
    - What is the income distribution of areas with library access?
    - Are libraries accessible to all demographic groups?
    """)
    
    # Show example CSV data
    st.subheader("Sample Library Data (CSV)")
    df = pd.read_csv(example_csv)
    library_df = df[df['name'].str.contains('Library')]
    st.dataframe(library_df, use_container_width=True)
    
    st.markdown("---")

with st.expander("2. Assessing Healthcare Access", expanded=False):
    st.markdown("""
    ### Assessing Access to Healthcare Facilities
    
    Access to healthcare is crucial for community well-being. This example focuses on hospitals.
    
    #### Example Configuration:
    - **POI Type**: `amenity`
    - **POI Name**: `hospital`
    - **Travel Time**: 20 minutes
    - **Census Variables**: 
      - Total Population
      - Median Age
      - Hispanic Population 
      
    #### Questions this analysis can answer:
    - What is the demographic profile of areas within a 20-minute travel time of hospitals?
    - Are there disparities in hospital access based on age or ethnicity?
    """)
    
    # Show example JSON data
    st.subheader("Sample Hospital Data (JSON)")
    with open(example_json, 'r') as f:
        data = json.load(f)
    health_df = pd.DataFrame(data['pois']) # Assuming 'pois' is the key
    health_df = health_df[health_df['tags'].apply(lambda x: x.get('amenity') == 'hospital')]
    st.dataframe(health_df, use_container_width=True)
    st.markdown("---")

with st.expander("3. Evaluating Green Space Availability", expanded=False):
    st.markdown("""
    ### Evaluating Access to Parks and Green Spaces
    
    Parks provide recreational opportunities and contribute to public health.
    
    #### Example Configuration:
    - **POI Type**: `leisure`
    - **POI Name**: `park`
    - **Travel Time**: 10 minutes
    - **Census Variables**: 
      - Total Population
      - Housing Units
      
    #### Questions this analysis can answer:
    - How densely populated are the areas with easy access to parks?
    - Is there a correlation between housing density and park availability?
    """)
    
    # Show example merged data
    st.subheader("Sample Park Data (CSV)") # This was using df, which is the full example_csv
    # Assuming we want to filter for parks from the CSV for this example as well
    park_df = df[df['name'].str.contains('Park', case=False, na=False)] 
    st.dataframe(park_df, use_container_width=True)
    st.markdown("---")

st.sidebar.info("These examples use pre-defined data. Run your own analyses using the 'Home' page.")

# How to use these examples
st.header("How to Use These Examples")
st.markdown("""
1. **Copy Configuration**: Use the example configurations above as starting points for your own analysis.
2. **Load Sample Data**: You can use the provided sample data files (`examples/streamlit_example.csv` or `examples/streamlit_example.json`) to test the app.
3. **Adapt to Your Needs**: Modify the parameters, locations, or census variables to suit your specific research questions.

### Steps to Run an Example:

1. Go back to the home page
2. Select the appropriate input method:
   - For OpenStreetMap queries, use the example configurations above
   - For custom coordinates, upload one of the example files
3. Adjust the travel time and census variables as needed
4. Click "Run Community Mapper Analysis"
""")

# Download example files
st.header("Download Example Files")
col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="Download Example CSV",
        data=open(example_csv, 'rb').read(),
        file_name="example_coordinates.csv",
        mime="text/csv"
    )

with col2:
    st.download_button(
        label="Download Example JSON",
        data=open(example_json, 'rb').read(),
        file_name="example_coordinates.json",
        mime="application/json"
    )

# Link back to main app
st.markdown("""
---
[Go back to the main app](./) to start your analysis
""") 