#!/usr/bin/env python3
"""
SocialMapper Tutorial 02: Using Custom POIs

This tutorial shows how to analyze your own points of interest:
- Loading POIs from a CSV file
- Creating isochrones for multiple locations
- Analyzing demographics for each POI's service area
- Comparing accessibility across different POIs

Prerequisites:
- Complete Tutorial 01 first
- Have a CSV file with your POI data (or use the example we create)
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

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
)
from socialmapper.api import import_poi_csv


def main():
    """Demonstrate custom POI analysis."""

    print("🗺️  SocialMapper Tutorial 02: Using Custom POIs\n")

    # Step 1: Understanding the CSV format
    print("Step 1: CSV Format Requirements")
    print("Your CSV file needs these columns:")
    print("  - name: POI name (required)")
    print("  - latitude: Decimal latitude (required)")
    print("  - longitude: Decimal longitude (required)")
    print("  - type: Category (optional)\n")

    # Step 2: Create example CSV file
    print("Step 2: Creating example custom POIs")
    csv_path = Path("custom_pois.csv")

    if not csv_path.exists():
        csv_content = """name,latitude,longitude,type
Downtown Library,35.7796,-78.6382,library
North Community Center,35.8050,-78.6200,community_center
South Recreation Park,35.7500,-78.6400,park
"""
        csv_path.write_text(csv_content)
        print(f"✅ Created example file: {csv_path}\n")
    else:
        print(f"✅ Using existing file: {csv_path}\n")

    # Step 3: Import POIs from CSV
    print("Step 3: Importing POIs from CSV...")

    try:
        pois = import_poi_csv(str(csv_path))
        print(f"✅ Loaded {len(pois)} POIs:")
        for poi in pois:
            print(f"   - {poi['name']} ({poi['lat']}, {poi['lon']})")
        print()

        # Step 4: Analyze each POI
        print("Step 4: Analyzing accessibility for each POI...")
        travel_time = 10  # minutes
        travel_mode = "drive"

        results = []

        for poi in pois:
            print(f"\n📍 Analyzing: {poi['name']}")

            # Create isochrone
            isochrone = create_isochrone(
                location=(poi['lat'], poi['lon']),
                travel_time=travel_time,
                travel_mode=travel_mode
            )

            area = isochrone['properties']['area_sq_km']
            print(f"   Isochrone area: {area:.2f} km²")

            # Get census blocks
            blocks = get_census_blocks(polygon=isochrone)
            print(f"   Census blocks: {len(blocks)}")

            # Get census data if blocks found
            population = 0
            if blocks:
                geoids = [block['geoid'] for block in blocks]
                census_data = get_census_data(
                    location=geoids,
                    variables=["population"],
                    year=2022
                )

                if census_data:
                    population = sum(d.get('population', 0) for d in census_data.values())
                    print(f"   Population served: {population:,}")

            # Store results for comparison
            results.append({
                'name': poi['name'],
                'type': poi.get('type', 'unknown'),
                'area_km2': area,
                'blocks': len(blocks),
                'population': population
            })

        # Step 5: Compare results
        print("\n" + "=" * 60)
        print("Step 5: Comparing POI Accessibility\n")

        print(f"{'POI Name':<30} {'Area (km²)':<12} {'Population':<12}")
        print("-" * 60)
        for result in results:
            print(f"{result['name']:<30} {result['area_km2']:<12.2f} {result['population']:<12,}")

        total_pop = sum(r['population'] for r in results)
        avg_area = sum(r['area_km2'] for r in results) / len(results)

        print("-" * 60)
        print(f"{'TOTAL/AVERAGE':<30} {avg_area:<12.2f} {total_pop:<12,}")
        print()

        print("=" * 60)
        print("🎉 Tutorial complete!\n")
        print("What we did:")
        print("1. Created a CSV file with custom POI locations")
        print("2. Imported POIs using import_poi_csv()")
        print("3. Generated isochrones for each POI")
        print("4. Analyzed census demographics for each service area")
        print("5. Compared accessibility across all POIs")
        print("\n💡 Key insights:")
        print("- Each POI serves different population sizes")
        print("- Isochrone areas vary based on road network density")
        print("- Custom POIs let you analyze any location type")
        print("\n📚 Next steps:")
        print("- Add more POIs to your CSV file")
        print("- Try different travel times for different POI types")
        print("- Create choropleth maps for each POI")
        print("- Analyze overlap between POI service areas")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check CSV format (name, latitude, longitude required)")
        print("- Ensure coordinates are in decimal degrees")
        print("- Verify coordinates are valid (lat: -90 to 90, lon: -180 to 180)")
        print("- Check internet connection for census data")
        return 1


if __name__ == "__main__":
    sys.exit(main())
