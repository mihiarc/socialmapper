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

import os
import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import run_socialmapper


def main():
    """Run a basic SocialMapper analysis."""
    
    print("🗺️  SocialMapper Tutorial 01: Getting Started\n")
    print("This tutorial will analyze access to libraries in Wake County, NC.\n")
    
    # Step 1: Define search parameters
    print("Step 1: Defining search parameters...")
    state = "North Carolina"
    county = "Wake County"
    place_type = "library"
    travel_time = 15  # minutes
    
    print(f"  📍 Location: {county}, {state}")
    print(f"  🏛️  POI Type: {place_type}")
    print(f"  ⏱️  Travel Time: {travel_time} minutes\n")
    
    # Step 2: Set census variables to analyze
    print("Step 2: Selecting census variables...")
    census_variables = [
        "total_population",
        "median_household_income",
        "percent_without_vehicle"
    ]
    print(f"  📊 Variables: {', '.join(census_variables)}\n")
    
    # Step 3: Run the analysis
    print("Step 3: Running analysis...")
    print("  🔍 Searching for libraries...")
    print("  🗺️  Generating isochrones...")
    print("  📊 Analyzing demographics...")
    
    try:
        results = run_socialmapper(
            state=state,
            county=county,
            place_type=place_type,
            travel_time=travel_time,
            census_variables=census_variables,
            export_csv=True,  # Save results to CSV
            export_maps=False  # Skip map generation for tutorial
        )
        
        print("\n✅ Analysis complete!\n")
        
        # Step 4: Explore results
        print("Step 4: Results summary:")
        
        if results.get("poi_data"):
            poi_count = len(results["poi_data"])
            print(f"  🏛️  Found {poi_count} libraries")
            
            # Show first few POIs
            print("\n  First 3 libraries found:")
            for i, poi in enumerate(results["poi_data"][:3], 1):
                name = poi.get("name", "Unnamed")
                lat = poi.get("latitude", 0)
                lon = poi.get("longitude", 0)
                print(f"    {i}. {name} ({lat:.4f}, {lon:.4f})")
        
        if results.get("census_data"):
            print(f"\n  📊 Census data collected for {len(results['census_data'])} block groups")
            
            # Calculate total population within reach
            total_pop = sum(
                row.get("total_population", 0) 
                for row in results["census_data"]
            )
            print(f"  👥 Total population within {travel_time} minutes: {total_pop:,}")
        
        print("\n📁 Results saved to output/ directory")
        print("   - CSV files with detailed data")
        print("   - Run with export_maps=True to generate visualizations")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("- Ensure you have internet connection")
        print("- Check if Census API key is set (optional)")
        print("- Try a different location or POI type")
        return 1
    
    print("\n🎉 Tutorial complete! Next steps:")
    print("- Try different POI types: 'school', 'hospital', 'park'")
    print("- Adjust travel time: 5, 10, 20, 30 minutes")
    print("- Add more census variables")
    print("- Enable map generation with export_maps=True")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())