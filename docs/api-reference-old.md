# API Reference

SocialMapper provides a simple, functional API for spatial analysis and demographic data retrieval. No classes or configuration needed - just import and use the functions directly.

## Installation

```bash
pip install socialmapper
```

## Quick Start

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data

# Create a 15-minute driving isochrone
isochrone = create_isochrone(
    location=(45.5152, -122.6784),  # Portland, OR
    travel_time=15,
    travel_mode="drive"
)

# Get census blocks within the isochrone
blocks = get_census_blocks(polygon=isochrone)

# Fetch demographic data
geoids = [block['geoid'] for block in blocks]
demographics = get_census_data(
    location=geoids,
    variables=["population", "median_income", "median_age"],
    year=2023
)

print(f"Area covered: {isochrone['properties']['area_sq_km']:.2f} km²")
print(f"Census blocks: {len(blocks)}")
print(f"Total population: {sum(d.get('population', 0) for d in demographics.values()):,}")
```

## Core Functions

SocialMapper exports five core functions for spatial analysis:

### create_isochrone()

Create a travel-time polygon (isochrone) from a location.

```python
def create_isochrone(
    location: Union[str, Tuple[float, float]],
    travel_time: int = 15,
    travel_mode: str = "drive"
) -> Dict[str, Any]
```

**Parameters:**

- **location** : `str` or `tuple of float`
  - Either a "City, State" string for geocoding or a (latitude, longitude) tuple with coordinates.
- **travel_time** : `int`, optional
  - Travel time in minutes. Must be between 1 and 120. Default is 15.
- **travel_mode** : `{'drive', 'walk', 'bike'}`, optional
  - Mode of transportation. Default is 'drive'.

**Returns:**

- **dict** : GeoJSON Feature containing:
  - `'type'`: Always "Feature"
  - `'geometry'`: GeoJSON polygon of the isochrone
  - `'properties'`: Dict with location, travel_time, travel_mode, and area_sq_km

**Raises:**

- **ValidationError** : If travel_time is not between 1-120, travel_mode is invalid, or location cannot be geocoded.

**Examples:**

```python
# Using coordinates (recommended)
iso = create_isochrone((45.5152, -122.6784), travel_time=20)
print(f"Area: {iso['properties']['area_sq_km']:.2f} km²")
# Output: Area: 125.34 km²

# Using city/state string (requires geocoding)
iso = create_isochrone("Portland, OR", travel_time=15, travel_mode="walk")
print(f"Travel mode: {iso['properties']['travel_mode']}")
# Output: Travel mode: walk

# Different travel modes
drive_iso = create_isochrone((40.7128, -74.0060), travel_time=10, travel_mode="drive")
bike_iso = create_isochrone((40.7128, -74.0060), travel_time=10, travel_mode="bike")
walk_iso = create_isochrone((40.7128, -74.0060), travel_time=10, travel_mode="walk")

print(f"Drive: {drive_iso['properties']['area_sq_km']:.2f} km²")
print(f"Bike:  {bike_iso['properties']['area_sq_km']:.2f} km²")
print(f"Walk:  {walk_iso['properties']['area_sq_km']:.2f} km²")
```

---

### get_census_blocks()

Get census block groups for a geographic area.

```python
def get_census_blocks(
    polygon: Optional[Dict] = None,
    location: Optional[Tuple[float, float]] = None,
    radius_km: float = 5
) -> List[Dict[str, Any]]
```

**Parameters:**

- **polygon** : `dict`, optional
  - GeoJSON Feature or geometry dict, typically from `create_isochrone()`. Either polygon or location must be provided.
- **location** : `tuple of float`, optional
  - (latitude, longitude) coordinates for center point. Creates circular area with radius_km.
- **radius_km** : `float`, optional
  - Radius in kilometers when using location parameter. Default is 5.

**Returns:**

- **list of dict** : List of census block groups, each containing:
  - `'geoid'`: 12-digit census block group ID
  - `'state_fips'`: 2-digit state FIPS code
  - `'county_fips'`: 3-digit county FIPS code
  - `'tract'`: 6-digit census tract code
  - `'block_group'`: 1-digit block group number
  - `'geometry'`: GeoJSON polygon geometry
  - `'area_sq_km'`: Area in square kilometers

**Raises:**

- **ValidationError** : If neither polygon nor location is provided, or if both are provided.

**Examples:**

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
```

---

### get_census_data()

Get census demographic data for specified locations.

```python
def get_census_data(
    location: Union[Dict, List[str], Tuple[float, float]],
    variables: List[str],
    year: int = 2023
) -> Dict[str, Any]
```

**Parameters:**

- **location** : `dict`, `list of str`, or `tuple of float`
  - Location specification:
    - `dict`: GeoJSON Feature/geometry from `create_isochrone()`
    - `list`: GEOID strings like `["060750201001", ...]`
    - `tuple`: (latitude, longitude) for single point
