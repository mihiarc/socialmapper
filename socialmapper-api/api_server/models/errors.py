"""Error response models for the SocialMapper API.
"""

from datetime import datetime
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, validator

from .base import APIError, ErrorCode


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Any | None = Field(None, description="The invalid value that was provided")
    constraint: str | None = Field(None, description="Validation constraint that was violated")

    @validator('field')
    def validate_field(cls, v):
        """Validate field name."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Field name cannot be empty")
        return v.strip()

    @validator('message')
    def validate_message(cls, v):
        """Validate error message."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Error message cannot be empty")
        return v.strip()


class DetailedValidationError(APIError):
    """Detailed validation error response."""
    error_code: Literal[ErrorCode.VALIDATION_ERROR] = Field(ErrorCode.VALIDATION_ERROR, description="Machine-readable error code")
    field_errors: list[ValidationErrorDetail] = Field(
        ...,
        description="Detailed field validation errors"
    )

    @validator('field_errors')
    def validate_field_errors(cls, v):
        """Validate field errors list."""
        if not v:
            raise ValueError("At least one field error must be provided")
        return v


class ResourceNotFoundError(APIError):
    """Resource not found error response."""
    error_code: Literal[ErrorCode.RESOURCE_NOT_FOUND] = Field(ErrorCode.RESOURCE_NOT_FOUND, description="Machine-readable error code")
    resource_type: str = Field(..., description="Type of resource that was not found")
    resource_id: str | None = Field(None, description="ID of the resource that was not found")

    @validator('resource_type')
    def validate_resource_type(cls, v):
        """Validate resource type."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Resource type cannot be empty")
        return v.strip()


class ProcessingError(APIError):
    """Processing error response."""
    error_code: Literal[ErrorCode.PROCESSING_ERROR] = Field(ErrorCode.PROCESSING_ERROR, description="Machine-readable error code")
    stage: str | None = Field(None, description="Processing stage where error occurred")
    retry_after_seconds: int | None = Field(None, description="Suggested retry delay in seconds")

    @validator('stage')
    def validate_stage(cls, v):
        """Validate processing stage."""
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Processing stage cannot be empty string")
        return v.strip() if v else None


class RateLimitError(APIError):
    """Rate limit exceeded error response."""
    error_code: Literal[ErrorCode.RATE_LIMIT_EXCEEDED] = Field(ErrorCode.RATE_LIMIT_EXCEEDED, description="Machine-readable error code")
    limit: int = Field(..., description="Rate limit that was exceeded")
    window_seconds: int = Field(..., description="Rate limit window in seconds")
    retry_after_seconds: int = Field(..., description="Seconds to wait before retrying")
    remaining_requests: int = Field(0, description="Remaining requests in current window")

    @validator('limit')
    def validate_limit(cls, v):
        """Validate rate limit."""
        if v <= 0:
            raise ValueError("Rate limit must be positive")
        return v

    @validator('window_seconds')
    def validate_window_seconds(cls, v):
        """Validate window seconds."""
        if v <= 0:
            raise ValueError("Window seconds must be positive")
        return v

    @validator('retry_after_seconds')
    def validate_retry_after_seconds(cls, v):
        """Validate retry after seconds."""
        if v < 0:
            raise ValueError("Retry after seconds cannot be negative")
        return v


class AuthenticationError(APIError):
    """Authentication error response."""
    error_code: Literal[ErrorCode.AUTHENTICATION_ERROR] = Field(ErrorCode.AUTHENTICATION_ERROR, description="Machine-readable error code")
    auth_method: str | None = Field(None, description="Expected authentication method")

    @validator('auth_method')
    def validate_auth_method(cls, v):
        """Validate authentication method."""
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Authentication method cannot be empty string")
        return v.strip() if v else None


class AuthorizationError(APIError):
    """Authorization error response."""
    error_code: Literal[ErrorCode.AUTHORIZATION_ERROR] = Field(ErrorCode.AUTHORIZATION_ERROR, description="Machine-readable error code")
    required_permission: str | None = Field(None, description="Required permission")

    @validator('required_permission')
    def validate_required_permission(cls, v):
        """Validate required permission."""
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Required permission cannot be empty string")
        return v.strip() if v else None


class InternalServerError(APIError):
    """Internal server error response."""
    error_code: Literal[ErrorCode.INTERNAL_ERROR] = Field(ErrorCode.INTERNAL_ERROR, description="Machine-readable error code")
    incident_id: str | None = Field(None, description="Incident ID for tracking")

    @validator('incident_id')
    def validate_incident_id(cls, v):
        """Validate incident ID."""
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Incident ID cannot be empty string")
        return v.strip() if v else None


class ServiceUnavailableError(APIError):
    """Service unavailable error response."""
    error_code: Literal[ErrorCode.SERVICE_UNAVAILABLE] = Field(ErrorCode.SERVICE_UNAVAILABLE, description="Machine-readable error code")
    retry_after_seconds: int | None = Field(None, description="Suggested retry delay in seconds")
    maintenance_window: dict[str, datetime] | None = Field(
        None,
        description="Maintenance window information"
    )

    @validator('retry_after_seconds')
    def validate_retry_after_seconds(cls, v):
        """Validate retry after seconds."""
        if v is not None and v < 0:
            raise ValueError("Retry after seconds cannot be negative")
        return v


class TimeoutError(APIError):
    """Timeout error response."""
    error_code: Literal[ErrorCode.TIMEOUT_ERROR] = Field(ErrorCode.TIMEOUT_ERROR, description="Machine-readable error code")
    timeout_seconds: float = Field(..., description="Timeout duration in seconds")
    operation: str | None = Field(None, description="Operation that timed out")

    @validator('timeout_seconds')
    def validate_timeout_seconds(cls, v):
        """Validate timeout seconds."""
        if v <= 0:
            raise ValueError("Timeout seconds must be positive")
        return v

    @validator('operation')
    def validate_operation(cls, v):
        """Validate operation."""
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Operation cannot be empty string")
        return v.strip() if v else None


class InvalidRequestError(APIError):
    """Invalid request error response."""
    error_code: Literal[ErrorCode.INVALID_REQUEST] = Field(ErrorCode.INVALID_REQUEST, description="Machine-readable error code")
    suggestion: str | None = Field(None, description="Suggestion for fixing the request")

    @validator('suggestion')
    def validate_suggestion(cls, v):
        """Validate suggestion."""
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Suggestion cannot be empty string")
        return v.strip() if v else None


# Union type for all possible error responses
ErrorResponse = Union[
    DetailedValidationError,
    ResourceNotFoundError,
    ProcessingError,
    RateLimitError,
    AuthenticationError,
    AuthorizationError,
    InternalServerError,
    ServiceUnavailableError,
    TimeoutError,
    InvalidRequestError,
    APIError  # Fallback for generic errors
]
