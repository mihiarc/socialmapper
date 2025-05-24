#!/usr/bin/env python3
"""
Demonstration of the dedicated neighbor database functionality.

This script shows how the new dedicated neighbor database provides:
1. Separation from the main census database
2. Fast neighbor lookups
3. Optimized storage for neighbor relationships
"""

import time
import sys
sys.path.append('socialmapper')

from census.neighbors import get_neighbor_manager
from census import get_census_database

def main():
    print("🎯 DEDICATED NEIGHBOR DATABASE DEMONSTRATION")
    print("=" * 60)
    
    # Show database separation
    print("\n📁 DATABASE SEPARATION:")
    census_db = get_census_database()
    neighbor_manager = get_neighbor_manager()
    
    print(f"   Main Census DB:  {census_db.db_path}")
    print(f"   Neighbor DB:     {neighbor_manager.db.db_path}")
    
    # Show database sizes
    if census_db.db_path.exists():
        census_size = census_db.db_path.stat().st_size
        print(f"   Census DB size:  {census_size:,} bytes ({census_size/(1024*1024):.1f} MB)")
    
    if neighbor_manager.db.db_path.exists():
        neighbor_size = neighbor_manager.db.db_path.stat().st_size
        print(f"   Neighbor DB size: {neighbor_size:,} bytes ({neighbor_size/1024:.1f} KB)")
        
        if census_size > 0:
            ratio = census_size / neighbor_size
            print(f"   📊 Size ratio: Census DB is {ratio:.1f}x larger than Neighbor DB")
    
    # Initialize state neighbors if needed
    print("\n🚀 INITIALIZING STATE NEIGHBORS:")
    start_time = time.time()
    count = neighbor_manager.initialize_state_neighbors()
    init_time = time.time() - start_time
    print(f"   ✅ Initialized {count} state relationships in {init_time:.3f} seconds")
    
    # Demonstrate fast lookups
    print("\n⚡ FAST NEIGHBOR LOOKUPS:")
    
    # Test multiple states
    test_states = [
        ('37', 'North Carolina'),
        ('06', 'California'), 
        ('48', 'Texas'),
        ('36', 'New York'),
        ('12', 'Florida')
    ]
    
    total_time = 0
    for state_fips, state_name in test_states:
        start_time = time.time()
        neighbors = neighbor_manager.get_neighboring_states(state_fips)
        lookup_time = time.time() - start_time
        total_time += lookup_time
        
        print(f"   {state_name} ({state_fips}): {len(neighbors)} neighbors in {lookup_time*1000:.2f} ms")
        print(f"      Neighbors: {neighbors}")
    
    avg_time = total_time / len(test_states)
    print(f"   📈 Average lookup time: {avg_time*1000:.2f} ms")
    
    # Show point geocoding cache
    print("\n🗺️  POINT GEOCODING CACHE:")
    
    # Test some sample points
    test_points = [
        (35.7796, -78.6382, "Raleigh, NC"),
        (34.0522, -118.2437, "Los Angeles, CA"),
        (29.7604, -95.3698, "Houston, TX")
    ]
    
    for lat, lon, location in test_points:
        start_time = time.time()
        geography = neighbor_manager.get_geography_from_point(lat, lon)
        lookup_time = time.time() - start_time
        
        print(f"   {location}: {lookup_time*1000:.1f} ms")
        print(f"      State: {geography.get('state_fips')}, County: {geography.get('county_fips')}")
    
    # Show statistics
    print("\n📊 NEIGHBOR DATABASE STATISTICS:")
    stats = neighbor_manager.get_neighbor_statistics()
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value:,}")
    
    print("\n🎉 BENEFITS OF DEDICATED NEIGHBOR DATABASE:")
    print("   ✅ Keeps neighbor data separate from main census cache")
    print("   ✅ Prevents main database from getting bloated")
    print("   ✅ Optimized specifically for neighbor relationships")
    print("   ✅ Fast lookups without real-time spatial computation")
    print("   ✅ Supports point geocoding cache for POI processing")
    print("   ✅ Can be backed up/restored independently")
    print("   ✅ Supports custom database paths for different projects")
    
    print(f"\n{'='*60}")
    print("🚀 Dedicated neighbor database is ready for use!")

if __name__ == "__main__":
    main() 