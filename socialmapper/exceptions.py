"""Enhanced exception hierarchy for SocialMapper.

This module provides helpful, context-aware exceptions that guide users
toward solutions. All exceptions inherit from SocialMapperError for
easy catching.
"""

from .constants import HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_SERVER_ERROR


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

    def __init__(self, message: str, help_text: str | None = None):
        """
        Initialize exception with message and optional help text.

        Parameters
        ----------
        message : str
            Main error message explaining what went wrong.
        help_text : str, optional
            Additional guidance on how to fix the issue.
        """
        self.help_text = help_text
        full_message = f"{message}\n\n{help_text}" if help_text else message
        super().__init__(full_message)



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


# Specific helpful exceptions for common issues


class MissingAPIKeyError(ValidationError):
    """
    Exception raised when Census API key is missing.

    This error occurs when attempting Census operations without
    configuring an API key. Provides clear guidance on obtaining
    and configuring a free Census API key.
    """

    def __init__(self, service: str = "Census"):
        """
        Initialize with helpful guidance for missing API key.

        Parameters
        ----------
        service : str, optional
            Name of the service requiring API key, by default "Census".
        """
        message = f"{service} API key not found"

        help_text = """Quick Solutions:

1. Get a free Census API key (takes 2 minutes):
   - Visit: https://api.census.gov/data/key_signup.html
   - Check your email for the key
   - Set environment variable: export CENSUS_API_KEY='your_key'
   - Or add to .env file: CENSUS_API_KEY=your_key

2. Use the key manager (recommended):
   socialmapper-keys set census_api your_key_here

Documentation: https://mihiarc.github.io/socialmapper/setup"""

        super().__init__(message, help_text)


class InvalidLocationError(ValidationError):
    """
    Exception raised when location cannot be geocoded.

    Provides suggestions for valid location formats and similar
    location names to help users correct their input.
    """

    def __init__(
        self,
        location: str,
        suggestions: list[str] | None = None
    ):
        """
        Initialize with location and optional suggestions.

        Parameters
        ----------
        location : str
            The invalid location that was provided.
        suggestions : list of str, optional
            Similar valid locations to suggest.
        """
        message = f"Could not find location: '{location}'"

        help_lines = [
            "Location Tips:",
            "- Try 'City, State' format (e.g., 'Portland, OR')",
            "- Use full state names or 2-letter codes",
            "- Include ZIP code for specific addresses",
            "- Check spelling and state abbreviations",
        ]

        if suggestions:
            help_lines.append("\nDid you mean one of these?")
            help_lines.extend(f"  - {suggestion}" for suggestion in suggestions[:5])

        help_text = "\n".join(help_lines)
        super().__init__(message, help_text)


class InvalidPOICategoryError(ValidationError):
    """
    Exception raised when invalid POI category is specified.

    Lists valid POI categories to help users select the correct one.
    """

    def __init__(self, category: str, valid_categories: list[str]):
        """
        Initialize with invalid category and valid options.

        Parameters
        ----------
        category : str
            The invalid category that was provided.
        valid_categories : list of str
            List of valid category names.
        """
        message = f"Invalid POI category: '{category}'"

        help_lines = [
            "Valid POI categories:",
        ]

        help_lines.extend(f"  - {cat}" for cat in sorted(valid_categories))

        help_lines.append(
            "\nExample: get_poi('Portland, OR', category='food_and_drink')"
        )

        help_text = "\n".join(help_lines)
        super().__init__(message, help_text)


class NetworkError(APIError):
    """
    Exception raised for network connectivity issues.

    Provides helpful guidance on troubleshooting network problems
    and suggests retry strategies.
    """

    def __init__(
        self,
        service: str,
        original_error: str | None = None,
        retry_suggested: bool = True
    ):
        """
        Initialize with service name and error details.

        Parameters
        ----------
        service : str
            Name of the service that couldn't be reached.
        original_error : str, optional
            Original error message from the network call.
        retry_suggested : bool, optional
            Whether to suggest retrying, by default True.
        """
        message = f"Network error connecting to {service}"

        if original_error:
            message += f": {original_error}"

        help_lines = [
            "Troubleshooting:",
            "- Check your internet connection",
            "- Verify firewall/proxy settings",
            "- The service may be temporarily down",
        ]

        if retry_suggested:
            help_lines.append("- Try again in a few moments")

        help_lines.append(
            f"\nService status: Check if {service} is operational"
        )

        help_text = "\n".join(help_lines)
        super().__init__(message, help_text)


class RateLimitError(APIError):
    """
    Exception raised when API rate limit is exceeded.

    Provides guidance on rate limiting and how to avoid it.
    """

    def __init__(
        self,
        service: str,
        retry_after: int | None = None
    ):
        """
        Initialize with service and optional retry timing.

        Parameters
        ----------
        service : str
            Name of the service that rate limited the request.
        retry_after : int, optional
            Seconds to wait before retrying, if known.
        """
        message = f"Rate limit exceeded for {service}"

        help_lines = [
            "Rate Limiting Tips:",
            "- Add delays between requests",
            "- Batch operations when possible",
            "- Use caching to reduce API calls",
        ]

        if retry_after:
            help_lines.insert(
                0,
                f"Retry after: {retry_after} seconds"
            )

        help_lines.append(
            "\nDocumentation: https://mihiarc.github.io/socialmapper/api-limits"
        )

        help_text = "\n".join(help_lines)
        super().__init__(message, help_text)


class InvalidAPIResponseError(APIError):
    """
    Exception raised when API returns invalid or unexpected data.

    Helps diagnose issues with API responses and suggests actions.
    """

    def __init__(
        self,
        service: str,
        status_code: int | None = None,
        details: str | None = None
    ):
        """
        Initialize with service and response details.

        Parameters
        ----------
        service : str
            Name of the service that returned invalid data.
        status_code : int, optional
            HTTP status code from the response.
        details : str, optional
            Additional details about what was invalid.
        """
        message = f"Invalid response from {service}"

        if status_code:
            message += f" (HTTP {status_code})"

        help_lines = []

        if status_code == HTTP_FORBIDDEN:
            help_lines.append("This usually means:")
            help_lines.append("- Invalid or missing API key")
            help_lines.append("- API key lacks required permissions")
        elif status_code == HTTP_NOT_FOUND:
            help_lines.append("This usually means:")
            help_lines.append("- Resource not found")
            help_lines.append("- Check location or identifier")
        elif status_code and status_code >= HTTP_SERVER_ERROR:
            help_lines.append("This is a server error:")
            help_lines.append("- The service is having issues")
            help_lines.append("- Try again later")

        if details:
            help_lines.append(f"\nDetails: {details}")

        if help_lines:
            help_text = "\n".join(help_lines)
        else:
            help_text = "Check service documentation for details"

        super().__init__(message, help_text)


# Legacy aliases for backward compatibility during transition
ConfigurationError = ValidationError
ExternalAPIError = APIError
DataProcessingError = DataError
FileSystemError = SocialMapperError
VisualizationError = SocialMapperError
