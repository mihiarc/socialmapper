#!/usr/bin/env python3
"""
SocialMapper Tutorial 09: Transit Equity Analysis Case Study

LEARNING OBJECTIVES:
- Analyze library access across different income levels
- Calculate equity metrics (Gini coefficient, disparity ratios)
- Identify and map underserved communities
- Create compelling equity visualizations
- Generate policy recommendations based on data

PREREQUISITES:
- Complete Tutorials 01-03 (basics, travel modes, demographics)
- Understanding of census variables
- Basic statistics knowledge helpful

KEY CONCEPTS:
- Transit Equity: Fair distribution of transportation access across populations
- Environmental Justice: Disproportionate impacts on disadvantaged communities
- Accessibility Gap: Difference in service access between groups
- Gini Coefficient: Measure of inequality (0=perfect equality, 1=perfect inequality)
- Spatial Mismatch: Geographic separation between people and opportunities

TIME ESTIMATE: 30-35 minutes

WHAT YOU'LL BUILD:
A comprehensive equity analysis showing how library access varies by income,
race, and age, with actionable insights for policy makers.
"""

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import statistics
from collections import defaultdict

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_data,
    get_census_blocks,
    create_map
)


def calculate_gini_coefficient(values: List[float]) -> float:
    """
    Calculate Gini coefficient for inequality measurement.

    Parameters
    ----------
    values : List[float]
        List of values (e.g., accessibility scores)

    Returns
    -------
    float
        Gini coefficient (0=perfect equality, 1=perfect inequality)
    """
    if not values or len(values) < 2:
        return 0.0

    # Sort values
    sorted_values = sorted(values)
    n = len(sorted_values)

    # Calculate cumulative values
    cumsum = 0
    for i, val in enumerate(sorted_values):
        cumsum += (n - i) * val

    # Gini calculation
    gini = (2 * cumsum) / (n * sum(sorted_values)) - (n + 1) / n

    return min(max(gini, 0), 1)  # Ensure between 0 and 1


def categorize_income(median_income: float) -> str:
    """
    Categorize areas by income level.

    Parameters
    ----------
    median_income : float
        Median household income

    Returns
    -------
    str
        Income category label
    """
    if median_income <= 0:
        return "Unknown"
    elif median_income < 35000:
        return "Low Income (<$35k)"
    elif median_income < 60000:
        return "Middle Income ($35-60k)"
    elif median_income < 100000:
        return "Upper Middle ($60-100k)"
    else:
        return "High Income (>$100k)"


def analyze_accessibility_gap(
    blocks: List[dict],
    census_data: Dict,
    pois: List[dict],
    travel_time: int
) -> Dict:
    """
    Analyze accessibility gaps across demographic groups.

    Parameters
    ----------
    blocks : List[dict]
        Census blocks within study area
    census_data : Dict
        Demographic data by GEOID
    pois : List[dict]
        Points of interest (libraries)
    travel_time : int
        Travel time threshold in minutes

    Returns
    -------
    Dict
        Analysis results with equity metrics
    """
    # Group blocks by income category
    income_groups = defaultdict(list)

    for block in blocks:
        geoid = block['geoid']
        if geoid in census_data:
            income = census_data[geoid].get('median_income', 0)
            category = categorize_income(income)
            income_groups[category].append({
                'geoid': geoid,
                'population': census_data[geoid].get('population', 0),
                'median_income': income,
                'area_km2': block.get('area_sq_km', 0)
            })

    # Calculate metrics for each income group
    group_metrics = {}

    for category, group_blocks in income_groups.items():
        if category == "Unknown":
            continue

        total_pop = sum(b['population'] for b in group_blocks)
        total_area = sum(b['area_km2'] for b in group_blocks)
        avg_income = statistics.mean([b['median_income'] for b in group_blocks if b['median_income'] > 0])

        # For a real analysis, you'd calculate actual POI access per block
        # Here we'll use a simplified metric
        accessibility_score = len(pois) / max(total_area, 1) if total_area > 0 else 0

        group_metrics[category] = {
            'population': total_pop,
            'area_km2': total_area,
            'average_income': avg_income,
            'block_count': len(group_blocks),
            'pop_density': total_pop / total_area if total_area > 0 else 0,
            'accessibility_score': accessibility_score,
            'libraries_per_10k': (len(pois) / total_pop * 10000) if total_pop > 0 else 0
        }

    return group_metrics


