"""Convenience functions for common SocialMapper use cases.

Simple one-line functions for the most common analysis scenarios.
"""

from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from .client import SocialMapper
from .results import AnalysisResult, POIResult


def quick_analysis(
    location: str,
    poi_search: str,
    travel_time: int = 15,
    travel_mode: str = "drive",
    census_variables: Optional[List[str]] = None,
    output_dir: str = "output"
) -> Dict[str, Any]:
    """Quick analysis for a location with minimal setup.
    
    This is the simplest way to run a SocialMapper analysis.
    
    Args:
        location: Location in "City, State" format
        poi_search: POI search in "type:name" or "name" format (e.g., "amenity:library", "library")
        travel_time: Travel time in minutes (default: 15)
        travel_mode: Travel mode ("drive", "walk", "bike")
        census_variables: Census variables to analyze
        output_dir: Output directory for results
    
    Returns:
        Dictionary with analysis results
    
    Example:
        ```python
        result = quick_analysis(
            "Portland, OR",
            "amenity:library",
            travel_time=20,
            census_variables=["total_population", "median_household_income"]
        )
        print(f"Found {result['poi_count']} libraries")
        ```
    """
    # Parse POI search string
    if ":" in poi_search:
        poi_type, poi_name = poi_search.split(":", 1)
        poi_types = [poi_name]
    else:
        poi_types = [poi_search]
    
    # Create client and run analysis
    mapper = SocialMapper()
    result = mapper.analyze_location(
        location=location,
        poi_types=poi_types,
        travel_time=travel_time,
        travel_mode=travel_mode,
        census_variables=census_variables,
        output_dir=output_dir
    )
    
    return result.to_dict()


def analyze_libraries(
    location: str,
    travel_time: int = 15,
    travel_mode: str = "drive",
    include_demographics: bool = True,
    output_dir: str = "output"
) -> AnalysisResult:
    """Analyze access to libraries in a location.
    
    Preset analysis for library accessibility with common demographic variables.
    
    Args:
        location: Location in "City, State" format
        travel_time: Travel time in minutes
        travel_mode: Travel mode ("drive", "walk", "bike")
        include_demographics: Whether to include demographic analysis
        output_dir: Output directory for results
    
    Returns:
        AnalysisResult with library accessibility data
    
    Example:
        ```python
        result = analyze_libraries("San Francisco, CA", travel_time=20, travel_mode="walk")
        result.print_summary()
        ```
    """
    census_vars = None
    if include_demographics:
        census_vars = [
            "total_population",
            "median_household_income", 
            "education_bachelors_plus",
            "median_age"
        ]
    
    mapper = SocialMapper()
    return mapper.analyze_location(
        location=location,
        poi_types=["library"],
        travel_time=travel_time,
        travel_mode=travel_mode,
        census_variables=census_vars,
        output_dir=output_dir
    )


def analyze_schools(
    location: str,
    travel_time: int = 15,
    travel_mode: str = "drive",
    include_demographics: bool = True,
    output_dir: str = "output"
) -> AnalysisResult:
    """Analyze access to schools in a location.
    
    Preset analysis for school accessibility with education-relevant demographics.
    
    Args:
        location: Location in "City, State" format
        travel_time: Travel time in minutes
        travel_mode: Travel mode ("drive", "walk", "bike")
        include_demographics: Whether to include demographic analysis
        output_dir: Output directory for results
    
    Returns:
        AnalysisResult with school accessibility data
    """
    census_vars = None
    if include_demographics:
        census_vars = [
            "total_population",
            "median_household_income",
            "children_under_18",
            "education_high_school_plus"
        ]
    
    mapper = SocialMapper()
    return mapper.analyze_location(
        location=location,
        poi_types=["school"],
        travel_time=travel_time,
        travel_mode=travel_mode,
        census_variables=census_vars,
        output_dir=output_dir
    )


def analyze_hospitals(
    location: str,
    travel_time: int = 30,
    travel_mode: str = "drive",
    include_demographics: bool = True,
    output_dir: str = "output"
) -> AnalysisResult:
    """Analyze access to hospitals in a location.
    
    Preset analysis for hospital accessibility with health-relevant demographics.
    Uses 30-minute default travel time since hospitals are typically accessed
    from greater distances.
    
    Args:
        location: Location in "City, State" format
        travel_time: Travel time in minutes (default: 30)
        travel_mode: Travel mode ("drive", "walk", "bike")
        include_demographics: Whether to include demographic analysis
        output_dir: Output directory for results
    
    Returns:
        AnalysisResult with hospital accessibility data
    """
    census_vars = None
    if include_demographics:
        census_vars = [
            "total_population",
            "median_household_income",
            "median_age",
            "seniors_65_plus",
            "disability_status"
        ]
    
    mapper = SocialMapper()
    return mapper.analyze_location(
        location=location,
        poi_types=["hospital"],
        travel_time=travel_time,
        travel_mode=travel_mode,
        census_variables=census_vars,
        output_dir=output_dir
    )


