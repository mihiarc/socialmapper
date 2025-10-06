"""
Tests for Overpass API connectivity and POI fetching.

These tests use real API calls to verify the Overpass endpoint is working.
"""

import pytest
import requests
from socialmapper import get_poi


class TestOverpassAPIConnectivity:
    """Test Overpass API endpoint connectivity."""

    def test_overpass_endpoint_accessible(self):
        """
        Test that the Overpass API endpoint is accessible.

        This makes a simple status check to verify the service is up.
        """
        url = "https://overpass-api.de/api/status"

        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, (
                f"Overpass API status endpoint returned {response.status_code}. "
                f"The service may be down or experiencing issues."
            )
        except requests.Timeout:
            pytest.fail(
                "Overpass API status check timed out. "
                "The service may be experiencing high load."
            )
        except requests.RequestException as e:
            pytest.fail(f"Cannot reach Overpass API: {e}")

    def test_overpass_simple_query(self):
        """
        Test a simple Overpass API query.

        This tests the interpreter endpoint with a minimal query.
        """
        url = "https://overpass-api.de/api/interpreter"

        # Very simple query - just get API version
        query = "[out:json];out;"

        try:
            response = requests.post(
                url,
                data=query,
                timeout=30,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            assert response.status_code == 200, (
                f"Overpass query returned status {response.status_code}. "
                f"Expected 200. The API may be experiencing issues."
            )

            data = response.json()
            assert "version" in data or "elements" in data, (
                "Unexpected Overpass API response format"
            )

        except requests.Timeout:
            pytest.fail(
                "Overpass API query timed out. "
                "The service may be overloaded or your connection is slow."
            )
        except requests.RequestException as e:
            pytest.fail(f"Overpass API query failed: {e}")


class TestPOIFetching:
    """Test POI fetching with real API calls."""

    def test_get_poi_with_small_area(self):
        """
        Test get_poi with a small search area to avoid timeouts.

        Uses a small travel time to limit the query area.
        """
        # Downtown Raleigh, NC
        location = (35.7796, -78.6382)

        # Use very small travel time to limit area
        pois = get_poi(
            location=location,
            categories=["library"],
            travel_time=3,  # 3 minutes - very small area
            limit=5
        )

        # May find 0 POIs if area is too small, but shouldn't error
        assert isinstance(pois, list), "get_poi should return a list"
        assert len(pois) <= 5, "Should respect limit parameter"

    def test_get_poi_with_coordinates(self):
        """
        Test get_poi using coordinate-based search (no isochrone).

        This is faster as it doesn't require network routing.
        """
        location = (35.7796, -78.6382)

        try:
            pois = get_poi(
                location=location,
                categories=["library"],
                travel_time=5,
                limit=3
            )

            assert isinstance(pois, list), "Should return a list"

            if pois:
                # Verify POI structure
                poi = pois[0]
                assert "lat" in poi, "POI should have latitude"
                assert "lon" in poi, "POI should have longitude"
                assert "tags" in poi, "POI should have tags"

        except Exception as e:
            if "504" in str(e) or "timeout" in str(e).lower():
                pytest.skip(
                    "Overpass API is currently overloaded (504/timeout). "
                    "This is a temporary service issue, not a code bug."
                )
            else:
                raise


class TestOverpassDiagnostics:
    """Diagnostic tests for Overpass API issues."""

    def test_overpass_rate_limiting(self):
        """
        Check if we're being rate limited by Overpass.

        Overpass has rate limits and may return 429 or 504 when overloaded.
        """
        url = "https://overpass-api.de/api/status"

        response = requests.get(url, timeout=10)

        if response.status_code == 429:
            pytest.fail(
                "Overpass API returned 429 (Too Many Requests). "
                "We are being rate limited. Wait before retrying."
            )
        elif response.status_code == 504:
            pytest.skip(
                "Overpass API returned 504 (Gateway Timeout). "
                "The service is currently overloaded. This is temporary."
            )

        assert response.status_code == 200, (
            f"Unexpected status code: {response.status_code}"
        )

    def test_alternative_overpass_endpoints(self):
        """
        Test alternative Overpass endpoints.

        Overpass has multiple public instances that can be used as fallbacks.
        """
        endpoints = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            # Add more endpoints as needed
        ]

        working_endpoints = []

        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    data="[out:json];out;",
                    timeout=10
                )
                if response.status_code == 200:
                    working_endpoints.append(endpoint)
            except:
                continue

        assert len(working_endpoints) > 0, (
            "No Overpass endpoints are currently accessible. "
            "All public instances may be down or experiencing issues."
        )

        print(f"\n✅ Working Overpass endpoints: {working_endpoints}")
