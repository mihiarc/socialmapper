#!/usr/bin/env python3
"""
Simple benchmark for enhanced isochrone generation with caching.

This script tests the performance benefits of the caching system
without the complexity of neatnet processing.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the parent directory to the path so we can import socialmapper
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper.isochrone import create_isochrones_from_poi_list
from socialmapper.util import PerformanceBenchmark

def clear_network_cache():
    """Clear the network cache."""
    try:
        from socialmapper.isochrone.network_cache import get_network_cache
        cache = get_network_cache()
        cache.clear_cache()
        print("Network cache cleared")
    except Exception as e:
        print(f"Warning: Could not clear cache: {e}")

def create_test_scenario():
    """Create a test scenario with multiple nearby POIs."""
    
    scenario = {
        "name": "Manhattan Libraries",
        "type": "urban_dense",
        "pois": [
            {
                'id': 'manhattan_library_1',
                'lat': 40.7589,  # New York Public Library
                'lon': -73.9851,
                'tags': {'name': 'New York Public Library'},
                'type': 'amenity'
            },
            {
                'id': 'manhattan_library_2', 
                'lat': 40.7505,  # Nearby library
                'lon': -73.9934,
                'tags': {'name': 'Manhattan Library Branch'},
                'type': 'amenity'
            },
            {
                'id': 'manhattan_library_3',
                'lat': 40.7614,  # Another nearby library
                'lon': -73.9776,
                'tags': {'name': 'East Side Library'},
                'type': 'amenity'
            }
        ]
    }
    
    return scenario

def benchmark_method(method_name, poi_data, travel_time):
    """Benchmark the standard method with caching."""
    
    print(f"\nTesting {method_name}...")
    
    try:
        start_time = time.time()
        
        result = create_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir=f"output/benchmark_simple/{method_name}",
            save_individual_files=False,
            combine_results=True
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"{method_name}: {elapsed_time:.2f}s")
        return {
            'method': method_name,
            'time': elapsed_time,
            'success': True
        }
        
    except Exception as e:
        print(f"{method_name} failed: {e}")
        return {
            'method': method_name,
            'time': float('inf'),
            'success': False,
            'error': str(e)
        }

def run_simple_benchmark():
    """Run a simple benchmark testing the caching system benefits."""
    
    print("=" * 80)
    print("Simple Caching Performance Benchmark")
    print("=" * 80)
    
    # Create output directory
    output_dir = Path("output/benchmark_simple")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get test scenario
    scenario = create_test_scenario()
    poi_data = {
        'pois': scenario['pois'],
        'metadata': {
            'source': 'test',
            'count': len(scenario['pois'])
        }
    }
    
    travel_time = 10
    results = []
    
    print(f"Testing scenario: {scenario['name']}")
    print(f"POIs: {len(scenario['pois'])}")
    print(f"Travel time: {travel_time} minutes")
    
    # Test 1: Standard method (cold cache)
    print("\n[1/2] Standard method (cold cache)")
    clear_network_cache()
    result1 = benchmark_method("standard_cold", poi_data, travel_time)
    results.append(result1)
    
    # Test 2: Standard method (warm cache) 
    print("\n[2/2] Standard method (warm cache)")
    # Don't clear cache - should benefit from previous downloads
    result2 = benchmark_method("standard_warm", poi_data, travel_time)
    results.append(result2)
    
    return results

def analyze_results(results):
    """Analyze the benchmark results."""
    
    print(f"\n{'='*80}")
    print(f"CACHING BENCHMARK ANALYSIS")
    print(f"{'='*80}")
    
    # Extract times
    cold_time = None
    warm_time = None
    
    for result in results:
        if result['success']:
            if result['method'] == 'standard_cold':
                cold_time = result['time']
            elif result['method'] == 'standard_warm':
                warm_time = result['time']
    
    print(f"\nTiming Results:")
    print(f"Cold cache (first run):    {cold_time:.2f}s" if cold_time else "Cold cache: FAILED")
    print(f"Warm cache (second run):   {warm_time:.2f}s" if warm_time else "Warm cache: FAILED")
    
    if cold_time is not None and warm_time is not None:
        cache_speedup = cold_time / warm_time
        time_saved = cold_time - warm_time
        
        print(f"\nCache Impact:")
        print(f"Speedup from caching:      {cache_speedup:.2f}x")
        print(f"Time saved:                {time_saved:.2f}s")
        print(f"Performance improvement:   {((cache_speedup - 1) * 100):.1f}%")
        
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        
        if cache_speedup > 3.0:
            print(f"✅ Network caching provides excellent performance improvement: {cache_speedup:.1f}x speedup")
        elif cache_speedup > 2.0:
            print(f"✅ Network caching provides significant performance improvement: {cache_speedup:.1f}x speedup")
        elif cache_speedup > 1.5:
            print(f"✅ Network caching provides moderate performance improvement: {cache_speedup:.1f}x speedup")
        elif cache_speedup > 1.1:
            print(f"➖ Network caching provides minimal improvement: {cache_speedup:.1f}x speedup")
        else:
            print(f"❌ Network caching shows no significant improvement: {cache_speedup:.1f}x speedup")
        
        print(f"\n💡 The caching system is most beneficial when processing multiple nearby POIs")
        print(f"   where network downloads can be reused across different analyses.")

def main():
    """Main benchmark execution."""
    
    results = run_simple_benchmark()
    
    if results:
        # Save results
        output_dir = Path("output/benchmark_simple")
        results_file = output_dir / "simple_benchmark_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Analyze results
        analyze_results(results)
        
        print(f"\nDetailed results saved to: {results_file}")
    
    print(f"\n{'='*80}")
    print(f"Simple benchmark completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 