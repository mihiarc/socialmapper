#!/usr/bin/env python3
"""
SocialMapper Tutorial 03: Using Different Travel Modes

This tutorial demonstrates how to generate isochrones using different travel modes
(walk, bike, drive) and compare their coverage areas.

Prerequisites:
- Complete Tutorials 01 and 02 first

Note: This tutorial uses coordinates instead of addresses due to geocoding limitations.
"""

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import create_isochrone


def main():
    """Run travel mode comparison example."""
    print("🗺️  SocialMapper Tutorial 03: Travel Modes\n")
    print("This tutorial compares walking, biking, and driving isochrones")
    print("from the same location to understand different accessibility patterns.\n")

    # Use Chapel Hill, NC coordinates
    location = (35.9132, -79.0558)  # Chapel Hill, NC
    location_name = "Chapel Hill, NC"
    travel_time = 15  # minutes

    print(f"📍 Location: {location_name} {location}")
    print(f"⏱️  Travel Time: {travel_time} minutes\n")

    results = {}

    # Example 1: Walking isochrone
    print("=" * 60)
    print("1. Walking Mode (pedestrian paths and sidewalks)")
    print("=" * 60)

    try:
        walk_iso = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode="walk"
        )

        walk_area = walk_iso['properties']['area_sq_km']
        results['walk'] = walk_area

        print(f"✅ Created walking isochrone")
        print(f"   Area coverage: {walk_area:.2f} km²")
        print(f"   Typical use: Access to parks, libraries, local shops\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")

    # Example 2: Biking isochrone
    print("=" * 60)
    print("2. Biking Mode (bike lanes, shared roads, trails)")
    print("=" * 60)

    try:
        bike_iso = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode="bike"
        )

        bike_area = bike_iso['properties']['area_sq_km']
        results['bike'] = bike_area

        print(f"✅ Created biking isochrone")
        print(f"   Area coverage: {bike_area:.2f} km²")
        print(f"   Typical use: Commuting, recreation, medium-distance access\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")

    # Example 3: Driving isochrone
    print("=" * 60)
    print("3. Driving Mode (roads accessible by car)")
    print("=" * 60)

    try:
        drive_iso = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode="drive"
        )

        drive_area = drive_iso['properties']['area_sq_km']
        results['drive'] = drive_area

        print(f"✅ Created driving isochrone")
        print(f"   Area coverage: {drive_area:.2f} km²")
        print(f"   Typical use: Hospitals, shopping centers, workplaces\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")

    # Comparison
    if len(results) >= 2:
        print("=" * 60)
        print("Travel Mode Comparison")
        print("=" * 60)

        print(f"\n{'Mode':<12} {'Area (km²)':<12} {'Relative Size'}")
        print("-" * 60)

        # Sort by area
        sorted_results = sorted(results.items(), key=lambda x: x[1])

        for mode, area in sorted_results:
            # Calculate relative size vs smallest
            relative = (area / sorted_results[0][1]) * 100
            print(f"{mode:<12} {area:<12.2f} {relative:.0f}%")

        print()

        # Show the multiplier effect
        if 'walk' in results and 'drive' in results:
            multiplier = results['drive'] / results['walk']
            print(f"💡 Key insight: Driving reaches {multiplier:.1f}x more area than walking")
            print(f"   in the same {travel_time} minutes!\n")

    # Example 4: Comparing different times for one mode
    print("=" * 60)
    print("4. Bonus: Comparing Different Travel Times (Drive Mode)")
    print("=" * 60)

    times = [5, 10, 15]
    time_results = {}

    print(f"\nGenerating {len(times)} isochrones with different times...\n")

    for time in times:
        try:
            iso = create_isochrone(
                location=location,
                travel_time=time,
                travel_mode="drive"
            )
            area = iso['properties']['area_sq_km']
            time_results[time] = area
            print(f"   {time} min: {area:.2f} km²")
        except Exception as e:
            print(f"   {time} min: Error - {e}")

    if len(time_results) > 1:
        print("\n📈 Area growth:")
        times_sorted = sorted(time_results.keys())
        for i in range(1, len(times_sorted)):
            prev_time = times_sorted[i-1]
            curr_time = times_sorted[i]
            growth = ((time_results[curr_time] - time_results[prev_time]) / time_results[prev_time]) * 100
            print(f"   {prev_time}→{curr_time} min: +{growth:.1f}%")

    # Summary
    print("\n" + "=" * 60)
    print("🎉 Tutorial complete!\n")
    print("What we learned:")
    print("1. Different travel modes use different transportation networks")
    print("2. Driving typically covers much more area than walking/biking")
    print("3. Each mode is appropriate for different types of accessibility analysis")
    print("4. Travel time has a non-linear effect on coverage area")
    print("\n💡 Travel mode selection guide:")
    print("- Walk: Local amenities (parks, shops, cafes)")
    print("- Bike: Medium-distance services (libraries, community centers)")
    print("- Drive: Regional services (hospitals, malls, workplaces)")
    print("\n📚 Next steps:")
    print("- Try different locations (urban vs rural)")
    print("- Compare modes for specific POI types")
    print("- Analyze demographic differences between modes")
    print("- Create maps overlaying different travel modes")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
