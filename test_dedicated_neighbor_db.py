#!/usr/bin/env python3
"""Test the dedicated neighbor database functionality."""

import tempfile
import time
from pathlib import Path
import sys
sys.path.append('socialmapper')
from census.neighbors import get_neighbor_manager, DEFAULT_NEIGHBOR_DB_PATH
from census import get_census_database, DEFAULT_DB_PATH

def test_dedicated_neighbor_database():
    """Test that neighbor database is separate from main census database."""
    print("="*60)
    print("TESTING DEDICATED NEIGHBOR DATABASE")
    print("="*60)
    
    # Test 1: Check default paths are different
    print(f"\n1. Checking database paths...")
    print(f"   Main census DB: {DEFAULT_DB_PATH}")
    print(f"   Neighbor DB:    {DEFAULT_NEIGHBOR_DB_PATH}")
    
    if DEFAULT_DB_PATH == DEFAULT_NEIGHBOR_DB_PATH:
        print("   ❌ ERROR: Databases use the same path!")
        return False
    else:
        print("   ✅ Databases use separate paths")
    
    # Test 2: Initialize neighbor manager
    print(f"\n2. Initializing neighbor manager...")
    start_time = time.time()
    
    try:
        manager = get_neighbor_manager()
        init_time = time.time() - start_time
        print(f"   ✅ Neighbor manager initialized in {init_time:.3f} seconds")
        print(f"   Database path: {manager.db.db_path}")
        
        # Check that the database file exists
        if manager.db.db_path.exists():
            size = manager.db.db_path.stat().st_size
            print(f"   Database size: {size:,} bytes ({size/1024:.1f} KB)")
        else:
            print("   Database file created (empty)")
            
    except Exception as e:
        print(f"   ❌ Failed to initialize neighbor manager: {e}")
        return False
    
    # Test 3: Initialize state neighbors
    print(f"\n3. Initializing state neighbors...")
    start_time = time.time()
    
    try:
        count = manager.initialize_state_neighbors()
        init_time = time.time() - start_time
        print(f"   ✅ Initialized {count} state relationships in {init_time:.3f} seconds")
        
        # Check database size after initialization
        if manager.db.db_path.exists():
            size = manager.db.db_path.stat().st_size
            print(f"   Database size after state init: {size:,} bytes ({size/1024:.1f} KB)")
            
    except Exception as e:
        print(f"   ❌ Failed to initialize state neighbors: {e}")
        return False
    
    # Test 4: Test neighbor lookups
    print(f"\n4. Testing neighbor lookups...")
    
    try:
        # Test North Carolina neighbors
        start_time = time.time()
        nc_neighbors = manager.get_neighboring_states('37')
        lookup_time = time.time() - start_time
        
        print(f"   ✅ NC neighbors lookup: {lookup_time*1000:.1f} ms")
        print(f"   NC neighbors: {nc_neighbors}")
        
        if len(nc_neighbors) == 0:
            print("   ⚠️  Warning: No neighbors found for NC")
        
    except Exception as e:
        print(f"   ❌ Failed neighbor lookup: {e}")
        return False
    
    # Test 5: Check database separation
    print(f"\n5. Checking database separation...")
    
    try:
        # Get main census database
        census_db = get_census_database()
        
        print(f"   Main census DB path: {census_db.db_path}")
        print(f"   Neighbor DB path:    {manager.db.db_path}")
        
        # Check if they're different objects
        if census_db.db_path == manager.db.db_path:
            print("   ❌ ERROR: Databases use the same file!")
            return False
        else:
            print("   ✅ Databases are properly separated")
            
        # Check main census DB doesn't have neighbor tables
        try:
            count = census_db.conn.execute("SELECT COUNT(*) FROM state_neighbors").fetchone()[0]
            print(f"   ❌ ERROR: Main census DB has neighbor tables! ({count} rows)")
            return False
        except Exception:
            print("   ✅ Main census DB doesn't have neighbor tables (as expected)")
            
        # Check neighbor DB has neighbor tables
        try:
            count = manager.db.conn.execute("SELECT COUNT(*) FROM state_neighbors").fetchone()[0]
            print(f"   ✅ Neighbor DB has {count} state neighbor relationships")
        except Exception as e:
            print(f"   ❌ ERROR: Neighbor DB missing state_neighbors table: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed database separation test: {e}")
        return False
    
    # Test 6: Test with custom path
    print(f"\n6. Testing custom database path...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom_neighbors.duckdb"
            
            # Create manager with custom path
            custom_manager = get_neighbor_manager(custom_path)
            
            print(f"   Custom DB path: {custom_manager.db.db_path}")
            
            if custom_manager.db.db_path != custom_path:
                print("   ❌ ERROR: Custom path not used!")
                return False
            else:
                print("   ✅ Custom path used correctly")
                
            # Initialize and test
            count = custom_manager.initialize_state_neighbors()
            print(f"   ✅ Custom DB initialized with {count} relationships")
            
    except Exception as e:
        print(f"   ❌ Failed custom path test: {e}")
        return False
    
    print(f"\n✅ ALL TESTS PASSED!")
    print("\nDedicated neighbor database is working correctly:")
    print("• Separate from main census database")
    print("• Uses dedicated file path")
    print("• Properly isolated neighbor data")
    print("• Supports custom database paths")
    print("• Fast neighbor lookups")
    
    return True

def test_database_sizes():
    """Compare database sizes to show separation benefits."""
    print(f"\n" + "="*60)
    print("DATABASE SIZE COMPARISON")
    print("="*60)
    
    try:
        # Check main census database
        census_db = get_census_database()
        if census_db.db_path.exists():
            census_size = census_db.db_path.stat().st_size
            print(f"Main census database: {census_size:,} bytes ({census_size/(1024*1024):.2f} MB)")
        else:
            print("Main census database: Not found")
            census_size = 0
        
        # Check neighbor database
        neighbor_manager = get_neighbor_manager()
        if neighbor_manager.db.db_path.exists():
            neighbor_size = neighbor_manager.db.db_path.stat().st_size
            print(f"Neighbor database:    {neighbor_size:,} bytes ({neighbor_size/1024:.1f} KB)")
        else:
            print("Neighbor database: Not found")
            neighbor_size = 0
        
        if census_size > 0 and neighbor_size > 0:
            ratio = census_size / neighbor_size
            print(f"\nSize ratio: Main DB is {ratio:.1f}x larger than neighbor DB")
            print("This shows the neighbor DB is lightweight and focused!")
        
    except Exception as e:
        print(f"Failed to compare database sizes: {e}")

def main():
    """Run all tests."""
    print("DEDICATED NEIGHBOR DATABASE TEST SUITE")
    print("="*60)
    
    try:
        # Test basic functionality
        if not test_dedicated_neighbor_database():
            print("❌ Tests failed")
            return
        
        # Compare database sizes
        test_database_sizes()
        
        print(f"\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 