def analyze_parks(
    location: str,
    travel_time: int = 15,
    travel_mode: str = "walk",
    include_demographics: bool = True,
    output_dir: str = "output"
) -> AnalysisResult:
    """Analyze access to parks in a location.
    
    Preset analysis for park accessibility with recreation-relevant demographics.
    Uses walking as default travel mode since parks are often accessed on foot.
    
    Args:
        location: Location in "City, State" format
        travel_time: Travel time in minutes
        travel_mode: Travel mode ("drive", "walk", "bike") - default: "walk"
        include_demographics: Whether to include demographic analysis
        output_dir: Output directory for results
    
    Returns:
        AnalysisResult with park accessibility data
    """
    census_vars = None
    if include_demographics:
        census_vars = [
            "total_population",
            "median_household_income",
            "children_under_18",
            "median_age"
        ]
    
    mapper = SocialMapper()
    return mapper.analyze_location(
        location=location,
        poi_types=["park"],
        travel_time=travel_time,
        travel_mode=travel_mode,
        census_variables=census_vars,
        output_dir=output_dir
    )


def discover_food_access(
    location: str,
    travel_time: int = 20,
    travel_mode: str = "drive",
    output_dir: str = "output"
) -> POIResult:
    """Discover food access options near a location.
    
    Finds grocery stores, supermarkets, restaurants, and food-related POIs
    within travel time of a location.
    
    Args:
        location: Location in "City, State" format
        travel_time: Travel time in minutes
        travel_mode: Travel mode ("drive", "walk", "bike")
        output_dir: Output directory for results
    
    Returns:
        POIResult with food access options
    """
    mapper = SocialMapper()
    return mapper.discover_nearby_pois(
        location=location,
        travel_time=travel_time,
        travel_mode=travel_mode,
        poi_categories=["food_and_drink", "shopping"],
        output_dir=output_dir
    )


def discover_healthcare_access(
    location: str, 
    travel_time: int = 30,
    travel_mode: str = "drive",
    output_dir: str = "output"
) -> POIResult:
    """Discover healthcare access options near a location.
    
    Finds hospitals, clinics, pharmacies, and health-related POIs
    within travel time of a location.
    
    Args:
        location: Location in "City, State" format
        travel_time: Travel time in minutes (default: 30)
        travel_mode: Travel mode ("drive", "walk", "bike")
        output_dir: Output directory for results
    
    Returns:
        POIResult with healthcare access options
    """
    mapper = SocialMapper()
    return mapper.discover_nearby_pois(
        location=location,
        travel_time=travel_time,
        travel_mode=travel_mode,
        poi_categories=["healthcare"],
        output_dir=output_dir
    )


def compare_locations(
    locations: List[str],
    poi_types: List[str],
    travel_time: int = 15,
    travel_mode: str = "drive",
    census_variables: Optional[List[str]] = None
) -> Dict[str, AnalysisResult]:
    """Compare accessibility across multiple locations.
    
    Runs the same analysis for multiple locations and returns results
    for easy comparison.
    
    Args:
        locations: List of locations in "City, State" format
        poi_types: List of POI types to analyze
        travel_time: Travel time in minutes
        travel_mode: Travel mode ("drive", "walk", "bike")
        census_variables: Census variables to analyze
    
    Returns:
        Dictionary mapping location names to AnalysisResult objects
    
    Example:
        ```python
        results = compare_locations(
            ["Portland, OR", "Seattle, WA", "San Francisco, CA"],
            poi_types=["library"],
            travel_time=15
        )
        
        for location, result in results.items():
            print(f"{location}: {result.poi_count} libraries")
        ```
    """
    mapper = SocialMapper()
    results = {}
    
    for location in locations:
        try:
            result = mapper.analyze_location(
                location=location,
                poi_types=poi_types,
                travel_time=travel_time,
                travel_mode=travel_mode,
                census_variables=census_variables,
                output_dir=f"output/{location.replace(', ', '_').replace(' ', '_')}"
            )
            results[location] = result
        except Exception as e:
            print(f"Analysis failed for {location}: {e}")
            # Continue with other locations
    
    return results


# Legacy compatibility - map old function names to new ones
def analyze_custom_pois(
    poi_file: Union[str, Path],
    travel_time: int = 15,
    travel_mode: str = "drive", 
    census_variables: Optional[List[str]] = None,
    output_dir: str = "output"
) -> AnalysisResult:
    """Analyze accessibility using custom POI coordinates from a file.
    
    This function provides backward compatibility with the old API.
    
    Args:
        poi_file: Path to CSV file with POI coordinates
        travel_time: Travel time in minutes
        travel_mode: Travel mode ("drive", "walk", "bike") 
        census_variables: Census variables to analyze
        output_dir: Output directory for results
    
    Returns:
        AnalysisResult with analysis data
    """
    mapper = SocialMapper()
    return mapper.analyze_custom_pois(
        poi_file=poi_file,
        travel_time=travel_time,
        travel_mode=travel_mode,
        census_variables=census_variables,
        output_dir=output_dir
    )


# Note: discover_food_access and discover_healthcare_access are already defined above