#!/usr/bin/env python3
"""
SocialMapper Tutorial 01: Getting Started (with Choropleth Maps)

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

from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.visualization.pipeline_integration import add_visualization_to_pipeline


def main():
    """Run a basic SocialMapper analysis with choropleth visualization."""

    print("🗺️  SocialMapper Tutorial 01: Getting Started (with Maps)\n")
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
        "median_age",
        "percent_poverty",
        "percent_no_vehicle"
    ]
    print(f"  📊 Variables: {', '.join(census_variables)}\n")

    # Step 3: Run the analysis
    print("Step 3: Running analysis...")
    print("  🔍 Searching for libraries...")
    print("  🗺️  Generating isochrones...")
    print("  📊 Analyzing demographics...")

    try:
        # Use the modern API with context manager
        with SocialMapperClient() as client:
            # Build configuration using fluent interface
            config = (SocialMapperBuilder()
                .with_location(geocode_area, state)
                .with_osm_pois(poi_type, poi_name)
                .with_travel_time(travel_time)
                .with_census_variables(*census_variables)
                .with_exports(csv=True, isochrones=True)  # Enable both CSV and map exports
                .build()
            )

            # Run analysis
            result = client.run_analysis(config)

            # Handle result using pattern matching
            if result.is_err():
                error = result.unwrap_err()
                print(f"\n❌ Error: {error.message}")
                print("\nTroubleshooting tips:")
                print("- Ensure you have internet connection")
                print("- Check if Census API key is set (optional)")
                print("- Try a different location or POI type")
                return 1

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
                print("\n📁 Initial results saved to output/ directory:")
                for file_type, file_path in analysis_result.files_generated.items():
                    print(f"   - {file_type}: {file_path}")

            # Step 5: Generate choropleth maps
            print("\nStep 5: Creating choropleth maps...")
            print("  🎨 Generating demographic visualizations...")

            # Find the parquet files needed for visualization
            pipeline_data_dir = Path("output/pipeline_data")
            census_data_path = None
            poi_data_path = None
            isochrone_data_path = None

            # Look for the most recent parquet files
            if pipeline_data_dir.exists():
                # Find census data
                census_files = list(pipeline_data_dir.glob("*census*.parquet"))
                if census_files:
                    census_data_path = sorted(census_files, key=lambda x: x.stat().st_mtime)[-1]

                # Find POI data
                poi_files = list(pipeline_data_dir.glob("*pois*.parquet"))
                if poi_files:
                    poi_data_path = sorted(poi_files, key=lambda x: x.stat().st_mtime)[-1]

                # Find isochrone data
                iso_files = list(pipeline_data_dir.glob("*isochrones*.parquet"))
                if iso_files:
                    isochrone_data_path = sorted(iso_files, key=lambda x: x.stat().st_mtime)[-1]

            if census_data_path:
                # Create visualization output directory
                viz_output_dir = Path("output/maps")

                try:
                    # Generate maps
                    map_paths = add_visualization_to_pipeline(
                        census_data_path=census_data_path,
                        output_dir=viz_output_dir,
                        poi_data_path=poi_data_path,
                        isochrone_data_path=isochrone_data_path,
                        demographic_columns=census_variables[:3],  # Limit to first 3 for demo
                        create_distance_map=False,  # Skip distance map for libraries
                        create_demographic_maps=True,
                        map_format="png",
                        dpi=150  # Lower DPI for faster generation
                    )

                    print("\n✅ Choropleth maps created!")
                    print("\n🗺️  Generated maps:")
                    for map_type, map_path in map_paths.items():
                        print(f"   - {map_type}: {map_path}")

                except Exception as e:
                    print(f"\n⚠️  Could not create choropleth maps: {e!s}")
                    print("   Maps require parquet output format. Ensure pipeline saves intermediate data.")
            else:
                print("\n⚠️  Choropleth map generation skipped - no parquet data found")
                print("   To enable maps, ensure the pipeline exports intermediate parquet files")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e!s}")
        return 1

    print("\n🎉 Tutorial complete! Next steps:")
    print("- Open the generated maps in output/maps/ directory")
    print("- Try different POI types: 'school', 'hospital', 'park'")
    print("- Adjust travel time: 5, 10, 20, 30 minutes")
    print("- Add more census variables for richer visualizations")
    print("- Experiment with different map styles and color schemes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
