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
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper.api import create_isochrone
from socialmapper import get_census_data_for_polygon, get_demographics_for_polygon
import pandas as pd


def example_1_basic_combination():
    """Combine isochrone with demographic data."""
    print("\n🔗 Example 1: Basic Combination")
    print("-" * 40)
    
    # Step 1: Create isochrone
    print("Step 1: Creating isochrone...")
    isochrone = create_isochrone(
        location="Durham, NC",
        travel_time=15,
        travel_mode="drive"
    )
    print(f"   ✅ Isochrone created")
    
    # Step 2: Get demographics
    print("Step 2: Adding demographic data...")
    demographics = get_demographics_for_polygon(
        polygon=isochrone
    )
    
    if demographics is not None and not demographics.empty:
        print(f"   ✅ Demographics retrieved")
        
        # Step 3: Analyze results
        print("Step 3: Analysis results:")
        total_pop = demographics['B01003_001E'].sum() if 'B01003_001E' in demographics.columns else 0
        print(f"   Population within 15 minutes: {total_pop:,}")
        print(f"   Block groups analyzed: {len(demographics)}")
        
        # Calculate population density
        iso_dict = create_isochrone(
            location="Durham, NC",
            travel_time=15,
            travel_mode="drive",
            return_type="dict"
        )
        area_km2 = iso_dict['properties']['area_sq_km']
        density = total_pop / area_km2 if area_km2 > 0 else 0
        print(f"   Population density: {density:.0f} people/km²")
    else:
        print("   ⚠️ No demographic data available")
    
    return isochrone, demographics


def example_2_accessibility_analysis():
    """Analyze accessibility to different resources."""
    print("\n🏥 Example 2: Resource Accessibility Analysis")
    print("-" * 40)
    
    # Compare accessibility at different travel times
    location = "Cary, NC"
    travel_times = [5, 10, 15]
    results = []
    
    print(f"Analyzing accessibility from {location}:")
    
    for time in travel_times:
        # Create isochrone
        iso_dict = create_isochrone(
            location=location,
            travel_time=time,
            travel_mode="drive",
            return_type="dict"
        )
        
        # Get demographics
        isochrone = create_isochrone(
            location=location,
            travel_time=time,
            travel_mode="drive"
        )
        
        demographics = get_census_data_for_polygon(
            polygon=isochrone,
            variables=["B01003_001E"],  # Total population
            year=2022
        )
        
        population = demographics['B01003_001E'].sum() if demographics is not None and not demographics.empty else 0
        area = iso_dict['properties']['area_sq_km']
        
        results.append({
            'time': time,
            'area_km2': area,
            'population': population,
            'density': population / area if area > 0 else 0
        })
        
        print(f"   {time} min: {population:,} people, {area:.1f} km²")
    
    # Show growth rates
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
    travel_time = 15
    modes = ["drive", "walk", "bike"]
    
    print(f"Comparing {travel_time}-minute access by different modes:")
    
    comparisons = []
    for mode in modes:
        # Create isochrone
        iso_dict = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode=mode,
            return_type="dict"
        )
        
        area = iso_dict['properties']['area_sq_km']
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
    
    # Analyze multiple city centers
    locations = [
        ("Raleigh, NC", "State Capital"),
        ("Durham, NC", "Bull City"),
        ("Chapel Hill, NC", "University Town"),
        ("Cary, NC", "Tech Hub")
    ]
    
    travel_time = 10
    print(f"Analyzing {travel_time}-minute drive access from key locations:")
    
    results = []
    for city, description in locations:
        # Create isochrone
        iso_dict = create_isochrone(
            location=city,
            travel_time=travel_time,
            travel_mode="drive",
            return_type="dict"
        )
        
        area = iso_dict['properties']['area_sq_km']
        results.append({
            'city': city,
            'description': description,
            'area': area
        })
        
        print(f"   {city:20} ({description:15}) → {area:6.2f} km²")
    
    # Find best/worst coverage
    if results:
        best = max(results, key=lambda x: x['area'])
        worst = min(results, key=lambda x: x['area'])
        
        print(f"\n📊 Summary:")
        print(f"   Best coverage:  {best['city']} ({best['area']:.2f} km²)")
        print(f"   Least coverage: {worst['city']} ({worst['area']:.2f} km²)")
    
    return results


