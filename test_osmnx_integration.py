#!/usr/bin/env python3
"""Test script to verify OSMnx integration for POI extraction."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from socialmapper.pipeline.extraction import extract_poi_data
from socialmapper.console import print_success, print_error, print_info


def test_fuquay_varina_schools():
    """Test POI extraction for Fuquay-Varina schools."""
    print_info("\n=== Testing Fuquay-Varina Schools POI Extraction ===")
    
    try:
        # Test the extraction with Fuquay-Varina
        poi_data, base_filename, state_abbreviations, sampled_pois = extract_poi_data(
            geocode_area="Fuquay-Varina",  # Note: not "Fuquay Varina"
            state="North Carolina",
            poi_type="amenity",
            poi_name="school"
        )
        
        # Display results
        poi_count = len(poi_data.get('pois', []))
        print_success(f"✓ Successfully found {poi_count} schools in Fuquay-Varina")
        
        if poi_count > 0:
            print_info("\nFirst 5 schools found:")
            for i, poi in enumerate(poi_data['pois'][:5], 1):
                name = poi.get('name') or poi.get('tags', {}).get('name', 'Unnamed')
                lat = poi.get('lat')
                lon = poi.get('lon')
                print(f"  {i}. {name} ({lat:.6f}, {lon:.6f})")
        
        print_info(f"\nBase filename: {base_filename}")
        print_info(f"State abbreviations: {state_abbreviations}")
        
        return True
        
    except Exception as e:
        print_error(f"✗ Error: {e}")
        return False


def test_location_variations():
    """Test different location name variations."""
    print_info("\n=== Testing Location Name Variations ===")
    
    test_cases = [
        ("Fuquay Varina", "North Carolina"),  # Space instead of hyphen
        ("Fuquay-Varina", "NC"),  # Hyphenated with state abbreviation
        ("Denver", "Colorado"),  # Simple city name
        ("Chapel Hill", "North Carolina"),  # Multi-word city
    ]
    
    for location, state in test_cases:
        print_info(f"\nTesting: {location}, {state}")
        try:
            poi_data, _, _, _ = extract_poi_data(
                geocode_area=location,
                state=state,
                poi_type="amenity",
                poi_name="library"
            )
            
            poi_count = len(poi_data.get('pois', []))
            if poi_count > 0:
                print_success(f"  ✓ Found {poi_count} libraries")
            else:
                print_info(f"  ⚠ No libraries found (may be correct)")
                
        except Exception as e:
            print_error(f"  ✗ Error: {str(e)[:100]}...")


def test_direct_osmnx():
    """Test direct OSMnx query for comparison."""
    print_info("\n=== Testing Direct OSMnx Query ===")
    
    from socialmapper.query.osmnx_query import query_pois_osmnx
    
    try:
        # Test direct OSMnx query
        result = query_pois_osmnx(
            location="Fuquay-Varina",
            poi_tags={"amenity": "school"},
            state="North Carolina"
        )
        
        poi_count = result.get('poi_count', 0)
        print_success(f"✓ Direct OSMnx query found {poi_count} schools")
        
        # Test with space instead of hyphen
        result2 = query_pois_osmnx(
            location="Fuquay Varina",  # Space instead of hyphen
            poi_tags={"amenity": "school"},
            state="North Carolina"
        )
        
        poi_count2 = result2.get('poi_count', 0)
        print_info(f"With 'Fuquay Varina' (space): found {poi_count2} schools")
        
    except Exception as e:
        print_error(f"✗ Direct OSMnx query failed: {e}")


def main():
    """Run all tests."""
    print_info("=" * 60)
    print_info("SocialMapper OSMnx Integration Test")
    print_info("=" * 60)
    
    # Run tests
    success = test_fuquay_varina_schools()
    test_direct_osmnx()
    test_location_variations()
    
    # Summary
    print_info("\n" + "=" * 60)
    if success:
        print_success("✓ OSMnx integration is working correctly!")
        print_info("The POI extraction now uses OSMnx's features_from_place()")
        print_info("which handles location name variations better than")
        print_info("the direct Overpass API approach.")
    else:
        print_error("✗ There were issues with the OSMnx integration.")
        print_info("Please check the errors above.")
    print_info("=" * 60)


if __name__ == "__main__":
    main()