"""Result types for SocialMapper operations.

This module provides Result types that are still used by pipeline operations
and POI discovery functionality, even though the main API is simplified.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

T = TypeVar('T')
E = TypeVar('E')


class ErrorType(Enum):
    """Types of errors that can occur."""
    VALIDATION = "validation"
    API_ERROR = "api_error"
    NETWORK = "network"
    DATA_PROCESSING = "data_processing"
    CONFIGURATION = "configuration"
    PROCESSING = "processing"
    POI_DISCOVERY = "poi_discovery"
    LOCATION_GEOCODING = "location_geocoding"
    ISOCHRONE_GENERATION = "isochrone_generation"
    POI_QUERY = "poi_query"


@dataclass
class Error:
    """Error information for failed operations."""
    message: str
    error_type: ErrorType = ErrorType.VALIDATION
    context: Optional[Dict[str, Any]] = None
    cause: Optional[Exception] = None

    def __str__(self) -> str:
        return f"{self.error_type.value}: {self.message}"


class Result(Generic[T, E]):
    """Result type for operations that can succeed or fail."""
    
    def __init__(self, value: Union[T, E], is_success: bool):
        self._value = value
        self._is_success = is_success
    
    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self._is_success
    
    def is_err(self) -> bool:
        """Check if result is an error."""
        return not self._is_success
    
    def unwrap(self) -> T:
        """Get the successful value or raise if error."""
        if self._is_success:
            return self._value
        raise ValueError(f"Called unwrap() on error result: {self._value}")
    
    def unwrap_err(self) -> E:
        """Get the error value or raise if successful."""
        if not self._is_success:
            return self._value
        raise ValueError(f"Called unwrap_err() on success result: {self._value}")
    
    def unwrap_or(self, default: T) -> T:
        """Get the successful value or return default if error."""
        if self._is_success:
            return self._value
        return default
    
    def unwrap_or_else(self, func) -> T:
        """Get the successful value or call func with error."""
        if self._is_success:
            return self._value
        return func(self._value)
    
    def map(self, func):
        """Map the successful value through a function."""
        if self._is_success:
            return Ok(func(self._value))
        return self
    
    def map_err(self, func):
        """Map the error value through a function."""
        if not self._is_success:
            return Err(func(self._value))
        return self
    
    def and_then(self, func):
        """Chain operations on successful values."""
        if self._is_success:
            return func(self._value)
        return self
    
    def or_else(self, func):
        """Chain operations on error values."""
        if not self._is_success:
            return func(self._value)
        return self


class Ok(Result[T, E]):
    """Successful result."""
    
    def __init__(self, value: T):
        super().__init__(value, True)


class Err(Result[T, E]):
    """Error result."""
    
    def __init__(self, error: E):
        super().__init__(error, False)


@dataclass(frozen=True)
class DiscoveredPOI:
    """A Point of Interest discovered during analysis."""
    id: str
    name: str
    category: str
    subcategory: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    amenity: Optional[str] = None
    shop: Optional[str] = None
    cuisine: Optional[str] = None
    straight_line_distance_m: Optional[float] = None
    travel_time_minutes: Optional[float] = None
    estimated_travel_time_min: Optional[float] = None
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    tags: Dict[str, str] = field(default_factory=dict)
    additional_tags: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        """Validate POI data after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("POI ID cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("POI name cannot be empty")
        
        if not (-90 <= self.latitude <= 90):
            raise ValueError("Invalid coordinates")
        
        if not (-180 <= self.longitude <= 180):
            raise ValueError("Invalid coordinates")
        
        if self.straight_line_distance_m is not None and self.straight_line_distance_m < 0:
            raise ValueError("Distance cannot be negative")
        
        if self.travel_time_minutes is not None and self.travel_time_minutes < 0:
            raise ValueError("Travel time cannot be negative")
        
        if self.estimated_travel_time_min is not None and self.estimated_travel_time_min < 0:
            raise ValueError("Travel time cannot be negative")


@dataclass
class NearbyPOIDiscoveryConfig:
    """Configuration for nearby POI discovery operations."""
    location: Union[str, tuple]
    travel_time: int = 15
    travel_mode: Any = None  # Will be set to TravelMode.DRIVE in __post_init__
    poi_categories: Optional[List[str]] = None
    exclude_categories: Optional[List[str]] = None
    max_pois_per_category: Optional[int] = None
    output_dir: Path = field(default_factory=lambda: Path("output"))
    include_poi_details: bool = True
    export_csv: bool = True
    export_geojson: bool = True
    create_map: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Import here to avoid circular import
        from ..isochrone.travel_modes import TravelMode
        
        # Set default travel mode
        if self.travel_mode is None:
            self.travel_mode = TravelMode.DRIVE
        
        # Import constants
        from ..constants import MIN_TRAVEL_TIME, MAX_TRAVEL_TIME
        
        if self.travel_time < MIN_TRAVEL_TIME or self.travel_time > MAX_TRAVEL_TIME:
            raise ValueError(f"Travel time must be between {MIN_TRAVEL_TIME} and {MAX_TRAVEL_TIME} minutes")
        
        # Validate location
        if isinstance(self.location, tuple):
            if len(self.location) != 2:
                raise ValueError("Coordinate location must be a tuple of (lat, lon)")
            lat, lon = self.location
            if not (-90 <= lat <= 90):
                raise ValueError("Invalid coordinates")
            if not (-180 <= lon <= 180):
                raise ValueError("Invalid coordinates")
        elif isinstance(self.location, str):
            if not self.location.strip():
                raise ValueError("Location address cannot be empty")
        else:
            raise ValueError("Location must be either an address string or (lat, lon) tuple")
        
        if self.max_pois_per_category is not None and self.max_pois_per_category <= 0:
            raise ValueError("max_pois_per_category must be positive")


@dataclass
class POIResult:
    """Result of POI discovery operation."""
    discovered_pois: List[DiscoveredPOI] = field(default_factory=list)
    total_poi_count: int = 0
    unique_categories: List[str] = field(default_factory=list)
    category_counts: Dict[str, int] = field(default_factory=dict)
    isochrone_area_km2: float = 0.0
    files_created: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class NearbyPOIResult:
    """Result of nearby POI discovery operation."""
    origin_location: Dict[str, float]
    travel_time: int
    travel_mode: Any  # TravelMode enum
    isochrone_area_km2: float = 0.0
    pois_by_category: Optional[Dict[str, List[DiscoveredPOI]]] = None
    total_poi_count: int = 0
    unique_categories: List[str] = field(default_factory=list)
    category_counts: Dict[str, int] = field(default_factory=dict)
    files_created: List[str] = field(default_factory=list)
    files_generated: Dict[str, Path] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    poi_categories: List[str] = field(default_factory=list)
    discovery_timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Initialize computed properties."""
        if self.pois_by_category is None:
            self.pois_by_category = {}
        
        # Update total_poi_count if not provided
        if self.total_poi_count == 0 and self.pois_by_category:
            self.total_poi_count = sum(len(pois) for pois in self.pois_by_category.values())
    
    @property
    def success(self) -> bool:
        """Check if the discovery operation was successful."""
        return self.total_poi_count > 0
    
    def get_all_pois(self) -> List[DiscoveredPOI]:
        """Get a flat list of all discovered POIs."""
        all_pois = []
        if self.pois_by_category:
            for pois in self.pois_by_category.values():
                all_pois.extend(pois)
        return all_pois
    
    def get_pois_by_distance(self, max_count: Optional[int] = None) -> List[DiscoveredPOI]:
        """Get POIs sorted by distance."""
        all_pois = self.get_all_pois()
        # Sort by straight_line_distance_m, handling None values
        sorted_pois = sorted(
            all_pois, 
            key=lambda poi: poi.straight_line_distance_m or float('inf')
        )
        
        if max_count is not None:
            return sorted_pois[:max_count]
        return sorted_pois
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the POI discovery result."""
        all_pois = self.get_all_pois()
        
        if not all_pois:
            return {
                "total_pois": 0,
                "avg_distance_m": 0,
                "min_distance_m": 0,
                "max_distance_m": 0,
                "categories": {},
            }
        
        distances = [poi.straight_line_distance_m for poi in all_pois if poi.straight_line_distance_m is not None]
        
        return {
            "total_pois": len(all_pois),
            "avg_distance_m": sum(distances) / len(distances) if distances else 0,
            "min_distance_m": min(distances) if distances else 0,
            "max_distance_m": max(distances) if distances else 0,
            "categories": {cat: len(pois) for cat, pois in self.pois_by_category.items()},
        }


# Helper functions for working with results
def collect_results(results: List[Result[T, E]]) -> Result[List[T], List[E]]:
    """Collect multiple results into a single result."""
    successes = []
    errors = []
    
    for result in results:
        if result.is_ok():
            successes.append(result.unwrap())
        else:
            errors.append(result.unwrap_err())
    
    if errors:
        return Err(errors)
    return Ok(successes)


def try_all(*operations) -> Result[List[Any], Error]:
    """Try all operations and return results."""
    results = []
    for op in operations:
        try:
            if callable(op):
                results.append(op())
            else:
                results.append(op)
        except Exception as e:
            return Err(Error(f"Operation failed: {e}", cause=e))
    return Ok(results)


class ResultCollector:
    """Helper for collecting multiple results."""
    
    def __init__(self):
        self.results = []
    
    def add(self, result: Result[T, E]):
        """Add a result to the collection."""
        self.results.append(result)
    
    def collect(self) -> Result[List[T], List[E]]:
        """Collect all results."""
        return collect_results(self.results)


def result_handler(func):
    """Decorator to handle exceptions and return Result types."""
    def wrapper(*args, **kwargs):
        try:
            return Ok(func(*args, **kwargs))
        except Exception as e:
            return Err(Error(str(e), cause=e))
    return wrapper


# Test utilities
def assert_ok(result: Result[T, E]) -> T:
    """Assert result is Ok and return value."""
    assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
    return result.unwrap()


def assert_err(result: Result[T, E]) -> E:
    """Assert result is Err and return error."""
    assert result.is_err(), f"Expected Err, got Ok: {result.unwrap()}"
    return result.unwrap_err()


def assert_err_type(result: Result[T, Error], error_type: ErrorType):
    """Assert result is Err with specific error type."""
    error = assert_err(result)
    assert error.error_type == error_type, f"Expected {error_type}, got {error.error_type}"