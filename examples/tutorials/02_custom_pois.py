#!/usr/bin/env python3
"""
SocialMapper Tutorial 02: Using Custom POIs

This tutorial shows how to analyze your own points of interest:
- Loading POIs from a CSV file
- Understanding the required format
- Analyzing multiple locations at once
- Comparing accessibility across different POIs

Prerequisites:
- Complete Tutorial 01 first
- Have a CSV file with your POI data
"""

import os
import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import run_socialmapper


def main():
    """Demonstrate custom POI analysis."""
    
    print("🗺️  SocialMapper Tutorial 02: Using Custom POIs\n")
    
    # Step 1: Understanding the CSV format
    print("Step 1: CSV Format Requirements")
    print("Your CSV file needs these columns:")
    print("  - name: POI name (required)")
    print("  - latitude: Decimal latitude (required)")
    print("  - longitude: Decimal longitude (required)")
    print("  - type: Category (optional)")
    print("  - address: Street address (optional)\n")
    
    # Step 2: Using example data
    print("Step 2: Using example custom POIs")
    custom_coords_path = "examples/data/custom_coordinates.csv"
    
    # Check if file exists
    if not Path(custom_coords_path).exists():
        print(f"❌ Example file not found: {custom_coords_path}")
        print("\nCreating a simple example CSV...")
        
        # Create example CSV
        csv_content = """name,latitude,longitude,type
Central Library,35.7796,-78.6382,library
City Park,35.7821,-78.6589,park
Community Center,35.7754,-78.6434,community_center
"""
        Path("custom_pois.csv").write_text(csv_content)
        custom_coords_path = "custom_pois.csv"
        print(f"✅ Created example file: {custom_coords_path}\n")
    
    # Step 3: Configure analysis
    print("Step 3: Configuring analysis parameters")
    travel_time = 10  # minutes
    census_variables = [
        "total_population",
        "median_age",
        "percent_poverty"
    ]
    
    print(f"  ⏱️  Travel time: {travel_time} minutes")
    print(f"  📊 Census variables: {', '.join(census_variables)}\n")
    
    # Step 4: Run analysis
    print("Step 4: Running analysis on custom POIs...")
    
    try:
        results = run_socialmapper(
            custom_coords_path=custom_coords_path,
            travel_time=travel_time,
            census_variables=census_variables,
            export_csv=True,
            export_maps=False  # Skip for tutorial speed
        )
        
        print("\n✅ Analysis complete!\n")
        
        # Step 5: Explore results
        print("Step 5: Results summary")
        
        if results.get("poi_data"):
            print(f"\n📍 Analyzed {len(results['poi_data'])} custom POIs:")
            for poi in results["poi_data"]:
                name = poi.get("name", "Unknown")
                poi_type = poi.get("type", "unspecified")
                print(f"  - {name} ({poi_type})")
        
        if results.get("census_data"):
            # Group results by POI
            print(f"\n👥 Population within {travel_time} minutes of each POI:")
            
            # Note: In real implementation, you'd need to track which
            # census blocks belong to which POI's isochrone
            total_pop = sum(
                row.get("total_population", 0) 
                for row in results["census_data"]
            )
            avg_pop_per_poi = total_pop / len(results["poi_data"])
            print(f"  Average population reach: {avg_pop_per_poi:,.0f}")
        
        print("\n💡 Tips for custom POI analysis:")
        print("  - Use descriptive names for your POIs")
        print("  - Group POIs by type for comparative analysis")
        print("  - Consider different travel times for different POI types")
        print("  - Export maps to visualize overlapping service areas")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nCommon issues:")
        print("- Check CSV format (name, latitude, longitude)")
        print("- Ensure coordinates are in decimal degrees")
        print("- Verify coordinates are in the US (for census data)")
        return 1
    
    print("\n🎉 Tutorial complete! Next steps:")
    print("- Try the trail_heads.csv dataset (2,600+ POIs)")
    print("- Create your own CSV with local POIs")
    print("- Compare accessibility between different POI types")
    print("- Use batch processing for large datasets")
    
    return 0


def show_batch_processing_example():
    """Show how to process multiple POI types separately."""
    print("\n📚 Bonus: Batch Processing Example")
    print("-" * 40)
    print("""
# Process different POI types separately
poi_types = ['library', 'school', 'hospital', 'park']

for poi_type in poi_types:
    print(f"Analyzing {poi_type}s...")
    results = run_socialmapper(
        state="North Carolina",
        county="Wake County", 
        place_type=poi_type,
        travel_time=15,
        census_variables=['total_population'],
        export_csv=True
    )
    print(f"Found {len(results['poi_data'])} {poi_type}s")
""")


if __name__ == "__main__":
    result = main()
    if result == 0:
        show_batch_processing_example()
    sys.exit(result)