"""Metrics collection for Census API monitoring.

Provides comprehensive metrics tracking for API performance, reliability,
and resource usage.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class APIMetrics:
    """Comprehensive metrics for API operations."""

    # Request counts
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    timeout_requests: int = 0

    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0

    # Performance metrics
    total_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0
    last_response_time: float = 0.0

    # Error tracking
    error_counts: dict[str, int] = field(default_factory=dict)
    last_error: str | None = None
    last_error_time: datetime | None = None

    # Circuit breaker metrics
    circuit_breaker_opens: int = 0
    circuit_breaker_successes: int = 0

    # Rate limiter metrics
    rate_limit_waits: int = 0
    total_rate_limit_wait_time: float = 0.0

    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.successful_requests > 0:
            return self.total_response_time / self.successful_requests
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests > 0:
            return (self.successful_requests / self.total_requests) * 100
        return 100.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            return (self.cache_hits / total_cache_requests) * 100
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            "requests": {
                "total": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests,
                "rate_limited": self.rate_limited_requests,
                "timeout": self.timeout_requests,
                "success_rate": f"{self.success_rate:.2f}%",
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "evictions": self.cache_evictions,
                "hit_rate": f"{self.cache_hit_rate:.2f}%",
            },
            "performance": {
                "average_response_time": f"{self.average_response_time:.3f}s",
                "min_response_time": f"{self.min_response_time:.3f}s" if self.min_response_time != float("inf") else "N/A",
                "max_response_time": f"{self.max_response_time:.3f}s",
                "last_response_time": f"{self.last_response_time:.3f}s",
            },
            "errors": {
                "counts_by_type": self.error_counts,
                "last_error": self.last_error,
                "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            },
            "circuit_breaker": {
                "opens": self.circuit_breaker_opens,
                "successful_recoveries": self.circuit_breaker_successes,
            },
            "rate_limiter": {
                "waits": self.rate_limit_waits,
                "total_wait_time": f"{self.total_rate_limit_wait_time:.3f}s",
                "average_wait_time": f"{self.total_rate_limit_wait_time / self.rate_limit_waits:.3f}s" if self.rate_limit_waits > 0 else "0s",
            },
        }


class MetricsCollector:
    """Thread-safe metrics collector for API operations."""

    def __init__(self, window_size: int = 1000):
        """Initialize metrics collector.

        Args:
            window_size: Size of sliding window for recent metrics
        """
        self._metrics = APIMetrics()
        self._lock = threading.RLock()
        self._response_time_window: deque[float] = deque(maxlen=window_size)
        self._error_window: deque[tuple[str, datetime]] = deque(maxlen=window_size)
        self._start_time = datetime.now()

    def record_request(self) -> None:
        """Record a new request."""
        with self._lock:
            self._metrics.total_requests += 1

    def record_success(self, response_time: float) -> None:
        """Record a successful request.

        Args:
            response_time: Time taken for the request in seconds
        """
        with self._lock:
            self._metrics.successful_requests += 1
            self._metrics.total_response_time += response_time
            self._metrics.last_response_time = response_time

            # Update min/max
            self._metrics.min_response_time = min(self._metrics.min_response_time, response_time)
            self._metrics.max_response_time = max(self._metrics.max_response_time, response_time)

            # Add to sliding window
            self._response_time_window.append(response_time)

    def record_error(self, error_type: str, error_message: str | None = None) -> None:
        """Record a failed request.

        Args:
            error_type: Type/class of error
            error_message: Optional error message
        """
        with self._lock:
            self._metrics.failed_requests += 1

            # Count by error type
            self._metrics.error_counts[error_type] = self._metrics.error_counts.get(error_type, 0) + 1

            # Track last error
            self._metrics.last_error = f"{error_type}: {error_message}" if error_message else error_type
            self._metrics.last_error_time = datetime.now()

            # Add to error window
            self._error_window.append((error_type, datetime.now()))

    def record_rate_limit(self, wait_time: float) -> None:
        """Record a rate limit event.

        Args:
            wait_time: Time waited due to rate limiting
        """
        with self._lock:
            self._metrics.rate_limited_requests += 1
            self._metrics.rate_limit_waits += 1
            self._metrics.total_rate_limit_wait_time += wait_time

    def record_timeout(self) -> None:
        """Record a timeout event."""
        with self._lock:
            self._metrics.timeout_requests += 1
            self.record_error("Timeout", "Request timed out")

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self._metrics.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._metrics.cache_misses += 1

    def record_cache_eviction(self) -> None:
        """Record a cache eviction."""
        with self._lock:
            self._metrics.cache_evictions += 1

    def record_circuit_breaker_open(self) -> None:
        """Record circuit breaker opening."""
        with self._lock:
            self._metrics.circuit_breaker_opens += 1

    def record_circuit_breaker_success(self) -> None:
        """Record successful circuit breaker recovery."""
        with self._lock:
            self._metrics.circuit_breaker_successes += 1

    def get_metrics(self) -> APIMetrics:
        """Get current metrics snapshot."""
        with self._lock:
            # Create a copy to avoid thread safety issues
            return APIMetrics(
                total_requests=self._metrics.total_requests,
                successful_requests=self._metrics.successful_requests,
                failed_requests=self._metrics.failed_requests,
                rate_limited_requests=self._metrics.rate_limited_requests,
                timeout_requests=self._metrics.timeout_requests,
                cache_hits=self._metrics.cache_hits,
                cache_misses=self._metrics.cache_misses,
                cache_evictions=self._metrics.cache_evictions,
                total_response_time=self._metrics.total_response_time,
                min_response_time=self._metrics.min_response_time,
                max_response_time=self._metrics.max_response_time,
                last_response_time=self._metrics.last_response_time,
                error_counts=dict(self._metrics.error_counts),
                last_error=self._metrics.last_error,
                last_error_time=self._metrics.last_error_time,
                circuit_breaker_opens=self._metrics.circuit_breaker_opens,
                circuit_breaker_successes=self._metrics.circuit_breaker_successes,
                rate_limit_waits=self._metrics.rate_limit_waits,
                total_rate_limit_wait_time=self._metrics.total_rate_limit_wait_time,
            )

    def get_recent_metrics(self, minutes: int = 5) -> dict[str, Any]:
        """Get metrics for recent time window.

        Args:
            minutes: Number of minutes to look back

        Returns:
            Dictionary with recent metrics
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)

            # Count recent errors
            recent_errors = sum(1 for _, error_time in self._error_window if error_time >= cutoff_time)

            # Calculate recent average response time
            recent_response_times = list(self._response_time_window)
            recent_avg = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0

            return {
                "time_window": f"{minutes} minutes",
                "recent_errors": recent_errors,
                "recent_average_response_time": f"{recent_avg:.3f}s",
                "response_time_samples": len(recent_response_times),
            }

    def get_uptime(self) -> str:
        """Get collector uptime."""
        uptime = datetime.now() - self._start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics = APIMetrics()
            self._response_time_window.clear()
            self._error_window.clear()
            self._start_time = datetime.now()


class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize with metrics collector."""
        self._metrics = metrics_collector
        self._start_time: float | None = None

    def __enter__(self) -> "RequestTimer":
        """Start timing."""
        self._start_time = time.time()
        self._metrics.record_request()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End timing and record result."""
        if self._start_time is not None:
            elapsed = time.time() - self._start_time

            if exc_type is None:
                # Success
                self._metrics.record_success(elapsed)
            elif exc_type.__name__ == "Timeout":
                self._metrics.record_timeout()
            else:
                # Error
                self._metrics.record_error(exc_type.__name__, str(exc_val))
