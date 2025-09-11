# 🏘️ SocialMapper: Python Toolkit for Spatial Analysis

[![PyPI version](https://badge.fury.io/py/socialmapper.svg)](https://badge.fury.io/py/socialmapper)
[![Python Versions](https://img.shields.io/pypi/pyversions/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Status](https://img.shields.io/pypi/status/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![Downloads](https://static.pepy.tech/badge/socialmapper)](https://pepy.tech/project/socialmapper)

SocialMapper is an open-source Python toolkit for spatial analysis, demographic mapping, and geospatial data processing. It provides comprehensive functionality for understanding community connections, accessibility patterns, and demographic insights.

## 🏗️ Repository Structure

- **🔧 Core Package** (`socialmapper/`) - Python toolkit for spatial analysis
- **📚 Documentation** (`docs/`) - Comprehensive guides and reference
- **🧪 Examples** (`examples/`) - Python usage examples and tutorials

## 🌟 Key Capabilities

SocialMapper helps you understand how people connect with important places in their community by:

- **Analyzing Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
- **Generating Travel Time Areas** - Create isochrones showing areas reachable within travel time constraints
- **Processing Demographic Data** - Integrate with US Census data for community insights  
- **Calculating Accessibility** - Measure travel distances and identify access patterns
- **Supporting Multiple Formats** - Export data as CSV, GeoJSON, Parquet, and more

## 🚀 Get Started with SocialMapper

**Example: Total Population Within 15-Minute Walk of Libraries in Fuquay-Varina, NC**

![Total Population Map](https://raw.githubusercontent.com/mihiarc/socialmapper/main/docs/assets/images/example-map.png)

## What's New in v0.7.0 🎉

### Major Architecture Update: Simplified Python Package

- **📦 Clean Installation** - Simple installation with `pip install socialmapper`
- **🔧 Focused Toolkit** - Streamlined Python package for spatial analysis
- **📚 Enhanced Documentation** - Improved guides and examples

### Previous v0.6.2 Updates

- **🐛 Fixed Travel Time Bug** - Census data exports now correctly show actual travel time
- **🚶‍♀️ Travel Mode Support** - Generate isochrones for walking, biking, or driving
- **💾 Lightweight Neighbor System** - Streaming census system reduces storage from 118MB to ~0.1MB
- **🗺️ Geographic Level Support** - Choose between census block groups or ZCTAs

📚 **[Full Documentation](https://mihiarc.github.io/socialmapper)** | 🐛 **[Report Issues](https://github.com/mihiarc/socialmapper/issues)**

## Features

- **🔍 Nearby POI Discovery** - Discover Points of Interest within travel time constraints from any location, with 10 categories and 338+ OSM tag mappings
- **Finding Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
- **Generating Travel Time Areas** - Create isochrones showing areas reachable within a certain travel time by walking, biking, or driving
- **Identifying Census Block Groups** - Determine which census block groups intersect with these areas
- **Calculating Travel Distance** - Measure the travel distance along roads from the point of interest to the block group centroids
- **Retrieving Demographic Data** - Pull census data for the identified areas
- **Data Export** - Export census data with travel distances to CSV for further analysis

## Installation

SocialMapper is available on PyPI with flexible installation options:

### Backend Only (Recommended for API/CLI usage)
```bash
# Install core functionality without UI dependencies
pip install socialmapper
```

### Backend + Streamlit UI (For backward compatibility)
```bash
# Install with optional UI components
pip install socialmapper[ui]
```

### Development Installation
```bash
# Clone and install in development mode
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper
pip install -e ".[dev]"
```

**Requirements:** Python 3.11 or higher (3.11, 3.12, or 3.13)

### Environment Variables

SocialMapper supports environment variables for configuration. Create a `.env` file in your project directory:

```bash
# Copy the example file and customize
cp env.example .env
```

Key environment variables:
- `CENSUS_API_KEY`: Your Census Bureau API key (get one free at https://api.census.gov/data/key_signup.html)
- `CENSUS_CACHE_ENABLED`: Enable/disable caching (default: true)
- `CENSUS_RATE_LIMIT`: API rate limit in requests per minute (default: 60)

See `env.example` for all available configuration options.

## Using SocialMapper

SocialMapper offers multiple ways to perform your analysis:

### Web Interface Options

#### Modern React UI (Recommended)

For the best interactive experience, use the new React-based frontend:

1. **Start the API Server**:
   ```bash
   cd socialmapper-api
   uvicorn main:app --reload
   ```

2. **Start the React Frontend** (in a separate terminal):
   ```bash
   cd socialmapper-ui
   npm install
   npm run dev
   ```

3. **Access the UI** at http://localhost:3000

#### Legacy Streamlit Dashboard

The Streamlit interface is still available if you installed with UI support:

```bash
# Requires: pip install socialmapper[ui]
streamlit run streamlit_app.py
```

**Note**: The Streamlit UI is deprecated and will be removed in a future version.

### Quick Start with Python API

#### POI Discovery (New!)

Discover what's around any location within realistic travel constraints:

```python
from socialmapper import SocialMapperClient

# Discover POIs within a 20-minute walk
with SocialMapperClient() as client:
    result = client.discover_nearby_pois(
        location="Chapel Hill, NC",
        travel_time=20,
        travel_mode="walk",
        poi_categories=["food_and_drink", "healthcare", "education"]
    )
    
    if result.is_ok():
        poi_result = result.unwrap()
        print(f"Found {poi_result.total_poi_count} POIs")
        for category, count in poi_result.category_counts.items():
            print(f"  {category}: {count}")
```

#### Traditional Census Analysis

```python
from socialmapper import SocialMapperClient

# Simple analysis
with SocialMapperClient() as client:
    result = client.analyze(
        location="San Francisco, CA",
        poi_type="amenity",
        poi_name="library",
        travel_time=15
    )
    
    if result.is_ok():
        analysis = result.unwrap()
        print(f"Found {analysis.poi_count} libraries")
        print(f"Analyzed {analysis.census_units_analyzed} census units")
```

### Advanced Usage with Builder Pattern

#### POI Discovery with Builder

```python
from socialmapper import SocialMapperBuilder
from socialmapper.isochrone import TravelMode

# Advanced POI discovery configuration
result = (
    SocialMapperBuilder()
    .with_nearby_poi_discovery("Boston, MA", 25, TravelMode.BIKE)
    .with_poi_categories("food_and_drink", "healthcare", "education")
    .exclude_poi_categories("utilities")
    .limit_pois_per_category(30)
    .with_export_options(csv=True, geojson=True, maps=True)
    .execute()
)
```

#### Traditional Census Analysis with Builder

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

with SocialMapperClient() as client:
    # Configure analysis using fluent builder
    config = (SocialMapperBuilder()
        .with_location("Chicago", "IL")
        .with_osm_pois("leisure", "park")
        .with_travel_time(20)
        .with_travel_mode("walk")  # Analyze walking access
        .with_census_variables("total_population", "median_income", "percent_poverty")
        .with_geographic_level("zcta")  # Use ZIP codes instead of block groups
        .with_exports(csv=True, isochrones=True)  # Generate maps
        .build()
    )
    
    result = client.run_analysis(config)
```

### Using Custom POI Coordinates

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_custom_pois("my_locations.csv")
        .with_travel_time(15)
        .with_census_variables("total_population")
        .build()
    )
    
    result = client.run_analysis(config)
```

### Python API Interface

SocialMapper provides a clean, Pythonic API:

```python
from socialmapper import SocialMapper, quick_analysis

# Simple one-liner for quick analyses
result = quick_analysis(
    "Chicago, IL", 
    "library", 
    travel_time=15,
    census_variables=["total_population", "median_household_income"]
)
print(f"Found {result['poi_count']} libraries")

# Full client for advanced usage
mapper = SocialMapper()

# Analyze libraries in Chicago
result = mapper.analyze_location(
    "Chicago, IL",
    poi_types=["library"],
    travel_time=15,
    census_variables=["total_population", "median_household_income"]
)
result.print_summary()

# Use custom coordinates from CSV
result = mapper.analyze_custom_pois(
    "my_hospitals.csv",
    travel_time=30,
    census_variables=["total_population", "median_age"]
)

# Discover all nearby POIs
result = mapper.discover_nearby_pois(
    "Portland, OR",
    travel_time=20,
    travel_mode="walk"
)
print(f"Found {result.total_poi_count} POIs in {result.unique_categories} categories")

# Compare multiple locations
from socialmapper import compare_locations
results = compare_locations(
    ["Portland, OR", "Seattle, WA", "San Francisco, CA"],
    poi_types=["library"],
    travel_time=15
)
for location, result in results.items():
    print(f"{location}: {result.poi_count} libraries")
```

### Preset Analysis Functions

For common scenarios, use preset functions:

```python
from socialmapper import analyze_libraries, analyze_schools, analyze_hospitals

# Library access analysis
result = analyze_libraries("Boston, MA", travel_time=20, travel_mode="walk")

# School access with demographics
result = analyze_schools("Austin, TX", include_demographics=True)

# Healthcare access (30-minute default)
result = analyze_hospitals("Chicago, IL")

# Each returns detailed results
result.print_summary()  # Human-readable summary
data = result.to_dict()  # Export to dictionary
```

### Travel Modes

SocialMapper supports three travel modes, each using appropriate road networks and speeds:

- **walk** - Pedestrian paths, sidewalks, crosswalks (default: 5 km/h)
- **bike** - Bike lanes, shared roads, trails (default: 15 km/h)  
- **drive** - Roads accessible by cars (default: 50 km/h)

```python
from socialmapper import SocialMapperBuilder, TravelMode

# Compare walking vs driving access
walk_config = (SocialMapperBuilder()
    .with_location("Seattle", "WA")
    .with_osm_pois("amenity", "grocery_or_supermarket")
    .with_travel_time(15)
    .with_travel_mode(TravelMode.WALK)
    .build()
)

drive_config = (SocialMapperBuilder()
    .with_location("Seattle", "WA")
    .with_osm_pois("amenity", "grocery_or_supermarket")
    .with_travel_time(15)
    .with_travel_mode(TravelMode.DRIVE)
    .build()
)
```

### Error Handling

The modern API uses Result types for explicit error handling:

```python
from socialmapper import SocialMapperClient

with SocialMapperClient() as client:
    result = client.analyze(
        location="Invalid Location",
        poi_type="amenity",
        poi_name="library"
    )
    
    # Pattern matching (Python 3.10+)
    match result:
        case Ok(analysis):
            print(f"Success: {analysis.poi_count} POIs found")
        case Err(error):
            print(f"Error type: {error.type.name}")
            print(f"Message: {error.message}")
            if error.context:
                print(f"Context: {error.context}")
```

## Creating Your Own Community Maps: Step-by-Step Guide

### 1. Define Your Points of Interest

You can specify points of interest with direct command-line parameters.

#### Using the Python API

You can run the analysis using the simple Python API:

```python
from socialmapper import analyze_libraries

result = analyze_libraries(
    "Fuquay-Varina, North Carolina",
    travel_time=15,
    include_demographics=True
)
result.print_summary()
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

For more specific queries, you can add additional tags in a YAML format:
```yaml
# Example tags:
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

1. **Food Desert Analysis**: Discover food access options and analyze demographics.
   ```python
   from socialmapper import discover_food_access
   
   result = discover_food_access(
       "Chicago, Illinois",
       travel_time=20
   )
   result.print_summary()
   ```

2. **Healthcare Access**: Map hospitals and analyze accessibility patterns.
   ```python
   from socialmapper import analyze_hospitals
   
   result = analyze_hospitals(
       "Los Angeles, California",
       travel_time=30,
       include_demographics=True
   )
   ```

3. **Educational Resource Distribution**: Analyze school accessibility with relevant demographics.
   ```python
   from socialmapper import analyze_schools
   
   result = analyze_schools(
       "Boston, Massachusetts",
       travel_time=15,
       include_demographics=True
   )
   ```

4. **Park Access Equity**: Assess equitable access to green spaces.
   ```python
   from socialmapper import analyze_parks
   
   result = analyze_parks(
       "Miami, Florida",
       travel_time=10,
       travel_mode="walk",
       include_demographics=True
   )
   ```

## Learn More

- 📖 **[Documentation](https://mihiarc.github.io/socialmapper)** - Full documentation and tutorials
- 🎯 **[Examples](https://github.com/mihiarc/socialmapper/tree/main/examples)** - Working code examples
- 💬 **[Discussions](https://github.com/mihiarc/socialmapper/discussions)** - Ask questions and share ideas
- 🐛 **[Issues](https://github.com/mihiarc/socialmapper/issues)** - Report bugs or request features

## Development

For development, clone the repository and install with development dependencies:

```bash
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper
uv pip install -e ".[dev]"
```

Run tests:
```bash
uv run pytest
```

### Troubleshooting

- **No POIs found**: Check your POI configuration. Try making the query more general or verify that the location name is correct.
- **Census API errors**: Ensure your API key is valid and properly set as an environment variable.
- **Isochrone generation issues**: For very large areas, try reducing the travel time to avoid timeouts.
- **Missing block groups**: The tool should automatically identify the appropriate states based on the POI locations.

## Documentation

### POI Discovery
- **[POI Discovery Overview](docs/features/nearby_poi_discovery.md)** - Comprehensive feature overview and capabilities
- **[POI Discovery API Reference](docs/api/poi_discovery.md)** - Complete API documentation for POI discovery
- **[POI Discovery Usage Guide](docs/guides/poi_discovery_guide.md)** - Step-by-step tutorials and examples

### General Documentation
- [Travel Modes Explained](docs/travel_modes_explained.md) - Detailed explanation of how walking, biking, and driving networks differ
- [API Reference](https://mihiarc.github.io/socialmapper/) - Full API documentation
- [Examples](examples/) - Sample scripts and use cases

## Migration Guide

### Migrating to v0.7.0

The v0.7.0 release simplifies the package architecture. Here's how to migrate:

#### For Python API Users
The new simplified API provides cleaner, more Pythonic usage:
```python
# New simple API (recommended)
from socialmapper import SocialMapper, quick_analysis

# Quick one-liner
result = quick_analysis("NYC, NY", "library")

# Simple client usage  
mapper = SocialMapper()
result = mapper.analyze_location("NYC, NY", poi_types=["library"])

# Preset functions for common use cases
from socialmapper import analyze_libraries
result = analyze_libraries("NYC, NY", travel_time=20)
```

**Migration Benefits:**
- **90% less boilerplate** - no context managers, builders, or result unwrapping
- **Standard Python patterns** - uses exceptions instead of Result types
- **Direct access to data** - no `.unwrap()` or pattern matching needed

#### For Streamlit UI Users
The Streamlit UI is now optional and will be removed in a future version. You have three options:

1. **Continue using Streamlit** (temporary):
   ```bash
   pip install socialmapper[ui]
   streamlit run streamlit_app.py
   ```

2. **Use the Python API directly** (recommended):
   ```python
   from socialmapper import SocialMapperClient
   
   # Initialize client and run analysis
   client = SocialMapperClient()
   results = client.analyze_location(
       latitude=40.7128,
       longitude=-74.0060,
       poi_types=["library"]
   )
   ```

#### For Package Developers
If you're importing SocialMapper in your package:
```python
# Old (will show deprecation warning)
from socialmapper.ui import some_function

# New (console utilities moved)
from socialmapper.console import print_info, get_logger
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

SocialMapper is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Citation

If you use SocialMapper in your research, please cite:

```bibtex
@software{socialmapper,
  title = {SocialMapper: Community Demographic and Accessibility Analysis},
  author = {mihiarc},
  year = {2025},
  url = {https://github.com/mihiarc/socialmapper}
}
```