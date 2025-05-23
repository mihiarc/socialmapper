#!/usr/bin/env python3
"""
Basic test script for the new census module.

This script tests core functionality to ensure the module works correctly.
Run this after installation to verify everything is working.
"""

import sys
import tempfile
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon

# Add parent directory to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_database_initialization():
    """Test that the database initializes correctly."""
    print("Testing database initialization...")
    
    try:
        from socialmapper.census_new import get_census_database
        
        # Use a temporary database for testing
        import tempfile
        import os
        
        # Create a proper temporary file
        fd, tmp_path = tempfile.mkstemp(suffix='.duckdb')
        os.close(fd)  # Close the file descriptor
        os.unlink(tmp_path)  # Remove the empty file so DuckDB can create it
        
        try:
            db = get_census_database(tmp_path)
            
            # Test that tables exist
            tables = ['geographic_units', 'census_data', 'metadata']
            for table in tables:
                result = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                assert result is not None, f"Table {table} not accessible"
            
            db.close()
        finally:
            # Clean up
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
            
        print("✓ Database initialization successful")
        return True
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


def test_block_groups_api():
    """Test the block groups API with a small state."""
    print("Testing block groups API...")
    
    try:
        from socialmapper.census_new import get_census_block_groups
        
        # Test with Delaware (small state, FIPS code '10')
        # This will fetch from the API if not cached
        gdf = get_census_block_groups(['10'], force_refresh=False)
        
        # Basic validation
        assert isinstance(gdf, gpd.GeoDataFrame), "Result should be a GeoDataFrame"
        assert not gdf.empty, "Should have some block groups"
        assert 'GEOID' in gdf.columns, "Should have GEOID column"
        assert 'geometry' in gdf.columns, "Should have geometry column"
        
        # Check GEOID format (should be 12 characters for block groups)
        sample_geoid = gdf.iloc[0]['GEOID']
        assert len(sample_geoid) == 12, f"GEOID should be 12 characters, got {len(sample_geoid)}"
        assert sample_geoid.startswith('10'), "Delaware GEOIDs should start with '10'"
        
        print(f"✓ Block groups API successful - retrieved {len(gdf)} block groups for Delaware")
        return True
        
    except Exception as e:
        print(f"✗ Block groups API failed: {e}")
        return False


def test_spatial_queries():
    """Test spatial query functionality."""
    print("Testing spatial queries...")
    
    try:
        from socialmapper.census_new import get_census_database
        
        # Create a test polygon (small area in Delaware)
        test_polygon = Polygon([
            (-75.6, 39.7),  # Southwest corner
            (-75.5, 39.7),  # Southeast corner  
            (-75.5, 39.8),  # Northeast corner
            (-75.6, 39.8),  # Northwest corner
            (-75.6, 39.7)   # Close the polygon
        ])
        
        # Create a test GeoDataFrame
        test_gdf = gpd.GeoDataFrame([{'id': 1}], geometry=[test_polygon], crs='EPSG:4326')
        
        # Get database and test spatial intersection
        db = get_census_database()
        
        # First ensure we have some block groups (use Delaware)
        from socialmapper.census_new import get_census_block_groups
        get_census_block_groups(['10'])  # This will cache Delaware block groups
        
        # Test spatial intersection
        result_gdf = db.find_intersecting_block_groups(test_gdf, selection_mode='intersect')
        
        # Validation
        assert isinstance(result_gdf, gpd.GeoDataFrame), "Result should be a GeoDataFrame"
        # Note: result might be empty if the test polygon doesn't intersect any block groups
        
        print(f"✓ Spatial queries successful - found {len(result_gdf)} intersecting block groups")
        return True
        
    except Exception as e:
        print(f"✗ Spatial queries failed: {e}")
        return False


def test_census_data_api():
    """Test census data retrieval (if API key is available)."""
    print("Testing census data API...")
    
    try:
        from socialmapper.census_new import get_census_data_for_block_groups
        from socialmapper.util import get_census_api_key
        
        # Check if API key is available
        api_key = get_census_api_key()
        if not api_key:
            print("⚠ Skipping census data test - no API key available")
            return True
        
        # Get a small sample of block groups
        from socialmapper.census_new import get_census_block_groups
        block_groups = get_census_block_groups(['10'])  # Delaware
        
        # Take just the first few block groups for testing
        sample_bgs = block_groups.head(3)
        
        # Test census data retrieval
        census_gdf = get_census_data_for_block_groups(
            sample_bgs,
            variables=['total_population'],
            api_key=api_key
        )
        
        # Validation
        assert isinstance(census_gdf, gpd.GeoDataFrame), "Result should be a GeoDataFrame"
        assert not census_gdf.empty, "Should have census data"
        assert 'B01003_001E' in census_gdf.columns, "Should have population variable"
        
        print(f"✓ Census data API successful - retrieved data for {len(census_gdf)} block groups")
        return True
        
    except Exception as e:
        print(f"✗ Census data API failed: {e}")
        return False


def test_backward_compatibility():
    """Test that backward compatibility functions work."""
    print("Testing backward compatibility...")
    
    try:
        # Test the old API functions
        from socialmapper.census_new import isochrone_to_block_groups
        
        # Create a simple test isochrone (polygon in Delaware)
        test_polygon = Polygon([
            (-75.6, 39.7),
            (-75.5, 39.7),
            (-75.5, 39.8),
            (-75.6, 39.8),
            (-75.6, 39.7)
        ])
        
        isochrone_gdf = gpd.GeoDataFrame([{'id': 1}], geometry=[test_polygon], crs='EPSG:4326')
        
        # Test the backward compatibility function
        result = isochrone_to_block_groups(
            isochrone_gdf,
            state_fips=['10'],
            selection_mode='intersect'
        )
        
        assert isinstance(result, gpd.GeoDataFrame), "Result should be a GeoDataFrame"
        
        print(f"✓ Backward compatibility successful - found {len(result)} intersecting block groups")
        return True
        
    except Exception as e:
        print(f"✗ Backward compatibility failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("SocialMapper Census Module - Basic Tests")
    print("=" * 60)
    
    tests = [
        test_database_initialization,
        test_block_groups_api,
        test_spatial_queries,
        test_census_data_api,
        test_backward_compatibility
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
        print("🎉 All tests passed! The census module is working correctly.")
        return True
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)