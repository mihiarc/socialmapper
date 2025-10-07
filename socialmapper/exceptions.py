"""Simple exception hierarchy for SocialMapper.

This module provides a minimal set of exceptions for the library.
All exceptions inherit from SocialMapperError for easy catching.
"""


class SocialMapperError(Exception):
    """
    Base exception for all SocialMapper library errors.

    Serves as the parent class for all custom exceptions in the
    library. Users can catch this exception to handle any
    library-specific errors.

    Examples
    --------
    >>> try:
    ...     # SocialMapper operation
    ...     pass
    ... except SocialMapperError as e:
    ...     print(f"Library error: {e}")
    """
    pass


class ValidationError(SocialMapperError):
    """
    Exception raised when input validation fails.

    Indicates that user-provided parameters do not meet the required
    criteria for processing. Common causes include invalid coordinate
    ranges, unsupported travel modes, or missing required parameters.

    Examples
    --------
    >>> from socialmapper import ValidationError
    >>> # Raised for invalid coordinates:
    >>> # raise ValidationError("Latitude must be between -90 and 90")
    >>> # Raised for invalid travel mode:
    >>> # raise ValidationError("Travel mode must be 'walking' or 'driving'")
    >>> # Raised for missing parameters:
    >>> # raise ValidationError("Census API key is required")
    """
    pass


class APIError(SocialMapperError):
    """
    Exception raised when external API calls fail.

    Indicates failures in communication with external services such
    as Census Bureau API, OpenStreetMap Overpass API, or geocoding
    services. Can be caused by network issues, rate limiting, or
    service unavailability.

    Examples
    --------
    >>> from socialmapper import APIError
    >>> # Raised for Census API errors:
    >>> # raise APIError("Census API returned 403: Invalid API key")
    >>> # Raised for Overpass API timeout:
    >>> # raise APIError("Overpass API request timed out")
    >>> # Raised for network issues:
    >>> # raise APIError("Failed to connect to geocoding service")
    """
    pass


class DataError(SocialMapperError):
    """
    Exception raised when data processing or retrieval fails.

    Indicates issues with data availability, quality, or
    transformation during processing. Common causes include empty
    query results, malformed data, or unsupported data formats.

    Examples
    --------
    >>> from socialmapper import DataError
    >>> # Raised for empty results:
    >>> # raise DataError("No census data found for specified area")
    >>> # Raised for insufficient data:
    >>> # raise DataError("Insufficient POIs for analysis")
    >>> # Raised for format errors:
    >>> # raise DataError("Unable to parse GeoJSON response")
    """
    pass


class AnalysisError(SocialMapperError):
    """
    Exception raised when spatial analysis operations fail.

    Indicates failures in computational operations such as isochrone
    generation, network routing, or spatial computations. Can be
    caused by algorithmic issues, insufficient data, or computational
    limitations.

    Examples
    --------
    >>> from socialmapper import AnalysisError
    >>> # Raised for isochrone failures:
    >>> # raise AnalysisError("Failed to generate isochrone: no routes found")
    >>> # Raised for network errors:
    >>> # raise AnalysisError("Network graph contains no reachable nodes")
    >>> # Raised for spatial computation errors:
    >>> # raise AnalysisError("Invalid geometry for spatial operation")
    """
    pass


# Legacy aliases for backward compatibility during transition
ConfigurationError = ValidationError
ExternalAPIError = APIError
DataProcessingError = DataError
FileSystemError = SocialMapperError
VisualizationError = SocialMapperError
