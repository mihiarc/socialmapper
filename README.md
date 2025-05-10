# 🏘️ SocialMapper: Explore Community Connections.

SocialMapper is an open-source Python toolkit that helps you understand how people connect with the important places in their community. Imagine taking a key spot like your local shopping center or school and seeing exactly what areas are within a certain travel time – whether it's a quick walk or a longer drive. SocialMapper does just that.

But it doesn't stop at travel time. SocialMapper also shows you the characteristics of the people who live within these accessible areas, like how many people live there and what the average income is. This helps you see who can easily reach vital community resources and identify any gaps in access.

Whether you're looking at bustling city neighborhoods or more spread-out rural areas, SocialMapper provides clear insights for making communities better, planning services, and ensuring everyone has good access to the places that matter.

With plans to expand and explore our connection to the natural world, SocialMapper is a tool for understanding people, places, and the environment around us.

**Total Population Within 15-Minute Travel Time**

![Total Population Map](output/maps/fuquay-varina_amenity_library_15min_B01003_001E_map.png)

**Median Household Income Within 15-Minute Travel Time**

![Median Household Income Map](output/maps/fuquay-varina_amenity_library_15min_B19013_001E_map.png)

## Features

- **Finding Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
- **Generating Travel Time Areas** - Create isochrones showing areas reachable within a certain travel time
- **Identifying Census Block Groups** - Determine which census block groups intersect with these areas
- **Retrieving Demographic Data** - Pull census data for the identified areas
- **Visualizing Results** - Generate maps showing the demographic variables around the POIs
- **Data Export** - Export census data with travel distances to CSV for further analysis

## ⚠️ PRE-RELEASE ⚠️
This is an alpha release (v0.3.0-alpha). Major features are still missing and those implemented may contain significant bugs. Not recommended for production use.

## New in v0.3.0-alpha -- **SocialMapper Interactive Dashboard**

We now provide a Streamlit web app as a user-friendly interface to the Community Mapper tool. The web app allows you to:

- Query OpenStreetMap for points of interest or use your own coordinates
- Set travel times and select demographic variables 
- Visualize results with interactive maps
- Export data to CSV for further analysis in other tools
- No coding experience required!

### Running the Streamlit App

1. Make sure you've installed dependencies with `uv pip install -r requirements.txt`
2. Run the app with `streamlit run Home.py`
3. Open your browser to http://localhost:8501 (if it doesn't open automatically)

The app provides an intuitive interface to configure your community mapping project, run the analysis, and visualize the results - all without writing a single line of code. It's perfect for:

- Urban planners analyzing access to public services
- Community organizations studying resource distribution 
- Researchers examining demographic patterns around facilities
- Anyone who wants to understand demographics around points of interest

For more information, see [STREAMLIT_README.md](STREAMLIT_README.md).

## Installation

### Prerequisites

