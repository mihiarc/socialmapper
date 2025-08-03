# Design Document

## Overview

The Nearby POI Discovery feature extends SocialMapper's capabilities by providing a reverse lookup approach to accessibility analysis. Instead of analyzing accessibility to specific POI types, users can discover all available POIs within their travel constraints from a given location. This feature integrates seamlessly with the existing SocialMapper architecture, leveraging the established isochrone generation, POI querying, and result handling infrastructure.

The feature follows SocialMapper's modern API patterns using the builder pattern for configuration, Ok/Err result types for error handling, and the existing pipeline architecture for processing. The implementation will be accessible through both the programmatic API and the Streamlit web interface.

## Architecture

### High-Level Flow

1. **Input Processing**: Accept user location (address/coordinates), travel time, and travel mode
2. **Geocoding**: Convert address to coordinates using existing geocoding infrastructure
3. **Isochrone Generation**: Create travel time polygon using existing isochrone system
4. **POI Discovery**: Query OpenStreetMap for all POIs within the isochrone boundary
5. **Result Processing**: Organize and categorize discovered POIs
6. **Output Generation**: Return structured results with export options

### Integration Points

The feature integrates with existing SocialMapper components:

- **API Layer**: Extends `SocialMapperBuilder` and `SocialMapperClient` with new methods
- **Pipeline System**: Adds new pipeline stage for POI discovery
- **Geocoding**: Uses existing address-to-coordinate conversion
- **Isochrone Generation**: Leverages existing travel time analysis
- **POI Querying**: Extends existing Overpass API integration
- **Export System**: Uses existing CSV/GeoJSON export infrastructure

## Components and Interfaces

### 1. API Extensions

#### SocialMapperBuilder Extensions
```python
class SocialMapperBuilder:
    def with_nearby_poi_discovery(
        self, 
        location: str | tuple[float, float],
        travel_time: int,
        travel_mode: TravelMode = TravelMode.DRIVE,
        poi_categories: list[str] | None = None
    ) -> Self:
        """Configure nearby POI discovery analysis."""
        
    def with_poi_categories(self, *categories: str) -> Self:
        """Filter POI discovery to specific categories."""
```

#### SocialMapperClient Extensions
```python
class SocialMapperClient:
    def discover_nearby_pois(
        self,
        location: str | tuple[float, float],
        travel_time: int = 15,
        travel_mode: TravelMode = TravelMode.DRIVE,
        poi_categories: list[str] | None = None,
        **kwargs
    ) -> Result[NearbyPOIResult, Error]:
        """Discover POIs within travel time from location."""
```

### 2. New Result Types

#### NearbyPOIResult
```python
@dataclass
class NearbyPOIResult:
    """Result from nearby POI discovery analysis."""
    
    origin_location: dict[str, float]  # lat, lon of origin
    travel_time: int
    travel_mode: TravelMode
    isochrone_area_km2: float
    
    # POI data organized by category
    pois_by_category: dict[str, list[dict]]
    total_poi_count: int
    category_counts: dict[str, int]
    
    # Geographic data
    isochrone_geometry: Any  # GeoDataFrame with isochrone polygon
    poi_points: Any  # GeoDataFrame with POI locations
    
    # Export paths
    files_generated: dict[str, Path]
    
    # Metadata
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
```

### 3. Pipeline Integration

#### New Pipeline Stage: NearbyPOIDiscoveryStage
```python
class NearbyPOIDiscoveryStage:
    """Pipeline stage for discovering nearby POIs."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.geocoder = get_geocoding_engine()
        
    def execute(self) -> dict[str, Any]:
        """Execute nearby POI discovery pipeline."""
        # 1. Geocode origin location
        # 2. Generate isochrone from origin
        # 3. Query all POIs within isochrone
        # 4. Categorize and organize results
        # 5. Generate exports
```

### 4. POI Query Extensions

#### Enhanced Overpass Query Builder
```python
def build_poi_discovery_query(
    isochrone_geometry: Polygon,
    poi_categories: list[str] | None = None
) -> str:
    """Build Overpass query to find all POIs within isochrone."""
    
def query_pois_in_polygon(
    polygon: Polygon,
    categories: list[str] | None = None
) -> dict[str, Any]:
    """Query all POIs within a polygon boundary."""
```

### 5. POI Categorization System

#### POI Category Mapping
```python
POI_CATEGORY_MAPPING = {
    "food_and_drink": ["restaurant", "cafe", "bar", "fast_food", "pub"],
    "shopping": ["shop", "mall", "supermarket", "convenience"],
    "education": ["school", "university", "library", "kindergarten"],
    "healthcare": ["hospital", "clinic", "pharmacy", "dentist"],
    "transportation": ["bus_station", "subway_station", "parking"],
    "recreation": ["park", "playground", "sports_centre", "cinema"],
    "services": ["bank", "post_office", "government", "police"],
    "accommodation": ["hotel", "hostel", "guest_house"],
}

def categorize_poi(poi_tags: dict) -> str:
    """Categorize a POI based on its OSM tags."""
    
def organize_pois_by_category(pois: list[dict]) -> dict[str, list[dict]]:
    """Organize POI list by categories."""
```