- **variables** : `list of str`
  - Census variables to retrieve. Can be:
    - Common names: `["population", "median_income", "median_age"]`
    - Census codes: `["B01003_001E", "B19013_001E", "B01002_001E"]`
- **year** : `int`, optional
  - Census year for ACS 5-year estimates. Default is 2023.

**Returns:**

- **dict** : Census data organized by location:
  - For polygon/GEOIDs: `{geoid: {variable: value, ...}, ...}`
  - For point: `{variable: value, ...}`

**Examples:**

```python
# From an isochrone
iso = create_isochrone("Denver, CO", travel_time=20)
data = get_census_data(
    location=iso,
    variables=["population", "median_income"]
)
print(f"Number of block groups: {len(data)}")
# Output: Number of block groups: 35

# Calculate total population
total_pop = sum(d.get('population', 0) for d in data.values())
print(f"Total population: {total_pop:,}")
# Output: Total population: 45,678

# From specific GEOIDs
geoids = ["060750201001", "060750201002"]
data = get_census_data(
    location=geoids,
    variables=["population", "median_income", "median_age"]
)

for geoid, values in data.items():
    print(f"{geoid}: {values.get('population', 0)} people")
# Output: 060750201001: 2543 people

# From a single point
data = get_census_data(
    location=(40.7128, -74.0060),
    variables=["population"]
)
print(f"Population: {data.get('population', 0)}")
# Output: Population: 3421

# Using different year
data = get_census_data(
    location=geoids,
    variables=["population"],
    year=2022
)
```

**Available Variables:**

Common variable names (automatically mapped to Census codes):

- `"population"` → Total population
- `"median_income"` → Median household income
- `"median_age"` → Median age
- `"percent_poverty"` → Percent below poverty line
- `"total_housing_units"` → Total housing units
- `"median_home_value"` → Median home value

For more variables, see the [Census Variables Reference](reference/census-variables.md).

---

### create_map()

Create a choropleth map visualization.

```python
def create_map(
    data: Union[List[Dict], pd.DataFrame, gpd.GeoDataFrame],
    column: str,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    export_format: str = "png"
) -> Optional[Union[bytes, Dict]]
```

**Parameters:**

- **data** : `list of dict`, `DataFrame`, or `GeoDataFrame`
  - Geographic data to visualize:
    - `list`: Dicts with 'geometry' key and data columns
    - `DataFrame`: Must have a 'geometry' column
    - `GeoDataFrame`: GeoPandas GeoDataFrame
- **column** : `str`
  - Name of the data column to visualize on the map.
- **title** : `str`, optional
  - Title to display on the map. Default is None.
- **save_path** : `str`, optional
  - Path to save the map file. If None, returns data. Default is None.
- **export_format** : `{'png', 'pdf', 'svg', 'geojson', 'shapefile'}`, optional
  - Output format for the map. Default is 'png'.

**Returns:**

- **bytes**, **dict**, or **None**
  - Image formats (png/pdf/svg): bytes if save_path is None
  - geojson: dict if save_path is None
  - shapefile: None (requires save_path)
  - All formats: None if save_path is provided

**Raises:**

- **ValueError** : If column not found in data, invalid export format, or shapefile format without save_path.

**Examples:**

```python
# Create map from census blocks with population data
iso = create_isochrone((40.7128, -74.0060), travel_time=15)
blocks = get_census_blocks(polygon=iso)
geoids = [b['geoid'] for b in blocks]
census_data = get_census_data(geoids, ["population"])

# Add population to blocks
for block in blocks:
    geoid = block['geoid']
    block['population'] = census_data.get(geoid, {}).get('population', 0)

# Create and save map
create_map(
    data=blocks,
    column="population",
    title="Population by Block Group",
    save_path="population_map.png",
    export_format="png"
)

# Return map as bytes without saving
img_bytes = create_map(
    data=blocks,
    column="population",
    title="Population Distribution"
)

# Export as GeoJSON
geojson = create_map(
    data=blocks,
    column="population",
    export_format="geojson"
)

# Save as shapefile
create_map(
    data=blocks,
    column="population",
    save_path="output.shp",
    export_format="shapefile"
)
```

---

### get_poi()

Get points of interest near a location.

```python
def get_poi(
    location: Union[str, Tuple[float, float]],
    categories: Optional[List[str]] = None,
    travel_time: Optional[int] = None,
    limit: int = 100,
    validate_coords: bool = True
) -> List[Dict[str, Any]]
```

**Parameters:**

- **location** : `str` or `tuple of float`
  - Either "City, State" string or (latitude, longitude) tuple.
