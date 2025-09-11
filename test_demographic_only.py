#!/usr/bin/env python3
"""Test demographic-only analysis without POI discovery."""

from socialmapper import SocialMapper

def test_demographic_only():
    """Test that analyze_location works without POI types."""
    mapper = SocialMapper()
    
    # Test 1: poi_types=None (default)
    print("Test 1: POI types = None")
    result = mapper.analyze_location(
        location="Chapel Hill, NC",
        travel_time=15,
        travel_mode="drive",
        census_variables=["total_population", "median_household_income"],
        create_maps=False
    )
    print(f"  POI count: {result.poi_count}")
    print(f"  Census units: {result.census_units_analyzed}")
    print(f"  Population: {result.demographics.get('total_population', 'N/A')}")
    
    # Test 2: poi_types=[] (explicit empty list)
    print("\nTest 2: POI types = []")
    result = mapper.analyze_location(
        location="Chapel Hill, NC",
        poi_types=[],  # Explicitly no POIs
        travel_time=15,
        travel_mode="drive",
        census_variables=["total_population", "median_age"],
        create_maps=False
    )
    print(f"  POI count: {result.poi_count}")
    print(f"  Census units: {result.census_units_analyzed}")
    print(f"  Population: {result.demographics.get('total_population', 'N/A')}")
    
    print("\n✅ Demographic-only analysis works!")

if __name__ == "__main__":
    test_demographic_only()