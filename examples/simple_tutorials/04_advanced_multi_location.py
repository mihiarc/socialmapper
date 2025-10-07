#!/usr/bin/env python3
"""
Simple Tutorial 04: Advanced Multi-Location Analysis

Learn advanced techniques for analyzing multiple locations.
Build sophisticated spatial analyses with simple functions.

What you'll learn:
- Batch processing multiple locations
- Finding overlapping service areas
- Gap analysis for underserved areas
- Optimizing facility placement
- Creating comparative reports
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
)


def example_1_batch_processing():
    """Process multiple locations efficiently."""
    print("\n⚡ Example 1: Batch Processing")
    print("-" * 40)

    # List of locations in Raleigh area
    locations = [
        ("Downtown Raleigh", (35.7796, -78.6382)),
        ("North Hills", (35.8321, -78.6414)),
        ("Crabtree Valley", (35.8198, -78.7074)),
    ]

    print(f"Processing {len(locations)} locations:")

    results = []
    for name, coords in locations:
        # Create isochrone for each location
        isochrone = create_isochrone(
            location=coords,
            travel_time=5,
            travel_mode="drive"
        )

        area = isochrone['properties']['area_sq_km']
        results.append({
            'name': name,
            'lat': coords[0],
            'lon': coords[1],
            'area_km2': area
        })

        print(f"   ✅ {name[:30]:30} → {area:.2f} km²")

    # Calculate summary statistics
    areas = [r['area_km2'] for r in results]
    avg_area = sum(areas) / len(areas)
    total_area = sum(areas)
    min_area = min(areas)
    max_area = max(areas)

    print(f"\n📊 Summary Statistics:")
    print(f"   Average coverage: {avg_area:.2f} km²")
    print(f"   Total coverage: {total_area:.2f} km²")
    print(f"   Coverage range: {min_area:.2f} - {max_area:.2f} km²")

    return results


def example_2_service_overlap():
    """Analyze overlapping service areas."""
    print("\n🔄 Example 2: Service Area Overlap")
    print("-" * 40)

    # Two nearby facilities
    facilities = [
        ("Facility A", (35.7796, -78.6382)),
        ("Facility B", (35.7915, -78.6569))
    ]

    print("Analyzing service areas:")

    isochrones = []
    populations = []

    for name, coords in facilities:
        # Create isochrone
        isochrone = create_isochrone(
            location=coords,
            travel_time=5,
            travel_mode="drive"
        )
        isochrones.append((name, isochrone))

        area = isochrone['properties']['area_sq_km']
        print(f"   ✅ {name}: {area:.2f} km²")

        # Get population in area
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

        populations.append(population)
        print(f"      Population: ~{population:,}")

    # Calculate distance between facilities
    dist_km = ((facilities[0][1][0] - facilities[1][1][0])**2 +
               (facilities[0][1][1] - facilities[1][1][1])**2)**0.5 * 111  # rough km conversion

    print(f"\n📍 Distance between facilities: {dist_km:.2f} km")

    if dist_km < 5:
        overlap = "High overlap (facilities very close)"
    elif dist_km < 10:
        overlap = "Moderate overlap"
    else:
        overlap = "Low overlap"

    print(f"🔄 Service area overlap: {overlap}")

    return isochrones


def example_3_gap_analysis():
    """Identify underserved areas."""
    print("\n🔍 Example 3: Gap Analysis")
    print("-" * 40)

    # Existing facility locations
    existing = [
        ("Existing 1", (35.7796, -78.6382)),
        ("Existing 2", (35.9132, -79.0558))
    ]

    # Potential new locations to test
    candidates = [
        ("Candidate A", (35.8500, -78.7000)),
        ("Candidate B", (35.7000, -78.5500)),
    ]

    print("Analyzing coverage gaps:")

    # Calculate current coverage
    print("\n1. Current facilities:")
    current_coverage = 0
    for name, coords in existing:
        isochrone = create_isochrone(
            location=coords,
            travel_time=5,
            travel_mode="drive"
        )
        area = isochrone['properties']['area_sq_km']
        current_coverage += area
        print(f"   {name}: {area:.2f} km²")

    print(f"   Total current: {current_coverage:.2f} km²")

    # Test each candidate location
    print("\n2. Testing candidate locations:")
    best_candidate = None
    best_improvement = 0

    for name, coords in candidates:
        # Create isochrone for candidate
        isochrone = create_isochrone(
            location=coords,
            travel_time=5,
            travel_mode="drive"
        )
        area = isochrone['properties']['area_sq_km']

        # Estimate improvement (simplified - assumes 40% overlap)
        improvement = area * 0.6
        improvement_pct = (improvement / current_coverage) * 100

        print(f"   {name}: +{improvement:.2f} km² (+{improvement_pct:.1f}%)")

        if improvement > best_improvement:
            best_improvement = improvement
            best_candidate = name

    print(f"\n✨ Best location: {best_candidate}")
    print(f"   Expected coverage increase: {best_improvement:.2f} km²")

    return best_candidate


def example_4_accessibility_matrix():
    """Create an accessibility matrix between locations."""
    print("\n📋 Example 4: Accessibility Matrix")
    print("-" * 40)

    # Key locations to analyze
    locations = {
        "Downtown": (35.7796, -78.6382),
        "North Hills": (35.8321, -78.6414),
        "RDU Airport": (35.8776, -78.7875),
    }

    travel_time = 5
    print(f"Creating {travel_time}-minute accessibility matrix:\n")

    # Create matrix
    matrix = {}
    for name, coords in locations.items():
        isochrone = create_isochrone(
            location=coords,
            travel_time=travel_time,
            travel_mode="drive"
        )

        area = isochrone['properties']['area_sq_km']
        matrix[name] = area

    # Display matrix
    print("Location        Area (km²)  Relative")
    print("-" * 40)
    max_area = max(matrix.values())
    for name, area in matrix.items():
        relative = area / max_area
        bar = "█" * int(relative * 20)
        print(f"{name:15} {area:8.2f}  {bar}")

    # Find best connected location
    best = max(matrix.items(), key=lambda x: x[1])
    print(f"\n🏆 Best connected: {best[0]} ({best[1]:.2f} km²)")

    return matrix


def main():
    """Run all examples."""
    print("=" * 50)
    print("🚀 SIMPLE TUTORIAL: ADVANCED MULTI-LOCATION")
    print("=" * 50)
    print("\nAdvanced spatial analysis techniques")
    print("Complex analyses with simple functions!\n")

    try:
        # Run examples
        example_1_batch_processing()
        example_2_service_overlap()
        example_3_gap_analysis()
        example_4_accessibility_matrix()

        print("\n" + "=" * 50)
        print("✨ Tutorial completed successfully!")
        print("\nKey takeaways:")
        print("1. Batch process multiple locations efficiently")
        print("2. Analyze service area overlaps")
        print("3. Identify coverage gaps")
        print("4. Create accessibility matrices")
        print("5. Optimize facility placement")
        print("\nSimple functions enable sophisticated analysis!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Census API may be slow - try smaller areas")
        print("3. Ensure coordinates are in the United States")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
