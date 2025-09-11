"""Pythonic API for SocialMapper.

This module provides a clean, intuitive interface that follows Python conventions.

Example:
    ```python
    from socialmapper import SocialMapper, quick_analysis
    
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
from .convenience import (
    analyze_custom_pois,
    analyze_hospitals,
    analyze_libraries,
    analyze_parks,
    analyze_schools,
    compare_locations,
    discover_food_access,
    discover_healthcare_access,
    quick_analysis,
)
from .exceptions import AnalysisError, APIError, SocialMapperError, ValidationError
from .results import AnalysisResult, POIResult

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
