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

from socialmapper import run_socialmapper


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
            geocode_area=geocode_area,
            state=state,
            poi_type=poi_type,
            poi_name=poi_name,
            travel_time=travel_time,
            census_variables=census_variables,
            export_csv=True,  # Save results to CSV
            export_isochrones=False  # Skip map generation for tutorial
        )
        
        print("\n✅ Analysis complete!\n")
        
        # Step 4: Explore results
        print("Step 4: Results summary:")
        
        if results.get("poi_data") and results["poi_data"].get("pois"):
            pois = results["poi_data"]["pois"]
            poi_count = len(pois)
            print(f"  🏛️  Found {poi_count} libraries")
            
            # Show first few POIs
            print("\n  First 3 libraries found:")
            for i, poi in enumerate(pois[:3], 1):
                name = poi.get("name", "Unnamed")
                lat = poi.get("lat", 0)
                lon = poi.get("lon", 0)
                print(f"    {i}. {name} ({lat:.4f}, {lon:.4f})")
        
        census_data = results.get("census_data")
        if census_data is not None and not census_data.empty:
            print(f"\n  📊 Census data collected for {len(census_data)} block groups")
            
            # Calculate total population within reach
            total_pop = 0
            if hasattr(census_data, 'iterrows'):
                # It's a DataFrame/GeoDataFrame
                for _, row in census_data.iterrows():
                    total_pop += row.get("total_population", 0) or 0
            else:
                # It's a list of dictionaries
                total_pop = sum(
                    row.get("total_population", 0) or 0
                    for row in census_data
                )
            print(f"  👥 Total population within {travel_time} minutes: {total_pop:,}")
        
        print("\n📁 Results saved to output/ directory")
        print("   - CSV files with detailed data")
        print("   - Run with export_isochrones=True to generate visualizations")
        
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
    print("- Enable map generation with export_isochrones=True")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())