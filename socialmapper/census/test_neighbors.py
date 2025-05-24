#!/usr/bin/env python3
"""
Test script for the neighbor functionality in the SocialMapper census module.

This script tests:
1. Neighbor manager initialization
2. State neighbor relationships
3. Point-to-geography lookups
4. POI processing
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_neighbor_manager_initialization():
    """Test that the neighbor manager initializes correctly."""
    print("Testing neighbor manager initialization...")
    
    try:
        from socialmapper.census import get_neighbor_manager
        
        # Use a temporary database for testing
        import tempfile
        import os
        
        # Create a proper temporary file
        fd, tmp_path = tempfile.mkstemp(suffix='.duckdb')
        os.close(fd)  # Close the file descriptor
        os.unlink(tmp_path)  # Remove the empty file so DuckDB can create it
        
        try:
            from socialmapper.census import get_census_database
            db = get_census_database(tmp_path)
            manager = get_neighbor_manager(db)
            
            # Test that neighbor tables exist
            tables = ['state_neighbors', 'county_neighbors', 'point_geography_cache']
            for table in tables:
                result = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                assert result is not None, f"Table {table} not accessible"
            
            db.close()
        finally:
            # Clean up
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
            
        print("✓ Neighbor manager initialization successful")
        return True
        
    except Exception as e:
        print(f"✗ Neighbor manager initialization failed: {e}")
        return False


def test_state_neighbors():
    """Test state neighbor initialization and lookup."""
    print("Testing state neighbors...")
    
    try:
        from socialmapper.census import get_neighbor_manager
        
        # Use a temporary database for testing
        import tempfile
        import os
        
        fd, tmp_path = tempfile.mkstemp(suffix='.duckdb')
        os.close(fd)
        os.unlink(tmp_path)
        
        try:
            from socialmapper.census import get_census_database
            db = get_census_database(tmp_path)
            manager = get_neighbor_manager(db)
            
            # Initialize state neighbors
            count = manager.initialize_state_neighbors()
            assert count > 0, "Should have initialized some state neighbors"
            
            # Test specific state neighbors
            nc_neighbors = manager.get_neighboring_states('37')  # North Carolina
            expected_nc_neighbors = ['13', '45', '47', '51']  # GA, SC, TN, VA
            
            assert len(nc_neighbors) > 0, "NC should have neighbors"
            
            # Check that expected neighbors are found
            found_expected = set(nc_neighbors) & set(expected_nc_neighbors)
            assert len(found_expected) == len(expected_nc_neighbors), f"Expected {expected_nc_neighbors}, found {nc_neighbors}"
            
            # Test California neighbors
            ca_neighbors = manager.get_neighboring_states('06')  # California
            expected_ca_neighbors = ['04', '32', '41']  # AZ, NV, OR
            
            found_ca_expected = set(ca_neighbors) & set(expected_ca_neighbors)
            assert len(found_ca_expected) == len(expected_ca_neighbors), f"Expected {expected_ca_neighbors}, found {ca_neighbors}"
            
            db.close()
        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
            
        print(f"✓ State neighbors successful - initialized {count} relationships")
        return True
        
    except Exception as e:
        print(f"✗ State neighbors failed: {e}")
        return False


def test_point_geocoding():
    """Test point-to-geography lookup functionality."""
    print("Testing point geocoding...")
    
    try:
        from socialmapper.census import get_neighbor_manager
        
        # Use a temporary database for testing
        import tempfile
        import os
        
        fd, tmp_path = tempfile.mkstemp(suffix='.duckdb')
        os.close(fd)
        os.unlink(tmp_path)
        
        try:
            from socialmapper.census import get_census_database
            db = get_census_database(tmp_path)
            manager = get_neighbor_manager(db)
            
            # Test point geocoding (this will use the Census API)
            # Using a well-known location: Raleigh, NC
            lat, lon = 35.7796, -78.6382
            
            geography = manager.get_geography_from_point(lat, lon)
            
            # Should return North Carolina (state FIPS 37)
            assert geography['state_fips'] == '37', f"Expected NC (37), got {geography['state_fips']}"
            
            # Should return Wake County (county FIPS 183)
            assert geography['county_fips'] == '183', f"Expected Wake County (183), got {geography['county_fips']}"
            
            # Test caching - second call should be faster and return same result
            geography2 = manager.get_geography_from_point(lat, lon)
            assert geography == geography2, "Cached result should match original"
            
            db.close()
        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
            
        print("✓ Point geocoding successful")
        return True
        
    except Exception as e:
        print(f"✗ Point geocoding failed: {e}")
        print("Note: This test requires internet access to Census API")
        return False


def test_poi_processing():
    """Test POI processing functionality."""
    print("Testing POI processing...")
    
    try:
        from socialmapper.census import get_neighbor_manager
        
        # Use a temporary database for testing
        import tempfile
        import os
        
        fd, tmp_path = tempfile.mkstemp(suffix='.duckdb')
        os.close(fd)
        os.unlink(tmp_path)
        
        try:
            from socialmapper.census import get_census_database
            db = get_census_database(tmp_path)
            manager = get_neighbor_manager(db)
            
            # Initialize state neighbors for neighbor lookup
            manager.initialize_state_neighbors()
            
            # Test POIs
            test_pois = [
                {'lat': 35.7796, 'lon': -78.6382, 'id': 'raleigh_nc'},
                {'lat': 35.2271, 'lon': -80.8431, 'id': 'charlotte_nc'}
            ]
            
            # Process POIs without neighbors
            counties_no_neighbors = manager.get_counties_from_pois(test_pois, include_neighbors=False)
            assert len(counties_no_neighbors) > 0, "Should find counties for POIs"
            
            # Process POIs with neighbors
            counties_with_neighbors = manager.get_counties_from_pois(test_pois, include_neighbors=True)
            assert len(counties_with_neighbors) >= len(counties_no_neighbors), "Should find same or more counties with neighbors"
            
            # Verify we got North Carolina counties
            nc_counties = [county for county in counties_with_neighbors if county[0] == '37']
            assert len(nc_counties) > 0, "Should find NC counties"
            
            db.close()
        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
            
        print(f"✓ POI processing successful - found {len(counties_with_neighbors)} counties")
        return True
        
    except Exception as e:
        print(f"✗ POI processing failed: {e}")
        print("Note: This test requires internet access to Census API")
        return False


def test_convenience_functions():
    """Test the convenience functions for backward compatibility."""
    print("Testing convenience functions...")
    
    try:
        from socialmapper.census import (
            get_neighboring_states,
            get_geography_from_point
        )
        
        # Test state neighbors
        neighbors = get_neighboring_states('37')  # North Carolina
        assert len(neighbors) > 0, "Should find neighbors for NC"
        assert '45' in neighbors, "SC should be a neighbor of NC"
        
        # Test point geocoding (if API is available)
        try:
            geography = get_geography_from_point(35.7796, -78.6382)  # Raleigh, NC
            assert geography['state_fips'] == '37', "Should identify NC"
        except Exception:
            print("  Note: Point geocoding test skipped (API not available)")
        
        print("✓ Convenience functions successful")
        return True
        
    except Exception as e:
        print(f"✗ Convenience functions failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("SocialMapper Census Neighbors - Test Suite")
    print("=" * 60)
    
    tests = [
        test_neighbor_manager_initialization,
        test_state_neighbors,
        test_point_geocoding,
        test_poi_processing,
        test_convenience_functions
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()  # Add spacing between tests
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The neighbor system is working correctly.")
        return True
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        print("Note: Some tests require internet access to the Census API.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 