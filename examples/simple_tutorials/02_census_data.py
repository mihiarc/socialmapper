#!/usr/bin/env python3
"""
Simple Tutorial 02: Direct Census Data Access

Learn how to work with census data using direct functions.
No complex abstractions - just simple, direct data access.

What you'll learn:
- Getting census data for isochrones
- Using different census variables
- Geocoding points to get location info
- Working with demographic data
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    get_census_data_for_isochrone,
    get_demographics_for_isochrone,
    geocode_point,
    normalize_variables
)
from socialmapper.api import create_isochrone


def example_1_basic_census():
    """Get census data for an isochrone area."""
    print("\n📊 Example 1: Basic Census Data")
    print("-" * 40)
    
    # First, create an isochrone
    print("Creating isochrone for downtown Raleigh...")
    isochrone = create_isochrone(
        location=(35.7796, -78.6382),  # Raleigh, NC
        travel_time=10,
        travel_mode="drive"
    )
    
    # Get census data for this area
    print("Fetching census data...")
    census_data = get_census_data_for_isochrone(
        isochrone=isochrone,
        variables=["B01003_001E"],  # Total population
        year=2022
    )
    
    if census_data is not None and not census_data.empty:
        print(f"✅ Retrieved census data")
        print(f"   Block groups found: {len(census_data)}")
        print(f"   Total population: {census_data['B01003_001E'].sum():,}")
        print(f"   Average per block group: {census_data['B01003_001E'].mean():.0f}")
    else:
        print("⚠️ No census data retrieved (API key may be needed)")
    
    return census_data


def example_2_demographics():
    """Get comprehensive demographic data."""
    print("\n👥 Example 2: Demographic Analysis")
    print("-" * 40)
    
    # Create isochrone for a specific area
    print("Creating isochrone for analysis...")
    isochrone = create_isochrone(
        location="Chapel Hill, NC",
        travel_time=15,
        travel_mode="drive"
    )
    
    # Get standard demographic variables
    print("Fetching demographic data...")
    demographics = get_demographics_for_isochrone(
        isochrone=isochrone,
        year=2022
    )
    
    if demographics is not None and not demographics.empty:
        print(f"✅ Retrieved demographic data")
        print(f"   Data points: {len(demographics)}")
        
        # Show some key demographics if available
        if 'B01003_001E' in demographics.columns:
            print(f"   Population range: {demographics['B01003_001E'].min():.0f} - {demographics['B01003_001E'].max():.0f}")
        if 'B19013_001E' in demographics.columns:
            median_income = demographics['B19013_001E'].median()
            if median_income > 0:
                print(f"   Median income: ${median_income:,.0f}")
    else:
        print("⚠️ No demographic data retrieved")
    
    return demographics


def example_3_geocoding():
    """Use geocoding to get location information."""
    print("\n📍 Example 3: Reverse Geocoding")
    print("-" * 40)
    
    # Geocode a point to get its location info
    lat, lon = 40.7128, -74.0060  # NYC coordinates
    
    print(f"Geocoding point: ({lat}, {lon})")
    location_info = geocode_point(lat, lon)
    
    if location_info:
        print(f"✅ Location identified:")
        for key, value in location_info.items():
            if value:
                print(f"   {key}: {value}")
    else:
        print("⚠️ Could not geocode location")
    
    return location_info


def example_4_variable_normalization():
    """Normalize census variable names."""
    print("\n🔧 Example 4: Variable Normalization")
    print("-" * 40)
    
    # Different ways people might specify variables
    user_variables = [
        "total_population",
        "median_income",
        "B01003_001E",  # Already normalized
        "median_household_income",
        "population"
    ]
    
    print("Normalizing variable names:")
    normalized = normalize_variables(user_variables)
    
    for original, normal in zip(user_variables, normalized):
        if original != normal:
            print(f"   '{original}' → '{normal}'")
        else:
            print(f"   '{original}' (already normalized)")
    
    return normalized


def example_5_custom_variables():
    """Work with specific census variables."""
    print("\n📈 Example 5: Custom Census Variables")
    print("-" * 40)
    
    # Create a small isochrone for testing
    print("Creating test isochrone...")
    isochrone = create_isochrone(
        location=(35.9132, -79.0558),  # UNC Chapel Hill
        travel_time=5,
        travel_mode="walk"
    )
    
    # Specific variables of interest
    variables = [
        "B01003_001E",  # Total population
        "B25001_001E",  # Total housing units
        "B08301_001E",  # Total commuters
        "B15003_022E",  # Bachelor's degree holders
    ]
    
    print("Fetching custom variables...")
    census_data = get_census_data_for_isochrone(
        isochrone=isochrone,
        variables=variables,
        year=2022
    )
    
    if census_data is not None and not census_data.empty:
        print(f"✅ Retrieved {len(variables)} variables")
        print(f"   Block groups: {len(census_data)}")
        
        # Show totals for each variable
        for var in variables:
            if var in census_data.columns:
                total = census_data[var].sum()
                print(f"   {var}: {total:,.0f}")
    else:
        print("⚠️ No data retrieved (check Census API key)")
    
    return census_data


def main():
    """Run all examples."""
    print("=" * 50)
    print("📊 SIMPLE TUTORIAL: CENSUS DATA ACCESS")
    print("=" * 50)
    print("\nDirect access to census and demographic data")
    print("Simple functions, no complex abstractions!")
    
    # Check for Census API key
    if not os.getenv('CENSUS_API_KEY'):
        print("\n⚠️ WARNING: No Census API key found!")
        print("Set CENSUS_API_KEY environment variable for full functionality")
        print("Get a free key at: https://api.census.gov/data/key_signup.html")
    
    try:
        # Run examples
        example_1_basic_census()
        example_2_demographics()
        example_3_geocoding()
        example_4_variable_normalization()
        example_5_custom_variables()
        
        print("\n" + "=" * 50)
        print("✨ Tutorial completed!")
        print("\nKey takeaways:")
        print("1. Direct functions for census data access")
        print("2. Works with any isochrone or geographic area")
        print("3. Support for standard and custom variables")
        print("4. Built-in geocoding capabilities")
        print("5. Simple, direct, no abstractions!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Set CENSUS_API_KEY environment variable")
        print("2. Check internet connection")
        print("3. Verify census data availability for the area")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())