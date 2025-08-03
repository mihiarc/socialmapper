"""Analysis endpoints for the SocialMapper API.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..models import (
    AnalysisRequest,  # Backward compatibility alias
    AnalysisResponse,
    AnalysisResult,
    JobStatus,
    JobStatusEnum,
)
from ..services.job_manager import JobManager, get_job_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis/location", response_model=AnalysisResponse)
async def submit_location_analysis(
    request: AnalysisRequest,
    job_manager: JobManager = Depends(get_job_manager),
    settings: Settings = Depends(get_settings)
):
    """Submit a location-based accessibility analysis request.
    
    This endpoint accepts analysis parameters and returns a job ID for tracking
    the analysis progress. The analysis runs in the background and results can
    be retrieved using the job status and results endpoints.
    
    Args:
        request: Analysis request parameters
        job_manager: Job manager dependency
        settings: Application settings
        
    Returns:
        AnalysisResponse: Job submission confirmation with job ID
        
    Raises:
        HTTPException: If request validation fails or system error occurs
    """
    try:
        logger.info(f"Received analysis request for location: {request.location}")

        # Create and start the background job
        job_id = job_manager.create_job(request)

        # Return job submission response
        response = AnalysisResponse(
            job_id=job_id,
            status=JobStatusEnum.PENDING,
            created_at=job_manager.get_job(job_id).created_at,
            message="Analysis job submitted successfully"
        )

        logger.info(f"Created analysis job {job_id}")
        return response

    except ValueError as e:
        logger.warning(f"Invalid request parameters: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "INVALID_REQUEST",
                "message": f"Invalid request parameters: {e!s}",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    except Exception as e:
        logger.error(f"Failed to submit analysis job: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to submit analysis job",
                "details": {"error": str(e)},
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@router.get("/analysis/{job_id}/status", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get the current status of an analysis job.
    
    Args:
        job_id: Unique job identifier
        job_manager: Job manager dependency
        
    Returns:
        JobStatus: Current job status and progress information
        
    Raises:
        HTTPException: If job not found
    """
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )

        return JobStatus(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            created_at=job.created_at,
            started_at=job.started_at,
            updated_at=job.updated_at,
            estimated_completion=None,  # TODO: Implement estimation logic
            error=job.error
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve job status",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@router.get("/analysis/{job_id}/result", response_model=AnalysisResult)
async def get_analysis_result(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get the complete results of a completed analysis job.
    
    Args:
        job_id: Unique job identifier
        job_manager: Job manager dependency
        
    Returns:
        AnalysisResult: Complete analysis results
        
    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )

        if job.status == JobStatusEnum.PENDING:
            raise HTTPException(
                status_code=202,
                detail={
                    "error_code": "JOB_PENDING",
                    "message": f"Job {job_id} is still pending",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )
        elif job.status == JobStatusEnum.RUNNING:
            raise HTTPException(
                status_code=202,
                detail={
                    "error_code": "JOB_RUNNING",
                    "message": f"Job {job_id} is still running",
                    "progress": job.progress,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )
        elif job.status == JobStatusEnum.FAILED:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "JOB_FAILED",
                    "message": f"Job {job_id} failed: {job.error}",
                    "details": job.error_details,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
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
            export_urls=None,  # TODO: Implement export URL generation
            error=job.error,
            error_details=job.error_details
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
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@router.delete("/analysis/{job_id}")
async def delete_analysis_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Delete an analysis job and its results.
    
    Args:
        job_id: Unique job identifier
        job_manager: Job manager dependency
        
    Returns:
        Dict: Deletion confirmation
        
    Raises:
        HTTPException: If job not found
    """
    try:
        deleted = job_manager.delete_job(job_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )

        return {
            "message": f"Job {job_id} deleted successfully",
            "job_id": job_id,
            "timestamp": "2024-01-01T00:00:00Z"
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
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@router.get("/analysis/jobs")
async def list_all_jobs(
    job_manager: JobManager = Depends(get_job_manager)
):
    """List all jobs (for debugging/admin purposes).
    
    Args:
        job_manager: Job manager dependency
        
    Returns:
        Dict: List of all jobs with their status
    """
    try:
        jobs = job_manager.get_all_jobs()

        job_summaries = {}
        for job_id, job in jobs.items():
            job_summaries[job_id] = {
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "location": job.request.location,
                "poi_type": job.request.poi_type,
                "poi_name": job.request.poi_name
            }

        return {
            "total_jobs": len(jobs),
            "jobs": job_summaries,
            "timestamp": "2024-01-01T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list jobs",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
