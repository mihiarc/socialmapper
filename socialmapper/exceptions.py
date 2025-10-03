"""Simple exception hierarchy for SocialMapper.

This module provides a minimal set of exceptions for the library.
All exceptions inherit from SocialMapperError for easy catching.
"""


class SocialMapperError(Exception):
    """Base exception for all SocialMapper errors.

    Users can catch this to handle any library-specific error.
    """
    pass


class ValidationError(SocialMapperError):
    """Raised when input validation fails.

    Examples:
        - Invalid coordinates
        - Invalid travel time/mode
        - Missing required parameters
        - Invalid configuration
    """
    pass


class APIError(SocialMapperError):
    """Raised when external API calls fail.

    Examples:
        - Census API errors
        - OpenStreetMap/Overpass API errors
        - Geocoding service errors
        - Network connectivity issues
    """
    pass


class DataError(SocialMapperError):
    """Raised when data processing fails.

    Examples:
        - No data found for query
        - Insufficient data for analysis
        - Data transformation errors
        - Invalid data formats
    """
    pass


class AnalysisError(SocialMapperError):
    """Raised when analysis operations fail.

    Examples:
        - Isochrone generation failures
        - Network analysis errors
        - Spatial computation errors
    """
    pass


# Legacy aliases for backward compatibility during transition
ConfigurationError = ValidationError
ExternalAPIError = APIError
DataProcessingError = DataError
FileSystemError = SocialMapperError
VisualizationError = SocialMapperError
