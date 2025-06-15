#!/usr/bin/env python3
"""
SocialMapper Tutorial 01: Getting Started

This tutorial introduces the basic concepts of SocialMapper:
- Finding Points of Interest (POIs) from OpenStreetMap
- Generating travel time isochrones
- Analyzing census demographics within reach
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

import os
import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import SocialMapperClient, SocialMapperBuilder


def main():
    """Run a basic SocialMapper analysis."""
    
    print("🗺️  SocialMapper Tutorial 01: Getting Started\n")
    print("This tutorial will analyze access to libraries in Wake County, NC.\n")
    
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
    
    try:
        # Use the modern API with context manager
        with SocialMapperClient() as client:
            # Build configuration using fluent interface
            config = (SocialMapperBuilder()
                .with_location(geocode_area, state)
                .with_osm_pois(poi_type, poi_name)
                .with_travel_time(travel_time)
                .with_census_variables(*census_variables)
                .with_exports(csv=True, isochrones=False)  # Skip map generation for tutorial
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
                print("\n📁 Results saved to output/ directory:")
                for file_type, file_path in analysis_result.files_generated.items():
                    print(f"   - {file_type}: {file_path}")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1
    
    print("\n🎉 Tutorial complete! Next steps:")
    print("- Try different POI types: 'school', 'hospital', 'park'")
    print("- Adjust travel time: 5, 10, 20, 30 minutes")
    print("- Add more census variables")
    print("- Enable map generation with export_isochrones=True")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())