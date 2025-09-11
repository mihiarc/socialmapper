#!/usr/bin/env python3
"""Demo of the simplified census API for SocialMapper.

This demo shows how easy it is to get census data for geographic areas
using the new, simplified API - no builders, no complex systems, just
simple functions that do what you need.
"""

import geopandas as gpd
from shapely.geometry import Point, Polygon
from socialmapper import (
    CensusClient,
    get_census_data,
    get_census_data_for_isochrone,
    get_demographics_for_isochrone,
    normalize_variables,
    geocode_point
)


def demo_basic_usage():
    """Demo 1: Basic census data fetching."""
    print("=" * 60)
    print("DEMO 1: Basic Census Data Fetching")
    print("=" * 60)
    
    print("\n📍 Getting census data for a specific location...")
    
    # Simple: Just pass a lat/lon point
    raleigh_downtown = (35.7796, -78.6382)
    
    census_data = get_census_data(
        location=raleigh_downtown,
        variables=['total_population', 'median_household_income', 'median_age']
    )
    
    if not census_data.empty:
        print(f"✅ Retrieved census data for block group at {raleigh_downtown}")
        print(f"   Columns: {list(census_data.columns)}")
        if 'B01003_001E' in census_data.columns:
            pop = census_data['B01003_001E'].iloc[0]
            print(f"   Population: {pop:,}")
    else:
        print("⚠️  No data retrieved (may need API key)")
    
    print("\n" + "-" * 40)


def demo_isochrone_analysis():
    """Demo 2: Get census data for an isochrone area."""
    print("\n" + "=" * 60)
    print("DEMO 2: Census Data for Isochrone Areas")
    print("=" * 60)
    
    print("\n🗺️  Creating a sample isochrone (15-min drive from downtown)...")
    
    # Create a simple polygon representing a 15-minute drive area
    # In reality, this would come from your isochrone generation
    downtown_coords = [
        (-78.65, 35.79),
        (-78.62, 35.79),
        (-78.61, 35.77),
        (-78.62, 35.75),
        (-78.65, 35.75),
        (-78.66, 35.77),
        (-78.65, 35.79)
    ]
    
    isochrone = gpd.GeoDataFrame(
        [{'travel_time': 15, 'mode': 'drive'}],
        geometry=[Polygon(downtown_coords)],
        crs='EPSG:4326'
    )
    
    print("📊 Fetching census data for all block groups in the isochrone...")
    
    # THE KEY FUNCTION - Simple and direct!
    census_data = get_census_data_for_isochrone(
        isochrone=isochrone,
        variables=['total_population', 'median_household_income', 'poverty_population']
    )
    
    if not census_data.empty:
        print(f"✅ Found {len(census_data)} block groups in the isochrone area")
        
        # Calculate some statistics
        if 'B01003_001E' in census_data.columns:
            total_pop = census_data['B01003_001E'].sum()
            print(f"   Total population in area: {total_pop:,}")
        
        if 'B19013_001E' in census_data.columns:
            median_income = census_data['B19013_001E'].median()
            print(f"   Median household income: ${median_income:,.0f}")
    else:
        print("⚠️  No block groups found (may need to adjust area or check API)")
    
    print("\n" + "-" * 40)


def demo_quick_demographics():
    """Demo 3: Quick demographic summary for an area."""
    print("\n" + "=" * 60)
    print("DEMO 3: Quick Demographic Summary")
    print("=" * 60)
    
    print("\n🎯 Getting a quick demographic summary...")
    
    # Create a sample area (e.g., from POI analysis)
    study_area = gpd.GeoDataFrame(
        geometry=[Polygon([
            (-78.64, 35.78),
            (-78.63, 35.78),
            (-78.63, 35.77),
            (-78.64, 35.77),
            (-78.64, 35.78)
        ])],
        crs='EPSG:4326'
    )
    
    # ONE FUNCTION for common demographics!
    demographics = get_demographics_for_isochrone(study_area)
    
    if demographics:
        print("✅ Demographic Summary:")
        for key, value in demographics.items():
            if isinstance(value, (int, float)):
                if 'income' in key or 'value' in key or 'rent' in key:
                    print(f"   {key}: ${value:,.0f}")
                elif 'age' in key:
                    print(f"   {key}: {value:.1f} years")
                else:
                    print(f"   {key}: {value:,.0f}")
            else:
                print(f"   {key}: {value}")
    else:
        print("⚠️  No demographics retrieved")
    
    print("\n" + "-" * 40)


