# API Reference

## Modern API (Recommended)

SocialMapper provides a modern, type-safe API with proper error handling and resource management.

### Quick Start

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

# Simple usage
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
    else:
        error = result.unwrap_err()
        print(f"Error: {error.message}")
```

### SocialMapperClient

The main client class for interacting with SocialMapper.

```python
from socialmapper import SocialMapperClient, ClientConfig

# With configuration
config = ClientConfig(
    api_key="your-census-api-key",
    rate_limit=5,  # requests per second
    timeout=600    # seconds
)

with SocialMapperClient(config) as client:
    # Use the client
    pass
```

#### Methods

##### `analyze(location, poi_type, poi_name, **kwargs)`

Simple analysis method for common use cases.

**Parameters:**
- `location` (str): City and state (e.g., "San Francisco, CA")
- `poi_type` (str): OSM POI type (e.g., "amenity")
- `poi_name` (str): OSM POI name (e.g., "library")
- `travel_time` (int): Travel time in minutes (default: 15)
- `census_variables` (List[str]): Census variables to analyze
- `**kwargs`: Additional options

**Returns:** `Result[AnalysisResult, Error]`

##### `create_analysis()`

Create a new analysis configuration builder.

**Returns:** `SocialMapperBuilder`

##### `run_analysis(config, on_progress=None)`

Run analysis with the given configuration.

**Parameters:**
- `config` (Dict[str, Any]): Configuration from builder
- `on_progress` (Optional[Callable[[float], None]]): Progress callback (0-100)

**Returns:** `Result[AnalysisResult, Error]`

### SocialMapperBuilder

Fluent builder for creating analysis configurations.

```python
config = (SocialMapperBuilder()
    .with_location("Durham", "NC")
    .with_osm_pois("amenity", "library")
    .with_travel_time(20)
    .with_census_variables("total_population", "median_income")
    .with_geographic_level("zcta")
    .with_exports(csv=True, isochrones=True)
    .build()
)
```

#### Methods

##### `with_location(area, state=None)`

Set the geographic area to analyze.

**Parameters:**
- `area` (str): City, county, or area name
- `state` (Optional[str]): State name or abbreviation

##### `with_osm_pois(poi_type, poi_name, additional_tags=None)`

Configure OpenStreetMap POI search.

**Parameters:**
- `poi_type` (str): OSM key (e.g., "amenity", "leisure")
- `poi_name` (str): OSM value (e.g., "library", "park")
- `additional_tags` (Optional[Dict]): Additional OSM tags to filter

##### `with_custom_pois(file_path, name_field="name", type_field="type")`

Use custom POI coordinates from a CSV file.

**Parameters:**
- `file_path` (str|Path): Path to CSV file
- `name_field` (str): Column name for POI names
- `type_field` (str): Column name for POI types

##### `with_travel_time(minutes)`

Set the travel time for isochrone generation.

**Parameters:**
- `minutes` (int): Travel time in minutes (1-120)

##### `with_census_variables(*variables)`

Set census variables to analyze.

**Parameters:**
- `*variables` (str): Variable names or codes

##### `with_geographic_level(level)`

Set the geographic unit for analysis.

**Parameters:**
- `level` (str|GeographicLevel): "block-group" or "zcta"

##### `with_exports(csv=True, isochrones=False)`

Configure export options.

**Parameters:**
- `csv` (bool): Export census data to CSV
- `isochrones` (bool): Generate map visualizations

### Result Types

SocialMapper uses Rust-style Result types for explicit error handling.

```python
from socialmapper import Result, Ok, Err

def process_result(result: Result[AnalysisResult, Error]):
    match result:
        case Ok(value):
            print(f"Success: {value}")
        case Err(error):
            print(f"Error: {error}")
```

#### AnalysisResult

```python
@dataclass
class AnalysisResult:
    poi_count: int
    isochrone_count: int
    census_units_analyzed: int
    files_generated: Dict[str, Path]
    metadata: Dict[str, Any]
```

#### Error

```python
@dataclass
class Error:
    type: ErrorType
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    cause: Optional[Exception] = None
```

#### ErrorType

```python
class ErrorType(Enum):
    VALIDATION = auto()
    NETWORK = auto()
    FILE_NOT_FOUND = auto()
    PERMISSION_DENIED = auto()
    RATE_LIMIT = auto()
    CENSUS_API = auto()
    OSM_API = auto()
    GEOCODING = auto()
    PROCESSING = auto()
    UNKNOWN = auto()
```

## Convenience Functions

### `quick_analysis(location, poi_spec, **kwargs)`

Perform a quick analysis with minimal configuration.

```python
from socialmapper import quick_analysis

result = quick_analysis(
    "Portland, OR",
    "amenity:library",
    travel_time=15,
    census_variables=["total_population", "median_income"]
)
```

### `analyze_location(location, **kwargs)`

Analyze all POIs of common types in a location.

```python
from socialmapper import analyze_location

results = analyze_location(
    "San Francisco, CA",
    poi_types=["library", "school", "hospital"],
    travel_time=20
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

## Environment Variables

- `CENSUS_API_KEY`: Your Census Bureau API key
- `SOCIALMAPPER_OUTPUT_DIR`: Default output directory

## Version Information

```python
import socialmapper
print(socialmapper.__version__)
```