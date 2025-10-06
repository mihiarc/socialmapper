"""
Diagnostic tests for Census Geocoding API.

These tests verify that the Census Geocoding API is accessible and working
correctly, and provide clear diagnostics when failures occur.
"""

import pytest
import requests
from socialmapper._geocoding import get_census_geography


class TestCensusGeocodingAPI:
    """Test Census Geocoding API connectivity and functionality."""

    def test_census_api_is_accessible(self):
        """
        Test that the Census Geocoding API is accessible.

        This test makes a direct HTTP request to verify the service is up.
        """
        url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
        params = {
            "x": -78.6382,  # Raleigh, NC
            "y": 35.7796,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "layers": "2020 Census Blocks",
            "format": "json"
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            assert response.status_code == 200, "Census API returned non-200 status"

            data = response.json()
            assert "result" in data, "Census API response missing 'result' field"

        except requests.Timeout:
            pytest.fail(
                "Census Geocoding API request timed out. "
                "Your internet connection may be slow or the service is experiencing high load."
            )
        except requests.RequestException as e:
            pytest.fail(
                f"Network error accessing Census Geocoding API: {e}. "
                f"Check your internet connection or try again later."
            )
        except Exception as e:
            pytest.fail(f"Unexpected error accessing Census API: {e}")

    def test_get_census_geography_with_valid_us_coordinates(self):
        """
        Test get_census_geography with known valid US coordinates.

        Uses Raleigh, NC coordinates which should always return valid
        census geography data.
        """
        # Raleigh, NC - State Capitol coordinates
        lat, lon = 35.7796, -78.6382

        result = get_census_geography(lat, lon)

        assert result is not None, (
            "get_census_geography returned None for valid US coordinates. "
            "Check logs for specific error (timeout, network, or API issue)."
        )

        # Verify structure
        assert "state_fips" in result, "Missing state_fips in result"
        assert "county_fips" in result, "Missing county_fips in result"
        assert "tract" in result, "Missing tract in result"
        assert "block_group" in result, "Missing block_group in result"
        assert "geoid" in result, "Missing geoid in result"

        # Verify NC values (state FIPS 37, Wake County FIPS 183)
        assert result["state_fips"] == "37", f"Expected NC (37), got {result['state_fips']}"
        assert result["county_fips"] == "183", f"Expected Wake County (183), got {result['county_fips']}"
        assert len(result["geoid"]) == 12, f"GEOID should be 12 digits, got {len(result['geoid'])}"

    def test_get_census_geography_with_ocean_coordinates(self):
        """
        Test get_census_geography with coordinates in the ocean.

        This should return None and log an appropriate warning.
        """
        # Coordinates in Atlantic Ocean
        lat, lon = 35.0, -70.0

        result = get_census_geography(lat, lon)

        assert result is None, (
            "get_census_geography should return None for ocean coordinates. "
            "Expected warning about location outside US or no census data."
        )

    def test_get_census_geography_with_international_coordinates(self):
        """
        Test get_census_geography with international coordinates.

        This should return None and log an appropriate warning.
        """
        # London, UK coordinates
        lat, lon = 51.5074, -0.1278

        result = get_census_geography(lat, lon)

        assert result is None, (
            "get_census_geography should return None for non-US coordinates. "
            "Expected warning about location outside US."
        )

    def test_multiple_us_locations(self):
        """
        Test get_census_geography with multiple known US locations.

        This verifies the API works consistently across different states.
        """
        test_locations = [
            (35.7796, -78.6382, "37", "183"),  # Raleigh, NC
            (34.0522, -118.2437, "06", "037"),  # Los Angeles, CA
            (41.8781, -87.6298, "17", "031"),  # Chicago, IL
        ]

        for lat, lon, expected_state, expected_county in test_locations:
            result = get_census_geography(lat, lon)

            assert result is not None, (
                f"Failed to get census geography for ({lat}, {lon}). "
                f"Check logs for specific error."
            )

            assert result["state_fips"] == expected_state, (
                f"State FIPS mismatch for ({lat}, {lon}): "
                f"expected {expected_state}, got {result['state_fips']}"
            )
            assert result["county_fips"] == expected_county, (
                f"County FIPS mismatch for ({lat}, {lon}): "
                f"expected {expected_county}, got {result['county_fips']}"
            )


class TestCensusGeocodingDiagnostics:
    """Diagnostic tests that help identify specific failure modes."""

    def test_network_connectivity(self):
        """
        Test basic network connectivity to Census API domain.

        This helps distinguish between network issues and API issues.
        """
        try:
            response = requests.get(
                "https://geocoding.geo.census.gov/",
                timeout=10
            )
            # Any response (even 404) means we can reach the server
            assert response.status_code in [200, 404, 301, 302], (
                f"Unexpected status code from Census API: {response.status_code}"
            )
        except requests.Timeout:
            pytest.fail(
                "Network timeout reaching Census API domain. "
                "Your internet connection may be slow or DNS resolution failed."
            )
        except requests.RequestException as e:
            pytest.fail(
                f"Cannot reach Census API domain: {e}. "
                f"Check your internet connection or firewall settings."
            )

    def test_api_response_format(self):
        """
        Test that Census API returns expected JSON format.

        This helps identify if the API structure has changed.
        """
        url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
        params = {
            "x": -78.6382,
            "y": 35.7796,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "layers": "2020 Census Blocks",
            "format": "json"
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        # Check expected structure
        assert "result" in data, "Response missing 'result' key"

        if data["result"] and data["result"].get("geographies"):
            blocks = data["result"]["geographies"].get("2020 Census Blocks", [])
            if blocks:
                block = blocks[0]
                required_fields = ["STATE", "COUNTY", "TRACT", "BLKGRP"]
                for field in required_fields:
                    assert field in block, (
                        f"Census API response missing expected field '{field}'. "
                        f"API format may have changed."
                    )
