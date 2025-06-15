# API Reference

This page provides a complete reference for the SocialMapper Python API. For census variable details, see the [Census Variables Reference](reference/census-variables.md).

## Installation

```bash
pip install socialmapper
```

## Quick Start

```python
from socialmapper import SocialMapperClient

# Simple analysis
with SocialMapperClient() as client:
    result = client.analyze(
        location="Portland, OR",
        poi_type="amenity",
        poi_name="library",
        travel_time=15,
        census_variables=["total_population", "median_income"]
    )
    
    if result.is_ok():
        analysis = result.unwrap()
        print(f"Found {analysis.poi_count} libraries")
        print(f"Census units analyzed: {analysis.census_units_analyzed}")
```

## Core Classes

### SocialMapperClient

The main client for interacting with SocialMapper. Implements a context manager for proper resource handling.

```python
from socialmapper import SocialMapperClient, ClientConfig

# Default configuration
with SocialMapperClient() as client:
    # Use the client
    pass

# Custom configuration
config = ClientConfig(
    api_key="your-census-api-key",
    rate_limit=5,      # requests per second
    timeout=600,       # seconds
    cache_strategy=None  # Optional cache implementation
)

with SocialMapperClient(config) as client:
    # Use the client
    pass
```

#### Methods

##### analyze()

Perform a simple analysis for a location and POI type.

```python
def analyze(
    location: str,
    poi_type: str,
    poi_name: str,
    travel_time: int = 15,
    census_variables: Optional[List[str]] = None,
    travel_mode: str = "drive",
    geographic_level: str = "block-group",
    output_dir: Union[str, Path] = "output",
    **kwargs
) -> Result[AnalysisResult, Error]
```

**Parameters:**
- `location`: Location in "City, State" format (e.g., "Portland, OR")
- `poi_type`: OpenStreetMap key (e.g., "amenity", "leisure", "healthcare")
- `poi_name`: OpenStreetMap value (e.g., "library", "park", "hospital")
- `travel_time`: Travel time in minutes (1-120, default: 15)
- `census_variables`: List of census variables to analyze (default: ["total_population"])
- `travel_mode`: Travel mode - "walk", "bike", or "drive" (default: "drive")
- `geographic_level`: Geographic unit - "block-group" or "zcta" (default: "block-group")
- `output_dir`: Directory for output files (default: "output")

**Returns:** `Result[AnalysisResult, Error]` - Success with analysis results or error

**Example:**
```python
result = client.analyze(
    location="Seattle, WA",
    poi_type="leisure",
    poi_name="park",
    travel_time=10,
    census_variables=["total_population", "median_age", "median_income"]
)
```

##### create_analysis()

Create a builder for complex analysis configurations.

```python
def create_analysis() -> SocialMapperBuilder
```

**Returns:** `SocialMapperBuilder` - Fluent builder for configuration

**Example:**
```python
builder = client.create_analysis()
config = (builder
    .with_location("Chicago", "IL")
    .with_osm_pois("amenity", "school")
    .with_travel_time(20)
    .build()
)
```

##### run_analysis()

Run analysis with a configuration from the builder.

```python
def run_analysis(
    config: Dict[str, Any],
    on_progress: Optional[Callable[[float], None]] = None
) -> Result[AnalysisResult, Error]
```

**Parameters:**
- `config`: Configuration dictionary from builder
- `on_progress`: Optional callback function for progress updates (0-100)

**Returns:** `Result[AnalysisResult, Error]` - Success with results or error

##### analyze_addresses()

Geocode and analyze a list of addresses.

```python
def analyze_addresses(
    addresses: List[str],
    travel_time: int = 15,
    census_variables: Optional[List[str]] = None,
    **kwargs
) -> Result[AnalysisResult, Error]
```

**Parameters:**
- `addresses`: List of address strings to geocode
- `travel_time`: Travel time in minutes
- `census_variables`: Census variables to analyze
- `**kwargs`: Additional options

**Returns:** `Result[AnalysisResult, Error]` - Success with results or error

##### batch()