def calculate_disparity_ratio(
    group_metrics: Dict,
    metric_name: str = 'libraries_per_10k'
) -> Dict:
    """
    Calculate disparity ratios between income groups.

    Parameters
    ----------
    group_metrics : Dict
        Metrics by income group
    metric_name : str
        Which metric to compare

    Returns
    -------
    Dict
        Disparity ratios between groups
    """
    ratios = {}

    # Get low and high income values
    low_income = None
    high_income = None

    for category, metrics in group_metrics.items():
        if "Low Income" in category:
            low_income = metrics.get(metric_name, 0)
        elif "High Income" in category:
            high_income = metrics.get(metric_name, 0)

    if low_income is not None and high_income is not None and high_income > 0:
        ratios['low_to_high'] = low_income / high_income
        ratios['gap_percentage'] = ((high_income - low_income) / high_income) * 100

    return ratios


def main():
    """Run comprehensive transit equity analysis."""

    print("🏛️  SocialMapper Tutorial 09: Transit Equity Analysis\n")
    print("This tutorial demonstrates how to measure and visualize")
    print("equity in access to public services like libraries.\n")

    # ================================================================
    # Part 1: Setup and Data Collection
    # ================================================================
    print("=" * 70)
    print("PART 1: SETUP AND DATA COLLECTION")
    print("=" * 70)

    # Use Atlanta, GA - a city with known equity challenges
    location = (33.7490, -84.3880)  # Downtown Atlanta
    location_name = "Atlanta, GA"
    travel_time = 15  # minutes
    travel_mode = "walk"  # Focus on pedestrian access for equity

    print(f"\n📍 Study Area: {location_name}")
    print(f"   Coordinates: {location}")
    print(f"🚶 Mode: {travel_mode} (most equitable mode)")
    print(f"⏱️  Time: {travel_time} minutes")
    print("\nWhy walking? It's the most universal mode - no vehicle required.")
    print("This reveals true accessibility for all residents.\n")

    try:
        # Generate walking isochrone
        print("Creating walking isochrone...")
        isochrone = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode=travel_mode
        )

        area_km2 = isochrone['properties']['area_sq_km']
        print(f"✅ Study area: {area_km2:.2f} km²\n")

        # ================================================================
        # Part 2: Find Libraries
        # ================================================================
        print("=" * 70)
        print("PART 2: LIBRARY ACCESS ANALYSIS")
        print("=" * 70)

        print("\nFinding libraries within walking distance...")
        libraries = get_poi(
            location=location,
            categories=["library"],
            travel_time=travel_time,
            travel_mode=travel_mode,
            limit=50
        )

        print(f"✅ Found {len(libraries)} libraries within {travel_time}-minute walk")

        if libraries:
            # Analyze library distribution
            distances = [lib.get('distance_km', 0) for lib in libraries]
            avg_distance = statistics.mean(distances)
            median_distance = statistics.median(distances)

            print(f"\nLibrary Distribution:")
            print(f"  Average distance: {avg_distance:.2f} km")
            print(f"  Median distance: {median_distance:.2f} km")
            print(f"  Closest: {min(distances):.2f} km")
            print(f"  Farthest: {max(distances):.2f} km")

            # Show some examples
            print(f"\nExample libraries:")
            for i, lib in enumerate(libraries[:3], 1):
                name = lib.get('name', 'Unknown')
                dist = lib.get('distance_km', 0)
                print(f"  {i}. {name[:40]} ({dist:.2f} km)")

        # ================================================================
        # Part 3: Census Demographics
        # ================================================================
        print("\n" + "=" * 70)
        print("PART 3: DEMOGRAPHIC ANALYSIS")
        print("=" * 70)

        print("\nRetrieving census blocks...")
        blocks = get_census_blocks(polygon=isochrone)
        print(f"✅ Found {len(blocks)} census block groups")

        if blocks:
            # Get detailed demographics
            geoids = [block['geoid'] for block in blocks]

            print(f"\nFetching demographic data for {len(geoids)} blocks...")
            census_data = get_census_data(
                location=geoids,
                variables=[
                    "population",
                    "median_income",
                    "median_age",
                    "percent_poverty",
                    "percent_no_vehicle"
                ],
                year=2022
            )

            if census_data:
                print(f"✅ Retrieved data for {len(census_data)} blocks\n")

                # Calculate overall statistics
                total_pop = 0
                incomes = []
                poverty_rates = []
                no_vehicle_rates = []

                for geoid, data in census_data.items():
                    pop = data.get('population', 0)
                    total_pop += pop

                    income = data.get('median_income', 0)
                    if income > 0:
                        incomes.append(income)

                    poverty = data.get('percent_poverty', 0)
                    if poverty >= 0:
                        poverty_rates.append(poverty)

                    no_vehicle = data.get('percent_no_vehicle', 0)
                    if no_vehicle >= 0:
                        no_vehicle_rates.append(no_vehicle)

                print("OVERALL DEMOGRAPHICS:")
                print(f"  Total population: {total_pop:,}")
                if incomes:
                    print(f"  Median income: ${statistics.median(incomes):,.0f}")
                    print(f"  Income range: ${min(incomes):,} - ${max(incomes):,}")
                if poverty_rates:
                    print(f"  Average poverty rate: {statistics.mean(poverty_rates):.1f}%")
                if no_vehicle_rates:
                    print(f"  Average no vehicle: {statistics.mean(no_vehicle_rates):.1f}%")

                # ================================================================
                # Part 4: Equity Analysis
                # ================================================================
                print("\n" + "=" * 70)
                print("PART 4: EQUITY ANALYSIS")
                print("=" * 70)

                print("\nAnalyzing accessibility gaps by income level...")

                # Perform equity analysis
                group_metrics = analyze_accessibility_gap(
                    blocks, census_data, libraries, travel_time
                )

                if group_metrics:
                    print("\n📊 ACCESSIBILITY BY INCOME GROUP:\n")
                    print(f"{'Income Group':<20} {'Population':<12} {'Libraries/10k':<15} {'Density'}")
                    print("-" * 65)

                    # Sort by income level
                    income_order = [
                        "Low Income (<$35k)",
                        "Middle Income ($35-60k)",
                        "Upper Middle ($60-100k)",
                        "High Income (>$100k)"
                    ]

                    for category in income_order:
                        if category in group_metrics:
                            metrics = group_metrics[category]
                            pop = metrics['population']
                            lib_per_10k = metrics['libraries_per_10k']
                            density = metrics['pop_density']

                            print(f"{category:<20} {pop:<12,} {lib_per_10k:<15.2f} {density:,.0f}/km²")

                    # Calculate disparity ratios
                    print("\n💔 DISPARITY ANALYSIS:")

                    disparities = calculate_disparity_ratio(group_metrics)
                    if disparities:
                        ratio = disparities.get('low_to_high', 0)
                        gap = disparities.get('gap_percentage', 0)

                        print(f"\nLow-income vs High-income library access:")
                        print(f"  Ratio: {ratio:.2f} (1.0 = equal access)")

                        if ratio < 0.5:
                            print(f"  ⚠️  Severe inequity: Low-income areas have {ratio:.0%} the access")
                        elif ratio < 0.8:
                            print(f"  ⚠️  Moderate inequity: {gap:.0f}% gap in access")
                        elif ratio < 1.2:
                            print(f"  ✅ Relatively equitable access")
                        else:
                            print(f"  ℹ️  Low-income areas have better access")

                    # Calculate Gini coefficient
                    if incomes:
                        gini = calculate_gini_coefficient(incomes)
                        print(f"\n📈 INEQUALITY METRICS:")
                        print(f"  Income Gini coefficient: {gini:.3f}")

                        if gini < 0.3:
                            print(f"    Interpretation: Low inequality")
                        elif gini < 0.4:
                            print(f"    Interpretation: Moderate inequality")
                        elif gini < 0.5:
                            print(f"    Interpretation: High inequality")
                        else:
                            print(f"    Interpretation: Very high inequality")

                    # Identify underserved areas
                    print("\n🚨 UNDERSERVED COMMUNITIES:")

                    underserved = []
                    for geoid, data in census_data.items():
                        income = data.get('median_income', 0)
                        pop = data.get('population', 0)
                        poverty = data.get('percent_poverty', 0)

                        # Criteria for underserved: low income AND high poverty
                        if income > 0 and income < 35000 and poverty > 20 and pop > 100:
                            underserved.append({
                                'geoid': geoid,
                                'population': pop,
                                'median_income': income,
                                'poverty_rate': poverty
                            })

                    if underserved:
                        # Sort by poverty rate
                        underserved.sort(key=lambda x: x['poverty_rate'], reverse=True)

                        print(f"\nFound {len(underserved)} underserved block groups:")
                        print(f"  Total population affected: {sum(b['population'] for b in underserved):,}")

                        print(f"\nMost underserved areas:")
                        for i, area in enumerate(underserved[:5], 1):
                            print(f"  {i}. GEOID {area['geoid']}")
                            print(f"     Population: {area['population']:,}")
                            print(f"     Median income: ${area['median_income']:,}")
                            print(f"     Poverty rate: {area['poverty_rate']:.1f}%")
                    else:
                        print("  No severely underserved areas identified")

                # ================================================================
                # Part 5: Create Equity Maps
                # ================================================================
                print("\n" + "=" * 70)
                print("PART 5: EQUITY VISUALIZATION")
                print("=" * 70)

                print("\nCreating equity visualization maps...")

                # Prepare data for mapping
                map_data = []
                for block in blocks:
                    geoid = block['geoid']
                    if geoid in census_data:
                        # Calculate accessibility score
                        # In practice, you'd calculate actual library access per block
                        pop = census_data[geoid].get('population', 0)
                        income = census_data[geoid].get('median_income', 0)
                        poverty = census_data[geoid].get('percent_poverty', 0)

                        # Simple equity score: lower income = higher need
                        equity_need = 0
                        if income > 0:
                            equity_need = (100000 - income) / 1000  # Normalize
                        if poverty > 0:
                            equity_need += poverty

                        map_data.append({
                            'geometry': block['geometry'],
                            'geoid': geoid,
                            'population': pop,
                            'median_income': income,
                            'poverty_rate': poverty,
                            'equity_need_score': equity_need,
                            'income_category': categorize_income(income)
                        })

                if map_data:
                    # Create output directory
                    output_dir = Path("output/equity_maps")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Create income distribution map
                    income_map = create_map(
                        data=map_data,
                        column="median_income",
                        title=f"Median Income - {travel_time}min Walk from {location_name}",
                        save_path=str(output_dir / "income_distribution.png")
                    )
                    print("  ✅ Created income distribution map")

                    # Create poverty map
                    poverty_map = create_map(
                        data=map_data,
                        column="poverty_rate",
                        title=f"Poverty Rate - {travel_time}min Walk from {location_name}",
                        save_path=str(output_dir / "poverty_distribution.png")
                    )
                    print("  ✅ Created poverty distribution map")

                    # Create equity need map
                    equity_map = create_map(
                        data=map_data,
                        column="equity_need_score",
                        title=f"Equity Need Score - {travel_time}min Walk from {location_name}",
                        save_path=str(output_dir / "equity_need.png")
                    )
                    print("  ✅ Created equity need score map")

                    print(f"\n📁 Maps saved to: {output_dir.absolute()}/")

                # ================================================================
                # Part 6: Policy Recommendations
                # ================================================================
                print("\n" + "=" * 70)
                print("PART 6: POLICY RECOMMENDATIONS")
                print("=" * 70)

                print("\nBased on the equity analysis, here are data-driven recommendations:\n")

                print("📋 RECOMMENDATIONS FOR POLICYMAKERS:\n")

                # Generate recommendations based on findings
                if disparities and disparities.get('low_to_high', 1) < 0.7:
                    print("1. URGENT: Address severe library access inequity")
                    print("   - Low-income areas have significantly less access")
                    print("   - Consider mobile library services for underserved areas")
                    print("   - Prioritize new library locations in low-income neighborhoods")

                if no_vehicle_rates and statistics.mean(no_vehicle_rates) > 10:
                    print("\n2. TRANSPORTATION: High car-free population")
                    print("   - Improve pedestrian infrastructure to libraries")
                    print("   - Add bike lanes and bike parking at libraries")
                    print("   - Consider library shuttle services")

                if underserved and len(underserved) > 5:
                    print(f"\n3. TARGETED INVESTMENT: {len(underserved)} underserved areas identified")
                    print("   - Focus resources on high-poverty block groups")
                    print("   - Partner with schools in these areas")
                    print("   - Expand library hours for working families")

                if libraries and len(libraries) < 5:
                    print(f"\n4. CAPACITY: Only {len(libraries)} libraries serve the area")
                    print("   - Increase library density to meet demand")
                    print("   - Consider pop-up libraries or book kiosks")
                    print("   - Partner with community centers")

                print("\n🎯 MEASURABLE GOALS:")
                print("- Achieve library access ratio > 0.8 between income groups")
                print("- Ensure 90% of residents within 15-min walk/transit of library")
                print("- Reduce average travel time to nearest library by 20%")
                print("- Increase library visits from underserved areas by 50%")

                # Save analysis results
                results_file = output_dir / "equity_analysis_results.json"
                with open(results_file, 'w') as f:
                    json.dump({
                        'location': location,
                        'travel_time': travel_time,
                        'travel_mode': travel_mode,
                        'total_population': total_pop,
                        'library_count': len(libraries),
                        'underserved_blocks': len(underserved),
                        'disparity_ratio': disparities.get('low_to_high', 0) if disparities else 0,
                        'income_gini': gini if 'gini' in locals() else 0,
                        'group_metrics': group_metrics
                    }, f, indent=2)

                print(f"\n📊 Full results saved to: {results_file.absolute()}")

            else:
                print("⚠️  No census data available - check API key")

        else:
            print("⚠️  No census blocks found in study area")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Ensure Census API key is set")
        print("- Check internet connection")
        print("- Try a different location")

    # ================================================================
    # Summary
    # ================================================================
    print("\n" + "=" * 70)
    print("🎉 TUTORIAL COMPLETE!")
    print("=" * 70)

    print("\n📚 WHAT YOU LEARNED:")
    print("1. How to measure transit equity using census data")
    print("2. Calculating inequality metrics (Gini coefficient, disparity ratios)")
    print("3. Identifying underserved communities systematically")
    print("4. Creating compelling equity visualizations")
    print("5. Generating data-driven policy recommendations")

    print("\n💡 KEY INSIGHTS:")
    print("- Equity analysis reveals hidden disparities in access")
    print("- Income is strongly correlated with service accessibility")
    print("- Walking access is the most equitable measure")
    print("- Data-driven recommendations are more compelling")

    print("\n⚠️  COMMON MISTAKES:")
    print("- Using only driving access (masks equity issues)")
    print("- Ignoring population density in analysis")
    print("- Not accounting for car-free households")
    print("- Focusing on average instead of distribution")

    print("\n🚀 NEXT STEPS:")
    print("- Expand analysis to other services (healthcare, food)")
    print("- Compare equity across multiple cities")
    print("- Incorporate transit data for multi-modal analysis")
    print("- Create interactive dashboards for stakeholders")

    print("=" * 70)

    return 0