- Python 3.9 or later
- A Census API key (get one at https://api.census.gov/data/key_signup.html)

### Easy Setup (Linux/Mac/Windows)

We provide a setup script that automates the installation process:

1. Clone this repository into your preferred location:
   ```bash
   git clone https://github.com/mihiarc/community-mapper.git
   cd community-mapper
   ```

#### For Linux/Mac:
2. Run the setup script:
   ```bash
   chmod +x setup_env.sh
   ./setup_env.sh
   ```

#### For Windows:
Simply double-click the `setup_env.bat` file in the project directory, or run it from Command Prompt:
```
setup_env.bat
```

This will:
    - Check if Python is installed
    - Install uv if needed
    - Create a virtual environment
    - Install all dependencies
    - Set up the required directory structure
    - Create a template .env file for your Census API key

After the script completes:
1. Edit the `.env` file in a text editor like notepad, and add your Census API key
2. Use the Command Prompt to activate the environment:
    ```
    .venv\Scripts\activate
    ```
3. Run the Streamlit app:
    ```
    streamlit run Home.py
    ```

## Creating Your Own Community Maps: Step-by-Step Guide

### 1. Define Your Points of Interest

You can specify points of interest either through the interactive Streamlit dashboard or with direct command-line parameters.

#### Option A: Using the Streamlit Dashboard (Recommended)

The easiest way to create maps is to use the Streamlit dashboard:

```bash
streamlit run Home.py
```

This provides an interactive interface where you can:
- Select POI types and names from dropdown menus
- Choose your location and state
- Set travel time and census variables
- View results in a user-friendly format

#### Option B: Command Line with Direct Parameters

You can run the tool directly with POI parameters:

```bash
python community_mapper.py --poi --geocode-area "Fuquay-Varina" --state "North Carolina" --poi-type "amenity" --poi-name "library" --travel-time 15 --census-variables total_population median_household_income
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

### 4. Run the Community Mapper

#### Using the Streamlit Dashboard

The simplest way to run the Community Mapper is through the Streamlit dashboard:

```bash
streamlit run Home.py
```

#### Using Direct POI Parameters

Run directly with POI parameters:

```bash
python community_mapper.py --poi --geocode-area "Chicago" --state "Illinois" --poi-type "amenity" --poi-name "library" --travel-time 15 --census-variables total_population
```

By default, census data is exported to CSV format. To disable this feature, use:

```bash
python community_mapper.py --poi --geocode-area "Chicago" --state "Illinois" --poi-type "amenity" --poi-name "library" --no-export
```

#### Using Your Own Coordinates

If you already have latitude/longitude coordinates, you can skip the POI query step by providing your own CSV or JSON file. 

```bash
python community_mapper.py --custom-coords examples/custom_coordinates.csv --travel-time 15 --census-variables total_population
```

Supported formats for custom POIs:

1. CSV with header row:
```
id,name,lat,lon,state,type
1,"Community Center",37.7749,-122.4194,public
2,"Food Bank",37.7833,-122.4167,nonprofit
```

2. JSON list format:
```json
[
  {
    "id": "1",
    "name": "Community Center",
    "lat": 37.7749,
    "lon": -122.4194,
    "state": "CA",
    "tags": {
      "type": "public"
    }
  },
  {
    "id": "2",
    "name": "Food Bank",
    "lat": 37.7833,
    "lon": -122.4167,
    "state": "CA",
    "tags": {
      "type": "nonprofit"
    }
  }
]
```

Parameters explained:
- `--poi`: Use direct POI parameters mode
- `--geocode-area`: Area/city to search within
- `--poi-type`: Type of POI from OpenStreetMap (e.g., "amenity", "leisure")
- `--poi-name`: Name of POI from OpenStreetMap (e.g., "library", "park")
- `--custom-coords`: Path to your custom coordinates CSV or JSON file
- `--travel-time`: Travel time in minutes (how far can people travel from each POI)
- `--census-variables`: Census data to retrieve (list the variables you want)
- `--export`: Export census data to CSV (default: enabled)
- `--no-export`: Disable exporting census data to CSV format

### 5. Analyze the Results

After running the script, you'll find several outputs in the `output/` directory:
- GeoJSON files with isochrones in `output/isochrones/`
- GeoJSON files with block groups in `output/block_groups/`
- GeoJSON files with census data in `output/census_data/`
- PNG map visualizations in `output/maps/`
- CSV files with census data and travel distances in `output/csv/`

The maps show each demographic variable for the areas within your specified travel time of the POIs.

The CSV files include:
- Census block group identifiers
- County and state FIPS codes
- Percentage of each block group area within the travel time area
- All selected census variables
- Travel distance (in kilometers) from each block group's centroid to the nearest POI

These CSV exports are ideal for further analysis in tools like Excel, R, or other statistical software.

### Example Projects

Here are some examples of community mapping projects you could create:

1. **Food Desert Analysis**: Map supermarkets with travel times and income data to identify areas with limited food access.
   ```bash
   python community_mapper.py --poi --geocode-area "Chicago" --state "Illinois" --poi-type "shop" --poi-name "supermarket" --travel-time 20 --census-variables total_population median_household_income
   ```

2. **Healthcare Access**: Map hospitals and clinics with population and age demographics.
   ```bash
   python community_mapper.py --poi --geocode-area "Los Angeles" --state "California" --poi-type "amenity" --poi-name "hospital" --travel-time 30 --census-variables total_population median_age
   ```

3. **Educational Resource Distribution**: Map schools and libraries with educational attainment data.
   ```bash
   python community_mapper.py --poi --geocode-area "Boston" --state "Massachusetts" --poi-type "amenity" --poi-name "school" --travel-time 15 --census-variables total_population education_bachelors_plus
   ```

4. **Park Access Equity**: Map parks with demographic and income data to assess equitable access.
   ```bash
   python community_mapper.py --poi --geocode-area "Miami" --state "Florida" --poi-type "leisure" --poi-name "park" --travel-time 10 --census-variables total_population median_household_income white_population black_population
   ```

### Troubleshooting

- **No POIs found**: Check your POI configuration. Try making the query more general or verify that the location name is correct.
- **Census API errors**: Ensure your API key is valid and properly set as an environment variable.
- **Isochrone generation issues**: For very large areas, try reducing the travel time to avoid timeouts.
- **Missing block groups**: The tool should automatically identify the appropriate states based on the POI locations.