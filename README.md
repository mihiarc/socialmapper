# 🏘️ SocialMapper: Explore Community Connections

[![PyPI version](https://badge.fury.io/py/socialmapper.svg)](https://badge.fury.io/py/socialmapper)
[![Python Versions](https://img.shields.io/pypi/pyversions/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Status](https://img.shields.io/pypi/status/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![Downloads](https://static.pepy.tech/badge/socialmapper)](https://pepy.tech/project/socialmapper)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://socialmapper.streamlit.app)

SocialMapper is an open-source Python toolkit that helps you understand how people connect with the important places in their community. Imagine taking a key spot like your local shopping center or school and seeing exactly what areas are within a certain travel time – whether it's a quick walk or a longer drive. SocialMapper does just that.

But it doesn't stop at travel time. SocialMapper also shows you the characteristics of the people who live within these accessible areas, like how many people live there and what the average income is. This helps you see who can easily reach vital community resources and identify any gaps in access.

Whether you're looking at bustling city neighborhoods or more spread-out rural areas, SocialMapper provides clear insights for making communities better, planning services, and ensuring everyone has good access to the places that matter.

With plans to expand and explore our connection to the natural world, SocialMapper is a tool for understanding people, places, and the environment around us.

## 🚀 Try SocialMapper Now!

**[Launch the SocialMapper Streamlit App](https://socialmapper.streamlit.app)** - Explore community connections with our interactive web app - no coding required!


**Total Population Within 15-Minute Travel Time**

![Total Population Map](output/maps/fuquay-varina_amenity_library_15min_B01003_001E_map.png)

## What's New in v0.4.0-beta

We're excited to announce our beta release with these new features:

- **Live Streamlit App** - Now available at [socialmapper.streamlit.app](https://socialmapper.streamlit.app)
- **Interactive Maps** - Explore data with interactive Folium maps in the Streamlit app
- **Distance Data Export** - Export travel distance data for deeper analysis
- **CSV Export** - Easily share and analyze your data in spreadsheet applications
- **Runtime Optimizations** - Significantly improved performance for faster analysis

## Features

- **Finding Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
- **Generating Travel Time Areas** - Create isochrones showing areas reachable within a certain travel time
- **Identifying Census Block Groups** - Determine which census block groups intersect with these areas
- **Calculating Travel Distance** - Measure the travel distance along roads from the point of interest to the block group centroids
- **Retrieving Demographic Data** - Pull census data for the identified areas
- **Interactive Visualizations** - Generate both static and interactive maps showing demographic variables around POIs
- **Data Export** - Export census data with travel distances to CSV for further analysis

## Installation

SocialMapper is available on PyPI. Install it easily with pip:

```bash
pip install socialmapper==0.4.0b0
```

## Using SocialMapper

### Using the Streamlit App

The easiest way to use SocialMapper is through the Streamlit web app:

**Option 1: Use our hosted app (Recommended)**
Visit [socialmapper.streamlit.app](https://socialmapper.streamlit.app) - no installation required!

**Option 2: Run locally**
```bash
# Run the Streamlit app
python -m socialmapper.streamlit_app
```

The app will open in your web browser at http://localhost:8501 (if it doesn't open automatically).

The Streamlit app allows you to:
- Query OpenStreetMap for points of interest or use your own coordinates
- Set travel times and select demographic variables 
- Visualize results with interactive maps
- Export data to CSV for further analysis in other tools
- No coding experience required!

It's perfect for:
- Urban planners analyzing access to public services
- Community organizations studying resource distribution 
- Researchers examining demographic patterns around facilities
- Anyone who wants to understand demographics around points of interest

### Using the Command-line Interface

SocialMapper can also be used directly from the command line:

```bash
# Show help
socialmapper --help

# Run with OpenStreetMap POI query
socialmapper --poi --geocode-area "Chicago" --state "Illinois" --poi-type "amenity" --poi-name "library" --travel-time 15 --census-variables total_population median_household_income

# Run with custom coordinates
socialmapper --custom-coords "path/to/coordinates.csv" --travel-time 20 --census-variables total_population median_household_income
```

### Using the Python API

You can import SocialMapper in your own Python code:

```python
from socialmapper import run_socialmapper

# Run with POI query
results = run_socialmapper(
    geocode_area="Chicago",
    state="IL",
    poi_type="amenity",
    poi_name="library",
    travel_time=15,
    census_variables=["total_population", "median_household_income"]
)

# Run with custom coordinates
results = run_socialmapper(
    custom_coords_path="path/to/coordinates.csv",
    travel_time=20,
    census_variables=["total_population", "median_household_income"]
)
```

## Creating Your Own Community Maps: Step-by-Step Guide

### 1. Define Your Points of Interest

You can specify points of interest either through the interactive Streamlit dashboard or with direct command-line parameters.

#### Option A: Using the Streamlit Dashboard (Recommended)

The easiest way to create maps is to use the Streamlit dashboard:

```bash
python -m socialmapper.streamlit_app
```

This provides an interactive interface where you can:
- Select POI types and names from dropdown menus
- Choose your location and state
- Set travel time and census variables
- View results in a user-friendly format

#### Option B: Command Line with Direct Parameters

You can run the tool directly with POI parameters:

```bash
socialmapper --poi --geocode-area "Fuquay-Varina" --state "North Carolina" --poi-type "amenity" --poi-name "library" --travel-time 15 --census-variables total_population median_household_income
```

### POI Types and Names Reference

Regardless of which method you use, you'll need to specify POI types and names. Common OpenStreetMap POI combinations:

- Libraries: `poi-type: "amenity"`, `poi-name: "library"`
- Schools: `poi-type: "amenity"`, `poi-name: "school"`
- Hospitals: `poi-type: "amenity"`, `poi-name: "hospital"`
- Parks: `poi-type: "leisure"`, `poi-name: "park"`
- Supermarkets: `poi-type: "shop"`, `poi-name: "supermarket"`
- Pharmacies: `poi-type: "amenity"`, `poi-name: "pharmacy"`

Check out the OpenStreetMap Wiki for more on map features: https://wiki.openstreetmap.org/wiki/Map_features

For more specific queries, you can add additional tags (through the Streamlit interface or in a YAML format with command-line):
```yaml
# Example tags (can be specified in the Streamlit interface):
operator: Chicago Park District
opening_hours: 24/7
```

### 2. Choose Your Target States

If you're using direct POI parameters, you should provide the state where your analysis should occur. This ensures accurate census data selection.

For areas near state borders or POIs spread across multiple states, you don't need to do anything special - the tool will automatically identify the appropriate census data.

### 3. Select Demographics to Analyze

Choose which census variables you want to analyze. Some useful options:

| Description                      | Notes                                      | SocialMapper Name    | Census Variable                                         |
|-------------------------------   |--------------------------------------------|--------------------------|----------------------------------------------------|
| Total Population                 | Basic population count                     | total_population         | B01003_001E                                        |
| Median Household Income          | In dollars                                 | median_income            | B19013_001E                                        |
| Median Home Value                | For owner-occupied units                   | median_home_value        | B25077_001E                                        |
| Median Age                       | Overall median age                         | median_age               | B01002_001E                                        |
| White Population                 | Population identifying as white alone      | white_population         | B02001_002E                                        |
| Black Population                 | Population identifying as Black/African American alone | black_population | B02001_003E                                     |
| Hispanic Population              | Hispanic or Latino population of any race  | hispanic_population      | B03003_003E                                        |
| Housing Units                    | Total housing units                        | housing_units            | B25001_001E                                        |
| Education (Bachelor's or higher) | Sum of education categories                | education_bachelors_plus | B15003_022E + B15003_023E + B15003_024E + B15003_025E   |

### 4. Run the SocialMapper

After specifying your POIs and census variables, SocialMapper will:
- Generate isochrones showing travel time areas
- Identify census block groups within these areas
- Retrieve demographic data for these block groups
- Create maps visualizing the demographics
- Export data to CSV for further analysis

The results will be found in the `output/` directory:
- GeoJSON files with isochrones in `output/isochrones/`
- GeoJSON files with block groups in `output/block_groups/`
- GeoJSON files with census data in `output/census_data/`
- PNG map visualizations in `output/maps/`
- CSV files with census data and travel distances in `output/csv/`

### Example Projects

Here are some examples of community mapping projects you could create:

1. **Food Desert Analysis**: Map supermarkets with travel times and income data to identify areas with limited food access.
   ```bash
   socialmapper --poi --geocode-area "Chicago" --state "Illinois" --poi-type "shop" --poi-name "supermarket" --travel-time 20 --census-variables total_population median_household_income
   ```

2. **Healthcare Access**: Map hospitals and clinics with population and age demographics.
   ```bash
   socialmapper --poi --geocode-area "Los Angeles" --state "California" --poi-type "amenity" --poi-name "hospital" --travel-time 30 --census-variables total_population median_age
   ```

3. **Educational Resource Distribution**: Map schools and libraries with educational attainment data.
   ```bash
   socialmapper --poi --geocode-area "Boston" --state "Massachusetts" --poi-type "amenity" --poi-name "school" --travel-time 15 --census-variables total_population education_bachelors_plus
   ```

4. **Park Access Equity**: Map parks with demographic and income data to assess equitable access.
   ```bash
   socialmapper --poi --geocode-area "Miami" --state "Florida" --poi-type "leisure" --poi-name "park" --travel-time 10 --census-variables total_population median_household_income white_population black_population
   ```

## Development

For development, install with the development dependencies:

```bash
pip install -e ".[dev,streamlit]"
```

### Troubleshooting

- **No POIs found**: Check your POI configuration. Try making the query more general or verify that the location name is correct.
- **Census API errors**: Ensure your API key is valid and properly set as an environment variable.
- **Isochrone generation issues**: For very large areas, try reducing the travel time to avoid timeouts.
- **Missing block groups**: The tool should automatically identify the appropriate states based on the POI locations.