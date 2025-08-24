"""MCP context middleware for tracking and monitoring MCP-specific requests.

This middleware adds MCP-specific context to requests, tracks performance,
and provides enhanced logging for MCP tool invocations.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


class MCPRequestContext(BaseModel):
    """Context information for MCP requests."""
    
    request_id: str = Field(..., description="Unique request identifier")
    client_id: Optional[str] = Field(None, description="MCP client identifier")
    tool_name: Optional[str] = Field(None, description="Invoked tool name")
    operation_id: Optional[str] = Field(None, description="FastAPI operation ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    mcp_version: Optional[str] = Field(None, description="MCP protocol version")
    session_id: Optional[str] = Field(None, description="MCP session identifier")
    parent_request_id: Optional[str] = Field(None, description="Parent request ID for nested calls")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MCPPerformanceMetrics(BaseModel):
    """Performance metrics for MCP requests."""
    
    request_id: str = Field(..., description="Request identifier")
    start_time: float = Field(..., description="Request start time (Unix timestamp)")
    end_time: Optional[float] = Field(None, description="Request end time (Unix timestamp)")
    duration_ms: Optional[float] = Field(None, description="Request duration in milliseconds")
    status_code: Optional[int] = Field(None, description="Response status code")
    error: Optional[str] = Field(None, description="Error message if failed")
    response_size: Optional[int] = Field(None, description="Response size in bytes")
    tool_metrics: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific metrics")


class MCPContextMiddleware:
    """Middleware for tracking MCP requests and adding context."""
    
    # MCP-specific headers
    MCP_HEADERS = {
        "x-mcp-request-id": "request_id",
        "x-mcp-client-id": "client_id",
        "x-mcp-tool": "tool_name",
        "x-mcp-session-id": "session_id",
        "x-mcp-version": "mcp_version",
        "x-mcp-parent-request": "parent_request_id"
    }
    
    def __init__(
        self,
        app: FastAPI,
        enable_performance_logging: bool = True,
        enable_request_logging: bool = True,
        log_response_body: bool = False,
        performance_threshold_ms: float = 1000.0,
        track_slow_requests: bool = True
    ):
        """Initialize MCP context middleware.
        
        Args:
            app: FastAPI application instance
            enable_performance_logging: Enable performance metrics logging
            enable_request_logging: Enable request/response logging
            log_response_body: Include response body in logs (be careful with sensitive data)
            performance_threshold_ms: Threshold for slow request warnings
            track_slow_requests: Track and report slow requests
        """
        self.app = app
        self.enable_performance_logging = enable_performance_logging
        self.enable_request_logging = enable_request_logging
        self.log_response_body = log_response_body
        self.performance_threshold_ms = performance_threshold_ms
        self.track_slow_requests = track_slow_requests
        
        # Performance tracking
        self.active_requests: Dict[str, MCPPerformanceMetrics] = {}
        self.request_history: Dict[str, MCPPerformanceMetrics] = {}
        self.slow_requests: list[MCPPerformanceMetrics] = []
        
        # Statistics
        self.total_requests = 0
        self.total_errors = 0
        self.total_duration_ms = 0.0
        self.request_counts_by_tool: Dict[str, int] = {}
        self.error_counts_by_tool: Dict[str, int] = {}
        self.avg_duration_by_tool: Dict[str, list[float]] = {}
        
    def extract_mcp_context(self, request: Request) -> MCPRequestContext:
        """Extract MCP context from request headers.
        
        Args:
            request: FastAPI request object
            
        Returns:
            MCP request context
        """
        # Generate or extract request ID
        request_id = request.headers.get("x-mcp-request-id")
        if not request_id:
            request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        
        # Extract MCP-specific headers
        context_data = {"request_id": request_id}
        for header_name, context_field in self.MCP_HEADERS.items():
            value = request.headers.get(header_name)
            if value and context_field != "request_id":
                context_data[context_field] = value
        
        # Add request metadata
        context_data["source_ip"] = request.client.host if request.client else None
        context_data["user_agent"] = request.headers.get("user-agent")
        
        # Try to extract tool name from path
        if not context_data.get("tool_name") and "/mcp/" in str(request.url):
            # Extract tool name from MCP path if present
            path_parts = str(request.url.path).split("/")
            if "tools" in path_parts:
                try:
                    tool_index = path_parts.index("tools")
                    if len(path_parts) > tool_index + 1:
                        context_data["tool_name"] = path_parts[tool_index + 1]
                except (ValueError, IndexError):
                    pass
        
        return MCPRequestContext(**context_data)
    
    def track_performance_start(self, context: MCPRequestContext) -> MCPPerformanceMetrics:
        """Start tracking performance for a request.
        
        Args:
            context: MCP request context
            
        Returns:
            Performance metrics object
        """
        metrics = MCPPerformanceMetrics(
            request_id=context.request_id,
            start_time=time.time()
        )
        
        self.active_requests[context.request_id] = metrics
        self.total_requests += 1
        
        if context.tool_name:
            self.request_counts_by_tool[context.tool_name] = \
                self.request_counts_by_tool.get(context.tool_name, 0) + 1
        
        return metrics
    
    def track_performance_end(
        self,
        context: MCPRequestContext,
        status_code: int,
        response_size: Optional[int] = None,
        error: Optional[str] = None
    ) -> Optional[MCPPerformanceMetrics]:
        """End tracking performance for a request.
        
        Args:
            context: MCP request context
            status_code: Response status code
            response_size: Response size in bytes
            error: Error message if failed
            
        Returns:
            Completed performance metrics or None
        """
        metrics = self.active_requests.get(context.request_id)
        if not metrics:
            return None
        
        # Update metrics
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.status_code = status_code
        metrics.response_size = response_size
        metrics.error = error
        
        # Track errors
        if status_code >= 400 or error:
            self.total_errors += 1
            if context.tool_name:
                self.error_counts_by_tool[context.tool_name] = \
                    self.error_counts_by_tool.get(context.tool_name, 0) + 1
        
        # Track duration
        self.total_duration_ms += metrics.duration_ms
        if context.tool_name:
            if context.tool_name not in self.avg_duration_by_tool:
                self.avg_duration_by_tool[context.tool_name] = []
            self.avg_duration_by_tool[context.tool_name].append(metrics.duration_ms)
            # Keep only last 100 measurements
            if len(self.avg_duration_by_tool[context.tool_name]) > 100:
                self.avg_duration_by_tool[context.tool_name] = \
                    self.avg_duration_by_tool[context.tool_name][-100:]
        
        # Track slow requests
        if self.track_slow_requests and metrics.duration_ms > self.performance_threshold_ms:
            self.slow_requests.append(metrics)
            # Keep only last 50 slow requests
            if len(self.slow_requests) > 50:
                self.slow_requests = self.slow_requests[-50:]
            
            if self.enable_performance_logging:
                logger.warning(
                    f"Slow MCP request detected: {context.request_id} "
                    f"(tool: {context.tool_name}, duration: {metrics.duration_ms:.2f}ms)"
                )
        
        # Move to history
        del self.active_requests[context.request_id]
        self.request_history[context.request_id] = metrics
        
        # Limit history size
        if len(self.request_history) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.request_history.keys())[:100]
            for key in oldest_keys:
                del self.request_history[key]
        
        return metrics
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with MCP context tracking.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint
            
        Returns:
            Response object
        """
        # Skip non-MCP requests unless they're tool invocations
        path = str(request.url.path)
        is_mcp_request = (
            "/mcp/" in path or
            "x-mcp-" in str(request.headers).lower() or
            request.headers.get("x-mcp-client-id")
        )
        
        if not is_mcp_request:
            # Pass through non-MCP requests
            return await call_next(request)
        
        # Extract MCP context
        context = self.extract_mcp_context(request)
        
        # Store context in request state for use by endpoints
        request.state.mcp_context = context
        
        # Log request if enabled
        if self.enable_request_logging:
            logger.info(
                f"MCP Request: {context.request_id} | "
                f"Client: {context.client_id} | "
                f"Tool: {context.tool_name} | "
                f"IP: {context.source_ip}"
            )
        
        # Start performance tracking
        metrics = self.track_performance_start(context)
        
        response_data = None
        error_message = None
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Extract response size
            response_size = None
            if hasattr(response, "body"):
                response_size = len(response.body) if response.body else 0
            elif hasattr(response, "headers"):
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        response_size = int(content_length)
                    except ValueError:
                        pass
            
            # Add MCP headers to response
            response.headers["x-mcp-request-id"] = context.request_id
            response.headers["x-mcp-processing-time-ms"] = str(
                int((time.time() - metrics.start_time) * 1000)
            )
            
            # Track performance
            self.track_performance_end(
                context,
                response.status_code,
                response_size
            )
            
            # Log response if enabled
            if self.enable_request_logging:
                logger.info(
                    f"MCP Response: {context.request_id} | "
                    f"Status: {response.status_code} | "
                    f"Duration: {(time.time() - metrics.start_time) * 1000:.2f}ms"
                )
            
            return response
            
        except Exception as e:
            # Track error
            error_message = str(e)
            self.track_performance_end(
                context,
                500,
                error=error_message
            )
            
            # Log error
            logger.error(
                f"MCP Request failed: {context.request_id} | "
                f"Tool: {context.tool_name} | "
                f"Error: {error_message}"
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": error_message if request.app.debug else "An error occurred",
                    "request_id": context.request_id
                },
                headers={
                    "x-mcp-request-id": context.request_id,
                    "x-mcp-error": "true"
                }
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get middleware statistics.
        
        Returns:
            Dictionary of statistics
        """
        avg_duration = (
            self.total_duration_ms / self.total_requests
            if self.total_requests > 0 else 0
        )
        
        tool_stats = {}
        for tool_name in self.request_counts_by_tool:
            durations = self.avg_duration_by_tool.get(tool_name, [])
            avg_tool_duration = sum(durations) / len(durations) if durations else 0
            
            tool_stats[tool_name] = {
                "requests": self.request_counts_by_tool.get(tool_name, 0),
                "errors": self.error_counts_by_tool.get(tool_name, 0),
                "avg_duration_ms": avg_tool_duration
            }
        
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / self.total_requests if self.total_requests > 0 else 0,
            "avg_duration_ms": avg_duration,
            "active_requests": len(self.active_requests),
            "slow_requests_count": len(self.slow_requests),
            "tool_statistics": tool_stats
        }
    
    def display_statistics(self) -> None:
        """Display statistics in a formatted table."""
        stats = self.get_statistics()
        
        # Main statistics table
        main_table = Table(title="MCP Context Middleware Statistics", show_header=True)
        main_table.add_column("Metric", style="cyan")
        main_table.add_column("Value", style="yellow")
        
        main_table.add_row("Total Requests", str(stats["total_requests"]))
        main_table.add_row("Total Errors", str(stats["total_errors"]))
        main_table.add_row("Error Rate", f"{stats['error_rate']:.2%}")
        main_table.add_row("Avg Duration (ms)", f"{stats['avg_duration_ms']:.2f}")
        main_table.add_row("Active Requests", str(stats["active_requests"]))
        main_table.add_row("Slow Requests", str(stats["slow_requests_count"]))
        
        console.print(main_table)
        
        # Tool statistics table
        if stats["tool_statistics"]:
            tool_table = Table(title="Tool Statistics", show_header=True)
            tool_table.add_column("Tool", style="cyan")
            tool_table.add_column("Requests", style="green")
            tool_table.add_column("Errors", style="red")
            tool_table.add_column("Avg Duration (ms)", style="blue")
            
            for tool_name, tool_stats in stats["tool_statistics"].items():
                tool_table.add_row(
                    tool_name,
                    str(tool_stats["requests"]),
                    str(tool_stats["errors"]),
                    f"{tool_stats['avg_duration_ms']:.2f}"
                )
            
            console.print(tool_table)
    
    def get_slow_requests(self) -> list[Dict[str, Any]]:
        """Get list of slow requests.
        
        Returns:
            List of slow request details
        """
        return [
            {
                "request_id": req.request_id,
                "duration_ms": req.duration_ms,
                "status_code": req.status_code,
                "timestamp": datetime.fromtimestamp(req.start_time).isoformat()
            }
            for req in self.slow_requests
        ]


def setup_mcp_context_middleware(
    app: FastAPI,
    enable_performance_logging: bool = True,
    enable_request_logging: bool = True,
    performance_threshold_ms: float = 1000.0
) -> MCPContextMiddleware:
    """Set up MCP context middleware for the application.
    
    Args:
        app: FastAPI application
        enable_performance_logging: Enable performance metrics logging
        enable_request_logging: Enable request/response logging
        performance_threshold_ms: Threshold for slow request warnings
        
    Returns:
        MCPContextMiddleware instance
    """
    middleware = MCPContextMiddleware(
        app=app,
        enable_performance_logging=enable_performance_logging,
        enable_request_logging=enable_request_logging,
        performance_threshold_ms=performance_threshold_ms
    )
    
    # Add as middleware
    app.middleware("http")(middleware)
    
    # Add statistics endpoint
    @app.get("/api/v1/mcp/statistics")
    async def get_mcp_statistics():
        """Get MCP middleware statistics."""
        return middleware.get_statistics()
    
    @app.get("/api/v1/mcp/slow-requests")
    async def get_slow_requests():
        """Get list of slow MCP requests."""
        return middleware.get_slow_requests()
    
    logger.info("MCP context middleware configured")
    return middleware