"""Pydantic models for API request and response validation.
"""

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
    # Base models and enums
    "JobStatusEnum",
    "TravelMode",
    "GeographicLevel",
    "ExportFormat",
    "ErrorCode",
    "APIError",
    "ValidationError",
    "BaseResponse",
    "HealthResponse",

    # Analysis models - Requests
    "BaseAnalysisRequest",
    "LocationAnalysisRequest",
    "CustomPOILocation",
    "CustomPOIAnalysisRequest",
    "BatchAnalysisItem",
    "BatchAnalysisRequest",
    "AnalysisRequest",

    # Analysis models - Responses
    "AnalysisResponse",
    "BatchAnalysisResponse",
    "JobStatus",
    "BatchJobStatus",
    "AnalysisResult",

    # Export models
    "ExportRequest",
    "ExportResponse",

    # Metadata models
    "CensusVariable",
    "CensusVariablesResponse",
    "POIType",
    "POITypesResponse",
    "LocationSearchResult",
    "LocationSearchResponse",

    # Internal models
    "ProcessingJob",

    # Error models
    "ValidationErrorDetail",
    "DetailedValidationError",
    "ResourceNotFoundError",
    "ProcessingError",
    "RateLimitError",
    "AuthenticationError",
    "AuthorizationError",
    "InternalServerError",
    "ServiceUnavailableError",
    "TimeoutError",
    "InvalidRequestError",
    "ErrorResponse"
]
