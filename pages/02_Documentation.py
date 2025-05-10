import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="SocialMapper - Documentation",
    page_icon="🗺️",
    layout="wide"
)

st.title("SocialMapper - Documentation")
st.markdown("""
This page explains how the SocialMapper works and guides you through its features in detail.
""")

# System Architecture
st.header("System Architecture")
st.markdown("""
The SocialMapper follows a pipeline architecture where each component builds on the output of the previous one:

1. **POI Query**: Obtains Points of Interest (POIs) from OpenStreetMap or custom coordinates
2. **Isochrone Generation**: Creates travel time polygons around each POI
3. **Block Group Identification**: Finds census block groups that intersect with isochrones
4. **Census Data Retrieval**: Gets demographic data for those block groups
5. **Map Visualization**: Generates maps showing the demographic data
""")

# Components
st.header("Components")

with st.expander("POI Query Module", expanded=True):
    st.markdown("""
    ### POI Query Module
    
    This module is responsible for obtaining Points of Interest (POIs) data:
    
    - **OpenStreetMap Queries**: Uses the Overpass API to find POIs based on tags
    - **Custom Coordinates**: Allows users to provide their own coordinates in CSV or JSON format
    
    #### Supported POI Types from OpenStreetMap:
    
    | Type | Examples | OSM Tags |
    |------|----------|----------|
    | Amenities | Libraries, Schools, Hospitals | `amenity=library`, `amenity=school`, `amenity=hospital` |
    | Leisure | Parks, Sports Centers | `leisure=park`, `leisure=sports_centre` |
    | Shops | Supermarkets, Pharmacies | `shop=supermarket`, `shop=pharmacy` |
    | Healthcare | Clinics, Doctors | `healthcare=doctor`, `healthcare=clinic` |
    
    #### Requirements for Custom Coordinates:
    
    Custom coordinates must include latitude, longitude, and state information for each point.
    """)
    
with st.expander("Isochrone Module"):
    st.markdown("""
    ### Isochrone Module
    
    This module generates travel time polygons around each POI:
    
    - Uses the OpenStreetMap network to calculate travel times
    - Supports different travel modes (walking, driving, cycling)
    - Creates polygon geometries representing areas reachable within the specified travel time
    
    #### Parameters:
    
    - **Travel Time**: Specified in minutes (typically 5-60 minutes)
    - **Travel Mode**: How people travel (walking, driving, cycling)
    - **Network Type**: Road network characteristics
    
    The isochrones are generated using the OSMnx library, which interfaces with the OpenStreetMap network.
    """)
    
with st.expander("Block Group Module"):
    st.markdown("""
    ### Block Group Module
    
    This module identifies census block groups that intersect with the isochrones:
    
    - Downloads block group geometries from the Census Bureau
    - Performs spatial joins to find which block groups intersect with isochrones
    - Calculates the proportion of each block group that falls within the isochrone
    
    Census block groups are the smallest geographical unit for which the Census Bureau publishes sample data.
    """)
    
with st.expander("Census Data Module"):
    st.markdown("""
    ### Census Data Module
    
    This module retrieves demographic data for the identified block groups:
    
    - Uses the Census Bureau's API to fetch data
    - Supports various demographic variables (population, income, education, etc.)
    - Aggregates data based on the proportion of block groups within isochrones
    
    #### Supported Census Variables:
    
    | Description | Community Mapper Name | Census Variable |
    |-------------|----------------------|-----------------|
    | Total Population | total_population | B01003_001E |
    | Median Household Income | median_household_income | B19013_001E |
    | Median Home Value | median_home_value | B25077_001E |
    | Median Age | median_age | B01002_001E |
    | White Population | white_population | B02001_002E |
    | Black Population | black_population | B02001_003E |
    | Hispanic Population | hispanic_population | B03003_003E |
    | Housing Units | housing_units | B25001_001E |
    | Education (Bachelor's+) | education_bachelors_plus | B15003_022E + B15003_023E + B15003_024E + B15003_025E |
    
    A Census API key is required to fetch this data. You can get one for free at https://api.census.gov/data/key_signup.html
    """)
    
with st.expander("Visualization Module"):
    st.markdown("""
    ### Visualization Module
    
    This module generates maps showing the demographic data:
    
    - Creates choropleth maps showing the distribution of demographic variables
    - Highlights block groups within isochrones
    - Marks POI locations on the maps
    
    #### Map Features:
    
    - Base map from contextily (OpenStreetMap)
    - Color-coded block groups based on demographic variables
    - POI markers with labels
    - Scale bar and north arrow
    - Legend explaining the color scale
    
    Maps are saved as PNG files and can be viewed in the app or downloaded for use in reports.
    """)