def demo_flexible_interface():
    """Demo 4: Flexible interface for different input types."""
    print("\n" + "=" * 60)
    print("DEMO 4: Flexible Interface")
    print("=" * 60)
    
    print("\n🔧 The get_census_data() function accepts multiple input types:\n")
    
    # Example 1: Point coordinates
    print("1️⃣  Point coordinates:")
    print("   get_census_data((35.78, -78.64), ['total_population'])")
    
    # Example 2: List of GEOIDs
    print("\n2️⃣  List of block group GEOIDs:")
    print("   get_census_data(['370630541021', '370630541022'], variables)")
    
    # Example 3: GeoDataFrame (isochrone)
    print("\n3️⃣  GeoDataFrame with polygon:")
    print("   get_census_data(isochrone_gdf, variables)")
    
    # Example 4: State/County dict
    print("\n4️⃣  State and county FIPS:")
    print("   get_census_data({'state_fips': '37', 'county_fips': '183'}, variables)")
    
    print("\n✨ One function, multiple ways to use it!")
    
    print("\n" + "-" * 40)


def demo_direct_client():
    """Demo 5: Using the CensusClient directly."""
    print("\n" + "=" * 60)
    print("DEMO 5: Direct Census Client Usage")
    print("=" * 60)
    
    print("\n🔌 Sometimes you want direct control...")
    
    # Create a client (uses CENSUS_API_KEY env var by default)
    client = CensusClient()
    
    # Fetch specific data
    variables = ['B01003_001E', 'B19013_001E']  # Population, median income
    geoids = ['370630541021', '370630541022']  # Specific block groups
    
    print(f"📊 Fetching {variables} for {len(geoids)} block groups...")
    
    data = client.get_data(variables, geoids)
    
    if not data.empty:
        print(f"✅ Retrieved {len(data)} rows of data")
        print(f"   Columns: {list(data.columns)}")
    else:
        print("⚠️  No data retrieved")
    
    print("\n" + "-" * 40)


def demo_variable_normalization():
    """Demo 6: Human-readable variable names."""
    print("\n" + "=" * 60)
    print("DEMO 6: Human-Readable Variable Names")
    print("=" * 60)
    
    print("\n📝 Use friendly names instead of census codes:\n")
    
    friendly_names = [
        'total_population',
        'median_household_income',
        'median_age',
        'poverty_population',
        'households_no_vehicle',
        'median_home_value',
        'median_rent'
    ]
    
    print("Friendly Name → Census Code:")
    print("-" * 40)
    
    codes = normalize_variables(friendly_names)
    for name, code in zip(friendly_names, codes):
        print(f"  {name:<30} → {code}")
    
    print("\n✨ No need to memorize census codes!")
    
    print("\n" + "-" * 40)


def main():
    """Run all demos."""
    print("\n")
    print("🚀 " + "=" * 56 + " 🚀")
    print("   SOCIALMAPPER SIMPLIFIED CENSUS API DEMO")
    print("🚀 " + "=" * 56 + " 🚀")
    print("\nShowing how simple it is to get census data with the new API!")
    print("No builders, no complex systems, just functions that work.\n")
    
    # Run each demo
    demo_basic_usage()
    demo_isochrone_analysis()
    demo_quick_demographics()
    demo_flexible_interface()
    demo_direct_client()
    demo_variable_normalization()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 SUMMARY: The New Census API")
    print("=" * 60)
    print("""
Key Benefits:
✅ Simple, direct functions
✅ Works with isochrones out of the box
✅ Flexible input types
✅ Human-readable variable names
✅ No complex abstractions
✅ Same functionality, 80% less code

Main Functions:
• get_census_data() - Flexible data fetching
• get_census_data_for_isochrone() - Direct isochrone support
• get_demographics_for_isochrone() - Quick summaries
• CensusClient() - Direct API access when needed
• normalize_variables() - Human-readable names

Compare the old way:
    census_system = (CensusSystemBuilder()
        .with_api_key(key)
        .with_cache_strategy(CacheStrategy.FILE)
        .with_repository_type(RepositoryType.SQLITE)
        .build())
    data = census_system.get_census_data(variables, units)

With the new way:
    data = get_census_data_for_isochrone(isochrone, variables)

Simple. Direct. Pythonic. ✨
""")
    
    print("=" * 60)
    print("\n📚 For more info, check the documentation!")
    print("💡 Questions? File an issue on GitHub!\n")


if __name__ == "__main__":
    main()