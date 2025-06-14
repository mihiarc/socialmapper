# API Reference

## Core Function

### `run_socialmapper()`

The main function for running SocialMapper analyses.

```python
from socialmapper import run_socialmapper

results = run_socialmapper(
    # Location parameters (choose one)
    state=None,              # State name or abbreviation
    county=None,             # County name
    place_type=None,         # POI type (e.g., "library")
    custom_coords_path=None, # Path to CSV with custom locations
    
    # Analysis parameters
    travel_time=15,          # Travel time in minutes (1-120)
    geographic_level="block-group",  # "block-group" or "zcta"
    census_variables=None,   # List of census variables
    
    # Output parameters
    export_csv=True,         # Export results to CSV
    export_maps=False,       # Generate map visualizations
    export_isochrones=False, # Export isochrone geometries
    output_dir="output",     # Output directory
    
    # Optional parameters
    api_key=None,           # Census API key
)
```

#### Parameters

**Location Parameters** (mutually exclusive):
- `state` (str): State name or two-letter abbreviation
- `county` (str): County name (include "County" suffix)
- `place_type` (str): OpenStreetMap place type
- `custom_coords_path` (str): Path to CSV file with custom coordinates

**Analysis Parameters**:
- `travel_time` (int): Travel time in minutes, 1-120 (default: 15)
- `geographic_level` (str): Geographic unit - "block-group" or "zcta" (default: "block-group")
- `census_variables` (list): List of census variable names (default: ["total_population"])

**Output Parameters**:
- `export_csv` (bool): Export results to CSV files (default: True)
- `export_maps` (bool): Generate static map images (default: False)
- `export_isochrones` (bool): Export isochrone geometries (default: False)
- `output_dir` (str): Directory for output files (default: "output")

**Optional Parameters**:
- `api_key` (str): Census API key (uses environment variable if not provided)

#### Returns

Dictionary containing:
- `poi_data` (list): Points of interest with geographic context
- `census_data` (list): Census demographics for areas within travel time
- Additional metadata about the analysis

#### Examples

**Basic POI Search**:
```python
results = run_socialmapper(
    state="California",
    county="San Francisco County",
    place_type="library",
    travel_time=15
)
```

**Custom Locations**:
```python
results = run_socialmapper(
    custom_coords_path="my_locations.csv",
    travel_time=20,
    census_variables=["total_population", "median_income"]
)
```

**Full Analysis with Exports**:
```python
results = run_socialmapper(
    state="Texas",
    county="Harris County",
    place_type="hospital",
    travel_time=30,
    geographic_level="zcta",
    census_variables=[
        "total_population",
        "median_age",
        "percent_poverty"
    ],
    export_csv=True,
    export_maps=True,
    export_isochrones=True,
    output_dir="hospital_analysis"
)
```

## Census Variables

### Common Variable Names

| Variable Name | Description |
|--------------|-------------|
| `total_population` | Total population count |
| `median_age` | Median age |
| `median_household_income` | Median household income |
| `median_income` | Alias for median household income |
| `percent_poverty` | Percentage below poverty line |
| `percent_without_vehicle` | Percentage of households without vehicles |

### Using Raw Census Codes

You can also use raw Census Bureau variable codes:
```python
census_variables = [
    "B01003_001E",  # Total population
    "B19013_001E",  # Median household income
    "B25044_003E"   # No vehicle available
]
```

## Error Handling

```python
try:
    results = run_socialmapper(
        state="California",
        county="Invalid County",
        place_type="library"
    )
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Analysis error: {e}")
```

## Working with Results

### Accessing POI Data
```python
for poi in results['poi_data']:
    print(f"Name: {poi['name']}")
    print(f"Location: {poi['latitude']}, {poi['longitude']}")
```

### Accessing Census Data
```python
total_population = sum(
    block.get('total_population', 0) 
    for block in results['census_data']
)
print(f"Total population: {total_population:,}")
```

### Checking Analysis Metadata
```python
if 'analysis_metadata' in results:
    print(f"Analysis completed at: {results['analysis_metadata']['timestamp']}")
    print(f"Travel time: {results['analysis_metadata']['travel_time']} minutes")
```

## Environment Variables

- `CENSUS_API_KEY`: Your Census Bureau API key
- `SOCIALMAPPER_OUTPUT_DIR`: Default output directory

## Version Information

```python
import socialmapper
print(socialmapper.__version__)
```