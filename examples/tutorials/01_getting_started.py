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

from socialmapper import SocialMapperBuilder, SocialMapperClient, tutorial_error_handler


def main():
    """Run a basic SocialMapper analysis with choropleth visualization."""

    print("🗺️  SocialMapper Tutorial 01: Getting Started\n")
    print("This tutorial will analyze access to libraries in Wake County, NC")
    print("and create choropleth maps to visualize the results.\n")

    # Step 1: Define search parameters
    print("Step 1: Defining search parameters...")
    geocode_area = "Wake County"
    state = "North Carolina"
    poi_type = "amenity"  # OpenStreetMap category
    poi_name = "library"  # Specific type within category
    travel_time = 15  # minutes

    print(f"  📍 Location: {geocode_area}, {state}")
    print(f"  🏛️  POI Type: {poi_type} - {poi_name}")
    print(f"  ⏱️  Travel Time: {travel_time} minutes\n")

    # Step 2: Set census variables to analyze
    print("Step 2: Selecting census variables...")
    census_variables = [
        "total_population",
        "median_household_income",
        "median_age"
    ]
    print(f"  📊 Variables: {', '.join(census_variables)}\n")

    # Step 3: Run the analysis
    print("Step 3: Running analysis...")
    print("  🔍 Searching for libraries...")
    print("  🗺️  Generating isochrones...")
    print("  📊 Analyzing demographics...")
    print("  🎨 Creating choropleth maps...")

    # Use tutorial error handler for better error messages
    with tutorial_error_handler("Getting Started Tutorial"):
        # Use the modern API with context manager
        with SocialMapperClient() as client:
            # Build configuration using fluent interface
            config = (SocialMapperBuilder()
                .with_location(geocode_area, state)
                .with_osm_pois(poi_type, poi_name)
                .with_travel_time(travel_time)
                .with_census_variables(*census_variables)
                .with_exports(csv=True, isochrones=False, maps=True)  # Enable map generation
                .build()
            )

            # Run analysis
            result = client.run_analysis(config)

            # Handle result using pattern matching
            if result.is_err():
                error = result.unwrap_err()
                # The error will be handled by tutorial_error_handler
                raise error.cause if error.cause else ValueError(error.message)

            # Get successful result
            analysis_result = result.unwrap()

            print("\n✅ Analysis complete!\n")

            # Step 4: Explore results
            print("Step 4: Results summary:")
            print(f"  🏛️  Found {analysis_result.poi_count} libraries")
            print(f"  📊 Census data collected for {analysis_result.census_units_analyzed} block groups")

            # Show metadata
            if analysis_result.metadata:
                travel_time = analysis_result.metadata.get("travel_time", 15)
                print(f"  ⏱️  Analysis performed with {travel_time} minute travel time")

            # Show generated files
            if analysis_result.files_generated:
                print("\n📁 Results saved to output/ directory:")
                for file_type, file_path in analysis_result.files_generated.items():
                    print(f"   - {file_type}: {file_path}")

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

    print("\n🎉 Tutorial complete! Next steps:")
    print("- View the generated choropleth maps in output/maps/")
    print("- Examine the detailed CSV data in output/csv/")
    print("- Try different POI types: 'school', 'hospital', 'park'")
    print("- Adjust travel time: 5, 10, 20, 30 minutes")
    print("- Add more census variables for richer analysis")

    return 0


if __name__ == "__main__":
    sys.exit(main())
