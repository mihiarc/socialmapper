"""Error handling utilities and context managers.

Provides utilities for consistent error handling across the codebase.
"""

from __future__ import annotations

import functools
import logging
import sys
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar

from ..exceptions import (
    ErrorContext,
    ErrorSeverity,
    SocialMapperError,
    format_error_for_log,
    format_error_for_user,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


@contextmanager
def error_context(operation: str, **context_kwargs):
    """Context manager that adds context to any errors raised within.
    
    Example:
        ```python
        with error_context("Loading census data", location="San Francisco"):
            # Any errors here will have context added
            data = load_census_data()
        ```
    """
    try:
        yield
    except SocialMapperError as e:
        # Enhance existing SocialMapper errors
        if not e.context.operation:
            e.context.operation = operation
        e.context.details.update(context_kwargs)
        raise
    except Exception as e:
        # Wrap other exceptions
        raise SocialMapperError(
            f"Error during {operation}",
            cause=e,
            operation=operation,
            **context_kwargs
        ) from e


@contextmanager
def suppress_and_log(
    *exceptions: type[Exception],
    severity: ErrorSeverity = ErrorSeverity.WARNING,
    fallback: Any = None,
):
    """Context manager that suppresses exceptions and logs them.
    
    Example:
        ```python
        with suppress_and_log(ValueError, KeyError) as handler:
            result = risky_operation()
        
        if handler.error_occurred:
            result = handler.fallback
        ```
    """
    class Handler:
        def __init__(self):
            self.error_occurred = False
            self.error = None
            self.fallback = fallback
    
    handler = Handler()
    
    try:
        yield handler
    except exceptions as e:
        handler.error_occurred = True
        handler.error = e
        
        # Log the error
        log_error(e, severity)
        
        # Don't re-raise


def with_retries(
    max_attempts: int = 3,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    delay: float = 1.0,
    backoff: float = 2.0,
    on_retry: Callable[[Exception, int], None] | None = None,
):
    """Decorator that retries function on specific exceptions.
    
    Example:
        ```python
        @with_retries(max_attempts=3, exceptions=(NetworkError,))
        def fetch_data():
            return api.get_data()
        ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            import time
            
            last_error = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    
                    if attempt < max_attempts - 1:
                        if on_retry:
                            on_retry(e, attempt + 1)
                        else:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                                f"Retrying in {current_delay:.1f}s..."
                            )
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        # Last attempt failed
                        logger.error(f"All {max_attempts} attempts failed")
                        raise
            
            # Should never reach here, but just in case
            if last_error:
                raise last_error
            else:
                raise RuntimeError("Unexpected retry logic error")
        
        return wrapper
    return decorator


def with_fallback(fallback_value: T, *exceptions: type[Exception]) -> Callable:
    """Decorator that returns fallback value on exception.
    
    Example:
        ```python
        @with_fallback([], ValueError, KeyError)
        def get_items():
            return parse_items(data)
        ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions:
                logger.warning(
                    f"{func.__name__} failed, returning fallback value",
                    exc_info=True
                )
                return fallback_value
        return wrapper
    return decorator


def log_error(
    error: Exception,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    **extra_context
):
    """Log an error with appropriate formatting and context."""
    error_data = format_error_for_log(error)
    error_data.update(extra_context)
    
    # Map severity to log level
    log_level = {
        ErrorSeverity.INFO: logging.INFO,
        ErrorSeverity.WARNING: logging.WARNING,
        ErrorSeverity.ERROR: logging.ERROR,
        ErrorSeverity.CRITICAL: logging.CRITICAL,
    }.get(severity, logging.ERROR)
    
    logger.log(
        log_level,
        format_error_for_user(error),
        extra={"error_data": error_data}
    )


def handle_error(
    error: Exception,
    exit_code: int = 1,
    show_traceback: bool = False,
):
    """Handle an error appropriately for CLI usage.
    
    Args:
        error: The exception to handle
        exit_code: Exit code to use if exiting
        show_traceback: Whether to show full traceback
    """
    # Log the error
    log_error(error, ErrorSeverity.ERROR)
    
    # Display to user
    user_message = format_error_for_user(error)
    print(f"\n❌ {user_message}", file=sys.stderr)
    
    if show_traceback:
        print("\nFull traceback:", file=sys.stderr)
        if isinstance(error, SocialMapperError) and hasattr(error, 'get_full_traceback'):
            print(error.get_full_traceback(), file=sys.stderr)
        else:
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    sys.exit(exit_code)


class ErrorCollector:
    """Collects errors during batch operations.
    
    Example:
        ```python
        collector = ErrorCollector()
        
        for item in items:
            with collector.collect(item):
                process_item(item)
        
        if collector.has_errors:
            print(f"Failed to process {len(collector.errors)} items")
            for ctx, error in collector.errors:
                print(f"  - {ctx}: {error}")
        ```
    """
    
    def __init__(self):
        self.errors: list[tuple[Any, Exception]] = []
        self.warnings: list[tuple[Any, Exception]] = []
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    @contextmanager
    def collect(self, context: Any = None):
        """Collect errors for a specific context."""
        try:
            yield
        except Exception as e:
            if isinstance(e, SocialMapperError) and e.context.severity == ErrorSeverity.WARNING:
                self.warnings.append((context, e))
            else:
                self.errors.append((context, e))
            # Don't re-raise - continue processing
    
    def raise_if_errors(self, message: str = "Multiple errors occurred"):
        """Raise an exception if any errors were collected."""
        if self.has_errors:
            error_details = []
            for ctx, error in self.errors:
                if ctx:
                    error_details.append(f"{ctx}: {error}")
                else:
                    error_details.append(str(error))
            
            raise SocialMapperError(
                message,
                error_count=len(self.errors),
                errors=error_details
            )
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of collected errors."""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "errors": [
                {
                    "context": str(ctx) if ctx else None,
                    "error": format_error_for_log(error)
                }
                for ctx, error in self.errors
            ],
            "warnings": [
                {
                    "context": str(ctx) if ctx else None,
                    "warning": format_error_for_log(warning)
                }
                for ctx, warning in self.warnings
            ],
        }


def validate_type(
    value: Any,
    expected_type: type | tuple[type, ...],
    name: str,
    allow_none: bool = False,
) -> None:
    """Validate that a value is of the expected type.
    
    Raises:
        TypeError: If type doesn't match
    """
    if allow_none and value is None:
        return
    
    if not isinstance(value, expected_type):
        expected_str = (
            " or ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )
        
        actual_type = type(value).__name__
        
        raise TypeError(
            f"{name} must be {expected_str}, got {actual_type}"
        )


def validate_range(
    value: int | float,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    name: str = "value",
) -> None:
    """Validate that a numeric value is within range.
    
    Raises:
        ValueError: If value is out of range
    """
    if min_value is not None and value < min_value:
        raise ValueError(
            f"{name} must be at least {min_value}, got {value}"
        )
    
    if max_value is not None and value > max_value:
        raise ValueError(
            f"{name} must be at most {max_value}, got {value}"
        )


def chain_errors(*errors: Exception | None) -> Exception | None:
    """Chain multiple errors together.
    
    Returns the first error with others chained as causes.
    """
    filtered_errors = [e for e in errors if e is not None]
    
    if not filtered_errors:
        return None
    
    if len(filtered_errors) == 1:
        return filtered_errors[0]
    
    # Chain errors together
    first_error = filtered_errors[0]
    current = first_error
    
    for error in filtered_errors[1:]:
        current.__cause__ = error
        current = error
    
    return first_error