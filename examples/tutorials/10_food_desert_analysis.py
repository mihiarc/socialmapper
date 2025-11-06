#!/usr/bin/env python3
"""
SocialMapper Tutorial 10: Food Desert Analysis and Research

LEARNING OBJECTIVES:
- Identify food deserts using USDA criteria
- Analyze food access by transportation mode and demographics
- Compare grocery stores vs convenience stores vs farmers markets
- Calculate health impact metrics
- Generate policy recommendations for food security

PREREQUISITES:
- Complete Tutorials 01-03 (basics)
- Understanding of census data
- Familiarity with public health concepts helpful

KEY CONCEPTS:
- Food Desert: Area with limited access to affordable, nutritious food
- USDA Definition: Low-income + low-access (>1 mile urban, >10 miles rural)
- Food Swamp: Area with abundance of unhealthy food options
- Food Apartheid: Systematic inequity in food access
- Healthy Food Financing Initiative: Federal program addressing food deserts

TIME ESTIMATE: 35-40 minutes

WHAT YOU'LL BUILD:
A comprehensive food access analysis identifying food deserts, analyzing
demographics, and providing actionable recommendations for improving food security.
"""

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
import math

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_data,
    get_census_blocks,
    create_map
)


@dataclass
class FoodAccessMetrics:
    """Container for food access analysis metrics."""
    total_population: int
    low_access_population: int
    low_income_population: int
    food_desert_population: int
    grocery_stores: int
    convenience_stores: int
    farmers_markets: int
    snap_retailers: int
    avg_distance_to_grocery: float
    percent_no_vehicle: float
    percent_seniors: float
    percent_children: float
    health_score: float


def classify_food_retailer(poi: dict) -> str:
    """
    Classify a POI as a type of food retailer.

    Parameters
    ----------
    poi : dict
        Point of interest data

    Returns
    -------
    str
        Food retailer category
    """
    name = poi.get('name', '').lower()
    categories = poi.get('categories', [])

    # Check for grocery stores (full-service)
    grocery_keywords = ['grocery', 'supermarket', 'whole foods', 'kroger',
                       'safeway', 'publix', 'wegmans', 'trader joe']
    if any(keyword in name for keyword in grocery_keywords):
        return 'grocery_store'

    # Check for convenience stores (limited healthy options)
    convenience_keywords = ['convenience', '7-eleven', 'wawa', 'circle k',
                          'gas station', 'mini mart', 'quickmart']
    if any(keyword in name for keyword in convenience_keywords):
        return 'convenience_store'

    # Check for farmers markets (fresh, local)
    if 'farmers' in name or 'market' in name and 'farmer' in name:
        return 'farmers_market'

    # Check for discount stores with food
    discount_keywords = ['dollar', 'discount', 'walmart', 'target']
    if any(keyword in name for keyword in discount_keywords):
        return 'discount_store'

    # Default to general food retailer
    return 'food_retailer'


def calculate_food_desert_criteria(
    census_data: Dict,
    food_access: Dict[str, List],
    urban: bool = True
) -> Tuple[Set[str], Dict]:
    """
    Identify food desert areas using USDA criteria.

    Parameters
    ----------
    census_data : Dict
        Census data by GEOID
    food_access : Dict
        Food retailers accessible from each block
    urban : bool
        Whether area is urban (True) or rural (False)

    Returns
    -------
    Tuple[Set[str], Dict]
        Set of food desert GEOIDs and detailed metrics
    """
    # USDA thresholds
    low_income_threshold = 0.20  # 20% poverty rate OR median income < 80% state median
    low_access_distance = 1.0 if urban else 10.0  # miles

    food_deserts = set()
    desert_metrics = {}

    for geoid, data in census_data.items():
        # Check low-income criteria
        poverty_rate = data.get('percent_poverty', 0)
        median_income = data.get('median_income', 0)

        # For simplicity, using fixed income threshold
        # In practice, you'd compare to state median
        is_low_income = (poverty_rate > 20) or (median_income < 35000 and median_income > 0)

        # Check low-access criteria
        has_grocery = geoid in food_access.get('grocery_store', [])
        min_distance = food_access.get(f'{geoid}_min_distance', float('inf'))

        # Convert km to miles
        min_distance_miles = min_distance * 0.621371

        is_low_access = (not has_grocery) or (min_distance_miles > low_access_distance)

        # Food desert = low income AND low access
        if is_low_income and is_low_access:
            food_deserts.add(geoid)

            desert_metrics[geoid] = {
                'population': data.get('population', 0),
                'poverty_rate': poverty_rate,
                'median_income': median_income,
                'distance_to_grocery': min_distance_miles,
                'is_food_desert': True
            }

    return food_deserts, desert_metrics


