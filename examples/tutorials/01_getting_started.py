#!/usr/bin/env python3
"""
SocialMapper Tutorial 01: Getting Started

This tutorial introduces the core concepts of SocialMapper using the
simplified functional API:
- Creating travel-time isochrones
- Finding Points of Interest (POIs)
- Analyzing census demographics within reach
- Creating choropleth maps to visualize results

Prerequisites:
- SocialMapper installed: pip install socialmapper
- Census API key (optional): Set CENSUS_API_KEY environment variable

Note: This tutorial uses coordinates instead of addresses due to
geocoding service limitations.
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
    get_poi
)


def main():
    """Run a basic SocialMapper analysis with choropleth visualization."""

    print("🗺️  SocialMapper Tutorial 01: Getting Started\n")
    print("This tutorial will analyze accessibility in Raleigh, NC using")
    print("the simplified functional API - no client class needed!\n")

    # Step 1: Create an isochrone
    print("Step 1: Creating a travel-time isochrone...")
    location = (35.7796, -78.6382)  # Raleigh, NC coordinates
    travel_time = 15  # minutes
    travel_mode = "drive"

    print(f"  📍 Location: Raleigh, NC {location}")
    print(f"  ⏱️  Travel Time: {travel_time} minutes")
    print(f"  🚗 Travel Mode: {travel_mode}\n")

    try:
        isochrone = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode=travel_mode
        )

        print(f"✅ Isochrone created!")
        print(f"   Area: {isochrone['properties']['area_sq_km']:.2f} km²\n")

        # Step 2: Find POIs within the isochrone
        print("Step 2: Finding libraries near the location...")

        pois = get_poi(
            location=location,
            categories=["library"],
            travel_time=travel_time,
            limit=10
        )

        print(f"✅ Found {len(pois)} libraries")
        if pois:
            print("   Top 3 closest:")
            for i, poi in enumerate(pois[:3], 1):
                name = poi.get('name', 'Unknown')
                distance = poi.get('distance_km', 0)
                print(f"   {i}. {name} ({distance:.2f} km)")
        print()

        # Step 3: Get census blocks within the isochrone
        print("Step 3: Getting census blocks within the isochrone...")

        blocks = get_census_blocks(polygon=isochrone)

        print(f"✅ Found {len(blocks)} census block groups")
        if blocks:
            total_area = sum(b.get('area_sq_km', 0) for b in blocks)
            print(f"   Total area: {total_area:.2f} km²\n")

        # Step 4: Get census data for those blocks
        print("Step 4: Fetching demographic data from US Census...")

        if blocks:
            # Extract GEOIDs from blocks
            geoids = [block['geoid'] for block in blocks]

            # Get demographic data
            census_data = get_census_data(
                location=geoids,
                variables=["population", "median_income", "median_age"],
                year=2022
            )

            if census_data:
                print(f"✅ Retrieved census data for {len(census_data)} block groups")

                # Calculate totals and averages
                total_pop = sum(data.get('population', 0) for data in census_data.values())
                incomes = [data.get('median_income', 0) for data in census_data.values() if data.get('median_income', 0) > 0]
                ages = [data.get('median_age', 0) for data in census_data.values() if data.get('median_age', 0) > 0]

                print(f"   Total population: {total_pop:,}")
                if incomes:
                    print(f"   Average median income: ${sum(incomes)/len(incomes):,.0f}")
                if ages:
                    print(f"   Average median age: {sum(ages)/len(ages):.1f} years")
                print()

                # Step 5: Create choropleth maps
                print("Step 5: Creating choropleth maps...")

                # Combine block geometry with census data
                map_data = []
                for block in blocks:
                    geoid = block['geoid']
                    if geoid in census_data:
                        map_data.append({
                            'geometry': block['geometry'],
                            'geoid': geoid,
                            'population': census_data[geoid].get('population', 0),
                            'median_income': census_data[geoid].get('median_income', 0),
                            'median_age': census_data[geoid].get('median_age', 0),
                        })

                if map_data:
                    # Create output directory
                    output_dir = Path("output/maps")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Create population map
                    pop_map = create_map(
                        data=map_data,
                        column="population",
                        title="Population Distribution - 15min Drive from Raleigh",
                        save_path=str(output_dir / "raleigh_population.png")
                    )
                    print("   ✅ Created population map")

                    # Create income map
                    income_map = create_map(
                        data=map_data,
                        column="median_income",
                        title="Median Income - 15min Drive from Raleigh",
                        save_path=str(output_dir / "raleigh_income.png")
                    )
                    print("   ✅ Created median income map")

                    # Create age map
                    age_map = create_map(
                        data=map_data,
                        column="median_age",
                        title="Median Age - 15min Drive from Raleigh",
                        save_path=str(output_dir / "raleigh_age.png")
                    )
                    print("   ✅ Created median age map")

                    print(f"\n📁 Maps saved to: {output_dir}/\n")
            else:
                print("⚠️  No census data available\n")
        else:
            print("⚠️  No census blocks found\n")

        print("=" * 60)
        print("🎉 Tutorial complete!\n")
        print("What we did:")
        print("1. Created a 15-minute driving isochrone around Raleigh, NC")
        print("2. Found libraries within that area")
        print("3. Retrieved census block groups intersecting the isochrone")
        print("4. Fetched demographic data from US Census Bureau")
        print("5. Created choropleth maps visualizing the data")
        print("\n💡 Key API highlights:")
        print("- Five simple functions: create_isochrone, get_poi, get_census_blocks,")
        print("  get_census_data, create_map")
        print("- No client class or builders needed")
        print("- Functions return standard Python dicts and lists")
        print("- Direct, readable, functional code")
        print("\n📚 Next steps:")
        print("- Try different locations by changing coordinates")
        print("- Experiment with travel times: 5, 10, 20, 30 minutes")
        print("- Search for different POI categories: 'school', 'hospital', 'park'")
        print("- Add more census variables for richer analysis")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check your internet connection")
        print("- Verify Census API key is set (optional but recommended)")
        print("- Try with a different location")
        return 1


if __name__ == "__main__":
    sys.exit(main())
