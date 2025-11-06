#!/usr/bin/env python3
"""
SocialMapper Tutorial 02: Comparing Travel Modes for Accessibility

LEARNING OBJECTIVES:
- Generate and compare isochrones for walk, bike, and drive modes
- Understand how transportation networks affect accessibility
- Calculate coverage multipliers between different modes
- Analyze the equity implications of transportation choices
- Visualize multi-modal accessibility patterns

PREREQUISITES:
- Complete Tutorial 01 (Getting Started)
- Basic understanding of isochrones
- SocialMapper installed with dependencies

KEY CONCEPTS:
- Modal Choice: How people choose to travel (walk, bike, drive, transit)
- Network Distance: Actual travel path vs straight-line distance
- Coverage Area: Geographic extent reachable in given time
- Accessibility Equity: Who can reach services based on available modes
- Travel Time Budget: Time people are willing to spend traveling

TIME ESTIMATE: 20-25 minutes

WHAT YOU'LL BUILD:
A comprehensive comparison showing how different travel modes affect accessibility
to services, with quantitative metrics and equity insights.
"""

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_data,
    get_census_blocks
)


def calculate_mode_statistics(isochrone: dict, mode: str) -> Dict:
    """
    Calculate detailed statistics for a travel mode isochrone.

    Parameters
    ----------
    isochrone : dict
        The isochrone GeoJSON feature
    mode : str
        The travel mode name

    Returns
    -------
    dict
        Statistics including area, perimeter estimate, and characteristics
    """
    area = isochrone['properties']['area_sq_km']

    # Estimate perimeter (rough approximation)
    # For a circle: perimeter = 2 * π * sqrt(area/π)
    import math
    radius_estimate = math.sqrt(area / math.pi)
    perimeter_estimate = 2 * math.pi * radius_estimate

    # Mode-specific insights
    insights = {
        'walk': {
            'typical_speed': '5 km/h',
            'max_distance': '1.25 km',
            'best_for': 'Local services, parks, cafes',
            'equity_note': 'Essential for non-drivers (children, elderly, low-income)'
        },
        'bike': {
            'typical_speed': '15 km/h',
            'max_distance': '3.75 km',
            'best_for': 'Schools, libraries, community centers',
            'equity_note': 'Low-cost transportation, requires safe infrastructure'
        },
        'drive': {
            'typical_speed': '40 km/h',
            'max_distance': '10 km',
            'best_for': 'Hospitals, shopping, employment',
            'equity_note': 'Requires car ownership, excludes ~20% of population'
        }
    }

    return {
        'area_km2': area,
        'perimeter_km': perimeter_estimate,
        'radius_km': radius_estimate,
        **insights.get(mode, {})
    }


