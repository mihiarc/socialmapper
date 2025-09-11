#!/usr/bin/env python3
"""
SocialMapper Tutorial 01: Getting Started

This tutorial introduces the basic concepts of SocialMapper:
- Finding Points of Interest (POIs) from OpenStreetMap
- Generating travel time isochrones
- Analyzing census demographics within reach
- Creating choropleth maps to visualize results
- Exporting results

Prerequisites:
- SocialMapper installed: pip install socialmapper
- Census API key (optional): Set CENSUS_API_KEY environment variable
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import SocialMapper, tutorial_error_handler


def main():
    """Run a basic SocialMapper analysis with choropleth visualization."""

    print("🗺️  SocialMapper Tutorial 01: Getting Started\n")
    print("This tutorial will analyze access to libraries in Wake County, NC")
    print("and create choropleth maps to visualize the results.\n")

    # Step 1: Define search parameters
    print("Step 1: Defining search parameters...")
    location = "Wake County, North Carolina"
    poi_types = ["library"]
    travel_time = 15  # minutes

    print(f"  📍 Location: {location}")
    print(f"  🏛️  POI Types: {', '.join(poi_types)}")
    print(f"  ⏱️  Travel Time: {travel_time} minutes\n")

    # Step 2: Set census variables to analyze
    print("Step 2: Selecting census variables...")
    census_variables = ["total_population", "median_household_income", "median_age"]
    print(f"  📊 Variables: {', '.join(census_variables)}\n")

    # Step 3: Run the analysis
    print("Step 3: Running analysis...")
    print("  🔍 Searching for libraries...")
    print("  🗺️  Generating isochrones...")
    print("  📊 Analyzing demographics...")
    print("  🎨 Creating choropleth maps...")

    # Use tutorial error handler for better error messages
    try:
        with tutorial_error_handler("Getting Started Tutorial"):
            # Initialize SocialMapper client
            mapper = SocialMapper()
            
            # Run analysis with simple, direct API
            result = mapper.analyze_location(
                location=location,
                poi_types=poi_types,
                travel_time=travel_time,
                census_variables=census_variables,
                output_dir="output",
                create_maps=True
            )

            print("\n✅ Analysis complete!\n")

            # Step 4: Explore results
            print("Step 4: Results summary:")
            print(f"  🏛️  Found {result.poi_count} libraries")
            print(f"  📊 Census data collected for {result.census_units_analyzed} block groups")
            print(f"  🗺️  Analysis area: {result.isochrone_area_km2:.2f} km²")

            # Show demographics if available
            if result.demographics:
                print(f"  👥 Total population in area: {result.demographics.get('total_population', 'N/A'):,}")
                print(f"  💰 Median household income: ${result.demographics.get('median_household_income', 0):,}")
                print(f"  📅 Median age: {result.demographics.get('median_age', 'N/A')} years")

            # Show generated files
            if result.files_created:
                print("\n📁 Results saved to output/ directory:")
                for file_path in result.files_created:
                    print(f"   - {file_path}")

            # Check for generated maps
            map_dir = Path("output/maps")
            if map_dir.exists():
                map_files = list(map_dir.glob("*.png"))
                if map_files:
                    print("\n🗺️  Choropleth maps generated:")
                    for map_file in sorted(map_files):
                        print(f"   - {map_file.name}")
                    print("\n   Open these files to visualize:")
                    print("   - Population density patterns")
                    print("   - Income distribution")
                    print("   - Age demographics")
                    print("   - Travel distance to libraries")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    print("\n🎉 Tutorial complete! Next steps:")
    print("- View the generated choropleth maps in output/maps/")
    print("- Examine the detailed CSV data in output/csv/")
    print("- Try different POI types: 'school', 'hospital', 'park'")
    print("- Adjust travel time: 5, 10, 20, 30 minutes")
    print("- Add more census variables for richer analysis")
    print("\n💡 Simple API highlights:")
    print("- No builders or configuration objects needed")
    print("- Direct results without unwrapping")
    print("- Standard Python exceptions")
    print("- Clean, readable code")

    return 0


if __name__ == "__main__":
    sys.exit(main())