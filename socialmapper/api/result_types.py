"""
Result types for explicit error handling in SocialMapper API.

Implements the Result pattern (similar to Rust's Result<T, E>) for
better error handling without exceptions.
"""

import traceback
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


class ErrorType(Enum):
    """Common error types in SocialMapper."""

    VALIDATION = auto()
    NETWORK = auto()
    FILE_NOT_FOUND = auto()
    PERMISSION_DENIED = auto()
    RATE_LIMIT = auto()
    CENSUS_API = auto()
    OSM_API = auto()
    GEOCODING = auto()
    PROCESSING = auto()
    UNKNOWN = auto()


@dataclass
class Error:
    """Structured error information."""

    type: ErrorType
    message: str
    context: Optional[Dict[str, Any]] = None
    cause: Optional[Exception] = None
    traceback: Optional[str] = None

    def __post_init__(self):
        """Capture traceback if cause is provided."""
        if self.cause and not self.traceback:
            self.traceback = traceback.format_exc()

    def __str__(self):
        """Human-readable error message."""
        return f"{self.type.name}: {self.message}"


class Result(Generic[T, E]):
    """
    Result type for explicit error handling.

    Example:
        ```python
        def divide(a: int, b: int) -> Result[float, Error]:
            if b == 0:
                return Err(Error(
                    type=ErrorType.VALIDATION,
                    message="Division by zero"
                ))
            return Ok(a / b)

        result = divide(10, 2)
        match result:
            case Ok(value):
                print(f"Result: {value}")
            case Err(error):
                print(f"Error: {error}")
        ```
    """

    def __init__(self, value: Union[T, E], is_ok: bool):
        """Initialize with value and success flag."""
        self._value = value
        self._is_ok = is_ok

    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self._is_ok

    def is_err(self) -> bool:
        """Check if result is an error."""
        return not self._is_ok

    def unwrap(self) -> T:
        """
        Get the success value or raise.

        Raises:
            RuntimeError: If result is an error
        """
        if self._is_ok:
            return self._value
        raise RuntimeError(f"Called unwrap on an Err value: {self._value}")

    def unwrap_err(self) -> E:
        """
        Get the error value or raise.

        Raises:
            RuntimeError: If result is not an error
        """
        if not self._is_ok:
            return self._value
        raise RuntimeError("Called unwrap_err on an Ok value")

    def unwrap_or(self, default: T) -> T:
        """Get the value or return default if error."""
        return self._value if self._is_ok else default

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        """Get the value or compute default from error."""
        return self._value if self._is_ok else f(self._value)

    def map(self, f: Callable[[T], Any]) -> "Result[Any, E]":
        """Transform the success value if present."""
        if self._is_ok:
            return Ok(f(self._value))
        return self

    def map_err(self, f: Callable[[E], Any]) -> "Result[T, Any]":
        """Transform the error value if present."""
        if not self._is_ok:
            return Err(f(self._value))
        return self

    def and_then(self, f: Callable[[T], "Result[Any, E]"]) -> "Result[Any, E]":
        """Chain operations that return Results."""
        if self._is_ok:
            return f(self._value)
        return self

    def or_else(self, f: Callable[[E], "Result[T, Any]"]) -> "Result[T, Any]":
        """Provide alternative Result on error."""
        if not self._is_ok:
            return f(self._value)
        return self

    __match_args__ = ("_value",)  # Enable pattern matching

    def __bool__(self):
        """Allow if result: syntax."""
        return self._is_ok


class Ok(Result[T, Any]):
    """Successful result."""

    def __init__(self, value: T):
        super().__init__(value, True)

    def __repr__(self):
        return f"Ok({self._value!r})"


class Err(Result[Any, E]):
    """Error result."""

    def __init__(self, error: E):
        super().__init__(error, False)

    def __repr__(self):
        return f"Err({self._value!r})"


# Convenience functions for common operations


def collect_results(results: List[Result[T, E]]) -> Result[List[T], E]:
    """
    Collect a list of Results into a Result of a list.

    Returns Ok with all values if all are Ok, or the first Err.

    Example:
        ```python
        results = [Ok(1), Ok(2), Ok(3)]
        collected = collect_results(results)
        assert collected.unwrap() == [1, 2, 3]
        ```
    """
    values = []
    for result in results:
        if result.is_err():
            return Err(result.unwrap_err())
        values.append(result.unwrap())
    return Ok(values)


def try_all(operations: List[Callable[[], Result[T, E]]]) -> Result[List[T], List[E]]:
    """
    Try all operations and collect results and errors.

    Unlike collect_results, this continues on errors.

    Example:
        ```python
        operations = [
            lambda: Ok(1),
            lambda: Err(Error(ErrorType.NETWORK, "Failed")),
            lambda: Ok(3)
        ]
        result = try_all(operations)
        # Returns Ok([1, 3]) if any succeeded
        # Returns Err([errors]) if all failed
        ```
    """
    successes = []
    errors = []

    for op in operations:
        result = op()
        if result.is_ok():
            successes.append(result.unwrap())
        else:
            errors.append(result.unwrap_err())

    if successes:
        return Ok(successes)
    return Err(errors)


# Decorators for Result-based functions


def result_handler(error_type: ErrorType = ErrorType.UNKNOWN):
    """
    Decorator to convert exceptions to Result types.

    Example:
        ```python
        @result_handler(ErrorType.FILE_NOT_FOUND)
        def read_file(path: str) -> Result[str, Error]:
            with open(path) as f:
                return Ok(f.read())
        ```
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # If function already returns Result, pass through
                if isinstance(result, Result):
                    return result
                # Otherwise wrap in Ok
                return Ok(result)
            except Exception as e:
                return Err(Error(type=error_type, message=str(e), cause=e))

        return wrapper

    return decorator
