"""Rate limiting middleware for the SocialMapper API.
"""

import asyncio
import logging
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..models import RateLimitError

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Simple in-memory rate limiting middleware.
    
    In production, you would use Redis or another distributed cache
    for rate limiting across multiple instances.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60  # 1 minute window

        # Store request timestamps per client IP
        # In production, use Redis instead of in-memory storage
        self.request_history: dict[str, deque[datetime]] = defaultdict(lambda: deque())

        # Cleanup task
        self.cleanup_task = None

    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/api/v1/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        is_allowed, retry_after = self._check_rate_limit(client_ip)

        if not is_allowed:
            # Return rate limit error
            error = RateLimitError(
                message="Rate limit exceeded. Please try again later.",
                limit=self.requests_per_minute,
                window_seconds=self.window_seconds,
                retry_after_seconds=retry_after,
                remaining_requests=0
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error.model_dump(),
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(datetime.now(UTC).timestamp()) + retry_after),
                    "Retry-After": str(retry_after)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining_requests(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int((datetime.now(UTC) + timedelta(seconds=self.window_seconds)).timestamp())
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        """Check if request is within rate limit.
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=self.window_seconds)

        # Get request history for this client
        history = self.request_history[client_ip]

        # Remove old requests outside the window
        while history and history[0] < window_start:
            history.popleft()

        # Check if within limit
        if len(history) >= self.requests_per_minute:
            # Calculate retry after
            oldest_request = history[0]
            retry_after = int((oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds())
            return False, max(1, retry_after)

        # Add current request to history
        history.append(now)
        return True, 0

    def _get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for client."""
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=self.window_seconds)

        history = self.request_history[client_ip]

        # Count requests in current window
        count = sum(1 for timestamp in history if timestamp >= window_start)

        return max(0, self.requests_per_minute - count)

    async def cleanup_history(self):
        """Periodically clean up old request history."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                now = datetime.now(UTC)
                window_start = now - timedelta(seconds=self.window_seconds)

                # Clean up old entries
                for client_ip in list(self.request_history.keys()):
                    history = self.request_history[client_ip]

                    # Remove old requests
                    while history and history[0] < window_start:
                        history.popleft()

                    # Remove empty histories
                    if not history:
                        del self.request_history[client_ip]

                logger.info(f"Cleaned up rate limit history. Active clients: {len(self.request_history)}")

            except Exception as e:
                logger.error(f"Error in rate limit cleanup: {e}")


def setup_rate_limiting(app, settings=None):
    """Set up rate limiting middleware."""
    if settings is None:
        settings = get_settings()

    # Create middleware instance
    middleware = RateLimitMiddleware(
        app,
        requests_per_minute=settings.rate_limit_per_minute
    )

    # Add middleware to app
    app.middleware("http")(middleware)

    # Start cleanup task
    @app.on_event("startup")
    async def start_cleanup():
        middleware.cleanup_task = asyncio.create_task(middleware.cleanup_history())

    @app.on_event("shutdown")
    async def stop_cleanup():
        if middleware.cleanup_task:
            middleware.cleanup_task.cancel()
            try:
                await middleware.cleanup_task
            except asyncio.CancelledError:
                pass

    logger.info(f"Rate limiting enabled: {settings.rate_limit_per_minute} requests per minute")
