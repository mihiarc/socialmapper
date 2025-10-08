# Demographic-Only Analysis

SocialMapper now supports demographic analysis within travel time areas without requiring POI (Points of Interest) search. This feature enables you to analyze population demographics within isochrones centered on a location, without searching for specific amenities.

## Use Cases

- **Market Analysis**: Understand the demographics within a certain travel time of a potential business location
- **Service Area Planning**: Analyze population characteristics within reach of a service center
- **Urban Planning**: Study demographic patterns within walking/biking distance of transit stops
- **Research**: Examine how demographics vary with travel time from city centers

## Basic Usage

### Analyze Demographics Without POI Search

```python
from socialmapper import SocialMapper

mapper = SocialMapper()

# Analyze demographics within 15-minute drive of Chapel Hill
result = mapper.analyze_location(
    location="Chapel Hill, NC",
    poi_types=None,  # No POI search
    travel_time=15,
    travel_mode="drive",
    census_variables=[
        "total_population",
        "median_household_income",
        "median_age",
        "education_bachelors_plus"
    ]
)

print(f"Population within 15 minutes: {result.demographics.get('total_population'):,}")
print(f"Area covered: {result.isochrone_area_km2:.2f} km²")
```

### Using Coordinates

```python
# Analyze demographics around specific coordinates
result = mapper.analyze_location(
    location=(35.9132, -79.0558),  # Chapel Hill coordinates
    poi_types=None,
    travel_time=20,
    travel_mode="bike",
    census_variables=["total_population", "median_age"]
)
```

### Explicitly Skip POI Search

```python
# Use empty list to explicitly indicate no POI search
result = mapper.analyze_location(
    location="Durham, NC",
    poi_types=[],  # Explicit empty list
    travel_time=10,
    travel_mode="walk",
    census_variables=["total_population"]
)
```

## Travel Modes

The feature supports all standard travel modes:

- **`drive`**: Analyze car-accessible areas (default)
- **`walk`**: Pedestrian-accessible areas
- **`bike`**: Bicycle-accessible areas

## Census Variables

Common census variables for demographic analysis:

### Population
- `total_population`: Total population count
- `population_density`: People per square kilometer
- `households`: Number of households

### Age Demographics
- `median_age`: Median age of population
- `children_under_18`: Population under 18
- `seniors_65_plus`: Population 65 and older

### Economic Indicators
- `median_household_income`: Median household income
- `poverty_rate`: Percentage below poverty line
- `unemployment_rate`: Unemployment rate

### Education
- `education_bachelors_plus`: Population with bachelor's degree or higher
- `education_high_school_plus`: High school graduates or higher

### Housing
- `median_home_value`: Median home value
- `median_rent`: Median monthly rent
- `owner_occupied_rate`: Percentage of owner-occupied homes

## Comparison with POI Analysis

### Traditional POI Analysis
```python
# Analyze libraries with demographics
result = mapper.analyze_location(
    location="Chapel Hill, NC",
    poi_types=["library"],  # Search for libraries
    travel_time=15,
    census_variables=["total_population"]
)
# Returns: Libraries found + demographics around each library
```

### Demographic-Only Analysis
```python
# Analyze demographics without POI search
result = mapper.analyze_location(
    location="Chapel Hill, NC",
    poi_types=None,  # No POI search
    travel_time=15,
    census_variables=["total_population"]
)
# Returns: Demographics within travel time from location center
```

## Output and Visualization

The demographic-only analysis still generates:

1. **Isochrone Maps**: Travel time polygons showing reachable areas
2. **Choropleth Maps**: If census variables are provided, creates demographic visualizations
3. **CSV Exports**: Tabular data of census block groups within the isochrone
4. **GeoJSON Files**: Geographic data for further analysis

### Example Output Structure
```
output/
├── csv/
│   └── census_data.csv          # Demographics by block group
├── geojson/
│   └── isochrone.geojson        # Travel time polygon
└── maps/
    ├── isochrone_map.html       # Interactive isochrone map
    └── population_choropleth.png # Population density visualization
```

## Performance Considerations

Demographic-only analysis is typically faster than POI analysis because:

1. **No POI Search**: Skips OpenStreetMap/Overpass API queries
2. **Single Isochrone**: Generates one isochrone from the center point instead of multiple from POIs
3. **Reduced Processing**: Less data aggregation and merging

## Error Handling

The feature includes robust error handling for:

- **Invalid Locations**: Clear error messages for unrecognized locations
- **Geocoding Failures**: Fallback coordinates for common locations
- **Census API Issues**: Graceful degradation if census data unavailable

## Examples

### Market Research
```python
# Analyze potential customer base for a new store
result = mapper.analyze_location(
    location="Downtown Raleigh, NC",
    poi_types=None,
    travel_time=20,
    travel_mode="drive",
    census_variables=[
        "total_population",
        "median_household_income",
        "median_age",
        "households"
    ]
)

print(f"Potential customers (20-min drive): {result.demographics['total_population']:,}")
print(f"Median income: ${result.demographics['median_household_income']:,}")
```

### Transit Planning
```python
# Analyze walking access to a proposed bus stop
result = mapper.analyze_location(
    location="Main St & 5th Ave, Durham, NC",
    poi_types=None,
    travel_time=10,
    travel_mode="walk",
    census_variables=[
        "total_population",
        "households",
        "seniors_65_plus",
        "poverty_rate"
    ]
)
```

### Comparative Analysis
```python
from socialmapper.api.convenience import compare_locations

# Compare demographics across multiple city centers
results = compare_locations(
    locations=["Chapel Hill, NC", "Durham, NC", "Raleigh, NC"],
    poi_types=None,  # Demographics only
    travel_time=15,
    travel_mode="drive",
    census_variables=["total_population", "median_household_income"]
)

for city, result in results.items():
    print(f"{city}: Population={result.demographics['total_population']:,}")
```

## API Reference

### `analyze_location()` Parameters

- **`location`** (str | tuple): Location as "City, State" or (latitude, longitude)
- **`poi_types`** (list | None): List of POI types to search. Use `None` or `[]` for demographic-only
- **`travel_time`** (int): Travel time in minutes (1-120)
- **`travel_mode`** (str): Travel mode ("drive", "walk", "bike")
- **`census_variables`** (list): Census variables to analyze
- **`output_dir`** (str): Output directory for results
- **`create_maps`** (bool): Whether to generate visualizations

### Returns

`AnalysisResult` object with:
- `poi_count`: Will be 0 or 1 (location point) for demographic-only
- `census_units_analyzed`: Number of census block groups analyzed
- `isochrone_area_km2`: Area of the travel time polygon
- `demographics`: Dictionary of census variable values
- `files_created`: List of generated output files