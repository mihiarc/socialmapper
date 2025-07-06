"""Request deduplication for preventing duplicate concurrent API calls.

Ensures that multiple concurrent requests for the same data result in only
one actual API call, with other requests waiting for the result.
"""

import asyncio
import threading
from collections.abc import Callable, Coroutine
from concurrent.futures import Future
from typing import Any, TypeVar

T = TypeVar("T")


class RequestDeduplicator:
    """Prevents duplicate concurrent requests for the same data.

    When multiple threads/coroutines request the same data simultaneously,
    only one actual request is made, and all callers receive the same result.
    """

    def __init__(self):
        """Initialize request deduplicator."""
        self._pending_requests: dict[str, Future[Any]] = {}
        self._lock = threading.RLock()

    def deduplicate(
        self, key: str, request_func: Callable[[], T], timeout: float | None = None
    ) -> T:
        """Execute request with deduplication.

        Args:
            key: Unique key for this request
            request_func: Function that makes the actual request
            timeout: Optional timeout for waiting on deduplicated request

        Returns:
            Request result

        Raises:
            Exception: If request fails
            TimeoutError: If timeout is exceeded
        """
        with self._lock:
            # Check if request is already pending
            if key in self._pending_requests:
                future = self._pending_requests[key]
            else:
                # Create new future for this request
                future = Future()
                self._pending_requests[key] = future

                # We're the first requester, so we need to make the actual request
                threading.Thread(
                    target=self._execute_request,
                    args=(key, request_func, future),
                    daemon=True,
                ).start()

        try:
            # Wait for result
            return future.result(timeout=timeout)
        finally:
            # Clean up completed request
            with self._lock:
                if key in self._pending_requests and self._pending_requests[key] is future:
                    if future.done():
                        del self._pending_requests[key]

    def _execute_request(self, key: str, request_func: Callable[[], T], future: Future) -> None:
        """Execute the actual request and set the future result."""
        try:
            result = request_func()
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

    def clear(self) -> None:
        """Clear all pending requests."""
        with self._lock:
            # Cancel all pending futures
            for future in self._pending_requests.values():
                if not future.done():
                    future.cancel()
            self._pending_requests.clear()

    def get_status(self) -> dict[str, Any]:
        """Get current deduplicator status."""
        with self._lock:
            return {
                "pending_requests": len(self._pending_requests),
                "request_keys": list(self._pending_requests.keys()),
            }


class AsyncRequestDeduplicator:
    """Async version of request deduplicator for async/await code."""

    def __init__(self):
        """Initialize async request deduplicator."""
        self._pending_requests: dict[str, asyncio.Future[Any]] = {}
        self._lock = asyncio.Lock()

    async def deduplicate(
        self,
        key: str,
        request_func: Callable[[], T] | Callable[[], Coroutine[Any, Any, T]],
        timeout: float | None = None,
    ) -> T:
        """Execute request with deduplication (async version).

        Args:
            key: Unique key for this request
            request_func: Async function that makes the actual request
            timeout: Optional timeout for waiting on deduplicated request

        Returns:
            Request result

        Raises:
            Exception: If request fails
            asyncio.TimeoutError: If timeout is exceeded
        """
        async with self._lock:
            # Check if request is already pending
            if key in self._pending_requests:
                future = self._pending_requests[key]
            else:
                # Create new future for this request
                loop = asyncio.get_event_loop()
                future = loop.create_future()
                self._pending_requests[key] = future

                # We're the first requester, so we need to make the actual request
                asyncio.create_task(self._execute_request(key, request_func, future))

        try:
            # Wait for result with timeout
            if timeout:
                return await asyncio.wait_for(future, timeout=timeout)
            else:
                return await future
        finally:
            # Clean up completed request
            async with self._lock:
                if key in self._pending_requests and self._pending_requests[key] is future:
                    if future.done():
                        del self._pending_requests[key]

    async def _execute_request(
        self,
        key: str,
        request_func: Callable[[], T] | Callable[[], Coroutine[Any, Any, T]],
        future: asyncio.Future,
    ) -> None:
        """Execute the actual request and set the future result."""
        try:
            # Handle both sync and async request functions
            if asyncio.iscoroutinefunction(request_func):
                result = await request_func()
            else:
                result = request_func()
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

    async def clear(self) -> None:
        """Clear all pending requests."""
        async with self._lock:
            # Cancel all pending futures
            for future in self._pending_requests.values():
                if not future.done():
                    future.cancel()
            self._pending_requests.clear()

    async def get_status(self) -> dict[str, Any]:
        """Get current deduplicator status."""
        async with self._lock:
            return {
                "pending_requests": len(self._pending_requests),
                "request_keys": list(self._pending_requests.keys()),
            }


def deduplicate_key(*args, **kwargs) -> str:
    """Generate a deduplication key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        String key suitable for deduplication
    """
    # Create a tuple of all arguments
    key_parts = []

    # Add positional arguments
    for arg in args:
        if isinstance(arg, (list, dict, set)):
            # Sort collections for consistent keys
            key_parts.append(str(sorted(str(x) for x in arg)))
        else:
            key_parts.append(str(arg))

    # Add keyword arguments (sorted by key)
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (list, dict, set)):
            key_parts.append(f"{k}={sorted(str(x) for x in v)}")
        else:
            key_parts.append(f"{k}={v}")

    return "|".join(key_parts)
