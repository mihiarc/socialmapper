"""Background task scheduler for periodic cleanup of expired results.
"""

import asyncio
import logging
from datetime import UTC, datetime

from .result_storage import get_result_storage

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """Scheduler for periodic cleanup of expired results.
    
    This scheduler runs a background task that periodically cleans up
    expired analysis results from storage.
    """

    def __init__(self, interval_minutes: int = 60):
        """Initialize the cleanup scheduler.
        
        Args:
            interval_minutes: Interval between cleanup runs in minutes
        """
        self.interval_minutes = interval_minutes
        self.task: asyncio.Task | None = None
        self.is_running = False

    async def start(self):
        """Start the cleanup scheduler."""
        if self.is_running:
            logger.warning("Cleanup scheduler is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_cleanup_loop())
        logger.info(f"Cleanup scheduler started with {self.interval_minutes} minute interval")

    async def stop(self):
        """Stop the cleanup scheduler."""
        self.is_running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        logger.info("Cleanup scheduler stopped")

    async def _run_cleanup_loop(self):
        """Run the cleanup loop."""
        while self.is_running:
            try:
                # Run cleanup
                await self._run_cleanup()

                # Wait for next interval
                await asyncio.sleep(self.interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _run_cleanup(self):
        """Run the cleanup task."""
        try:
            logger.info("Running scheduled cleanup of expired results")
            start_time = datetime.now(UTC)

            # Get result storage and run cleanup
            result_storage = get_result_storage()
            cleaned_count = await asyncio.to_thread(result_storage.cleanup_expired)

            elapsed_time = (datetime.now(UTC) - start_time).total_seconds()

            if cleaned_count > 0:
                logger.info(f"Cleanup completed: removed {cleaned_count} expired results in {elapsed_time:.2f} seconds")
            else:
                logger.debug(f"Cleanup completed: no expired results found (took {elapsed_time:.2f} seconds)")

        except Exception as e:
            logger.error(f"Failed to run cleanup: {e}")


# Global instance
_cleanup_scheduler: CleanupScheduler | None = None


def get_cleanup_scheduler() -> CleanupScheduler:
    """Get the global cleanup scheduler instance."""
    global _cleanup_scheduler
    if _cleanup_scheduler is None:
        _cleanup_scheduler = CleanupScheduler()
    return _cleanup_scheduler


def init_cleanup_scheduler(interval_minutes: int = 60):
    """Initialize the global cleanup scheduler instance."""
    global _cleanup_scheduler
    _cleanup_scheduler = CleanupScheduler(interval_minutes)
    logger.info(f"Cleanup scheduler initialized with {interval_minutes} minute interval")
