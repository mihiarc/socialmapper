"""Optimized analysis endpoints with enhanced job management."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request

from ..config import Settings, get_settings
from ..models import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisResult,
    JobStatus,
    JobStatusEnum,
)
from ..services.enhanced_job_manager import EnhancedJobManager, JobPriority

logger = logging.getLogger(__name__)
router = APIRouter()


def get_job_manager(request: Request) -> EnhancedJobManager:
    """Get job manager from app state."""
    if hasattr(request.app.state, "job_manager"):
        return request.app.state.job_manager
    # Fallback for testing
    return EnhancedJobManager()


@router.post("/analysis/location", response_model=AnalysisResponse)
async def submit_location_analysis(
    analysis_request: AnalysisRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    x_session_id: Optional[str] = Header(None),
    x_demo_mode: Optional[str] = Header(None),
    x_priority: Optional[str] = Header(None),
):
    """Submit a location-based accessibility analysis request with prioritization.

    This endpoint accepts analysis parameters and returns a job ID for tracking
    the analysis progress. Jobs are prioritized based on demo mode and custom headers.

    Args:
        analysis_request: Analysis request parameters
        request: FastAPI request object
        settings: Application settings
        x_session_id: Session identifier for resource tracking
        x_demo_mode: Demo mode flag ("true" for demo)
        x_priority: Custom priority level ("high", "normal", "low")

    Returns:
        AnalysisResponse: Job submission confirmation with job ID

    Raises:
        HTTPException: If request validation fails or resource limits exceeded
    """
    try:
        logger.info(f"Received analysis request for location: {analysis_request.location}")
        
        # Get job manager
        job_manager = get_job_manager(request)
        
        # Determine priority
        is_demo = x_demo_mode == "true" or settings.demo_mode_enabled
        
        if is_demo:
            priority = JobPriority.DEMO
        elif x_priority == "high":
            priority = JobPriority.PREMIUM
        elif x_priority == "low":
            priority = JobPriority.LOW
        else:
            priority = JobPriority.NORMAL
        
        # Create and start the background job
        job_id = job_manager.create_job(
            request=analysis_request,
            session_id=x_session_id,
            priority=priority,
            is_demo=is_demo
        )

        # Return job submission response
        job = job_manager.get_job(job_id)
        response = AnalysisResponse(
            job_id=job_id,
            status=JobStatusEnum.PENDING,
            created_at=job.created_at,
            message="Analysis job submitted successfully",
        )

        logger.info(f"Created analysis job {job_id} with priority {priority.name}")
        return response

    except ValueError as e:
        logger.warning(f"Invalid request or resource limit: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "INVALID_REQUEST",
                "message": str(e),
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )
    except Exception as e:
        logger.error(f"Failed to submit analysis job: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to submit analysis job",
                "details": {"error": str(e)},
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )


@router.get("/analysis/{job_id}/status", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    request: Request,
    include_performance: bool = False
):
    """Get the current status of an analysis job.

    Args:
        job_id: Unique job identifier
        request: FastAPI request object
        include_performance: Include performance metrics

    Returns:
        JobStatus: Current job status and progress information

    Raises:
        HTTPException: If job not found
    """
    try:
        job_manager = get_job_manager(request)
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": "2025-01-01T00:00:00Z",
                },
            )

        status = JobStatus(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            created_at=job.created_at,
            started_at=job.started_at,
            updated_at=job.updated_at,
            estimated_completion=None,
            error=job.error,
        )
        
        # Add performance metrics if requested
        if include_performance and hasattr(job_manager, 'get_performance_stats'):
            status.performance_stats = job_manager.get_performance_stats()
        
        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve job status",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )


@router.get("/analysis/{job_id}/result", response_model=AnalysisResult)
async def get_analysis_result(
    job_id: str,
    request: Request
):
    """Get the complete results of a completed analysis job.

    Args:
        job_id: Unique job identifier
        request: FastAPI request object

    Returns:
        AnalysisResult: Complete analysis results

    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        job_manager = get_job_manager(request)
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": "2025-01-01T00:00:00Z",
                },
            )

        if job.status == JobStatusEnum.PENDING:
            raise HTTPException(
                status_code=202,
                detail={
                    "error_code": "JOB_PENDING",
                    "message": f"Job {job_id} is still pending",
                    "timestamp": "2025-01-01T00:00:00Z",
                },
            )
        elif job.status == JobStatusEnum.RUNNING:
            raise HTTPException(
                status_code=202,
                detail={
                    "error_code": "JOB_RUNNING",
                    "message": f"Job {job_id} is still running",
                    "progress": job.progress,
                    "timestamp": "2025-01-01T00:00:00Z",
                },
            )
        elif job.status == JobStatusEnum.FAILED:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "JOB_FAILED",
                    "message": f"Job {job_id} failed: {job.error}",
                    "details": job.error_details,
                    "timestamp": "2025-01-01T00:00:00Z",
                },
            )

        # Job completed successfully
        result = AnalysisResult(
            job_id=job.id,
            status=job.status,
            request=job.request,
            poi_count=job.result.get("poi_count") if job.result else None,
            demographics=job.result.get("demographics") if job.result else None,
            isochrones=job.result.get("isochrones") if job.result else None,
            processing_time_seconds=job.processing_time_seconds,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            export_urls=None,
            error=job.error,
            error_details=job.error_details,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis result for {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve analysis result",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )


@router.delete("/analysis/{job_id}")
async def delete_analysis_job(
    job_id: str,
    request: Request
):
    """Delete an analysis job and its results.

    Args:
        job_id: Unique job identifier
        request: FastAPI request object

    Returns:
        Dict: Deletion confirmation

    Raises:
        HTTPException: If job not found
    """
    try:
        job_manager = get_job_manager(request)
        deleted = job_manager.delete_job(job_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": "2025-01-01T00:00:00Z",
                },
            )

        return {
            "message": f"Job {job_id} deleted successfully",
            "job_id": job_id,
            "timestamp": "2025-01-01T00:00:00Z",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to delete job",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )


@router.get("/analysis/jobs")
async def list_all_jobs(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    session_id: Optional[str] = Header(None),
):
    """List jobs with pagination and filtering.

    Args:
        request: FastAPI request object
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        status: Filter by job status
        session_id: Filter by session ID

    Returns:
        Dict: Paginated list of jobs
    """
    try:
        job_manager = get_job_manager(request)
        jobs = job_manager.get_all_jobs()

        # Apply filters
        filtered_jobs = {}
        for job_id, job in jobs.items():
            # Status filter
            if status and job.status.value != status:
                continue
            
            # Session filter
            if session_id and getattr(job, "session_id", None) != session_id:
                continue
            
            filtered_jobs[job_id] = job

        # Apply pagination
        job_items = list(filtered_jobs.items())
        paginated_jobs = job_items[offset:offset + limit]

        job_summaries = {}
        for job_id, job in paginated_jobs:
            job_summaries[job_id] = {
                "status": job.status.value,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "location": job.request.location,
                "poi_type": job.request.poi_type,
                "poi_name": job.request.poi_name,
                "priority": getattr(job, "priority", JobPriority.NORMAL).name,
                "is_demo": getattr(job, "is_demo", False),
            }

        return {
            "total_jobs": len(filtered_jobs),
            "limit": limit,
            "offset": offset,
            "jobs": job_summaries,
            "timestamp": "2025-01-01T00:00:00Z",
        }

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list jobs",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )


@router.get("/analysis/performance")
async def get_performance_metrics(
    request: Request
):
    """Get system performance metrics.

    Args:
        request: FastAPI request object

    Returns:
        Dict: Performance statistics
    """
    try:
        job_manager = get_job_manager(request)
        
        if hasattr(job_manager, 'get_performance_stats'):
            stats = job_manager.get_performance_stats()
        else:
            stats = {"message": "Performance stats not available"}
        
        # Add cache stats if available
        from ..services.cache_service import get_cache_service
        cache_service = get_cache_service()
        if cache_service.enabled:
            cache_stats = await cache_service.get_cache_stats()
            stats["cache"] = cache_stats
        
        return {
            "performance": stats,
            "timestamp": "2025-01-01T00:00:00Z",
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get performance metrics",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )