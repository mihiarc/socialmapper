"""Custom exception hierarchy for SocialMapper.

This module provides a comprehensive exception system with:
- Clear exception hierarchy
- Rich error context
- Exception chaining
- User-friendly error messages
- Structured logging support
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, ClassVar


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorCategory(Enum):
    """Categories of errors for better organization."""

    VALIDATION = auto()
    NETWORK = auto()
    DATA_PROCESSING = auto()
    CONFIGURATION = auto()
    EXTERNAL_API = auto()
    FILE_SYSTEM = auto()
    ANALYSIS = auto()
    VISUALIZATION = auto()


@dataclass
class ErrorContext:
    """Rich context for error reporting."""

    timestamp: datetime = field(default_factory=datetime.now)
    category: ErrorCategory = ErrorCategory.ANALYSIS
    severity: ErrorSeverity = ErrorSeverity.ERROR
    operation: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    user_message: str | None = None
    technical_details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.name,
            "severity": self.severity.name,
            "operation": self.operation,
            "details": self.details,
            "suggestions": self.suggestions,
            "user_message": self.user_message,
            "technical_details": self.technical_details,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class SocialMapperError(Exception):
    """Base exception for all SocialMapper errors.
    
    This provides rich error context and chaining support.
    """

    default_message: ClassVar[str] = "An error occurred in SocialMapper"

    def __init__(
        self,
        message: str | None = None,
        context: ErrorContext | None = None,
        cause: Exception | None = None,
        **kwargs,
    ):
        """Initialize with rich context.
        
        Args:
            message: User-friendly error message
            context: Detailed error context
            cause: Original exception that caused this error
            **kwargs: Additional context details
        """
        self.message = message or self.default_message
        self.context = context or ErrorContext()
        self.cause = cause

        # Add any kwargs to context details
        if kwargs:
            self.context.details.update(kwargs)

        # Set user message if not already set
        if not self.context.user_message:
            self.context.user_message = self.message

        # Capture technical details if cause is provided
        if cause and not self.context.technical_details:
            self.context.technical_details = f"{type(cause).__name__}: {cause!s}"

        # Chain the exception
        super().__init__(self.message)
        if cause:
            self.__cause__ = cause

    def __str__(self) -> str:
        """User-friendly string representation."""
        parts = [self.message]

        if self.context.suggestions:
            parts.append("\n\nSuggestions:")
            for i, suggestion in enumerate(self.context.suggestions, 1):
                parts.append(f"  {i}. {suggestion}")

        if self.context.operation:
            parts.append(f"\nOperation: {self.context.operation}")

        return "\n".join(parts)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"category={self.context.category.name}, "
            f"severity={self.context.severity.name})"
        )

    def get_full_traceback(self) -> str:
        """Get complete traceback including chained exceptions."""
        return "".join(traceback.format_exception(type(self), self, self.__traceback__))

    def add_suggestion(self, suggestion: str) -> SocialMapperError:
        """Add a suggestion for resolving the error."""
        self.context.suggestions.append(suggestion)
        return self

    def with_operation(self, operation: str) -> SocialMapperError:
        """Set the operation context."""
        self.context.operation = operation
        return self

    def with_details(self, **details) -> SocialMapperError:
        """Add additional context details."""
        self.context.details.update(details)
        return self


# Configuration Errors
class ConfigurationError(SocialMapperError):
    """Raised when there are configuration issues."""

    default_message = "Configuration error"

    def __init__(self, message: str | None = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.ERROR,
        )
        super().__init__(message, context, **kwargs)


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing."""

    default_message = "Required API key is missing"

    def __init__(self, api_name: str = "Census", **kwargs):
        message = f"{api_name} API key is required but not provided"
        super().__init__(message, api_name=api_name, **kwargs)
        self.add_suggestion(f"Set the {api_name.upper()}_API_KEY environment variable")
        self.add_suggestion("Or pass the API key directly to the configuration")


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid."""

    default_message = "Invalid configuration values"

    def __init__(self, field: str, value: Any, reason: str, **kwargs):
        message = f"Invalid value for '{field}': {value}. {reason}"
        super().__init__(
            message,
            field=field,
            value=value,
            reason=reason,
            **kwargs
        )


# Validation Errors
class ValidationError(SocialMapperError):
    """Raised when input validation fails."""

    default_message = "Validation error"

    def __init__(self, message: str | None = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
        )
        super().__init__(message, context, **kwargs)


class InvalidLocationError(ValidationError):
    """Raised when location format is invalid."""

    default_message = "Invalid location format"

    def __init__(self, location: str, **kwargs):
        message = f"Invalid location format: '{location}'"
        super().__init__(message, location=location, **kwargs)
        self.add_suggestion("Use format: 'City, State' (e.g., 'San Francisco, CA')")
        self.add_suggestion("Or use format: 'City, State Code' (e.g., 'San Francisco, California')")


class InvalidCensusVariableError(ValidationError):
    """Raised when census variable is invalid."""

    default_message = "Invalid census variable"

    def __init__(self, variable: str, available: list[str] | None = None, **kwargs):
        message = f"Invalid census variable: '{variable}'"
        super().__init__(message, variable=variable, **kwargs)

        if available:
            self.add_suggestion(f"Available variables: {', '.join(available[:5])}...")
        self.add_suggestion("Check the census variable documentation")


class InvalidTravelTimeError(ValidationError):
    """Raised when travel time is out of range."""

    default_message = "Invalid travel time"

    def __init__(self, travel_time: int, min_time: int = 1, max_time: int = 60, **kwargs):
        message = f"Travel time {travel_time} is out of range [{min_time}, {max_time}]"
        super().__init__(
            message,
            travel_time=travel_time,
            min_time=min_time,
            max_time=max_time,
            **kwargs
        )
        self.add_suggestion(f"Use a travel time between {min_time} and {max_time} minutes")


# Data Processing Errors
class DataProcessingError(SocialMapperError):
    """Raised during data processing operations."""

    default_message = "Data processing error"

    def __init__(self, message: str | None = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.DATA_PROCESSING,
            severity=ErrorSeverity.ERROR,
        )
        super().__init__(message, context, **kwargs)


class NoDataFoundError(DataProcessingError):
    """Raised when no data is found for the query."""

    default_message = "No data found"

    def __init__(self, data_type: str, location: str | None = None, **kwargs):
        message = f"No {data_type} found"
        if location:
            message += f" in {location}"

        super().__init__(message, data_type=data_type, location=location, **kwargs)
        self.add_suggestion("Try a different location or expand the search area")
        self.add_suggestion(f"Verify that {data_type} exist in this area")


class InsufficientDataError(DataProcessingError):
    """Raised when there's not enough data for analysis."""

    default_message = "Insufficient data for analysis"

    def __init__(self, required: int, found: int, data_type: str = "points", **kwargs):
        message = f"Need at least {required} {data_type}, but only found {found}"
        super().__init__(
            message,
            required=required,
            found=found,
            data_type=data_type,
            **kwargs
        )


