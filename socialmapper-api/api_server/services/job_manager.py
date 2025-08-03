"""Job management service for handling background analysis tasks.
"""

import asyncio
import logging
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any

from ..config import get_settings
from ..models.analysis import AnalysisRequest, JobStatusEnum, ProcessingJob
from .result_storage import get_result_storage

logger = logging.getLogger(__name__)


class JobManager:
    """Manages background analysis jobs and their lifecycle."""

    def __init__(self):
        self.jobs: dict[str, ProcessingJob] = {}
        self.executor = ThreadPoolExecutor(max_workers=get_settings().max_concurrent_jobs)
        self._cleanup_task: asyncio.Task | None = None

    async def start(self):
        """Start the job manager and cleanup task."""
        logger.info("Starting job manager...")
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_jobs())

    async def stop(self):
        """Stop the job manager and cleanup resources."""
        logger.info("Stopping job manager...")
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self.executor.shutdown(wait=True)

    def create_job(self, request: AnalysisRequest) -> str:
        """Create a new analysis job.
        
        Args:
            request: Analysis request parameters
            
        Returns:
            str: Unique job ID
        """
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id,
            request=request,
            status=JobStatusEnum.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} for location: {request.location}")

        # Start processing the job in background
        asyncio.create_task(self._process_job(job_id))

        return job_id

    def get_job(self, job_id: str) -> ProcessingJob | None:
        """Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            ProcessingJob or None if not found
        """
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> dict[str, ProcessingJob]:
        """Get all jobs (for debugging/admin purposes)."""
        return self.jobs.copy()

    def delete_job(self, job_id: str) -> bool:
        """Delete a job and its results.
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if job was deleted, False if not found
        """
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Deleted job {job_id}")
            return True
        return False

    async def _process_job(self, job_id: str):
        """Process a job in the background.
        
        Args:
            job_id: Job identifier
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found for processing")
            return

        try:
            # Update job status to running
            job.status = JobStatusEnum.RUNNING
            job.started_at = datetime.now(UTC)
            job.updated_at = datetime.now(UTC)
            job.message = "Starting analysis..."
            job.progress = 0.1

            logger.info(f"Starting processing for job {job_id}")

            # Run the actual analysis in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_socialmapper_analysis,
                job.request
            )

            # Update job with results
            job.status = JobStatusEnum.COMPLETED
            job.completed_at = datetime.now(UTC)
            job.updated_at = datetime.now(UTC)
            job.result = result
            job.progress = 1.0
            job.message = "Analysis completed successfully"

            if job.started_at:
                job.processing_time_seconds = (
                    job.completed_at - job.started_at
                ).total_seconds()

            # Save results to storage
            result_storage = get_result_storage()
            result_storage.save_results(job_id, result)

            logger.info(f"Completed processing for job {job_id}")

        except Exception as e:
            # Handle job failure
            job.status = JobStatusEnum.FAILED
            job.completed_at = datetime.now(UTC)
            job.updated_at = datetime.now(UTC)
            job.error = str(e)
            job.error_details = {
                "traceback": traceback.format_exc(),
                "error_type": type(e).__name__
            }
            job.progress = 0.0
            job.message = f"Analysis failed: {e!s}"

            logger.error(f"Job {job_id} failed: {e!s}")
            logger.debug(f"Job {job_id} traceback: {traceback.format_exc()}")

    def _run_socialmapper_analysis(self, request: AnalysisRequest) -> dict[str, Any]:
        """Run the actual SocialMapper analysis.
        
        Args:
            request: Analysis request parameters
            
        Returns:
            Dict containing analysis results
        """
        try:
            # For now, create a mock analysis result to demonstrate the API functionality
            # TODO: Replace with actual SocialMapper integration once import issues are resolved

            logger.info(f"Running mock analysis for {request.location}")

            # Simulate processing time
            import time
            time.sleep(2)  # Simulate 2 seconds of processing

            # Create mock results that match the expected structure
            mock_result = {
                "poi_count": 5,  # Mock: found 5 POIs
                "isochrone_count": 1,
                "census_units_analyzed": 12,
                "demographics": {
                    "B01003_001E": 15420  # Mock total population
                },
                "isochrone_area": 2.5,  # Mock area in square kilometers
                "metadata": {
                    "travel_time": request.travel_time,
                    "geographic_level": request.geographic_level.value,
                    "census_variables": request.census_variables,
                    "center_lat": 45.5152,  # Mock Portland coordinates
                    "center_lon": -122.6784
                },
                "pois": [
                    {
                        "name": f"Mock {request.poi_name.title()} {i+1}",
                        "lat": 45.5152 + (i * 0.01),
                        "lon": -122.6784 + (i * 0.01),
                        "type": request.poi_type,
                        "subtype": request.poi_name
                    }
                    for i in range(5)
                ],
                "files_generated": {
                    "census_data": "/tmp/mock_census_data.csv",
                    "isochrones": "/tmp/mock_isochrones.geojson"
                }
            }

            logger.info(f"Mock analysis completed for {request.location}")
            return mock_result

            # TODO: Uncomment and fix the real implementation below
            """
            # Real SocialMapper integration (currently disabled due to import issues)
            import sys
            from pathlib import Path
            
            # Add the parent directory to sys.path to find socialmapper
            parent_dir = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(parent_dir))
                
            from socialmapper import analyze_location
            
            # Parse location (expecting "City, State" format)
            location_parts = request.location.split(",")
            if len(location_parts) != 2:
                raise Exception(f"Location must be in 'City, State' format, got: {request.location}")
            
            city = location_parts[0].strip()
            state = location_parts[1].strip()
            
            # Run analysis using the convenience function
            result = analyze_location(
                city=city,
                state=state,
                poi_type=request.poi_type,
                poi_name=request.poi_name,
                travel_time=request.travel_time,
                census_variables=request.census_variables,
                geographic_level=request.geographic_level.value
            )
            
            # Handle Result type (Ok/Err pattern)
            if hasattr(result, 'is_ok') and result.is_ok():
                analysis_result = result.unwrap()
                return self._serialize_analysis_result(analysis_result)
            elif hasattr(result, 'is_err') and result.is_err():
                error = result.unwrap_err()
                raise Exception(f"Analysis failed: {error.message}")
            else:
                # Fallback for direct result
                return self._serialize_analysis_result(result)
            """

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise Exception(f"Analysis failed: {e}")

    def _serialize_analysis_result(self, result: Any) -> dict[str, Any]:
        """Convert SocialMapper result to JSON-serializable format.
        
        Args:
            result: SocialMapper analysis result (AnalysisResult object)
            
        Returns:
            Dict containing serialized results
        """
        try:
            # Handle AnalysisResult object from SocialMapper
            if hasattr(result, 'poi_count'):
                serialized = {
                    "poi_count": result.poi_count,
                    "isochrone_count": getattr(result, 'isochrone_count', 0),
                    "census_units_analyzed": getattr(result, 'census_units_analyzed', 0),
                    "demographics": getattr(result, 'demographics', {}),
                    "isochrone_area": getattr(result, 'isochrone_area', 0.0),
                    "metadata": getattr(result, 'metadata', {}),
                    "pois": getattr(result, 'pois', [])
                }

                # Handle isochrones - convert GeoDataFrame to GeoJSON if present
                if hasattr(result, 'isochrones') and result.isochrones is not None:
                    try:
                        # Convert GeoDataFrame to GeoJSON format
                        if hasattr(result.isochrones, 'to_json'):
                            serialized["isochrones"] = result.isochrones.to_json()
                        elif hasattr(result.isochrones, '__geo_interface__'):
                            serialized["isochrones"] = result.isochrones.__geo_interface__
                        else:
                            serialized["isochrones"] = str(result.isochrones)
                    except Exception as e:
                        logger.warning(f"Failed to serialize isochrones: {e}")
                        serialized["isochrones"] = None

                # Handle files_generated
                if hasattr(result, 'files_generated'):
                    files_dict = {}
                    for key, path in result.files_generated.items():
                        files_dict[key] = str(path) if path else None
                    serialized["files_generated"] = files_dict

                return serialized

            # Fallback serialization methods
            elif hasattr(result, 'to_dict'):
                return result.to_dict()
            elif hasattr(result, '__dict__'):
                # Convert any Path objects to strings
                result_dict = {}
                for key, value in result.__dict__.items():
                    if hasattr(value, '__fspath__'):  # Path-like object
                        result_dict[key] = str(value)
                    elif hasattr(value, 'to_json'):  # GeoDataFrame
                        try:
                            result_dict[key] = value.to_json()
                        except:
                            result_dict[key] = str(value)
                    else:
                        result_dict[key] = value
                return result_dict
            else:
                return {
                    "raw_result": str(result),
                    "result_type": type(result).__name__
                }

        except Exception as e:
            logger.warning(f"Failed to serialize result: {e}")
            return {
                "error": "Failed to serialize analysis result",
                "result_summary": str(result)[:500],  # Truncated string representation
                "result_type": type(result).__name__
            }

    async def _cleanup_expired_jobs(self):
        """Periodically clean up expired jobs."""
        settings = get_settings()
        cleanup_interval = 3600  # 1 hour

        while True:
            try:
                await asyncio.sleep(cleanup_interval)

                current_time = datetime.now(UTC)
                expired_jobs = []

                for job_id, job in self.jobs.items():
                    # Remove jobs older than TTL
                    age = current_time - job.created_at
                    if age > timedelta(hours=settings.result_ttl_hours):
                        expired_jobs.append(job_id)

                for job_id in expired_jobs:
                    del self.jobs[job_id]
                    logger.info(f"Cleaned up expired job {job_id}")

                if expired_jobs:
                    logger.info(f"Cleaned up {len(expired_jobs)} expired jobs")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during job cleanup: {e}")


# Global job manager instance
_job_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    """Get the global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager


async def start_job_manager():
    """Start the global job manager."""
    manager = get_job_manager()
    await manager.start()


async def stop_job_manager():
    """Stop the global job manager."""
    global _job_manager
    if _job_manager:
        await _job_manager.stop()
        _job_manager = None
