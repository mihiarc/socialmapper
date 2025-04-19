# POI Query

A Python package for querying Points of Interest (POIs) from OpenStreetMap, generating isochrones, and analyzing census block groups.

## Installation

1. Clone the repository
2. Create a virtual environment using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/Mac
   # or
   .venv\Scripts\activate  # On Windows
   ```
3. Install dependencies with uv:
   ```bash
   uv pip install -r requirements.txt
   ```

## Features

### POI Query
- Query Points of Interest from OpenStreetMap using the Overpass API
- Configure queries using YAML files
- Save POI data as GeoJSON

### Isochrone Generation
- Generate isochrones (travel time polygons) for POIs
- Support for multiple travel time thresholds
- Save isochrones as GeoJSON

### Census Block Group Analysis
- Find census block groups that intersect with isochrones
- Cache block group boundaries to reduce API calls
- Process and save results as GeoJSON

### Census Data Retrieval
- Fetch demographic data from the Census API for identified block groups
- Support for any American Community Survey (ACS) variables
- Merge census data with spatial information for further analysis

## Usage

### Basic Usage

```python
from poi_query import (
    # POI query functionality
    load_poi_config,
    build_overpass_query,
    query_overpass,
    format_results,
    save_json,
    
    # Isochrone functionality
    create_isochrone_from_poi,
    
    # Block groups functionality
    isochrone_to_block_groups,
    
    # Census data functionality
    get_census_data_for_block_groups
)

# 1. Query POIs
config = load_poi_config("config.yaml")
query = build_overpass_query(config)
raw_results = query_overpass(query)
poi_data = format_results(raw_results)
save_json(poi_data, "pois.json")

# 2. Generate isochrones
isochrone_file = create_isochrone_from_poi(
    poi=poi_data["pois"][0],
    travel_time_limit=30,
    output_dir="isochrones",
    save_file=True
)

# 3. Find intersecting block groups
block_groups_file = "results/block_groups.geojson"
block_groups = isochrone_to_block_groups(
    isochrone_path=isochrone_file,
    state_fips=["20"],  # Kansas
    output_path=block_groups_file
)

# 4. Fetch census data for block groups
census_data = get_census_data_for_block_groups(
    geojson_path=block_groups_file,
    variables=["B01003_001E", "B19013_001E"],  # Population and income
    output_path="results/block_groups_with_census_data.geojson",
    variable_mapping={
        "B01003_001E": "total_population",
        "B19013_001E": "median_household_income"
    }
)
```

### Example Script

See `example.py` for a complete end-to-end pipeline example.

## Census API Variables

Common Census API variables:

- `B01003_001E`: Total population
- `B19013_001E`: Median household income
- `B02001_002E`: White population
- `B02001_003E`: Black or African American population
- `B25077_001E`: Median home value

To get metadata about available variables:

```python
from poi_query import get_variable_metadata

variables = get_variable_metadata(year=2021, dataset="acs/acs5")
```

## API Key

Census API functionality requires an API key. Either:

1. Set the `CENSUS_API_KEY` environment variable
2. Pass the API key directly to functions that require it
3. Create a `.env` file with `CENSUS_API_KEY=your_key_here`

Get a Census API key at: https://api.census.gov/data/key_signup.html

## License

MIT License 