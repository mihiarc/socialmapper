#!/usr/bin/env python3
"""
SocialMapper Tutorial 05: Address Geocoding

This tutorial demonstrates how to convert addresses into coordinates for analysis:
- Understanding geocoding and coordinate systems
- Single address geocoding
- Batch processing multiple addresses
- Creating custom POI datasets from addresses
- Integration with SocialMapper analysis workflow

Use cases:
- Researchers with address lists who need coordinates
- Urban planners analyzing accessibility by address
- Business analysts studying location-based demographics
- Creating custom POI datasets from address databases

Prerequisites:
- Complete Tutorials 01-04 first
- Internet connection for geocoding services
"""

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import create_isochrone, get_census_data, get_census_blocks
from socialmapper.geocoding import geocode_address, geocode_addresses
from socialmapper.helpers import resolve_coordinates


def main():
    """Run address geocoding tutorial."""

    print("🗺️  SocialMapper Tutorial 05: Address Geocoding\n")
    print("Learn how to convert addresses to coordinates for spatial analysis.\n")

    # Step 1: Explain geocoding
    print("=" * 70)
    print("What is Geocoding?")
    print("=" * 70)
    print("\nGeocoding converts human-readable addresses into geographic")
    print("coordinates (latitude/longitude) that can be used for mapping")
    print("and spatial analysis.\n")
    print("🎯 Why geocode addresses?")
    print("  • Convert address lists into mappable locations")
    print("  • Analyze service accessibility by street address")
    print("  • Create custom POI datasets from business directories")
    print("  • Integrate demographic data with physical locations\n")

    # Step 2: Resolve coordinates (geocoding wrapper)
    print("=" * 70)
    print("Step 1: Basic Coordinate Resolution")
    print("=" * 70)
    print("\nSocialMapper's resolve_coordinates() accepts either:")
    print("  • Coordinates: (latitude, longitude) tuple")
    print("  • Addresses: 'City, State' or full street addresses\n")

    # Example with coordinates (no geocoding needed)
    coords1 = (35.7796, -78.6382)
    result_coords, location_name = resolve_coordinates(coords1)
    print(f"Input: {coords1}")
    print(f"   → Coordinates: {result_coords}")
    print(f"   → Location: {location_name}\n")

    # Example with city name (requires geocoding)
    city = "Raleigh, NC"
    try:
        result_coords, location_name = resolve_coordinates(city)
        print(f"Input: '{city}'")
        print(f"   → Coordinates: {result_coords}")
        print(f"   → Location: {location_name}\n")
    except Exception as e:
        print(f"Input: '{city}'")
        print(f"   ⚠️  Geocoding unavailable: {e}\n")
        print("   💡 When geocoding services are limited, use coordinates instead\n")

    # Step 3: Working with addresses
    print("=" * 70)
    print("Step 2: Creating POIs from Addresses")
    print("=" * 70)
    print("\nFor real-world analysis, you often have a list of addresses")
    print("that need to be converted to coordinates.\n")

    # Example: Create a simple address list for analysis
    addresses_example = [
        "State Capitol, Raleigh, NC",
        "NC State University, Raleigh, NC",
        "RDU Airport, Morrisville, NC",
    ]

    print("Example address list:")
    for i, addr in enumerate(addresses_example, 1):
        print(f"  {i}. {addr}")

    print("\n💡 Converting addresses to coordinates:")
    print("   Option 1: Use geocoding service (requires API access)")
    print("   Option 2: Manually find coordinates and create CSV")
    print("   Option 3: Use approximate coordinates for known landmarks\n")

    # Step 4: Using manual coordinates (recommended approach)
    print("=" * 70)
    print("Step 3: Manual Coordinates Approach (Recommended)")
    print("=" * 70)
    print("\nFor reliable analysis, we recommend looking up coordinates manually")
    print("and creating a CSV file.\n")

    # Create example CSV content
    csv_example = """name,latitude,longitude,type
State Capitol,35.7806,-78.6389,government
NC State University,35.7847,-78.6821,education
RDU Airport,35.8776,-78.7875,transportation
North Hills,35.8321,-78.6414,shopping
Crabtree Valley,35.8198,-78.7074,shopping"""

    print("Example CSV format:")
    print(csv_example)
    print()

    # Save example CSV
    csv_path = Path("example_addresses.csv")
    csv_path.write_text(csv_example)
    print(f"✅ Created example file: {csv_path}\n")

    # Step 5: Import and use the POIs
    print("=" * 70)
    print("Step 4: Using Custom POIs in Analysis")
    print("=" * 70)

    from socialmapper.api import import_poi_csv

    pois = import_poi_csv(str(csv_path))
    print(f"\n✅ Loaded {len(pois)} POIs from CSV\n")

    # Analyze first POI
    if pois:
        poi = pois[0]
        print(f"Analyzing: {poi['name']}")
        print(f"Coordinates: ({poi['lat']}, {poi['lon']})\n")

        try:
            # Create isochrone around this location
            isochrone = create_isochrone(
                location=(poi['lat'], poi['lon']),
                travel_time=10,
                travel_mode="drive"
            )

            area = isochrone['properties']['area_sq_km']
            print(f"   10-minute drive area: {area:.2f} km²")

            # Get census data
            blocks = get_census_blocks(polygon=isochrone)
            print(f"   Census blocks: {len(blocks)}")

            if blocks:
                geoids = [block['geoid'] for block in blocks]
                census_data = get_census_data(
                    location=geoids,
                    variables=["population"],
                    year=2022
                )

                if census_data:
                    total_pop = sum(d.get('population', 0) for d in census_data.values())
                    print(f"   Population within 10 min: {total_pop:,}")

        except Exception as e:
            print(f"   ⚠️  Analysis error: {e}")

    # Step 6: Batch processing workflow
    print("\n\n" + "=" * 70)
    print("Step 5: Complete Workflow Example")
    print("=" * 70)
    print("\nRecommended workflow for address-based analysis:\n")

    print("1️⃣  Collect addresses")
    print("   • Business locations, service centers, facilities, etc.")
    print()
    print("2️⃣  Look up coordinates")
    print("   • Use Google Maps, OpenStreetMap, or other services")
    print("   • Copy latitude/longitude for each address")
    print()
    print("3️⃣  Create CSV file")
    print("   • Format: name,latitude,longitude,type")
    print("   • One row per location")
    print()
    print("4️⃣  Import with import_poi_csv()")
    print("   • pois = import_poi_csv('locations.csv')")
    print()
    print("5️⃣  Analyze each location")
    print("   • Loop through POIs")
    print("   • Create isochrones")
    print("   • Get census data")
    print("   • Compare accessibility")
    print()

    # Summary
    print("=" * 70)
    print("🎉 Tutorial complete!\n")
    print("What we learned:")
    print("1. How geocoding converts addresses to coordinates")
    print("2. Using resolve_coordinates() for flexible location input")
    print("3. Creating POI datasets from address lists")
    print("4. Manual coordinate lookup is most reliable approach")
    print("5. Complete workflow from addresses to analysis")
    print("\n💡 Key takeaways:")
    print("- Coordinates are more reliable than geocoding services")
    print("- CSV format makes it easy to manage location data")
    print("- import_poi_csv() integrates seamlessly with SocialMapper")
    print("- Same analysis workflow works for any POI source")
    print("\n📚 Next steps:")
    print("- Create your own CSV file with locations of interest")
    print("- Try analyzing different location types (stores, schools, etc.)")
    print("- Compare accessibility across multiple address lists")
    print("- Combine with travel mode analysis from Tutorial 03")
    print("- Export results for presentations or reports")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
