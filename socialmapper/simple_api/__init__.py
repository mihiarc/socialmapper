"""Simple, Pythonic API for SocialMapper.

This module provides a clean, intuitive interface that follows Python conventions
and eliminates the over-engineering of the legacy API.

Example:
    ```python
    from socialmapper.simple_api import SocialMapper, quick_analysis
    
    # Simple one-liner
    result = quick_analysis("San Francisco, CA", "amenity:library")
    print(f"Found {result['poi_count']} libraries")
    
    # Full client usage
    mapper = SocialMapper(api_key="your-census-key")
    result = mapper.analyze_location(
        "Chicago, IL",
        poi_types=["library", "school"], 
        travel_time=15,
        census_variables=["total_population", "median_household_income"]
    )
    print(f"Analysis complete: {result.poi_count} POIs found")
    ```
"""

from .client import SocialMapper
from .results import AnalysisResult, POIResult
from .exceptions import SocialMapperError, ValidationError, AnalysisError, APIError
from .convenience import (
    quick_analysis,
    analyze_libraries,
    analyze_schools,
    analyze_hospitals,
    analyze_parks,
    discover_food_access,
    discover_healthcare_access,
    compare_locations,
    analyze_custom_pois,
)

__all__ = [
    # Core classes
    "SocialMapper",
    "AnalysisResult", 
    "POIResult",
    # Exceptions
    "SocialMapperError",
    "ValidationError",
    "AnalysisError", 
    "APIError",
    # Convenience functions
    "quick_analysis",
    "analyze_libraries",
    "analyze_schools",
    "analyze_hospitals",
    "analyze_parks",
    "discover_food_access",
    "discover_healthcare_access",
    "compare_locations",
    "analyze_custom_pois",
]