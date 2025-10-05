#!/usr/bin/env python3
"""
Simple Tutorial 01: Basic Isochrone Creation

Learn how to create travel-time polygons (isochrones) using the direct API.
No client class needed - just simple function calls.

What you'll learn:
- Creating isochrones from coordinates
- Different travel modes (drive, walk, bike)
- Working with GeoJSON Feature results
- JSON serialization for web/API integration
- Comparing travel times and areas

NOTE: Due to geocoding service limitations, this tutorial uses coordinates
instead of addresses. See CITY_COORDINATES below for common locations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper.api import create_isochrone
import json

# Common city coordinates (since geocoding may be unavailable)
CITY_COORDINATES = {
    "Portland, OR": (45.5152, -122.6784),
    "San Francisco, CA": (37.7749, -122.4194),
    "Seattle, WA": (47.6062, -122.3321),
    "New York, NY": (40.7128, -74.0060),
    "Raleigh, NC": (35.7796, -78.6382),
    "Durham, NC": (35.9940, -78.8986),
    "Chapel Hill, NC": (35.9132, -79.0558),
    "Cary, NC": (35.7915, -78.7811),
}


def example_1_coordinate_isochrone():
    """Create an isochrone from coordinates."""
    print("\n📍 Example 1: Isochrone from Coordinates")
    print("-" * 40)

    # Portland, OR coordinates
    lat, lon = CITY_COORDINATES["Portland, OR"]

    try:
        # Create a 15-minute driving isochrone
        isochrone = create_isochrone(
            location=(lat, lon),
            travel_time=15,
            travel_mode="drive"
        )

        print(f"✅ Created isochrone for Portland, OR ({lat}, {lon})")
        print(f"   Result type: {isochrone['type']}")
        print(f"   Geometry type: {isochrone['geometry']['type']}")
        print(f"   Travel time: {isochrone['properties']['travel_time']} minutes")
        print(f"   Travel mode: {isochrone['properties']['travel_mode']}")
        print(f"   Area: {isochrone['properties']['area_sq_km']:.2f} km²")

        return isochrone

    except Exception as e:
        print(f"⚠️ Failed to create isochrone: {e}")
        print("   This may be due to network issues or service availability")
        return None


def example_2_coordinate_isochrone():
    """Create an isochrone from latitude/longitude coordinates."""
    print("\n📍 Example 2: Walking Isochrone")
    print("-" * 40)

    # San Francisco coordinates (City Hall)
    lat, lon = 37.7793, -122.4193

    # Create a 10-minute walking isochrone
    isochrone = create_isochrone(
        location=(lat, lon),
        travel_time=10,
        travel_mode="walk"
    )

    print(f"✅ Created isochrone for coordinates ({lat}, {lon})")
    print(f"   Result type: {isochrone['type']}")
    print(f"   Location: {isochrone['properties']['location']}")
    print(f"   Travel mode: {isochrone['properties']['travel_mode']}")
    print(f"   Area: {isochrone['properties']['area_sq_km']:.2f} km²")

    return isochrone


def example_3_bike_isochrone():
    """Create a biking isochrone."""
    print("\n🚴 Example 3: Bike Isochrone")
    print("-" * 40)

    # Create a 20-minute biking isochrone
    isochrone = create_isochrone(
        location=(40.7128, -74.0060),  # NYC coordinates
        travel_time=20,
        travel_mode="bike"
    )

    print(f"✅ Created bike isochrone for NYC")
    print(f"   Travel mode: {isochrone['properties']['travel_mode']}")
    print(f"   Travel time: {isochrone['properties']['travel_time']} minutes")
    print(f"   Area: {isochrone['properties']['area_sq_km']:.2f} km²")

    return isochrone


def example_4_json_output():
    """Demonstrate JSON serialization of isochrone results."""
    print("\n📊 Example 4: JSON Serialization")
    print("-" * 40)

    # Seattle, WA coordinates
    lat, lon = 47.6062, -122.3321

    # Create isochrone - returns GeoJSON Feature dict by default
    isochrone = create_isochrone(
        location=(lat, lon),
        travel_time=15,
        travel_mode="drive"
    )

    print(f"✅ Created isochrone")
    print(f"   Type: {isochrone['type']}")
    print(f"   Location: {isochrone['properties']['location']}")
    print(f"   Area: {isochrone['properties']['area_sq_km']:.2f} km²")
    print(f"   Travel time: {isochrone['properties']['travel_time']} minutes")

    # The result is already a dict, ready for JSON serialization
    json_str = json.dumps(isochrone, indent=2)
    print(f"\n   JSON output preview (first 200 chars):")
    print(f"   {json_str[:200]}...")

    return isochrone


def example_5_comparison():
    """Compare different travel times."""
    print("\n⏱️ Example 5: Comparing Travel Times")
    print("-" * 40)

    location = (35.7796, -78.6382)  # Raleigh, NC

    # Create isochrones for different times
    times = [5, 10, 15]
    areas = []

    for time in times:
        isochrone = create_isochrone(
            location=location,
            travel_time=time,
            travel_mode="drive"
        )
        area = isochrone['properties']['area_sq_km']
        areas.append(area)
        print(f"   {time} minutes: {area:.2f} km²")

    # Show how area grows with time
    print(f"\n📈 Area growth:")
    for i in range(1, len(times)):
        growth = (areas[i] - areas[i-1]) / areas[i-1] * 100
        print(f"   {times[i-1]} → {times[i]} min: +{growth:.1f}%")


def main():
    """Run all examples."""
    print("=" * 50)
    print("🗺️  SIMPLE TUTORIAL: ISOCHRONE CREATION")
    print("=" * 50)
    print("\nThis tutorial demonstrates the direct API functions")
    print("No client class needed - just simple, direct calls!")
    
    try:
        # Run examples
        example_1_coordinate_isochrone()
        example_2_coordinate_isochrone()
        example_3_bike_isochrone()
        example_4_json_output()
        example_5_comparison()
        
        print("\n" + "=" * 50)
        print("✨ Tutorial completed successfully!")
        print("\nKey takeaways:")
        print("1. Use create_isochrone() directly - no client needed")
        print("2. Works with addresses or coordinates")
        print("3. Supports drive, walk, and bike modes")
        print("4. Returns GeoJSON Feature dict (ready for JSON)")
        print("5. Simple, direct, and efficient!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Ensure geocoding services are available")
        print("3. Try with simpler parameters")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())