Create a batch context for running multiple analyses efficiently.

```python
def batch() -> BatchContext
```

**Example:**
```python
with client.batch() as batch:
    batch.add_analysis(config1)
    batch.add_analysis(config2)
    results = batch.run()
```

### SocialMapperBuilder

Fluent builder for creating analysis configurations.

```python
from socialmapper import SocialMapperBuilder, GeographicLevel

config = (SocialMapperBuilder()
    .with_location("Durham", "NC")
    .with_osm_pois("amenity", "library")
    .with_travel_time(20)
    .with_travel_mode("bike")
    .with_census_variables("total_population", "median_income")
    .with_geographic_level(GeographicLevel.ZCTA)
    .enable_isochrone_export()
    .with_output_directory("output/durham")
    .build()
)
```

#### Methods

##### with_location()

Set the geographic area for analysis.

```python
def with_location(area: str, state: Optional[str] = None) -> Self
```

**Parameters:**
- `area`: City, county, or area name
- `state`: Optional state name or abbreviation

**Examples:**
```python
.with_location("San Francisco", "CA")
.with_location("San Francisco, CA")
.with_location("Cook County", "IL")
```

##### with_osm_pois()

Configure OpenStreetMap POI search.

```python
def with_osm_pois(
    poi_type: str,
    poi_name: str,
    additional_tags: Optional[Dict[str, str]] = None
) -> Self
```

**Parameters:**
- `poi_type`: OSM key (e.g., "amenity", "leisure", "healthcare")
- `poi_name`: OSM value (e.g., "library", "park", "hospital")
- `additional_tags`: Optional additional OSM tags for filtering

**Example:**
```python
.with_osm_pois("amenity", "school", {"school:type": "elementary"})
```

##### with_custom_pois()

Use custom POI coordinates from a file.

```python
def with_custom_pois(
    file_path: Union[str, Path],
    name_field: Optional[str] = None,
    type_field: Optional[str] = None
) -> Self
```

**Parameters:**
- `file_path`: Path to CSV or JSON file with POI data
- `name_field`: Column name for POI names (auto-detected if not specified)
- `type_field`: Column name for POI types (auto-detected if not specified)

**Required columns:** `latitude`, `longitude`

##### with_travel_time()

Set the travel time for isochrone generation.

```python
def with_travel_time(minutes: int) -> Self
```

**Parameters:**
- `minutes`: Travel time in minutes (1-120)

##### with_travel_mode()

Set the travel mode for routing.

```python
def with_travel_mode(mode: Union[str, TravelMode]) -> Self
```

**Parameters:**
- `mode`: "walk", "bike", "drive", or TravelMode enum value

##### with_census_variables()

Set census variables to analyze.

```python
def with_census_variables(*variables: str) -> Self
```

**Parameters:**
- `*variables`: Variable names or census codes

**Example:**
```python
.with_census_variables("total_population", "median_income", "B01002_001E")
```

##### with_geographic_level()

Set the geographic unit for analysis.

```python
def with_geographic_level(level: Union[str, GeographicLevel]) -> Self
```

**Parameters:**
- `level`: "block-group", "zcta", or GeographicLevel enum value

##### enable_isochrone_export()

Enable saving of isochrone geometries.

```python
def enable_isochrone_export() -> Self
```

##### disable_csv_export()

Disable CSV export (enabled by default).

```python
def disable_csv_export() -> Self
```

##### with_output_directory()

Set the output directory for results.

```python
def with_output_directory(path: Union[str, Path]) -> Self
```

##### limit_pois()

Limit the number of POIs to analyze.

```python
def limit_pois(max_count: int) -> Self
```

##### build()

Build and validate the configuration.

```python
def build() -> Dict[str, Any]
```

**Returns:** Configuration dictionary for use with `run_analysis()`

**Raises:** `ValueError` if configuration is invalid

## Result Types

SocialMapper uses the Result pattern for explicit error handling without exceptions.

### Result[T, E]

A generic result type that can contain either a success value (Ok) or an error (Err).

