# Community Mapper Streamlit App

This Streamlit app provides a user-friendly interface for the Community Mapper tool, allowing you to analyze demographics around community resources without writing code.

## Features

- Query OpenStreetMap for points of interest (POIs) like libraries, schools, and parks
- Upload or manually enter custom coordinates
- Generate travel time isochrones around POIs
- Fetch census data for the areas within those isochrones
- Visualize demographic data with interactive maps

## Getting Started

### Prerequisites

- Python 3.9 or later
- A Census API key (get one at https://api.census.gov/data/key_signup.html)

### Installation

1. Clone the community-mapper repository:
   ```bash
   git clone https://github.com/mihiarc/community-mapper.git
   cd community-mapper
   ```

2. Create a virtual environment using uv:
   ```bash
   uv venv
   ```

3. Activate the virtual environment:
   ```bash
   # On Unix/Mac
   source .venv/bin/activate
   
   # On Windows
   .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

5. Set your Census API key as an environment variable or in a `.env` file:
   ```
   CENSUS_API_KEY=your-census-api-key
   ```

### Running the Streamlit App

Launch the Streamlit app with:

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`.

## Using the App

### Method 1: OpenStreetMap POI Query

1. Select "OpenStreetMap POI Query" from the sidebar
2. Enter the area (city/town) and state
3. Select the POI type and name (e.g., "amenity" and "library")
4. Optionally, add advanced query options
5. Set your travel time (in minutes) and select census variables to analyze
6. Click "Run Community Mapper Analysis"

### Method 2: Custom Coordinates

1. Select "Custom Coordinates" from the sidebar
2. Choose to either upload a file or enter coordinates manually:
   - **Upload file**: Select a CSV or JSON file with latitude, longitude, and state information
   - **Manual entry**: Enter coordinates one by one, including name, latitude, longitude, and state
3. Set your travel time and select census variables to analyze
4. Click "Run Community Mapper Analysis"

### Required Format for Custom Coordinates

#### CSV Format
Your CSV file should include columns for latitude, longitude, and state:
```
id,name,lat,lon,state
1,"Community Center",37.7749,-122.4194,CA
2,"Food Bank",37.7833,-122.4167,CA
```

#### JSON Format
Your JSON file should follow this structure:
```json
{
  "pois": [
    {
      "id": "1",
      "name": "Community Center",
      "lat": 37.7749,
      "lon": -122.4194,
      "state": "CA"
    },
    {
      "id": "2",
      "name": "Food Bank",
      "lat": 37.7833,
      "lon": -122.4167,
      "state": "CA"
    }
  ]
}
```

## Viewing Results

After the analysis completes:

1. The Points of Interest section will show details about the locations analyzed
2. The Demographic Maps section will display visualizations of census data around the POIs
3. All output files are saved to the `output/` directory for further use

## Troubleshooting

- **Census API key issues**: Ensure your API key is valid and properly set
- **No POIs found**: Try broadening your search terms or checking the spelling of the location
- **Processing errors**: For large areas, try reducing the travel time

## About

This Streamlit app is powered by the Community Mapper project, which integrates several geospatial analysis tools to help understand the demographics of areas around community amenities.

For more information, see the [main project README](README.md). 