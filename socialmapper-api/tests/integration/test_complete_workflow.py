#!/usr/bin/env python3
"""Test script for complete analysis workflow including job completion.
"""

import json
import sys
import time
from pathlib import Path

# Add the API server to the path
sys.path.append(str(Path(__file__).parent))

from api_server.main import create_app
from fastapi.testclient import TestClient


def test_complete_workflow():
    """Test the complete analysis workflow from submission to completion."""
    # Create test client
    app = create_app()
    client = TestClient(app)

    print("Testing Complete SocialMapper Analysis Workflow")
    print("=" * 60)

    # Step 1: Submit analysis job
    print("\n1. Submitting analysis job...")
    analysis_request = {
        "location": "Portland, OR",
        "poi_type": "amenity",
        "poi_name": "library",
        "travel_time": 15,
        "census_variables": ["B01003_001E"],
        "geographic_level": "block_group",
        "travel_mode": "walk",
        "include_isochrones": True,
        "include_demographics": True
    }

    response = client.post("/api/v1/analysis/location", json=analysis_request)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Failed to submit job: {response.json()}")
        return

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"Job submitted successfully with ID: {job_id}")
    print(f"Response: {json.dumps(job_data, indent=2)}")

    # Step 2: Monitor job status until completion
    print("\n2. Monitoring job status...")
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        response = client.get(f"/api/v1/analysis/{job_id}/status")
        print(f"Attempt {attempt + 1}: Status {response.status_code}")

        if response.status_code == 200:
            status_data = response.json()
            print(f"Job Status: {status_data['status']}")
            print(f"Progress: {status_data['progress']:.1%}")
            print(f"Message: {status_data.get('message', 'N/A')}")

            if status_data['status'] == 'completed':
                print("✅ Job completed successfully!")
                break
            elif status_data['status'] == 'failed':
                print("❌ Job failed!")
                print(f"Error: {status_data.get('error', 'Unknown error')}")
                return

        time.sleep(1)  # Wait 1 second before checking again
        attempt += 1

    if attempt >= max_attempts:
        print("⚠️ Job did not complete within expected time")
        return

    # Step 3: Retrieve analysis results
    print("\n3. Retrieving analysis results...")
    response = client.get(f"/api/v1/analysis/{job_id}/result")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result_data = response.json()
        print("✅ Results retrieved successfully!")
        print(f"POI Count: {result_data.get('poi_count', 'N/A')}")
        print(f"Demographics: {json.dumps(result_data.get('demographics', {}), indent=2)}")
        print(f"Processing Time: {result_data.get('processing_time_seconds', 'N/A')} seconds")

        # Show some POIs if available
        pois = result_data.get('pois', [])
        if pois:
            print(f"\nFound {len(pois)} POIs:")
            for i, poi in enumerate(pois[:3]):  # Show first 3
                print(f"  {i+1}. {poi.get('name', 'Unknown')} at ({poi.get('lat', 'N/A')}, {poi.get('lon', 'N/A')})")
    else:
        print(f"Failed to retrieve results: {response.json()}")
        return

    # Step 4: Test job listing
    print("\n4. Testing job listing...")
    response = client.get("/api/v1/analysis/jobs")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        jobs_data = response.json()
        print(f"Total jobs: {jobs_data.get('total_jobs', 0)}")
        print("Jobs summary:")
        for job_id_key, job_info in jobs_data.get('jobs', {}).items():
            print(f"  {job_id_key}: {job_info.get('status', 'unknown')} - {job_info.get('location', 'N/A')}")

    # Step 5: Test job deletion
    print("\n5. Testing job deletion...")
    response = client.delete(f"/api/v1/analysis/{job_id}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("✅ Job deleted successfully!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        # Verify job is gone
        response = client.get(f"/api/v1/analysis/{job_id}/status")
        if response.status_code == 404:
            print("✅ Confirmed: Job no longer exists")
        else:
            print("⚠️ Job still exists after deletion")
    else:
        print(f"Failed to delete job: {response.json()}")

    print("\n" + "=" * 60)
    print("Complete workflow test finished!")


if __name__ == "__main__":
    test_complete_workflow()
