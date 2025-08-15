"""WebSocket endpoints for real-time job progress tracking."""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime, UTC

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from ..services.job_manager import get_job_manager, JobManager
from ..models import JobStatusEnum

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Map job_id to set of connected websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map websocket to set of job_ids it's subscribed to
        self.connection_jobs: Dict[WebSocket, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        async with self._lock:
            # Add to job connections
            if job_id not in self.active_connections:
                self.active_connections[job_id] = set()
            self.active_connections[job_id].add(websocket)
            
            # Track jobs per connection
            if websocket not in self.connection_jobs:
                self.connection_jobs[websocket] = set()
            self.connection_jobs[websocket].add(job_id)
        
        logger.info(f"WebSocket connected for job {job_id}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            # Get all jobs this connection was subscribed to
            job_ids = self.connection_jobs.get(websocket, set())
            
            # Remove from all job connections
            for job_id in job_ids:
                if job_id in self.active_connections:
                    self.active_connections[job_id].discard(websocket)
                    # Clean up empty job entries
                    if not self.active_connections[job_id]:
                        del self.active_connections[job_id]
            
            # Remove connection tracking
            if websocket in self.connection_jobs:
                del self.connection_jobs[websocket]
        
        logger.info(f"WebSocket disconnected, was subscribed to {len(job_ids)} jobs")
    
    async def send_job_update(self, job_id: str, message: dict):
        """Send update to all connections subscribed to a job."""
        async with self._lock:
            connections = self.active_connections.get(job_id, set()).copy()
        
        if not connections:
            return
        
        # Send to all connected clients
        disconnected = []
        for connection in connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error sending update to websocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_to_job(self, job_id: str, event_type: str, data: dict):
        """Broadcast an event to all connections for a job."""
        message = {
            "type": event_type,
            "job_id": job_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": data
        }
        await self.send_job_update(job_id, message)
    
    def get_connection_count(self, job_id: str) -> int:
        """Get number of active connections for a job."""
        return len(self.active_connections.get(job_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return len(self.connection_jobs)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_updates(
    websocket: WebSocket,
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """WebSocket endpoint for real-time job progress updates.
    
    Clients can connect to this endpoint to receive real-time updates
    about job progress, status changes, and completion notifications.
    
    Message format:
    {
        "type": "status_update" | "progress" | "completed" | "failed" | "log",
        "job_id": "job-uuid",
        "timestamp": "ISO-8601 timestamp",
        "data": {
            // Event-specific data
        }
    }
    """
    # Validate job exists
    job = job_manager.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason=f"Job {job_id} not found")
        return
    
    # Accept connection
    await manager.connect(websocket, job_id)
    
    try:
        # Send initial status
        await manager.broadcast_to_job(job_id, "status_update", {
            "status": job.status.value,
            "progress": job.progress,
            "message": job.message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
        })
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for any message from client (ping/pong)
                # Use timeout to periodically check job status
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=2.0  # Check every 2 seconds
                )
                
                # Handle client messages (e.g., ping)
                if message == "ping":
                    await websocket.send_text("pong")
                
            except asyncio.TimeoutError:
                # Check job status and send update if changed
                current_job = job_manager.get_job(job_id)
                if current_job:
                    # Send progress updates
                    if current_job.progress != job.progress or current_job.status != job.status:
                        await manager.broadcast_to_job(job_id, "progress", {
                            "status": current_job.status.value,
                            "progress": current_job.progress,
                            "message": current_job.message,
                        })
                        job = current_job
                    
                    # Send completion notification
                    if current_job.status == JobStatusEnum.COMPLETED:
                        await manager.broadcast_to_job(job_id, "completed", {
                            "result_summary": {
                                "poi_count": current_job.result.get("poi_count") if current_job.result else 0,
                                "processing_time": current_job.processing_time_seconds,
                            },
                            "completed_at": current_job.completed_at.isoformat() if current_job.completed_at else None,
                        })
                        break
                    
                    # Send failure notification
                    elif current_job.status == JobStatusEnum.FAILED:
                        await manager.broadcast_to_job(job_id, "failed", {
                            "error": current_job.error,
                            "error_details": current_job.error_details,
                        })
                        break
                else:
                    # Job no longer exists
                    await websocket.close(code=4004, reason="Job no longer exists")
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        await manager.disconnect(websocket)


@router.websocket("/ws/jobs")
async def websocket_all_jobs(
    websocket: WebSocket,
    job_manager: JobManager = Depends(get_job_manager)
):
    """WebSocket endpoint for monitoring all jobs (admin/dashboard use).
    
    Provides real-time updates for all active jobs in the system.
    Useful for admin dashboards and monitoring interfaces.
    """
    await websocket.accept()
    
    try:
        # Send initial job list
        jobs = job_manager.get_all_jobs()
        await websocket.send_json({
            "type": "job_list",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {
                "total_jobs": len(jobs),
                "jobs": [
                    {
                        "job_id": job_id,
                        "status": job.status.value,
                        "progress": job.progress,
                        "location": job.request.location,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                    }
                    for job_id, job in jobs.items()
                ]
            }
        })
        
        # Keep connection alive and send updates
        while True:
            try:
                # Wait for messages or timeout
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=5.0  # Check every 5 seconds
                )
                
                if message == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send periodic updates about active jobs
                jobs = job_manager.get_all_jobs()
                active_jobs = [
                    job for job in jobs.values()
                    if job.status in [JobStatusEnum.PENDING, JobStatusEnum.RUNNING]
                ]
                
                if active_jobs:
                    await websocket.send_json({
                        "type": "active_jobs_update",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "data": {
                            "active_count": len(active_jobs),
                            "jobs": [
                                {
                                    "job_id": job.id,
                                    "status": job.status.value,
                                    "progress": job.progress,
                                    "message": job.message,
                                }
                                for job in active_jobs
                            ]
                        }
                    })
                    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for all jobs monitor")
    except Exception as e:
        logger.error(f"WebSocket error for all jobs monitor: {e}")


# Export the connection manager for use in job updates
def get_websocket_manager() -> ConnectionManager:
    """Get the global WebSocket connection manager."""
    return manager