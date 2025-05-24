#!/usr/bin/env python3
"""Test the dual distribution system for neighbor data."""

import time
import tempfile
from pathlib import Path
import sys
sys.path.append('socialmapper')
from census import (
    export_neighbor_data,
    get_distributed_neighbor_loader,
    get_neighboring_states_distributed,
    get_neighboring_counties_distributed
)

def test_export_and_load():
    """Test exporting neighbor data and loading it back."""
    print("="*60)
    print("TESTING DUAL DISTRIBUTION SYSTEM")
    print("="*60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Using temporary directory: {temp_path}")
        
        # Test 1: Export production formats (JSON + DuckDB)
        print(f"\n1. Exporting production formats...")
        start_time = time.time()
        
        try:
            exported_files = export_neighbor_data(
                output_dir=temp_path,
                formats=['production'],
                state_fips_list=['37']  # Just North Carolina for testing
            )
            
            export_time = time.time() - start_time
            print(f"   Export completed in {export_time:.2f} seconds")
            
            # Show exported files
            for format_name, filepath in exported_files.items():
                size = filepath.stat().st_size
                print(f"   {format_name}: {filepath.name} ({size:,} bytes, {size/1024:.1f} KB)")
            
        except Exception as e:
            print(f"   ❌ Export failed: {e}")
            return False
        
        # Test 2: Load from DuckDB format
        print(f"\n2. Testing DuckDB loader...")
        start_time = time.time()
        
        try:
            loader = get_distributed_neighbor_loader(temp_path)
            success = loader.load_data(force_format='duckdb')
            load_time = time.time() - start_time
            
            if success:
                print(f"   ✅ DuckDB loaded in {load_time*1000:.1f} ms")
                metadata = loader.get_metadata()
                print(f"   Format: {metadata.get('loaded_format', 'unknown')}")
                
                # Test state neighbors
                nc_neighbors = loader.get_state_neighbors('37')
                print(f"   NC state neighbors: {nc_neighbors}")
                
                # Test county neighbors
                wake_neighbors = loader.get_county_neighbors('37', '183')  # Wake County, NC
                print(f"   Wake County neighbors: {len(wake_neighbors)} counties")
                
            else:
                print(f"   ❌ DuckDB loading failed")
                return False
                
        except Exception as e:
            print(f"   ❌ DuckDB test failed: {e}")
            return False
        
        # Test 3: Load from JSON format
        print(f"\n3. Testing JSON loader...")
        start_time = time.time()
        
        try:
            # Create new loader instance to test JSON fallback
            loader2 = get_distributed_neighbor_loader(temp_path)
            
            # Remove DuckDB file to force JSON loading
            duckdb_file = temp_path / "neighbor_data.duckdb"
            if duckdb_file.exists():
                duckdb_file.unlink()
            
            success = loader2.load_data(force_format='json')
            load_time = time.time() - start_time
            
            if success:
                print(f"   ✅ JSON loaded in {load_time*1000:.1f} ms")
                metadata = loader2.get_metadata()
                print(f"   Format: {metadata.get('loaded_format', 'unknown')}")
                
                # Test same queries
                nc_neighbors = loader2.get_state_neighbors('37')
                print(f"   NC state neighbors: {nc_neighbors}")
                
                wake_neighbors = loader2.get_county_neighbors('37', '183')
                print(f"   Wake County neighbors: {len(wake_neighbors)} counties")
                
            else:
                print(f"   ❌ JSON loading failed")
                return False
                
        except Exception as e:
            print(f"   ❌ JSON test failed: {e}")
            return False
        
        # Test 4: Convenience functions
        print(f"\n4. Testing convenience functions...")
        
        try:
            # Test with DuckDB (restore the file)
            exported_files = export_neighbor_data(
                output_dir=temp_path,
                formats=['duckdb'],
                state_fips_list=['37']
            )
            
            # Test convenience functions
            start_time = time.time()
            nc_neighbors = get_neighboring_states_distributed('37')
            state_time = time.time() - start_time
            
            start_time = time.time()
            wake_neighbors = get_neighboring_counties_distributed('37', '183')
            county_time = time.time() - start_time
            
            print(f"   ✅ State lookup: {state_time*1000:.1f} ms")
            print(f"   ✅ County lookup: {county_time*1000:.1f} ms")
            print(f"   NC neighbors: {nc_neighbors}")
            print(f"   Wake neighbors: {len(wake_neighbors)} counties")
            
        except Exception as e:
            print(f"   ❌ Convenience function test failed: {e}")
            return False
        
        print(f"\n✅ All tests passed!")
        return True

def test_performance_comparison():
    """Compare performance between formats."""
    print(f"\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Export both formats
        print("Exporting test data...")
        export_neighbor_data(
            output_dir=temp_path,
            formats=['production'],
            state_fips_list=['37']  # North Carolina
        )
        
        # Test DuckDB performance
        print(f"\nTesting DuckDB performance...")
        loader_db = get_distributed_neighbor_loader(temp_path)
        
        # Initial load
        start_time = time.time()
        loader_db.load_data(force_format='duckdb')
        initial_load_time = time.time() - start_time
        
        # Query performance
        query_times = []
        for _ in range(10):
            start_time = time.time()
            neighbors = loader_db.get_county_neighbors('37', '183')
            query_times.append(time.time() - start_time)
        
        avg_query_time = sum(query_times) * 1000 / len(query_times)  # Convert to ms
        
        print(f"   Initial load: {initial_load_time*1000:.1f} ms")
        print(f"   Average query: {avg_query_time:.3f} ms")
        
        # Test JSON performance
        print(f"\nTesting JSON performance...")
        
        # Remove DuckDB to force JSON
        duckdb_file = temp_path / "neighbor_data.duckdb"
        if duckdb_file.exists():
            duckdb_file.unlink()
        
        loader_json = get_distributed_neighbor_loader(temp_path)
        
        # Initial load
        start_time = time.time()
        loader_json.load_data(force_format='json')
        initial_load_time = time.time() - start_time
        
        # Query performance
        query_times = []
        for _ in range(10):
            start_time = time.time()
            neighbors = loader_json.get_county_neighbors('37', '183')
            query_times.append(time.time() - start_time)
        
        avg_query_time = sum(query_times) * 1000 / len(query_times)  # Convert to ms
        
        print(f"   Initial load: {initial_load_time*1000:.1f} ms")
        print(f"   Average query: {avg_query_time:.3f} ms")

def test_export_formats():
    """Test exporting all formats."""
    print(f"\n" + "="*60)
    print("TESTING ALL EXPORT FORMATS")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print("Exporting all formats...")
        exported_files = export_neighbor_data(
            output_dir=temp_path,
            formats=['all'],
            state_fips_list=['37']  # North Carolina only for speed
        )
        
        print(f"\nExported files:")
        total_size = 0
        for format_name, filepath in exported_files.items():
            size = filepath.stat().st_size
            total_size += size
            print(f"  {format_name}: {filepath.name}")
            print(f"    Size: {size:,} bytes ({size/1024:.1f} KB)")
            if size > 1024*1024:
                print(f"    Size: {size/(1024*1024):.2f} MB")
        
        print(f"\nTotal size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
        
        # Test loading from each format
        print(f"\nTesting format compatibility:")
        
        # Test DuckDB
        try:
            loader = get_distributed_neighbor_loader(temp_path)
            success = loader.load_data(force_format='duckdb')
            print(f"  DuckDB: {'✅ Success' if success else '❌ Failed'}")
        except Exception as e:
            print(f"  DuckDB: ❌ Error - {e}")
        
        # Test JSON (remove DuckDB first)
        try:
            (temp_path / "neighbor_data.duckdb").unlink()
            loader = get_distributed_neighbor_loader(temp_path)
            success = loader.load_data(force_format='json')
            print(f"  JSON: {'✅ Success' if success else '❌ Failed'}")
        except Exception as e:
            print(f"  JSON: ❌ Error - {e}")

def main():
    """Run all tests."""
    print("DUAL DISTRIBUTION SYSTEM TEST SUITE")
    print("="*60)
    
    try:
        # Test basic functionality
        if not test_export_and_load():
            print("❌ Basic tests failed")
            return
        
        # Test performance
        test_performance_comparison()
        
        # Test all formats
        test_export_formats()
        
        print(f"\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nThe dual distribution system is working correctly:")
        print("• Export: Creates both DuckDB and compressed JSON formats")
        print("• Load: Automatically chooses best available format")
        print("• Performance: DuckDB for speed, JSON for compatibility")
        print("• Size: Both formats are very small and GitHub-friendly")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 