"""Enhanced job management with prioritization and resource limits."""

import asyncio
import logging
import time
from datetime import datetime, UTC, timedelta
from typing import Dict, Optional, List, Any
from enum import Enum
from dataclasses import dataclass, field
import heapq
from collections import defaultdict

from ..models import AnalysisRequest, JobStatusEnum, ProcessingJob
from .job_manager import JobManager
from .cache_service import get_cache_service

logger = logging.getLogger(__name__)


class JobPriority(Enum):
    """Job priority levels."""
    DEMO = 100  # Highest priority for demo users
    PREMIUM = 50  # Premium users
    NORMAL = 10  # Regular users
    LOW = 1  # Low priority batch jobs


@dataclass
class JobQueueItem:
    """Priority queue item for jobs."""
    priority: int
    timestamp: float
    job_id: str
    
    def __lt__(self, other):
        # Higher priority value = higher priority
        # For same priority, earlier timestamp wins
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.timestamp < other.timestamp


@dataclass
class SessionInfo:
    """Track session resource usage."""
    session_id: str
    created_at: datetime
    job_count: int = 0
    total_processing_time: float = 0.0
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_demo: bool = False
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired (1 hour of inactivity)."""
        return (datetime.now(UTC) - self.last_activity) > timedelta(hours=1)


class EnhancedJobManager(JobManager):
    """Enhanced job manager with prioritization and resource management."""
    
    def __init__(self):
        super().__init__()
        
        # Priority queue for pending jobs
        self.job_queue: List[JobQueueItem] = []
        self.queue_lock = asyncio.Lock()
        
        # Session tracking
        self.sessions: Dict[str, SessionInfo] = {}
        self.session_lock = asyncio.Lock()
        
        # Resource limits
        self.max_jobs_per_session = 10  # Max concurrent jobs per session
        self.max_jobs_per_demo_session = 3  # Stricter limit for demo
        self.max_total_demo_jobs = 20  # Global demo job limit
        
        # Performance tracking
        self.processing_times: List[float] = []
        self.max_processing_samples = 100
        
        # Job processor task
        self._processor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the enhanced job manager."""
        await super().start()
        
        # Start job processor
        self._processor_task = asyncio.create_task(self._process_job_queue())
        
        # Start session cleanup
        asyncio.create_task(self._cleanup_sessions())
        
        logger.info("Enhanced job manager started with prioritization")
    
    async def stop(self):
        """Stop the enhanced job manager."""
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
    
    def create_job(
        self,
        request: AnalysisRequest,
        session_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        is_demo: bool = False
    ) -> str:
        """Create a new job with priority and session tracking.
        
        Args:
            request: Analysis request
            session_id: Session identifier for resource tracking
            priority: Job priority level
            is_demo: Whether this is a demo job
            
        Returns:
            Job ID
            
        Raises:
            ValueError: If resource limits exceeded
        """
        # Check resource limits
        if session_id:
            asyncio.create_task(self._check_session_limits(session_id, is_demo))
        
        if is_demo:
            # Check global demo limit
            demo_job_count = sum(
                1 for job in self.jobs.values()
                if getattr(job, "is_demo", False) and
                job.status in [JobStatusEnum.PENDING, JobStatusEnum.RUNNING]
            )
            if demo_job_count >= self.max_total_demo_jobs:
                raise ValueError("Demo service is at capacity. Please try again later.")
        
        # Create job with parent method
        job_id = super().create_job(request)
        
        # Add priority and session info to job
        job = self.jobs[job_id]
        job.priority = priority
        job.session_id = session_id
        job.is_demo = is_demo
        
        # Add to priority queue instead of direct processing
        asyncio.create_task(self._enqueue_job(job_id, priority))
        
        # Update session
        if session_id:
            asyncio.create_task(self._update_session(session_id, is_demo))
        
        return job_id
    
    async def _enqueue_job(self, job_id: str, priority: JobPriority):
        """Add job to priority queue."""
        async with self.queue_lock:
            item = JobQueueItem(
                priority=priority.value,
                timestamp=time.time(),
                job_id=job_id
            )
            heapq.heappush(self.job_queue, item)
            logger.info(f"Enqueued job {job_id} with priority {priority.name}")
    
    async def _process_job_queue(self):
        """Process jobs from priority queue."""
        while True:
            try:
                # Check if we have capacity
                running_jobs = sum(
                    1 for job in self.jobs.values()
                    if job.status == JobStatusEnum.RUNNING
                )
                
                if running_jobs >= self.executor._max_workers:
                    await asyncio.sleep(0.5)
                    continue
                
                # Get next job from queue
                async with self.queue_lock:
                    if not self.job_queue:
                        await asyncio.sleep(0.5)
                        continue
                    
                    item = heapq.heappop(self.job_queue)
                
                # Check if job still exists and is pending
                job = self.jobs.get(item.job_id)
                if not job or job.status != JobStatusEnum.PENDING:
                    continue
                
                # Check cache before processing
                cache_result = await self._check_cache(job)
                if cache_result:
                    logger.info(f"Job {item.job_id} served from cache")
                    job.status = JobStatusEnum.COMPLETED
                    job.result = cache_result
                    job.completed_at = datetime.now(UTC)
                    job.processing_time_seconds = 0.1  # Minimal time for cache hit
                    continue
                
                # Process the job
                logger.info(f"Processing job {item.job_id} from queue")
                asyncio.create_task(self._process_job_with_tracking(item.job_id))
                
                # Small delay to prevent tight loop
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in job queue processor: {e}")
                await asyncio.sleep(1)
    
    async def _process_job_with_tracking(self, job_id: str):
        """Process job with performance tracking."""
        start_time = time.time()
        
        try:
            # Process job
            await self._process_job(job_id)
            
            # Track processing time
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            # Keep only recent samples
            if len(self.processing_times) > self.max_processing_samples:
                self.processing_times = self.processing_times[-self.max_processing_samples:]
            
            # Cache successful results
            job = self.jobs.get(job_id)
            if job and job.status == JobStatusEnum.COMPLETED and job.result:
                await self._cache_result(job)
                
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
    
    async def _check_cache(self, job: ProcessingJob) -> Optional[Dict[str, Any]]:
        """Check if we have cached results for this request."""
        cache = get_cache_service()
        
        # Try to get cached POI data
        poi_data = await cache.get_poi_data(
            job.request.location,
            job.request.poi_type,
            job.request.poi_name
        )
        
        # Try to get cached census data
        census_data = await cache.get_census_data(
            job.request.location,
            job.request.census_variables
        )
        
        # If we have both, construct a result
        if poi_data and census_data:
            return {
                "poi_count": len(poi_data),
                "pois": poi_data,
                "demographics": census_data,
                "isochrone_count": 1,
                "census_units_analyzed": len(census_data),
                "metadata": {
                    "travel_time": job.request.travel_time,
                    "geographic_level": job.request.geographic_level.value,
                    "census_variables": job.request.census_variables,
                    "from_cache": True,
                },
            }
        
        return None
    
    async def _cache_result(self, job: ProcessingJob):
        """Cache job results for future use."""
        cache = get_cache_service()
        
        if not job.result:
            return
        
        # Cache POI data
        if "pois" in job.result:
            await cache.cache_poi_data(
                job.request.location,
                job.request.poi_type,
                job.request.poi_name,
                job.result["pois"]
            )
        
        # Cache census data
        if "demographics" in job.result:
            await cache.cache_census_data(
                job.request.location,
                job.request.census_variables,
                job.result["demographics"]
            )
    
    async def _check_session_limits(self, session_id: str, is_demo: bool):
        """Check if session has exceeded resource limits."""
        async with self.session_lock:
            session = self.sessions.get(session_id)
            
            if not session:
                return  # New session, no limits yet
            
            # Count active jobs for this session
            active_jobs = sum(
                1 for job in self.jobs.values()
                if getattr(job, "session_id", None) == session_id and
                job.status in [JobStatusEnum.PENDING, JobStatusEnum.RUNNING]
            )
            
            # Check limits
            limit = self.max_jobs_per_demo_session if is_demo else self.max_jobs_per_session
            if active_jobs >= limit:
                raise ValueError(f"Session has reached maximum concurrent jobs limit ({limit})")
    
    async def _update_session(self, session_id: str, is_demo: bool):
        """Update session tracking information."""
        async with self.session_lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionInfo(
                    session_id=session_id,
                    created_at=datetime.now(UTC),
                    is_demo=is_demo
                )
            
            session = self.sessions[session_id]
            session.job_count += 1
            session.last_activity = datetime.now(UTC)
    
    async def _cleanup_sessions(self):
        """Periodically clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                async with self.session_lock:
                    expired = [
                        sid for sid, session in self.sessions.items()
                        if session.is_expired
                    ]
                    
                    for sid in expired:
                        # Cancel any remaining jobs for expired session
                        for job in self.jobs.values():
                            if getattr(job, "session_id", None) == sid:
                                if job.status in [JobStatusEnum.PENDING, JobStatusEnum.RUNNING]:
                                    job.status = JobStatusEnum.FAILED
                                    job.error = "Session expired"
                        
                        del self.sessions[sid]
                        logger.info(f"Cleaned up expired session {sid}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.processing_times:
            avg_time = 0
            p95_time = 0
        else:
            sorted_times = sorted(self.processing_times)
            avg_time = sum(sorted_times) / len(sorted_times)
            p95_index = int(len(sorted_times) * 0.95)
            p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        
        # Count jobs by status
        status_counts = defaultdict(int)
        for job in self.jobs.values():
            status_counts[job.status.value] += 1
        
        # Count by priority
        priority_counts = defaultdict(int)
        async with self.queue_lock:
            for item in self.job_queue:
                if item.priority == JobPriority.DEMO.value:
                    priority_counts["demo"] += 1
                elif item.priority == JobPriority.PREMIUM.value:
                    priority_counts["premium"] += 1
                elif item.priority == JobPriority.NORMAL.value:
                    priority_counts["normal"] += 1
                else:
                    priority_counts["low"] += 1
        
        return {
            "total_jobs": len(self.jobs),
            "queued_jobs": len(self.job_queue),
            "active_sessions": len(self.sessions),
            "status_counts": dict(status_counts),
            "priority_counts": dict(priority_counts),
            "avg_processing_time": round(avg_time, 2),
            "p95_processing_time": round(p95_time, 2),
            "samples": len(self.processing_times),
        }
    
    def cleanup_abandoned_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up abandoned jobs older than specified hours.
        
        Args:
            max_age_hours: Maximum age in hours for pending/running jobs
            
        Returns:
            Number of jobs cleaned up
        """
        cleaned = 0
        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
        
        for job_id, job in list(self.jobs.items()):
            # Check if job is abandoned
            if job.status in [JobStatusEnum.PENDING, JobStatusEnum.RUNNING]:
                if job.created_at < cutoff_time:
                    job.status = JobStatusEnum.FAILED
                    job.error = "Job abandoned - exceeded maximum age"
                    job.completed_at = datetime.now(UTC)
                    cleaned += 1
                    logger.info(f"Cleaned up abandoned job {job_id}")
        
        return cleaned