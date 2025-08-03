# 📚 POI Discovery API Reference

This document provides complete API reference for SocialMapper's POI discovery functionality, including all classes, methods, parameters, and return types.

## Table of Contents

- [Client API](#client-api)
- [Builder API](#builder-api)
- [Pipeline Functions](#pipeline-functions)
- [Data Structures](#data-structures)
- [Configuration Classes](#configuration-classes)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## Client API

### SocialMapperClient.discover_nearby_pois()

The primary entry point for POI discovery through the client interface.

```python
def discover_nearby_pois(
    self,
    location: str | tuple[float, float],
    travel_time: int = 15,
    travel_mode: str = "drive",
    poi_categories: list[str] | None = None,
    exclude_categories: list[str] | None = None,
    max_pois_per_category: int | None = None,
    export_csv: bool = True,
    export_geojson: bool = True,
    create_map: bool = True,
    output_dir: str | None = None,
    **kwargs,
) -> Result[NearbyPOIResult, Error]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `location` | `str \| tuple[float, float]` | *Required* | Address string (e.g., "San Francisco, CA") or coordinate tuple (lat, lon) |
| `travel_time` | `int` | `15` | Travel time in minutes (1-120) |
| `travel_mode` | `str` | `"drive"` | Travel mode: "drive", "walk", or "bike" |
| `poi_categories` | `list[str] \| None` | `None` | POI categories to include (default: all) |
| `exclude_categories` | `list[str] \| None` | `None` | POI categories to exclude |
| `max_pois_per_category` | `int \| None` | `None` | Maximum POIs per category (no limit if None) |
| `export_csv` | `bool` | `True` | Export results to CSV format |
| `export_geojson` | `bool` | `True` | Export results to GeoJSON format |
| `create_map` | `bool` | `True` | Create interactive HTML map |
| `output_dir` | `str \| None` | `None` | Output directory (default: "output") |

**Returns:**
- `Result[NearbyPOIResult, Error]` - Success result with POI data or error information

**Example:**
```python
with SocialMapperClient() as client:
    result = client.discover_nearby_pois(
        location="Chapel Hill, NC",
        travel_time=20,
        travel_mode="walk",
        poi_categories=["food_and_drink", "healthcare"],
        max_pois_per_category=50
    )
    
    match result:
        case Ok(poi_result):
            print(f"Found {poi_result.total_poi_count} POIs")
            for category, count in poi_result.category_counts.items():
                print(f"  {category}: {count}")
        case Err(error):
            print(f"Error: {error}")
```

---

## Builder API

### SocialMapperBuilder.with_nearby_poi_discovery()

Configure POI discovery using the builder pattern for more complex scenarios.

```python
def with_nearby_poi_discovery(
    self,
    location: str | tuple[float, float],
    travel_time: int,
    travel_mode: str | TravelMode = TravelMode.DRIVE,
    poi_categories: list[str] | None = None,
) -> Self
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `location` | `str \| tuple[float, float]` | *Required* | Origin location for POI discovery |
| `travel_time` | `int` | *Required* | Travel time in minutes (1-120) |
| `travel_mode` | `str \| TravelMode` | `TravelMode.DRIVE` | Travel mode enum or string |
| `poi_categories` | `list[str] \| None` | `None` | POI categories to include |

**Returns:**
- `Self` - Builder instance for method chaining

### Additional Builder Methods

#### with_poi_categories()
```python
def with_poi_categories(self, *categories: str) -> Self
```
Set POI categories to include in discovery.

**Parameters:**
- `*categories` - Variable number of category names

#### exclude_poi_categories()
```python
def exclude_poi_categories(self, *categories: str) -> Self
```
Set POI categories to exclude from discovery.

**Parameters:**
- `*categories` - Variable number of category names to exclude

#### limit_pois_per_category()
```python
def limit_pois_per_category(self, limit: int) -> Self
```
Set maximum number of POIs per category.

**Parameters:**
- `limit` - Maximum POIs per category (must be positive)

**Example:**
```python
builder = (
    SocialMapperBuilder()
    .with_nearby_poi_discovery("Boston, MA", 25, "bike")
    .with_poi_categories("food_and_drink", "education", "healthcare")
    .exclude_poi_categories("utilities")
    .limit_pois_per_category(30)
    .with_export_options(csv=True, geojson=True, maps=True)
)

result = builder.execute()
```

---

## Pipeline Functions

### execute_poi_discovery_pipeline()

Direct pipeline execution function for advanced use cases.

```python
def execute_poi_discovery_pipeline(
    config: NearbyPOIDiscoveryConfig,
) -> Result[NearbyPOIResult, Error]
```

**Parameters:**
- `config` - `NearbyPOIDiscoveryConfig` object with full configuration

**Returns:**
- `Result[NearbyPOIResult, Error]` - Pipeline execution result

### Convenience Functions

#### discover_pois_near_address()
```python
def discover_pois_near_address(
    address: str,
    travel_time: int = 15,
    travel_mode: TravelMode = TravelMode.DRIVE,
    categories: Optional[list[str]] = None,
    output_dir: Optional[Path] = None,
) -> Result[NearbyPOIResult, Error]
```

#### discover_pois_near_coordinates()
```python
def discover_pois_near_coordinates(
    latitude: float,
    longitude: float,
    travel_time: int = 15,
    travel_mode: TravelMode = TravelMode.DRIVE,
    categories: Optional[list[str]] = None,
    output_dir: Optional[Path] = None,
) -> Result[NearbyPOIResult, Error]
```

---

## Data Structures

### DiscoveredPOI

Immutable representation of a discovered Point of Interest.

```python
@dataclass(frozen=True)
class DiscoveredPOI:
    # Core identification
    id: str                           # Unique POI identifier
    name: str                         # POI name
    category: str                     # Primary category
    subcategory: str                  # Specific subcategory
    
    # Location data
    latitude: float                   # Decimal latitude
    longitude: float                  # Decimal longitude
    
    # Distance information
    straight_line_distance_m: float   # Distance from origin in meters
    
    # OpenStreetMap metadata
    osm_type: str                     # "node", "way", or "relation"
    osm_id: int                       # OSM element ID
    
    # Optional enhanced data
    address: str | None = None        # Formatted address
    estimated_travel_time_min: float | None = None  # Estimated travel time
    tags: dict[str, str] = field(default_factory=dict)  # Raw OSM tags
    phone: str | None = None          # Contact phone
    website: str | None = None        # Website URL
    opening_hours: str | None = None  # Opening hours string
```

**Properties:**
- All fields are validated on creation
- Immutable after creation (frozen dataclass)
- Coordinates must be valid lat/lon values
- Distance cannot be negative

### NearbyPOIResult

Complete result set from POI discovery analysis.

```python
@dataclass
class NearbyPOIResult:
    # Origin information
    origin_location: dict[str, float]              # {"lat": x, "lon": y}
    travel_time: int                               # Travel time constraint
    travel_mode: TravelMode                        # Travel mode used
    isochrone_area_km2: float                      # Isochrone area
    
    # POI organization
    pois_by_category: dict[str, list[DiscoveredPOI]]  # POIs grouped by category
    total_poi_count: int = 0                          # Total POI count
    category_counts: dict[str, int] = field(default_factory=dict)  # Count per category
    
    # Geographic data
    isochrone_geometry: Any | None = None          # GeoDataFrame with isochrone
    poi_points: Any | None = None                  # GeoDataFrame with POI points
    
    # Export information
    files_generated: dict[str, Path] = field(default_factory=dict)  # Generated files
    
    # Metadata and warnings
    metadata: dict[str, Any] = field(default_factory=dict)      # Analysis metadata
    warnings: list[str] = field(default_factory=list)          # Warning messages
```

**Key Methods:**

#### get_all_pois()
```python
def get_all_pois(self) -> list[DiscoveredPOI]
```
Returns a flat list of all discovered POIs across all categories.

#### get_pois_by_distance()
```python
def get_pois_by_distance(self, max_distance_m: float | None = None) -> list[DiscoveredPOI]
```
Returns POIs sorted by distance, optionally filtered by maximum distance.

#### get_summary_stats()
```python
def get_summary_stats(self) -> dict[str, Any]
```
Returns summary statistics including total POIs, categories, and distance metrics.

**Properties:**

#### success
```python
@property
def success(self) -> bool
```
Returns `True` if any POIs were discovered.

---

## Configuration Classes

### NearbyPOIDiscoveryConfig

Complete configuration for POI discovery operations.

```python
@dataclass
class NearbyPOIDiscoveryConfig:
    # Location specification
    location: str | tuple[float, float]           # Origin location
    
    # Travel constraints
    travel_time: int                              # Travel time in minutes
    travel_mode: TravelMode = TravelMode.DRIVE    # Travel mode
    
    # POI filtering
    poi_categories: list[str] | None = None       # Categories to include
    exclude_categories: list[str] | None = None   # Categories to exclude
    
    # Output options
    export_csv: bool = True                       # Export CSV file
    export_geojson: bool = True                   # Export GeoJSON files
    create_map: bool = True                       # Create interactive map
    output_dir: Path = field(default_factory=lambda: Path("output"))  # Output directory
    
    # Processing options
    max_pois_per_category: int | None = None      # Limit POIs per category
    include_poi_details: bool = True              # Include enhanced POI data
```

**Validation:**
- Automatically validates all parameters on creation
- Ensures travel time is within valid range (1-120 minutes)
- Validates coordinates if provided as tuple
- Ensures output directory is valid

---

## Error Handling

### Error Types

POI discovery uses structured error handling with specific error types:

```python
class ErrorType(Enum):
    POI_DISCOVERY = auto()        # General POI discovery errors
    LOCATION_GEOCODING = auto()   # Location geocoding failures
    ISOCHRONE_GENERATION = auto() # Isochrone creation errors
    POI_QUERY = auto()           # POI querying errors
    PROCESSING = auto()          # Data processing errors
    CONFIGURATION = auto()       # Invalid configuration
    NETWORK = auto()             # Network/API errors
```

### Error Structure

```python
@dataclass
class Error:
    type: ErrorType                    # Error category
    message: str                       # Human-readable message
    context: dict[str, Any] | None     # Additional context
    cause: Exception | None            # Original exception
    traceback: str | None              # Stack trace
```

### Common Error Scenarios

#### Location Geocoding Errors
```python
# Invalid address
Error(
    type=ErrorType.LOCATION_GEOCODING,
    message="Failed to geocode address: Invalid Street Name",
    context={"address": "Invalid Street Name"}
)
```

#### POI Query Errors
```python
# No POIs found
Error(
    type=ErrorType.POI_QUERY,
    message="No POIs found within the travel time isochrone",
    context={
        "isochrone_area_km2": 5.2,
        "categories_searched": ["food_and_drink"]
    }
)
```

#### Configuration Errors
```python
# Invalid travel time
Error(
    type=ErrorType.CONFIGURATION,
    message="Travel time must be between 1 and 120 minutes",
    context={"provided_time": 150}
)
```

---

## POI Categories

### Available Categories

The system supports 10 primary POI categories:

| Category | Count | Description |
|----------|--------|-------------|
| `food_and_drink` | 47 types | Restaurants, cafes, bars, food shops |
| `shopping` | 89 types | Retail stores, malls, markets |
| `healthcare` | 26 types | Hospitals, clinics, pharmacies |
| `education` | 16 types | Schools, libraries, universities |
| `transportation` | 21 types | Transit, parking, fuel stations |
| `recreation` | 41 types | Parks, sports, entertainment |
| `services` | 40 types | Banks, government, professional services |
| `accommodation` | 12 types | Hotels, hostels, camping |
| `religious` | 14 types | Churches, temples, worship places |
| `utilities` | 16 types | Public facilities, utilities |

### Category Functions

```python
from socialmapper.poi_categorization import (
    get_poi_category_info,
    is_valid_category,
    get_category_values
)

# Get all category information
info = get_poi_category_info()
print(f"Available categories: {info['categories']}")

# Validate a category
if is_valid_category("food_and_drink"):
    values = get_category_values("food_and_drink")
    print(f"Food & drink includes: {values[:5]}")  # First 5 values
```

---

## Examples

### Basic Usage

```python
from socialmapper import SocialMapperClient
from socialmapper.api.result_types import Ok, Err

with SocialMapperClient() as client:
    result = client.discover_nearby_pois(
        location="Portland, OR",
        travel_time=15,
        travel_mode="bike"
    )
    
    match result:
        case Ok(poi_result):
            print(f"✅ Found {poi_result.total_poi_count} POIs")
            
            # Show results by category
            for category, pois in poi_result.pois_by_category.items():
                print(f"\n{category.title()} ({len(pois)} POIs):")
                for poi in pois[:3]:  # Show first 3
                    distance_km = poi.straight_line_distance_m / 1000
                    print(f"  • {poi.name} ({distance_km:.1f}km)")
                    
        case Err(error):
            print(f"❌ Error: {error.message}")
            if error.context:
                print(f"   Context: {error.context}")
```

### Advanced Configuration

```python
from socialmapper.api.builder import SocialMapperBuilder
from socialmapper.isochrone import TravelMode
from pathlib import Path

# Complex configuration using builder
result = (
    SocialMapperBuilder()
    .with_nearby_poi_discovery(
        location=(45.5152, -122.6784),  # Portland coordinates
        travel_time=30,
        travel_mode=TravelMode.WALK
    )
    .with_poi_categories("healthcare", "education", "services")
    .exclude_poi_categories("utilities")
    .limit_pois_per_category(25)
    .with_export_options(
        csv=True,
        geojson=True,
        maps=True,
        output_dir=Path("results/portland_analysis")
    )
    .execute()
)

if result.is_ok():
    poi_result = result.unwrap()
    
    # Access detailed statistics
    stats = poi_result.get_summary_stats()
    print(f"Analysis covered {stats['isochrone_area_km2']:.1f} km²")
    print(f"Average POI distance: {stats['avg_distance_m']:.0f}m")
    
    # Find nearest POIs
    nearest_pois = poi_result.get_pois_by_distance(max_distance_m=500)
    print(f"\nNearest POIs (within 500m): {len(nearest_pois)}")
```

### Pipeline Direct Usage

```python
from socialmapper.api.result_types import NearbyPOIDiscoveryConfig
from socialmapper.pipeline.poi_discovery import execute_poi_discovery_pipeline
from socialmapper.isochrone import TravelMode
from pathlib import Path

# Direct pipeline configuration
config = NearbyPOIDiscoveryConfig(
    location="Austin, TX",
    travel_time=20,
    travel_mode=TravelMode.BIKE,
    poi_categories=["food_and_drink", "recreation"],
    export_csv=True,
    export_geojson=True,
    create_map=True,
    output_dir=Path("output/austin_bike_pois"),
    max_pois_per_category=50,
    include_poi_details=True
)

result = execute_poi_discovery_pipeline(config)

match result:
    case Ok(poi_result):
        # Access generated files
        for file_type, path in poi_result.files_generated.items():
            print(f"{file_type}: {path}")
            
        # Check for warnings
        if poi_result.warnings:
            print(f"\nWarnings: {poi_result.warnings}")
            
    case Err(error):
        print(f"Pipeline failed: {error}")
```

### Error Handling Patterns

```python
from socialmapper.api.result_types import ErrorType

result = client.discover_nearby_pois(
    location="Nonexistent City, XX",
    travel_time=15
)

match result:
    case Ok(poi_result):
        # Success handling
        process_results(poi_result)
        
    case Err(error):
        # Specific error handling
        match error.type:
            case ErrorType.LOCATION_GEOCODING:
                print("Could not find the specified location")
                if error.context:
                    print(f"Tried to geocode: {error.context.get('address')}")
                    
            case ErrorType.POI_QUERY:
                print("No POIs found in the area")
                area = error.context.get('isochrone_area_km2', 0)
                print(f"Searched area: {area:.1f} km²")
                
            case ErrorType.NETWORK:
                print("Network error - check your connection")
                
            case _:
                print(f"Unexpected error: {error.message}")
```

This API reference provides complete documentation for all POI discovery functionality in SocialMapper. For practical examples and tutorials, see the [POI Discovery Usage Guide](../guides/poi_discovery_guide.md).