- **categories** : `list of str`, optional
  - POI categories to filter. Options include:
    - Food: `"restaurant"`, `"cafe"`, `"bar"`, `"fast_food"`
    - Education: `"school"`, `"university"`, `"library"`
    - Health: `"hospital"`, `"clinic"`, `"pharmacy"`
    - Recreation: `"park"`, `"playground"`, `"sports"`
    - Shopping: `"grocery"`, `"supermarket"`, `"convenience"`
    - Finance: `"bank"`, `"atm"`
  - Default is None (all categories).
- **travel_time** : `int`, optional
  - Travel time in minutes for boundary (uses driving). If provided, finds POIs within isochrone. If None, uses 5km radius. Default is None.
- **limit** : `int`, optional
  - Maximum number of POIs to return. Default is 100.
- **validate_coords** : `bool`, optional
  - Whether to validate POI coordinates. Default is True.

**Returns:**

- **list of dict** : POIs sorted by distance, each containing:
  - `'name'`: POI name
  - `'category'`: POI category
  - `'lat'`: Latitude
  - `'lon'`: Longitude
  - `'distance_km'`: Distance from origin
  - `'address'`: Address if available
  - `'tags'`: Additional OSM tags

**Examples:**

```python
# Find restaurants within 5km radius
pois = get_poi(
    location="Seattle, WA",
    categories=["restaurant", "cafe"]
)
print(f"Found {len(pois)} restaurants and cafes")
# Output: Found 75 restaurants and cafes

# POIs within 15-minute drive
pois = get_poi(
    location=(47.6062, -122.3321),
    travel_time=15,
    categories=["hospital", "clinic"]
)
print(f"Healthcare facilities: {len(pois)}")
for poi in pois[:3]:
    print(f"  {poi['name']}: {poi['distance_km']:.2f} km away")
# Output: Healthcare facilities: 12
#   Seattle Medical Center: 0.54 km away

# All POIs within radius
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

---

## Error Handling

SocialMapper uses standard Python exceptions for error handling. All functions may raise exceptions that inherit from `SocialMapperError`.

### Exception Hierarchy

```python
SocialMapperError              # Base exception
├── ValidationError            # Invalid input parameters
├── APIError                   # External API errors
├── DataError                  # Data processing errors
└── AnalysisError              # Analysis computation errors
```

### Exception Examples

```python
from socialmapper import (
    create_isochrone,
    ValidationError,
    APIError
)

try:
    # Invalid travel time
    iso = create_isochrone((45.5152, -122.6784), travel_time=150)
except ValidationError as e:
    print(f"Validation error: {e}")
    # Output: Validation error: travel_time must be between 1 and 120 minutes

try:
    # Network or API issue
    census_data = get_census_data(geoids, ["population"])
except APIError as e:
    print(f"API error: {e}")
    # Output: API error: Census API request failed

# Catch all SocialMapper errors
from socialmapper import SocialMapperError

try:
    iso = create_isochrone(location, travel_time, travel_mode)
    blocks = get_census_blocks(polygon=iso)
    data = get_census_data([b['geoid'] for b in blocks], variables)
except SocialMapperError as e:
    print(f"SocialMapper error: {e}")
```

---

## Complete Workflow Example

Here's a complete example combining all functions to analyze library accessibility:

```python
from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data,
    create_map
)

# 1. Find libraries in the area
print("Finding libraries...")
libraries = get_poi(
    location=(35.7796, -78.6382),  # Raleigh, NC
    categories=["library"],
    limit=10
)
print(f"Found {len(libraries)} libraries")

# 2. Create 15-minute walking isochrones for each library
print("\nCreating isochrones...")
library_analysis = []

for lib in libraries[:5]:  # Analyze first 5 libraries
    # Create isochrone
    iso = create_isochrone(
        location=(lib['lat'], lib['lon']),
        travel_time=15,
        travel_mode="walk"
    )

    # Get census blocks
    blocks = get_census_blocks(polygon=iso)

    # Get demographics
    if blocks:
        geoids = [b['geoid'] for b in blocks]
        census_data = get_census_data(
            location=geoids,
            variables=["population", "median_income", "percent_poverty"]
        )

        # Calculate totals
        total_pop = sum(d.get('population', 0) for d in census_data.values())
        avg_income = sum(
            d.get('median_income', 0) for d in census_data.values()
            if d.get('median_income', 0) > 0
        ) / len([d for d in census_data.values() if d.get('median_income', 0) > 0])

        library_analysis.append({
            'name': lib['name'],
            'lat': lib['lat'],
            'lon': lib['lon'],
            'area_km2': iso['properties']['area_sq_km'],
            'population_served': total_pop,
            'avg_income': avg_income,
            'blocks': blocks,
            'census_data': census_data
        })

        print(f"  {lib['name']}: {total_pop:,} people within 15-min walk")

