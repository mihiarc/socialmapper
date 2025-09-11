#!/usr/bin/env python3
"""
SocialMapper Tutorial 01: Getting Started (Quick Test Version)

This is a faster version of the tutorial that analyzes a smaller area for testing.
Instead of analyzing all of Wake County (34 libraries), we'll analyze just 
downtown Raleigh (2-3 libraries) to run much faster.

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

from socialmapper import SocialMapper, tutorial_error_handler


def main():
    """Run a quick SocialMapper analysis for testing."""

    print("🗺️  SocialMapper Tutorial 01: Getting Started (Quick Test)\n")
    print("This quick version analyzes a smaller area for faster testing.\n")

    # Step 1: Define smaller search parameters
    print("Step 1: Defining search parameters (smaller area for testing)...")
    
    # Use a specific coordinate in downtown Raleigh instead of whole county
    # This will limit the search radius and find fewer POIs
    location = "Downtown Raleigh, NC"  # Much smaller area than Wake County
    poi_types = ["library"]
    travel_time = 10  # Shorter time = smaller area = faster processing
    
    print(f"  📍 Location: {location}")
    print(f"  🏛️  POI Types: {', '.join(poi_types)}")
    print(f"  ⏱️  Travel Time: {travel_time} minutes\n")

    # Step 2: Set minimal census variables
    print("Step 2: Selecting census variables (minimal set)...")
    census_variables = ["total_population"]  # Just one variable for speed
    print(f"  📊 Variables: {', '.join(census_variables)}\n")

    # Step 3: Run the analysis
    print("Step 3: Running quick analysis...")
    print("  🔍 Searching for libraries in downtown area...")
    print("  🗺️  Generating isochrones...")
    print("  📊 Analyzing demographics...")

    # Use tutorial error handler for better error messages
    try:
        with tutorial_error_handler("Getting Started Tutorial (Quick)"):
            # Initialize SocialMapper client
            mapper = SocialMapper()
            
            # Run analysis with simple, direct API
            # Don't create maps for speed
            result = mapper.analyze_location(
                location=location,
                poi_types=poi_types,
                travel_time=travel_time,
                census_variables=census_variables,
                output_dir="output_quick",
                create_maps=False  # Skip map creation for speed
            )

            print("\n✅ Quick analysis complete!\n")

            # Step 4: Explore results
            print("Step 4: Results summary:")
            print(f"  🏛️  Found {result.get('poi_count', 0)} libraries")
            print(f"  📊 Census data collected for {result.get('census_units_analyzed', 0)} block groups")
            print(f"  🗺️  Analysis area: {result.get('isochrone_area_km2', 0):.2f} km²")

            # Show demographics if available
            demographics = result.get('demographics', {})
            if demographics:
                pop = demographics.get('total_population', 'N/A')
                if pop != 'N/A':
                    print(f"  👥 Total population in area: {pop:,}")

            # Show generated files
            files = result.get('files_created', [])
            if files:
                print(f"\n📁 Results saved to output_quick/ directory ({len(files)} files)")
            
            # Success indicator
            if result.get('success'):
                print("\n✨ Tutorial completed successfully!")
                print("Try the full tutorial with larger areas when ready.")
            else:
                error = result.get('error', 'Unknown error')
                print(f"\n⚠️ Analysis had issues: {error}")

    except Exception as e:
        print(f"\n❌ Tutorial failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your Census API key is set")
        print("2. Ensure you have internet connection")
        print("3. Try with even simpler parameters")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())