#!/usr/bin/env python3
"""Test the job manager directly to verify it works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the API server to the path
sys.path.append(str(Path(__file__).parent))

from api_server.models.analysis import AnalysisRequest
from api_server.services.job_manager import JobManager


async def test_job_manager():
    """Test the job manager directly."""
    print("Testing Job Manager Directly")
    print("=" * 40)

    # Create job manager
    job_manager = JobManager()
    await job_manager.start()

    try:
        # Create a test request
        request = AnalysisRequest(
            location="Portland, OR",
            poi_type="amenity",
            poi_name="library",
            travel_time=15,
            census_variables=["B01003_001E"]
        )

        # Submit job
        print("1. Creating job...")
        job_id = job_manager.create_job(request)
        print(f"Job ID: {job_id}")

        # Check initial status
        job = job_manager.get_job(job_id)
        print(f"Initial status: {job.status}")

        # Wait for completion
        print("2. Waiting for completion...")
        max_wait = 10  # 10 seconds
        waited = 0

        while waited < max_wait:
            await asyncio.sleep(1)
            waited += 1

            job = job_manager.get_job(job_id)
            print(f"After {waited}s: Status={job.status}, Progress={job.progress:.1%}")

            if job.status.value in ['completed', 'failed']:
                break

        # Check final results
        final_job = job_manager.get_job(job_id)
        print("\n3. Final Results:")
        print(f"Status: {final_job.status}")
        print(f"Progress: {final_job.progress:.1%}")
        print(f"Message: {final_job.message}")

        if final_job.status.value == 'completed':
            print(f"Processing time: {final_job.processing_time_seconds}s")
            print(f"Result keys: {list(final_job.result.keys()) if final_job.result else 'None'}")
            if final_job.result:
                print(f"POI count: {final_job.result.get('poi_count', 'N/A')}")
            print("✅ Job completed successfully!")
        elif final_job.status.value == 'failed':
            print(f"Error: {final_job.error}")
            print("❌ Job failed!")
        else:
            print("⚠️ Job did not complete in time")

    finally:
        await job_manager.stop()


if __name__ == "__main__":
    asyncio.run(test_job_manager())
