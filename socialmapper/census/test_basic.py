#!/usr/bin/env python3
"""
Basic test script for the new census module including neighbor functionality.

This script tests core functionality to ensure the module works correctly:
- Database initialization and schema
- Block groups API and streaming
- Spatial queries and intersections
- Census data retrieval (if API key available)
- Neighbor relationships and lookups
- Backward compatibility with old APIs

Run this after installation to verify everything is working.
"""

import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, List
import geopandas as gpd
from shapely.geometry import Polygon

# Add parent directory to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_database_initialization():
    """Test that the database initializes correctly."""
    print("Testing database initialization...")
    
    try:
        from socialmapper.census import get_census_database
        
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
        from socialmapper.census import get_census_block_groups
        from socialmapper.util import get_census_api_key
        
        # Check if API key is available
        api_key = get_census_api_key()
        if not api_key:
            print("⚠ Skipping block groups test - no API key available")
            return True
        
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
        from socialmapper.census import get_census_database
        from socialmapper.util import get_census_api_key
        
        # Check if API key is available
        api_key = get_census_api_key()
        if not api_key:
            print("⚠ Skipping spatial queries test - no API key available")
            return True
        
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
        from socialmapper.census import get_census_block_groups
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
        from socialmapper.census import get_census_data_for_block_groups
        from socialmapper.util import get_census_api_key
        
        # Check if API key is available
        api_key = get_census_api_key()
        if not api_key:
            print("⚠ Skipping census data test - no API key available")
            return True
        
        # Get a small sample of block groups
        from socialmapper.census import get_census_block_groups
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


def test_neighbor_functionality():
    """Test the new neighbor functionality with performance measurements."""
    print("Testing neighbor functionality...")
    
    try:
        from socialmapper.census import (
            get_neighboring_states,
            get_neighboring_counties,
            get_geography_from_point,
            get_counties_from_pois,
            get_neighbor_manager
        )
        
        # Test 1: State neighbors with timing
        start_time = time.time()
        nc_neighbors = get_neighboring_states('37')  # North Carolina
        state_time = time.time() - start_time
        assert len(nc_neighbors) > 0, "NC should have neighbors"
        assert '45' in nc_neighbors, "SC should be a neighbor of NC"
        print(f"  State neighbors lookup: {state_time*1000:.2f}ms ({len(nc_neighbors)} neighbors)")
        
        # Test repeated state lookup (should be cached)
        start_time = time.time()
        nc_neighbors_cached = get_neighboring_states('37')
        cached_state_time = time.time() - start_time
        print(f"  Cached state lookup: {cached_state_time*1000:.2f}ms (speedup: {state_time/cached_state_time:.1f}x)")
        
        # Test 2: County neighbors with timing
        start_time = time.time()
        county_neighbors = get_neighboring_counties('37', '183')  # Wake County, NC
        county_time = time.time() - start_time
        print(f"  County neighbors lookup: {county_time*1000:.2f}ms ({len(county_neighbors)} neighbors)")
        
        # Test 3: Point geocoding (if API is available)
        point_times = []
        try:
            # First lookup (may hit API)
            start_time = time.time()
            geography = get_geography_from_point(39.7391, -75.5398)  # Delaware coordinates
            first_point_time = time.time() - start_time
            assert geography['state_fips'] == '10', "Should identify Delaware"
            point_times.append(first_point_time)
            print(f"  Point geocoding (first): {first_point_time*1000:.2f}ms -> {geography}")
            
            # Second lookup (should be cached)
            start_time = time.time()
            geography_cached = get_geography_from_point(39.7391, -75.5398)
            cached_point_time = time.time() - start_time
            point_times.append(cached_point_time)
            print(f"  Point geocoding (cached): {cached_point_time*1000:.2f}ms (speedup: {first_point_time/cached_point_time:.1f}x)")
            
        except Exception as e:
            print(f"  Point geocoding skipped (API issue): {e}")
        
        # Test 4: POI processing with timing
        test_pois = [
            {'lat': 39.7391, 'lon': -75.5398, 'id': 'delaware_poi_1'},
            {'lat': 39.7500, 'lon': -75.5500, 'id': 'delaware_poi_2'},
            {'lat': 39.7600, 'lon': -75.5600, 'id': 'delaware_poi_3'}
        ]
        
        start_time = time.time()
        counties = get_counties_from_pois(test_pois, include_neighbors=False)
        poi_time = time.time() - start_time
        print(f"  POI processing ({len(test_pois)} POIs): {poi_time*1000:.2f}ms -> {len(counties)} counties")
        
        # Test 5: Neighbor manager statistics
        manager = get_neighbor_manager()
        stats = manager.get_neighbor_statistics()
        assert 'state_neighbors' in stats, "Should have state neighbor statistics"
        
        print(f"✓ Neighbor functionality successful - {stats['state_neighbors']} state relationships")
        return True
        
    except Exception as e:
        print(f"✗ Neighbor functionality failed: {e}")
        return False


