# Tutorials

Welcome to the SocialMapper tutorials! These hands-on examples will guide you through common use cases and demonstrate the full capabilities of the toolkit.

## Available Tutorials

### 1. Getting Started
**File:** `01_getting_started.py`

Learn the basics of SocialMapper by analyzing library accessibility in Raleigh, NC. This tutorial covers:
- Finding points of interest (POIs) from OpenStreetMap
- Generating travel time isochrones
- Creating demographic analysis
- Exporting results

### 2. Custom Points of Interest
**File:** `02_custom_pois.py`

Discover how to work with your own location data instead of OpenStreetMap queries. This tutorial demonstrates:
- Loading custom POI data from CSV files
- Geocoding addresses
- Analyzing accessibility for custom locations
- Combining custom and OpenStreetMap data

### 3. ZCTA Analysis
**File:** `02_zcta_analysis.py`

Analyze demographics at the ZIP Code Tabulation Area (ZCTA) level. This tutorial covers:
- Working with ZCTA boundaries
- Aggregating demographic data by ZIP code
- Creating ZCTA-level visualizations

### 4. ZCTA POI Analysis
**File:** `03_zcta_poi_analysis.py`

Combine ZCTA analysis with POI accessibility. Learn how to:
- Find POIs within specific ZIP codes
- Analyze demographic access to services by ZCTA
- Create comparative analyses across ZIP codes

### 5. Modern ZCTA API
**File:** `04_modern_zcta_api.py`

Use the latest ZCTA analysis features with the modern API. This tutorial shows:
- Streamlined ZCTA workflows
- Advanced demographic queries
- Performance optimizations for large-scale analysis

### 6. TIGER API and ZCTA Boundaries
**File:** `05_tiger_api_zcta_boundaries.py`

Work with official Census TIGER boundary data. Learn about:
- Accessing TIGER/Line shapefiles
- Working with official ZCTA boundaries
- Integrating Census geography with analysis

### 7. Travel Modes
**File:** `05_travel_modes.py`

Explore different transportation modes for accessibility analysis. This tutorial covers:
- Walking, driving, and biking isochrones
- Comparing accessibility across travel modes
- Understanding mode-specific network constraints
- Customizing travel parameters

## Running the Tutorials

All tutorials are located in the `examples/tutorials/` directory of the SocialMapper repository. To run a tutorial:

1. Clone the repository:
   ```bash
   git clone https://github.com/mihiarc/socialmapper.git
   cd socialmapper
   ```

2. Install SocialMapper:
   ```bash
   pip install -e ".[dev]"
   ```

3. Set up your Census API key:
   ```bash
   export CENSUS_API_KEY="your-key-here"
   ```

4. Navigate to the tutorials directory:
   ```bash
   cd examples/tutorials
   ```

5. Run any tutorial:
   ```bash
   python 01_getting_started.py
   ```

## Tutorial Data

Some tutorials include sample data files:
- `custom_pois.csv`: Example custom location data for tutorial 2
- `README_ZCTA_TUTORIALS.md`: Additional documentation for ZCTA-related tutorials

Output from the tutorials will be saved in:
- `output/csv/`: Demographic and analysis results in CSV format
- `output/isochrones/`: Generated travel time visualizations
- `cache/`: Cached geocoding and network data for faster re-runs

## Tips for Success

1. **API Key**: Make sure your Census API key is properly configured before running tutorials
2. **Dependencies**: Some tutorials may require additional data downloads on first run
3. **Caching**: Tutorials use caching to speed up repeated runs - clear the cache directory if you need fresh data
4. **Customization**: Feel free to modify the tutorials to explore your own areas of interest

## Next Steps

After completing these tutorials, you'll be ready to:
- Analyze accessibility in your own community
- Create custom demographic studies
- Build interactive applications with SocialMapper
- Contribute to the SocialMapper project

For more information, see the [User Guide](../user-guide/index.md) and [API Reference](../api-reference.md).