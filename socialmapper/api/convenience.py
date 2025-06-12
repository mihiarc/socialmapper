"""
Convenience functions for common SocialMapper use cases.

These functions provide simple interfaces for the most common operations.
"""

from pathlib import Path
from typing import List, Optional, Union

from .builder import AnalysisResult, GeographicLevel, SocialMapperBuilder
from .client import SocialMapperClient
from .result_types import Error, Result


def quick_analysis(
    location: str,
    poi_search: str,
    travel_time: int = 15,
    census_variables: Optional[List[str]] = None,
    output_dir: Union[str, Path] = "output",
) -> Result[AnalysisResult, Error]:
    """
    Quick analysis for a location with minimal configuration.

    Args:
        location: Location in "City, State" format
        poi_search: POI search in "type:name" format (e.g., "amenity:library")
        travel_time: Travel time in minutes (default: 15)
        census_variables: Census variables to analyze
        output_dir: Output directory for results

    Returns:
        Result with AnalysisResult or Error

    Example:
        ```python
        result = quick_analysis(
            "Portland, OR",
            "amenity:school",
            travel_time=10,
            census_variables=["total_population", "median_income"]
        )

        if result.is_ok():
            analysis = result.unwrap()
            print(f"Found {analysis.poi_count} schools")
        ```
    """
    # Parse POI search
    try:
        poi_type, poi_name = poi_search.split(":", 1)
    except ValueError:
        return Result.err(
            Error(
                type=ErrorType.VALIDATION,
                message=f"POI search must be in 'type:name' format, got: {poi_search}",
            )
        )

    # Use the modern client
    with SocialMapperClient() as client:
        return client.analyze(
            location=location,
            poi_type=poi_type,
            poi_name=poi_name,
            travel_time=travel_time,
            census_variables=census_variables or ["total_population"],
            output_dir=output_dir,
        )


def analyze_location(
    city: str, state: str, poi_type: str = "amenity", poi_name: str = "library", **options
) -> Result[AnalysisResult, Error]:
    """
    Analyze a specific location with common POIs.

    Args:
        city: City name
        state: State name or abbreviation
        poi_type: OpenStreetMap POI type
        poi_name: OpenStreetMap POI name
        **options: Additional options (travel_time, census_variables, etc.)

    Returns:
        Result with AnalysisResult or Error

    Example:
        ```python
        result = analyze_location(
            "Austin",
            "TX",
            poi_type="leisure",
            poi_name="park",
            travel_time=20
        )
        ```
    """
    # Build configuration
    config = SocialMapperBuilder().with_location(city, state).with_osm_pois(poi_type, poi_name)

    # Apply options
    if "travel_time" in options:
        config.with_travel_time(options["travel_time"])

    if "census_variables" in options:
        config.with_census_variables(*options["census_variables"])

    if "output_dir" in options:
        config.with_output_directory(options["output_dir"])

    if "geographic_level" in options:
        level = GeographicLevel[options["geographic_level"].upper().replace("-", "_")]
        config.with_geographic_level(level)

    # Run analysis
    with SocialMapperClient() as client:
        return client.run_analysis(config.build())


def analyze_custom_pois(
    poi_file: Union[str, Path],
    travel_time: int = 15,
    census_variables: Optional[List[str]] = None,
    name_field: Optional[str] = None,
    type_field: Optional[str] = None,
    **options,
) -> Result[AnalysisResult, Error]:
    """
    Analyze custom POIs from a file.

    Args:
        poi_file: Path to CSV or JSON file with POI coordinates
        travel_time: Travel time in minutes
        census_variables: Census variables to analyze
        name_field: Field name for POI names in the file
        type_field: Field name for POI types in the file
        **options: Additional options

    Returns:
        Result with AnalysisResult or Error

    Example:
        ```python
        result = analyze_custom_pois(
            "my_locations.csv",
            travel_time=20,
            census_variables=["total_population", "median_age"],
            name_field="location_name"
        )
        ```
    """
    # Build configuration
    config = (
        SocialMapperBuilder()
        .with_custom_pois(poi_file, name_field, type_field)
        .with_travel_time(travel_time)
    )

    # Add census variables
    if census_variables:
        config.with_census_variables(*census_variables)
    else:
        config.with_census_variables("total_population")

    # Apply additional options

    if options.get("enable_isochrones"):
        config.enable_isochrone_export()

    if "output_dir" in options:
        config.with_output_directory(options["output_dir"])

    if "max_pois" in options:
        config.limit_pois(options["max_pois"])

    # Run analysis
    with SocialMapperClient() as client:
        return client.run_analysis(config.build())


# Pandas DataFrame integration
def analyze_dataframe(
    df: "pd.DataFrame",
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    name_col: Optional[str] = "name",
    type_col: Optional[str] = "type",
    **options,
) -> Result[AnalysisResult, Error]:
    """
    Analyze POIs from a pandas DataFrame.

    Args:
        df: DataFrame with POI data
        lat_col: Column name for latitude
        lon_col: Column name for longitude
        name_col: Column name for POI names
        type_col: Column name for POI types
        **options: Additional analysis options

    Returns:
        Result with AnalysisResult or Error

    Example:
        ```python
        import pandas as pd

        df = pd.DataFrame({
            'latitude': [37.7749, 37.7849, 37.7949],
            'longitude': [-122.4194, -122.4094, -122.3994],
            'name': ['Library 1', 'Library 2', 'Library 3'],
            'type': ['library', 'library', 'library']
        })

        result = analyze_dataframe(
            df,
            travel_time=15,
            census_variables=["total_population"]
        )
        ```
    """
    # Save DataFrame to temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name

    try:
        # Use the custom POI analyzer
        return analyze_custom_pois(temp_path, name_field=name_col, type_field=type_col, **options)
    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)