def main():
    """Run comprehensive travel mode comparison with educational insights."""

    print("🗺️  SocialMapper Tutorial 02: Travel Mode Comparison\n")
    print("This tutorial demonstrates how transportation choices affect")
    print("accessibility to services and opportunities.\n")

    # ================================================================
    # Setup: Define location and parameters
    # ================================================================
    print("SETUP: Analysis Parameters")
    print("-" * 60)

    # Use Chapel Hill, NC - a university town with varied transportation
    location = (35.9132, -79.0558)
    location_name = "Chapel Hill, NC (UNC Campus Area)"
    travel_time = 15  # Standard accessibility threshold

    print(f"📍 Location: {location_name}")
    print(f"   Coordinates: {location}")
    print(f"⏱️  Travel Time: {travel_time} minutes")
    print(f"📊 Why 15 minutes? Research shows this is a key threshold for")
    print(f"   regular trips - people rarely travel >15 min for daily needs.\n")

    # Store results for comparison
    results = {}
    isochrones = {}

    # ================================================================
    # Part 1: Generate isochrones for each mode
    # ================================================================
    print("=" * 70)
    print("PART 1: GENERATING ISOCHRONES BY MODE")
    print("=" * 70)

    modes = ['walk', 'bike', 'drive']
    mode_emojis = {'walk': '🚶', 'bike': '🚴', 'drive': '🚗'}

    for i, mode in enumerate(modes, 1):
        print(f"\n{i}. {mode_emojis[mode]} {mode.upper()} MODE")
        print("-" * 40)

        try:
            # Create isochrone
            print(f"   Generating {mode} isochrone...")
            iso = create_isochrone(
                location=location,
                travel_time=travel_time,
                travel_mode=mode
            )

            # Store for later use
            isochrones[mode] = iso

            # Calculate statistics
            stats = calculate_mode_statistics(iso, mode)
            results[mode] = stats

            # Display results
            print(f"   ✅ Success!")
            print(f"   Area covered: {stats['area_km2']:.2f} km²")
            print(f"   Estimated radius: {stats['radius_km']:.2f} km")

            if 'typical_speed' in stats:
                print(f"\n   Mode characteristics:")
                print(f"   - Typical speed: {stats['typical_speed']}")
                print(f"   - Max distance in {travel_time} min: {stats['max_distance']}")
                print(f"   - Best for: {stats['best_for']}")
                print(f"   - Equity note: {stats['equity_note']}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[mode] = {'area_km2': 0, 'error': str(e)}

    # ================================================================
    # Part 2: Comparative Analysis
    # ================================================================
    if len(results) >= 2:
        print("\n" + "=" * 70)
        print("PART 2: COMPARATIVE ANALYSIS")
        print("=" * 70)

        # Create comparison table
        print("\n📊 Coverage Comparison Table:")
        print(f"\n{'Mode':<10} {'Area (km²)':<12} {'Radius (km)':<12} {'Relative':<10}")
        print("-" * 50)

        # Sort by area for clear comparison
        sorted_modes = sorted(
            [(m, r['area_km2']) for m, r in results.items() if 'area_km2' in r],
            key=lambda x: x[1]
        )

        if sorted_modes:
            base_area = sorted_modes[0][1] if sorted_modes[0][1] > 0 else 1

            for mode, area in sorted_modes:
                if area > 0:
                    radius = results[mode].get('radius_km', 0)
                    relative = (area / base_area)
                    emoji = mode_emojis.get(mode, '')
                    print(f"{emoji} {mode:<8} {area:<12.2f} {radius:<12.2f} {relative:.1f}x")

        # Key insights
        print("\n💡 KEY INSIGHTS:")

        # Calculate multipliers
        if 'walk' in results and 'drive' in results:
            if results['walk']['area_km2'] > 0:
                drive_walk_ratio = results['drive']['area_km2'] / results['walk']['area_km2']
                print(f"- Driving covers {drive_walk_ratio:.1f}x more area than walking")

        if 'walk' in results and 'bike' in results:
            if results['walk']['area_km2'] > 0:
                bike_walk_ratio = results['bike']['area_km2'] / results['walk']['area_km2']
                print(f"- Biking covers {bike_walk_ratio:.1f}x more area than walking")

        if 'bike' in results and 'drive' in results:
            if results['bike']['area_km2'] > 0:
                drive_bike_ratio = results['drive']['area_km2'] / results['bike']['area_km2']
                print(f"- Driving covers {drive_bike_ratio:.1f}x more area than biking")

        # Equity implications
        print("\n🏛️ EQUITY IMPLICATIONS:")
        print("- Car-dependent areas exclude ~20% without vehicle access")
        print("- Walking-only access limits reach to ~2 km radius")
        print("- Bike infrastructure can 3-4x accessibility at low cost")
        print("- Mixed-mode planning ensures equitable access")

    # ================================================================
    # Part 3: Service Accessibility by Mode
    # ================================================================
    print("\n" + "=" * 70)
    print("PART 3: SERVICE ACCESSIBILITY ANALYSIS")
    print("=" * 70)
    print("\nAnalyzing what services are reachable by each mode...")

    # Service categories to check
    service_categories = {
        'grocery': '🛒 Grocery Stores',
        'pharmacy': '💊 Pharmacies',
        'hospital': '🏥 Hospitals',
        'school': '🏫 Schools'
    }

    service_results = {}

    for category, label in service_categories.items():
        print(f"\n{label}:")

        for mode in modes:
            if mode in isochrones:
                try:
                    # Find POIs reachable by this mode
                    pois = get_poi(
                        location=location,
                        categories=[category],
                        travel_time=travel_time,
                        travel_mode=mode,
                        limit=20
                    )

                    count = len(pois)
                    emoji = mode_emojis.get(mode, '')

                    if mode not in service_results:
                        service_results[mode] = {}
                    service_results[mode][category] = count

                    print(f"   {emoji} {mode}: {count} reachable")

                    # Show closest if any found
                    if pois:
                        closest = pois[0]
                        name = closest.get('name', 'Unknown')
                        dist = closest.get('distance_km', 0)
                        print(f"      Closest: {name[:40]} ({dist:.1f} km)")

                except Exception as e:
                    print(f"   {mode}: Error - {str(e)[:50]}")

    # ================================================================
    # Part 4: Travel Time Scaling Analysis
    # ================================================================
    print("\n" + "=" * 70)
    print("PART 4: TRAVEL TIME SCALING")
    print("=" * 70)
    print("\nHow does coverage area grow with travel time?")

    times = [5, 10, 15, 20, 30]
    time_results = {}

    # Analyze for driving mode (most dramatic scaling)
    print(f"\n🚗 Driving Mode - Time vs Coverage:")
    print(f"{'Time (min)':<12} {'Area (km²)':<12} {'Growth Rate'}")
    print("-" * 40)

    prev_area = 0
    for time in times:
        try:
            iso = create_isochrone(
                location=location,
                travel_time=time,
                travel_mode="drive"
            )
            area = iso['properties']['area_sq_km']
            time_results[time] = area

            if prev_area > 0:
                growth = ((area - prev_area) / prev_area) * 100
                growth_str = f"+{growth:.0f}%"
            else:
                growth_str = "baseline"

            print(f"{time:<12} {area:<12.2f} {growth_str}")
            prev_area = area

        except Exception as e:
            print(f"{time:<12} Error: {str(e)[:30]}")

    # Analyze scaling pattern
    if len(time_results) > 2:
        print("\n📈 SCALING ANALYSIS:")
        # Check if it's roughly quadratic (area ~ time²)
        times_list = sorted(time_results.keys())
        if len(times_list) >= 3:
            t1, t2 = times_list[0], times_list[-1]
            a1, a2 = time_results[t1], time_results[t2]
            time_ratio = t2 / t1
            area_ratio = a2 / a1
            expected_ratio = time_ratio ** 2

            print(f"- Time increased {time_ratio:.1f}x ({t1}→{t2} min)")
            print(f"- Area increased {area_ratio:.1f}x")
            print(f"- Quadratic prediction: {expected_ratio:.1f}x")

            if abs(area_ratio - expected_ratio) / expected_ratio < 0.3:
                print("- ✅ Scaling is approximately quadratic (area ~ time²)")
            else:
                print("- ⚠️  Scaling deviates from quadratic (network constraints)")

    # ================================================================
    # Part 5: Population Coverage Analysis (if Census API available)
    # ================================================================
    print("\n" + "=" * 70)
    print("PART 5: POPULATION COVERAGE BY MODE")
    print("=" * 70)

    try:
        print("\nAnalyzing population reached by each mode...")

        for mode in modes:
            if mode in isochrones:
                print(f"\n{mode_emojis[mode]} {mode.upper()} MODE:")

                # Get census blocks within isochrone
                blocks = get_census_blocks(polygon=isochrones[mode])

                if blocks:
                    geoids = [block['geoid'] for block in blocks]

                    # Get population data
                    census_data = get_census_data(
                        location=geoids,
                        variables=["population"],
                        year=2022
                    )

                    if census_data:
                        total_pop = sum(
                            data.get('population', 0)
                            for data in census_data.values()
                        )
                        print(f"   Population reached: {total_pop:,}")

                        # Calculate density
                        area = results[mode]['area_km2']
                        if area > 0:
                            density = total_pop / area
                            print(f"   Population density: {density:,.0f} people/km²")
                    else:
                        print("   No census data available")
                else:
                    print("   No census blocks found")

    except Exception as e:
        print(f"\n⚠️  Census analysis skipped (API key may be needed)")
        print(f"   Error: {str(e)[:60]}")

    # ================================================================
    # Summary and Learning Points
    # ================================================================
    print("\n" + "=" * 70)
    print("🎉 TUTORIAL COMPLETE!")
    print("=" * 70)

    print("\n📚 WHAT YOU LEARNED:")
    print("1. Travel modes have dramatically different coverage areas")
    print("2. Service accessibility varies significantly by mode")
    print("3. Area scales roughly quadratically with travel time")
    print("4. Transportation equity requires multi-modal planning")
    print("5. Mode choice affects who can access opportunities")

    print("\n🔑 KEY TAKEAWAYS:")
    print("- Walking: Essential for local access, limited range")
    print("- Biking: 3-4x walking range, requires safe infrastructure")
    print("- Driving: Maximum coverage, excludes non-drivers")
    print("- 15-minute threshold captures daily travel patterns")

    print("\n⚠️  COMMON MISTAKES TO AVOID:")
    print("- Assuming everyone has car access (20% don't)")
    print("- Ignoring walking/biking in suburban analysis")
    print("- Using straight-line instead of network distance")
    print("- Not considering time-of-day traffic variations")

    print("\n🚀 NEXT STEPS:")
    print("- Tutorial 03: Analyze demographics within each mode")
    print("- Tutorial 04: Import custom POI data")
    print("- Compare urban vs suburban mode differences")
    print("- Create overlapping isochrone visualizations")

    # Save results for exercises
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    results_file = output_dir / "tutorial02_mode_comparison.json"
    with open(results_file, 'w') as f:
        json.dump({
            'location': location,
            'travel_time': travel_time,
            'mode_areas': {m: r.get('area_km2', 0) for m, r in results.items()},
            'service_counts': service_results
        }, f, indent=2)

    print(f"\n📁 Results saved to: {results_file.absolute()}")
    print("=" * 70)

    return 0


# ================================================================
# EXERCISES SECTION
# ================================================================
"""
EXERCISES: Apply what you've learned!

EXERCISE 1: RUSH HOUR ANALYSIS (Beginner - 10 min)
   Compare travel times during peak vs off-peak hours.
   How does congestion affect driving coverage?

   Hint: Some routing APIs support time-of-day parameters
   Expected: Driving coverage reduces during peak hours

   Solution:
   # Note: This is conceptual - actual implementation depends on API
   peak_iso = create_isochrone(location, 15, "drive")  # peak
   offpeak_iso = create_isochrone(location, 15, "drive")  # off-peak
   reduction = (1 - peak_area/offpeak_area) * 100
   print(f"Peak hour reduces coverage by {reduction:.0f}%")

EXERCISE 2: EQUITY SCORE CALCULATION (Intermediate - 15 min)
   Calculate an "equity score" based on walk vs drive accessibility.
   Score = (POIs reachable by walk) / (POIs reachable by drive)

   Hint: Higher scores mean more equitable access
   Expected: Score between 0.1 and 0.5 for most locations

   Solution:
   walk_pois = get_poi(location, ["grocery", "pharmacy"], 15, "walk")
   drive_pois = get_poi(location, ["grocery", "pharmacy"], 15, "drive")
   equity_score = len(walk_pois) / max(len(drive_pois), 1)
   print(f"Equity Score: {equity_score:.2f}")
   if equity_score > 0.5:
       print("High equity: Good walkable access")
   elif equity_score > 0.2:
       print("Moderate equity: Some walkable access")
   else:
       print("Low equity: Car-dependent area")

EXERCISE 3: MULTI-MODAL JOURNEY (Intermediate - 15 min)
   Simulate park-and-ride: 10 min drive + 5 min walk.
   Compare to 15 min drive alone.

   Hint: Create two isochrones and find overlap
   Expected: Different coverage pattern, possibly better downtown access

   Solution:
   # First leg: 10 min drive from origin
   drive_iso = create_isochrone(location, 10, "drive")

   # For simplicity, use the centroid as transfer point
   # In practice, you'd use actual park-and-ride locations
   transfer_point = (location[0] + 0.05, location[1])  # Example

   # Second leg: 5 min walk from transfer
   walk_iso = create_isochrone(transfer_point, 5, "walk")

   print("Multi-modal coverage combines both isochrones")
   print("Often provides better downtown access than driving alone")

EXERCISE 4: INFRASTRUCTURE IMPACT (Advanced - 20 min)
   Estimate the impact of adding bike lanes.
   Compare current bike coverage to potential with better infrastructure.

   Hint: Increase bike travel speed to simulate protected lanes
   Expected: 20-30% increase in coverage with good infrastructure

   Solution:
   # Current infrastructure (mixed traffic)
   current = create_isochrone(location, 15, "bike")
   current_area = current['properties']['area_sq_km']

   # With protected lanes (faster, more direct)
   # Simulate by using longer time (represents faster speed)
   improved = create_isochrone(location, 18, "bike")  # 20% faster
   improved_area = improved['properties']['area_sq_km']

   improvement = ((improved_area - current_area) / current_area) * 100
   print(f"Protected bike lanes could increase coverage by {improvement:.0f}%")

   # Calculate population benefit
   blocks = get_census_blocks(polygon=improved)
   # ... census analysis ...

EXERCISE 5: MODE CHOICE MODEL (Advanced - 30 min)
   Build a simple mode choice model based on distance and demographics.
   Predict which mode people would choose for different trip types.

   Hint: Use distance thresholds and income data
   Expected: Mode choice varies by trip purpose and demographics

   Solution:
   def predict_mode(distance_km, trip_purpose, median_income):
       # Simple decision tree model
       if trip_purpose == "grocery":
           if distance_km < 1:
               return "walk"
           elif distance_km < 3 and median_income < 50000:
               return "bike"
           else:
               return "drive"
       elif trip_purpose == "work":
           if distance_km < 2:
               return "walk" if median_income < 40000 else "bike"
           elif distance_km < 5:
               return "bike" if median_income < 60000 else "drive"
           else:
               return "drive"
       return "drive"  # default

   # Test the model
   test_cases = [
       (0.5, "grocery", 45000),  # Short grocery trip, modest income
       (4, "work", 70000),       # Medium work commute, high income
       (1.5, "grocery", 30000),  # Short trip, low income
   ]

   for dist, purpose, income in test_cases:
       mode = predict_mode(dist, purpose, income)
       print(f"{dist}km {purpose} trip (${income:,}): {mode}")

CHALLENGE: COMPLETE MODAL ANALYSIS (Advanced - 45 min)
   Create a comprehensive report comparing all three modes across:
   - Coverage area and population
   - Service accessibility (multiple categories)
   - Demographics of covered areas
   - Time-of-day variations
   - Equity implications
   Export as formatted markdown or HTML report.
"""

if __name__ == "__main__":
    sys.exit(main())