```python
from socialmapper import Result, Ok, Err

# Pattern matching (Python 3.10+)
match result:
    case Ok(value):
        print(f"Success: {value}")
    case Err(error):
        print(f"Error: {error}")

# Traditional approach
if result.is_ok():
    value = result.unwrap()
else:
    error = result.unwrap_err()
```

#### Methods

- `is_ok() -> bool`: Check if result is successful
- `is_err() -> bool`: Check if result is an error
- `unwrap() -> T`: Get success value (raises if error)
- `unwrap_err() -> E`: Get error value (raises if success)
- `unwrap_or(default: T) -> T`: Get value or default
- `map(func: Callable[[T], U]) -> Result[U, E]`: Transform success value
- `map_err(func: Callable[[E], F]) -> Result[T, F]`: Transform error value

### AnalysisResult

Results from a successful analysis.

```python
@dataclass
class AnalysisResult:
    poi_count: int                    # Number of POIs found
    isochrone_count: int             # Number of isochrones generated
    census_units_analyzed: int       # Number of census units analyzed
    files_generated: Dict[str, Path] # Paths to generated files
    metadata: Dict[str, Any]         # Additional metadata
    
    def is_complete(self) -> bool:
        """Check if analysis completed successfully."""
        return self.poi_count > 0 and self.isochrone_count > 0
```

### Error

Structured error information.

```python
@dataclass
class Error:
    type: ErrorType              # Error category
    message: str                 # Human-readable message
    context: Dict[str, Any]      # Additional context
    cause: Optional[Exception]   # Original exception if any
    traceback: Optional[str]     # Stack trace
```

### ErrorType

Error categories for better error handling.

```python
class ErrorType(Enum):
    VALIDATION = auto()         # Invalid input parameters
    NETWORK = auto()           # Network connectivity issues
    FILE_NOT_FOUND = auto()    # File or path not found
    PERMISSION_DENIED = auto() # Insufficient permissions
    RATE_LIMIT = auto()        # API rate limit exceeded
    CENSUS_API = auto()        # Census API errors
    OSM_API = auto()           # OpenStreetMap API errors
    GEOCODING = auto()         # Address geocoding failures
    PROCESSING = auto()        # General processing errors
    UNKNOWN = auto()           # Unclassified errors
```

## Configuration Classes

### ClientConfig

Configuration for the SocialMapper client.

```python
@dataclass
class ClientConfig:
    api_key: Optional[str] = None       # Census API key
    rate_limit: float = 1.0             # Requests per second
    timeout: int = 600                  # Request timeout in seconds
    cache_strategy: Optional[CacheStrategy] = None  # Cache implementation
    max_retries: int = 3                # Maximum retry attempts
    log_level: str = "INFO"             # Logging level
```

### GeographicLevel

Geographic units for census data.

```python
class GeographicLevel(Enum):
    BLOCK_GROUP = "block-group"  # Census block groups (~600-3000 people)
    ZCTA = "zcta"               # ZIP Code Tabulation Areas
```

### TravelMode

Available travel modes for routing.

```python
class TravelMode(Enum):
    WALK = "walk"   # Walking (5 km/h)
    BIKE = "bike"   # Cycling (15 km/h)
    DRIVE = "drive" # Driving (uses road network)
```

## Convenience Functions

High-level functions for common use cases.

### quick_analysis()

Perform a quick analysis with minimal configuration.

```python
def quick_analysis(
    location: str,
    poi_search: str,
    travel_time: int = 15,
    census_variables: Optional[List[str]] = None,
    output_dir: Union[str, Path] = "output"
) -> Result[AnalysisResult, Error]
```

**Parameters:**
- `location`: Location in "City, State" format
- `poi_search`: POI search in "type:name" format (e.g., "amenity:library")
- `travel_time`: Travel time in minutes
- `census_variables`: Census variables to analyze
- `output_dir`: Output directory

**Example:**
```python
from socialmapper import quick_analysis

result = quick_analysis(
    "Portland, OR",
    "amenity:school",
    travel_time=10,
    census_variables=["total_population", "median_income"]
)
```

### analyze_location()