# 3. Find the library serving the most people
if library_analysis:
    best_library = max(library_analysis, key=lambda x: x['population_served'])

    print(f"\n📊 Best Coverage:")
    print(f"Library: {best_library['name']}")
    print(f"Population served: {best_library['population_served']:,}")
    print(f"Average income: ${best_library['avg_income']:,.0f}")

    # 4. Create visualization for best library
    print("\nCreating map...")

    # Add population data to blocks
    for block in best_library['blocks']:
        geoid = block['geoid']
        block['population'] = best_library['census_data'].get(
            geoid, {}
        ).get('population', 0)

    # Generate map
    create_map(
        data=best_library['blocks'],
        column='population',
        title=f"Population served by {best_library['name']} (15-min walk)",
        save_path='library_accessibility.png'
    )

    print("Map saved to library_accessibility.png")
```

---

## Working with Results

### GeoJSON Output

All geographic results use standard GeoJSON format, making them easy to use with web mapping libraries and GIS software.

```python
import json

# Create isochrone
iso = create_isochrone((45.5152, -122.6784), travel_time=15)

# Save as GeoJSON file
with open('isochrone.geojson', 'w') as f:
    json.dump(iso, f, indent=2)

# Use with web mapping libraries (Leaflet, Mapbox, etc.)
# The geometry can be directly passed to these libraries
geometry = iso['geometry']
properties = iso['properties']
```

### Data Aggregation

Common patterns for aggregating census data:

```python
# Get census data
blocks = get_census_blocks(polygon=isochrone)
geoids = [b['geoid'] for b in blocks]
census_data = get_census_data(geoids, ["population", "median_income", "median_age"])

# Total population
total_pop = sum(d.get('population', 0) for d in census_data.values())

# Average median income (excluding zeros)
incomes = [d.get('median_income', 0) for d in census_data.values() if d.get('median_income', 0) > 0]
avg_income = sum(incomes) / len(incomes) if incomes else 0

# Median of median ages
ages = [d.get('median_age', 0) for d in census_data.values() if d.get('median_age', 0) > 0]
median_age = sorted(ages)[len(ages) // 2] if ages else 0

# Population-weighted average income
weighted_income = sum(
    d.get('population', 0) * d.get('median_income', 0)
    for d in census_data.values()
    if d.get('median_income', 0) > 0
) / total_pop if total_pop > 0 else 0

print(f"Total population: {total_pop:,}")
print(f"Average income: ${avg_income:,.0f}")
print(f"Median age: {median_age:.1f}")
print(f"Population-weighted income: ${weighted_income:,.0f}")
```

---

## Environment Variables

SocialMapper reads configuration from environment variables:

- `CENSUS_API_KEY` - Your Census Bureau API key (required for census data)
- `SOCIALMAPPER_CACHE_DIR` - Directory for caching network data (default: `.cache`)

Set these in a `.env` file in your project root:

```bash
CENSUS_API_KEY=your-api-key-here
SOCIALMAPPER_CACHE_DIR=/path/to/cache
```

Get a free Census API key at: https://api.census.gov/data/key_signup.html

---

## Performance Tips

### 1. Sample Large Result Sets

When working with many census blocks, sample for faster analysis:

```python
blocks = get_census_blocks(polygon=isochrone)

if len(blocks) > 50:
    # Sample first 50 blocks
    sample_blocks = blocks[:50]
    geoids = [b['geoid'] for b in sample_blocks]

    census_data = get_census_data(geoids, ["population"])

    # Calculate sample statistics
    sample_pop = sum(d.get('population', 0) for d in census_data.values())

    # Extrapolate to full area
    estimated_total = int(sample_pop * len(blocks) / len(sample_blocks))
    print(f"Estimated population: ~{estimated_total:,}")
```

### 2. Reuse Isochrones

Cache isochrone results when analyzing the same location multiple times:

```python
# Create once
isochrone = create_isochrone(location, travel_time=15)

# Use multiple times
blocks = get_census_blocks(polygon=isochrone)
pois = get_poi(location, travel_time=15)  # Uses same boundary
```

### 3. Batch Census Requests

Request multiple variables in one call rather than separate calls:

```python
# Good - single request
data = get_census_data(
    geoids,
    variables=["population", "median_income", "median_age", "percent_poverty"]
)

# Avoid - multiple requests
pop = get_census_data(geoids, ["population"])
income = get_census_data(geoids, ["median_income"])
age = get_census_data(geoids, ["median_age"])
```

---

## See Also

- [Getting Started Guide](getting-started/quick-start.md) - Step-by-step tutorial
- [Census Variables Reference](reference/census-variables.md) - Complete list of available census variables
- [Examples](https://github.com/mihiarc/socialmapper/tree/main/examples) - More code examples
- [User Guide](user-guide/index.md) - In-depth usage guides

---

## Version

Current version: **0.9.0**

Check your installed version:

```python
import socialmapper
print(socialmapper.__version__)
```
