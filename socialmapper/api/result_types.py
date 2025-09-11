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


class Ok(Result[T, E]):
    """Successful result."""
    
    def __init__(self, value: T):
        super().__init__(value, True)


class Err(Result[T, E]):
    """Error result."""
    
    def __init__(self, error: E):
        super().__init__(error, False)


@dataclass
class DiscoveredPOI:
    """A Point of Interest discovered during analysis."""
    name: str
    category: str
    subcategory: str
    latitude: float
    longitude: float
    osm_id: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    amenity: Optional[str] = None
    shop: Optional[str] = None
    cuisine: Optional[str] = None
    additional_tags: Optional[Dict[str, str]] = None


@dataclass
class NearbyPOIDiscoveryConfig:
    """Configuration for nearby POI discovery operations."""
    location: Union[str, tuple]
    travel_time: int = 15
    travel_mode: str = "drive"
    poi_categories: Optional[List[str]] = None
    exclude_categories: Optional[List[str]] = None
    max_pois_per_category: Optional[int] = None
    output_directory: Path = Path("output")
    include_detailed_info: bool = True
    create_maps: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.travel_time < 1 or self.travel_time > 120:
            raise ValueError("Travel time must be between 1 and 120 minutes")
        
        if self.travel_mode not in ["drive", "walk", "bike"]:
            raise ValueError("Travel mode must be 'drive', 'walk', or 'bike'")


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
    discovered_pois: List[DiscoveredPOI] = field(default_factory=list)
    total_poi_count: int = 0
    unique_categories: List[str] = field(default_factory=list)
    category_counts: Dict[str, int] = field(default_factory=dict)
    isochrone_area_km2: float = 0.0
    files_created: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    poi_categories: List[str] = field(default_factory=list)
    center_location: Optional[Dict[str, float]] = None
    discovery_timestamp: Optional[str] = None


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