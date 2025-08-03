"""
Health check and status endpoints for the SocialMapper API.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict, Any
import sys
import platform

from ..config import Settings, get_settings

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
    system_info: Dict[str, Any]
    configuration: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        HealthResponse: Basic health status information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0"
    )


@router.get("/status", response_model=StatusResponse)
async def status_check(settings: Settings = Depends(get_settings)):
    """
    Detailed status endpoint with system information.
    
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
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        system_info=system_info,
        configuration=config_info
    )