"""Pythonic exception hierarchy for SocialMapper.

Provides clear, standard Python exceptions instead of complex Result types.
"""

from typing import Any, Dict, Optional


class SocialMapperError(Exception):
    """Base exception for all SocialMapper errors.
    
    Provides consistent error information and context throughout the API.
    """
    
    def __init__(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize with message and optional context.
        
        Args:
            message: Human-readable error message
            context: Additional context information
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.context = context or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """Return formatted error message with context."""
        msg = super().__str__()
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg += f" (context: {context_str})"
        return msg


class ValidationError(SocialMapperError):
    """Raised when input parameters are invalid.
    
    Examples:
        - Invalid location format
        - Travel time out of range
        - Unknown POI types
        - Invalid census variables
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Any = None,
        valid_options: Optional[list] = None,
        **kwargs
    ):
        """Initialize validation error with specific field information.
        
        Args:
            message: Description of validation failure
            field: Name of the invalid field
            value: The invalid value provided
            valid_options: List of valid alternatives
            **kwargs: Additional context
        """
        context = kwargs
        if field:
            context['field'] = field
        if value is not None:
            context['invalid_value'] = value
        if valid_options:
            context['valid_options'] = valid_options
            
        super().__init__(message, context)


class AnalysisError(SocialMapperError):
    """Raised when analysis execution fails.
    
    Examples:
        - Pipeline execution errors
        - Data processing failures
        - File I/O errors
        - Calculation errors
    """
    
    def __init__(
        self, 
        message: str, 
        stage: Optional[str] = None,
        **kwargs
    ):
        """Initialize analysis error with stage information.
        
        Args:
            message: Description of analysis failure
            stage: Analysis stage where error occurred
            **kwargs: Additional context
        """
        context = kwargs
        if stage:
            context['stage'] = stage
            
        super().__init__(message, context)


class APIError(SocialMapperError):
    """Raised when external API calls fail.
    
    Examples:
        - Census API failures
        - OpenStreetMap API errors
        - Geocoding service errors
        - Network connectivity issues
    """
    
    def __init__(
        self, 
        message: str, 
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        **kwargs
    ):
        """Initialize API error with response information.
        
        Args:
            message: Description of API failure
            api_name: Name of the failing API (e.g., "census", "osm")
            status_code: HTTP status code if applicable
            response_text: API response text if available
            **kwargs: Additional context
        """
        context = kwargs
        if api_name:
            context['api'] = api_name
        if status_code:
            context['status_code'] = status_code
        if response_text:
            context['response'] = response_text[:200]  # Truncate for readability
            
        super().__init__(message, context)


class ConfigurationError(SocialMapperError):
    """Raised when SocialMapper configuration is invalid.
    
    Examples:
        - Missing required configuration
        - Invalid configuration values
        - Conflicting configuration options
    """
    pass


# Convenience functions for common error patterns

def validate_location(location: str) -> None:
    """Validate location format and raise ValidationError if invalid."""
    if not location or not isinstance(location, str):
        raise ValidationError(
            "Location must be a non-empty string",
            field="location",
            value=location
        )
    
    if "," not in location:
        raise ValidationError(
            "Location must be in 'City, State' format",
            field="location", 
            value=location,
            valid_options=["San Francisco, CA", "New York, NY", "Austin, TX"]
        )


def validate_travel_time(travel_time: int) -> None:
    """Validate travel time and raise ValidationError if invalid."""
    if not isinstance(travel_time, int):
        raise ValidationError(
            "Travel time must be an integer",
            field="travel_time",
            value=travel_time
        )
    
    if not 1 <= travel_time <= 120:
        raise ValidationError(
            "Travel time must be between 1 and 120 minutes",
            field="travel_time",
            value=travel_time,
            valid_options="1-120 minutes"
        )


def validate_poi_types(poi_types: list) -> None:
    """Validate POI types list and raise ValidationError if invalid."""
    if poi_types is not None and not isinstance(poi_types, list):
        raise ValidationError(
            "POI types must be a list of strings",
            field="poi_types",
            value=poi_types
        )
    
    if poi_types is not None:
        for poi_type in poi_types:
            if not isinstance(poi_type, str):
                raise ValidationError(
                    "All POI types must be strings",
                    field="poi_types",
                    value=poi_type
                )