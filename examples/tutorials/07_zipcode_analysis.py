#!/usr/bin/env python3
"""
SocialMapper Tutorial 04: Multi-Location Comparison Analysis

This tutorial demonstrates how to compare accessibility and demographics across
multiple neighborhoods or ZIP code areas using the simplified functional API.

You'll learn:
- Analyzing multiple locations in batch
- Comparing demographics across different areas
- Creating comparison tables and visualizations
- Best practices for multi-location analysis

Prerequisites:
- Complete Tutorials 01-03 first
- Census API key (optional but recommended)

Note: This tutorial uses representative coordinates for different ZIP code areas
in Raleigh, NC to demonstrate multi-location analysis.
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

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    get_poi,
)


def main():
    """Run multi-location comparison analysis."""

    print("🗺️  SocialMapper Tutorial 04: Multi-Location Comparison\n")
    print("This tutorial compares accessibility and demographics across")
    print("multiple neighborhoods in Raleigh, NC.\n")

    # Define multiple locations to analyze (different ZIP code areas)
    locations = {
        "Downtown Raleigh (27601)": (35.7796, -78.6382),
        "North Raleigh (27609)": (35.8699, -78.6204),
    }

    print("=" * 70)
    print("📍 Analyzing Locations")
    print("=" * 70)
    for name, coords in locations.items():
        print(f"  {name}: {coords}")
    print()

    # Analysis parameters
    travel_time = 5  # minutes (reduced for faster demo)
    travel_mode = "drive"

    print(f"⏱️  Travel Time: {travel_time} minutes")
    print(f"🚗 Travel Mode: {travel_mode}\n")

    # Step 1: Analyze each location
    print("=" * 70)
    print("Step 1: Analyzing Each Location")
    print("=" * 70)

    results = []

    for name, coords in locations.items():
        print(f"\n📍 {name}")
        print("-" * 70)

        try:
            # Create isochrone
            isochrone = create_isochrone(
                location=coords,
                travel_time=travel_time,
                travel_mode=travel_mode
            )

            area = isochrone['properties']['area_sq_km']
            print(f"   Isochrone area: {area:.2f} km²")

            # Get census blocks
            blocks = get_census_blocks(polygon=isochrone)
            print(f"   Census blocks: {len(blocks)}")

            # Get census data (sample for speed)
            population = 0
            median_income = 0
            median_age = 0

            if blocks:
                # Limit to 30 blocks for faster API calls
                sample_blocks = blocks[:30]
                geoids = [block['geoid'] for block in sample_blocks]

                print(f"   Fetching census data for {len(geoids)} blocks (sampled)...")
                census_data = get_census_data(
                    location=geoids,
                    variables=["population", "median_income", "median_age"],
                    year=2022
                )

                if census_data:
                    # Calculate aggregated statistics
                    pop_values = [d.get('population', 0) for d in census_data.values()]
                    income_values = [d.get('median_income', 0) for d in census_data.values() if d.get('median_income', 0) > 0]
                    age_values = [d.get('median_age', 0) for d in census_data.values() if d.get('median_age', 0) > 0]

                    sample_pop = sum(pop_values)
                    median_income = sum(income_values) / len(income_values) if income_values else 0
                    median_age = sum(age_values) / len(age_values) if age_values else 0

                    # Estimate total from sample if we sampled
                    if len(blocks) > 30:
                        population = int(sample_pop * (len(blocks) / len(sample_blocks)))
                        print(f"   Population (estimated): ~{population:,}")
                    else:
                        population = sample_pop
                        print(f"   Population: {population:,}")

                    print(f"   Median income: ${median_income:,.0f}")
                    print(f"   Median age: {median_age:.1f} years")

            # Store results
            results.append({
                'name': name,
                'coords': coords,
                'area_km2': area,
                'census_blocks': len(blocks),
                'population': population,
                'median_income': median_income,
                'median_age': median_age,
            })

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'name': name,
                'coords': coords,
                'area_km2': 0,
                'census_blocks': 0,
                'population': 0,
                'median_income': 0,
                'median_age': 0,
            })

    # Step 2: Compare results
    print("\n\n" + "=" * 70)
    print("Step 2: Comparison Analysis")
    print("=" * 70)

    # Create comparison table
    print(f"\n{'Location':<30} {'Pop':<12} {'Income':<14} {'Age':<8}")
    print("-" * 70)

    for result in results:
        name = result['name'].split('(')[0].strip()  # Shorten name
        pop = result['population']
        income = result['median_income']
        age = result['median_age']

        print(f"{name:<30} {pop:<12,} ${income:<13,.0f} {age:<8.1f}")

    # Calculate totals and averages
    total_pop = sum(r['population'] for r in results)
    avg_income = sum(r['median_income'] for r in results) / len(results)
    avg_age = sum(r['median_age'] for r in results) / len(results)

    print("-" * 70)
    print(f"{'TOTALS/AVERAGES':<30} {total_pop:<12,} ${avg_income:<13,.0f} {avg_age:<8.1f}")

    # Step 3: Insights
    print("\n\n" + "=" * 70)
    print("Step 3: Key Insights")
    print("=" * 70)

    # Find most populous area
    max_pop = max(results, key=lambda x: x['population'])
    print(f"\n👥 Largest population: {max_pop['name']}")
    print(f"   {max_pop['population']:,} people within {travel_time} minutes")

    # Find highest income area
    max_income = max(results, key=lambda x: x['median_income'])
    if max_income['median_income'] > 0:
        print(f"\n💰 Highest median income: {max_income['name']}")
        print(f"   ${max_income['median_income']:,.0f}")

    # Find youngest area
    min_age = min(results, key=lambda x: x['median_age'] if x['median_age'] > 0 else 100)
    if min_age['median_age'] > 0:
        print(f"\n🎂 Youngest median age: {min_age['name']}")
        print(f"   {min_age['median_age']:.1f} years")

    # Summary
    print("\n" + "=" * 70)
    print("🎉 Tutorial complete!\n")
    print("What we learned:")
    print("1. Batch analysis of multiple locations using functional API")
    print("2. Creating comparison tables for demographics")
    print("3. Comparing population, income, and age across areas")
    print("4. Using sampled census data for faster analysis")
    print("\n💡 Multi-location analysis use cases:")
    print("- Comparing neighborhoods for real estate decisions")
    print("- Identifying demographic differences across regions")
    print("- Understanding population characteristics by area")
    print("- Site selection based on target demographics")
    print("\n📚 Next steps:")
    print("- Add more locations (3rd location, more ZIP codes)")
    print("- Increase travel time to 10-15 minutes for larger areas")
    print("- Add more census variables (education, housing, etc.)")
    print("- Create visualizations of the comparison data")
    print("- Export results to CSV for further analysis")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
