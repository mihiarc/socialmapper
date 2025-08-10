"""Pydantic models for API request and response validation."""

# Base models and enums
# Analysis models
from .analysis import (
    AnalysisRequest,  # Backward compatibility alias
    # Response models
    AnalysisResponse,
    AnalysisResult,
    # Request models
    BaseAnalysisRequest,
    BatchAnalysisItem,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchJobStatus,
    # Metadata models
    CensusVariable,
    CensusVariablesResponse,
    CustomPOIAnalysisRequest,
    CustomPOILocation,
    # Export models
    ExportRequest,
    ExportResponse,
    JobStatus,
    LocationAnalysisRequest,
    LocationSearchResponse,
    LocationSearchResult,
    POIType,
    POITypesResponse,
    # Internal models
    ProcessingJob,
)
from .base import (
    APIError,
    BaseResponse,
    ErrorCode,
    ExportFormat,
    GeographicLevel,
    HealthResponse,
    JobStatusEnum,
    TravelMode,
    ValidationError,
)

# Error models
from .errors import (
    AuthenticationError,
    AuthorizationError,
    DetailedValidationError,
    ErrorResponse,
    InternalServerError,
    InvalidRequestError,
    ProcessingError,
    RateLimitError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationErrorDetail,
)

__all__ = [
    "APIError",
    "AnalysisRequest",
    # Analysis models - Responses
    "AnalysisResponse",
    "AnalysisResult",
    "AuthenticationError",
    "AuthorizationError",
    # Analysis models - Requests
    "BaseAnalysisRequest",
    "BaseResponse",
    "BatchAnalysisItem",
    "BatchAnalysisRequest",
    "BatchAnalysisResponse",
    "BatchJobStatus",
    # Metadata models
    "CensusVariable",
    "CensusVariablesResponse",
    "CustomPOIAnalysisRequest",
    "CustomPOILocation",
    "DetailedValidationError",
    "ErrorCode",
    "ErrorResponse",
    "ExportFormat",
    # Export models
    "ExportRequest",
    "ExportResponse",
    "GeographicLevel",
    "HealthResponse",
    "InternalServerError",
    "InvalidRequestError",
    "JobStatus",
    # Base models and enums
    "JobStatusEnum",
    "LocationAnalysisRequest",
    "LocationSearchResponse",
    "LocationSearchResult",
    "POIType",
    "POITypesResponse",
    "ProcessingError",
    # Internal models
    "ProcessingJob",
    "RateLimitError",
    "ResourceNotFoundError",
    "ServiceUnavailableError",
    "TimeoutError",
    "TravelMode",
    "ValidationError",
    # Error models
    "ValidationErrorDetail",
]
