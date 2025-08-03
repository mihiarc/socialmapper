"""Error handling middleware for the SocialMapper API.

This middleware provides centralized error handling, logging, and
standardized error responses for all API endpoints.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..models.errors import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    DetailedValidationError,
    ErrorCode,
    InternalServerError,
    InvalidRequestError,
    ProcessingError,
    RateLimitError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationErrorDetail,
)

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Custom API exception with structured error response."""

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware.
    
    This middleware catches all exceptions and returns standardized
    error responses. It also logs errors appropriately.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await handle_exception(request, exc)


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle exceptions and return appropriate error responses.
    
    Args:
        request: The incoming request
        exc: The exception that was raised
        
    Returns:
        JSONResponse with standardized error format
    """
    # Generate incident ID for tracking
    incident_id = str(uuid.uuid4())

    # Log the error with context
    logger.error(
        f"Error handling request {request.method} {request.url.path}",
        extra={
            "incident_id": incident_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
            "exception_type": type(exc).__name__,
            "exception": str(exc)
        },
        exc_info=True
    )

    # Handle different exception types
    if isinstance(exc, APIException):
        return create_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            incident_id=incident_id
        )

    elif isinstance(exc, RequestValidationError):
        # Handle FastAPI validation errors
        field_errors = []
        for error in exc.errors():
            field_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Validation error",
            details={"field_errors": field_errors},
            incident_id=incident_id
        )

    elif isinstance(exc, HTTPException):
        # Handle FastAPI HTTPException
        error_code = ErrorCode.INTERNAL_ERROR
        if exc.status_code == 404:
            error_code = ErrorCode.RESOURCE_NOT_FOUND
        elif exc.status_code == 405:
            error_code = ErrorCode.METHOD_NOT_ALLOWED
        elif exc.status_code == 401:
            error_code = ErrorCode.AUTHENTICATION_ERROR
        elif exc.status_code == 403:
            error_code = ErrorCode.AUTHORIZATION_ERROR
        elif exc.status_code == 429:
            error_code = ErrorCode.RATE_LIMIT_EXCEEDED
        elif exc.status_code == 503:
            error_code = ErrorCode.SERVICE_UNAVAILABLE

        return create_error_response(
            status_code=exc.status_code,
            error_code=error_code,
            message=exc.detail,
            details={},
            incident_id=incident_id
        )

    elif isinstance(exc, StarletteHTTPException):
        # Handle Starlette HTTPException (similar to above)
        error_code = ErrorCode.INTERNAL_ERROR
        if exc.status_code == 404:
            error_code = ErrorCode.RESOURCE_NOT_FOUND
        elif exc.status_code == 405:
            error_code = ErrorCode.METHOD_NOT_ALLOWED

        return create_error_response(
            status_code=exc.status_code,
            error_code=error_code,
            message=exc.detail or "HTTP Error",
            details={},
            incident_id=incident_id
        )

    elif isinstance(exc, ValidationError):
        # Handle Pydantic validation errors
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Validation error",
            details={"errors": exc.errors()},
            incident_id=incident_id
        )

    elif isinstance(exc, TimeoutError):
        return create_error_response(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            error_code=ErrorCode.TIMEOUT_ERROR,
            message="Request timeout",
            details={"operation": str(exc)},
            incident_id=incident_id
        )

    elif isinstance(exc, ConnectionError):
        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Service temporarily unavailable",
            details={"reason": "Connection error"},
            incident_id=incident_id
        )

    else:
        # Generic internal server error
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            details={},
            incident_id=incident_id
        )


def handle_validation_error(exc: RequestValidationError, incident_id: str) -> JSONResponse:
    """Handle request validation errors."""
    field_errors = []

    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        field_errors.append(
            ValidationErrorDetail(
                field=field_path,
                message=error["msg"],
                invalid_value=error.get("input"),
                constraint=error.get("type")
            )
        )

    error_response = DetailedValidationError(
        message="Validation error in request",
        details={"request_errors": exc.errors()},
        timestamp=datetime.now(UTC),
        field_errors=field_errors
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


def handle_http_exception(exc: HTTPException, incident_id: str) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    error_code_map = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.AUTHENTICATION_ERROR,
        403: ErrorCode.AUTHORIZATION_ERROR,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
        504: ErrorCode.TIMEOUT_ERROR
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    # Handle detail that might be a dict
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", str(exc.detail))
        details = exc.detail
    else:
        message = str(exc.detail)
        details = {}

    return create_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
        details=details,
        incident_id=incident_id
    )


def handle_starlette_http_exception(exc: StarletteHTTPException, incident_id: str) -> JSONResponse:
    """Handle Starlette HTTP exceptions."""
    return handle_http_exception(
        HTTPException(status_code=exc.status_code, detail=exc.detail),
        incident_id
    )


def handle_pydantic_validation_error(exc: ValidationError, incident_id: str) -> JSONResponse:
    """Handle Pydantic validation errors."""
    field_errors = []

    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        field_errors.append(
            ValidationErrorDetail(
                field=field_path,
                message=error["msg"],
                invalid_value=error.get("input"),
                constraint=error.get("type")
            )
        )

    error_response = DetailedValidationError(
        message="Data validation error",
        details={"validation_errors": exc.errors()},
        timestamp=datetime.now(UTC),
        field_errors=field_errors
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


def create_error_response(
    status_code: int,
    error_code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
    incident_id: str | None = None
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Additional error details
        incident_id: Incident ID for tracking
        
    Returns:
        JSONResponse with error details
    """
    # Select appropriate error model based on error code
    error_class_map = {
        ErrorCode.VALIDATION_ERROR: DetailedValidationError,
        ErrorCode.RESOURCE_NOT_FOUND: ResourceNotFoundError,
        ErrorCode.PROCESSING_ERROR: ProcessingError,
        ErrorCode.RATE_LIMIT_EXCEEDED: RateLimitError,
        ErrorCode.AUTHENTICATION_ERROR: AuthenticationError,
        ErrorCode.AUTHORIZATION_ERROR: AuthorizationError,
        ErrorCode.SERVICE_UNAVAILABLE: ServiceUnavailableError,
        ErrorCode.TIMEOUT_ERROR: TimeoutError,
        ErrorCode.INVALID_REQUEST: InvalidRequestError,
        ErrorCode.INTERNAL_ERROR: InternalServerError
    }

    error_class = error_class_map.get(error_code, APIError)

    # Build error response
    error_data = {
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.now(UTC),
        "details": details or {}
    }

    # Add incident ID for internal errors
    if error_code == ErrorCode.INTERNAL_ERROR and incident_id:
        error_data["incident_id"] = incident_id

    # Create error instance
    if error_class == APIError:
        error_response = error_class(**error_data)
    else:
        # For specific error types, add type-specific fields
        if error_code == ErrorCode.RESOURCE_NOT_FOUND:
            error_data["resource_type"] = details.get("resource_type", "unknown")
            error_data["resource_id"] = details.get("resource_id")
        elif error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
            error_data["limit"] = details.get("limit", 60)
            error_data["window_seconds"] = details.get("window_seconds", 60)
            error_data["retry_after_seconds"] = details.get("retry_after_seconds", 30)
            error_data["remaining_requests"] = details.get("remaining_requests", 0)

        try:
            error_response = error_class(**error_data)
        except:
            # Fallback to generic error if specific model fails
            error_response = APIError(**error_data)

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode='json'),
        headers={
            "X-Incident-ID": incident_id or "",
            "X-Error-Code": error_code
        }
    )


def setup_error_handling(app):
    """Set up error handling for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add middleware
    app.middleware("http")(error_handling_middleware)

    # Add exception handlers
    app.add_exception_handler(RequestValidationError, handle_exception)
    app.add_exception_handler(HTTPException, handle_exception)
    app.add_exception_handler(StarletteHTTPException, handle_exception)
    app.add_exception_handler(ValidationError, handle_exception)
    app.add_exception_handler(Exception, handle_exception)

    logger.info("Error handling middleware configured")