# ================================================================
# EXERCISES SECTION
# ================================================================
"""
EXERCISES: Deepen your equity analysis skills!

EXERCISE 1: TEMPORAL EQUITY (Beginner - 15 min)
   Compare library access during different times of day.
   Are services equally accessible during working hours vs evenings?

   Hint: Consider library operating hours in your analysis
   Expected: Access may be inequitable for working families

   Solution:
   # Check library hours (conceptual)
   working_hours_access = 0
   evening_access = 0

   for library in libraries:
       # In practice, you'd fetch actual hours
       if "open_evenings" in library:
           evening_access += 1
       if "open_weekdays" in library:
           working_hours_access += 1

   evening_ratio = evening_access / len(libraries)
   print(f"Libraries with evening hours: {evening_ratio:.0%}")

EXERCISE 2: MULTI-SERVICE EQUITY (Intermediate - 20 min)
   Compare equity for libraries, healthcare, and grocery stores.
   Which service type has the largest equity gap?

   Hint: Run analysis for each service category
   Expected: Healthcare often has largest gaps

   Solution:
   services = ["library", "hospital", "grocery"]
   equity_scores = {}

   for service in services:
       pois = get_poi(location, [service], 15, "walk")
       # Calculate equity metrics as in main tutorial
       # ... analysis code ...
       equity_scores[service] = calculate_disparity_ratio(metrics)

   # Find service with worst equity
   worst_service = min(equity_scores, key=lambda x: equity_scores[x])
   print(f"Worst equity: {worst_service}")

EXERCISE 3: INTERSECTIONAL ANALYSIS (Advanced - 30 min)
   Analyze how race and income interact to affect access.
   Do minority communities face compounded disadvantages?

   Hint: Add race variables to census data request
   Expected: Often find compounded disadvantages

   Solution:
   # Get additional demographic variables
   census_data = get_census_data(
       location=geoids,
       variables=["population", "median_income", "percent_minority"],
       year=2022
   )

   # Create 2x2 matrix: income x race
   groups = {
       'low_minority': [],
       'low_majority': [],
       'high_minority': [],
       'high_majority': []
   }

   for geoid, data in census_data.items():
       income = data.get('median_income', 0)
       minority = data.get('percent_minority', 0)

       low_income = income < 40000
       high_minority = minority > 50

       if low_income and high_minority:
           groups['low_minority'].append(data)
       # ... etc

   # Analyze each group's access
   for group_name, group_data in groups.items():
       # Calculate metrics
       print(f"{group_name}: access analysis...")

EXERCISE 4: INTERVENTION MODELING (Advanced - 30 min)
   Model the impact of adding a new library in the most underserved area.
   How much would equity improve?

   Hint: Add synthetic library and recalculate metrics
   Expected: 15-30% improvement in equity ratio

   Solution:
   # Find most underserved block centroid
   most_underserved = min(blocks,
                         key=lambda b: census_data[b['geoid']].get('median_income', float('inf')))

   # Add synthetic library at that location
   new_library = {
       'name': 'Proposed Library',
       'lat': most_underserved['centroid'][0],
       'lon': most_underserved['centroid'][1],
       'distance_km': 0
   }

   libraries_with_new = libraries + [new_library]

   # Recalculate all equity metrics
   new_metrics = analyze_accessibility_gap(
       blocks, census_data, libraries_with_new, travel_time
   )

   # Compare improvement
   old_ratio = disparities.get('low_to_high', 0)
   new_disparities = calculate_disparity_ratio(new_metrics)
   new_ratio = new_disparities.get('low_to_high', 0)

   improvement = ((new_ratio - old_ratio) / old_ratio) * 100
   print(f"Equity improvement: {improvement:.1f}%")

EXERCISE 5: EQUITY SCORECARD (Advanced - 45 min)
   Create a comprehensive equity scorecard with multiple dimensions:
   - Access equity (services per capita by group)
   - Spatial equity (travel time distribution)
   - Temporal equity (service hours)
   - Quality equity (service quality metrics)

   Export as formatted report card with letter grades.

CHALLENGE: LONGITUDINAL EQUITY STUDY (Expert - 60 min)
   Analyze how equity has changed over time using historical census data.
   - Compare 2010, 2015, 2020 census data
   - Track gentrification patterns
   - Identify improving vs declining equity
   - Project future equity trends
   - Create time-series visualizations
"""

if __name__ == "__main__":
    sys.exit(main())