## Data Models

### Input Models

#### NearbyPOIDiscoveryConfig
```python
@dataclass
class NearbyPOIDiscoveryConfig:
    """Configuration for nearby POI discovery."""
    
    # Location (either address string or coordinates)
    location: str | tuple[float, float]
    
    # Travel constraints
    travel_time: int  # minutes
    travel_mode: TravelMode
    
    # POI filtering
    poi_categories: list[str] | None = None
    exclude_categories: list[str] | None = None
    
    # Output options
    export_csv: bool = True
    export_geojson: bool = True
    create_map: bool = True
    output_dir: Path = Path("output")
    
    # Processing options
    max_pois_per_category: int | None = None
    include_poi_details: bool = True
```

### Output Models

#### POI Data Structure
```python
@dataclass
class DiscoveredPOI:
    """Individual POI discovered in analysis."""
    
    id: str
    name: str
    category: str
    subcategory: str
    
    # Location
    latitude: float
    longitude: float
    address: str | None = None
    
    # Distance/travel info
    straight_line_distance_m: float
    estimated_travel_time_min: float | None = None
    
    # OSM data
    osm_type: str  # node, way, relation
    osm_id: int
    tags: dict[str, str]
    
    # Additional details
    phone: str | None = None
    website: str | None = None
    opening_hours: str | None = None
```

## Error Handling

### New Error Types

```python
class POIDiscoveryError(SocialMapperError):
    """Base error for POI discovery operations."""
    
class IsochroneGenerationError(POIDiscoveryError):
    """Error generating isochrone for POI discovery."""
    
class POIQueryError(POIDiscoveryError):
    """Error querying POIs within isochrone."""
    
class LocationGeocodingError(POIDiscoveryError):
    """Error geocoding the origin location."""
```

### Error Handling Strategy

1. **Graceful Degradation**: If specific POI categories fail, continue with others
2. **Detailed Error Context**: Provide specific information about what failed
3. **Recovery Suggestions**: Offer actionable suggestions for common failures
4. **Partial Results**: Return partial results when possible with warnings

## Testing Strategy

### Unit Tests

1. **Configuration Validation**: Test builder pattern and input validation
2. **POI Categorization**: Test POI classification logic
3. **Query Building**: Test Overpass query generation for polygon searches
4. **Result Processing**: Test POI organization and result structure
5. **Error Handling**: Test error scenarios and recovery

### Integration Tests

1. **End-to-End Discovery**: Test complete POI discovery workflow
2. **Geocoding Integration**: Test address-to-coordinate conversion
3. **Isochrone Integration**: Test isochrone generation for discovery
4. **Export Integration**: Test CSV/GeoJSON export functionality
5. **API Integration**: Test builder and client integration

### Performance Tests

1. **Large Isochrone Handling**: Test with large travel times/areas
2. **High POI Density**: Test in areas with many POIs
3. **Query Optimization**: Test Overpass query performance
4. **Memory Usage**: Test memory efficiency with large result sets

### User Acceptance Tests

1. **Common Use Cases**: Test typical user scenarios
2. **Edge Cases**: Test boundary conditions and unusual inputs
3. **Error Recovery**: Test user experience during failures
4. **Export Functionality**: Test result export and visualization

## Implementation Phases

### Phase 1: Core Infrastructure
- Extend API builder and client classes
- Implement basic POI discovery pipeline stage
- Create result data structures
- Add basic error handling

### Phase 2: POI Query Enhancement
- Extend Overpass query system for polygon-based searches
- Implement POI categorization system
- Add result organization and filtering
- Enhance error handling with specific error types

### Phase 3: Integration and Export
- Integrate with existing export system
- Add visualization support
- Implement distance calculations
- Add comprehensive logging and monitoring

### Phase 4: Optimization and Polish
- Optimize query performance
- Add caching for repeated queries
- Enhance error messages and suggestions
- Add comprehensive documentation and examples

## Security Considerations

1. **Input Validation**: Validate all user inputs including coordinates and travel times
2. **Query Limits**: Implement reasonable limits on isochrone size and POI counts
3. **Rate Limiting**: Respect OpenStreetMap API rate limits
4. **Path Security**: Ensure output paths are secure and within allowed directories
5. **Error Information**: Avoid exposing sensitive system information in error messages

## Performance Considerations

1. **Query Optimization**: Use efficient Overpass queries with appropriate bounding boxes
2. **Result Caching**: Cache isochrones and POI results for repeated queries
3. **Streaming Processing**: Process large POI result sets in chunks
4. **Memory Management**: Efficiently handle large geographic datasets
5. **Parallel Processing**: Consider parallel processing for multiple POI categories

## Monitoring and Observability

1. **Performance Metrics**: Track query times, result sizes, and success rates
2. **Error Tracking**: Monitor error frequencies and types
3. **Usage Analytics**: Track feature usage patterns and popular configurations
4. **Resource Monitoring**: Monitor memory and CPU usage during processing
5. **API Health**: Monitor external API dependencies (OpenStreetMap, geocoding)