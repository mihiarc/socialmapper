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
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper.api import create_isochrone
from socialmapper import get_census_data_for_polygon
import pandas as pd
from typing import List, Dict, Tuple


def example_1_batch_processing():
    """Process multiple locations efficiently."""
    print("\n⚡ Example 1: Batch Processing")
    print("-" * 40)
    
    # List of libraries in the Triangle area
    libraries = [
        ("Cameron Village Regional Library", (35.7895, -78.6565)),
        ("Eva Perry Regional Library", (35.9049, -78.9984)),
        ("Southeast Regional Library", (35.7215, -78.6469)),
        ("North Regional Library", (35.8437, -78.6435))
    ]
    
    print(f"Processing {len(libraries)} library locations:")
    
    results = []
    for name, coords in libraries:
        # Create isochrone for each library
        iso_dict = create_isochrone(
            location=coords,
            travel_time=10,
            travel_mode="drive",
            return_type="dict"
        )
        
        area = iso_dict['properties']['area_sq_km']
        results.append({
            'name': name,
            'lat': coords[0],
            'lon': coords[1],
            'area_km2': area
        })
        
        print(f"   ✅ {name[:30]:30} → {area:.2f} km²")
    
    # Create DataFrame for analysis
    df = pd.DataFrame(results)
    
    print(f"\n📊 Summary Statistics:")
    print(f"   Average coverage: {df['area_km2'].mean():.2f} km²")
    print(f"   Total coverage: {df['area_km2'].sum():.2f} km²")
    print(f"   Coverage range: {df['area_km2'].min():.2f} - {df['area_km2'].max():.2f} km²")
    
    return df


def example_2_service_overlap():
    """Analyze overlapping service areas."""
    print("\n🔄 Example 2: Service Area Overlap")
    print("-" * 40)
    
    # Two nearby facilities
    facilities = [
        ("Hospital A", (35.7796, -78.6382)),
        ("Hospital B", (35.7915, -78.6569))
    ]
    
    print("Analyzing service area overlap between facilities:")
    
    isochrones = []
    for name, coords in facilities:
        # Create isochrone
        iso = create_isochrone(
            location=coords,
            travel_time=10,
            travel_mode="drive"
        )
        isochrones.append((name, iso))
        print(f"   ✅ Created isochrone for {name}")
    
    # In a real application, you would calculate geometric intersection
    # For this tutorial, we'll estimate based on distance
    dist_km = ((facilities[0][1][0] - facilities[1][1][0])**2 + 
               (facilities[0][1][1] - facilities[1][1][1])**2)**0.5 * 111  # rough km conversion
    
    if dist_km < 5:
        overlap = "High overlap (facilities very close)"
    elif dist_km < 10:
        overlap = "Moderate overlap"
    else:
        overlap = "Low overlap"
    
    print(f"\n📍 Distance between facilities: {dist_km:.2f} km")
    print(f"🔄 Service area overlap: {overlap}")
    
    # Get population in each area
    for name, iso in isochrones:
        demographics = get_census_data_for_polygon(
            polygon=iso,
            variables=["B01003_001E"],
            year=2022
        )
        
        if demographics is not None and not demographics.empty:
            pop = demographics['B01003_001E'].sum()
            print(f"   {name} serves: {pop:,} people")
    
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
        ("Candidate C", (35.8000, -78.9000))
    ]
    
    print("Analyzing coverage gaps:")
    
    # Calculate current coverage
    print("\n1. Current facilities:")
    current_coverage = 0
    for name, coords in existing:
        iso_dict = create_isochrone(
            location=coords,
            travel_time=15,
            travel_mode="drive",
            return_type="dict"
        )
        area = iso_dict['properties']['area_sq_km']
        current_coverage += area
        print(f"   {name}: {area:.2f} km²")
    
    print(f"   Total current: {current_coverage:.2f} km²")
    
    # Test each candidate location
    print("\n2. Testing candidate locations:")
    best_candidate = None
    best_improvement = 0
    
    for name, coords in candidates:
        # Create isochrone for candidate
        iso_dict = create_isochrone(
            location=coords,
            travel_time=15,
            travel_mode="drive",
            return_type="dict"
        )
        area = iso_dict['properties']['area_sq_km']
        
        # Estimate improvement (simplified - assumes no overlap)
        improvement = area * 0.6  # Assume 40% overlap with existing
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
        "University": (35.9132, -79.0558),
        "Airport": (35.8801, -78.7880),
        "Tech Park": (35.7358, -78.8286)
    }
    
    travel_time = 20
    print(f"Creating {travel_time}-minute accessibility matrix:\n")
    
    # Create matrix
    matrix = {}
    for from_name, from_coords in locations.items():
        iso_dict = create_isochrone(
            location=from_coords,
            travel_time=travel_time,
            travel_mode="drive",
            return_type="dict"
        )
        
        area = iso_dict['properties']['area_sq_km']
        matrix[from_name] = area
    
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


