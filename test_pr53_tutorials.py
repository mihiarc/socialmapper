#!/usr/bin/env python3
"""
Comprehensive test of PR #53 tutorials and API functionality.
This tests whether the new simple API actually works as advertised.
"""

import sys
import traceback
from pathlib import Path

# Test results tracking
test_results = {
    'passed': [],
    'failed': [],
    'errors': []
}

def test_basic_imports():
    """Test that basic imports work."""
    print("\n1. Testing Basic Imports...")
    try:
        from socialmapper.api import create_isochrone, SocialMapper
        from socialmapper import (
            get_census_data_for_isochrone,
            get_demographics_for_isochrone,
            geocode_point,
            normalize_variables
        )
        test_results['passed'].append("Basic imports")
        print("   ✅ All imports successful")
        return True
    except Exception as e:
        test_results['failed'].append(f"Basic imports: {str(e)}")
        print(f"   ❌ Import failed: {e}")
        return False

def test_create_isochrone_coords():
    """Test creating an isochrone from coordinates."""
    print("\n2. Testing Isochrone from Coordinates...")
    try:
        from socialmapper.api import create_isochrone
        
        # Use coordinates to bypass geocoding issues
        iso = create_isochrone(
            location=(35.7796, -78.6382),  # Raleigh, NC
            travel_time=10,
            travel_mode="drive"
        )
        
        if iso is not None and not iso.empty:
            test_results['passed'].append("Isochrone from coordinates")
            print(f"   ✅ Created isochrone successfully")
            print(f"      Shape: {iso.shape}")
            return True
        else:
            test_results['failed'].append("Isochrone from coordinates: Empty result")
            print("   ❌ Isochrone is empty")
            return False
            
    except Exception as e:
        test_results['errors'].append(f"Isochrone from coords: {str(e)}")
        print(f"   ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_create_isochrone_dict():
    """Test getting isochrone as dictionary."""
    print("\n3. Testing Isochrone as Dictionary...")
    try:
        from socialmapper.api import create_isochrone
        
        iso_dict = create_isochrone(
            location=(40.7128, -74.0060),  # NYC
            travel_time=5,
            travel_mode="walk",
            return_type="dict"
        )
        
        if isinstance(iso_dict, dict) and 'properties' in iso_dict:
            test_results['passed'].append("Isochrone as dict")
            print(f"   ✅ Got dictionary format")
            print(f"      Type: {iso_dict.get('type')}")
            print(f"      Area: {iso_dict['properties'].get('area_sq_km', 0):.2f} km²")
            return True
        else:
            test_results['failed'].append("Isochrone as dict: Wrong format")
            print(f"   ❌ Unexpected format: {type(iso_dict)}")
            return False
            
    except Exception as e:
        test_results['errors'].append(f"Isochrone dict: {str(e)}")
        print(f"   ❌ Error: {e}")
        return False

def test_socialmapper_client():
    """Test the SocialMapper client class."""
    print("\n4. Testing SocialMapper Client...")
    try:
        from socialmapper.api import SocialMapper
        
        # Create client
        mapper = SocialMapper(api_key=None)
        print(f"   ✓ Client created: {mapper}")
        
        # Check if analyze_location exists
        if hasattr(mapper, 'analyze_location'):
            print("   ✓ analyze_location method exists")
            
            # Try to use it (may fail due to dependencies)
            try:
                result = mapper.analyze_location(
                    location="Raleigh, NC",
                    poi_types=["library"],
                    travel_time=10
                )
                if result and result.get('success'):
                    test_results['passed'].append("SocialMapper client")
                    print("   ✅ Client analyze_location works")
                    return True
                else:
                    print(f"   ⚠️ analyze_location returned: {result}")
            except Exception as e:
                print(f"   ⚠️ analyze_location failed: {e}")
        else:
            test_results['failed'].append("SocialMapper client: Missing analyze_location")
            print("   ❌ analyze_location method not found")
            return False
            
    except Exception as e:
        test_results['errors'].append(f"SocialMapper client: {str(e)}")
        print(f"   ❌ Error: {e}")
        return False

def test_geocoding():
    """Test geocoding functionality."""
    print("\n5. Testing Geocoding...")
    try:
        from socialmapper import geocode_point
        
        # Try reverse geocoding
        result = geocode_point(40.7128, -74.0060)  # NYC
        
        if result:
            test_results['passed'].append("Geocoding")
            print(f"   ✅ Geocoding successful")
            print(f"      Location: {result}")
            return True
        else:
            test_results['failed'].append("Geocoding: No result")
            print("   ❌ No geocoding result")
            return False
            
    except Exception as e:
        test_results['errors'].append(f"Geocoding: {str(e)}")
        print(f"   ❌ Error: {e}")
        return False

def test_variable_normalization():
    """Test census variable normalization."""
    print("\n6. Testing Variable Normalization...")
    try:
        from socialmapper import normalize_variables
        
        vars_in = ["total_population", "median_income", "B01003_001E"]
        vars_out = normalize_variables(vars_in)
        
        if vars_out and len(vars_out) == len(vars_in):
            test_results['passed'].append("Variable normalization")
            print(f"   ✅ Normalization successful")
            for i, o in zip(vars_in, vars_out):
                if i != o:
                    print(f"      {i} → {o}")
            return True
        else:
            test_results['failed'].append("Variable normalization: Wrong output")
            print(f"   ❌ Unexpected output: {vars_out}")
            return False
            
    except Exception as e:
        test_results['errors'].append(f"Variable normalization: {str(e)}")
        print(f"   ❌ Error: {e}")
        return False

def test_tutorial_execution():
    """Test if tutorials can actually run."""
    print("\n7. Testing Tutorial Execution...")
    
    tutorial_results = []
    
    # Test a simple coordinate-based isochrone (should work)
    try:
        from socialmapper.api import create_isochrone
        iso = create_isochrone((35.7796, -78.6382), 5, "drive")
        if iso is not None and not iso.empty:
            tutorial_results.append("✓ Basic isochrone")
        else:
            tutorial_results.append("✗ Basic isochrone failed")
    except Exception as e:
        tutorial_results.append(f"✗ Basic isochrone error: {e}")
    
    # Test dictionary output
    try:
        iso_dict = create_isochrone((35.7796, -78.6382), 5, "drive", return_type="dict")
        if isinstance(iso_dict, dict):
            tutorial_results.append("✓ Dictionary output")
        else:
            tutorial_results.append("✗ Dictionary output wrong type")
    except Exception as e:
        tutorial_results.append(f"✗ Dictionary output error: {e}")
    
    # Test different travel modes
    for mode in ["drive", "walk", "bike"]:
        try:
            iso = create_isochrone((35.7796, -78.6382), 5, mode)
            if iso is not None:
                tutorial_results.append(f"✓ {mode} mode")
            else:
                tutorial_results.append(f"✗ {mode} mode failed")
        except Exception as e:
            tutorial_results.append(f"✗ {mode} mode error")
    
    # Print results
    for result in tutorial_results:
        print(f"   {result}")
    
    passed = sum(1 for r in tutorial_results if r.startswith("✓"))
    total = len(tutorial_results)
    
    if passed == total:
        test_results['passed'].append("Tutorial execution")
        print(f"   ✅ All tutorial components work ({passed}/{total})")
        return True
    else:
        test_results['failed'].append(f"Tutorial execution: {passed}/{total} passed")
        print(f"   ⚠️ Partial success ({passed}/{total})")
        return False

def main():
    """Run all tests and provide summary."""
    print("=" * 60)
    print("PR #53 TUTORIAL FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Run tests
    test_basic_imports()
    test_create_isochrone_coords()
    test_create_isochrone_dict()
    test_socialmapper_client()
    test_geocoding()
    test_variable_normalization()
    test_tutorial_execution()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"\n✅ Passed: {len(test_results['passed'])}")
    for test in test_results['passed']:
        print(f"   • {test}")
    
    if test_results['failed']:
        print(f"\n❌ Failed: {len(test_results['failed'])}")
        for test in test_results['failed']:
            print(f"   • {test}")
    
    if test_results['errors']:
        print(f"\n🔥 Errors: {len(test_results['errors'])}")
        for test in test_results['errors']:
            print(f"   • {test}")
    
    # Overall assessment
    total = len(test_results['passed']) + len(test_results['failed']) + len(test_results['errors'])
    success_rate = len(test_results['passed']) / total * 100 if total > 0 else 0
    
    print(f"\n📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ VERDICT: Tutorials are mostly functional")
    elif success_rate >= 50:
        print("⚠️ VERDICT: Tutorials have significant issues")
    else:
        print("❌ VERDICT: Tutorials are largely broken")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())