# External API Errors
class ExternalAPIError(SocialMapperError):
    """Base class for external API errors."""

    default_message = "External API error"

    def __init__(self, message: str | None = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.ERROR,
        )
        super().__init__(message, context, **kwargs)


class CensusAPIError(ExternalAPIError):
    """Raised when Census API calls fail."""

    default_message = "Census API error"

    def __init__(self, message: str | None = None, status_code: int | None = None, **kwargs):
        super().__init__(message, status_code=status_code, **kwargs)

        if status_code == 401:
            self.add_suggestion("Check your Census API key")
        elif status_code == 429:
            self.add_suggestion("You've hit the rate limit. Wait and try again")
        elif status_code == 404:
            self.add_suggestion("The requested census data may not be available")
        else:
            self.add_suggestion("Check your internet connection")
            self.add_suggestion("Try again in a few moments")


class OSMAPIError(ExternalAPIError):
    """Raised when OpenStreetMap/Overpass API calls fail."""

    default_message = "OpenStreetMap API error"

    def __init__(self, message: str | None = None, query: str | None = None, **kwargs):
        super().__init__(message, query=query, **kwargs)
        self.add_suggestion("Check your internet connection")
        self.add_suggestion("The Overpass API may be temporarily unavailable")
        if query:
            self.add_suggestion("Verify your query syntax")


class GeocodingError(ExternalAPIError):
    """Raised when geocoding fails."""

    default_message = "Geocoding error"

    def __init__(self, location: str, service: str = "Nominatim", **kwargs):
        message = f"Failed to geocode location: '{location}'"
        super().__init__(message, location=location, service=service, **kwargs)
        self.add_suggestion("Verify the location name is correct")
        self.add_suggestion("Try a more specific location (e.g., add state/country)")


