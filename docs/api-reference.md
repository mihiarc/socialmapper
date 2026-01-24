# API Reference

Complete reference for all SocialMapper API functions, models, exceptions, and utilities.

## Table of Contents

- [Core Functions](#core-functions)
  - [create_isochrone()](#create_isochrone)
  - [get_poi()](#get_poi)
  - [get_census_blocks()](#get_census_blocks)
  - [get_census_data()](#get_census_data)
  - [create_map()](#create_map)
- [Demo Module](#demo-module)
- [Performance Module](#performance-module)
- [Result Types](#result-types)
- [Exception Classes](#exception-classes)
- [Type Models](#type-models)

---

## Core Functions

### create_isochrone()

Create a travel-time polygon (isochrone) from a location.

```python
def create_isochrone(
    location: str | tuple[float, float],
    travel_time: int = 15,
    travel_mode: str = "drive"
) -> dict[str, Any]
```

Generates an isochrone showing the area reachable within a specified travel time from a given location using a specific mode of transport.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `location` | `str` or `tuple[float, float]` | Required | Either a "City, State" string for geocoding or a (latitude, longitude) tuple with coordinates |
| `travel_time` | `int` | `15` | Travel time in minutes. Must be between 1 and 120 |
| `travel_mode` | `str` | `"drive"` | Mode of transportation: `"drive"`, `"walk"`, or `"bike"` |

#### Returns

**`dict`** - GeoJSON Feature containing:
- `'type'`: Always "Feature"
- `'geometry'`: GeoJSON polygon of the isochrone
- `'properties'`: Dict with:
  - `location`: Location name or coordinates
  - `travel_time`: Travel time in minutes
  - `travel_mode`: Mode of transportation
  - `area_sq_km`: Area in square kilometers

#### Raises

- **`ValidationError`** - If travel_time is not between 1-120, travel_mode is invalid, or location cannot be geocoded

#### Examples

```python
# Using coordinates (recommended for precision)
iso = create_isochrone((45.5152, -122.6784), travel_time=20)
print(f"Area: {iso['properties']['area_sq_km']:.2f} km²")
# Output: Area: 125.34 km²

# Using city/state string (requires geocoding)
iso = create_isochrone("Portland, OR", travel_time=15, travel_mode="walk")
print(f"Travel mode: {iso['properties']['travel_mode']}")
# Output: Travel mode: walk

# Different travel modes comparison
drive_iso = create_isochrone((40.7128, -74.0060), travel_time=10, travel_mode="drive")
bike_iso = create_isochrone((40.7128, -74.0060), travel_time=10, travel_mode="bike")
walk_iso = create_isochrone((40.7128, -74.0060), travel_time=10, travel_mode="walk")

print(f"Drive: {drive_iso['properties']['area_sq_km']:.2f} km²")
print(f"Bike:  {bike_iso['properties']['area_sq_km']:.2f} km²")
print(f"Walk:  {walk_iso['properties']['area_sq_km']:.2f} km²")
```

#### Performance Considerations

- **Caching**: Network graphs are cached by location to speed up repeated queries
- **Travel time**: Larger travel times (>30 minutes) may take longer to compute
- **Urban areas**: Dense road networks may increase computation time
- **First run**: Initial isochrone for a new area downloads and processes OSM network data

#### Common Patterns

```python
# Create isochrone and save to GeoJSON
iso = create_isochrone("Seattle, WA", travel_time=20)
import json
with open('seattle_20min.geojson', 'w') as f:
    json.dump(iso, f)

# Use isochrone as boundary for other queries
iso = create_isochrone((47.6062, -122.3321), travel_time=15)
blocks = get_census_blocks(polygon=iso)
pois = get_poi(location=(47.6062, -122.3321), travel_time=15)
```

---

### get_poi()

Get points of interest near a location.

```python
def get_poi(
    location: str | tuple[float, float],
    categories: list[str] | None = None,
    travel_time: int | None = None,
    limit: int = 100,
    validate_coords: bool = True
) -> list[dict[str, Any]]
```

Retrieves POIs from OpenStreetMap within a specified area, either defined by travel time or radius.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `location` | `str` or `tuple[float, float]` | Required | Either "City, State" string or (latitude, longitude) tuple |
| `categories` | `list[str]` or `None` | `None` | POI categories to filter (see available categories below). If None, returns all categories |
| `travel_time` | `int` or `None` | `None` | Travel time in minutes for boundary (uses driving). If None, uses 5km radius |
| `limit` | `int` | `100` | Maximum number of POIs to return |
| `validate_coords` | `bool` | `True` | Whether to validate POI coordinates and filter invalid ones |

#### Available POI Categories

Use these high-level category names:

| Category | Includes |
|----------|----------|
| `"food_and_drink"` | Restaurants, cafes, bars, bakeries, fast food |
| `"education"` | Schools, universities, libraries, kindergartens |
| `"healthcare"` | Hospitals, clinics, pharmacies, doctors, dentists |
| `"recreation"` | Parks, playgrounds, sports centres, theatres, cinemas |
| `"shopping"` | Supermarkets, malls, convenience stores, retail |
| `"services"` | Banks, ATMs, post offices, salons |
| `"transportation"` | Bus stations, parking, fuel stations |
| `"accommodation"` | Hotels, hostels, motels |
| `"religious"` | Churches, mosques, temples |
| `"utilities"` | Police, fire stations, government offices |

#### Returns

**`list[dict]`** - POIs sorted by distance from origin, each containing:
- `'name'`: POI name (str)
- `'category'`: POI category (str)
- `'lat'`: Latitude (float)
- `'lon'`: Longitude (float)
- `'distance_km'`: Distance from origin in kilometers (float)
- `'address'`: Address if available (str or None)
- `'tags'`: Additional OSM tags (dict)

#### Raises

- **`InvalidPOICategoryError`** - If an invalid category is specified
- **`ValidationError`** - If travel_time is provided but not between 1-120

#### Examples

```python
# Find food and drink POIs within 5km radius (default)
pois = get_poi(
    location="Seattle, WA",
    categories=["food_and_drink"]
)
print(f"Found {len(pois)} food and drink places")
# Output: Found 75 food and drink places

# POIs within 15-minute drive
pois = get_poi(
    location=(47.6062, -122.3321),
    travel_time=15,
    categories=["healthcare"]
)
print(f"Healthcare facilities: {len(pois)}")
for poi in pois[:3]:
    print(f"  {poi['name']}: {poi['distance_km']:.2f} km away")
# Output: Healthcare facilities: 12
#   Seattle Medical Center: 0.54 km away
#   Harborview Medical: 1.23 km away

# All POIs within radius (no category filter)
pois = get_poi(
    location=(40.7128, -74.0060),
    limit=50
)

# Find closest POI of each type
from collections import defaultdict
closest_by_category = defaultdict(lambda: {'name': None, 'distance': float('inf')})

for poi in pois:
    cat = poi['category']
    dist = poi['distance_km']
    if dist < closest_by_category[cat]['distance']:
        closest_by_category[cat] = {'name': poi['name'], 'distance': dist}

for category, info in sorted(closest_by_category.items()):
    print(f"{category}: {info['name']} ({info['distance']:.2f} km)")
```

#### Performance Considerations

- **Category filtering**: More categories = slower query. Use specific categories when possible
- **Travel time**: Setting `travel_time` generates an isochrone first, adding computation time
- **Coordinate validation**: Set `validate_coords=False` if you know coordinates are valid
- **Large areas**: Urban areas with many POIs may be slower; use `limit` to cap results

---

### get_census_blocks()

Get census block groups for a geographic area.

```python
def get_census_blocks(
    polygon: dict | None = None,
    location: tuple[float, float] | None = None,
    radius_km: float = 5
) -> list[dict[str, Any]]
```

Retrieves census block group boundaries that intersect with either a polygon or a circular area around a point.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `polygon` | `dict` or `None` | `None` | GeoJSON Feature or geometry dict, typically from `create_isochrone()`. Either polygon or location must be provided |
| `location` | `tuple[float, float]` or `None` | `None` | (latitude, longitude) coordinates for center point. Creates circular area with radius_km |
| `radius_km` | `float` | `5` | Radius in kilometers when using location parameter. Must be > 0 and <= 100 |

#### Returns

**`list[dict]`** - List of census block groups, each containing:
- `'geoid'`: 12-digit census block group ID (str)
- `'state_fips'`: 2-digit state FIPS code (str)
- `'county_fips'`: 3-digit county FIPS code (str)
- `'tract'`: 6-digit census tract code (str)
- `'block_group'`: 1-digit block group number (str)
- `'geometry'`: GeoJSON polygon geometry (dict)
- `'area_sq_km'`: Area in square kilometers (float)

#### Raises

- **`ValidationError`** - If neither polygon nor location is provided, or if both are provided
- **`ValidationError`** - If radius_km is not within valid range

#### Examples

```python
# Using an isochrone polygon
iso = create_isochrone("San Francisco, CA", travel_time=15)
blocks = get_census_blocks(polygon=iso)
print(f"Found {len(blocks)} census block groups")
# Output: Found 42 census block groups

# Using a point and radius
blocks = get_census_blocks(
    location=(37.7749, -122.4194),
    radius_km=3
)
print(f"Block group ID: {blocks[0]['geoid']}")
# Output: Block group ID: 060750201001

# Access block details
for block in blocks[:3]:
    print(f"GEOID: {block['geoid']}, Area: {block['area_sq_km']:.2f} km²")

# Extract GEOIDs for census data queries
geoids = [block['geoid'] for block in blocks]
census_data = get_census_data(location=geoids, variables=['population'])
```

#### Understanding Census Block Groups

Census block groups are statistical divisions used by the U.S. Census Bureau:

- **GEOID Format**: 12 characters: `SSCCCTTTTTTB`
  - `SS`: State FIPS (2 digits)
  - `CCC`: County FIPS (3 digits)
  - `TTTTTT`: Census Tract (6 digits)
  - `B`: Block Group (1 digit)

Example: `530330051001`
- State: 53 (Washington)
- County: 033 (King County)
- Tract: 005100
- Block Group: 1

#### Performance Considerations

- **Polygon complexity**: Complex polygons with many vertices take longer
- **Area size**: Larger areas intersect more block groups
- **Caching**: Results are not automatically cached; cache manually if reusing

---

### get_census_data()

Get census demographic data for specified locations.

```python
def get_census_data(
    location: dict | list[str] | tuple[float, float],
    variables: list[str],
    year: int = 2023
) -> CensusDataResult
```

Retrieves census data for various geographic units. Supports multiple input formats and automatically handles different census geographic levels.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `location` | `dict`, `list[str]`, or `tuple[float, float]` | Required | Location specification (see format options below) |
| `variables` | `list[str]` | Required | Census variables to retrieve (see available variables below) |
| `year` | `int` | `2023` | Census year for ACS 5-year estimates (2010-2023) |

#### Location Format Options

**1. GeoJSON Polygon (dict):**
```python
# Use isochrone or custom polygon
iso = create_isochrone("Denver, CO", travel_time=20)
data = get_census_data(location=iso, variables=['population'])
```

**2. List of GEOIDs (list[str]):**
```python
# Specific block groups
geoids = ["060750201001", "060750201002"]
data = get_census_data(location=geoids, variables=['population'])
```

**3. Point Coordinates (tuple[float, float]):**
```python
# Single point - returns data for containing block group
data = get_census_data(
    location=(37.7749, -122.4194),
    variables=['population']
)
```

#### Available Variables

**Common variable names** (automatically mapped to Census codes):

| Variable Name | Description | Census Code |
|---------------|-------------|-------------|
| `"population"` | Total population | B01003_001E |
| `"median_income"` | Median household income | B19013_001E |
| `"median_age"` | Median age | B01002_001E |
| `"percent_poverty"` | Percent below poverty line | Calculated |
| `"total_housing_units"` | Total housing units | B25001_001E |
| `"median_home_value"` | Median home value | B25077_001E |
| `"median_rent"` | Median gross rent | B25064_001E |
| `"percent_white"` | Percent white alone | Calculated |
| `"percent_black"` | Percent Black or African American | Calculated |
| `"percent_hispanic"` | Percent Hispanic or Latino | Calculated |
| `"percent_asian"` | Percent Asian alone | Calculated |
| `"unemployment_rate"` | Unemployment rate | Calculated |

**You can also use raw Census variable codes:**
```python
variables = ["B01003_001E", "B19013_001E", "B01002_001E"]
```

For a complete list, see: https://api.census.gov/data/2023/acs/acs5/variables.html

#### Returns

**`CensusDataResult`** - Pydantic model containing:

```python
class CensusDataResult(BaseModel):
    data: dict[str, dict[str, Any]]  # {geoid: {variable: value, ...}}
    location_type: Literal["polygon", "geoids", "point"]
    query_info: dict[str, Any]  # Metadata about the query
```

**Attributes:**
- `data`: Census data as nested dict `{geoid: {variable: value, ...}}`
- `location_type`: Type of location query performed
- `query_info`: Contains `year`, `variables`, `variable_codes`, `geoid_count`

#### Raises

- **`MissingAPIKeyError`** - If CENSUS_API_KEY environment variable not set
- **`ValidationError`** - If invalid location format or invalid year
- **`APIError`** - If Census API request fails

#### Examples

```python
# From an isochrone
iso = create_isochrone("Denver, CO", travel_time=20)
result = get_census_data(iso, ["population", "median_income"])
print(f"Number of block groups: {len(result.data)}")
# Output: Number of block groups: 35

# Calculate total population
total_pop = sum(
    data.get('population', 0)
    for data in result.data.values()
)
print(f"Total population: {total_pop:,}")
# Output: Total population: 45,678

# From specific GEOIDs
result = get_census_data(
    location=["060750201001"],
    variables=["population", "median_income", "median_age"]
)
geoid = "060750201001"
print(f"Population: {result.data[geoid]['population']}")
# Output: Population: 2543

# From a point location
result = get_census_data(
    location=(40.7128, -74.0060),
    variables=["population", "median_income"]
)
# Returns data for the block group containing this point

# Using different year
result = get_census_data(
    location=geoids,
    variables=["population"],
    year=2022
)

# Access structured result
print(f"Query type: {result.location_type}")
print(f"Year: {result.query_info['year']}")
print(f"GEOIDs queried: {result.query_info['geoid_count']}")
```

#### Data Aggregation Patterns

```python
# Total population across all block groups
blocks = get_census_blocks(polygon=isochrone)
geoids = [b['geoid'] for b in blocks]
census_data = get_census_data(geoids, ["population", "median_income"])

total_pop = sum(d.get('population', 0) for d in census_data.data.values())

# Average median income (excluding zeros/nulls)
incomes = [
    d.get('median_income', 0)
    for d in census_data.data.values()
    if d.get('median_income', 0) > 0
]
avg_income = sum(incomes) / len(incomes) if incomes else 0

# Population-weighted average income
weighted_income = sum(
    d.get('population', 0) * d.get('median_income', 0)
    for d in census_data.data.values()
    if d.get('median_income', 0) > 0
) / total_pop if total_pop > 0 else 0

print(f"Total population: {total_pop:,}")
print(f"Average income: ${avg_income:,.0f}")
print(f"Population-weighted income: ${weighted_income:,.0f}")
```

#### Performance Considerations

- **Batch requests**: Request multiple variables in one call for efficiency
- **Rate limiting**: Census API has rate limits; SocialMapper handles this automatically
- **Caching**: Results are cached to minimize API calls
- **Large queries**: Queries with >500 GEOIDs may be split into batches

---

### create_map()

Create a choropleth map visualization.

```python
def create_map(
    data: list[dict] | pd.DataFrame | gpd.GeoDataFrame,
    column: str,
    title: str | None = None,
    save_path: str | None = None,
    export_format: str = "png"
) -> MapResult
```

Generates a thematic map where geographic areas are colored according to the values of a data variable. Always returns a MapResult object for consistent return types regardless of format or save behavior.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `list[dict]`, `DataFrame`, or `GeoDataFrame` | Required | Geographic data to visualize (see format options below) |
| `column` | `str` | Required | Name of the data column to visualize on the map |
| `title` | `str` or `None` | `None` | Title to display on the map |
| `save_path` | `str` or `None` | `None` | Path to save the map file. If None, returns data in memory |
| `export_format` | `str` | `"png"` | Output format: `"png"`, `"pdf"`, `"svg"`, `"geojson"`, or `"shapefile"` |

#### Data Format Options

**1. List of Dictionaries:**
```python
blocks = get_census_blocks(polygon=iso)
# Add data to blocks
for block in blocks:
    block['population'] = census_data.data[block['geoid']]['population']

result = create_map(blocks, column='population')
```

**2. Pandas DataFrame:**
```python
import pandas as pd
from shapely.geometry import shape

df = pd.DataFrame(blocks)
df['geometry'] = df['geometry'].apply(shape)
result = create_map(df, column='population')
```

**3. GeoDataFrame:**
```python
import geopandas as gpd

gdf = gpd.GeoDataFrame(blocks, geometry='geometry', crs="EPSG:4326")
result = create_map(gdf, column='population')
```

#### Returns

**`MapResult`** - Pydantic model containing:

```python
class MapResult(BaseModel):
    format: Literal["png", "pdf", "svg", "geojson", "shapefile"]
    image_data: bytes | None = None
    geojson_data: dict | None = None
    file_path: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

**Attributes:**
- `format`: The export format used
- `image_data`: Raw bytes for image formats (PNG, PDF, SVG) when not saved
- `geojson_data`: GeoJSON dict when format is "geojson" and not saved
- `file_path`: Absolute path to saved file when `save_path` provided
- `metadata`: Additional info (column name, title, feature count, etc.)

#### Raises

- **`ValueError`** - If column not found in data
- **`ValueError`** - If invalid export format
- **`ValueError`** - If shapefile format without save_path
- **`ValidationError`** - If data format is invalid or missing required fields

#### Examples

```python
# Create map and get image bytes
iso = create_isochrone((40.7128, -74.0060), travel_time=15)
blocks = get_census_blocks(polygon=iso)
geoids = [b['geoid'] for b in blocks]
census_data = get_census_data(geoids, ["population"])

# Add population to blocks
for block in blocks:
    geoid = block['geoid']
    block['population'] = census_data.data.get(geoid, {}).get('population', 0)

# Create PNG map in memory
map_result = create_map(blocks, "population", title="Population by Block Group")
print(f"Format: {map_result.format}")
print(f"Image size: {len(map_result.image_data)} bytes")
# Output: Format: png
#         Image size: 45231 bytes

# Save as file
map_result = create_map(
    blocks,
    column="population",
    title="Population Distribution",
    save_path="population_map.png"
)
print(f"Saved to: {map_result.file_path}")
# Output: Saved to: /absolute/path/to/population_map.png

# Export as GeoJSON
map_result = create_map(blocks, "population", export_format="geojson")
print(f"Features: {len(map_result.geojson_data['features'])}")

# Export as shapefile (requires save_path)
map_result = create_map(
    blocks,
    column="population",
    save_path="output.shp",
    export_format="shapefile"
)

# Generate PDF report map
map_result = create_map(
    blocks,
    column="median_income",
    title="Median Income Distribution",
    save_path="income_map.pdf",
    export_format="pdf"
)
```

#### Export Format Details

| Format | Returns | Use Case | Requires save_path |
|--------|---------|----------|-------------------|
| `png` | Image bytes or file | Web display, presentations | No |
| `pdf` | PDF bytes or file | Reports, printing | No |
| `svg` | SVG bytes or file | Editing, scalable graphics | No |
| `geojson` | GeoJSON dict or file | Web mapping, GIS import | No |
| `shapefile` | File path | GIS software (ArcGIS, QGIS) | Yes |

#### Styling and Customization

The map automatically uses:
- **Color scheme**: Sequential colors based on data values
- **Classification**: Natural breaks (Jenks) for optimal data distribution
- **Legend**: Automatic legend with value ranges
- **Basemap**: Optional contextual basemap (requires Mapbox token)

#### Performance Considerations

- **Feature count**: Maps with >1000 features may be slow; consider aggregating
- **Export format**: Vector formats (PDF, SVG) are slower but scalable
- **Shapefile**: Creates multiple files (.shp, .shx, .dbf, .prj)
- **Memory**: Large image maps consume more memory; save to disk for large datasets

---

## Demo Module

The demo module provides sample data and quick-start functions for exploring SocialMapper without API keys.

### Available Demo Locations

| Location | Description |
|----------|-------------|
| `"Portland, OR"` | Rose City with excellent library coverage |
| `"Chapel Hill, NC"` | College town with strong community amenities |
| `"Durham, NC"` | Bull City with vibrant food scene |

### Functions

```python
from socialmapper import demo
```

#### demo.list_available_demos()

Display all available demo locations in a formatted table.

```python
demo.list_available_demos()
```

#### demo.quick_start()

Run complete accessibility analysis with cached demo data.

```python
result = demo.quick_start(
    location="Portland, OR",  # Must be one of the available demo locations
    travel_time=15,           # 5, 10, 15, 20, or 30 minutes
    travel_mode="drive"       # "drive", "walk", or "bike"
)

# Returns dict with:
# - location, isochrone, poi_count, pois
# - total_population, median_income
# - census_blocks, area_sq_km
```

#### demo.show_libraries()

Analyze library accessibility for a demo location.

```python
result = demo.show_libraries("Chapel Hill, NC", travel_time=15)
print(f"{result['library_count']} libraries")
print(f"Serving {result['population_served']:,} people")
```

#### demo.show_food_access()

Analyze food access for a demo location.

```python
result = demo.show_food_access("Durham, NC", travel_time=15)
print(f"{result['grocery_count']} grocery stores")
print(f"{result['restaurant_count']} restaurants")
```

---

## Result Types

SocialMapper uses Pydantic models for structured, type-safe results.

### CensusDataResult

```python
class CensusDataResult(BaseModel):
    data: dict[str, dict[str, Any]]  # {geoid: {variable: value}}
    location_type: Literal["polygon", "geoids", "point"]
    query_info: dict[str, Any]
```

### MapResult

```python
class MapResult(BaseModel):
    format: Literal["png", "pdf", "svg", "geojson", "shapefile"]
    image_data: bytes | None
    geojson_data: dict | None
    file_path: Path | None
    metadata: dict[str, Any]
```

### IsochroneResult

```python
class IsochroneResult(BaseModel):
    geometry: dict
    location: str
    travel_time: int
    travel_mode: str
    area_sq_km: float

    def to_geojson(self) -> dict:
        """Convert to GeoJSON Feature."""
        ...
```

---

## Exception Classes

All exceptions inherit from `SocialMapperError` for easy catching.

### Exception Hierarchy

```
SocialMapperError
├── ValidationError
├── APIError
│   ├── NetworkError
│   ├── RateLimitError
│   └── InvalidAPIResponseError
├── DataError
└── AnalysisError
```

### Specific Exceptions

#### MissingAPIKeyError

```python
from socialmapper import MissingAPIKeyError

try:
    result = get_census_data(geoids, ['population'])
except MissingAPIKeyError as e:
    print(f"API key missing: {e}")
    print(e.help_text)  # Provides setup instructions
```

#### InvalidLocationError

```python
from socialmapper import InvalidLocationError

try:
    iso = create_isochrone("Nonexistent City, XX")
except InvalidLocationError as e:
    print(f"Location error: {e}")
    # Provides suggestions for valid locations
```

#### InvalidPOICategoryError

```python
from socialmapper import InvalidPOICategoryError

try:
    pois = get_poi("Portland, OR", categories=["invalid_category"])
except InvalidPOICategoryError as e:
    print(f"Invalid category: {e}")
    # Lists valid categories
```

#### NetworkError

```python
from socialmapper import NetworkError

try:
    result = get_census_data(geoids, ['population'])
except NetworkError as e:
    print(f"Network issue: {e}")
    # Provides troubleshooting tips
```

#### RateLimitError

```python
from socialmapper import RateLimitError

try:
    # Many rapid API calls
    results = [get_census_data([geoid], ['population']) for geoid in many_geoids]
except RateLimitError as e:
    print(f"Rate limited: {e}")
    print(f"Retry after: {e.retry_after} seconds")
```

### Error Handling Best Practices

```python
from socialmapper import SocialMapperError, ValidationError, APIError

try:
    iso = create_isochrone(location, travel_time)
    blocks = get_census_blocks(polygon=iso)
    census_data = get_census_data([b['geoid'] for b in blocks], variables)

except ValidationError as e:
    # Handle user input errors
    logger.error(f"Invalid input: {e}")
    # Show user-friendly error message

except APIError as e:
    # Handle external API failures
    logger.error(f"API error: {e}")
    # Retry with exponential backoff

except SocialMapperError as e:
    # Catch any other library errors
    logger.error(f"SocialMapper error: {e}")

except Exception as e:
    # Catch unexpected errors
    logger.exception("Unexpected error occurred")
    raise
```

---

## Type Models

### Request Models

Pydantic models for validating API requests.

#### IsochroneRequest

```python
class IsochroneRequest(BaseModel):
    location: str | tuple[float, float]
    travel_time: int = Field(ge=1, le=120, default=15)
    travel_mode: Literal["drive", "walk", "bike"] = "drive"
```

#### CensusBlocksRequest

```python
class CensusBlocksRequest(BaseModel):
    polygon: dict | None = None
    location: tuple[float, float] | None = None
    radius_km: float = Field(gt=0, le=100, default=5)
```

#### CensusDataRequest

```python
class CensusDataRequest(BaseModel):
    location: dict | list[str] | tuple[float, float]
    variables: list[str] = Field(min_length=1)
    year: int = Field(ge=2010, le=2023, default=2023)
```

#### MapRequest

```python
class MapRequest(BaseModel):
    column: str
    title: str | None = None
    save_path: Path | None = None
    export_format: Literal["png", "pdf", "svg", "geojson", "shapefile"] = "png"
```

#### POIRequest

```python
class POIRequest(BaseModel):
    location: str | tuple[float, float]
    categories: list[str] | None = None
    travel_time: int | None = Field(None, ge=1, le=120)
    limit: int = Field(default=100, ge=1, le=1000)
    validate_coords: bool = True
```

### Domain Models

#### CensusBlock

```python
class CensusBlock(BaseModel):
    geoid: str
    state_fips: str
    county_fips: str
    tract: str
    block_group: str
    geometry: dict
    area_sq_km: float
```

#### DiscoveredPOI

```python
class DiscoveredPOI(BaseModel):
    osm_id: int
    name: str | None
    category: str
    subcategory: str | None
    latitude: float
    longitude: float
    distance_meters: float
    travel_time_minutes: float | None
    tags: dict[str, Any]
    address: str | None
```

---

## Version Information

```python
import socialmapper

print(socialmapper.__version__)
# Output: 1.0.0
```

---

## Additional Resources

- [Quick Start Guide](quick-start.md) - Get started in 2 minutes
- [Performance Guide](performance.md) - Performance optimization tips
- [Examples](https://github.com/mihiarc/socialmapper/tree/main/examples) - Working code examples
- [Census Variables](https://api.census.gov/data/2023/acs/acs5/variables.html) - Complete Census variable list

---

**Version**: 1.0.0
