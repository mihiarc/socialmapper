#!/usr/bin/env python3
"""Test script for analysis API endpoints.
"""

import json
import sys
from pathlib import Path

# Add the API server to the path
sys.path.append(str(Path(__file__).parent))

from api_server.main import create_app
from fastapi.testclient import TestClient


def test_analysis_endpoints():
    """Test the analysis API endpoints."""
    # Create test client
    app = create_app()
    client = TestClient(app)

    print("Testing SocialMapper Analysis API Endpoints")
    print("=" * 50)

    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    response = client.get("/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200

    # Test 2: Status check
    print("\n2. Testing status endpoint...")
    response = client.get("/api/v1/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

    # Test 3: Submit analysis job
    print("\n3. Testing analysis submission...")
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
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 202:
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"Job submitted successfully with ID: {job_id}")

        # Test 4: Check job status
        print(f"\n4. Testing job status for {job_id}...")
        response = client.get(f"/api/v1/analysis/{job_id}/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        # Test 5: List all jobs
        print("\n5. Testing job listing...")
        response = client.get("/api/v1/analysis/jobs")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        # Test 6: Try to get results (should be pending/running)
        print(f"\n6. Testing result retrieval for {job_id}...")
        response = client.get(f"/api/v1/analysis/{job_id}/result")
        print(f"Status: {response.status_code}")
        if response.status_code == 202:
            print("Job is still running (expected)")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Response: {json.dumps(response.json(), indent=2)}")

    else:
        print(f"Failed to submit job: {response.json()}")

    # Test 7: Test invalid requests
    print("\n7. Testing invalid request handling...")
    invalid_request = {
        "location": "",  # Invalid empty location
        "poi_type": "amenity",
        "poi_name": "library"
    }

    response = client.post("/api/v1/analysis/location", json=invalid_request)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 422

    # Test 8: Test non-existent job
    print("\n8. Testing non-existent job...")
    response = client.get("/api/v1/analysis/non-existent-job/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 404

    print("\n" + "=" * 50)
    print("All tests completed successfully!")


if __name__ == "__main__":
    test_analysis_endpoints()
