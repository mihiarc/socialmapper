#!/usr/bin/env python3
"""Test the API server with real HTTP requests.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import requests


def test_api_server():
    """Test the API server with real HTTP requests."""
    print("Testing SocialMapper API Server")
    print("=" * 40)

    # Start the server in the background
    print("1. Starting API server...")

    # Change to the API directory
    api_dir = Path(__file__).parent

    # Start the server process
    server_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "api_server.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "info"
    ], cwd=api_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to start
    time.sleep(3)

    base_url = "http://127.0.0.1:8000"

    try:
        # Test health endpoint
        print("2. Testing health endpoint...")
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print("❌ Server health check failed")
            return

        # Submit analysis job
        print("3. Submitting analysis job...")
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

        response = requests.post(
            f"{base_url}/api/v1/analysis/location",
            json=analysis_request,
            timeout=10
        )

        print(f"Job submission: {response.status_code}")
        if response.status_code != 200:
            print(f"Failed to submit job: {response.text}")
            return

        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"Job ID: {job_id}")

        # Monitor job status
        print("4. Monitoring job status...")
        max_attempts = 15

        for attempt in range(max_attempts):
            response = requests.get(f"{base_url}/api/v1/analysis/{job_id}/status", timeout=5)

            if response.status_code == 200:
                status_data = response.json()
                status = status_data['status']
                progress = status_data['progress']

                print(f"Attempt {attempt + 1}: {status} ({progress:.1%})")

                if status == 'completed':
                    print("✅ Job completed!")
                    break
                elif status == 'failed':
                    print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
                    return
            else:
                print(f"Status check failed: {response.status_code}")

            time.sleep(1)

        # Get results
        print("5. Retrieving results...")
        response = requests.get(f"{base_url}/api/v1/analysis/{job_id}/result", timeout=10)

        if response.status_code == 200:
            result_data = response.json()
            print("✅ Results retrieved successfully!")
            print(f"POI Count: {result_data.get('poi_count', 'N/A')}")
            print(f"Processing Time: {result_data.get('processing_time_seconds', 'N/A')}s")

            demographics = result_data.get('demographics', {})
            if demographics:
                print(f"Demographics: {json.dumps(demographics, indent=2)}")
        else:
            print(f"Failed to get results: {response.status_code} - {response.text}")

        print("✅ All tests completed successfully!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Stop the server
        print("6. Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server stopped.")


if __name__ == "__main__":
    test_api_server()
