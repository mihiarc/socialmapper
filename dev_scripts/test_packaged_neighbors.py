#!/usr/bin/env python3
"""
Test script to verify that the packaged neighbor database works correctly.

This simulates what an end user would experience when using the SocialMapper package.
"""

def test_packaged_neighbors():
    """Test that the packaged neighbor database works correctly."""
    print("🧪 Testing Packaged Neighbor Database")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from socialmapper.census import (
            get_neighbor_manager,
            get_neighboring_states,
            get_neighboring_counties,
            get_geography_from_point
        )
        print("✅ Imports successful")
        
        # Test neighbor manager initialization
        print("\n🔧 Testing neighbor manager initialization...")
        manager = get_neighbor_manager()
        print(f"✅ Database path: {manager.db.db_path}")
        
        # Test database statistics
        print("\n📊 Testing database statistics...")
        stats = manager.get_neighbor_statistics()
        print(f"  State relationships: {stats['state_relationships']:,}")
        print(f"  County relationships: {stats['county_relationships']:,}")
        print(f"  Cross-state relationships: {stats['cross_state_county_relationships']:,}")
        print(f"  States with data: {stats['states_with_county_data']}")
        
        # Verify completeness
        assert stats['state_relationships'] >= 200, "Missing state relationships"
        assert stats['county_relationships'] >= 15000, "Missing county relationships"
        assert stats['states_with_county_data'] >= 50, "Missing state data"
        print("✅ Database appears complete")
        
        # Test state neighbor lookups
        print("\n🏛️  Testing state neighbor lookups...")
        
        # Test North Carolina
        nc_neighbors = get_neighboring_states('37')
        print(f"  NC neighbors: {nc_neighbors}")
        assert '13' in nc_neighbors, "Georgia should be NC neighbor"
        assert '45' in nc_neighbors, "South Carolina should be NC neighbor"
        
        # Test California
        ca_neighbors = get_neighboring_states('06')
        print(f"  CA neighbors: {ca_neighbors}")
        assert '04' in ca_neighbors, "Arizona should be CA neighbor"
        assert '32' in ca_neighbors, "Nevada should be CA neighbor"
        
        print("✅ State neighbor lookups working")
        
        # Test county neighbor lookups
        print("\n🏘️  Testing county neighbor lookups...")
        
        # Test Wake County, NC
        wake_neighbors = get_neighboring_counties('37', '183')
        print(f"  Wake County neighbors: {len(wake_neighbors)} counties")
        assert len(wake_neighbors) > 0, "Wake County should have neighbors"
        
        # Test Los Angeles County, CA
        la_neighbors = get_neighboring_counties('06', '037')
        print(f"  LA County neighbors: {len(la_neighbors)} counties")
        assert len(la_neighbors) > 0, "LA County should have neighbors"
        
        print("✅ County neighbor lookups working")
        
        # Test point geocoding (if available)
        print("\n📍 Testing point geocoding...")
        try:
            # Test Raleigh, NC
            raleigh_geo = get_geography_from_point(35.7796, -78.6382)
            print(f"  Raleigh geography: {raleigh_geo}")
            
            if raleigh_geo['state_fips']:
                assert raleigh_geo['state_fips'] == '37', "Raleigh should be in NC"
                print("✅ Point geocoding working")
            else:
                print("⚠️  Point geocoding returned no results (may need API key)")
                
        except Exception as e:
            print(f"⚠️  Point geocoding failed: {e} (may need API key)")
        
        print("\n🎉 All tests passed!")
        print("✅ Packaged neighbor database is working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_shapefile_dependency():
    """Test that the package doesn't require local shapefiles."""
    print("\n🚫 Testing that no local shapefiles are required...")
    
    try:
        from socialmapper.census import get_neighbor_manager
        
        # This should work without any local shapefiles
        manager = get_neighbor_manager()
        stats = manager.get_neighbor_statistics()
        
        # Should have pre-computed data
        assert stats['county_relationships'] > 0, "Should have pre-computed county data"
        
        print("✅ No local shapefiles required")
        return True
        
    except FileNotFoundError as e:
        if "shapefile" in str(e).lower():
            print(f"❌ Package still requires local shapefiles: {e}")
            return False
        else:
            raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 SocialMapper Packaged Neighbor Database Test")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_packaged_neighbors()
    test2_passed = test_no_shapefile_dependency()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The packaged neighbor database is ready for distribution")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please check the issues above before distributing") 