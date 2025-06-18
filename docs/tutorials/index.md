# Tutorials

Welcome to the SocialMapper tutorials! These hands-on examples will guide you through common use cases and demonstrate the full capabilities of the toolkit.

## Available Tutorials

### 1. [Getting Started Tutorial](getting-started-tutorial.md)
**Example code:** `01_getting_started.py`

Learn the basics of SocialMapper by analyzing library accessibility in Raleigh, NC. This tutorial covers:
- Finding points of interest (POIs) from OpenStreetMap
- Generating travel time isochrones
- Creating demographic analysis
- Exporting results

### 2. [Getting Started with Maps](getting-started-with-maps.md)
**Example code:** `01_getting_started_with_maps.py`

Enhanced version of the getting started tutorial that includes choropleth map generation:
- Creating professional choropleth maps
- Visualizing demographic patterns
- Customizing map appearance
- Exporting high-quality visualizations

### 3. [Custom Points of Interest](custom-pois-tutorial.md)
**Example code:** `02_custom_pois.py`

Discover how to work with your own location data instead of OpenStreetMap queries. This tutorial demonstrates:
- Loading custom POI data from CSV files
- Geocoding addresses
- Analyzing accessibility for custom locations
- Combining custom and OpenStreetMap data

### 4. [Travel Modes](travel-modes-tutorial.md)
**Example code:** `03_travel_modes.py`

Explore different transportation modes for accessibility analysis. This tutorial covers:
- Walking, driving, and biking isochrones
- Comparing accessibility across travel modes
- Understanding mode-specific network constraints
- Customizing travel parameters

### 5. [ZIP Code (ZCTA) Analysis](zcta-analysis-tutorial.md)
**Example code:** `04_zipcode_analysis.py`

Analyze demographics at the ZIP Code Tabulation Area (ZCTA) level. This tutorial covers:
- Understanding ZCTAs vs block groups
- Fetching ZCTA boundaries and census data
- Batch processing multiple states
- Choosing the right geographic unit for your analysis

### 6. [Address Geocoding](address-geocoding-tutorial.md)
**Example code:** `05_address_geocoding.py`

Convert street addresses into geographic coordinates for analysis. This tutorial demonstrates:
- Single and batch address geocoding
- Understanding quality levels and providers
- Error handling for problematic addresses
- Creating custom POI datasets from address lists
- Integration with demographic analysis

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

The tutorials create their own sample data as needed. Output from the tutorials will be saved in:
- `output/csv/`: Demographic and analysis results in CSV format
- `output/isochrones/`: Generated travel time visualizations
- `cache/`: Cached geocoding and network data for faster re-runs

Each tutorial creates its own subdirectory in the output folder to keep results organized.

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