"""MCP metrics collection and reporting service.

This module provides comprehensive metrics tracking for MCP tool invocations,
client usage, performance monitoring, and error rate tracking.
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, DefaultDict, Deque, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

logger = logging.getLogger(__name__)
console = Console()


class MetricType(str, Enum):
    """Types of metrics tracked."""
    
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class ToolInvocation(BaseModel):
    """Record of a tool invocation."""
    
    tool_name: str = Field(..., description="Name of the invoked tool")
    client_id: str = Field(..., description="Client identifier")
    request_id: str = Field(..., description="Request identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = Field(..., description="Execution duration in milliseconds")
    success: bool = Field(..., description="Whether the invocation was successful")
    error_type: Optional[str] = Field(None, description="Error type if failed")
    input_size: Optional[int] = Field(None, description="Input payload size in bytes")
    output_size: Optional[int] = Field(None, description="Output payload size in bytes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ClientUsageStats(BaseModel):
    """Usage statistics for a specific client."""
    
    client_id: str = Field(..., description="Client identifier")
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_requests: int = Field(default=0, description="Total number of requests")
    successful_requests: int = Field(default=0, description="Number of successful requests")
    failed_requests: int = Field(default=0, description="Number of failed requests")
    total_duration_ms: float = Field(default=0.0, description="Total processing time")
    tools_used: Set[str] = Field(default_factory=set, description="Set of tools used")
    error_types: DefaultDict[str, int] = Field(
        default_factory=lambda: defaultdict(int),
        description="Count of errors by type"
    )
    hourly_requests: DefaultDict[int, int] = Field(
        default_factory=lambda: defaultdict(int),
        description="Requests by hour of day"
    )


class ToolMetrics(BaseModel):
    """Metrics for a specific tool."""
    
    tool_name: str = Field(..., description="Tool name")
    total_invocations: int = Field(default=0, description="Total invocations")
    successful_invocations: int = Field(default=0, description="Successful invocations")
    failed_invocations: int = Field(default=0, description="Failed invocations")
    total_duration_ms: float = Field(default=0.0, description="Total duration")
    min_duration_ms: Optional[float] = Field(None, description="Minimum duration")
    max_duration_ms: Optional[float] = Field(None, description="Maximum duration")
    avg_duration_ms: Optional[float] = Field(None, description="Average duration")
    median_duration_ms: Optional[float] = Field(None, description="Median duration")
    p95_duration_ms: Optional[float] = Field(None, description="95th percentile duration")
    p99_duration_ms: Optional[float] = Field(None, description="99th percentile duration")
    error_rate: float = Field(default=0.0, description="Error rate")
    unique_clients: Set[str] = Field(default_factory=set, description="Unique clients")
    error_types: DefaultDict[str, int] = Field(
        default_factory=lambda: defaultdict(int),
        description="Error counts by type"
    )
    recent_durations: Deque[float] = Field(
        default_factory=lambda: deque(maxlen=1000),
        description="Recent duration samples"
    )


class AggregateMetrics(BaseModel):
    """Aggregate metrics across all tools and clients."""
    
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_invocations: int = Field(default=0, description="Total invocations")
    successful_invocations: int = Field(default=0, description="Successful invocations")
    failed_invocations: int = Field(default=0, description="Failed invocations")
    unique_tools: int = Field(default=0, description="Number of unique tools")
    unique_clients: int = Field(default=0, description="Number of unique clients")
    avg_duration_ms: float = Field(default=0.0, description="Average duration")
    error_rate: float = Field(default=0.0, description="Overall error rate")
    requests_per_minute: float = Field(default=0.0, description="Average requests per minute")
    peak_rpm: float = Field(default=0.0, description="Peak requests per minute")
    peak_rpm_time: Optional[datetime] = Field(None, description="Time of peak RPM")


class MCPMetricsCollector:
    """Collector for MCP-specific metrics."""
    
    def __init__(
        self,
        retention_hours: int = 24,
        sample_size: int = 1000,
        enable_detailed_tracking: bool = True
    ):
        """Initialize the metrics collector.
        
        Args:
            retention_hours: Hours to retain detailed metrics
            sample_size: Size of sample windows for percentile calculations
            enable_detailed_tracking: Enable detailed per-invocation tracking
        """
        self.retention_hours = retention_hours
        self.sample_size = sample_size
        self.enable_detailed_tracking = enable_detailed_tracking
        
        # Metrics storage
        self.invocations: Deque[ToolInvocation] = deque()
        self.tool_metrics: Dict[str, ToolMetrics] = {}
        self.client_stats: Dict[str, ClientUsageStats] = {}
        self.aggregate_metrics = AggregateMetrics()
        
        # Time-series data
        self.minute_buckets: DefaultDict[datetime, Dict[str, Any]] = defaultdict(
            lambda: {"requests": 0, "errors": 0, "duration_ms": 0.0}
        )
        self.hourly_buckets: DefaultDict[datetime, Dict[str, Any]] = defaultdict(
            lambda: {"requests": 0, "errors": 0, "duration_ms": 0.0, "unique_clients": set()}
        )
        
        # Real-time tracking
        self.current_rpm = 0
        self.last_minute_requests: Deque[datetime] = deque()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the metrics collector background tasks."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("MCP metrics collector started")
    
    async def stop(self) -> None:
        """Stop the metrics collector background tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("MCP metrics collector stopped")
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up old metrics."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up metrics older than retention period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        
        # Clean invocations
        if self.enable_detailed_tracking:
            while self.invocations and self.invocations[0].timestamp < cutoff_time:
                self.invocations.popleft()
        
        # Clean minute buckets
        old_minutes = [
            minute for minute in self.minute_buckets
            if minute < cutoff_time
        ]
        for minute in old_minutes:
            del self.minute_buckets[minute]
        
        # Clean hourly buckets
        old_hours = [
            hour for hour in self.hourly_buckets
            if hour < cutoff_time
        ]
        for hour in old_hours:
            del self.hourly_buckets[hour]
        
        logger.info(f"Cleaned up metrics older than {cutoff_time}")
    
    def record_invocation(
        self,
        tool_name: str,
        client_id: str,
        request_id: str,
        duration_ms: float,
        success: bool,
        error_type: Optional[str] = None,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a tool invocation.
        
        Args:
            tool_name: Name of the invoked tool
            client_id: Client identifier
            request_id: Request identifier
            duration_ms: Execution duration in milliseconds
            success: Whether the invocation was successful
            error_type: Error type if failed
            input_size: Input payload size
            output_size: Output payload size
            metadata: Additional metadata
        """
        now = datetime.now(timezone.utc)
        
        # Create invocation record
        invocation = ToolInvocation(
            tool_name=tool_name,
            client_id=client_id,
            request_id=request_id,
            timestamp=now,
            duration_ms=duration_ms,
            success=success,
            error_type=error_type,
            input_size=input_size,
            output_size=output_size,
            metadata=metadata or {}
        )
        
        # Store detailed record if enabled
        if self.enable_detailed_tracking:
            self.invocations.append(invocation)
            # Limit size
            if len(self.invocations) > 10000:
                self.invocations.popleft()
        
        # Update tool metrics
        self._update_tool_metrics(invocation)
        
        # Update client stats
        self._update_client_stats(invocation)
        
        # Update aggregate metrics
        self._update_aggregate_metrics(invocation)
        
        # Update time-series data
        self._update_time_series(invocation)
        
        # Update real-time RPM
        self._update_rpm(now)
    
    def _update_tool_metrics(self, invocation: ToolInvocation) -> None:
        """Update metrics for a specific tool."""
        tool_name = invocation.tool_name
        
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolMetrics(tool_name=tool_name)
        
        metrics = self.tool_metrics[tool_name]
        metrics.total_invocations += 1
        
        if invocation.success:
            metrics.successful_invocations += 1
        else:
            metrics.failed_invocations += 1
            if invocation.error_type:
                metrics.error_types[invocation.error_type] += 1
        
        # Update duration statistics
        metrics.total_duration_ms += invocation.duration_ms
        metrics.recent_durations.append(invocation.duration_ms)
        
        if metrics.min_duration_ms is None or invocation.duration_ms < metrics.min_duration_ms:
            metrics.min_duration_ms = invocation.duration_ms
        
        if metrics.max_duration_ms is None or invocation.duration_ms > metrics.max_duration_ms:
            metrics.max_duration_ms = invocation.duration_ms
        
        # Calculate statistics
        if metrics.recent_durations:
            sorted_durations = sorted(metrics.recent_durations)
            metrics.avg_duration_ms = sum(sorted_durations) / len(sorted_durations)
            metrics.median_duration_ms = sorted_durations[len(sorted_durations) // 2]
            
            p95_index = int(len(sorted_durations) * 0.95)
            p99_index = int(len(sorted_durations) * 0.99)
            metrics.p95_duration_ms = sorted_durations[min(p95_index, len(sorted_durations) - 1)]
            metrics.p99_duration_ms = sorted_durations[min(p99_index, len(sorted_durations) - 1)]
        
        metrics.error_rate = (
            metrics.failed_invocations / metrics.total_invocations
            if metrics.total_invocations > 0 else 0
        )
        
        metrics.unique_clients.add(invocation.client_id)
    
    def _update_client_stats(self, invocation: ToolInvocation) -> None:
        """Update statistics for a specific client."""
        client_id = invocation.client_id
        
        if client_id not in self.client_stats:
            self.client_stats[client_id] = ClientUsageStats(client_id=client_id)
        
        stats = self.client_stats[client_id]
        stats.last_seen = invocation.timestamp
        stats.total_requests += 1
        
        if invocation.success:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
            if invocation.error_type:
                stats.error_types[invocation.error_type] += 1
        
        stats.total_duration_ms += invocation.duration_ms
        stats.tools_used.add(invocation.tool_name)
        
        # Track hourly pattern
        hour = invocation.timestamp.hour
        stats.hourly_requests[hour] += 1
    
    def _update_aggregate_metrics(self, invocation: ToolInvocation) -> None:
        """Update aggregate metrics."""
        self.aggregate_metrics.total_invocations += 1
        
        if invocation.success:
            self.aggregate_metrics.successful_invocations += 1
        else:
            self.aggregate_metrics.failed_invocations += 1
        
        self.aggregate_metrics.unique_tools = len(self.tool_metrics)
        self.aggregate_metrics.unique_clients = len(self.client_stats)
        
        # Calculate average duration
        total_duration = sum(m.total_duration_ms for m in self.tool_metrics.values())
        total_count = self.aggregate_metrics.total_invocations
        self.aggregate_metrics.avg_duration_ms = (
            total_duration / total_count if total_count > 0 else 0
        )
        
        # Calculate error rate
        self.aggregate_metrics.error_rate = (
            self.aggregate_metrics.failed_invocations / self.aggregate_metrics.total_invocations
            if self.aggregate_metrics.total_invocations > 0 else 0
        )
        
        # Calculate requests per minute
        elapsed_minutes = (
            datetime.now(timezone.utc) - self.aggregate_metrics.start_time
        ).total_seconds() / 60
        if elapsed_minutes > 0:
            self.aggregate_metrics.requests_per_minute = (
                self.aggregate_metrics.total_invocations / elapsed_minutes
            )
    
    def _update_time_series(self, invocation: ToolInvocation) -> None:
        """Update time-series data."""
        # Update minute bucket
        minute = invocation.timestamp.replace(second=0, microsecond=0)
        self.minute_buckets[minute]["requests"] += 1
        if not invocation.success:
            self.minute_buckets[minute]["errors"] += 1
        self.minute_buckets[minute]["duration_ms"] += invocation.duration_ms
        
        # Update hourly bucket
        hour = invocation.timestamp.replace(minute=0, second=0, microsecond=0)
        self.hourly_buckets[hour]["requests"] += 1
        if not invocation.success:
            self.hourly_buckets[hour]["errors"] += 1
        self.hourly_buckets[hour]["duration_ms"] += invocation.duration_ms
        self.hourly_buckets[hour]["unique_clients"].add(invocation.client_id)
    
    def _update_rpm(self, now: datetime) -> None:
        """Update real-time requests per minute."""
        # Remove requests older than 1 minute
        cutoff = now - timedelta(minutes=1)
        while self.last_minute_requests and self.last_minute_requests[0] < cutoff:
            self.last_minute_requests.popleft()
        
        # Add current request
        self.last_minute_requests.append(now)
        self.current_rpm = len(self.last_minute_requests)
        
        # Update peak RPM
        if self.current_rpm > self.aggregate_metrics.peak_rpm:
            self.aggregate_metrics.peak_rpm = self.current_rpm
            self.aggregate_metrics.peak_rpm_time = now
    
    def get_tool_metrics(self, tool_name: str) -> Optional[ToolMetrics]:
        """Get metrics for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool metrics if available
        """
        return self.tool_metrics.get(tool_name)
    
    def get_client_stats(self, client_id: str) -> Optional[ClientUsageStats]:
        """Get statistics for a specific client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Client statistics if available
        """
        return self.client_stats.get(client_id)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics.
        
        Returns:
            Dictionary containing metrics summary
        """
        top_tools = sorted(
            self.tool_metrics.values(),
            key=lambda x: x.total_invocations,
            reverse=True
        )[:5]
        
        top_clients = sorted(
            self.client_stats.values(),
            key=lambda x: x.total_requests,
            reverse=True
        )[:5]
        
        return {
            "aggregate": {
                "total_invocations": self.aggregate_metrics.total_invocations,
                "successful_invocations": self.aggregate_metrics.successful_invocations,
                "failed_invocations": self.aggregate_metrics.failed_invocations,
                "unique_tools": self.aggregate_metrics.unique_tools,
                "unique_clients": self.aggregate_metrics.unique_clients,
                "avg_duration_ms": round(self.aggregate_metrics.avg_duration_ms, 2),
                "error_rate": round(self.aggregate_metrics.error_rate, 4),
                "current_rpm": self.current_rpm,
                "avg_rpm": round(self.aggregate_metrics.requests_per_minute, 2),
                "peak_rpm": self.aggregate_metrics.peak_rpm,
                "peak_rpm_time": (
                    self.aggregate_metrics.peak_rpm_time.isoformat()
                    if self.aggregate_metrics.peak_rpm_time else None
                ),
                "uptime_hours": round(
                    (datetime.now(timezone.utc) - self.aggregate_metrics.start_time).total_seconds() / 3600,
                    2
                )
            },
            "top_tools": [
                {
                    "name": tool.tool_name,
                    "invocations": tool.total_invocations,
                    "success_rate": round(
                        tool.successful_invocations / tool.total_invocations
                        if tool.total_invocations > 0 else 0,
                        4
                    ),
                    "avg_duration_ms": round(tool.avg_duration_ms or 0, 2),
                    "p95_duration_ms": round(tool.p95_duration_ms or 0, 2),
                    "unique_clients": len(tool.unique_clients)
                }
                for tool in top_tools
            ],
            "top_clients": [
                {
                    "client_id": client.client_id,
                    "total_requests": client.total_requests,
                    "success_rate": round(
                        client.successful_requests / client.total_requests
                        if client.total_requests > 0 else 0,
                        4
                    ),
                    "avg_duration_ms": round(
                        client.total_duration_ms / client.total_requests
                        if client.total_requests > 0 else 0,
                        2
                    ),
                    "tools_used": len(client.tools_used),
                    "last_seen": client.last_seen.isoformat()
                }
                for client in top_clients
            ]
        }
    
    def get_time_series(
        self,
        granularity: str = "minute",
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get time-series metrics data.
        
        Args:
            granularity: "minute" or "hour"
            hours: Number of hours of data to return
            
        Returns:
            List of time-series data points
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=hours)
        
        if granularity == "minute":
            buckets = self.minute_buckets
        else:
            buckets = self.hourly_buckets
        
        result = []
        for timestamp, data in sorted(buckets.items()):
            if timestamp >= cutoff:
                point = {
                    "timestamp": timestamp.isoformat(),
                    "requests": data["requests"],
                    "errors": data["errors"],
                    "error_rate": data["errors"] / data["requests"] if data["requests"] > 0 else 0,
                    "avg_duration_ms": (
                        data["duration_ms"] / data["requests"]
                        if data["requests"] > 0 else 0
                    )
                }
                
                if granularity == "hour":
                    point["unique_clients"] = len(data["unique_clients"])
                
                result.append(point)
        
        return result
    
    def display_dashboard(self) -> None:
        """Display a metrics dashboard in the console."""
        summary = self.get_summary()
        
        # Aggregate metrics table
        agg_table = Table(title="MCP Aggregate Metrics", show_header=True)
        agg_table.add_column("Metric", style="cyan")
        agg_table.add_column("Value", style="yellow")
        
        agg = summary["aggregate"]
        agg_table.add_row("Total Invocations", str(agg["total_invocations"]))
        agg_table.add_row("Success Rate", f"{(1 - agg['error_rate']) * 100:.2f}%")
        agg_table.add_row("Current RPM", str(agg["current_rpm"]))
        agg_table.add_row("Average RPM", f"{agg['avg_rpm']:.2f}")
        agg_table.add_row("Peak RPM", f"{agg['peak_rpm']}")
        agg_table.add_row("Avg Duration (ms)", f"{agg['avg_duration_ms']:.2f}")
        agg_table.add_row("Unique Tools", str(agg["unique_tools"]))
        agg_table.add_row("Unique Clients", str(agg["unique_clients"]))
        agg_table.add_row("Uptime (hours)", f"{agg['uptime_hours']:.2f}")
        
        console.print(agg_table)
        
        # Top tools table
        if summary["top_tools"]:
            tools_table = Table(title="Top Tools by Usage", show_header=True)
            tools_table.add_column("Tool", style="cyan")
            tools_table.add_column("Invocations", style="green")
            tools_table.add_column("Success Rate", style="yellow")
            tools_table.add_column("Avg Duration", style="blue")
            tools_table.add_column("P95 Duration", style="magenta")
            
            for tool in summary["top_tools"]:
                tools_table.add_row(
                    tool["name"],
                    str(tool["invocations"]),
                    f"{tool['success_rate'] * 100:.2f}%",
                    f"{tool['avg_duration_ms']:.2f}ms",
                    f"{tool['p95_duration_ms']:.2f}ms"
                )
            
            console.print(tools_table)
        
        # Top clients table
        if summary["top_clients"]:
            clients_table = Table(title="Top Clients by Usage", show_header=True)
            clients_table.add_column("Client ID", style="cyan")
            clients_table.add_column("Requests", style="green")
            clients_table.add_column("Success Rate", style="yellow")
            clients_table.add_column("Avg Duration", style="blue")
            clients_table.add_column("Tools Used", style="magenta")
            
            for client in summary["top_clients"]:
                clients_table.add_row(
                    client["client_id"][:16] + "...",
                    str(client["total_requests"]),
                    f"{client['success_rate'] * 100:.2f}%",
                    f"{client['avg_duration_ms']:.2f}ms",
                    str(client["tools_used"])
                )
            
            console.print(clients_table)
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format.
        
        Args:
            format: Export format ("json" or "prometheus")
            
        Returns:
            Exported metrics string
        """
        if format == "json":
            return json.dumps(self.get_summary(), indent=2, default=str)
        
        elif format == "prometheus":
            lines = []
            agg = self.aggregate_metrics
            
            # Aggregate metrics
            lines.append(f"# HELP mcp_invocations_total Total MCP tool invocations")
            lines.append(f"# TYPE mcp_invocations_total counter")
            lines.append(f"mcp_invocations_total {agg.total_invocations}")
            
            lines.append(f"# HELP mcp_invocations_success_total Successful MCP invocations")
            lines.append(f"# TYPE mcp_invocations_success_total counter")
            lines.append(f"mcp_invocations_success_total {agg.successful_invocations}")
            
            lines.append(f"# HELP mcp_invocations_failed_total Failed MCP invocations")
            lines.append(f"# TYPE mcp_invocations_failed_total counter")
            lines.append(f"mcp_invocations_failed_total {agg.failed_invocations}")
            
            lines.append(f"# HELP mcp_error_rate MCP error rate")
            lines.append(f"# TYPE mcp_error_rate gauge")
            lines.append(f"mcp_error_rate {agg.error_rate}")
            
            lines.append(f"# HELP mcp_rpm Current requests per minute")
            lines.append(f"# TYPE mcp_rpm gauge")
            lines.append(f"mcp_rpm {self.current_rpm}")
            
            # Tool-specific metrics
            for tool_name, metrics in self.tool_metrics.items():
                safe_name = tool_name.replace("-", "_").replace(" ", "_")
                
                lines.append(f'mcp_tool_invocations_total{{tool="{tool_name}"}} {metrics.total_invocations}')
                lines.append(f'mcp_tool_success_total{{tool="{tool_name}"}} {metrics.successful_invocations}')
                lines.append(f'mcp_tool_failed_total{{tool="{tool_name}"}} {metrics.failed_invocations}')
                
                if metrics.avg_duration_ms:
                    lines.append(f'mcp_tool_duration_ms{{tool="{tool_name}",quantile="0.5"}} {metrics.median_duration_ms}')
                    lines.append(f'mcp_tool_duration_ms{{tool="{tool_name}",quantile="0.95"}} {metrics.p95_duration_ms}')
                    lines.append(f'mcp_tool_duration_ms{{tool="{tool_name}",quantile="0.99"}} {metrics.p99_duration_ms}')
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global metrics collector instance
_metrics_collector: Optional[MCPMetricsCollector] = None


def get_mcp_metrics_collector() -> MCPMetricsCollector:
    """Get or create the global MCP metrics collector.
    
    Returns:
        MCP metrics collector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MCPMetricsCollector()
    return _metrics_collector


async def init_mcp_metrics_collector(
    retention_hours: int = 24,
    enable_detailed_tracking: bool = True
) -> MCPMetricsCollector:
    """Initialize the global MCP metrics collector.
    
    Args:
        retention_hours: Hours to retain detailed metrics
        enable_detailed_tracking: Enable detailed per-invocation tracking
        
    Returns:
        Initialized MCP metrics collector
    """
    global _metrics_collector
    _metrics_collector = MCPMetricsCollector(
        retention_hours=retention_hours,
        enable_detailed_tracking=enable_detailed_tracking
    )
    await _metrics_collector.start()
    return _metrics_collector


async def shutdown_mcp_metrics_collector() -> None:
    """Shutdown the global MCP metrics collector."""
    global _metrics_collector
    if _metrics_collector:
        await _metrics_collector.stop()
        _metrics_collector = None