def example_5_time_distance_analysis():
    """Analyze how coverage changes with travel time."""
    print("\n⏱️ Example 5: Time-Distance Analysis")
    print("-" * 40)
    
    location = "NC State Capitol, Raleigh, NC"
    times = [5, 10, 15, 20, 25, 30]
    
    print(f"Analyzing coverage growth from {location}:\n")
    
    results = []
    for time in times:
        # Create isochrone
        iso_dict = create_isochrone(
            location=location,
            travel_time=time,
            travel_mode="drive",
            return_type="dict"
        )
        
        area = iso_dict['properties']['area_sq_km']
        
        # Get population if Census API available
        iso_gdf = create_isochrone(
            location=location,
            travel_time=time,
            travel_mode="drive"
        )
        
        demographics = get_census_data_for_polygon(
            polygon=iso_gdf,
            variables=["B01003_001E"],
            year=2022
        )
        
        pop = demographics['B01003_001E'].sum() if demographics is not None and not demographics.empty else 0
        
        results.append({
            'time': time,
            'area': area,
            'population': pop
        })
        
        print(f"   {time:2d} min → {area:7.2f} km² → {pop:8,} people")
    
    # Calculate growth rates
    print("\n📈 Growth Analysis:")
    for i in range(1, len(results)):
        prev = results[i-1]
        curr = results[i]
        
        area_growth = ((curr['area'] - prev['area']) / prev['area']) * 100 if prev['area'] > 0 else 0
        pop_growth = ((curr['population'] - prev['population']) / prev['population']) * 100 if prev['population'] > 0 else 0
        
        print(f"   {prev['time']} → {curr['time']} min:")
        print(f"      Area: +{area_growth:.1f}%")
        if pop_growth > 0:
            print(f"      Population: +{pop_growth:.1f}%")
    
    # Find diminishing returns point
    if len(results) > 2:
        growth_rates = []
        for i in range(1, len(results)):
            if results[i-1]['area'] > 0:
                rate = (results[i]['area'] - results[i-1]['area']) / results[i-1]['area']
                growth_rates.append(rate)
        
        # Find where growth rate drops below 20%
        for i, rate in enumerate(growth_rates):
            if rate < 0.2:
                print(f"\n💡 Diminishing returns after {results[i]['time']} minutes")
                break
    
    return pd.DataFrame(results)


def main():
    """Run all examples."""
    print("=" * 50)
    print("🚀 SIMPLE TUTORIAL: ADVANCED MULTI-LOCATION")
    print("=" * 50)
    print("\nAdvanced spatial analysis techniques")
    print("Complex analyses with simple functions!")
    
    # Check for Census API key
    if not os.getenv('CENSUS_API_KEY'):
        print("\n⚠️ Note: Census API key not set")
        print("Population data will be unavailable")
    
    try:
        # Run examples
        example_1_batch_processing()
        example_2_service_overlap()
        example_3_gap_analysis()
        example_4_accessibility_matrix()
        example_5_time_distance_analysis()
        
        print("\n" + "=" * 50)
        print("✨ Tutorial completed!")
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
        print("2. Verify geocoding service availability")
        print("3. Set Census API key for population data")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())