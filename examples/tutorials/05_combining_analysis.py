#!/usr/bin/env python3
"""
Simple Tutorial 03: Combining Isochrones with Demographics

Learn how to combine spatial analysis with demographic data.
Build complete analyses using simple, composable functions.

What you'll learn:
- Creating isochrones and adding demographics
- Comparing multiple areas
- Analyzing accessibility to resources
- Building custom analysis workflows
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
)


def example_1_basic_combination():
    """Combine isochrone with demographic data."""
    print("\n🔗 Example 1: Basic Combination")
    print("-" * 40)

    # Step 1: Create isochrone
    print("Step 1: Creating isochrone...")
    isochrone = create_isochrone(
        location=(35.7796, -78.6382),  # Raleigh, NC
        travel_time=5,
        travel_mode="drive"
    )

    area = isochrone['properties']['area_sq_km']
    print(f"   ✅ Isochrone created: {area:.2f} km²")

    # Step 2: Get census blocks
    print("Step 2: Getting census blocks...")
    blocks = get_census_blocks(polygon=isochrone)
    print(f"   Found {len(blocks)} census blocks")

    if not blocks:
        print("   ⚠️ No census blocks found")
        return None

    # Step 3: Get demographics (sample for speed)
    print("Step 3: Fetching demographic data...")
    sample_blocks = blocks[:30]
    geoids = [block['geoid'] for block in sample_blocks]

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

        sample_pop = sum(pop_values)
        avg_income = sum(income_values) / len(income_values) if income_values else 0
        avg_age = sum(age_values) / len(age_values) if age_values else 0

        # Estimate total if we sampled
        if len(blocks) > 30:
            total_pop = int(sample_pop * (len(blocks) / len(sample_blocks)))
            print(f"   ✅ Demographics retrieved")
            print(f"      Population (estimated): ~{total_pop:,}")
        else:
            total_pop = sample_pop
            print(f"   ✅ Demographics retrieved")
            print(f"      Population: {total_pop:,}")

        print(f"      Median income: ${avg_income:,.0f}")
        print(f"      Median age: {avg_age:.1f} years")

        # Calculate population density
        density = total_pop / area if area > 0 else 0
        print(f"      Population density: {density:.0f} people/km²")
    else:
        print("   ⚠️ No demographic data available")

    return isochrone, demographics


def example_2_accessibility_analysis():
    """Analyze accessibility at different travel times."""
    print("\n⏱️ Example 2: Travel Time Comparison")
    print("-" * 40)

    # Compare accessibility at different travel times
    location = (35.7796, -78.6382)  # Raleigh, NC
    travel_times = [5, 10]  # Reduced for speed
    results = []

    print(f"Analyzing accessibility from Raleigh, NC:")

    for time in travel_times:
        # Create isochrone
        isochrone = create_isochrone(
            location=location,
            travel_time=time,
            travel_mode="drive"
        )

        area = isochrone['properties']['area_sq_km']

        # Get census blocks
        blocks = get_census_blocks(polygon=isochrone)

        # Get demographics (sample for speed)
        population = 0
        if blocks:
            sample_blocks = blocks[:30]
            geoids = [block['geoid'] for block in sample_blocks]

            census_data = get_census_data(
                location=geoids,
                variables=["population"],
                year=2022
            )

            if census_data:
                pop_values = [d.get('population', 0) for d in census_data.values()]
                sample_pop = sum(pop_values)

                # Estimate total if we sampled
                if len(blocks) > 30:
                    population = int(sample_pop * (len(blocks) / len(sample_blocks)))
                else:
                    population = sample_pop

        results.append({
            'time': time,
            'area_km2': area,
            'population': population,
            'density': population / area if area > 0 else 0
        })

        print(f"   {time} min: {population:,} people, {area:.1f} km²")

    # Show growth rates
    if len(results) > 1:
        print("\n📈 Accessibility growth:")
        for i in range(1, len(results)):
            pop_growth = (results[i]['population'] - results[i-1]['population'])
            area_growth = (results[i]['area_km2'] - results[i-1]['area_km2'])
            print(f"   {results[i-1]['time']} → {results[i]['time']} min: +{pop_growth:,} people, +{area_growth:.1f} km²")

    return results


def example_3_mode_comparison():
    """Compare different transportation modes."""
    print("\n🚗🚶🚴 Example 3: Transportation Mode Comparison")
    print("-" * 40)

    location = (35.7796, -78.6382)  # Raleigh, NC
    travel_time = 5  # Reduced for speed
    modes = ["drive", "walk", "bike"]

    print(f"Comparing {travel_time}-minute access by different modes:")

    comparisons = []
    for mode in modes:
        # Create isochrone
        isochrone = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode=mode
        )

        area = isochrone['properties']['area_sq_km']
        comparisons.append({
            'mode': mode,
            'area': area
        })

        print(f"   {mode:8} → {area:6.2f} km²")

    # Calculate ratios
    drive_area = comparisons[0]['area']
    print("\nArea ratios (compared to driving):")
    for comp in comparisons:
        ratio = comp['area'] / drive_area if drive_area > 0 else 0
        print(f"   {comp['mode']:8} → {ratio:.1%} of driving area")

    return comparisons


def example_4_multi_location():
    """Analyze multiple locations simultaneously."""
    print("\n📍 Example 4: Multi-Location Analysis")
    print("-" * 40)

    # Analyze multiple locations in Raleigh area
    locations = {
        "Downtown Raleigh": (35.7796, -78.6382),
        "North Hills": (35.8321, -78.6414),
    }

    travel_time = 5  # Reduced for speed
    print(f"Analyzing {travel_time}-minute drive access from key locations:")

    results = []
    for name, coords in locations.items():
        # Create isochrone
        isochrone = create_isochrone(
            location=coords,
            travel_time=travel_time,
            travel_mode="drive"
        )

        area = isochrone['properties']['area_sq_km']

        # Get demographics (sample for speed)
        blocks = get_census_blocks(polygon=isochrone)
        population = 0

        if blocks:
            sample_blocks = blocks[:30]
            geoids = [block['geoid'] for block in sample_blocks]

            census_data = get_census_data(
                location=geoids,
                variables=["population"],
                year=2022
            )

            if census_data:
                pop_values = [d.get('population', 0) for d in census_data.values()]
                sample_pop = sum(pop_values)

                if len(blocks) > 30:
                    population = int(sample_pop * (len(blocks) / len(sample_blocks)))
                else:
                    population = sample_pop

        results.append({
            'name': name,
            'area': area,
            'population': population
        })

        print(f"   {name:20} → {area:6.2f} km², ~{population:,} people")

    # Find best coverage
    if results:
        best = max(results, key=lambda x: x['population'])

        print(f"\n📊 Summary:")
        print(f"   Best population reach: {best['name']} ({best['population']:,} people)")

    return results


def main():
    """Run all examples."""
    print("=" * 50)
    print("🔗 SIMPLE TUTORIAL: COMBINING ANALYSIS")
    print("=" * 50)
    print("\nCombine spatial and demographic analysis")
    print("Build powerful insights with simple functions!\n")

    try:
        # Run selected examples (reduced for speed)
        example_1_basic_combination()
        example_2_accessibility_analysis()
        example_3_mode_comparison()

        print("\n" + "=" * 50)
        print("✨ Tutorial completed successfully!")
        print("\nKey takeaways:")
        print("1. Combine isochrones with demographics easily")
        print("2. Use get_census_blocks() to find blocks in area")
        print("3. Use get_census_data() to fetch demographics")
        print("4. Sample blocks (first 30) for faster analysis")
        print("5. Estimate total from sample for large areas")
        print("\n💡 Try other examples:")
        print("- example_4_multi_location() for comparing locations")

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