def calculate_health_impact_score(
    metrics: FoodAccessMetrics
) -> float:
    """
    Calculate a health impact score based on food access metrics.

    Parameters
    ----------
    metrics : FoodAccessMetrics
        Food access metrics for an area

    Returns
    -------
    float
        Health impact score (0-100, higher is better)
    """
    score = 100.0

    # Penalize for lack of grocery stores
    if metrics.grocery_stores == 0:
        score -= 30
    else:
        # Ideal: 1 grocery per 2,500 people
        grocery_ratio = metrics.grocery_stores / max(metrics.total_population / 2500, 1)
        score -= max(0, 10 * (1 - grocery_ratio))

    # Penalize for high convenience store ratio
    if metrics.grocery_stores > 0:
        unhealthy_ratio = metrics.convenience_stores / metrics.grocery_stores
        if unhealthy_ratio > 2:
            score -= 10  # Food swamp penalty

    # Penalize for distance
    if metrics.avg_distance_to_grocery > 2:  # km
        score -= min(20, metrics.avg_distance_to_grocery * 5)

    # Penalize for vulnerable populations without vehicle
    vulnerable_factor = (metrics.percent_seniors + metrics.percent_children) / 100
    no_vehicle_penalty = metrics.percent_no_vehicle * vulnerable_factor * 0.2
    score -= no_vehicle_penalty

    # Bonus for farmers markets
    if metrics.farmers_markets > 0:
        score += min(5, metrics.farmers_markets * 2)

    return max(0, min(100, score))


