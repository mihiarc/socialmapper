#!/usr/bin/env python3
"""Test script to verify the 5-function API architecture."""

import sys
import traceback
from typing import Any, Dict, List

def test_api_imports():
    """Test that all 5 API functions can be imported."""
    print("Testing API imports...")
    try:
        from socialmapper import (
            create_isochrone,
            get_poi,
            get_census_blocks,
            get_census_data,
            create_map
        )
        print("✓ All 5 functions imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_function_signatures():
    """Test that function signatures match documentation."""
    print("\nTesting function signatures...")
    from socialmapper import (
        create_isochrone,
        get_poi,
        get_census_blocks,
        get_census_data,
        create_map
    )
    import inspect

    expected_sigs = {
        "create_isochrone": ["location", "travel_time", "travel_mode"],
        "get_poi": ["location", "categories", "travel_time", "limit"],
        "get_census_blocks": ["polygon", "location", "radius_km"],
        "get_census_data": ["location", "variables", "year"],
        "create_map": ["data", "column", "title", "save_path"]
    }

    for func_name, expected_params in expected_sigs.items():
        func = locals()[func_name]
        sig = inspect.signature(func)
        actual_params = list(sig.parameters.keys())

        # Check if expected parameters exist
        missing_params = [p for p in expected_params if p not in actual_params]
        if missing_params:
            print(f"✗ {func_name}: Missing parameters {missing_params}")
        else:
            print(f"✓ {func_name}: Signature matches ({', '.join(actual_params)})")

def test_basic_functionality():
    """Test basic functionality without actual API calls."""
    print("\nTesting basic functionality (mock test)...")

    from socialmapper import create_isochrone

    # Test with invalid parameters to check validation
    try:
        # This should fail with validation error
        result = create_isochrone("", travel_time=0, travel_mode="invalid")
        print("✗ Validation not working - accepted invalid parameters")
    except (ValueError, TypeError) as e:
        print(f"✓ Input validation working: {type(e).__name__}")
    except Exception as e:
        print(f"? Unexpected error: {type(e).__name__}: {e}")

def test_api_consistency():
    """Test API consistency and patterns."""
    print("\nTesting API consistency...")

    from socialmapper import (
        create_isochrone,
        get_poi,
        get_census_blocks,
        get_census_data,
        create_map
    )
    import inspect

    issues = []

    # Check return type annotations
    for func_name, func in [
        ("create_isochrone", create_isochrone),
        ("get_poi", get_poi),
        ("get_census_blocks", get_census_blocks),
        ("get_census_data", get_census_data),
        ("create_map", create_map)
    ]:
        sig = inspect.signature(func)
        if sig.return_annotation == inspect.Signature.empty:
            issues.append(f"{func_name} lacks return type annotation")

        # Check docstring exists
        if not func.__doc__:
            issues.append(f"{func_name} lacks docstring")

    if issues:
        print(f"✗ Found {len(issues)} consistency issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ API is consistent")

def main():
    """Run all architecture tests."""
    print("=" * 60)
    print("SocialMapper API Architecture Test")
    print("=" * 60)

    tests = [
        test_api_imports,
        test_function_signatures,
        test_basic_functionality,
        test_api_consistency
    ]

    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            traceback.print_exc()
            results.append((test.__name__, False))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())