#!/usr/bin/env python3
"""
Census Geocoding Diagnostic Script

This script demonstrates and tests the Census Geocoding workflow:
1. Convert coordinates to census geography (state/county/tract/block)
2. Fetch census block groups for an area
3. Display results with clear diagnostics

Use this to verify Census API connectivity and troubleshoot issues.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper._geocoding import get_census_geography
from socialmapper._census import fetch_block_groups_for_area
from shapely.geometry import Point, box
import logging

# Configure logging to see warnings and debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def test_coordinate_geocoding():
    """Test geocoding individual coordinates to census geography."""
    print("=" * 70)
    print("TEST 1: Coordinate → Census Geography")
    print("=" * 70)

    test_points = [
        (35.7796, -78.6382, "Raleigh, NC (State Capitol)"),
        (34.0522, -118.2437, "Los Angeles, CA"),
        (41.8781, -87.6298, "Chicago, IL"),
        (35.0, -70.0, "Atlantic Ocean (should fail)"),
    ]

    for lat, lon, description in test_points:
        print(f"\n📍 Testing: {description}")
        print(f"   Coordinates: ({lat}, {lon})")

        result = get_census_geography(lat, lon)

        if result:
            print(f"   ✅ Success!")
            print(f"      State FIPS: {result['state_fips']}")
            print(f"      County FIPS: {result['county_fips']}")
            print(f"      Tract: {result['tract']}")
            print(f"      Block Group: {result['block_group']}")
            print(f"      Full GEOID: {result['geoid']}")
        else:
            print(f"   ❌ Failed - Check warnings above for reason")


def test_area_block_groups():
    """Test fetching block groups for a geographic area."""
    print("\n\n" + "=" * 70)
    print("TEST 2: Area → Census Block Groups")
    print("=" * 70)

    # Create a small bounding box around Raleigh
    # (roughly 0.1 degrees ~ 10km square)
    center_lat, center_lon = 35.7796, -78.6382
    bbox = box(
        center_lon - 0.05,  # west
        center_lat - 0.05,  # south
        center_lon + 0.05,  # east
        center_lat + 0.05   # north
    )

    print(f"\n📐 Testing area around Raleigh, NC")
    print(f"   Bounding box: ~10km × 10km")
    print(f"   Center: ({center_lat}, {center_lon})")

    block_groups = fetch_block_groups_for_area(bbox)

    if block_groups:
        print(f"   ✅ Success! Found {len(block_groups)} block groups")
        print(f"\n   Sample block groups:")
        for i, bg in enumerate(block_groups[:5], 1):
            geoid = bg.get('geoid', 'N/A')
            print(f"      {i}. GEOID: {geoid}")

        if len(block_groups) > 5:
            print(f"      ... and {len(block_groups) - 5} more")
    else:
        print(f"   ❌ Failed - Check warnings above for reason")
        print(f"   Possible causes:")
        print(f"      • Census Geocoding API timeout (slow connection)")
        print(f"      • Network connectivity issue")
        print(f"      • Census API service temporarily unavailable")


def test_census_api_connectivity():
    """Test basic Census API connectivity."""
    print("\n\n" + "=" * 70)
    print("TEST 3: Census API Connectivity")
    print("=" * 70)

    import requests

    print("\n🔌 Testing Census Geocoding API endpoint...")

    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": -78.6382,
        "y": 35.7796,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "2020 Census Blocks",
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        print(f"   ✅ Census API is accessible")
        print(f"   Status code: {response.status_code}")

        data = response.json()
        if data.get("result"):
            print(f"   ✅ API returned valid data structure")
        else:
            print(f"   ⚠️  API response missing 'result' field")

    except requests.Timeout:
        print(f"   ❌ Request timed out (30 seconds)")
        print(f"   Your connection may be slow or API is experiencing high load")
    except requests.RequestException as e:
        print(f"   ❌ Network error: {e}")
        print(f"   Check your internet connection")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def main():
    """Run all diagnostic tests."""
    print("\n🔍 Census Geocoding Diagnostic Tool")
    print("This script tests the Census Geocoding API workflow\n")

    # Run tests
    test_coordinate_geocoding()
    test_area_block_groups()
    test_census_api_connectivity()

    # Summary
    print("\n\n" + "=" * 70)
    print("✅ Diagnostics Complete")
    print("=" * 70)
    print("\nIf all tests passed:")
    print("  → Census Geocoding API is working correctly")
    print("  → Your network connection is stable")
    print("  → SocialMapper can fetch census geographies")
    print("\nIf tests failed, check the warnings above for:")
    print("  • Timeout issues (slow connection)")
    print("  • Network connectivity problems")
    print("  • Invalid coordinates (outside US)")
    print("  • Census API service status")
    print()


if __name__ == "__main__":
    sys.exit(main())
