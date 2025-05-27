#!/usr/bin/env python3
"""
Debug script to understand the performance differences.
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import socialmapper
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper.isochrone.neatnet_enhanced import (
    create_enhanced_isochrones_from_poi_list,
    NEATNET_AVAILABLE
)
from socialmapper.isochrone import create_isochrones_from_poi_list

def clear_network_cache():
    """Clear the network cache."""
    try:
        from socialmapper.isochrone.network_cache import get_network_cache
        cache = get_network_cache()
        cache.clear_cache()
        print("Network cache cleared")
    except Exception as e:
        print(f"Warning: Could not clear cache: {e}")

def debug_single_comparison():
    """Debug a single comparison to understand the difference."""
    
    poi_data = {
        'pois': [{
            'id': 'manhattan_library_1',
            'lat': 40.7589,
            'lon': -73.9851,
            'tags': {'name': 'New York Public Library'},
            'type': 'amenity'
        }],
        'metadata': {
            'source': 'test',
            'count': 1
        }
    }
    
    travel_time = 10
    
    print("=" * 60)
    print("DEBUG: Single Comparison (10-minute isochrone)")
    print("=" * 60)
    
    # Test 1: Standard method (cold cache)
    print("\n1. Standard method (cold cache):")
    clear_network_cache()
    start_time = time.time()
    try:
        result1 = create_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir="output/debug/standard_cold",
            save_individual_files=False,
            combine_results=False
        )
        time1 = time.time() - start_time
        print(f"Standard (cold): {time1:.2f}s")
    except Exception as e:
        print(f"Standard failed: {e}")
        time1 = None
    
    # Test 2: Enhanced method (cold cache, no neatnet)
    print("\n2. Enhanced method (cold cache, no neatnet):")
    clear_network_cache()
    start_time = time.time()
    try:
        result2 = create_enhanced_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir="output/debug/enhanced_cold_no_neatnet",
            save_individual_files=False,
            combine_results=False,
            use_neatnet=False
        )
        time2 = time.time() - start_time
        print(f"Enhanced (cold, no neatnet): {time2:.2f}s")
    except Exception as e:
        print(f"Enhanced (no neatnet) failed: {e}")
        time2 = None
    
    # Test 3: Enhanced method (warm cache, no neatnet)
    print("\n3. Enhanced method (warm cache, no neatnet):")
    # Don't clear cache - should hit cache from previous test
    start_time = time.time()
    try:
        result3 = create_enhanced_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir="output/debug/enhanced_warm_no_neatnet",
            save_individual_files=False,
            combine_results=False,
            use_neatnet=False
        )
        time3 = time.time() - start_time
        print(f"Enhanced (warm, no neatnet): {time3:.2f}s")
    except Exception as e:
        print(f"Enhanced (warm, no neatnet) failed: {e}")
        time3 = None
    
    # Test 4: Enhanced method (cold cache, with neatnet)
    print("\n4. Enhanced method (cold cache, with neatnet):")
    clear_network_cache()
    start_time = time.time()
    try:
        result4 = create_enhanced_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir="output/debug/enhanced_cold_neatnet",
            save_individual_files=False,
            combine_results=False,
            use_neatnet=True
        )
        time4 = time.time() - start_time
        print(f"Enhanced (cold, with neatnet): {time4:.2f}s")
    except Exception as e:
        print(f"Enhanced (with neatnet) failed: {e}")
        time4 = None
    
    # Test 5: Enhanced method (warm cache, with neatnet)
    print("\n5. Enhanced method (warm cache, with neatnet):")
    # Don't clear cache - should hit cache from previous test
    start_time = time.time()
    try:
        result5 = create_enhanced_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir="output/debug/enhanced_warm_neatnet",
            save_individual_files=False,
            combine_results=False,
            use_neatnet=True
        )
        time5 = time.time() - start_time
        print(f"Enhanced (warm, with neatnet): {time5:.2f}s")
    except Exception as e:
        print(f"Enhanced (warm, with neatnet) failed: {e}")
        time5 = None
    
    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    if all(t is not None for t in [time1, time2, time3, time4, time5]):
        print(f"\nTiming Results:")
        print(f"1. Standard (cold):           {time1:.2f}s")
        print(f"2. Enhanced (cold, no neat):  {time2:.2f}s")
        print(f"3. Enhanced (warm, no neat):  {time3:.2f}s")
        print(f"4. Enhanced (cold, neat):     {time4:.2f}s")
        print(f"5. Enhanced (warm, neat):     {time5:.2f}s")
        
        print(f"\nSpeedups vs Standard:")
        print(f"Enhanced (cold, no neat):  {time1/time2:.2f}x")
        print(f"Enhanced (warm, no neat):  {time1/time3:.2f}x")
        print(f"Enhanced (cold, neat):     {time1/time4:.2f}x")
        print(f"Enhanced (warm, neat):     {time1/time5:.2f}x")
        
        print(f"\nCache Impact:")
        print(f"No neatnet: {time2/time3:.2f}x speedup from cache")
        print(f"With neatnet: {time4/time5:.2f}x speedup from cache")
        
        print(f"\nneatnet Impact:")
        print(f"Cold cache: {time2/time4:.2f}x speedup from neatnet")
        print(f"Warm cache: {time3/time5:.2f}x speedup from neatnet")

if __name__ == "__main__":
    debug_single_comparison() 