with st.expander("Data Export Module"):
    st.markdown("""
    ### Data Export Module
    
    This module exports census data to CSV format for further analysis:
    
    - Exports all selected census variables for each block group
    - Includes geographic identifiers (block group ID, county FIPS, state FIPS)
    - Calculates and includes travel distances in both kilometers and miles
    - Uses human-readable but standardized names (lowercase with underscores)
    
    #### CSV File Structure:
    
    | Column | Description |
    |--------|-------------|
    | census_block_group | Census Block Group GEOID (12-digit identifier) |
    | state_fips | State FIPS code (2-digit identifier) |
    | county_fips | County FIPS code (5-digit identifier) |
    | tract | Census tract component of the GEOID |
    | block_group | Block group component of the GEOID |
    | poi_id | ID of the point of interest |
    | poi_name | Name of the point of interest |
    | travel_time_minutes | Travel time limit in minutes |
    | avg_travel_speed_kmh | Average travel speed used in isochrone calculations (kilometers per hour) |
    | avg_travel_speed_mph | Average travel speed used in isochrone calculations (miles per hour) |
    | travel_distance_km | Distance in kilometers from block group centroid to nearest POI |
    | travel_distance_miles | Distance in miles from block group centroid to nearest POI |
    | area_within_travel_time_pct | Percentage of block group area within the travel time area |
    | [census variables] | Values for each selected census variable using standardized names |
    
    #### Technical Details:
    
    - Distance calculation uses Albers Equal Area projection (EPSG:5070) for accurate measurements across the US
    - For areas with multiple POIs, the distance to the nearest POI is used
    - Census variables use lowercase names with underscores (e.g., "total_population" instead of "B01003_001E")
    - Columns are organized in a logical order with identifiers first, followed by travel metrics and census data
    - CSV files are saved in the `output/csv/` directory with the same base filename as other outputs
    
    This feature enables deeper analysis in statistical software, spreadsheets, or other tools.
    """)

# Using the API
st.header("Advanced: Using the API")
st.markdown("""
For advanced users or programmatic access, you can use the Community Mapper as a Python library:

```python
from community_mapper import run_community_mapper

# Example with OpenStreetMap query
results = run_community_mapper(
    config_path="my_config.yaml",
    travel_time=15,
    census_variables=["total_population", "median_household_income"],
    api_key="YOUR_CENSUS_API_KEY",
    export=True  # Export to CSV (default is True)
)

# Example with custom coordinates
results = run_community_mapper(
    custom_coords_path="my_coordinates.csv",
    travel_time=15,
    census_variables=["total_population", "median_household_income"],
    api_key="YOUR_CENSUS_API_KEY",
    export=True  # Export to CSV (default is True)
)
```

The `run_community_mapper` function returns a dictionary with paths to the generated files:

```python
{
    "poi_file": "output/pois/pois_YYYY-MM-DD_HHMMSS.json",
    "isochrone_file": "output/isochrones/isochrones_YYYY-MM-DD_HHMMSS.geojson",
    "block_group_file": "output/block_groups/block_groups_YYYY-MM-DD_HHMMSS.geojson",
    "census_data_file": "output/census_data/census_data_YYYY-MM-DD_HHMMSS.geojson",
    "map_files": [
        "output/maps/map_total_population_YYYY-MM-DD_HHMMSS.png",
        "output/maps/map_median_household_income_YYYY-MM-DD_HHMMSS.png"
    ],
    "csv_data": "output/csv/census_data_YYYY-MM-DD_HHMMSS.csv"
}
```
""")

# Troubleshooting
st.header("Troubleshooting")
st.markdown("""
### Common Issues

#### No POIs Found
- Check your query terms and location spelling
- Try broadening your search (e.g., use a more general POI type)
- Verify that the area has OSM data available

#### Census API Issues
- Ensure your API key is valid and properly set
- Check that you're not exceeding API rate limits
- Verify that the requested variables are available

#### Isochrone Generation Problems
- For very large areas, try reducing the travel time
- Check that the network is connected (islands or remote areas may cause issues)
- For large cities, consider processing smaller areas separately

#### Performance Tips
- Limit the number of POIs for faster processing
- Start with a smaller travel time to test your query
- Process one demographic variable at a time for quicker results
""")

# Resources
st.header("Resources")
st.markdown("""
### Additional Resources

- [Census API Documentation](https://www.census.gov/data/developers/guidance/api-user-guide.html)
- [OpenStreetMap Wiki: Map Features](https://wiki.openstreetmap.org/wiki/Map_features)
- [OpenStreetMap Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [GeoPandas Documentation](https://geopandas.org/en/stable/)
- [Streamlit Documentation](https://docs.streamlit.io/)

### Getting Help

If you encounter issues not covered in this documentation, please:

1. Check the [GitHub repository](https://github.com/mihiarc/community-mapper) for known issues
2. Review the troubleshooting section above
3. File a GitHub issue with details about your problem
""")

# Link back to main app
st.markdown("""
---
[Go back to the main app](./) to start your analysis
""") 