Analyze a specific location with custom POIs.

```python
def analyze_location(
    city: str,
    state: str,
    poi_type: str = "amenity",
    poi_name: str = "library",
    **options
) -> Result[AnalysisResult, Error]
```

**Parameters:**
- `city`: City name
- `state`: State name or abbreviation
- `poi_type`: OpenStreetMap POI type
- `poi_name`: OpenStreetMap POI name
- `**options`: Additional options (travel_time, census_variables, etc.)

### analyze_custom_pois()

Analyze custom POIs from a file.

```python
def analyze_custom_pois(
    poi_file: Union[str, Path],
    travel_time: int = 15,
    census_variables: Optional[List[str]] = None,
    name_field: Optional[str] = None,
    type_field: Optional[str] = None,
    **options
) -> Result[AnalysisResult, Error]
```

**Parameters:**
- `poi_file`: Path to CSV or JSON file with POI coordinates
- `travel_time`: Travel time in minutes
- `census_variables`: Census variables to analyze
- `name_field`: Field name for POI names
- `type_field`: Field name for POI types
- `**options`: Additional options

### analyze_dataframe()

Analyze POIs from a pandas DataFrame.

```python
def analyze_dataframe(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    name_col: Optional[str] = "name",
    type_col: Optional[str] = "type",
    **options
) -> Result[AnalysisResult, Error]
```

**Parameters:**
- `df`: DataFrame with POI data
- `lat_col`: Column name for latitude
- `lon_col`: Column name for longitude
- `name_col`: Column name for POI names
- `type_col`: Column name for POI types
- `**options`: Additional analysis options

## Async Support

SocialMapper provides async support for concurrent operations.

### AsyncSocialMapper

Asynchronous client for streaming and concurrent operations.

```python
from socialmapper import AsyncSocialMapper
import asyncio

async def main():
    async with AsyncSocialMapper(config) as mapper:
        # Stream POIs as they're found
        async for poi in mapper.stream_pois():
            print(f"Found: {poi.name}")
        
        # Generate isochrones with progress
        async for progress in mapper.generate_isochrones_with_progress():
            print(f"Progress: {progress.completed}/{progress.total}")

asyncio.run(main())
```

## Error Handling

### Basic Error Handling

```python
result = client.analyze("Portland, OR", "amenity", "library")

if result.is_ok():
    analysis = result.unwrap()
    print(f"Success! Found {analysis.poi_count} POIs")
else:
    error = result.unwrap_err()
    print(f"Error: {error.message}")
    
    # Check error type
    if error.type == ErrorType.CENSUS_API:
        print("Census API error - check your API key")
```

### Pattern Matching (Python 3.10+)

```python
match result:
    case Ok(analysis):
        print(f"Found {analysis.poi_count} POIs")
    case Err(Error(type=ErrorType.RATE_LIMIT)):
        print("Rate limited - try again later")
    case Err(error):
        print(f"Other error: {error}")
```

### Collecting Multiple Results

```python
from socialmapper import collect_results

results = [
    client.analyze("Portland, OR", "amenity", "library"),
    client.analyze("Seattle, WA", "amenity", "school"),
    client.analyze("Eugene, OR", "leisure", "park")
]

match collect_results(results):
    case Ok(analyses):
        for analysis in analyses:
            print(f"Analysis complete: {analysis.poi_count} POIs")
    case Err(errors):
        for error in errors:
            print(f"Error: {error}")
```

## Environment Variables

SocialMapper uses the following environment variables:

- `CENSUS_API_KEY`: Your Census Bureau API key (required for census data)
- `SOCIALMAPPER_OUTPUT_DIR`: Default output directory (default: "output")
- `SOCIALMAPPER_LOG_LEVEL`: Logging level (default: "INFO")
- `SOCIALMAPPER_CACHE_DIR`: Cache directory (default: "cache")

You can set these in a `.env` file:

```bash
CENSUS_API_KEY=your-api-key-here
SOCIALMAPPER_OUTPUT_DIR=/path/to/output
SOCIALMAPPER_LOG_LEVEL=DEBUG
```

