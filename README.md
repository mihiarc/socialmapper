# 🏘️ SocialMapper: Explore Community Connections

[![PyPI version](https://badge.fury.io/py/socialmapper.svg)](https://badge.fury.io/py/socialmapper)
[![Python Versions](https://img.shields.io/pypi/pyversions/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Status](https://img.shields.io/pypi/status/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![Downloads](https://static.pepy.tech/badge/socialmapper)](https://pepy.tech/project/socialmapper)

SocialMapper is an open-source Python toolkit that helps you understand how people connect with the important places in their community. Imagine taking a key spot like your local shopping center or school and seeing exactly what areas are within a certain travel time – whether it's a quick walk or a longer drive. SocialMapper does just that.

But it doesn't stop at travel time. SocialMapper also shows you the characteristics of the people who live within these accessible areas, like how many people live there and what the average income is. This helps you see who can easily reach vital community resources and identify any gaps in access.

Whether you're looking at bustling city neighborhoods or more spread-out rural areas, SocialMapper provides clear insights for making communities better, planning services, and ensuring everyone has good access to the places that matter.

SocialMapper is a focused tool for understanding people, places, and accessibility patterns in your community.

## 🚀 Get Started with SocialMapper

**Example: Total Population Within 15-Minute Walk of Libraries in Fuquay-Varina, NC**

![Total Population Map](https://raw.githubusercontent.com/mihiarc/socialmapper/main/docs/assets/images/example-map.png)

## What's New in v0.6.0 🎉

- **🚶‍♀️ Travel Mode Support** - Generate isochrones for walking, biking, or driving with mode-specific speeds
- **🏗️ Streamlined Architecture** - Simplified codebase focused on core demographic and accessibility analysis
- **⚡ Enhanced Pipeline** - Refactored core functionality into modular ETL pipeline for better maintainability
- **💾 Lightweight Neighbor System** - Streaming census system reduces storage from 118MB to ~0.1MB
- **🗺️ Geographic Level Support** - Choose between census block groups or ZIP Code Tabulation Areas (ZCTAs)
- **🖥️ Enhanced CLI** - New options for addresses, dry-run mode, and more

📚 **[Full Documentation](https://mihiarc.github.io/socialmapper)** | 🐛 **[Report Issues](https://github.com/mihiarc/socialmapper/issues)**

## Features

- **Finding Points of Interest** - Query OpenStreetMap for libraries, schools, parks, healthcare facilities, etc.
- **Generating Travel Time Areas** - Create isochrones showing areas reachable within a certain travel time by walking, biking, or driving
- **Identifying Census Block Groups** - Determine which census block groups intersect with these areas
- **Calculating Travel Distance** - Measure the travel distance along roads from the point of interest to the block group centroids
- **Retrieving Demographic Data** - Pull census data for the identified areas
- **Data Export** - Export census data with travel distances to CSV for further analysis

## Installation

SocialMapper is available on PyPI. Install it easily with uv:

```bash
uv pip install socialmapper
```

Or with pip:

```bash
pip install socialmapper
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

### Quick Start with Python API

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

### Command Line Interface

SocialMapper also provides a powerful command-line interface:

```bash
# Show help
uv run socialmapper --help

# Analyze libraries in Chicago
uv run socialmapper --poi --geocode-area "Chicago" --state "Illinois" \
    --poi-type "amenity" --poi-name "library" --travel-time 15 \
    --census-variables total_population median_household_income

# Use custom coordinates
uv run socialmapper --custom-coords "path/to/coordinates.csv" \
    --travel-time 20 --census-variables total_population median_household_income

# Use ZIP codes instead of block groups
uv run socialmapper --poi --geocode-area "Denver" --state "Colorado" \
    --poi-type "amenity" --poi-name "hospital" --geographic-level zcta

# Analyze walking access to parks
uv run socialmapper --poi --geocode-area "Portland" --state "Oregon" \
    --poi-type "leisure" --poi-name "park" --travel-time 15 \
    --travel-mode walk
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

#### Using the Command Line

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