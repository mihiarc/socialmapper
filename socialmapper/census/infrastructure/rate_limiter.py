"""
Rate limiting implementations for API calls.

Provides token bucket algorithm for smooth rate limiting that respects
Census Bureau API limits while allowing burst traffic when possible.
"""

import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TokenBucket:
    """
    Token bucket for rate limiting.
    
    Implements the token bucket algorithm which allows for burst traffic
    up to the bucket capacity while maintaining an average rate.
    """
    capacity: int  # Maximum tokens in bucket
    tokens: float  # Current tokens available
    fill_rate: float  # Tokens added per second
    last_update: float  # Last time bucket was updated
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens available
        """
        now = time.time()
        
        # Add tokens based on time elapsed
        time_passed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + time_passed * self.fill_rate)
        self.last_update = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until enough tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time in seconds until tokens are available
        """
        if self.tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.fill_rate


class TokenBucketRateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.
    
    Maintains separate buckets for different resources and provides
    smooth rate limiting with burst capability.
    """
    
    def __init__(
        self, 
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Average requests allowed per minute
            burst_size: Maximum burst size (defaults to requests_per_minute)
        """
        self._requests_per_minute = requests_per_minute
        self._burst_size = burst_size or requests_per_minute
        
        # Convert to requests per second
        self._fill_rate = requests_per_minute / 60.0
        
        # Thread-safe storage for buckets per resource
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.RLock()
    
    def wait_if_needed(self, resource: str = "default") -> None:
        """
        Wait if rate limit would be exceeded.
        
        Args:
            resource: Resource identifier for separate rate limiting
        """
        wait_time = 0.0
        
        with self._lock:
            bucket = self._get_or_create_bucket(resource)
            
            if not bucket.consume(1):
                # Calculate wait time
                wait_time = bucket.time_until_available(1)
        
        # Sleep outside the lock to avoid blocking other threads
        if wait_time > 0:
            time.sleep(wait_time)
            
            # Try again after waiting
            with self._lock:
                bucket = self._get_or_create_bucket(resource)
                bucket.consume(1)  # Should succeed now
    
    def can_proceed(self, resource: str = "default") -> bool:
        """
        Check if a request can proceed without waiting.
        
        Args:
            resource: Resource identifier
            
        Returns:
            True if request can proceed immediately
        """
        with self._lock:
            bucket = self._get_or_create_bucket(resource)
            return bucket.consume(1)
    
    def time_until_available(self, resource: str = "default") -> float:
        """
        Get time until next request can be made.
        
        Args:
            resource: Resource identifier
            
        Returns:
            Time in seconds until next request is allowed
        """
        with self._lock:
            bucket = self._get_or_create_bucket(resource)
            return bucket.time_until_available(1)
    
    def reset_limits(self, resource: str = "default") -> None:
        """
        Reset rate limiting for a resource.
        
        Args:
            resource: Resource identifier to reset
        """
        with self._lock:
            if resource in self._buckets:
                bucket = self._buckets[resource]
                bucket.tokens = bucket.capacity
                bucket.last_update = time.time()
    
    def get_status(self, resource: str = "default") -> Dict[str, float]:
        """
        Get current status of rate limiter for a resource.
        
        Args:
            resource: Resource identifier
            
        Returns:
            Dictionary with current status information
        """
        with self._lock:
            bucket = self._get_or_create_bucket(resource)
            
            # Update bucket to get current token count
            now = time.time()
            time_passed = now - bucket.last_update
            current_tokens = min(
                bucket.capacity, 
                bucket.tokens + time_passed * bucket.fill_rate
            )
            
            return {
                "current_tokens": current_tokens,
                "capacity": bucket.capacity,
                "fill_rate": bucket.fill_rate,
                "utilization": 1.0 - (current_tokens / bucket.capacity),
                "time_until_full": (bucket.capacity - current_tokens) / bucket.fill_rate
            }
    
    def _get_or_create_bucket(self, resource: str) -> TokenBucket:
        """Get or create a token bucket for a resource."""
        if resource not in self._buckets:
            self._buckets[resource] = TokenBucket(
                capacity=self._burst_size,
                tokens=self._burst_size,  # Start with full bucket
                fill_rate=self._fill_rate,
                last_update=time.time()
            )
        
        return self._buckets[resource]


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on API responses.
    
    Monitors API response times and error rates to automatically
    adjust rate limiting to stay within API limits.
    """
    
    def __init__(
        self,
        initial_requests_per_minute: int = 60,
        min_requests_per_minute: int = 10,
        max_requests_per_minute: int = 120,
        adaptation_factor: float = 0.1
    ):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_requests_per_minute: Starting rate limit
            min_requests_per_minute: Minimum rate limit
            max_requests_per_minute: Maximum rate limit  
            adaptation_factor: How quickly to adapt (0.0 to 1.0)
        """
        self._current_rate = initial_requests_per_minute
        self._min_rate = min_requests_per_minute
        self._max_rate = max_requests_per_minute
        self._adaptation_factor = adaptation_factor
        
        self._base_limiter = TokenBucketRateLimiter(initial_requests_per_minute)
        self._lock = threading.RLock()
        
        # Statistics for adaptation
        self._recent_errors = 0
        self._recent_requests = 0
        self._last_adaptation = time.time()
    
    def wait_if_needed(self, resource: str = "default") -> None:
        """Wait if rate limit would be exceeded."""
        self._base_limiter.wait_if_needed(resource)
        
        with self._lock:
            self._recent_requests += 1
    
    def record_success(self, response_time: float) -> None:
        """
        Record a successful API response.
        
        Args:
            response_time: Response time in seconds
        """
        with self._lock:
            # If response time is good and no recent errors, consider increasing rate
            if response_time < 1.0 and self._recent_errors == 0:
                self._consider_rate_increase()
    
    def record_error(self, is_rate_limit_error: bool = False) -> None:
        """
        Record an API error.
        
        Args:
            is_rate_limit_error: Whether this was a rate limiting error
        """
        with self._lock:
            self._recent_errors += 1
            
            if is_rate_limit_error:
                # Immediately reduce rate on rate limit errors
                self._reduce_rate(factor=0.5)
            else:
                # Consider rate reduction for other errors
                self._consider_rate_decrease()
    
    def _consider_rate_increase(self) -> None:
        """Consider increasing the rate limit."""
        now = time.time()
        
        # Only adapt every 60 seconds
        if now - self._last_adaptation < 60:
            return
        
        # Only increase if we have enough successful requests
        if self._recent_requests >= 10 and self._recent_errors == 0:
            new_rate = min(
                self._max_rate,
                self._current_rate * (1 + self._adaptation_factor)
            )
            self._update_rate(new_rate)
        
        self._reset_stats()
    
    def _consider_rate_decrease(self) -> None:
        """Consider decreasing the rate limit."""
        # Decrease rate if error rate is too high
        if self._recent_requests > 0:
            error_rate = self._recent_errors / self._recent_requests
            if error_rate > 0.1:  # More than 10% errors
                self._reduce_rate(factor=0.8)
    
    def _reduce_rate(self, factor: float) -> None:
        """Reduce the rate limit by a factor."""
        new_rate = max(
            self._min_rate,
            self._current_rate * factor
        )
        self._update_rate(new_rate)
        self._reset_stats()
    
    def _update_rate(self, new_rate: float) -> None:
        """Update the rate limit."""
        if new_rate != self._current_rate:
            self._current_rate = new_rate
            self._base_limiter = TokenBucketRateLimiter(int(new_rate))
            self._last_adaptation = time.time()
    
    def _reset_stats(self) -> None:
        """Reset adaptation statistics."""
        self._recent_errors = 0
        self._recent_requests = 0
    
    def get_current_rate(self) -> float:
        """Get the current rate limit."""
        return self._current_rate


class NoOpRateLimiter:
    """
    No-operation rate limiter for testing or disabled rate limiting.
    
    Implements the rate limiter interface but doesn't actually limit anything.
    """
    
    def wait_if_needed(self, resource: str = "default") -> None:
        """Does nothing (no rate limiting)."""
        pass
    
    def can_proceed(self, resource: str = "default") -> bool:
        """Always returns True (no rate limiting)."""
        return True
    
    def time_until_available(self, resource: str = "default") -> float:
        """Always returns 0 (no waiting needed)."""
        return 0.0
    
    def reset_limits(self, resource: str = "default") -> None:
        """Does nothing (no-op)."""
        pass 