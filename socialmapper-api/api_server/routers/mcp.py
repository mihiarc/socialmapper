"""MCP-specific API routes for metrics and monitoring."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from ..services.mcp_metrics import get_mcp_metrics_collector
from ..services.mcp_service import get_mcp_service

router = APIRouter()


@router.get("/metrics/summary")
async def get_mcp_metrics_summary(request: Request) -> Dict[str, Any]:
    """Get a summary of MCP metrics.
    
    Returns comprehensive metrics about MCP tool usage, client statistics,
    and performance data.
    """
    collector = get_mcp_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="MCP metrics collector not initialized")
    
    return collector.get_summary()


@router.get("/metrics/time-series")
async def get_mcp_time_series(
    granularity: str = "minute",
    hours: int = 1
) -> list[Dict[str, Any]]:
    """Get time-series MCP metrics data.
    
    Args:
        granularity: Data granularity ("minute" or "hour")
        hours: Number of hours of data to return (max 24)
    
    Returns:
        List of time-series data points with request counts, errors, and durations
    """
    if granularity not in ["minute", "hour"]:
        raise HTTPException(status_code=400, detail="Granularity must be 'minute' or 'hour'")
    
    if hours < 1 or hours > 24:
        raise HTTPException(status_code=400, detail="Hours must be between 1 and 24")
    
    collector = get_mcp_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="MCP metrics collector not initialized")
    
    return collector.get_time_series(granularity=granularity, hours=hours)


@router.get("/metrics/prometheus")
async def get_mcp_metrics_prometheus() -> Response:
    """Export MCP metrics in Prometheus format.
    
    Returns metrics in Prometheus text format for scraping by Prometheus server.
    """
    collector = get_mcp_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="MCP metrics collector not initialized")
    
    metrics_text = collector.export_metrics(format="prometheus")
    return PlainTextResponse(content=metrics_text, media_type="text/plain; version=0.0.4")


@router.get("/metrics/tool/{tool_name}")
async def get_tool_metrics(tool_name: str) -> Dict[str, Any]:
    """Get metrics for a specific MCP tool.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Detailed metrics for the specified tool
    """
    collector = get_mcp_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="MCP metrics collector not initialized")
    
    metrics = collector.get_tool_metrics(tool_name)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No metrics found for tool: {tool_name}")
    
    return {
        "tool_name": metrics.tool_name,
        "total_invocations": metrics.total_invocations,
        "successful_invocations": metrics.successful_invocations,
        "failed_invocations": metrics.failed_invocations,
        "error_rate": metrics.error_rate,
        "avg_duration_ms": metrics.avg_duration_ms,
        "min_duration_ms": metrics.min_duration_ms,
        "max_duration_ms": metrics.max_duration_ms,
        "median_duration_ms": metrics.median_duration_ms,
        "p95_duration_ms": metrics.p95_duration_ms,
        "p99_duration_ms": metrics.p99_duration_ms,
        "unique_clients": len(metrics.unique_clients),
        "error_types": dict(metrics.error_types)
    }


@router.get("/metrics/client/{client_id}")
async def get_client_metrics(client_id: str) -> Dict[str, Any]:
    """Get metrics for a specific MCP client.
    
    Args:
        client_id: Client identifier
    
    Returns:
        Usage statistics for the specified client
    """
    collector = get_mcp_metrics_collector()
    if not collector:
        raise HTTPException(status_code=503, detail="MCP metrics collector not initialized")
    
    stats = collector.get_client_stats(client_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"No metrics found for client: {client_id}")
    
    return {
        "client_id": stats.client_id,
        "first_seen": stats.first_seen.isoformat(),
        "last_seen": stats.last_seen.isoformat(),
        "total_requests": stats.total_requests,
        "successful_requests": stats.successful_requests,
        "failed_requests": stats.failed_requests,
        "success_rate": stats.successful_requests / stats.total_requests if stats.total_requests > 0 else 0,
        "avg_duration_ms": stats.total_duration_ms / stats.total_requests if stats.total_requests > 0 else 0,
        "tools_used": list(stats.tools_used),
        "error_types": dict(stats.error_types),
        "hourly_pattern": dict(stats.hourly_requests)
    }


@router.get("/health")
async def get_mcp_health(request: Request) -> Dict[str, Any]:
    """Get MCP service health status.
    
    Returns comprehensive health information about the MCP service,
    including configuration, tool availability, and current metrics.
    """
    mcp_service = get_mcp_service()
    if not mcp_service:
        return {
            "status": "disabled",
            "message": "MCP service is not enabled"
        }
    
    health_status = mcp_service.get_health_status()
    
    # Add current metrics if available
    collector = get_mcp_metrics_collector()
    if collector:
        summary = collector.get_summary()
        health_status["current_metrics"] = {
            "current_rpm": summary["aggregate"]["current_rpm"],
            "total_invocations": summary["aggregate"]["total_invocations"],
            "error_rate": summary["aggregate"]["error_rate"],
            "uptime_hours": summary["aggregate"]["uptime_hours"]
        }
    
    health_status["status"] = "healthy" if health_status["initialized"] else "initializing"
    
    return health_status


@router.get("/tools")
async def list_mcp_tools(request: Request) -> Dict[str, Any]:
    """List available MCP tools.
    
    Returns a list of all registered MCP tools with their metadata
    and current status.
    """
    mcp_service = get_mcp_service()
    if not mcp_service:
        raise HTTPException(status_code=503, detail="MCP service not initialized")
    
    tools = []
    for tool in mcp_service.tool_registry.get_available_tools():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "endpoint": tool.endpoint,
            "category": tool.category,
            "status": tool.status.value,
            "requires_auth": tool.requires_auth,
            "rate_limit": tool.rate_limit,
            "cache_ttl": tool.cache_ttl,
            "usage_count": tool.usage_count,
            "error_count": tool.error_count,
            "avg_response_time": tool.avg_response_time,
            "last_used": tool.last_used.isoformat() if tool.last_used else None
        })
    
    return {
        "total_tools": len(tools),
        "tools": tools
    }


@router.get("/tools/{tool_name}")
async def get_tool_details(tool_name: str, request: Request) -> Dict[str, Any]:
    """Get detailed information about a specific MCP tool.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Detailed tool information including metadata and usage statistics
    """
    mcp_service = get_mcp_service()
    if not mcp_service:
        raise HTTPException(status_code=503, detail="MCP service not initialized")
    
    tool = mcp_service.tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    # Get metrics if available
    metrics = None
    collector = get_mcp_metrics_collector()
    if collector:
        tool_metrics = collector.get_tool_metrics(tool_name)
        if tool_metrics:
            metrics = {
                "total_invocations": tool_metrics.total_invocations,
                "success_rate": (
                    tool_metrics.successful_invocations / tool_metrics.total_invocations
                    if tool_metrics.total_invocations > 0 else 0
                ),
                "avg_duration_ms": tool_metrics.avg_duration_ms,
                "p95_duration_ms": tool_metrics.p95_duration_ms,
                "unique_clients": len(tool_metrics.unique_clients)
            }
    
    return {
        "tool": {
            "name": tool.name,
            "description": tool.description,
            "endpoint": tool.endpoint,
            "method": tool.method,
            "category": tool.category,
            "operation_id": tool.operation_id,
            "tag": tool.tag,
            "requires_auth": tool.requires_auth,
            "rate_limit": tool.rate_limit,
            "timeout": tool.timeout,
            "cache_ttl": tool.cache_ttl,
            "status": tool.status.value,
            "usage_count": tool.usage_count,
            "error_count": tool.error_count,
            "avg_response_time": tool.avg_response_time,
            "last_used": tool.last_used.isoformat() if tool.last_used else None
        },
        "metrics": metrics
    }