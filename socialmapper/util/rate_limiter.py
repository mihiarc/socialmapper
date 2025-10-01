"""Simple retry logic for external API services.

Provides exponential backoff retry functionality for handling transient errors
when interacting with external APIs.
"""

import random
import time
from functools import wraps

import httpx


class RetryHandler:
    """Handles retrying failed API requests with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
    ):
        """Initialize the retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Factor to increase delay by after each failure
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def calculate_delay(self, attempt: int) -> float:
        """Calculate the delay before the next retry attempt.

        Args:
            attempt: The current attempt number (0-based)

        Returns:
            The delay in seconds
        """
        # Calculate exponential backoff with jitter
        delay = min(self.max_delay, self.base_delay * (self.backoff_factor**attempt))
        # Add up to 15% random jitter to avoid thundering herd
        delay = delay * (1 + random.uniform(-0.15, 0.15))
        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if a retry should be attempted.

        Args:
            exception: The exception that occurred
            attempt: The current attempt number (0-based)

        Returns:
            True if a retry should be attempted, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        # Network errors and timeouts should be retried
        if isinstance(exception, (httpx.NetworkError, httpx.TimeoutException)):
            return True

        # Rate limiting (429) and server errors (5xx) should be retried
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code == 429 or (500 <= status_code < 600)

        return False


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retry_exceptions: list[type[Exception]] | None = None,
    service: str | None = None,  # Kept for backward compatibility, not used
):
    """Decorator that implements retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor to increase delay by after each failure
        retry_exceptions: List of exception types to retry on
        service: (Deprecated) Service name - kept for backward compatibility

    Returns:
        A decorator function
    """
    if retry_exceptions is None:
        retry_exceptions = [httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError]

    retry_handler = RetryHandler(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
    )

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0

            while True:
                try:
                    return func(*args, **kwargs)

                except tuple(retry_exceptions) as e:
                    attempt += 1

                    if not retry_handler.should_retry(e, attempt - 1):
                        raise

                    delay = retry_handler.calculate_delay(attempt - 1)
                    time.sleep(delay)

        return wrapper

    return decorator