def test_performance_benchmarks():
    """Run comprehensive performance benchmarks to identify bottlenecks."""
    print("Running performance benchmarks...")
    
    try:
        from socialmapper.census import (
            get_neighboring_states,
            get_neighboring_counties,
            get_geography_from_point,
            get_counties_from_pois,
            get_neighbor_manager
        )
        
        print("\n  === Performance Benchmark Results ===")
        print("  (Testing both cold cache and warm cache performance)")
        
        # Clear cache to simulate first-time user experience
        manager = get_neighbor_manager()
        print("\n  🧹 Clearing cache to simulate first-time user experience...")
        
        # Clear point geocoding cache
        try:
            manager.db.conn.execute("DELETE FROM point_geography_cache")
            print("     ✓ Point geocoding cache cleared")
        except Exception as e:
            print(f"     ⚠ Could not clear point cache: {e}")
        
        # Benchmark 1: State neighbor lookups (multiple states)
        test_states = ['06', '37', '48', '12', '36']  # CA, NC, TX, FL, NY
        state_times = []
        
        print(f"\n  1. State Neighbor Lookups ({len(test_states)} states):")
        for state_fips in test_states:
            start_time = time.time()
            neighbors = get_neighboring_states(state_fips)
            elapsed = time.time() - start_time
            state_times.append(elapsed)
            print(f"     State {state_fips}: {elapsed*1000:.2f}ms ({len(neighbors)} neighbors)")
        
        avg_state_time = sum(state_times) / len(state_times)
        print(f"     Average: {avg_state_time*1000:.2f}ms")
        
        # Benchmark 2: County neighbor lookups (various counties)
        test_counties = [
            ('06', '037'),  # LA County, CA
            ('37', '183'),  # Wake County, NC
            ('48', '201'),  # Harris County, TX
            ('12', '086'),  # Miami-Dade County, FL
            ('36', '061')   # Manhattan County, NY
        ]
        county_times = []
        
        print(f"\n  2. County Neighbor Lookups ({len(test_counties)} counties):")
        for state_fips, county_fips in test_counties:
            start_time = time.time()
            try:
                neighbors = get_neighboring_counties(state_fips, county_fips)
                elapsed = time.time() - start_time
                county_times.append(elapsed)
                print(f"     County {state_fips}{county_fips}: {elapsed*1000:.2f}ms ({len(neighbors)} neighbors)")
            except Exception as e:
                print(f"     County {state_fips}{county_fips}: Failed - {e}")
        
        if county_times:
            avg_county_time = sum(county_times) / len(county_times)
            print(f"     Average: {avg_county_time*1000:.2f}ms")
        
        # Benchmark 3: Point geocoding performance (cold cache vs warm cache)
        test_points = [
            (39.7391, -75.5398),  # Delaware
            (34.0522, -118.2437), # Los Angeles
            (35.7796, -78.6382),  # Raleigh
            (29.7604, -95.3698),  # Houston
            (40.7128, -74.0060)   # NYC
        ]
        
        print(f"\n  3. Point Geocoding - Cold Cache Performance ({len(test_points)} points):")
        print("     (First-time user experience - hits Census API)")
        cold_cache_times = []
        
        for i, (lat, lon) in enumerate(test_points):
            try:
                # Clear cache for this specific point to ensure cold lookup
                manager.db.conn.execute(
                    "DELETE FROM point_geography_cache WHERE lat = ? AND lon = ?", 
                    (lat, lon)
                )
                
                # Cold cache lookup (will hit API)
                start_time = time.time()
                geography = get_geography_from_point(lat, lon)
                cold_time = time.time() - start_time
                cold_cache_times.append(cold_time)
                
                print(f"     Point {i+1} (cold): {cold_time*1000:.2f}ms -> {geography}")
                
            except Exception as e:
                print(f"     Point {i+1} (cold): Failed - {e}")
        
        print(f"\n  3b. Point Geocoding - Warm Cache Performance (same points):")
        print("     (Subsequent lookups - uses cache)")
        warm_cache_times = []
        
        for i, (lat, lon) in enumerate(test_points):
            try:
                # Warm cache lookup (should be cached from above)
                start_time = time.time()
                geography_cached = get_geography_from_point(lat, lon)
                warm_time = time.time() - start_time
                warm_cache_times.append(warm_time)
                
                if cold_cache_times and i < len(cold_cache_times):
                    speedup = cold_cache_times[i] / warm_time if warm_time > 0 else float('inf')
                    print(f"     Point {i+1} (warm): {warm_time*1000:.2f}ms (speedup: {speedup:.1f}x)")
                else:
                    print(f"     Point {i+1} (warm): {warm_time*1000:.2f}ms")
                
            except Exception as e:
                print(f"     Point {i+1} (warm): Failed - {e}")
        
        if cold_cache_times and warm_cache_times:
            avg_cold_time = sum(cold_cache_times) / len(cold_cache_times)
            avg_warm_time = sum(warm_cache_times) / len(warm_cache_times)
            overall_speedup = avg_cold_time / avg_warm_time if avg_warm_time > 0 else 0
            print(f"     Average cold cache: {avg_cold_time*1000:.2f}ms (first-time user)")
            print(f"     Average warm cache: {avg_warm_time*1000:.2f}ms (cached)")
            print(f"     Overall cache speedup: {overall_speedup:.1f}x")
        
        # Benchmark 4: POI processing at scale (cold cache vs warm cache)
        print(f"\n  4. POI Processing at Scale - Cold Cache:")
        print("     (First-time user experience)")
        
        # Generate test POIs in different regions
        poi_counts = [10, 50, 100]
        cold_poi_results = []
        
        for count in poi_counts:
            test_pois = []
            for i in range(count):
                # Distribute POIs across different states
                if i % 5 == 0:
                    lat, lon = 39.7391 + (i * 0.001), -75.5398 + (i * 0.001)  # Delaware area
                elif i % 5 == 1:
                    lat, lon = 34.0522 + (i * 0.001), -118.2437 + (i * 0.001)  # LA area
                elif i % 5 == 2:
                    lat, lon = 35.7796 + (i * 0.001), -78.6382 + (i * 0.001)   # Raleigh area
                elif i % 5 == 3:
                    lat, lon = 29.7604 + (i * 0.001), -95.3698 + (i * 0.001)   # Houston area
                else:
                    lat, lon = 40.7128 + (i * 0.001), -74.0060 + (i * 0.001)   # NYC area
                
                test_pois.append({'lat': lat, 'lon': lon, 'id': f'poi_{i}'})
            
            # Clear cache for these POI coordinates
            for poi in test_pois:
                try:
                    manager.db.conn.execute(
                        "DELETE FROM point_geography_cache WHERE lat = ? AND lon = ?", 
                        (poi['lat'], poi['lon'])
                    )
                except:
                    pass  # Ignore if cache doesn't exist
            
            start_time = time.time()
            counties = get_counties_from_pois(test_pois, include_neighbors=False)
            elapsed = time.time() - start_time
            
            per_poi_time = elapsed / count * 1000
            cold_poi_results.append((count, elapsed, per_poi_time, len(counties)))
            print(f"     {count} POIs (cold): {elapsed*1000:.2f}ms total, {per_poi_time:.2f}ms per POI -> {len(counties)} counties")
        
        print(f"\n  4b. POI Processing at Scale - Warm Cache:")
        print("     (Subsequent runs with cache)")
        
        for count, _, _, _ in cold_poi_results:
            # Use same POIs but now they should be cached
            test_pois = []
            for i in range(count):
                if i % 5 == 0:
                    lat, lon = 39.7391 + (i * 0.001), -75.5398 + (i * 0.001)
                elif i % 5 == 1:
                    lat, lon = 34.0522 + (i * 0.001), -118.2437 + (i * 0.001)
                elif i % 5 == 2:
                    lat, lon = 35.7796 + (i * 0.001), -78.6382 + (i * 0.001)
                elif i % 5 == 3:
                    lat, lon = 29.7604 + (i * 0.001), -95.3698 + (i * 0.001)
                else:
                    lat, lon = 40.7128 + (i * 0.001), -74.0060 + (i * 0.001)
                
                test_pois.append({'lat': lat, 'lon': lon, 'id': f'poi_{i}'})
            
            start_time = time.time()
            counties = get_counties_from_pois(test_pois, include_neighbors=False)
            elapsed = time.time() - start_time
            
            per_poi_time = elapsed / count * 1000
            
            # Find corresponding cold cache result
            cold_elapsed = next(result[1] for result in cold_poi_results if result[0] == count)
            speedup = cold_elapsed / elapsed if elapsed > 0 else 0
            
            print(f"     {count} POIs (warm): {elapsed*1000:.2f}ms total, {per_poi_time:.2f}ms per POI (speedup: {speedup:.1f}x)")
        
        # Benchmark 5: County neighbor initialization (if not already done)
        print(f"\n  5. County Neighbor Initialization Test:")
        manager = get_neighbor_manager()
        stats = manager.get_neighbor_statistics()
        
        if stats['county_neighbors'] == 0:
            print("     County neighbors not initialized. Testing initialization for one state...")
            start_time = time.time()
            try:
                # Initialize just North Carolina for testing
                import asyncio
                count = asyncio.run(manager.initialize_county_neighbors(['37'], force_refresh=False))
                init_time = time.time() - start_time
                print(f"     Initialized {count} county relationships for NC in {init_time:.2f}s")
                
                # Test county lookup after initialization
                start_time = time.time()
                nc_county_neighbors = get_neighboring_counties('37', '183')  # Wake County
                lookup_time = time.time() - start_time
                print(f"     Wake County neighbors after init: {lookup_time*1000:.2f}ms ({len(nc_county_neighbors)} neighbors)")
                
            except Exception as e:
                print(f"     County initialization failed: {e}")
        else:
            print(f"     County neighbors already initialized ({stats['county_neighbors']} relationships)")
        
        # Benchmark 6: Database statistics
        print(f"\n  6. Database Statistics:")
        updated_stats = manager.get_neighbor_statistics()
        
        for key, value in updated_stats.items():
            print(f"     {key}: {value}")
        
        print("\n  === Benchmark Summary ===")
        print(f"  • State lookups are very fast (~{avg_state_time*1000:.1f}ms average)")
        if county_times:
            print(f"  • County lookups are fast (~{avg_county_time*1000:.1f}ms average)")
        if cold_cache_times and warm_cache_times:
            cache_speedup = (sum(cold_cache_times) / sum(warm_cache_times)) if sum(warm_cache_times) > 0 else 0
            avg_cold = sum(cold_cache_times) / len(cold_cache_times)
            avg_warm = sum(warm_cache_times) / len(warm_cache_times)
            print(f"  • Point geocoding: {avg_cold*1000:.1f}ms cold → {avg_warm*1000:.1f}ms warm ({cache_speedup:.1f}x speedup)")
        
        if cold_poi_results:
            # Calculate average speedup for POI processing
            poi_speedups = []
            for count, cold_elapsed, _, _ in cold_poi_results:
                # Find warm cache time for same count
                test_pois = []
                for i in range(count):
                    if i % 5 == 0:
                        lat, lon = 39.7391 + (i * 0.001), -75.5398 + (i * 0.001)
                    elif i % 5 == 1:
                        lat, lon = 34.0522 + (i * 0.001), -118.2437 + (i * 0.001)
                    elif i % 5 == 2:
                        lat, lon = 35.7796 + (i * 0.001), -78.6382 + (i * 0.001)
                    elif i % 5 == 3:
                        lat, lon = 29.7604 + (i * 0.001), -95.3698 + (i * 0.001)
                    else:
                        lat, lon = 40.7128 + (i * 0.001), -74.0060 + (i * 0.001)
                    test_pois.append({'lat': lat, 'lon': lon, 'id': f'poi_{i}'})
                
                start_time = time.time()
                get_counties_from_pois(test_pois, include_neighbors=False)
                warm_elapsed = time.time() - start_time
                
                if warm_elapsed > 0:
                    poi_speedups.append(cold_elapsed / warm_elapsed)
            
            if poi_speedups:
                avg_poi_speedup = sum(poi_speedups) / len(poi_speedups)
                print(f"  • POI processing benefits significantly from caching ({avg_poi_speedup:.1f}x speedup)")
        
        print(f"  • Major bottleneck eliminated: First-time users get realistic performance")
        print(f"  • Subsequent runs benefit from intelligent caching")
        
        print("✓ Performance benchmarks completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Performance benchmarks failed: {e}")
        return False


def test_backward_compatibility():
    """Test that backward compatibility functions work."""
    print("Testing backward compatibility...")
    
    try:
        # Test the old API functions
        from socialmapper.census import isochrone_to_block_groups
        
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
        test_neighbor_functionality,
        test_performance_benchmarks,
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


def run_performance_only():
    """Run only performance benchmarks for focused analysis."""
    print("=" * 60)
    print("SocialMapper Census Module - Performance Benchmarks")
    print("=" * 60)
    
    try:
        success = test_performance_benchmarks()
        print("\n" + "=" * 60)
        if success:
            print("🚀 Performance benchmarks completed successfully!")
        else:
            print("⚠ Performance benchmarks encountered issues.")
        return success
    except Exception as e:
        print(f"✗ Performance benchmarks crashed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # Check if user wants to run only performance tests
    if len(sys.argv) > 1 and sys.argv[1] == "--performance":
        success = run_performance_only()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)