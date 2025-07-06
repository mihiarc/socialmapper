"""Circuit breaker pattern implementation for API reliability.

Prevents cascading failures by temporarily blocking requests to a failing service.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking all requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening circuit
    recovery_timeout: int = 60  # Seconds before attempting recovery
    success_threshold: int = 2  # Successes needed to close circuit
    excluded_exceptions: tuple[type[Exception], ...] = ()  # Exceptions to ignore


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, recovery_time: float):
        super().__init__(message)
        self.recovery_time = recovery_time


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures.

    Monitors function calls and opens the circuit (blocks calls) when
    failure threshold is reached. After recovery timeout, allows test
    calls to check if service has recovered.
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """Initialize circuit breaker with configuration."""
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            self._check_recovery()
            return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function fails
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                self._check_recovery()
                if self._state == CircuitState.OPEN:
                    recovery_time = self._get_recovery_time()
                    raise CircuitBreakerError(
                        f"Circuit breaker is open. Retry after {recovery_time:.1f} seconds",
                        recovery_time,
                    )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if not isinstance(e, self._config.excluded_exceptions):
                self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._success_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
            elif self._failure_count >= self._config.failure_threshold:
                self._state = CircuitState.OPEN

    def _check_recovery(self) -> None:
        """Check if circuit should attempt recovery."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            time_since_failure = datetime.now() - self._last_failure_time
            if time_since_failure >= timedelta(seconds=self._config.recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._failure_count = 0

    def _get_recovery_time(self) -> float:
        """Get time until recovery attempt."""
        if self._last_failure_time:
            elapsed = (datetime.now() - self._last_failure_time).total_seconds()
            return max(0, self._config.recovery_timeout - elapsed)
        return 0

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        with self._lock:
            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure": (
                    self._last_failure_time.isoformat() if self._last_failure_time else None
                ),
                "recovery_time": self._get_recovery_time() if self._state == CircuitState.OPEN else 0,
            }


class CircuitBreakerDecorator:
    """Decorator for applying circuit breaker to functions."""

    def __init__(self, circuit_breaker: CircuitBreaker):
        """Initialize with circuit breaker instance."""
        self._circuit_breaker = circuit_breaker

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Wrap function with circuit breaker."""

        def wrapper(*args, **kwargs) -> T:
            return self._circuit_breaker.call(func, *args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.circuit_breaker = self._circuit_breaker  # type: ignore
        return wrapper