def main():
    """Run comprehensive food desert analysis."""

    print("🥗 SocialMapper Tutorial 10: Food Desert Analysis\n")
    print("This tutorial demonstrates how to identify food deserts")
    print("and analyze food access equity in urban communities.\n")

    # ================================================================
    # Part 1: Setup and Study Area Definition
    # ================================================================
    print("=" * 70)
    print("PART 1: SETUP AND STUDY AREA DEFINITION")
    print("=" * 70)

    # Use Phoenix, AZ - known for food desert challenges
    location = (33.4484, -112.0740)  # Downtown Phoenix
    location_name = "Phoenix, AZ"
    is_urban = True

    print(f"\n📍 Study Area: {location_name}")
    print(f"   Coordinates: {location}")
    print(f"🏙️  Classification: {'Urban' if is_urban else 'Rural'}")
    print(f"📏 USDA Threshold: {1 if is_urban else 10} mile to grocery\n")

    # Define analysis parameters
    walk_time = 15  # minutes
    drive_time = 10  # minutes

    print("Analysis Parameters:")
    print(f"  Walking radius: {walk_time} minutes")
    print(f"  Driving radius: {drive_time} minutes")
    print("  Focus: Full-service grocery stores vs food deserts\n")

    try:
        # ================================================================
        # Part 2: Multi-Modal Food Access Analysis
        # ================================================================
        print("=" * 70)
        print("PART 2: MULTI-MODAL FOOD ACCESS")
        print("=" * 70)

        # Analyze walking access (equity focus)
        print("\n🚶 WALKING ACCESS (15 minutes):")

        walk_iso = create_isochrone(
            location=location,
            travel_time=walk_time,
            travel_mode="walk"
        )

        walk_area = walk_iso['properties']['area_sq_km']
        print(f"  Coverage area: {walk_area:.2f} km²")

        # Find food retailers within walking distance
        walk_food = get_poi(
            location=location,
            categories=["grocery", "supermarket", "food", "market"],
            travel_time=walk_time,
            travel_mode="walk",
            limit=100
        )

        # Classify food retailers
        walk_food_types = defaultdict(list)
        for poi in walk_food:
            food_type = classify_food_retailer(poi)
            walk_food_types[food_type].append(poi)

        print(f"\n  Food Retailers (Walking):")
        for food_type, pois in walk_food_types.items():
            print(f"    {food_type.replace('_', ' ').title()}: {len(pois)}")

        # Analyze driving access
        print("\n🚗 DRIVING ACCESS (10 minutes):")

        drive_iso = create_isochrone(
            location=location,
            travel_time=drive_time,
            travel_mode="drive"
        )

        drive_area = drive_iso['properties']['area_sq_km']
        print(f"  Coverage area: {drive_area:.2f} km²")

        # Find food retailers within driving distance
        drive_food = get_poi(
            location=location,
            categories=["grocery", "supermarket", "food", "market"],
            travel_time=drive_time,
            travel_mode="drive",
            limit=100
        )

        # Classify food retailers
        drive_food_types = defaultdict(list)
        for poi in drive_food:
            food_type = classify_food_retailer(poi)
            drive_food_types[food_type].append(poi)

        print(f"\n  Food Retailers (Driving):")
        for food_type, pois in drive_food_types.items():
            print(f"    {food_type.replace('_', ' ').title()}: {len(pois)}")

        # Calculate access disparity
        walk_grocery = len(walk_food_types.get('grocery_store', []))
        drive_grocery = len(drive_food_types.get('grocery_store', []))

        if drive_grocery > 0:
            access_ratio = walk_grocery / drive_grocery
            print(f"\n📊 Access Disparity:")
            print(f"  Walk/Drive grocery ratio: {access_ratio:.2%}")
            if access_ratio < 0.2:
                print("  ⚠️  Severe car-dependency for food access")
            elif access_ratio < 0.5:
                print("  ⚠️  Moderate car-dependency")
            else:
                print("  ✅ Relatively walkable food access")

        # ================================================================
        # Part 3: Census Demographics and Vulnerable Populations
        # ================================================================
        print("\n" + "=" * 70)
        print("PART 3: DEMOGRAPHIC ANALYSIS")
        print("=" * 70)

        print("\nAnalyzing demographics within food access areas...")

        # Get census blocks for walking area (most restrictive)
        blocks = get_census_blocks(polygon=walk_iso)
        print(f"  Found {len(blocks)} census block groups")

        if blocks:
            geoids = [block['geoid'] for block in blocks]

            # Get comprehensive demographics
            census_data = get_census_data(
                location=geoids,
                variables=[
                    "population",
                    "median_income",
                    "percent_poverty",
                    "percent_no_vehicle",
                    "percent_seniors",
                    "percent_children",
                    "percent_snap"  # SNAP recipients
                ],
                year=2022
            )

            if census_data:
                print(f"  Retrieved data for {len(census_data)} blocks\n")

                # Calculate vulnerable population statistics
                total_pop = 0
                total_poverty = 0
                total_no_vehicle = 0
                total_seniors = 0
                total_children = 0
                total_snap = 0

                for geoid, data in census_data.items():
                    pop = data.get('population', 0)
                    total_pop += pop

                    # Calculate vulnerable populations
                    poverty_rate = data.get('percent_poverty', 0)
                    total_poverty += pop * poverty_rate / 100

                    no_vehicle_rate = data.get('percent_no_vehicle', 0)
                    total_no_vehicle += pop * no_vehicle_rate / 100

                    senior_rate = data.get('percent_seniors', 0)
                    total_seniors += pop * senior_rate / 100

                    child_rate = data.get('percent_children', 0)
                    total_children += pop * child_rate / 100

                    snap_rate = data.get('percent_snap', 0)
                    total_snap += pop * snap_rate / 100

                print("VULNERABLE POPULATIONS:")
                print(f"  Total population: {total_pop:,}")
                print(f"  Living in poverty: {total_poverty:,.0f} ({total_poverty/total_pop*100:.1f}%)")
                print(f"  No vehicle access: {total_no_vehicle:,.0f} ({total_no_vehicle/total_pop*100:.1f}%)")
                print(f"  Seniors (65+): {total_seniors:,.0f} ({total_seniors/total_pop*100:.1f}%)")
                print(f"  Children (<18): {total_children:,.0f} ({total_children/total_pop*100:.1f}%)")
                print(f"  SNAP recipients: {total_snap:,.0f} ({total_snap/total_pop*100:.1f}%)")

                # ================================================================
                # Part 4: Food Desert Identification
                # ================================================================
                print("\n" + "=" * 70)
                print("PART 4: FOOD DESERT IDENTIFICATION")
                print("=" * 70)

                print("\nApplying USDA food desert criteria...")
                print("  Criteria: Low-income AND low-access")
                print(f"  Low-income: >20% poverty OR median income <$35k")
                print(f"  Low-access: >1 mile to grocery (urban)\n")

                # Build food access map by block
                food_access_by_block = defaultdict(list)
                min_distances = {}

                # For each block, find nearest grocery
                for block in blocks:
                    geoid = block['geoid']
                    # Simplified: use block centroid
                    # In practice, you'd calculate actual centroid
                    block_center = location  # Simplified

                    # Find nearest grocery store
                    min_dist = float('inf')
                    for poi in walk_food_types.get('grocery_store', []):
                        dist = poi.get('distance_km', float('inf'))
                        min_dist = min(min_dist, dist)

                    min_distances[f'{geoid}_min_distance'] = min_dist

                    if min_dist < 1.6:  # Within 1 mile (1.6 km)
                        food_access_by_block['grocery_store'].append(geoid)

                # Identify food deserts
                food_deserts, desert_metrics = calculate_food_desert_criteria(
                    census_data,
                    food_access_by_block,
                    urban=is_urban
                )

                if food_deserts:
                    desert_population = sum(
                        census_data[geoid].get('population', 0)
                        for geoid in food_deserts
                    )

                    print(f"🏜️  FOOD DESERTS IDENTIFIED:")
                    print(f"  Block groups: {len(food_deserts)}")
                    print(f"  Population affected: {desert_population:,}")
                    print(f"  Percent of total: {desert_population/total_pop*100:.1f}%")

                    # Show worst areas
                    print(f"\n  Most severe food deserts:")
                    worst_deserts = sorted(
                        desert_metrics.items(),
                        key=lambda x: x[1]['distance_to_grocery'],
                        reverse=True
                    )[:5]

                    for i, (geoid, metrics) in enumerate(worst_deserts, 1):
                        print(f"\n  {i}. GEOID: {geoid}")
                        print(f"     Population: {metrics['population']:,}")
                        print(f"     Poverty rate: {metrics['poverty_rate']:.1f}%")
                        print(f"     Distance to grocery: {metrics['distance_to_grocery']:.1f} miles")
                else:
                    print("✅ No food deserts identified in study area")

                # ================================================================
                # Part 5: Health Impact Assessment
                # ================================================================
                print("\n" + "=" * 70)
                print("PART 5: HEALTH IMPACT ASSESSMENT")
                print("=" * 70)

                print("\nCalculating health impact scores...")

                # Calculate overall metrics
                overall_metrics = FoodAccessMetrics(
                    total_population=total_pop,
                    low_access_population=len(food_deserts) * (total_pop // len(blocks)) if blocks else 0,
                    low_income_population=int(total_poverty),
                    food_desert_population=sum(
                        census_data[g].get('population', 0)
                        for g in food_deserts
                    ) if food_deserts else 0,
                    grocery_stores=walk_grocery,
                    convenience_stores=len(walk_food_types.get('convenience_store', [])),
                    farmers_markets=len(walk_food_types.get('farmers_market', [])),
                    snap_retailers=len([p for p in walk_food if 'snap' in str(p).lower()]),
                    avg_distance_to_grocery=statistics.mean(
                        min_distances.values()
                    ) if min_distances else 0,
                    percent_no_vehicle=(total_no_vehicle/total_pop*100) if total_pop > 0 else 0,
                    percent_seniors=(total_seniors/total_pop*100) if total_pop > 0 else 0,
                    percent_children=(total_children/total_pop*100) if total_pop > 0 else 0,
                    health_score=0  # Calculate below
                )

                # Calculate health score
                health_score = calculate_health_impact_score(overall_metrics)
                overall_metrics.health_score = health_score

                print(f"\n🏥 HEALTH IMPACT SCORE: {health_score:.1f}/100")

                if health_score >= 80:
                    print("  Grade: A - Excellent food access")
                elif health_score >= 70:
                    print("  Grade: B - Good food access")
                elif health_score >= 60:
                    print("  Grade: C - Moderate food access")
                elif health_score >= 50:
                    print("  Grade: D - Poor food access")
                else:
                    print("  Grade: F - Critical food access issues")

                print("\n  Score Breakdown:")
                print(f"    Grocery store density: {walk_grocery} stores")
                print(f"    Average distance: {overall_metrics.avg_distance_to_grocery:.2f} km")
                print(f"    Food swamp risk: {overall_metrics.convenience_stores}/{walk_grocery} ratio")
                print(f"    Vulnerable population: {overall_metrics.percent_no_vehicle:.1f}% without vehicle")

                # Check for food swamp conditions
                if walk_grocery > 0:
                    swamp_ratio = overall_metrics.convenience_stores / walk_grocery
                    if swamp_ratio > 3:
                        print("\n  ⚠️  FOOD SWAMP DETECTED:")
                        print(f"    Convenience stores outnumber grocery {swamp_ratio:.1f}:1")
                        print("    High availability of unhealthy options")
                        print("    Increased risk of diet-related diseases")

                # ================================================================
                # Part 6: Visualization
                # ================================================================
                print("\n" + "=" * 70)
                print("PART 6: FOOD ACCESS VISUALIZATION")
                print("=" * 70)

                print("\nCreating food access maps...")

                # Prepare map data
                map_data = []
                for block in blocks:
                    geoid = block['geoid']
                    if geoid in census_data:
                        # Determine food access status
                        is_desert = geoid in food_deserts
                        distance = min_distances.get(f'{geoid}_min_distance', 0)

                        map_data.append({
                            'geometry': block['geometry'],
                            'geoid': geoid,
                            'population': census_data[geoid].get('population', 0),
                            'poverty_rate': census_data[geoid].get('percent_poverty', 0),
                            'food_desert': 1 if is_desert else 0,
                            'grocery_distance': distance,
                            'no_vehicle_rate': census_data[geoid].get('percent_no_vehicle', 0)
                        })

                if map_data:
                    output_dir = Path("output/food_access")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Create food desert map
                    desert_map = create_map(
                        data=map_data,
                        column="food_desert",
                        title=f"Food Deserts - {location_name}",
                        save_path=str(output_dir / "food_deserts.png")
                    )
                    print("  ✅ Created food desert map")

                    # Create grocery distance map
                    distance_map = create_map(
                        data=map_data,
                        column="grocery_distance",
                        title=f"Distance to Nearest Grocery (km) - {location_name}",
                        save_path=str(output_dir / "grocery_distance.png")
                    )
                    print("  ✅ Created grocery distance map")

                    # Create vehicle access map
                    vehicle_map = create_map(
                        data=map_data,
                        column="no_vehicle_rate",
                        title=f"Households Without Vehicle (%) - {location_name}",
                        save_path=str(output_dir / "no_vehicle_access.png")
                    )
                    print("  ✅ Created vehicle access map")

                    print(f"\n📁 Maps saved to: {output_dir.absolute()}/")

                # ================================================================
                # Part 7: Policy Recommendations
                # ================================================================
                print("\n" + "=" * 70)
                print("PART 7: POLICY RECOMMENDATIONS")
                print("=" * 70)

                print("\n📋 DATA-DRIVEN POLICY RECOMMENDATIONS:\n")

                # Generate targeted recommendations
                if len(food_deserts) > 0:
                    print("1. ADDRESS FOOD DESERTS (URGENT)")
                    print(f"   - {len(food_deserts)} areas lack adequate food access")
                    print(f"   - {desert_population:,} residents affected")
                    print("   Actions:")
                    print("   • Incentivize grocery stores in underserved areas")
                    print("   • Support mobile markets and food co-ops")
                    print("   • Expand SNAP retailer network")

                if overall_metrics.percent_no_vehicle > 15:
                    print("\n2. IMPROVE TRANSPORTATION ACCESS")
                    print(f"   - {overall_metrics.percent_no_vehicle:.1f}% lack vehicle access")
                    print("   Actions:")
                    print("   • Create grocery shuttle services")
                    print("   • Improve transit routes to food retailers")
                    print("   • Support grocery delivery programs for seniors")

                if overall_metrics.convenience_stores > walk_grocery * 2:
                    print("\n3. COMBAT FOOD SWAMP CONDITIONS")
                    print(f"   - Unhealthy options dominate ({overall_metrics.convenience_stores} convenience stores)")
                    print("   Actions:")
                    print("   • Healthy corner store initiatives")
                    print("   • Require healthy food in convenience stores")
                    print("   • Support urban agriculture programs")

                if overall_metrics.farmers_markets < 2:
                    print("\n4. EXPAND FRESH FOOD OPTIONS")
                    print(f"   - Only {overall_metrics.farmers_markets} farmers markets found")
                    print("   Actions:")
                    print("   • Establish weekly farmers markets")
                    print("   • Create community gardens")
                    print("   • Support farm-to-table programs")

                print("\n🎯 MEASURABLE GOALS:")
                print("- Eliminate food deserts within 2 years")
                print("- Achieve <1 mile average distance to grocery")
                print("- Ensure 1 grocery store per 2,500 residents")
                print("- Reduce food insecurity by 30%")
                print("- Increase SNAP redemption at farmers markets by 50%")

                print("\n💰 FUNDING OPPORTUNITIES:")
                print("- USDA Healthy Food Financing Initiative")
                print("- Community Development Block Grants")
                print("- New Markets Tax Credits")
                print("- Local Food Promotion Program")
                print("- SNAP retailer equipment grants")

                # Save comprehensive results
                results_file = output_dir / "food_access_analysis.json"
                with open(results_file, 'w') as f:
                    json.dump({
                        'location': location,
                        'location_name': location_name,
                        'total_population': total_pop,
                        'food_desert_population': overall_metrics.food_desert_population,
                        'food_desert_blocks': list(food_deserts),
                        'health_score': health_score,
                        'grocery_stores': walk_grocery,
                        'convenience_stores': overall_metrics.convenience_stores,
                        'avg_distance_km': overall_metrics.avg_distance_to_grocery,
                        'percent_no_vehicle': overall_metrics.percent_no_vehicle,
                        'recommendations': [
                            "Address food deserts",
                            "Improve transportation",
                            "Combat food swamps",
                            "Expand fresh options"
                        ]
                    }, f, indent=2)

                print(f"\n📊 Analysis results saved to: {results_file.absolute()}")

            else:
                print("⚠️  No census data available")

        else:
            print("⚠️  No census blocks found")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check Census API key")
        print("- Verify internet connection")
        print("- Try different location")

    # ================================================================
    # Summary
    # ================================================================
    print("\n" + "=" * 70)
    print("🎉 TUTORIAL COMPLETE!")
    print("=" * 70)

    print("\n📚 WHAT YOU LEARNED:")
    print("1. How to identify food deserts using USDA criteria")
    print("2. Analyzing multi-modal food access patterns")
    print("3. Assessing vulnerable populations and food security")
    print("4. Calculating health impact scores")
    print("5. Generating evidence-based policy recommendations")

    print("\n💡 KEY INSIGHTS:")
    print("- Food access is a critical social determinant of health")
    print("- Transportation is key barrier to food security")
    print("- Food swamps can be as harmful as food deserts")
    print("- Solutions require multi-sector collaboration")

    print("\n⚠️  COMMON PITFALLS:")
    print("- Focusing only on distance, not quality of food")
    print("- Ignoring transportation barriers")
    print("- Not considering operating hours and prices")
    print("- Missing cultural food preferences")

    print("\n🚀 NEXT STEPS:")
    print("- Compare food access across multiple cities")
    print("- Analyze correlation with health outcomes")
    print("- Model impact of proposed interventions")
    print("- Create interactive food access dashboard")

    print("=" * 70)

    return 0


# ================================================================
# EXERCISES SECTION
# ================================================================
"""
EXERCISES: Deepen your food security analysis skills!

EXERCISE 1: FOOD QUALITY ASSESSMENT (Beginner - 15 min)
   Differentiate between healthy and unhealthy food retailers.
   Calculate a "food quality index" for the area.

   Hint: Weight grocery stores positively, fast food negatively
   Expected: Quality index between 0-100

   Solution:
   healthy_points = grocery_stores * 10 + farmers_markets * 5
   unhealthy_points = convenience_stores * -5 + fast_food * -3
   quality_index = max(0, min(100, 50 + healthy_points + unhealthy_points))
   print(f"Food Quality Index: {quality_index}/100")

EXERCISE 2: TIME-BASED ACCESS (Intermediate - 20 min)
   Analyze how food access changes throughout the day.
   Many stores have limited hours affecting working families.

   Hint: Check store hours and overlap with work schedules
   Expected: Significant reduction in evening/weekend access

   Solution:
   evening_stores = 0
   weekend_stores = 0

   for store in grocery_stores:
       # In practice, fetch actual hours from API
       if "24 hour" in store.name or "late" in store.name:
           evening_stores += 1
       if "sunday" not in store.get("closed_days", []):
           weekend_stores += 1

   evening_access = evening_stores / len(grocery_stores)
   weekend_access = weekend_stores / len(grocery_stores)
   print(f"Evening access: {evening_access:.0%}")
   print(f"Weekend access: {weekend_access:.0%}")

EXERCISE 3: PRICE ANALYSIS (Intermediate - 25 min)
   Compare food prices between different store types.
   Calculate affordability for low-income residents.

   Hint: Convenience stores often 20-40% more expensive
   Expected: Significant price disparities

   Solution:
   # Conceptual - would need price data API
   store_prices = {
       'grocery_store': 1.0,  # baseline
       'convenience_store': 1.35,  # 35% markup
       'farmers_market': 1.15,  # 15% premium
       'discount_store': 0.90  # 10% discount
   }

   # Calculate weighted average price index
   total_stores = sum(len(stores) for stores in food_types.values())
   weighted_price = sum(
       len(stores) * store_prices.get(store_type, 1.0)
       for store_type, stores in food_types.items()
   ) / total_stores

   print(f"Area price index: {weighted_price:.2f}")
   if weighted_price > 1.2:
       print("High prices burden low-income residents")

EXERCISE 4: INTERVENTION MODELING (Advanced - 30 min)
   Model the impact of adding a new grocery store or farmers market.
   Calculate reduction in food desert population.

   Hint: Place new store in centroid of largest food desert
   Expected: 20-40% reduction in affected population

   Solution:
   # Find optimal location for new store
   if food_deserts:
       # Get centroid of largest desert
       largest_desert = max(food_deserts,
           key=lambda g: census_data[g].get('population', 0))

       # Add hypothetical store
       new_store_location = calculate_centroid(largest_desert)

       # Recalculate food deserts with new store
       updated_access = food_access_by_block.copy()
       for block in blocks:
           distance = calculate_distance(block, new_store_location)
           if distance < 1.6:  # 1 mile
               updated_access['grocery_store'].append(block['geoid'])

       new_deserts, _ = calculate_food_desert_criteria(
           census_data, updated_access, is_urban
       )

       reduction = len(food_deserts) - len(new_deserts)
       print(f"New store would eliminate {reduction} food deserts")

       pop_reduction = sum(
           census_data[g].get('population', 0)
           for g in (food_deserts - new_deserts)
       )
       print(f"Population no longer in food desert: {pop_reduction:,}")

EXERCISE 5: CULTURAL FOOD ACCESS (Advanced - 35 min)
   Analyze access to culturally appropriate food for different communities.
   Important for immigrant and minority populations.

   Hint: Search for ethnic grocery stores, halal/kosher markets
   Expected: Often limited cultural food access

   Solution:
   cultural_stores = {
       'asian': ['asian market', 'chinese', 'korean', 'japanese'],
       'latin': ['mexican', 'latino', 'bodega', 'carniceria'],
       'halal': ['halal', 'muslim', 'middle eastern'],
       'kosher': ['kosher', 'jewish']
   }

   cultural_access = {}
   for culture, keywords in cultural_stores.items():
       stores = get_poi(location, keywords, 15, "walk")
       cultural_access[culture] = len(stores)
       print(f"{culture.title()} food stores: {len(stores)}")

   # Compare to demographics
   # Would need census data on ethnicity/race
   print("\nCultural food gaps identified")

CHALLENGE: COMPREHENSIVE FOOD SYSTEM ANALYSIS (Expert - 60 min)
   Create a complete food system assessment including:
   - Production (urban farms, gardens)
   - Distribution (stores, markets)
   - Consumption (restaurants, schools)
   - Waste (composting, food rescue)
   - Create a food system scorecard
   - Generate strategic plan for food security
   - Include climate resilience factors
"""

if __name__ == "__main__":
    sys.exit(main())