# File System Errors
class FileSystemError(SocialMapperError):
    """Raised for file system operations."""

    default_message = "File system error"

    def __init__(self, message: str | None = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.ERROR,
        )
        super().__init__(message, context, **kwargs)


class FileNotFoundError(FileSystemError):
    """Raised when required file is not found."""

    default_message = "File not found"

    def __init__(self, file_path: str, **kwargs):
        message = f"File not found: {file_path}"
        super().__init__(message, file_path=file_path, **kwargs)
        self.add_suggestion(f"Check that the file exists at: {file_path}")
        self.add_suggestion("Verify the file path is correct")


class PermissionError(FileSystemError):
    """Raised when file permissions prevent operation."""

    default_message = "Permission denied"

    def __init__(self, file_path: str, operation: str = "access", **kwargs):
        message = f"Permission denied to {operation} file: {file_path}"
        super().__init__(message, file_path=file_path, operation=operation, **kwargs)
        self.add_suggestion(f"Check file permissions for: {file_path}")
        self.add_suggestion("Run with appropriate permissions or as administrator")


# Analysis Errors
class AnalysisError(SocialMapperError):
    """Raised during analysis operations."""

    default_message = "Analysis error"

    def __init__(self, message: str | None = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.ANALYSIS,
            severity=ErrorSeverity.ERROR,
        )
        super().__init__(message, context, **kwargs)


class IsochroneGenerationError(AnalysisError):
    """Raised when isochrone generation fails."""

    default_message = "Failed to generate isochrones"

    def __init__(self, location: str | None = None, travel_mode: str | None = None, **kwargs):
        message = "Failed to generate travel time areas"
        if location:
            message += f" for {location}"
        if travel_mode:
            message += f" using {travel_mode} mode"

        super().__init__(message, location=location, travel_mode=travel_mode, **kwargs)
        self.add_suggestion("Check that the location has a road network")
        self.add_suggestion("Try a different travel mode")
        self.add_suggestion("Ensure the area is accessible by the chosen mode")


class NetworkAnalysisError(AnalysisError):
    """Raised when network analysis fails."""

    default_message = "Network analysis error"

    def __init__(self, message: str | None = None, network_type: str | None = None, **kwargs):
        super().__init__(message, network_type=network_type, **kwargs)
        self.add_suggestion("The area may not have sufficient network data")
        self.add_suggestion("Try a different location or travel mode")


# Visualization Errors
class VisualizationError(SocialMapperError):
    """Raised during visualization operations."""

    default_message = "Visualization error"

    def __init__(self, message: str | None = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.VISUALIZATION,
            severity=ErrorSeverity.WARNING,
        )
        super().__init__(message, context, **kwargs)


class MapGenerationError(VisualizationError):
    """Raised when map generation fails."""

    default_message = "Failed to generate map"

    def __init__(self, map_type: str | None = None, **kwargs):
        message = "Failed to generate map"
        if map_type:
            message += f" of type '{map_type}'"

        super().__init__(message, map_type=map_type, **kwargs)
        self.add_suggestion("Check that all required data is available")
        self.add_suggestion("Verify the output directory is writable")


# Helper functions for error handling
def handle_with_context(operation: str):
    """Decorator to add operation context to exceptions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SocialMapperError as e:
                # Add operation context if not already set
                if not e.context.operation:
                    e.context.operation = operation
                raise
            except Exception as e:
                # Wrap unexpected exceptions
                raise SocialMapperError(
                    f"Unexpected error in {operation}",
                    cause=e
                ).with_operation(operation)
        return wrapper
    return decorator


def format_error_for_user(error: Exception) -> str:
    """Format any error for user display."""
    if isinstance(error, SocialMapperError):
        return str(error)
    else:
        # Generic error formatting
        return f"An unexpected error occurred: {type(error).__name__}: {error!s}"


def format_error_for_log(error: Exception) -> dict[str, Any]:
    """Format error for structured logging."""
    if isinstance(error, SocialMapperError):
        return {
            "error_type": type(error).__name__,
            "message": error.message,
            "context": error.context.to_dict(),
            "traceback": error.get_full_traceback() if hasattr(error, 'get_full_traceback') else None,
        }
    else:
        return {
            "error_type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
