"""Test the cleanup functionality for expired results.
"""

import asyncio
import json
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api_server.services.cleanup_scheduler import CleanupScheduler
from api_server.services.result_storage import ResultStorage


@pytest.fixture
def temp_storage_path():
    """Create a temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_result_storage_ttl(temp_storage_path):
    """Test that expired results are properly cleaned up."""
    # Create storage with 1 hour TTL
    storage = ResultStorage(storage_path=temp_storage_path, ttl_hours=1)

    # Save a result
    job_id = "test_job_123"
    results = {
        "poi_count": 5,
        "demographics": {"population": 1000},
        "analysis_area_km2": 10.5
    }

    assert storage.save_results(job_id, results)

    # Verify result exists
    retrieved = storage.get_results(job_id)
    assert retrieved is not None
    assert retrieved["poi_count"] == 5

    # Manually expire the result by modifying metadata
    metadata_file = Path(temp_storage_path) / job_id / "metadata.json"
    with open(metadata_file) as f:
        metadata = json.load(f)

    # Set expiration to past
    metadata["expires_at"] = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

    with open(metadata_file, "w") as f:
        json.dump(metadata, f)

    # Try to get expired result - should return None and delete it
    retrieved = storage.get_results(job_id)
    assert retrieved is None

    # Verify files are deleted
    assert not (Path(temp_storage_path) / job_id).exists()


def test_cleanup_expired(temp_storage_path):
    """Test bulk cleanup of expired results."""
    storage = ResultStorage(storage_path=temp_storage_path, ttl_hours=24)

    # Create multiple results
    for i in range(5):
        job_id = f"job_{i}"
        results = {"poi_count": i, "data": f"test_{i}"}
        storage.save_results(job_id, results)

    # Expire some results
    for i in [1, 3]:
        job_id = f"job_{i}"
        metadata_file = Path(temp_storage_path) / job_id / "metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)
        metadata["expires_at"] = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

    # Run cleanup
    cleaned = storage.cleanup_expired()
    assert cleaned == 2

    # Verify correct results remain
    assert storage.get_results("job_0") is not None
    assert storage.get_results("job_1") is None
    assert storage.get_results("job_2") is not None
    assert storage.get_results("job_3") is None
    assert storage.get_results("job_4") is not None


def test_storage_stats(temp_storage_path):
    """Test storage statistics."""
    storage = ResultStorage(storage_path=temp_storage_path, ttl_hours=24)

    # Create results
    for i in range(3):
        job_id = f"job_{i}"
        results = {"poi_count": i, "large_data": "x" * 1000}
        storage.save_results(job_id, results)

    # Expire one result
    metadata_file = Path(temp_storage_path) / "job_1" / "metadata.json"
    with open(metadata_file) as f:
        metadata = json.load(f)
    metadata["expires_at"] = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    with open(metadata_file, "w") as f:
        json.dump(metadata, f)

    # Get stats
    stats = storage.get_storage_stats()

    assert stats["total_jobs"] == 3
    assert stats["expired_jobs"] == 1
    assert stats["total_size_bytes"] > 0
    assert stats["total_size_mb"] >= 0  # May be 0 due to rounding
    assert temp_storage_path in stats["storage_path"]


@pytest.mark.asyncio
async def test_cleanup_scheduler():
    """Test the cleanup scheduler."""
    # Create scheduler with very short interval for testing
    scheduler = CleanupScheduler(interval_minutes=0.01)  # 0.6 seconds

    # Track cleanup runs
    cleanup_count = 0
    original_cleanup = scheduler._run_cleanup

    async def mock_cleanup():
        nonlocal cleanup_count
        cleanup_count += 1
        await original_cleanup()

    scheduler._run_cleanup = mock_cleanup

    # Start scheduler
    await scheduler.start()

    # Wait for at least 2 cleanup cycles
    await asyncio.sleep(1.5)

    # Stop scheduler
    await scheduler.stop()

    # Verify cleanup ran multiple times
    assert cleanup_count >= 2
    assert not scheduler.is_running


if __name__ == "__main__":
    # Run basic tests
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Testing result storage TTL...")
        test_result_storage_ttl(temp_dir)
        print("✓ TTL test passed")

    with tempfile.TemporaryDirectory() as temp_dir:
        print("\nTesting cleanup of expired results...")
        test_cleanup_expired(temp_dir)
        print("✓ Cleanup test passed")

    with tempfile.TemporaryDirectory() as temp_dir:
        print("\nTesting storage statistics...")
        test_storage_stats(temp_dir)
        print("✓ Statistics test passed")

    print("\nTesting cleanup scheduler...")
    asyncio.run(test_cleanup_scheduler())
    print("✓ Scheduler test passed")

    print("\nAll cleanup tests passed!")
