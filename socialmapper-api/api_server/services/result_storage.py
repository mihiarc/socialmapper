"""Result storage service for managing analysis results.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ResultStorage:
    """Service for storing and retrieving analysis results.
    
    This service manages the storage of completed analysis results,
    providing methods to save, retrieve, and clean up result data.
    """

    def __init__(self, storage_path: str = "./results", ttl_hours: int = 24):
        """Initialize the result storage service.
        
        Args:
            storage_path: Directory path for storing results
            ttl_hours: Time-to-live for results in hours
        """
        self.storage_path = Path(storage_path)
        self.ttl_hours = ttl_hours

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"ResultStorage initialized with path: {self.storage_path}")

    def save_results(self, job_id: str, results: dict[str, Any]) -> bool:
        """Save analysis results to storage.
        
        Args:
            job_id: Unique job identifier
            results: Analysis results to save
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create job-specific directory
            job_dir = self.storage_path / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Save main results
            results_file = job_dir / "results.json"
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2, default=str)

            # Save metadata
            metadata = {
                "job_id": job_id,
                "saved_at": datetime.now(UTC).isoformat(),
                "expires_at": (datetime.now(UTC) + timedelta(hours=self.ttl_hours)).isoformat(),
                "size_bytes": results_file.stat().st_size
            }

            metadata_file = job_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Saved results for job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save results for job {job_id}: {e}")
            return False

    def get_results(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve analysis results from storage.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Optional[Dict[str, Any]]: Results if found, None otherwise
        """
        try:
            results_file = self.storage_path / job_id / "results.json"

            if not results_file.exists():
                logger.debug(f"Results not found for job {job_id}")
                return None

            # Check if results have expired
            metadata_file = self.storage_path / job_id / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)

                expires_at = datetime.fromisoformat(metadata["expires_at"])
                if datetime.now(UTC) > expires_at:
                    logger.info(f"Results for job {job_id} have expired")
                    self.delete_results(job_id)
                    return None

            # Load and return results
            with open(results_file) as f:
                results = json.load(f)

            logger.debug(f"Retrieved results for job {job_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to retrieve results for job {job_id}: {e}")
            return None

    def delete_results(self, job_id: str) -> bool:
        """Delete analysis results from storage.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            job_dir = self.storage_path / job_id

            if not job_dir.exists():
                logger.debug(f"No results to delete for job {job_id}")
                return True

            # Remove all files in job directory
            for file in job_dir.iterdir():
                file.unlink()

            # Remove job directory
            job_dir.rmdir()

            logger.info(f"Deleted results for job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete results for job {job_id}: {e}")
            return False

    def cleanup_expired(self) -> int:
        """Clean up expired results from storage.
        
        Returns:
            int: Number of expired results cleaned up
        """
        try:
            cleaned = 0

            for job_dir in self.storage_path.iterdir():
                if not job_dir.is_dir():
                    continue

                metadata_file = job_dir / "metadata.json"
                if not metadata_file.exists():
                    continue

                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)

                    expires_at = datetime.fromisoformat(metadata["expires_at"])
                    if datetime.now(UTC) > expires_at:
                        if self.delete_results(job_dir.name):
                            cleaned += 1

                except Exception as e:
                    logger.error(f"Error checking expiration for {job_dir.name}: {e}")

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired results")

            return cleaned

        except Exception as e:
            logger.error(f"Failed to cleanup expired results: {e}")
            return 0

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dict[str, Any]: Storage statistics
        """
        try:
            total_size = 0
            job_count = 0
            expired_count = 0

            for job_dir in self.storage_path.iterdir():
                if not job_dir.is_dir():
                    continue

                job_count += 1

                # Calculate size
                for file in job_dir.iterdir():
                    total_size += file.stat().st_size

                # Check expiration
                metadata_file = job_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)

                        expires_at = datetime.fromisoformat(metadata["expires_at"])
                        if datetime.now(UTC) > expires_at:
                            expired_count += 1

                    except Exception:
                        pass

            return {
                "total_jobs": job_count,
                "expired_jobs": expired_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": str(self.storage_path)
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "error": str(e),
                "storage_path": str(self.storage_path)
            }


# Global instance
_result_storage: ResultStorage | None = None


def get_result_storage() -> ResultStorage:
    """Get the global result storage instance."""
    global _result_storage
    if _result_storage is None:
        _result_storage = ResultStorage()
    return _result_storage


def init_result_storage(storage_path: str = "./results", ttl_hours: int = 24):
    """Initialize the global result storage instance."""
    global _result_storage
    _result_storage = ResultStorage(storage_path, ttl_hours)
    logger.info("Result storage initialized")
