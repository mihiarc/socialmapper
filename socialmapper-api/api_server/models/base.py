"""Base models and common types for the SocialMapper API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class JobStatusEnum(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TravelMode(str, Enum):
    """Travel mode enumeration."""
    WALK = "walk"
    BIKE = "bike"
    DRIVE = "drive"


class GeographicLevel(str, Enum):
    """Geographic analysis level enumeration."""
    BLOCK_GROUP = "block_group"
    ZCTA = "zcta"


class ExportFormat(str, Enum):
    """Export format enumeration."""
    CSV = "csv"
    GEOJSON = "geojson"
    PARQUET = "parquet"
    GEOPARQUET = "geoparquet"


class ErrorCode(str, Enum):
    """Standard error codes."""
    VALIDATION_ERROR = "validation_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PROCESSING_ERROR = "processing_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT_ERROR = "timeout_error"
    INVALID_REQUEST = "invalid_request"


class APIError(BaseModel):
    """Standard API error response model."""
    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: str | None = Field(None, description="Request identifier for tracking")

    @validator('message')
    def validate_message(cls, v):
        """Ensure error message is not empty."""
        if not v or not v.strip():
            raise ValueError("Error message cannot be empty")
        return v.strip()


class ValidationError(APIError):
    """Validation error response model."""
    error_code: Literal[ErrorCode.VALIDATION_ERROR] = Field(ErrorCode.VALIDATION_ERROR, description="Machine-readable error code")
    field_errors: list[dict[str, str]] | None = Field(
        None,
        description="Field-specific validation errors"
    )


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: str | None = Field(None, description="Request identifier for tracking")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthResponse(BaseResponse):
    """Health check response model."""
    status: str = Field("healthy", description="Service health status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    dependencies: dict[str, str] | None = Field(
        None,
        description="Status of external dependencies"
    )