## Caching

SocialMapper supports pluggable caching strategies.

### Implementing a Cache Strategy

```python
from socialmapper import CacheStrategy
from typing import Any, Optional

class RedisCache(CacheStrategy):
    def get(self, key: str) -> Optional[Any]:
        # Implement Redis get
        pass
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        # Implement Redis set with TTL
        pass

# Use with client
config = ClientConfig(cache_strategy=RedisCache())
```

## Rate Limiting

The client includes built-in rate limiting to respect API limits.

```python
# Configure rate limit
config = ClientConfig(
    rate_limit=5.0  # 5 requests per second
)

# Rate limits are applied automatically
with SocialMapperClient(config) as client:
    # All API calls are rate limited
    result = client.analyze(...)
```

## Logging

SocialMapper uses Python's standard logging module.

```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Or set via environment variable
# SOCIALMAPPER_LOG_LEVEL=DEBUG
```

## Examples

### Complete Analysis Pipeline

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

# Configure the analysis
config = (SocialMapperBuilder()
    .with_location("Austin", "TX")
    .with_osm_pois("amenity", "school")
    .with_travel_time(15)
    .with_travel_mode("walk")
    .with_census_variables(
        "total_population",
        "median_age",
        "median_income",
        "percent_poverty"
    )
    .with_geographic_level("block-group")
    .enable_isochrone_export()
    .with_output_directory("output/austin-schools")
    .build()
)

# Run the analysis
with SocialMapperClient() as client:
    result = client.run_analysis(
        config,
        on_progress=lambda p: print(f"Progress: {p:.1f}%")
    )
    
    match result:
        case Ok(analysis):
            print(f"Analysis complete!")
            print(f"Found {analysis.poi_count} schools")
            print(f"Analyzed {analysis.census_units_analyzed} census units")
            print(f"Files saved to: {analysis.files_generated}")
        case Err(error):
            print(f"Analysis failed: {error}")
```

### Batch Processing

```python
from socialmapper import SocialMapperClient

locations = [
    ("Portland", "OR"),
    ("Seattle", "WA"),
    ("San Francisco", "CA")
]

with SocialMapperClient() as client:
    with client.batch() as batch:
        for city, state in locations:
            config = (client.create_analysis()
                .with_location(city, state)
                .with_osm_pois("amenity", "hospital")
                .with_travel_time(20)
                .build()
            )
            batch.add_analysis(config)
        
        results = batch.run()
        
        for (city, state), result in zip(locations, results):
            match result:
                case Ok(analysis):
                    print(f"{city}: {analysis.poi_count} hospitals")
                case Err(error):
                    print(f"{city}: Failed - {error}")
```

### Custom POI Analysis

```python
from socialmapper import analyze_custom_pois

# Analyze custom locations from CSV
result = analyze_custom_pois(
    "my_locations.csv",
    travel_time=15,
    census_variables=["total_population", "median_age"],
    name_field="location_name",
    type_field="location_type"
)

if result.is_ok():
    analysis = result.unwrap()
    print(f"Analyzed {analysis.poi_count} custom locations")
```

## Version Information

```python
import socialmapper

# Get version
print(socialmapper.__version__)

# Check API version
from socialmapper.api import __version__ as api_version
print(f"API version: {api_version}")
```

## Migration from Legacy API

If you're using the old `run_socialmapper` function, migrate to the new client-based API:

```python
# Old API (deprecated)
from socialmapper import run_socialmapper
results = run_socialmapper(state="CA", county="Los Angeles", ...)

# New API (recommended)
from socialmapper import SocialMapperClient
with SocialMapperClient() as client:
    result = client.analyze("Los Angeles, CA", "amenity", "library")
    if result.is_ok():
        analysis = result.unwrap()
        # Use analysis results
```

## See Also

- [Census Variables Reference](reference/census-variables.md) - Complete list of available census variables
- [User Guide](user-guide/index.md) - Detailed usage instructions
- [Examples](https://github.com/mihiarc/socialmapper/tree/main/examples) - Code examples and tutorials