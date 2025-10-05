#!/usr/bin/env python3
"""
SocialMapper Tutorial 01: Getting Started (Quick Test Version)

This is a faster version of the tutorial that analyzes a smaller area for testing.
Uses a 10-minute travel time in downtown Raleigh instead of a larger area.

Prerequisites:
- SocialMapper installed: pip install socialmapper
- Census API key (optional): Set CENSUS_API_KEY environment variable
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
    get_poi
)


def main():
    """Run a quick SocialMapper analysis for testing."""

    print("🗺️  SocialMapper Tutorial 01: Getting Started (Quick Test)\n")
    print("This quick version uses a smaller travel time for faster testing.\n")

    # Use downtown Raleigh coordinates with shorter travel time
    location = (35.7796, -78.6382)  # Raleigh, NC
    travel_time = 10  # Shorter time = smaller area = faster
    travel_mode = "drive"

    print(f"Step 1: Creating a {travel_time}-minute isochrone...")
    print(f"  📍 Location: Raleigh, NC {location}")
    print(f"  ⏱️  Travel Time: {travel_time} minutes (smaller area for speed)\n")

    try:
        # Create isochrone
        isochrone = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode=travel_mode
        )

        print(f"✅ Isochrone created!")
        print(f"   Area: {isochrone['properties']['area_sq_km']:.2f} km²\n")

        # Find POIs
        print("Step 2: Finding libraries...")
        pois = get_poi(
            location=location,
            categories=["library"],
            travel_time=travel_time,
            limit=5  # Fewer POIs for speed
        )

        print(f"✅ Found {len(pois)} libraries")
        if pois:
            for i, poi in enumerate(pois[:3], 1):
                print(f"   {i}. {poi.get('name', 'Unknown')}")
        print()

        # Get census blocks
        print("Step 3: Getting census blocks...")
        blocks = get_census_blocks(polygon=isochrone)

        print(f"✅ Found {len(blocks)} census block groups\n")

        # Get census data (single variable for speed)
        if blocks:
            print("Step 4: Fetching population data...")
            geoids = [block['geoid'] for block in blocks]

            census_data = get_census_data(
                location=geoids,
                variables=["population"],  # Single variable for speed
                year=2022
            )

            if census_data:
                total_pop = sum(d.get('population', 0) for d in census_data.values())
                print(f"✅ Total population: {total_pop:,}\n")

        print("=" * 60)
        print("✨ Quick tutorial complete!")
        print("\nTested successfully:")
        print("- Created isochrone")
        print(f"- Found {len(pois)} POIs")
        print(f"- Retrieved {len(blocks)} census blocks")
        print("\n💡 Try the full 01_getting_started.py for:")
        print("- Larger travel times (15, 20, 30 minutes)")
        print("- More census variables")
        print("- Choropleth map generation")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check internet connection")
        print("- Verify Census API key (optional)")
        print("- Try even smaller travel time (5 min)")
        return 1


if __name__ == "__main__":
    exit(main())
