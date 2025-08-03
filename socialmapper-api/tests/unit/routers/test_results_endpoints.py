"""Test script for the results and export endpoints.
"""

import asyncio

import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def test_results_endpoints():
    """Test the results and export endpoints."""
    async with httpx.AsyncClient() as client:
        print("Testing Results and Export Endpoints")
        print("=" * 50)

        # First, create an analysis job
        print("\n1. Creating analysis job...")
        analysis_request = {
            "location": "Portland, OR",
            "poi_type": "amenity",
            "poi_name": "library",
            "travel_time": 15,
            "census_variables": ["B01003_001E"],
            "geographic_level": "block_group",
            "travel_mode": "walk"
        }

        response = await client.post(
            f"{BASE_URL}/analysis/location",
            json=analysis_request
        )

        if response.status_code == 200:
            job_response = response.json()
            job_id = job_response["job_id"]
            print(f"✓ Created job: {job_id}")
        else:
            print(f"✗ Failed to create job: {response.status_code}")
            print(response.text)
            return

        # Wait for job to complete
        print("\n2. Waiting for job to complete...")
        max_attempts = 10
        for i in range(max_attempts):
            await asyncio.sleep(1)

            status_response = await client.get(
                f"{BASE_URL}/analysis/{job_id}/status"
            )

            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   Status: {status['status']} (progress: {status['progress']:.0%})")

                if status['status'] == 'completed':
                    print("✓ Job completed successfully")
                    break
                elif status['status'] == 'failed':
                    print(f"✗ Job failed: {status.get('error', 'Unknown error')}")
                    return
            else:
                print(f"✗ Failed to get status: {status_response.status_code}")
                return

        # Test getting results
        print("\n3. Testing GET /results/{job_id}...")
        results_response = await client.get(
            f"{BASE_URL}/results/{job_id}"
        )

        if results_response.status_code == 200:
            results = results_response.json()
            print("✓ Successfully retrieved results")
            print(f"   - POI count: {results.get('poi_count', 0)}")
            print(f"   - Status: {results.get('status')}")
            print(f"   - Export URLs: {len(results.get('export_urls', {}))}")
        else:
            print(f"✗ Failed to get results: {results_response.status_code}")
            print(results_response.text)

        # Test CSV export
        print("\n4. Testing CSV export...")
        csv_response = await client.get(
            f"{BASE_URL}/results/{job_id}/export",
            params={"format": "csv"}
        )

        if csv_response.status_code == 200:
            print("✓ Successfully exported as CSV")
            print(f"   Content-Type: {csv_response.headers.get('content-type')}")
            print(f"   First 200 chars: {csv_response.text[:200]}...")
        else:
            print(f"✗ Failed to export CSV: {csv_response.status_code}")

        # Test GeoJSON export
        print("\n5. Testing GeoJSON export...")
        geojson_response = await client.get(
            f"{BASE_URL}/results/{job_id}/export",
            params={"format": "geojson"}
        )

        if geojson_response.status_code == 200:
            print("✓ Successfully exported as GeoJSON")
            print(f"   Content-Type: {geojson_response.headers.get('content-type')}")
            try:
                geojson_data = geojson_response.json()
                print(f"   Feature count: {len(geojson_data.get('features', []))}")
            except:
                pass
        else:
            print(f"✗ Failed to export GeoJSON: {geojson_response.status_code}")

        # Test async export job creation
        print("\n6. Testing async export job creation...")
        export_request = {
            "job_id": job_id,
            "format": "geoparquet",
            "include_isochrones": True,
            "include_demographics": True
        }

        export_response = await client.post(
            f"{BASE_URL}/results/{job_id}/export",
            json=export_request
        )

        if export_response.status_code == 200:
            export_data = export_response.json()
            print("✓ Successfully created export job")
            print(f"   Export ID: {export_data.get('export_id')}")
            print(f"   Format: {export_data.get('format')}")
            print(f"   Status: {export_data.get('status')}")
        else:
            print(f"✗ Failed to create export job: {export_response.status_code}")
            print(export_response.text)

        # Test deleting results
        print("\n7. Testing DELETE /results/{job_id}...")
        delete_response = await client.delete(
            f"{BASE_URL}/results/{job_id}"
        )

        if delete_response.status_code == 200:
            print("✓ Successfully deleted results")
            delete_data = delete_response.json()
            print(f"   Message: {delete_data.get('message')}")
        else:
            print(f"✗ Failed to delete results: {delete_response.status_code}")

        # Verify deletion
        print("\n8. Verifying deletion...")
        verify_response = await client.get(
            f"{BASE_URL}/results/{job_id}"
        )

        if verify_response.status_code == 404:
            print("✓ Results properly deleted (404 returned)")
        else:
            print(f"✗ Results still accessible: {verify_response.status_code}")

        print("\n" + "=" * 50)
        print("Results endpoints test completed!")


if __name__ == "__main__":
    asyncio.run(test_results_endpoints())
