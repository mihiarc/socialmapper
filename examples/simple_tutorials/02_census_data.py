#!/usr/bin/env python3
"""
Simple Tutorial 02: Census Data Access

Learn how to work with census data using the simplified API.
No complex abstractions - just simple, direct data access.

What you'll learn:
- Creating isochrones and getting census blocks
- Fetching census data for demographic variables
- Working with population, income, and age data
- Aggregating statistics across block groups
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
)


def example_1_basic_census():
    """Get census data for an isochrone area."""
    print("\n📊 Example 1: Basic Census Data")
    print("-" * 40)

    # Create isochrone
    print("Creating 5-minute isochrone for Raleigh...")
    isochrone = create_isochrone(
        location=(35.7796, -78.6382),  # Raleigh, NC
        travel_time=5,
        travel_mode="drive"
    )

    print(f"   Isochrone area: {isochrone['properties']['area_sq_km']:.2f} km²")

    # Get census blocks in the area
    print("Fetching census blocks...")
    blocks = get_census_blocks(polygon=isochrone)
    print(f"   Found {len(blocks)} census blocks")

    if not blocks:
        print("⚠️ No census blocks found")
        return None

    # Sample blocks for speed (limit to 30)
    sample_blocks = blocks[:30]
    geoids = [block['geoid'] for block in sample_blocks]

    # Get census data
    print(f"Fetching census data for {len(geoids)} blocks...")
    census_data = get_census_data(
        location=geoids,
        variables=["population"],
        year=2022
    )

    if census_data:
        # Calculate statistics
        pop_values = [d.get('population', 0) for d in census_data.values()]
        total_pop = sum(pop_values)
        avg_pop = total_pop / len(pop_values) if pop_values else 0

        # Estimate total if we sampled
        if len(blocks) > 30:
            estimated_total = int(total_pop * (len(blocks) / len(sample_blocks)))
            print(f"✅ Retrieved census data")
            print(f"   Sample population: {total_pop:,}")
            print(f"   Estimated total: ~{estimated_total:,}")
            print(f"   Average per block: {avg_pop:.0f}")
        else:
            print(f"✅ Retrieved census data")
            print(f"   Total population: {total_pop:,}")
            print(f"   Average per block: {avg_pop:.0f}")
    else:
        print("⚠️ No census data retrieved")

    return census_data


def example_2_demographics():
    """Get comprehensive demographic data."""
    print("\n👥 Example 2: Demographic Analysis")
    print("-" * 40)

    # Create isochrone
    print("Creating 5-minute isochrone...")
    isochrone = create_isochrone(
        location=(35.7796, -78.6382),  # Raleigh, NC
        travel_time=5,
        travel_mode="drive"
    )

    # Get census blocks
    blocks = get_census_blocks(polygon=isochrone)
    print(f"   Found {len(blocks)} census blocks")

    if not blocks:
        print("⚠️ No census blocks found")
        return None

    # Sample for speed
    sample_blocks = blocks[:30]
    geoids = [block['geoid'] for block in sample_blocks]

    # Get multiple demographic variables
    print(f"Fetching demographic data...")
    demographics = get_census_data(
        location=geoids,
        variables=["population", "median_income", "median_age"],
        year=2022
    )

    if demographics:
        # Calculate aggregated statistics
        pop_values = [d.get('population', 0) for d in demographics.values()]
        income_values = [d.get('median_income', 0) for d in demographics.values()
                        if d.get('median_income', 0) > 0]
        age_values = [d.get('median_age', 0) for d in demographics.values()
                     if d.get('median_age', 0) > 0]

        total_pop = sum(pop_values)
        avg_income = sum(income_values) / len(income_values) if income_values else 0
        avg_age = sum(age_values) / len(age_values) if age_values else 0

        print(f"✅ Retrieved demographic data")
        print(f"   Population: {total_pop:,}")
        print(f"   Median income: ${avg_income:,.0f}")
        print(f"   Median age: {avg_age:.1f} years")
    else:
        print("⚠️ No demographic data retrieved")

    return demographics


def example_3_variables():
    """Demonstrate different census variables."""
    print("\n📈 Example 3: Different Census Variables")
    print("-" * 40)

    # Create isochrone
    isochrone = create_isochrone(
        location=(35.7796, -78.6382),
        travel_time=5,
        travel_mode="drive"
    )

    # Get census blocks
    blocks = get_census_blocks(polygon=isochrone)

    if not blocks:
        print("⚠️ No census blocks found")
        return None

    # Sample blocks
    sample_blocks = blocks[:20]
    geoids = [block['geoid'] for block in sample_blocks]

    # Request multiple variables
    print("Available variables include:")
    print("   - population / total_population")
    print("   - median_income")
    print("   - median_age")
    print("   - housing_units")
    print("   - median_home_value")
    print("   - median_rent")

    print(f"\nFetching housing data...")
    housing_data = get_census_data(
        location=geoids,
        variables=["housing_units", "median_home_value", "median_rent"],
        year=2022
    )

    if housing_data:
        housing_values = [d.get('housing_units', 0) for d in housing_data.values()]
        home_values = [d.get('median_home_value', 0) for d in housing_data.values()
                      if d.get('median_home_value', 0) > 0]
        rent_values = [d.get('median_rent', 0) for d in housing_data.values()
                      if d.get('median_rent', 0) > 0]

        total_housing = sum(housing_values)
        avg_home_value = sum(home_values) / len(home_values) if home_values else 0
        avg_rent = sum(rent_values) / len(rent_values) if rent_values else 0

        print(f"✅ Retrieved housing data")
        print(f"   Housing units: {total_housing:,}")
        print(f"   Median home value: ${avg_home_value:,.0f}")
        print(f"   Median rent: ${avg_rent:,.0f}/month")
    else:
        print("⚠️ No housing data retrieved")

    return housing_data


def main():
    """Run all examples."""
    print("=" * 50)
    print("🗺️  SIMPLE TUTORIAL: CENSUS DATA")
    print("=" * 50)
    print("\nThis tutorial demonstrates census data access")
    print("using the simplified API\n")

    try:
        # Run single example for speed
        example_2_demographics()

        print("\n" + "=" * 50)
        print("✨ Tutorial completed successfully!")
        print("\nKey takeaways:")
        print("1. Use get_census_blocks() to find blocks in an area")
        print("2. Use get_census_data() to fetch demographic variables")
        print("3. Sample blocks for faster analysis (first 20-30)")
        print("4. Supports population, income, age, housing, and more")
        print("5. Returns dict with human-readable variable names")
        print("\n💡 Try other examples:")
        print("- example_1_basic_census() for population only")
        print("- example_3_variables() for housing data")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection for Census API")
        print("2. Ensure coordinates are in the United States")
        print("3. Census API may be slow - try smaller areas")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
