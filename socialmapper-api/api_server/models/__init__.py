"""
Pydantic models for API request and response validation.
"""

# Base models and enums
from .base import (
    JobStatusEnum,
    TravelMode,
    GeographicLevel,
    ExportFormat,
    ErrorCode,
    APIError,
    ValidationError,
    BaseResponse,
    HealthResponse
)

# Analysis models
from .analysis import (
    # Request models
    BaseAnalysisRequest,
    LocationAnalysisRequest,
    CustomPOILocation,
    CustomPOIAnalysisRequest,
    BatchAnalysisItem,
    BatchAnalysisRequest,
    AnalysisRequest,  # Backward compatibility alias
    
    # Response models
    AnalysisResponse,
    BatchAnalysisResponse,
    JobStatus,
    BatchJobStatus,
    AnalysisResult,
    
    # Export models
    ExportRequest,
    ExportResponse,
    
    # Metadata models
    CensusVariable,
    CensusVariablesResponse,
    POIType,
    POITypesResponse,
    LocationSearchResult,
    LocationSearchResponse,
    
    # Internal models
    ProcessingJob
)

# Error models
from .errors import (
    ValidationErrorDetail,
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
    ErrorResponse
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