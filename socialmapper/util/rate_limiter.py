"""
Rate limiting and retry logic for external API services.

This module provides utilities for managing rate limits and implementing
retry logic when interacting with external APIs like OpenStreetMaps and Census API.
"""

import time
import random
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union, List
import httpx

# Configure logger
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter for API calls to ensure we don't exceed allowed request limits.
    
    Maintains a record of requests per service and enforces minimum time
    between requests.
    """
    
    def __init__(self):
        # Default rate limits per service (requests per second)
        self.rate_limits = {
            "openstreetmap": 1,    # OSM allows ~1 req/sec for anonymous users
            "census": 5,           # Census API is more permissive
            "default": 1,          # Default fallback rate
        }
        
        # Timestamps of last requests
        self.last_request_time: Dict[str, float] = {}
    
    def wait_if_needed(self, service: str = "default") -> None:
        """
        Wait if necessary to comply with the rate limit for the specified service.
        
        Args:
            service: The service identifier (e.g., "openstreetmap", "census")
        """
        # Get the rate limit for the service (or use default)
        requests_per_second = self.rate_limits.get(service, self.rate_limits["default"])
        min_interval = 1.0 / requests_per_second
        
        # Check if we need to wait
        current_time = time.time()
        if service in self.last_request_time:
            elapsed = current_time - self.last_request_time[service]
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                # Add a small random jitter to avoid synchronization
                wait_time += random.uniform(0.05, 0.15)
                logger.debug(f"Rate limiting {service}: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        
        # Update the last request time
        self.last_request_time[service] = time.time()
    
    def update_rate_limit(self, service: str, requests_per_second: float) -> None:
        """
        Update the rate limit for a specific service.
        
        Args:
            service: The service identifier
            requests_per_second: Maximum number of requests per second
        """
        self.rate_limits[service] = requests_per_second


# Create a global instance for use throughout the application
rate_limiter = RateLimiter()


def rate_limited(service: str = "default"):
    """
    Decorator to apply rate limiting to a function.
    
    Args:
        service: The service identifier to apply rate limiting for
        
    Returns:
        A decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter.wait_if_needed(service)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class RetryHandler:
    """
    Handles retrying failed API requests with exponential backoff.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize the retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Factor to increase delay by after each failure
            jitter: Whether to add randomness to the delay
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay before the next retry attempt.
        
        Args:
            attempt: The current attempt number (0-based)
            
        Returns:
            The delay in seconds
        """
        # Calculate exponential backoff
        delay = min(self.max_delay, self.base_delay * (self.backoff_factor ** attempt))
        
        # Add jitter to avoid thundering herd problem
        if self.jitter:
            # Add up to 15% random jitter
            delay = delay * (1 + random.uniform(-0.15, 0.15))
        
        return delay
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if a retry should be attempted based on the exception and attempt count.
        
        Args:
            exception: The exception that occurred
            attempt: The current attempt number (0-based)
            
        Returns:
            True if a retry should be attempted, False otherwise
        """
        # Always respect max_retries
        if attempt >= self.max_retries:
            return False
        
        # Network errors should be retried
        if isinstance(exception, (httpx.NetworkError, httpx.TimeoutException)):
            return True
        
        # Rate limiting (429) and server errors (5xx) should be retried
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code == 429 or (500 <= status_code < 600)
        
        # Other exceptions can be handled on a case-by-case basis
        # For now, we'll return False for any other exceptions
        return False


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retry_exceptions: Optional[List[Type[Exception]]] = None,
    service: Optional[str] = None
):
    """
    Decorator that implements retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor to increase delay by after each failure
        retry_exceptions: List of exception types to retry on
        service: Optional service name for rate limiting
        
    Returns:
        A decorator function
    """
    if retry_exceptions is None:
        # Default exceptions to retry on
        retry_exceptions = [
            httpx.NetworkError,
            httpx.TimeoutException,
            httpx.HTTPStatusError
        ]
    
    retry_handler = RetryHandler(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor
    )
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            
            while True:
                try:
                    # Apply rate limiting if service is specified
                    if service:
                        rate_limiter.wait_if_needed(service)
                    
                    # Call the original function
                    return func(*args, **kwargs)
                
                except tuple(retry_exceptions) as e:
                    attempt += 1
                    
                    # Check if we should retry
                    if not retry_handler.should_retry(e, attempt - 1):
                        logger.warning(f"Max retries ({max_retries}) exceeded or non-retryable error")
                        raise
                    
                    # Calculate delay for next attempt
                    delay = retry_handler.calculate_delay(attempt - 1)
                    
                    # Log the retry attempt
                    logger.info(
                        f"Request failed with {e.__class__.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f}s (attempt {attempt}/{max_retries})"
                    )
                    
                    # Wait before retrying
                    time.sleep(delay)
        
        return wrapper
    
    return decorator


# HTTP Client with built-in retry and rate limiting
class RateLimitedClient:
    """
    HTTP client with built-in rate limiting and retry logic.
    
    Wraps httpx.Client to provide automatic rate limiting and retry functionality
    for API requests.
    """
    
    def __init__(
        self,
        service: str = "default",
        max_retries: int = 3,
        timeout: float = 30.0,
        **client_kwargs
    ):
        """
        Initialize the rate-limited client.
        
        Args:
            service: Service identifier for rate limiting
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            **client_kwargs: Additional arguments to pass to httpx.Client
        """
        self.service = service
        self.max_retries = max_retries
        self.retry_handler = RetryHandler(max_retries=max_retries)
        self.client = httpx.Client(timeout=timeout, **client_kwargs)
    
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make an HTTP request with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments to pass to httpx.Client.request
            
        Returns:
            The HTTP response
            
        Raises:
            httpx.HTTPError: If the request ultimately fails after retries
        """
        attempt = 0
        
        while True:
            try:
                # Apply rate limiting
                rate_limiter.wait_if_needed(self.service)
                
                # Make the request
                return self.client.request(method, url, **kwargs)
            
            except (httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                attempt += 1
                
                # Check if we should retry
                if not self.retry_handler.should_retry(e, attempt - 1):
                    logger.warning(f"Max retries ({self.max_retries}) exceeded or non-retryable error")
                    raise
                
                # Calculate delay for next attempt
                delay = self.retry_handler.calculate_delay(attempt - 1)
                
                # Log the retry attempt
                logger.info(
                    f"Request to {url} failed with {e.__class__.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f}s (attempt {attempt}/{self.max_retries})"
                )
                
                # Wait before retrying
                time.sleep(delay)
    
    def get(self, url: str, **kwargs) -> httpx.Response:
        """Convenience method for making GET requests."""
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> httpx.Response:
        """Convenience method for making POST requests."""
        return self.request("POST", url, **kwargs)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
    
    def close(self):
        """Close the underlying HTTP client."""
        self.client.close()


# Async version of the HTTP client
class AsyncRateLimitedClient:
    """
    Asynchronous HTTP client with built-in rate limiting and retry logic.
    
    Wraps httpx.AsyncClient to provide automatic rate limiting and retry functionality
    for API requests.
    """
    
    def __init__(
        self,
        service: str = "default",
        max_retries: int = 3,
        timeout: float = 30.0,
        **client_kwargs
    ):
        """
        Initialize the async rate-limited client.
        
        Args:
            service: Service identifier for rate limiting
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            **client_kwargs: Additional arguments to pass to httpx.AsyncClient
        """
        self.service = service
        self.max_retries = max_retries
        self.retry_handler = RetryHandler(max_retries=max_retries)
        self.client = httpx.AsyncClient(timeout=timeout, **client_kwargs)
    
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make an asynchronous HTTP request with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments to pass to httpx.AsyncClient.request
            
        Returns:
            The HTTP response
            
        Raises:
            httpx.HTTPError: If the request ultimately fails after retries
        """
        attempt = 0
        
        while True:
            try:
                # Apply rate limiting
                rate_limiter.wait_if_needed(self.service)
                
                # Make the request
                return await self.client.request(method, url, **kwargs)
            
            except (httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                attempt += 1
                
                # Check if we should retry
                if not self.retry_handler.should_retry(e, attempt - 1):
                    logger.warning(f"Max retries ({self.max_retries}) exceeded or non-retryable error")
                    raise
                
                # Calculate delay for next attempt
                delay = self.retry_handler.calculate_delay(attempt - 1)
                
                # Log the retry attempt
                logger.info(
                    f"Request to {url} failed with {e.__class__.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f}s (attempt {attempt}/{self.max_retries})"
                )
                
                # Wait before retrying
                time.sleep(delay)
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Convenience method for making asynchronous GET requests."""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Convenience method for making asynchronous POST requests."""
        return await self.request("POST", url, **kwargs)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()
    
    async def aclose(self):
        """Close the underlying async HTTP client."""
        await self.client.aclose() 