def example_5_custom_workflow():
    """Build a custom analysis workflow."""
    print("\n⚙️ Example 5: Custom Analysis Workflow")
    print("-" * 40)
    
    print("Building custom workflow: Transit accessibility analysis")
    
    # Step 1: Define analysis parameters
    print("\n1️⃣ Define parameters:")
    base_location = "NC State University, Raleigh, NC"
    walk_time = 5  # Walk to transit
    transit_time = 15  # Transit ride
    
    print(f"   Base: {base_location}")
    print(f"   Walk time: {walk_time} min")
    print(f"   Transit equivalent: {transit_time} min drive")
    
    # Step 2: Create walking isochrone (to transit stops)
    print("\n2️⃣ Create walking access area:")
    walk_iso = create_isochrone(
        location=base_location,
        travel_time=walk_time,
        travel_mode="walk",
        return_type="dict"
    )
    print(f"   Walking area: {walk_iso['properties']['area_sq_km']:.2f} km²")
    
    # Step 3: Create driving isochrone (simulating transit reach)
    print("\n3️⃣ Create transit-equivalent area:")
    transit_iso = create_isochrone(
        location=base_location,
        travel_time=transit_time,
        travel_mode="drive",
        return_type="dict"
    )
    print(f"   Transit reach: {transit_iso['properties']['area_sq_km']:.2f} km²")
    
    # Step 4: Get demographics for transit area
    print("\n4️⃣ Analyze demographics:")
    isochrone_gdf = create_isochrone(
        location=base_location,
        travel_time=transit_time,
        travel_mode="drive"
    )
    
    demographics = get_census_data_for_polygon(
        polygon=isochrone_gdf,
        variables=["B01003_001E", "B08301_010E"],  # Population & transit users
        year=2022
    )
    
    if demographics is not None and not demographics.empty:
        total_pop = demographics['B01003_001E'].sum() if 'B01003_001E' in demographics.columns else 0
        transit_users = demographics['B08301_010E'].sum() if 'B08301_010E' in demographics.columns else 0
        
        print(f"   Population reached: {total_pop:,}")
        print(f"   Existing transit users: {transit_users:,}")
        
        if total_pop > 0:
            transit_rate = (transit_users / total_pop) * 100
            print(f"   Transit usage rate: {transit_rate:.1f}%")
    else:
        print("   ⚠️ Demographics not available")
    
    print("\n5️⃣ Analysis complete!")
    
    return walk_iso, transit_iso, demographics


def main():
    """Run all examples."""
    print("=" * 50)
    print("🔗 SIMPLE TUTORIAL: COMBINING ANALYSIS")
    print("=" * 50)
    print("\nCombine spatial and demographic analysis")
    print("Build powerful insights with simple functions!")
    
    # Check for Census API key
    if not os.getenv('CENSUS_API_KEY'):
        print("\n⚠️ WARNING: Census API key not found")
        print("Demographics will be limited without API key")
        print("Get free key: https://api.census.gov/data/key_signup.html")
    
    try:
        # Run examples
        example_1_basic_combination()
        example_2_accessibility_analysis()
        example_3_mode_comparison()
        example_4_multi_location()
        example_5_custom_workflow()
        
        print("\n" + "=" * 50)
        print("✨ Tutorial completed!")
        print("\nKey takeaways:")
        print("1. Combine isochrones with demographics easily")
        print("2. Compare different modes and locations")
        print("3. Build custom analysis workflows")
        print("4. Simple functions, powerful results")
        print("5. Composable API for flexibility!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check Census API key is set")
        print("2. Verify internet connection")
        print("3. Try simpler parameters")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())