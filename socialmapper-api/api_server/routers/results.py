"""Results and export endpoints for the SocialMapper API.
"""

import csv
import io
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from ..config import Settings, get_settings
from ..models import (
    AnalysisResult,
    ExportFormat,
    ExportRequest,
    ExportResponse,
    JobStatusEnum,
)
from ..services.job_manager import JobManager, get_job_manager
from ..services.result_storage import ResultStorage, get_result_storage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/results/{job_id}", response_model=AnalysisResult)
async def get_analysis_results(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
    result_storage: ResultStorage = Depends(get_result_storage)
):
    """Get the complete results of an analysis job.
    
    This endpoint retrieves the full analysis results including POI data,
    demographics, and isochrones for a completed job.
    
    Args:
        job_id: Unique job identifier
        job_manager: Job manager dependency
        result_storage: Result storage dependency
        
    Returns:
        AnalysisResult: Complete analysis results
        
    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        logger.info(f"Retrieving results for job {job_id}")

        # Get job from job manager
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Check job status
        if job.status != JobStatusEnum.COMPLETED:
            status_messages = {
                JobStatusEnum.PENDING: "Job is pending execution",
                JobStatusEnum.RUNNING: f"Job is still running (progress: {job.progress:.0%})",
                JobStatusEnum.FAILED: f"Job failed: {job.error}",
                JobStatusEnum.CANCELLED: "Job was cancelled"
            }

            status_code = 202 if job.status in [JobStatusEnum.PENDING, JobStatusEnum.RUNNING] else 422

            raise HTTPException(
                status_code=status_code,
                detail={
                    "error_code": f"JOB_{job.status.upper()}",
                    "message": status_messages.get(job.status, f"Job status: {job.status}"),
                    "progress": job.progress if job.status == JobStatusEnum.RUNNING else None,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Get full results from storage
        full_results = result_storage.get_results(job_id)
        if not full_results:
            # If not in storage, use job result
            full_results = job.result

        # Generate export URLs
        export_urls = {}
        for format in ExportFormat:
            export_urls[format] = f"/api/v1/results/{job_id}/export?format={format.value}"

        # Build response
        result = AnalysisResult(
            job_id=job.id,
            status=job.status,
            request=job.request,
            poi_count=full_results.get("poi_count") if full_results else None,
            demographics=full_results.get("demographics") if full_results else None,
            isochrones=full_results.get("isochrones") if full_results else None,
            analysis_area_km2=full_results.get("analysis_area_km2") if full_results else None,
            population_covered=full_results.get("population_covered") if full_results else None,
            processing_time_seconds=job.processing_time_seconds,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            export_urls=export_urls,
            error=job.error,
            error_details=job.error_details
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve analysis results",
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


@router.get("/results/{job_id}/export")
async def export_analysis_results(
    job_id: str,
    format: ExportFormat,
    include_isochrones: bool = True,
    include_demographics: bool = True,
    job_manager: JobManager = Depends(get_job_manager),
    result_storage: ResultStorage = Depends(get_result_storage),
    settings: Settings = Depends(get_settings)
):
    """Export analysis results in the specified format.
    
    This endpoint exports the analysis results in various formats including
    CSV, GeoJSON, Parquet, and GeoParquet.
    
    Args:
        job_id: Unique job identifier
        format: Export format
        include_isochrones: Include isochrone data in export
        include_demographics: Include demographic data in export
        job_manager: Job manager dependency
        result_storage: Result storage dependency
        settings: Application settings
        
    Returns:
        FileResponse or StreamingResponse: Exported data
        
    Raises:
        HTTPException: If job not found or export fails
    """
    try:
        logger.info(f"Exporting results for job {job_id} in {format} format")

        # Get job and verify it's completed
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        if job.status != JobStatusEnum.COMPLETED:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "JOB_NOT_COMPLETED",
                    "message": f"Job {job_id} is not completed (status: {job.status})",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Get results
        results = result_storage.get_results(job_id)
        if not results:
            results = job.result

        if not results:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "RESULTS_NOT_FOUND",
                    "message": f"Results not found for job {job_id}",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Export based on format
        if format == ExportFormat.CSV:
            return _export_csv(job_id, results, include_demographics)
        elif format == ExportFormat.GEOJSON:
            return _export_geojson(job_id, results, include_isochrones, include_demographics)
        elif format == ExportFormat.PARQUET:
            return _export_parquet(job_id, results, include_demographics)
        elif format == ExportFormat.GEOPARQUET:
            return _export_geoparquet(job_id, results, include_isochrones, include_demographics)
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_FORMAT",
                    "message": f"Unsupported export format: {format}",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export results for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "EXPORT_ERROR",
                "message": "Failed to export analysis results",
                "details": {"error": str(e)},
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


@router.post("/results/{job_id}/export", response_model=ExportResponse)
async def create_export_job(
    job_id: str,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    job_manager: JobManager = Depends(get_job_manager),
    result_storage: ResultStorage = Depends(get_result_storage),
    settings: Settings = Depends(get_settings)
):
    """Create an asynchronous export job for analysis results.
    
    This endpoint creates a background job to export large result sets
    asynchronously. Use this for large exports that may take time to process.
    
    Args:
        job_id: Unique job identifier
        request: Export request parameters
        background_tasks: FastAPI background tasks
        job_manager: Job manager dependency
        result_storage: Result storage dependency
        settings: Application settings
        
    Returns:
        ExportResponse: Export job information
        
    Raises:
        HTTPException: If job not found or export creation fails
    """
    try:
        logger.info(f"Creating export job for job {job_id}")

        # Validate source job exists and is completed
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        if job.status != JobStatusEnum.COMPLETED:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "JOB_NOT_COMPLETED",
                    "message": f"Job {job_id} is not completed (status: {job.status})",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Create export job
        export_id = f"export_{job_id}_{request.format.value}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

        # Add background task to process export
        background_tasks.add_task(
            _process_export_async,
            export_id,
            job_id,
            request,
            job_manager,
            result_storage,
            settings
        )

        # Return export job response
        response = ExportResponse(
            export_id=export_id,
            job_id=job_id,
            format=request.format,
            status=JobStatusEnum.PENDING,
            download_url=None,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            file_size_bytes=None
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create export job for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "EXPORT_CREATION_ERROR",
                "message": "Failed to create export job",
                "details": {"error": str(e)},
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


@router.delete("/results/{job_id}")
async def delete_analysis_results(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
    result_storage: ResultStorage = Depends(get_result_storage)
):
    """Delete analysis results and clean up associated data.
    
    This endpoint removes the job and its results from storage. Use this
    to clean up completed jobs and free up storage space.
    
    Args:
        job_id: Unique job identifier
        job_manager: Job manager dependency
        result_storage: Result storage dependency
        
    Returns:
        Dict: Deletion confirmation
        
    Raises:
        HTTPException: If job not found or deletion fails
    """
    try:
        logger.info(f"Deleting results for job {job_id}")

        # Check if job exists
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Delete from result storage
        result_storage.delete_results(job_id)

        # Delete from job manager
        deleted = job_manager.delete_job(job_id)

        return {
            "message": f"Results for job {job_id} deleted successfully",
            "job_id": job_id,
            "timestamp": datetime.now(UTC).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete results for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "DELETION_ERROR",
                "message": "Failed to delete analysis results",
                "details": {"error": str(e)},
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


@router.post("/results/cleanup")
async def cleanup_expired_results(
    result_storage: ResultStorage = Depends(get_result_storage)
):
    """Manually trigger cleanup of expired results.
    
    This endpoint allows administrators to manually trigger the cleanup
    of expired analysis results from storage. This is in addition to the
    automatic periodic cleanup.
    
    Args:
        result_storage: Result storage dependency
        
    Returns:
        Dict: Cleanup summary including number of cleaned results
        
    Raises:
        HTTPException: If cleanup fails
    """
    try:
        logger.info("Manual cleanup triggered")

        # Get storage stats before cleanup
        stats_before = result_storage.get_storage_stats()

        # Run cleanup
        cleaned_count = result_storage.cleanup_expired()

        # Get storage stats after cleanup
        stats_after = result_storage.get_storage_stats()

        return {
            "message": "Cleanup completed successfully",
            "cleaned_count": cleaned_count,
            "stats_before": {
                "total_jobs": stats_before.get("total_jobs", 0),
                "expired_jobs": stats_before.get("expired_jobs", 0),
                "total_size_mb": stats_before.get("total_size_mb", 0)
            },
            "stats_after": {
                "total_jobs": stats_after.get("total_jobs", 0),
                "expired_jobs": stats_after.get("expired_jobs", 0),
                "total_size_mb": stats_after.get("total_size_mb", 0)
            },
            "timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to run manual cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "CLEANUP_ERROR",
                "message": "Failed to run cleanup",
                "details": {"error": str(e)},
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


@router.get("/results/storage/stats")
async def get_storage_statistics(
    result_storage: ResultStorage = Depends(get_result_storage)
):
    """Get storage statistics for analysis results.
    
    This endpoint provides information about the current storage usage
    including total jobs, expired jobs, and storage size.
    
    Args:
        result_storage: Result storage dependency
        
    Returns:
        Dict: Storage statistics
        
    Raises:
        HTTPException: If unable to get statistics
    """
    try:
        stats = result_storage.get_storage_stats()

        return {
            "total_jobs": stats.get("total_jobs", 0),
            "expired_jobs": stats.get("expired_jobs", 0),
            "active_jobs": stats.get("total_jobs", 0) - stats.get("expired_jobs", 0),
            "total_size_bytes": stats.get("total_size_bytes", 0),
            "total_size_mb": stats.get("total_size_mb", 0),
            "storage_path": stats.get("storage_path", ""),
            "timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get storage statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "STATS_ERROR",
                "message": "Failed to get storage statistics",
                "details": {"error": str(e)},
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# Helper functions for export formats

def _export_csv(job_id: str, results: dict[str, Any], include_demographics: bool) -> StreamingResponse:
    """Export results as CSV."""
    output = io.StringIO()

    # Get demographics data
    demographics = results.get("demographics", {}) if include_demographics else {}

    # Create CSV writer
    writer = csv.writer(output)

    # Write header
    header = ["job_id", "poi_count", "analysis_area_km2", "population_covered"]
    if include_demographics:
        header.extend(demographics.keys())
    writer.writerow(header)

    # Write data row
    row = [
        job_id,
        results.get("poi_count", 0),
        results.get("analysis_area_km2", 0),
        results.get("population_covered", 0)
    ]
    if include_demographics:
        row.extend(demographics.values())
    writer.writerow(row)

    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=socialmapper_results_{job_id}.csv"
        }
    )


def _export_geojson(job_id: str, results: dict[str, Any], include_isochrones: bool, include_demographics: bool) -> Response:
    """Export results as GeoJSON."""
    geojson_data = {
        "type": "FeatureCollection",
        "features": []
    }

    # Add isochrones if requested
    if include_isochrones and "isochrones" in results:
        isochrones = results["isochrones"]
        if isinstance(isochrones, dict) and "features" in isochrones:
            geojson_data["features"].extend(isochrones["features"])

    # Add properties
    properties = {
        "job_id": job_id,
        "poi_count": results.get("poi_count", 0),
        "analysis_area_km2": results.get("analysis_area_km2", 0),
        "population_covered": results.get("population_covered", 0)
    }

    if include_demographics and "demographics" in results:
        properties["demographics"] = results["demographics"]

    # Add properties to first feature or create a new one
    if geojson_data["features"]:
        geojson_data["features"][0]["properties"].update(properties)
    else:
        # Create a point feature with properties
        geojson_data["features"].append({
            "type": "Feature",
            "properties": properties,
            "geometry": None
        })

    # Return as JSON response
    return Response(
        content=json.dumps(geojson_data, indent=2),
        media_type="application/geo+json",
        headers={
            "Content-Disposition": f"attachment; filename=socialmapper_results_{job_id}.geojson"
        }
    )


def _export_parquet(job_id: str, results: dict[str, Any], include_demographics: bool) -> Response:
    """Export results as Parquet."""
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq

        # Prepare data for DataFrame
        data = {
            "job_id": [job_id],
            "poi_count": [results.get("poi_count", 0)],
            "analysis_area_km2": [results.get("analysis_area_km2", 0)],
            "population_covered": [results.get("population_covered", 0)]
        }

        # Add demographics if requested
        if include_demographics and "demographics" in results:
            demographics = results["demographics"]
            for key, value in demographics.items():
                data[key] = [value]

        # Create DataFrame
        df = pd.DataFrame(data)

        # Convert to Parquet bytes
        output = io.BytesIO()
        df.to_parquet(output, engine='pyarrow', compression='snappy', index=False)
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=socialmapper_results_{job_id}.parquet"
            }
        )
    except ImportError as e:
        logger.warning(f"Parquet export requires pandas and pyarrow: {e}")
        return Response(
            content=b"Parquet export requires pandas and pyarrow to be installed",
            media_type="text/plain",
            status_code=501
        )


def _export_geoparquet(job_id: str, results: dict[str, Any], include_isochrones: bool, include_demographics: bool) -> Response:
    """Export results as GeoParquet."""
    try:
        import geopandas as gpd
        import pandas as pd
        from shapely.geometry import shape

        # Check if we have isochrones
        if not include_isochrones or "isochrones" not in results:
            # Fall back to regular parquet if no geometry
            return _export_parquet(job_id, results, include_demographics)

        # Extract isochrone features
        isochrones = results.get("isochrones", {})
        features = isochrones.get("features", [])

        if not features:
            # No features, fall back to regular parquet
            return _export_parquet(job_id, results, include_demographics)

        # Convert features to GeoDataFrame
        geometries = []
        properties_list = []

        for feature in features:
            if feature.get("geometry"):
                geometries.append(shape(feature["geometry"]))
                props = feature.get("properties", {})
                props["job_id"] = job_id
                props["poi_count"] = results.get("poi_count", 0)
                props["analysis_area_km2"] = results.get("analysis_area_km2", 0)
                props["population_covered"] = results.get("population_covered", 0)

                # Add demographics if requested
                if include_demographics and "demographics" in results:
                    props.update(results["demographics"])

                properties_list.append(props)

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs="EPSG:4326")

        # Convert to GeoParquet bytes
        output = io.BytesIO()
        gdf.to_parquet(output, compression='snappy', index=False)
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=socialmapper_results_{job_id}.geoparquet"
            }
        )
    except ImportError as e:
        logger.warning(f"GeoParquet export requires geopandas: {e}")
        return Response(
            content=b"GeoParquet export requires geopandas to be installed",
            media_type="text/plain",
            status_code=501
        )


async def _process_export_async(
    export_id: str,
    job_id: str,
    request: ExportRequest,
    job_manager: JobManager,
    result_storage: ResultStorage,
    settings: Settings
):
    """Process export asynchronously in the background."""
    try:
        logger.info(f"Processing export {export_id} for job {job_id}")

        # Get results
        results = result_storage.get_results(job_id)
        if not results:
            job = job_manager.get_job(job_id)
            results = job.result if job else None

        if not results:
            logger.error(f"No results found for job {job_id}")
            return

        # Process export based on format
        # This is a simplified implementation
        # In a real system, you would save the export to a file storage service
        # and update the export job status

        logger.info(f"Export {export_id} completed successfully")

    except Exception as e:
        logger.error(f"Failed to process export {export_id}: {e}")
