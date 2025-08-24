"""Health check and status endpoints for the SocialMapper API."""

import platform
import sys
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..config import Settings, get_settings
from ..services.mcp_service import get_mcp_service

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str


class StatusResponse(BaseModel):
    """Detailed status response model."""

    status: str
    timestamp: datetime
    version: str
    system_info: dict[str, Any]
    configuration: dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint.

    Returns:
        HealthResponse: Basic health status information
    """
    return HealthResponse(status="healthy", timestamp=datetime.now(UTC), version="0.1.0")


@router.get("/status", response_model=StatusResponse)
async def status_check(settings: Settings = Depends(get_settings)):
    """Detailed status endpoint with system information.

    Args:
        settings: Application settings

    Returns:
        StatusResponse: Detailed status information
    """
    system_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
    }

    # Safe configuration info (no sensitive data)
    config_info = {
        "cors_origins": settings.cors_origins,
        "max_concurrent_jobs": settings.max_concurrent_jobs,
        "result_ttl_hours": settings.result_ttl_hours,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "has_census_api_key": bool(settings.census_api_key),
    }

    return StatusResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
        version="0.1.0",
        system_info=system_info,
        configuration=config_info,
    )


class MCPStatusResponse(BaseModel):
    """MCP service status response model."""
    
    enabled: bool
    initialized: bool
    mount_path: Optional[str] = None
    total_tools: int = 0
    available_tools: int = 0
    auth_enabled: bool = False
    rate_limit: int = 0
    stats: Optional[dict[str, Any]] = None


@router.get("/mcp/status", response_model=MCPStatusResponse)
async def mcp_status(request: Request, settings: Settings = Depends(get_settings)):
    """Get MCP service status.
    
    Args:
        request: FastAPI request object
        settings: Application settings
        
    Returns:
        MCPStatusResponse: MCP service status information
    """
    if not settings.mcp_enabled:
        return MCPStatusResponse(
            enabled=False,
            initialized=False
        )
    
    # Get MCP service from app state
    mcp_service = None
    if hasattr(request.app.state, "mcp_service"):
        mcp_service = request.app.state.mcp_service
    else:
        mcp_service = get_mcp_service()
    
    if not mcp_service:
        return MCPStatusResponse(
            enabled=True,
            initialized=False
        )
    
    # Get health status from MCP service
    health_status = mcp_service.get_health_status()
    
    return MCPStatusResponse(
        enabled=health_status.get("enabled", False),
        initialized=health_status.get("initialized", False),
        mount_path=health_status.get("mount_path"),
        total_tools=health_status.get("total_tools", 0),
        available_tools=health_status.get("available_tools", 0),
        auth_enabled=health_status.get("auth_enabled", False),
        rate_limit=health_status.get("rate_limit", 0),
        stats=health_status.get("stats")
    )
